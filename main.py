from contextlib import asynccontextmanager
from typing import Optional

import uvicorn
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

from gemini_service import ask_gemini, clear_session
import telegram_service
from sqlalchemy import select, func, cast, Date
from pydantic import BaseModel
from database import init_db, AsyncSessionLocal, User, MessageLog, Lead, Config, Product, Admin
import logging
import jwt
import datetime
from passlib.context import CryptContext

SECRET_KEY = "arzonchi_super_secret_key_2026"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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
            
        admin_res = await db.execute(select(Admin).limit(1))
        first_admin = admin_res.scalar_one_or_none()
        hashed_pwd = pwd_context.hash("2222")
        
        if not first_admin:
            db.add(Admin(username="Fibot", hashed_password=hashed_pwd))
            await db.commit()
            logger.info("[Startup] Default admin yaratildi (Fibot / 2222)")
        else:
            first_admin.username = "Fibot"
            first_admin.hashed_password = hashed_pwd
            await db.commit()
            logger.info("[Startup] Admin paroli Fibot / 2222 qilib yangilandi")
            
        prod_count = await db.execute(select(func.count(Product.id)))
        logger.info(f"[Startup] Baza (Sklad) ulandi ✓ ({prod_count.scalar()} ta mahsulot)")

    logger.info("[Startup] Bot tayyor ✓")

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
# POST /api/chat — Generic endpoint for testing or other frontend
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    user_id: str
    text: Optional[str] = None
    image_url: Optional[str] = None

@app.post("/api/chat")
async def receive_chat(payload: ChatMessage):
    logger.info(f"[API Chat] Yangi xabar | sender={payload.user_id} | text={repr(payload.text)}")
    
    if not payload.text and not payload.image_url:
        return {"status": "ignored", "reply": ""}

    reply_text = await _process_message_inner(
        sender_id=payload.user_id,
        user_text=payload.text,
        image_url=payload.image_url,
    )

    return {"status": "ok", "reply": reply_text}


# ---------------------------------------------------------------------------
# POST /telegram/webhook — Incoming Telegram Request
# ---------------------------------------------------------------------------

