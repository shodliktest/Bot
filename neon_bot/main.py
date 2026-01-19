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

# 2. Runtime va Konfiguratsiyani yuklash
# Streamlit har safar refresh bo'lganda ob'ektlarni yo'qotmaslik uchun session_state'dan foydalanamiz
if "rt" not in st.session_state:
    st.session_state.rt = Runtime()

rt = st.session_state.rt
config = load_config()

# --- ADMIN PANEL INTERFEYSI ---
st.set_page_config(page_title="Neon Bot Admin", page_icon="🤖")
st.title("🤖 Neon Hybrid Bot — Tizim Nazorati")

# Bot holatini ko'rsatish
status_placeholder = st.empty()
if rt.is_running:
    status_placeholder.success("✅ Bot fon rejimida muvaffaqiyatli ishlamoqda")
else:
    status_placeholder.info("⏳ Bot ishga tushirilmoqda...")

# Kelajakdagi funksiyalar uchun bo'sh joy
st.divider()
st.subheader("📊 Tizim ma'lumotlari")
col1, col2 = st.columns(2)
with col1:
    st.metric("Faol topshiriqlar", len(rt.tasks))
with col2:
    st.metric("Default Rejim", config.get("DEFAULT_MODE", "groq").upper())

st.subheader("📝 So'nggi amallar (Logs)")
st.code("\n".join(rt.logs[-15:]), language="text")
# ------------------------------

# 3. Botni ishga tushirish mantig'i (Async)
async def start_bot_background():
    if rt.is_running:
        return
    
    rt.loop = asyncio.get_running_loop()
    rt.bot = Bot(token=config["BOT_TOKEN"])
    rt.dp = Dispatcher(rt.bot)

    # Servislarni initsializatsiya qilish
    db = init_firebase(config["FIREBASE_CONF"])
    groq_client = init_groq(config["GROQ_API_KEY"])
    whisper_model = init_whisper()
    services = {"db": db, "groq": groq_client, "whisper": whisper_model}

    # Handlerlarni ulaymiz
    await register_common_handlers(rt.dp, rt, config, db)
    await register_audio_handlers(rt.dp, rt, config, services)

    rt.is_running = True
    rt.log("Bot fon rejimida start oldi.")
    
    try:
        # Aiogram 2.x uchun xavfsiz polling
        await rt.dp.skip_updates()
        await rt.dp.start_polling()
    finally:
        session = await rt.bot.get_session()
        await session.close()
        rt.is_running = False

# 4. Thread (Oqim) funksiyasi
def bot_thread_executor():
    # Yangi thread uchun yangi asyncio loop yaratish shart
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    new_loop.run_until_complete(start_bot_background())

# 5. AVTO-START: Botni tekshirish va ishga tushirish
# threading.enumerate() orqali bot allaqachon fonda ishlayotganini tekshiramiz
bot_exists = any(t.name == "NeonBotThread" for t in threading.enumerate())

if not rt.is_running and not bot_exists:
    # Botni yangi oqimda, NeonBotThread nomi bilan fonda boshlaymiz
    thread = threading.Thread(target=bot_thread_executor, name="NeonBotThread", daemon=True)
    thread.start()
    st.rerun() # UI ni yangilab, bot holatini ko'rsatish uchun
