import asyncio
import logging
import threading
import streamlit as st
from aiogram import Bot, Dispatcher
from runtime import Runtime
from config import load_config
from services.firebase import init_firebase
from services.groq_service import init_groq
from services.whisper_service import init_whisper
from handlers.common import register_common_handlers
from handlers.audio import register_audio_handlers

# 1. Loglarni sozlash
logging.basicConfig(level=logging.INFO)

# 2. Runtime va Konfiguratsiya
if "rt" not in st.session_state:
    st.session_state.rt = Runtime()
rt = st.session_state.rt
config = load_config()

# UI qismi (Interfeys oqarib qolmasligi uchun)
st.title("🤖 Neon Hybrid Bot")
st.write("Bot holati: ", "🟢 Ishlamoqda" if rt.is_running else "🔴 Yuklanmoqda...")
if rt.logs:
    st.code("\n".join(rt.logs[-10:]), language="text")

# 3. Botni ishga tushirish funksiyasi
async def start_bot_async():
    if rt.is_running:
        return
    
    # Yangi loop yaratamiz
    rt.loop = asyncio.get_running_loop()
    rt.bot = Bot(token=config["BOT_TOKEN"])
    rt.dp = Dispatcher(rt.bot)

    # Servislar
    db = init_firebase(config["FIREBASE_CONF"])
    groq_client = init_groq(config["GROQ_API_KEY"])
    whisper_model = init_whisper()
    services = {"db": db, "groq": groq_client, "whisper": whisper_model}

    # Handlerlar
    await register_common_handlers(rt.dp, rt, config, db)
    await register_audio_handlers(rt.dp, rt, config, services)

    rt.is_running = True
    rt.log("Bot fon rejimida ishga tushdi.")
    
    try:
        # Aiogram 2.x uchun to'g'ri polling
        await rt.dp.skip_updates()
        await rt.dp.start_polling()
    finally:
        session = await rt.bot.get_session()
        await session.close()
        rt.is_running = False

# 4. Thread (Oqim) boshqaruvchisi
def run_worker():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_bot_async())

# 5. AVTO-START MANTIQI
# Agar bot ishlamayotgan bo'lsa, uni darhol thread-da boshlaymiz
if not rt.is_running:
    # Faqat bitta thread ishlashini ta'minlash uchun nom beramiz
    is_already_running = any(t.name == "BotThread" for t in threading.enumerate())
    if not is_already_running:
        bot_thread = threading.Thread(target=run_worker, name="BotThread", daemon=True)
        bot_thread.start()
        st.rerun() # Holatni yangilash uchun
