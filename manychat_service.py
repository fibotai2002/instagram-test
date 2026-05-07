import asyncio
import httpx
from config import MANYCHAT_API_TOKEN, MANYCHAT_API_URL
import logging

logger = logging.getLogger("arzonchi-bot.manychat")

# ManyChat generally supports 2000 characters per text block,
# but we will keep it safe around 1000 characters.
MAX_MSG_LEN = 1000

async def _send_single(subscriber_id: str, text: str) -> None:
    """Send one message chunk to ManyChat subscriber."""
    payload = {
        "subscriber_id": subscriber_id,
        "data": {
            "version": "v2",
            "content": {
                "messages": [
                    {
                        "type": "text",
                        "text": text
                    }
                ]
            }
        },
        "message_tag": "ACCOUNT_UPDATE"
    }
    
    headers = {
        "Authorization": f"Bearer {MANYCHAT_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            MANYCHAT_API_URL,
            json=payload,
            headers=headers
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

async def send_message(subscriber_id: str, text: str) -> None:
    """Send a message to ManyChat subscriber, splitting if over MAX_MSG_LEN."""
    if not text.strip():
        return

    chunks = _split_text(text)
    total = len(chunks)

    for i, chunk in enumerate(chunks, 1):
        try:
            await _send_single(subscriber_id, chunk)
            logger.info(f"[ManyChat] Xabar yuborildi -> {subscriber_id} ({i}/{total})")
            if total > 1 and i < total:
                await asyncio.sleep(0.5)  # Throttle between chunks
        except httpx.HTTPStatusError as e:
            logger.error(f"[ManyChat] HTTP xato {e.response.status_code}: {e.response.text}")
            break
        except httpx.TimeoutException:
            logger.error(f"[ManyChat] Timeout xatosi -> {subscriber_id}")
            break
        except Exception as e:
            logger.error(f"[ManyChat] Xabar yuborishda xato: {e}")
            break
