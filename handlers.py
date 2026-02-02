from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from db import ensure_user, set_user_goal, get_user_goal, get_user_unit, set_user_unit, insert_lift, get_user_lifts
from llm import parse_lift_text, get_workout_recommendation, refine_recommendation
from prompts import (
    CANCEL_MESSAGE,
    HELP_MESSAGE,
    RECOMMEND_LOADING,
    RECOMMEND_REFINE_PROMPT,
    SETGOAL_EXAMPLE,
    SETGOAL_UPDATED,
    SETUNIT_USAGE,
    SETUNIT_UPDATED,
    START_MESSAGE,
    TRACK_CANCELLED,
    TRACK_CONFIRM_QUESTION,
    TRACK_CONTINUE_PROMPT,
    TRACK_FILL,
    TRACK_INVALID_EXERCISE,
    TRACK_INVALID_GENERIC,
    TRACK_INVALID_SETS_REPS,
    TRACK_INVALID_WEIGHT,
    TRACK_SAVED,
    TRACK_SAVED_MULTI,
    TRACK_START,
    VIEW_EMPTY,
)

# Conversation states for /track
WAITING_INPUT, FILLING_EXERCISE, FILLING_SETS, FILLING_REPS, FILLING_WEIGHT, CONFIRMING = range(6)

LBS_TO_KG = 0.453592


def _format_weight(weight_lbs: float, unit: str) -> str:
    """Format weight for display. Weight is always stored in lbs."""
    if unit == "kg":
        return f"{float(weight_lbs) * LBS_TO_KG:.1f} kg"
    return f"{weight_lbs} lbs"


