# main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from runtime import Runtime
from config import load_config
# Services va Handlerlarni import qilishni unutmang
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
    
    # Audio handler uchun loopni saqlaymiz
    rt.loop = asyncio.get_running_loop()
    
    rt.bot = Bot(token=config["BOT_TOKEN"])
    rt.dp = Dispatcher(rt.bot)

    # Servislarni ishga tushirish
    db = init_firebase(config["FIREBASE_CONF"])
    groq_client = init_groq(config["GROQ_API_KEY"])
    whisper_model = init_whisper()
    services = {"db": db, "groq": groq_client, "whisper": whisper_model}

    # Handlerlarni ro'yxatdan o'tkazish
    await register_common_handlers(rt.dp, rt, config, db)
    await register_audio_handlers(rt.dp, rt, config, services)

    rt.is_running = True
    print("Bot polling boshlanmoqda...")
    
    try:
        # AIOGRAM 2.x uchun to'g'ri usul:
        # Avval eski xabarlarni tozalaymiz
        await rt.dp.skip_updates() 
        # Keyin pollingni argumentlarsiz boshlaymiz
        await rt.dp.start_polling() 
    finally:
        # Sessiyani yopish Conflict xatosini oldini oladi
        session = await rt.bot.get_session()
        await session.close()

async def stop_bot():
    if not rt.is_running:
        return
    rt.is_running = False
    rt.dp.stop_polling()
    await rt.dp.wait_closed()

# Admin panel uchun funksiyalarni eksport qilish
rt.start_bot = start_bot
rt.stop_bot = stop_bot
