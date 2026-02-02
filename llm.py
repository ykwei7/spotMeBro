import json
from typing import Optional

from groq import Groq

from config import GROQ_API_KEY
from prompts import (
    PARSE_LIFT,
    RECOMMEND_BASE_DEFAULT,
    RECOMMEND_BASE_WITH_REQUEST,
    RECOMMEND_ERROR,
    RECOMMEND_GOAL_NOT_SET,
    RECOMMEND_HISTORY_EMPTY,
    RECOMMEND_WORKOUT,
    REFINE_RECOMMENDATION,
)


def _get_client() -> Groq:
    return Groq(api_key=GROQ_API_KEY)


def parse_lift_text(text: str):
    """Parse free-form lift text. Returns list of dicts with exercise, sets, reps, weight (or empty list)."""
    client = _get_client()
    prompt = PARSE_LIFT + text
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        data = json.loads(content)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return [data]
        return []
    except Exception:
        return []


def get_workout_recommendation(
    user_goal: Optional[str], lift_history: list, user_request: Optional[str] = None
) -> str:
    """Generate a workout recommendation based on goal, history, and optional user request."""
    client = _get_client()
    history_str = RECOMMEND_HISTORY_EMPTY if not lift_history else json.dumps(lift_history[-20:], indent=2)
    base = RECOMMEND_BASE_WITH_REQUEST.format(user_request=user_request) if user_request else RECOMMEND_BASE_DEFAULT
    prompt = RECOMMEND_WORKOUT.format(
        base=base,
        user_goal=user_goal or RECOMMEND_GOAL_NOT_SET,
        history_str=history_str,
    )
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return RECOMMEND_ERROR.format(error=e)


def refine_recommendation(
    user_goal: Optional[str],
    lift_history: list,
    previous_recommendation: str,
    user_feedback: str,
) -> str:
    """Refine a previous recommendation based on user feedback."""
    client = _get_client()
    history_str = RECOMMEND_HISTORY_EMPTY if not lift_history else json.dumps(lift_history[-20:], indent=2)
    prompt = REFINE_RECOMMENDATION.format(
        previous_recommendation=previous_recommendation,
        user_feedback=user_feedback,
        user_goal=user_goal or RECOMMEND_GOAL_NOT_SET,
        history_str=history_str,
    )
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return RECOMMEND_ERROR.format(error=e)