def _format_lift(exercise: str, sets: int, reps: int, weight: float, unit: str = "lbs") -> str:
    return f"{exercise}: {sets}x{reps} @ {_format_weight(weight, unit)}"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    ensure_user(user.id, user.username, user.first_name)
    context.user_data.pop("recommend_followup", None)
    await update.message.reply_text(START_MESSAGE, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    ensure_user(user.id, user.username, user.first_name)
    context.user_data.pop("recommend_followup", None)
    await update.message.reply_text(HELP_MESSAGE, parse_mode="Markdown")


async def setunit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    ensure_user(user.id, user.username, user.first_name)
    context.user_data.pop("recommend_followup", None)
    if context.args and context.args[0].lower() in ("lbs", "kg"):
        unit = context.args[0].lower()
        set_user_unit(user.id, unit)
        await update.message.reply_text(SETUNIT_UPDATED.format(unit=unit), parse_mode="Markdown")
    else:
        await update.message.reply_text(SETUNIT_USAGE, parse_mode="Markdown")


async def setgoal_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    ensure_user(user.id, user.username, user.first_name)
    context.user_data.pop("recommend_followup", None)
    if context.args:
        goal = " ".join(context.args)
        set_user_goal(user.id, goal)
        await update.message.reply_text(SETGOAL_UPDATED.format(goal=goal), parse_mode="Markdown")
    else:
        await update.message.reply_text(SETGOAL_EXAMPLE, parse_mode="Markdown")


async def track_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    ensure_user(user.id, user.username, user.first_name)
    context.user_data.clear()
    await update.message.reply_text(TRACK_START)
    return WAITING_INPUT


def _parse_single_lift(item):
    """Extract valid lift dict from a parsed item. Returns None if incomplete."""
    if not isinstance(item, dict):
        return None
    ex = item.get("exercise")
    s, r, w = item.get("sets"), item.get("reps"), item.get("weight")
    if not isinstance(ex, str) or not ex.strip():
        return None
    try:
        sets = int(s) if s is not None else None
        reps = int(r) if r is not None else None
        weight = float(w) if w is not None else None
    except (TypeError, ValueError):
        return None
    if sets is None or reps is None or weight is None:
        return None
    if sets < 1 or sets > 100 or reps < 1 or reps > 100 or weight <= 0 or weight > 2000:
        return None
    return {"exercise": ex.strip(), "sets": sets, "reps": reps, "weight": weight}


def _extract_complete_lifts(parsed):
    """From LLM parse result, return list of complete lift dicts."""
    if not parsed:
        return []
    items = parsed if isinstance(parsed, list) else [parsed]
    lifts = []
    for item in items:
        lift = _parse_single_lift(item)
        if lift:
            lifts.append(lift)
    return lifts


async def track_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    data = context.user_data
    data["raw"] = text

    parsed = []
    try:
        parsed = parse_lift_text(text) or []
        complete_lifts = _extract_complete_lifts(parsed)
    except (AttributeError, TypeError, ValueError, KeyError):
        complete_lifts = []

    if complete_lifts:
        data["pending_lifts"] = complete_lifts
        return await _show_confirmation(update, context)

    # Fall back to single-lift step-by-step
    data["pending_lifts"] = None
    data["exercise"] = None
    data["sets"] = None
    data["reps"] = None
    data["weight"] = None
    first = parsed[0] if (parsed and isinstance(parsed, list)) else {}
    if isinstance(first, dict):
        try:
            if isinstance(first.get("exercise"), str):
                data["exercise"] = first["exercise"].strip()
            for key, conv in [("sets", int), ("reps", int), ("weight", float)]:
                v = first.get(key)
                if v is not None:
                    data[key] = conv(v)
        except (TypeError, ValueError):
            pass

    missing = []
    if not data.get("exercise"):
        missing.append("exercise")
    if data.get("sets") is None:
        missing.append("sets")
    if data.get("reps") is None:
        missing.append("reps")
    if data.get("weight") is None:
        missing.append("weight")

    data["missing"] = missing
    data["missing_idx"] = 0
    field = missing[0]
    await update.message.reply_text(TRACK_FILL[field])
    return FILLING_EXERCISE if field == "exercise" else FILLING_SETS if field == "sets" else FILLING_REPS if field == "reps" else FILLING_WEIGHT


def _get_fill_state(field: str) -> int:
    return {"exercise": FILLING_EXERCISE, "sets": FILLING_SETS, "reps": FILLING_REPS, "weight": FILLING_WEIGHT}[field]


async def track_fill_exercise(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await _track_fill_field(update, context, "exercise", str, lambda x: x.strip())


async def track_fill_sets(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await _track_fill_field(update, context, "sets", int, lambda x: int(x.strip()))


async def track_fill_reps(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await _track_fill_field(update, context, "reps", int, lambda x: int(x.strip()))


async def track_fill_weight(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await _track_fill_field(update, context, "weight", float, lambda x: float(x.strip()))


async def _track_fill_field(update: Update, context: ContextTypes.DEFAULT_TYPE, field: str, _type: type, parse_fn) -> int:
    data = context.user_data
    try:
        val = parse_fn(update.message.text)
        if field == "exercise" and not val:
            await update.message.reply_text(TRACK_INVALID_EXERCISE)
            return _get_fill_state(field)
        if field in ("sets", "reps") and (not isinstance(val, int) or val < 1 or val > 100):
            await update.message.reply_text(TRACK_INVALID_SETS_REPS)
            return _get_fill_state(field)
        if field == "weight" and (val <= 0 or val > 2000):
            await update.message.reply_text(TRACK_INVALID_WEIGHT)
            return _get_fill_state(field)
        data[field] = val
    except (ValueError, TypeError):
        hint = "a number" if field in ("sets", "reps", "weight") else "text"
        await update.message.reply_text(TRACK_INVALID_GENERIC.format(hint=hint))
        return _get_fill_state(field)

    missing = data.get("missing", [])
    idx = data.get("missing_idx", 0) + 1
    data["missing_idx"] = idx
    if idx < len(missing):
        next_field = missing[idx]
        await update.message.reply_text(TRACK_FILL[next_field])
        return _get_fill_state(next_field)
    return await _show_confirmation(update, context)


async def _show_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = context.user_data
    unit = get_user_unit(update.effective_user.id)
    if data.get("pending_lifts"):
        lifts = data["pending_lifts"]
        lines = [_format_lift(l["exercise"], l["sets"], l["reps"], l["weight"], unit) for l in lifts]
        summary = "\n".join(lines)
        count = len(lifts)
    else:
        ex, sets, reps, weight = data["exercise"], data["sets"], data["reps"], data["weight"]
        summary = _format_lift(ex, sets, reps, weight, unit)
        count = 1
    keyboard = [
        [InlineKeyboardButton("✓ Confirm", callback_data="confirm_save"), InlineKeyboardButton("✗ Cancel", callback_data="confirm_cancel")],
    ]
    await update.message.reply_text(
        TRACK_CONFIRM_QUESTION.format(count=count, summary=summary),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return CONFIRMING


async def track_confirm_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "confirm_cancel":
        context.user_data.clear()
        await query.edit_message_text(TRACK_CANCELLED)
        return ConversationHandler.END

    data = context.user_data
    user_id = update.effective_user.id
    unit = get_user_unit(user_id)

    if data.get("pending_lifts"):
        lifts = data["pending_lifts"]
        for l in lifts:
            insert_lift(user_id, l["exercise"], l["sets"], l["reps"], l["weight"])
        lines = [_format_lift(l["exercise"], l["sets"], l["reps"], l["weight"], unit) for l in lifts]
        summary = ", ".join(lines)
        count = len(lifts)
        msg = TRACK_SAVED_MULTI.format(count=count) if count > 1 else TRACK_SAVED.format(summary=lines[0])
    else:
        insert_lift(
            user_id,
            data["exercise"],
            data["sets"],
            data["reps"],
            data["weight"],
        )
        summary = _format_lift(data["exercise"], data["sets"], data["reps"], data["weight"], unit)
        msg = TRACK_SAVED.format(summary=summary)

    context.user_data.clear()
    await query.edit_message_text(msg, parse_mode="Markdown")
    await query.message.reply_text(TRACK_CONTINUE_PROMPT)
    return WAITING_INPUT


def _serialize_history(history: list) -> list:
    return [
        {**h, "created_at": h["created_at"]} if isinstance(h.get("created_at"), str)
        else {**h, "created_at": h["created_at"].isoformat() if h.get("created_at") else None}
        for h in history
    ]


async def recommend(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    ensure_user(user.id, user.username, user.first_name)
    user_request = " ".join(context.args).strip() if context.args else None
    goal = get_user_goal(user.id)
    history = get_user_lifts(user.id)
    history_serializable = _serialize_history(history)
    await update.message.reply_text(RECOMMEND_LOADING)
    rec = get_workout_recommendation(goal, history_serializable, user_request)
    await update.message.reply_text(rec, parse_mode="Markdown")
    context.user_data["recommend_followup"] = True
    context.user_data["recommend_goal"] = goal
    context.user_data["recommend_history"] = history_serializable
    context.user_data["last_recommendation"] = rec
    await update.message.reply_text(RECOMMEND_REFINE_PROMPT)


async def view(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    ensure_user(user.id, user.username, user.first_name)
    context.user_data.pop("recommend_followup", None)
    lifts = get_user_lifts(user.id)
    if not lifts:
        await update.message.reply_text(VIEW_EMPTY)
        return
    by_date: dict[str, list[dict]] = {}
    for lift in lifts:
        created = lift.get("created_at")
        if created:
            dt = created if isinstance(created, datetime) else datetime.fromisoformat(created.replace("Z", "+00:00"))
            key = dt.strftime("%Y-%m-%d")
        else:
            key = "Unknown"
        if key not in by_date:
            by_date[key] = []
        by_date[key].append(lift)
    unit = get_user_unit(user.id)
    lines = []
    for date in sorted(by_date.keys(), reverse=True):
        lines.append(f"*{date}*")
        for l in by_date[date]:
            ex = l["exercise"]
            s, r, w = l["sets"], l["reps"], float(l["weight"])
            lines.append(f"  • {ex}: {s}x{r} @ {_format_weight(w, unit)}")
        lines.append("")
    text = "\n".join(lines).strip()
    if len(text) > 4000:
        text = text[:3997] + "..."
    await update.message.reply_text(text or "No lifts.", parse_mode="Markdown")


async def recommend_followup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle follow-up messages to refine a recommendation. Only processes when in recommend_followup mode."""
    if not context.user_data.get("recommend_followup"):
        return
    feedback = update.message.text.strip()
    if not feedback:
        return
    prev = context.user_data.get("last_recommendation", "")
    goal = context.user_data.get("recommend_goal")
    history = context.user_data.get("recommend_history", [])
    await update.message.reply_text(RECOMMEND_LOADING)
    rec = refine_recommendation(goal, history, prev, feedback)
    context.user_data["last_recommendation"] = rec
    await update.message.reply_text(rec, parse_mode="Markdown")
    await update.message.reply_text(RECOMMEND_REFINE_PROMPT)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(CANCEL_MESSAGE)
    return ConversationHandler.END
