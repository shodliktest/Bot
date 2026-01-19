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
    
    # Loopni saqlash (Audio handler uchun kerak)
    rt.loop = asyncio.get_running_loop()
    
    rt.bot = Bot(token=config["BOT_TOKEN"])
    rt.dp = Dispatcher(rt.bot)

    db = init_firebase(config["FIREBASE_CONF"])
    groq_client = init_groq(config["GROQ_API_KEY"])
    whisper_model = init_whisper()
    services = {"db": db, "groq": groq_client, "whisper": whisper_model}

    await register_common_handlers(rt.dp, rt, config, db)
    await register_audio_handlers(rt.dp, rt, config, services)

    rt.is_running = True
    print("Bot polling boshlanmoqda...")
    
    try:
        # skip_updates=True TypeError bergani uchun uni alohida chaqiramiz:
        await rt.dp.skip_updates() 
        # start_polling ichida skip_updates argumenti yo'q!
        await rt.dp.start_polling() 
    finally:
        session = await rt.bot.get_session()
        await session.close()

async def stop_bot():
    if not rt.is_running:
        return
    rt.is_running = False
    rt.dp.stop_polling()
    await rt.dp.wait_closed()

rt.start_bot = start_bot
rt.stop_bot = stop_bot
