import asyncio
from database import engine, Base

async def recreate():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("Database recreated with new schema.")

asyncio.run(recreate())
