import os
import sys
import asyncio
import logging
import streamlit as st
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# 1. YO'LLARNI SOZLASH
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# 2. KONFIGURATSIYA
try:
    CONFIG = {
        "BOT_TOKEN": st.secrets["BOT_TOKEN"],
        "GROQ_API_KEY": st.secrets["GROQ_API_KEY"],
        "DEFAULT_MODE": "groq",
        "FIREBASE_CONF": st.secrets["FIREBASE_SERVICE_ACCOUNT"] # Secrets'da bo'lishi shart
    }
except Exception as e:
    st.error("❌ Secrets topilmadi!")
    st.stop()

# 3. RUNTIME VA LOGGING
class RuntimeContext:
    def __init__(self, bot):
        self.bot = bot
        self.user_settings = {} 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    bot = Bot(token=CONFIG["BOT_TOKEN"])
    dp = Dispatcher(bot, storage=MemoryStorage())
    rt = RuntimeContext(bot)

    # 4. MODULLARNI YUKLASH
    from services.groq_service import init_groq
    from services.whisper_service import load_whisper_model
    from services.firebase import init_firebase, save_user_mode, get_user_mode
    from handlers.audio import register_audio_handlers

    # 5. XIZMATLARNI ISHGA TUSHIRISH
    services = {}
    services["db"] = init_firebase(CONFIG["FIREBASE_CONF"])
    services["groq"] = init_groq(CONFIG["GROQ_API_KEY"])
    services["whisper"] = load_whisper_model("base")

    # 6. HANDLERLARNI RO'YXATDAN O'TKAZISH
    # Audio handlerga barcha xizmatlarni uzatamiz
    register_audio_handlers(dp, rt, CONFIG, services)

    @dp.message_handler(commands=['start'])
    async def cmd_start(message: types.Message):
        chat_id = message.chat.id
        # Firebase'dan mode olish
        mode = get_user_mode(services["db"], chat_id, CONFIG["DEFAULT_MODE"])
        rt.user_settings[chat_id] = mode
        
        await message.answer(f"🤖 Bot tayyor!\nRejim: {mode.upper()}")

    # 7. BOTNI ISHGA TUSHIRISH
    try:
        logger.info("🚀 Bot polling rejimida ishga tushdi...")
        await dp.start_polling()
    finally:
        await bot.close()

if __name__ == '__main__':
    asyncio.run(main())
