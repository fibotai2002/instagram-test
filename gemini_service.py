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

def _get_session(user_id: str, system_instruction: str, db_history: list) -> genai.ChatSession:
    if user_id not in _sessions or _last_instruction.get(user_id) != system_instruction:
        model = _get_model(system_instruction)
        
        gemini_history = []
        for log in db_history:
            # Gemini faqat 'user' va 'model' rollarini qabul qiladi
            role = "user" if log["role"] == "user" else "model"
            # Agar kontent bo'lmasa, uni qo'shmaslik kerak
            if log["content"]:
                gemini_history.append({"role": role, "parts": [log["content"]]})

        _sessions[user_id] = model.start_chat(history=gemini_history)
        _last_instruction[user_id] = system_instruction
        logger.info(f"[Gemini] Yangi sessiya (Tarix: {len(gemini_history)} ta xabar): {user_id}")
    return _sessions[user_id]


def _parse_lead(text: str) -> Tuple[Optional[Dict], str]:
    """Extract JSON lead block from response. Returns (lead_dict, clean_text)."""
    # Regex: Ochiq qavsdan boshlab oxirgi qavsgacha yoki markdown bo'lsa uni ushlash
    pattern = r'\{[\s\S]*?"lead_captured"\s*:\s*true[\s\S]*?\}'
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if not match:
        return None, text
    
    json_str = match.group(0)
    try:
        lead = json.loads(json_str)
        # JSON'ni va markdown qoldiqlarini o'chirish (masalan: ```json, ```)
        clean_text = text.replace(json_str, "").replace("```json", "").replace("```", "").strip()
        return lead, clean_text
    except json.JSONDecodeError:
        logger.error(f"[Gemini] JSON parse xatosi: {json_str}")
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
    chat_history: list = None,
) -> Tuple[str, Optional[dict]]:
    """Send user message to Gemini with dynamic system prompt."""
    if chat_history is None:
        chat_history = []
        
    shop_name = config.get("shop_name", "Do'kon")
    tone = config.get("bot_tone", "G'amxo'r, do'stona va lunda")
    delivery = config.get("delivery_info", "Mavjud")
    lang = config.get("language", "O'zbek")

    dynamic_prompt = f"""Sen "{shop_name}" do'konining tajribali, g'amxo'r va xushmuomala xodimisan.
Suhbat uslubing: {tone}. Mijoz bilan Instagram/Telegram kabi ijtimoiy tarmoqda yozishayapsan.
Aslo AI yoki bot ekanligingni aytma, inson xodimdek harakat qil.
Til: {lang}. Yetkazib berish: {delivery}.

Qoidalaring:
1. QISQA VA LUNDA Yoz! Uzun xatboshilar va keraksiz jumlalardan qoch. Har bir xabar 1-2 gapdan iborat bo'lsin.
2. Empoatiya va Tabiiylik: Joyida munosib emojilardan foydalan (😊, ✅, 🚚). Quruq javob o'rniga muloyim gapir.
3. INVENTAR (Baza): FAQAT [Inventory Context] asosida javob ber. Mijoz nima xohlayotganini qiziqib so'ra (qaysi rangi, xotirasi...).
4. LEAD YIG'ISH (Tabiiy): To'g'ridan-to'g'ri raqam so'rama! Mahsulot haqida ma'lumot berib, keyin tabiiy tarzda: "Buyurtma berish uchun yoki menejerimiz bog'lanishi uchun raqamingizni yozib qoldirishingiz mumkin" deb taklif qil.
5. JSON QAYTARISH: QACHONKI mijoz o'z telefon raqamini yozsa (+998 bilan yoki boshqa formatda), javobingning eng oxiriga FAQAT quyidagi JSON'ni qo'sh.
{{"lead_captured": true, "phone": "+998XXXXXXXXX", "item": "mahsulot_nomi"}}
Boshqa holatda JSON qaytarma!"""

    session = _get_session(user_id, dynamic_prompt, db_history=chat_history)

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
