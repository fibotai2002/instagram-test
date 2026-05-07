import asyncio
import httpx
import logging
from config import TELEGRAM_BOT_TOKEN

logger = logging.getLogger("arzonchi-bot.telegram")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
TELEGRAM_FILE_URL = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}"


async def send_message(chat_id: str | int, text: str) -> None:
    """Send text message to Telegram user."""
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("[Telegram] Token yo'q, xabar yuborilmadi.")
        return

    if not text.strip():
        return

    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"  # Or HTML depending on your need
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            logger.info(f"[Telegram] Xabar yuborildi -> {chat_id}")
    except Exception as e:
        logger.error(f"[Telegram] Xabar yuborishda xato: {e}")


async def get_file_url(file_id: str) -> str | None:
    """Get the direct download URL for a Telegram file/photo."""
    if not TELEGRAM_BOT_TOKEN:
        return None

    url = f"{TELEGRAM_API_URL}/getFile"
    payload = {"file_id": file_id}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            if data.get("ok"):
                file_path = data["result"]["file_path"]
                return f"{TELEGRAM_FILE_URL}/{file_path}"
            else:
                logger.error(f"[Telegram] getFile xatosi: {data}")
                return None
    except Exception as e:
        logger.error(f"[Telegram] File o'qishda xato: {e}")
        return None
