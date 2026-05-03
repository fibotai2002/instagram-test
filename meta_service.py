import asyncio
import httpx
import httpx
from config import META_ACCESS_TOKEN, META_API_URL
import logging

logger = logging.getLogger("arzonchi-bot.meta")

# Instagram DM has a 1000-character limit per message
MAX_MSG_LEN = 1000


async def _send_single(recipient_id: str, text: str) -> None:
    """Send one message chunk to Instagram user."""
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text},
        "messaging_type": "RESPONSE",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            META_API_URL,
            json=payload,
            params={"access_token": META_ACCESS_TOKEN},
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()


def _split_text(text: str, max_len: int = MAX_MSG_LEN) -> list[str]:
    """Split text into chunks without cutting words."""
    if len(text) <= max_len:
        return [text]

    chunks: list[str] = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        # Try to cut at last newline or space within limit
        cut = text.rfind("\n", 0, max_len)
        if cut == -1:
            cut = text.rfind(" ", 0, max_len)
        if cut == -1:
            cut = max_len
        chunks.append(text[:cut].rstrip())
        text = text[cut:].lstrip()
    return chunks


async def send_message(recipient_id: str, text: str) -> None:
    """Send a message to Instagram user, splitting if over MAX_MSG_LEN."""
    if not text.strip():
        return

    chunks = _split_text(text)
    total = len(chunks)

    for i, chunk in enumerate(chunks, 1):
        try:
            await _send_single(recipient_id, chunk)
            logger.info(f"[Meta] Xabar yuborildi -> {recipient_id} ({i}/{total})")
            if total > 1 and i < total:
                await asyncio.sleep(0.5)  # Throttle between chunks
        except httpx.HTTPStatusError as e:
            logger.error(f"[Meta] HTTP xato {e.response.status_code}: {e.response.text}")
            break
        except httpx.TimeoutException:
            print(f"[Meta] Timeout xatosi -> {recipient_id}")
            break
        except Exception as e:
            print(f"[Meta] Xabar yuborishda xato: {e}")
            break
