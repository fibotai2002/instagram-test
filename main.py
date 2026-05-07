from contextlib import asynccontextmanager
from typing import Optional

import uvicorn
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

# from sheets import fetch_inventory, append_lead

from gemini_service import ask_gemini, clear_session
from manychat_service import send_message
from sqlalchemy import select, func, cast, Date
from pydantic import BaseModel
from database import init_db, AsyncSessionLocal, User, MessageLog, Lead, Config
import logging


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("arzonchi-bot")


# ---------------------------------------------------------------------------
# Startup / Shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 50)
    logger.info("[Startup] Arzonchi Instagram Bot ishga tushdi")

    await init_db()
    logger.info("[Startup] SQLite ma'lumotlar bazasi tayyor ✓")

    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Config).where(Config.key == "shop_name"))
        if not res.scalar():
            defaults = [
                Config(key="shop_name", value="Arzonchi Maishiy Texnika"),
                Config(key="bot_tone", value="Insondek, qisqa va samimiy"),
                Config(key="delivery_info", value="O'zbekiston bo'ylab 24 soat ichida"),
                Config(key="language", value="O'zbek"),
            ]
            db.add_all(defaults)
            await db.commit()
            logger.info("[Startup] Boshlang'ich sozlamalar yuklandi ✓")

    # inv = await fetch_inventory()
    # count = inv.count("- ")
    # logger.info(f"[Startup] Google Sheets ulandi ✓ ({count} ta mahsulot)")
    logger.info("[Startup] Bot tayyor ✓ (Sheets vaqtincha o'chirilgan)")

    logger.info("=" * 50)
    yield
    logger.info("[Shutdown] Bot to'xtatildi")


