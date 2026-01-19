# main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from runtime import Runtime
from config import load_config
from services.firebase import init_firebase
from services.groq_service import init_groq
from services.whisper_service import init_whisper
from handlers.common import register_common_handlers
from handlers.audio import register_audio_handlers

logging.basicConfig(level=logging.INFO)

rt = Runtime()
config = load_config()

async def start_bot():
    if rt.is_running:
        return
    rt.loop = asyncio.get_event_loop()
    rt.bot = Bot(token=config["BOT_TOKEN"])
    rt.dp = Dispatcher(rt.bot)

    # Services
    db = init_firebase(config["FIREBASE_CONF"])
    groq_client = init_groq(config["GROQ_API_KEY"])
    whisper_model = init_whisper()

    services = {"db": db, "groq": groq_client, "whisper": whisper_model}

    await register_common_handlers(rt.dp, rt, config, db)
    await register_audio_handlers(rt.dp, rt, config, services)

    rt.is_running = True
    print("Bot started.")
    await rt.dp.start_polling()

async def stop_bot():
    if not rt.is_running:
        return
    try:
        for _, task in list(rt.tasks.items()):
            task.cancel()
        rt.tasks.clear()
        await rt.dp.storage.close()
        await rt.dp.storage.wait_closed()
    except Exception:
        pass
    rt.is_running = False
    print("Bot stopped.")

# Expose to admin_app
rt.start_bot = start_bot
rt.stop_bot = stop_bot

if __name__ == "__main__":
    asyncio.run(start_bot())
