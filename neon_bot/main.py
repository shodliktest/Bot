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

# 2. KONFIGURATSIYA - Streamlit Secrets'dan o'qish
try:
    CONFIG = {
        "BOT_TOKEN": st.secrets["BOT_TOKEN"],
        "GROQ_API_KEY": st.secrets["GROQ_API_KEY"],
        "DEFAULT_MODE": "groq",
        "FIREBASE_CONF": st.secrets["FIREBASE_SERVICE_ACCOUNT"], # TOML'dagi lug'at
        "TASK_TIMEOUT_SEC": 300
    }
except Exception as e:
    st.error(f"❌ Secrets (Token, API Key yoki Firebase) topilmadi: {e}")
    st.stop()

# 3. RUNTIME VA LOGGING
class RuntimeContext:
    def __init__(self, bot):
        self.bot = bot
        self.tasks = {}
        self.user_settings = {}      # RAM kesh
        self.translation_cache = {}  # Tarjima keshi

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Bot va Dispatcher (Aiogram 2.x versiyasi bo'yicha)
    bot = Bot(token=CONFIG["BOT_TOKEN"])
    dp = Dispatcher(bot, storage=MemoryStorage())
    rt = RuntimeContext(bot)

    # 4. MODULLARNI IMPORT QILISH
    try:
        from services.groq_service import init_groq
        from services.whisper_service import load_whisper_model
        from services.firebase import init_firebase, get_user_mode, save_user_mode
        from handlers.audio import register_audio_handlers
    except ImportError as e:
        logger.error(f"❌ Modullarni yuklashda xato: {e}")
        return

    # 5. XIZMATLARNI ISHGA TUSHIRISH
    services = {}
    
    # Firebase Initialization
    services["db"] = init_firebase(CONFIG["FIREBASE_CONF"])
    if services["db"]:
        logger.info("🔥 Firebase Firestore muvaffaqiyatli ulandi.")
    else:
        logger.error("⚠️ Firebase ulanmadi, ba'zi funksiyalar ishlamasligi mumkin.")

    # Groq API Init
    services["groq"] = init_groq(CONFIG["GROQ_API_KEY"])
    
    # Whisper Local Model Init (Keshni hisobga oladi)
    try:
        services["whisper"] = load_whisper_model("base")
        logger.info("🎙 Whisper modeli yuklandi.")
    except Exception as e:
        logger.error(f"⚠️ Whisper yuklashda xato: {e}")
        services["whisper"] = None

    # 6. HANDLERLARNI RO'YXATDAN O'TKAZISH
    await register_audio_handlers(dp, rt, CONFIG, services)

    # /start komandasi handlerini shu yerda qoldiramiz
    @dp.message_handler(commands=['start'])
    async def cmd_start(message: types.Message):
        chat_id = message.chat.id
        db = services["db"]
        
        # Firebase'dan foydalanuvchi rejimini olish
        mode = get_user_mode(db, chat_id, CONFIG["DEFAULT_MODE"])
        rt.user_settings[chat_id] = mode
        
        await message.answer(
            f"🤖 **Neon Voice Bot ishga tushdi!**\n\n"
            f"Sizning ID: `{chat_id}`\n"
            f"Joriy rejim: `{mode.upper()}`\n\n"
            f"Audio yuboring, men uni matnga aylantirib, tarjima qilaman va Firebase'ga saqlayman."
        )

    # 7. BOTNI ISHGA TUSHIRISH (Polling)
    try:
        logger.info("🚀 Bot ishga tushmoqda...")
        await dp.start_polling()
    finally:
        await bot.close()

if __name__ == '__main__':
    # Streamlit o'zi main loopni boshqarishi mumkin, 
    # lekin bot uchun alohida asyncio run kerak
    asyncio.run(main())
