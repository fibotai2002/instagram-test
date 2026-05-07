import asyncio
from gemini_service import ask_gemini
import config

async def test():
    config_dict = {"shop_name": "Test", "bot_tone": "Samimiy"}
    try:
        reply, lead = await ask_gemini("user_test", "Salom, telefonlar bormi?", None, "iPhone 15", config_dict, [])
        print("Reply:", reply)
    except Exception as e:
        print("Error:", e)

asyncio.run(test())
