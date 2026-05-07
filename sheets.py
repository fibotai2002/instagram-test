import asyncio
import json
from datetime import datetime
from typing import Optional

import gspread
from google.oauth2.service_account import Credentials

from config import CREDENTIALS_FILE, SHEET_ID, GOOGLE_CREDENTIALS_JSON

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]


def _get_worksheet(sheet_name: str) -> gspread.Worksheet:
    if GOOGLE_CREDENTIALS_JSON:
        # Load from environment variable (JSON string)
        creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    else:
        # Fallback to local file
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID).worksheet(sheet_name)



# Global cache for inventory
_inventory_cache: Optional[str] = None
_last_fetch_time: Optional[datetime] = None
CACHE_TTL_SECONDS = 600  # 10 daqiqa


# ---------------------------------------------------------------------------
# Sync helpers (run in thread pool via asyncio.to_thread)
# ---------------------------------------------------------------------------

def _fetch_inventory_sync() -> str:
    ws = _get_worksheet("Inventory")
    rows = ws.get_all_records()
    if not rows:
        return ""

    lines = ["=== MAVJUD MAHSULOTLAR ==="]
    for row in rows:
        name     = row.get("Item Name", "")
        category = row.get("Category", "")
        price    = row.get("Price", "")
        stock    = row.get("Stock Status", "")
        specs    = row.get("Specs", "")
        lines.append(
            f"- {name} | Kategoriya: {category} | Narx: {price} | "
            f"Mavjudligi: {stock} | Xususiyatlar: {specs}"
        )
    return "\n".join(lines)


def _append_lead_sync(ig_id: str, phone: str, item: str) -> None:
    ws = _get_worksheet("Leads")
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    ws.append_row([date_str, ig_id, phone, item])


# ---------------------------------------------------------------------------
# Async public API
# ---------------------------------------------------------------------------

async def fetch_inventory(force_refresh: bool = False) -> str:
    """Fetch all rows from Inventory worksheet (non-blocking) with caching."""
    global _inventory_cache, _last_fetch_time

    now = datetime.now()
    if not force_refresh and _inventory_cache and _last_fetch_time:
        delta = (now - _last_fetch_time).total_seconds()
        if delta < CACHE_TTL_SECONDS:
            print(f"[Sheets] Inventory keshdan olindi (age={int(delta)}s)")
            return _inventory_cache

    try:
        result = await asyncio.to_thread(_fetch_inventory_sync)
        _inventory_cache = result
        _last_fetch_time = now
        product_count = result.count("- ")
        print(f"[Sheets] Inventory yuklandi: {product_count} ta mahsulot")
        return result
    except FileNotFoundError:
        print("[Sheets] credentials.json topilmadi!")
        return ""
    except gspread.exceptions.SpreadsheetNotFound:
        print("[Sheets] Google Sheet topilmadi. SHEET_ID ni tekshiring.")
        return ""
    except Exception as e:
        print(f"[Sheets] Inventory xato: {e}")
        return _inventory_cache or ""


async def append_lead(ig_id: str, phone: str, item: str) -> None:
    """Append a new lead row to the Leads worksheet (non-blocking)."""
    try:
        await asyncio.to_thread(_append_lead_sync, ig_id, phone, item)
        print(f"[Sheets] Lead saqlandi -> IG: {ig_id} | Tel: {phone} | Mahsulot: {item}")
    except Exception as e:
        print(f"[Sheets] Lead saqlashda xato: {e}")
