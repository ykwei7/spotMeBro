import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").strip()
SUPABASE_SERVICE_KEY = (os.getenv("SUPABASE_SERVICE_KEY") or "").strip()


def validate_config():
    """Raise a clear error if required config is missing."""
    if not SUPABASE_URL or not SUPABASE_URL.startswith("https://"):
        raise ValueError(
            "Invalid SUPABASE_URL. Set it in .env to your Supabase project URL, e.g. "
            "https://xxxxxxxxxxxx.supabase.co (from Supabase Dashboard → Project Settings → API)"
        )
    if not SUPABASE_SERVICE_KEY:
        raise ValueError("SUPABASE_SERVICE_KEY is missing. Set it in .env (Project Settings → API → service_role)")