@app.post("/telegram/webhook")
async def receive_telegram(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    logger.info(f"[Telegram Webhook] Yangi update: {data.get('update_id')}")

    if "message" not in data:
        return {"status": "ok"}

    msg = data["message"]
    chat_id = str(msg["chat"]["id"])
    text = msg.get("text", "")
    
    # Rasm kelgan bo'lsa
    image_url = None
    if "photo" in msg:
        # Eng katta rasmni olish (oxirgisi)
        photo_id = msg["photo"][-1]["file_id"]
        image_url = await telegram_service.get_file_url(photo_id)
        if not text:
            text = msg.get("caption", "")

    if not text and not image_url:
        return {"status": "ignored"}

    # Telegram uchun orqa fonda ishlash kerak, aks holda telegram qayta-qayta jo'natadi
    background_tasks.add_task(
        process_telegram_message,
        sender_id=chat_id,
        user_text=text,
        image_url=image_url
    )
    return {"status": "ok"}


async def process_telegram_message(sender_id: str, user_text: str, image_url: str):
    try:
        reply_text = await _process_message_inner(sender_id, user_text, image_url)
        if reply_text:
            await telegram_service.send_message(sender_id, reply_text)
    except Exception as e:
        logger.error(f"[Telegram Pipeline] Xato: {e}", exc_info=True)


# ---------------------------------------------------------------------------
# Background pipeline (Core)
# ---------------------------------------------------------------------------

async def fetch_inventory_db(db) -> str:
    stmt = select(Product).order_by(Product.id)
    result = await db.execute(stmt)
    products = result.scalars().all()
    if not products:
        return ""
    
    lines = ["=== MAVJUD MAHSULOTLAR ==="]
    for p in products:
        lines.append(
            f"- {p.name} | Kategoriya: {p.category} | Narx: {p.price} | "
            f"Mavjudligi: {p.stock} ta | Xususiyatlar: {p.specs}"
        )
    return "\n".join(lines)


async def _process_message_inner(
    sender_id: str,
    user_text: Optional[str],
    image_url: Optional[str],
) -> str:
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

        # 1. Oldingi xabarlar tarixini olish (oxirgi 10 ta)
        history_stmt = select(MessageLog).where(MessageLog.user_id == sender_id).order_by(MessageLog.id.desc()).limit(10)
        history_res = await db.execute(history_stmt)
        history_logs = list(reversed(history_res.scalars().all()))
        chat_history = [{"role": log.role, "content": log.content} for log in history_logs]

        # 2. Foydalanuvchi joriy xabarini bazaga saqlash
        if user_text:
            db.add(MessageLog(user_id=sender_id, role="user", content=user_text))
            await db.commit()

        # 3. Sozlamalarni bazadan olish
        config_res = await db.execute(select(Config))
        config_data = {c.key: c.value for c in config_res.scalars().all()}

        # 4. Inventory (Baza orqali)
        inventory_context = await fetch_inventory_db(db)

        # 5. Gemini'ga yuborish
        reply_text, lead = await ask_gemini(
            user_id=sender_id,
            user_text=user_text,
            image_url=image_url,
            inventory_context=inventory_context,
            config=config_data,
            chat_history=chat_history
        )

        # 6. Lead topilgan bo'lsa — DB'ga yozish
        if lead and lead.get("lead_captured"):
            phone = lead.get("phone", "")
            item  = lead.get("item", "noma'lum")
            
            # Telegram webhookdan kelganda source "telegram" bo'ladi, aks holda default
            source = "telegram" 

            logger.info(f"[Pipeline] Lead saqlandi (DB): {phone} | {item}")

            db.add(Lead(user_id=sender_id, phone=phone, item=item, source=source))
            await db.commit()

            clear_session(sender_id)

        # 7. Javobni log qilish va yuborish
        if reply_text:
            db.add(MessageLog(user_id=sender_id, role="assistant", content=reply_text))
            await db.commit()

    logger.info(f"[Pipeline] ✓ Yakunlandi -> {sender_id}")
    return reply_text or ""


# ---------------------------------------------------------------------------
# Dashboard Models & API Endpoints
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/admin/login")
async def admin_login(req: LoginRequest):
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Admin).where(Admin.username == req.username))
        admin = res.scalar_one_or_none()
        if not admin or not pwd_context.verify(req.password, admin.hashed_password):
            raise HTTPException(status_code=401, detail="Noto'g'ri login yoki parol")
            
        token = jwt.encode(
            {"sub": admin.username, "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)},
            SECRET_KEY,
            algorithm="HS256"
        )
        return {"token": token}

class ProductCreate(BaseModel):
    name: str
    category: str = "Boshqa"
    price: str = ""
    stock: int = 0
    specs: str = ""
    image_url: Optional[str] = None

class ProductUpdate(ProductCreate):
    pass

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


@app.get("/api/products")
async def get_products():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Product).order_by(Product.id.desc()))
        return result.scalars().all()

@app.post("/api/products")
async def create_product(data: ProductCreate):
    async with AsyncSessionLocal() as db:
        new_prod = Product(**data.model_dump())
        db.add(new_prod)
        await db.commit()
        await db.refresh(new_prod)
        return new_prod

@app.put("/api/products/{prod_id}")
async def update_product(prod_id: int, data: ProductUpdate):
    async with AsyncSessionLocal() as db:
        prod = await db.get(Product, prod_id)
        if not prod:
            raise HTTPException(status_code=404, detail="Mahsulot topilmadi")
        for k, v in data.model_dump().items():
            setattr(prod, k, v)
        await db.commit()
        await db.refresh(prod)
        return prod

@app.delete("/api/products/{prod_id}")
async def delete_product(prod_id: int):
    async with AsyncSessionLocal() as db:
        prod = await db.get(Product, prod_id)
        if not prod:
            raise HTTPException(status_code=404, detail="Mahsulot topilmadi")
        await db.delete(prod)
        await db.commit()
        return {"status": "deleted"}


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