app = FastAPI(title="Arzonchi Instagram Bot", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# POST /manychat — Incoming ManyChat External Request
# ---------------------------------------------------------------------------

class ManyChatWebhook(BaseModel):
    subscriber_id: str
    user_text: Optional[str] = None
    image_url: Optional[str] = None

@app.post("/manychat")
async def receive_manychat(payload: ManyChatWebhook, background_tasks: BackgroundTasks):
    logger.info(f"[ManyChat Webhook] Yangi xabar | sender={payload.subscriber_id} | text={repr(payload.user_text)}")
    
    if not payload.user_text and not payload.image_url:
        logger.debug(f"[ManyChat Webhook] Bo'sh xabar — o'tkazildi | sender={payload.subscriber_id}")
        return {"status": "ignored"}

    background_tasks.add_task(
        process_message,
        sender_id=payload.subscriber_id,
        user_text=payload.user_text,
        image_url=payload.image_url,
    )

    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Background pipeline
# ---------------------------------------------------------------------------

async def process_message(
    sender_id: str,
    user_text: Optional[str],
    image_url: Optional[str],
) -> None:
    try:
        await _process_message_inner(sender_id, user_text, image_url)
    except Exception as e:
        logger.error(f"[Pipeline] ✗ Kritik xato ({sender_id}): {e}", exc_info=True)


async def _process_message_inner(
    sender_id: str,
    user_text: Optional[str],
    image_url: Optional[str],
) -> None:
    logger.info(f"[Pipeline] ▶ Boshlandi -> {sender_id}")

    async with AsyncSessionLocal() as db:
        # 0. Foydalanuvchini bazada tekshirish/yaratish
        stmt = select(User).where(User.id == sender_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            user = User(id=sender_id)
            db.add(user)
            await db.commit()

        # 1. Foydalanuvchi xabarini log qilish
        if user_text:
            db.add(MessageLog(user_id=sender_id, role="user", content=user_text))
            await db.commit()

        # 2. Sozlamalarni bazadan olish
        config_res = await db.execute(select(Config))
        config_data = {c.key: c.value for c in config_res.scalars().all()}

        # 3. Inventory (Vaqtincha qo'lda yozilgan)
        inventory_context = """
=== MAVJUD MAHSULOTLAR ===
- iPhone 15 Pro | Narx: 1200$ | Mavjud: Ha
- Samsung S24 Ultra | Narx: 1100$ | Mavjud: Ha
- MacBook Air M3 | Narx: 1300$ | Mavjud: Ha
"""


        # 4. Gemini'ga yuborish
        reply_text, lead = await ask_gemini(
            user_id=sender_id,
            user_text=user_text,
            image_url=image_url,
            inventory_context=inventory_context,
            config=config_data,
        )

        # 5. Lead topilgan bo'lsa — Sheets'ga va DB'ga yozish
        if lead and lead.get("lead_captured"):
            phone = lead.get("phone", "")
            item  = lead.get("item", "noma'lum")

            # await append_lead(ig_id=sender_id, phone=phone, item=item)
            logger.info(f"[Pipeline] Lead saqlandi (Faqat DB): {phone} | {item}")


            db.add(Lead(user_id=sender_id, phone=phone, item=item))
            await db.commit()

            clear_session(sender_id)

        # 6. Javobni log qilish va yuborish
        if reply_text:
            db.add(MessageLog(user_id=sender_id, role="assistant", content=reply_text))
            await db.commit()
            await send_message(recipient_id=sender_id, text=reply_text)

    logger.info(f"[Pipeline] ✓ Yakunlandi -> {sender_id}")


# ---------------------------------------------------------------------------
# Dashboard Models & API Endpoints
# ---------------------------------------------------------------------------

class LeadUpdate(BaseModel):
    status: str

class ConfigUpdate(BaseModel):
    # Dynamic config update
    pass

@app.get("/api/stats")
async def get_stats():
    async with AsyncSessionLocal() as db:
        leads_count = await db.execute(select(func.count(Lead.id)))
        users_count = await db.execute(select(func.count(User.id)))
        msgs_count  = await db.execute(select(func.count(MessageLog.id)))

        daily = await db.execute(
            select(
                cast(Lead.created_at, Date).label("date"),
                func.count(Lead.id).label("count"),
            )
            .group_by(cast(Lead.created_at, Date))
            .order_by(cast(Lead.created_at, Date).desc())
            .limit(7)
        )
        daily_leads = [{"date": str(r.date), "count": r.count} for r in daily]

        return {
            "total_leads":    leads_count.scalar() or 0,
            "total_users":    users_count.scalar() or 0,
            "total_messages": msgs_count.scalar() or 0,
            "daily_leads":    list(reversed(daily_leads)),
        }


@app.get("/health")
async def health_check():
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(select(Config).limit(1))
        db_ok = True
    except Exception:
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "db": "ok" if db_ok else "error"}


@app.get("/api/leads")
async def get_leads():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Lead).order_by(Lead.created_at.desc()))
        leads = result.scalars().all()
        return leads


@app.patch("/api/leads/{lead_id}")
async def update_lead_status(lead_id: int, payload: LeadUpdate):
    status = payload.status
    if status not in ("yangi", "qo'ng'iroq_qilindi", "yakunlandi"):
        raise HTTPException(status_code=400, detail="Noto'g'ri status")
    async with AsyncSessionLocal() as db:
        lead = await db.get(Lead, lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead topilmadi")
        lead.status = status
        await db.commit()
        return {"id": lead_id, "status": status}


@app.get("/api/users")
async def get_users():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).order_by(User.created_at.desc()))
        users = result.scalars().all()
        return users


@app.get("/api/messages")
async def get_messages(user_id: str | None = None):
    async with AsyncSessionLocal() as db:
        stmt = select(MessageLog).order_by(MessageLog.created_at.asc())
        if user_id:
            stmt = stmt.where(MessageLog.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalars().all()


@app.get("/api/config")
async def get_config():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Config))
        configs = result.scalars().all()
        return {c.key: c.value for c in configs}


@app.post("/api/config")
async def update_config(data: dict):
    async with AsyncSessionLocal() as db:
        for key, value in data.items():
            config = await db.get(Config, key)
            if config:
                config.value = str(value)
            else:
                db.add(Config(key=key, value=str(value)))
        await db.commit()
    return {"status": "updated"}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
