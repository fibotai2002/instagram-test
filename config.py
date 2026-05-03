import os
import json
from dotenv import load_dotenv

load_dotenv()


def _require(key: str, default: str = None) -> str:
    value = os.environ.get(key, default)
    if not value:
        raise RuntimeError(f"Muhit o'zgaruvchisi topilmadi: {key}  (.env faylini tekshiring)")
    return value


META_ACCESS_TOKEN: str = _require("META_ACCESS_TOKEN")
VERIFY_TOKEN: str      = _require("VERIFY_TOKEN")
GEMINI_API_KEY: str    = _require("GEMINI_API_KEY")
SHEET_ID: str          = _require("SHEET_ID")

# PostgreSQL URL on Render, default to SQLite for local development
DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./arzonchi.db")

# Google Credentials from JSON string (Env Var)
GOOGLE_CREDENTIALS_JSON: str = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")

META_API_URL     = "https://graph.facebook.com/v19.0/me/messages"
CREDENTIALS_FILE = "credentials.json"

