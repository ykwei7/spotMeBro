from datetime import datetime, timezone
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY
from typing import Optional

_client: Optional[Client] = None


def get_db() -> Client:
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _client


def ensure_user(user_id: int, username: Optional[str] = None, first_name: Optional[str] = None) -> None:
    """Ensure user exists; create if not, update name fields if yes (without overwriting goal)."""
    db = get_db()
    existing = db.table("users").select("id").eq("id", user_id).execute()
    if not existing.data:
        db.table("users").insert({"id": user_id, "username": username, "first_name": first_name}).execute()
    else:
        db.table("users").update({"username": username, "first_name": first_name}).eq("id", user_id).execute()


def set_user_goal(user_id: int, goal: str) -> None:
    db = get_db()
    db.table("users").update({"goal": goal, "updated_at": datetime.now(timezone.utc).isoformat()}).eq("id", user_id).execute()


def get_user_goal(user_id: int) -> Optional[str]:
    db = get_db()
    result = db.table("users").select("goal").eq("id", user_id).execute()
    if result.data and len(result.data) > 0:
        return result.data[0].get("goal")
    return None


def get_user_unit(user_id: int) -> str:
    """Returns 'lbs' or 'kg'. Defaults to 'lbs'."""
    db = get_db()
    result = db.table("users").select("weight_unit").eq("id", user_id).execute()
    if result.data and len(result.data) > 0:
        unit = result.data[0].get("weight_unit")
        if unit in ("lbs", "kg"):
            return unit
    return "lbs"


def set_user_unit(user_id: int, unit: str) -> None:
    """Set weight_unit to 'lbs' or 'kg'."""
    if unit not in ("lbs", "kg"):
        raise ValueError("Unit must be 'lbs' or 'kg'")
    db = get_db()
    db.table("users").update({"weight_unit": unit}).eq("id", user_id).execute()


def insert_lift(user_id: int, exercise: str, sets: int, reps: int, weight: float, notes: Optional[str] = None) -> None:
    db = get_db()
    db.table("lifts").insert(
        {
            "user_id": user_id,
            "exercise": exercise,
            "sets": sets,
            "reps": reps,
            "weight": weight,
            "notes": notes,
        }
    ).execute()


def get_user_lifts(user_id: int, limit: int = 100) -> list[dict]:
    db = get_db()
    result = db.table("lifts").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
    return result.data or []
