"""All prompts and user-facing messages."""

# --- LLM prompts (sent to Groq) ---

PARSE_LIFT = """Parse this gym/workout log into structured data. The user may enter ONE or MULTIPLE lifts (comma or newline separated).
Return a JSON ARRAY of objects. Each object has: exercise (string), sets (int), reps (int), weight (float, in lbs). Use null for unknown values.
Single lift: [{"exercise": "Bench Press", "sets": 3, "reps": 5, "weight": 135}]
Multiple: [{"exercise": "Bench Press", "sets": 3, "reps": 5, "weight": 135}, {"exercise": "Squat", "sets": 3, "reps": 5, "weight": 225}]
Examples:
- "Bench 3x5 135, Squat 225x5" -> array of 2 objects
- "Deadlift 1x5 315" -> array of 1 object

User input: """

RECOMMEND_WORKOUT = """You are a fitness coach that provides succint workout recommendations. {base}
The user's fitness goal: {user_goal}
Their recent lift history:
{history_str}

Provide a concise, actionable workout recommendation (3-6 exercises). Include suggested sets, reps, and weight progression if relevant.
IMPORTANT: Do NOT use markdown tables (| pipes) — Telegram does not support them. Instead use this format:
• *Exercise Name* — X sets × Y reps @ Z kg (or lbs)
Example:
• *Squats* — 4 sets × 8-12 reps @ 60-70kg
• *Leg Press* — 3 sets × 10-15 reps @ 80-90kg
Keep it under 400 words. No extra text besides the workout."""

RECOMMEND_BASE_DEFAULT = "Recommend a workout for today."
RECOMMEND_BASE_WITH_REQUEST = 'The user has requested: "{user_request}". Recommend a workout that addresses this request.'
RECOMMEND_HISTORY_EMPTY = "No past lifts recorded."
RECOMMEND_GOAL_NOT_SET = "Not set"
RECOMMEND_ERROR = "Sorry, I couldn't generate a recommendation right now: {error}"

REFINE_RECOMMENDATION = """You are a fitness coach. The user received this workout recommendation and wants to adjust it.

Previous recommendation:
{previous_recommendation}

User's feedback/request: "{user_feedback}"

The user's goal: {user_goal}
Their recent lift history:
{history_str}

Provide an updated workout recommendation that incorporates their feedback.
IMPORTANT: Do NOT use markdown tables (| pipes) — Telegram does not support them. Use bullet points with bold exercise names:
• *Exercise Name* — X sets × Y reps @ Z kg (or lbs)
Under 400 words. No extra text besides the workout."""

# --- Track flow prompts ---

TRACK_START = """Send your lift(s) in free-form. You can log one or multiple at once.
Examples:
• Bench press 3x5 at 135 lbs
• Bench 3x5 135, Squat 3x5 225, Deadlift 1x5 315
• Squat 225 for 5 reps"""

TRACK_FILL = {
    "exercise": "What exercise did you do?",
    "sets": "How many sets?",
    "reps": "How many reps per set?",
    "weight": "What weight (in lbs)?",
}

TRACK_INVALID_EXERCISE = "Please enter a non-empty exercise name."
TRACK_INVALID_SETS_REPS = "Please enter a number between 1 and 100."
TRACK_INVALID_WEIGHT = "Please enter a reasonable weight in lbs (1–2000)."
TRACK_INVALID_GENERIC = "Invalid input. Please enter {hint}."
TRACK_CONFIRM_QUESTION = "Save {count} lift(s)?\n\n*{summary}*"
TRACK_SAVED = "Saved: *{summary}*"
TRACK_SAVED_MULTI = "Saved {count} lift(s)! Send another to log more, or use /view, /recommend, etc."
TRACK_CONTINUE_PROMPT = "Send another lift to log, or use /view, /recommend, etc. to switch."
TRACK_CANCELLED = "Cancelled. No lift saved."

# --- Other bot messages ---

START_MESSAGE = """Hey! I'm Spot Me Bro — your gym tracking buddy.

*Commands:*
/setgoal — Set or change your fitness goal
/setunit — Set weight display (lbs or kg)
/track — Log a lift (free-form or step-by-step)
/recommend — Get a workout suggestion
/view — View your past lifts
/help — Show this help
/cancel — Cancel current action"""

HELP_MESSAGE = """*Spot Me Bro — Commands*

/setgoal — Set or change your fitness goal
/setunit — Set weight display (lbs or kg)
/track — Log a lift (free-form or step-by-step)
/recommend — Get a workout suggestion
/view — View your past lifts
/help — Show this help
/cancel — Cancel current action"""

SETUNIT_USAGE = "Usage: `/setunit lbs` or `/setunit kg`"
SETUNIT_UPDATED = "Weight display set to *{unit}*"

SETGOAL_EXAMPLE = "Set your fitness goal. Example:\n`/setgoal Build strength and add 20 lbs to my bench`"
SETGOAL_UPDATED = "Goal updated: *{goal}*"
VIEW_EMPTY = "No lifts recorded yet. Use /track to log one!"
RECOMMEND_LOADING = "Generating recommendation..."
RECOMMEND_REFINE_PROMPT = "Send feedback to adjust the recommendation (e.g. 'make it shorter', 'swap squats for leg press'). Or use /track, /view, etc. to switch."
CANCEL_MESSAGE = "Cancelled."
