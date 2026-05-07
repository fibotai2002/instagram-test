import os
import json
from dotenv import load_dotenv

load_dotenv()


def _require(key: str, default: str = None) -> str:
    value = os.environ.get(key, default)
    if not value:
        raise RuntimeError(f"Muhit o'zgaruvchisi topilmadi: {key}  (.env faylini tekshiring)")
    return value


GEMINI_API_KEY: str    = _require("GEMINI_API_KEY")
SHEET_ID: str          = os.environ.get("SHEET_ID", "")
TELEGRAM_BOT_TOKEN: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")

# PostgreSQL URL on Render, default to SQLite for local development
DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./arzonchi.db")

# Google Credentials from JSON string (Env Var)
GOOGLE_CREDENTIALS_JSON: str = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")

MANYCHAT_API_URL = "https://api.manychat.com/fb/sending/sendContent"
CREDENTIALS_FILE = "credentials.json"

