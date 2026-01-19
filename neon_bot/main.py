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

# Global runtime instance
rt = Runtime()
config = load_config()

async def start_bot():
    if rt.is_running:
        return
    
    # MUHIM: Hozirgi ishlayotgan loopni Runtime-ga bog'laymiz
    rt.loop = asyncio.get_running_loop()
    
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
    print("Bot polling boshlandi...")
    
    try:
        # skip_updates=True eski "Conflict" xabarlarini o'chirib yuboradi
        await rt.dp.start_polling(skip_updates=True)
    finally:
        # Bot to'xtaganda sessiyani tozalash
        session = await rt.bot.get_session()
        await session.close()

async def stop_bot():
    if not rt.is_running:
        return
    
    try:
        rt.dp.stop_polling()
        await rt.dp.wait_closed()
        
        for _, task in list(rt.tasks.items()):
            task.cancel()
        rt.tasks.clear()
    except Exception as e:
        print(f"To'xtatishda xatolik: {e}")
    finally:
        rt.is_running = False

# Funksiyalarni runtime obyektiga bog'lab qo'yamiz
rt.start_bot = start_bot
rt.stop_bot = stop_bot

if __name__ == "__main__":
    asyncio.run(start_bot())
