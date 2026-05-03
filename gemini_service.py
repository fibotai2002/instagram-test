import json
import re
import io
import asyncio
from typing import Optional, Tuple, Dict

import httpx
import PIL.Image
import google.generativeai as genai

from config import GEMINI_API_KEY

import logging

genai.configure(api_key=GEMINI_API_KEY)
logger = logging.getLogger("arzonchi-bot.gemini")

def _get_model(system_instruction: str):
    return genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=system_instruction,
    )

# Per-user chat sessions stored in memory.
_sessions: Dict[str, genai.ChatSession] = {}
_last_instruction: Dict[str, str] = {}

def _get_session(user_id: str, system_instruction: str) -> genai.ChatSession:
    if user_id not in _sessions or _last_instruction.get(user_id) != system_instruction:
        model = _get_model(system_instruction)
        _sessions[user_id] = model.start_chat(history=[])
        _last_instruction[user_id] = system_instruction
        logger.info(f"[Gemini] Yangi sessiya: {user_id}")
    return _sessions[user_id]


def _parse_lead(text: str) -> Tuple[Optional[Dict], str]:
    """Extract JSON lead block from response. Returns (lead_dict, clean_text)."""
    pattern = r'\{\s*"lead_captured"\s*:\s*true.*?\}'
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        return None, text
    try:
        lead = json.loads(match.group())
        clean_text = text[: match.start()].rstrip()
        return lead, clean_text
    except json.JSONDecodeError:
        logger.error(f"[Gemini] JSON parse xatosi: {match.group()}")
        return None, text


async def _download_image(url: str) -> bytes:
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content


def _open_image(image_bytes: bytes) -> PIL.Image.Image:
    return PIL.Image.open(io.BytesIO(image_bytes))


async def ask_gemini(
    user_id: str,
    user_text: Optional[str],
    image_url: Optional[str],
    inventory_context: str,
    config: dict,
) -> Tuple[str, Optional[dict]]:
    """Send user message to Gemini with dynamic system prompt."""
    shop_name = config.get("shop_name", "Do'kon")
    tone = config.get("bot_tone", "Do'stona")
    delivery = config.get("delivery_info", "Mavjud")
    lang = config.get("language", "O'zbek")

    dynamic_prompt = f"""Sen "{shop_name}" do'konining xodimi Sardorsan.
Suhbat uslubing: {tone}. Insondek gapir, AI ekanligingni aytma.
Javoblaring qisqa, lunda va samimiy bo'lsin.
Til: {lang}.
Yetkazib berish: {delivery}.

Qoidalaring:
1. Insondek tabiiy salomlash.
2. FAQAT [Inventory Context] asosida javob ber. Agar ma'lumot bo'lmasa, muloyimlik bilan tushuntir.
3. Uzun matnlar yozma, xuddi messenjerda yozishayotgandek qisqa javob ber.
4. Foydalanuvchi rasm yuborsa, unga e'tibor ber va inventar bilan solishtir.
5. Telefon raqam bersa, javob oxiriga FAQAT ushbu JSONni qo'sh:
{{"lead_captured": true, "phone": "+998XXXXXXXXX", "item": "mahsulot_nomi"}}
"""

    session = _get_session(user_id, dynamic_prompt)

    message_text = (
        f"[Inventory Context]\n{inventory_context}\n\n"
        f"[Foydalanuvchi xabari]\n{user_text or '(rasm yubordi)'}"
    )
    parts: list = [message_text]

    if image_url:
        try:
            logger.info(f"[Gemini] Rasm yuklanmoqda...")
            image_bytes = await _download_image(image_url)
            img = await asyncio.to_thread(_open_image, image_bytes)
            parts.append(img)
            logger.info(f"[Gemini] Rasm tayyor ({len(image_bytes) // 1024} KB)")
        except Exception as e:
            logger.error(f"[Gemini] Rasm yuklab bo'lmadi: {e}")
            parts.append("(Foydalanuvchi rasm yubordi, lekin yuklab bo'lmadi.)")

    try:
        logger.info(f"[Gemini] So'rov yuborilmoqda (user={user_id})...")
        response = await session.send_message_async(parts)
        raw_text = response.text
        logger.info(f"[Gemini] Javob keldi: {len(raw_text)} belgi")

        lead, clean_text = _parse_lead(raw_text)
        if lead:
            logger.info(f"[Gemini] Lead aniqlandi: {lead}")
        return clean_text, lead

    except Exception as e:
        logger.error(f"[Gemini] Xato: {e}", exc_info=True)
        _sessions.pop(user_id, None)
        return "Kechirasiz, hozir texnik muammo bor. Iltimos, bir oz kutib qayta yozing.", None


def clear_session(user_id: str) -> None:
    """Reset conversation history for a user (e.g., after lead capture)."""
    _sessions.pop(user_id, None)
    logger.info(f"[Gemini] Sessiya tozalandi: {user_id}")
