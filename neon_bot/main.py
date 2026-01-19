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

# 2. KONFIGURATSIYA - Secrets'dan o'qish
try:
    CONFIG = {
        "BOT_TOKEN": st.secrets["BOT_TOKEN"],
        "GROQ_API_KEY": st.secrets["GROQ_API_KEY"],
        "DEFAULT_MODE": "groq",
        "TASK_TIMEOUT_SEC": 300
    }
except Exception as e:
    st.error("❌ Secrets (Token yoki API Key) topilmadi!")
    st.stop()

# 3. RUNTIME VA LOGGING
class RuntimeContext:
    def __init__(self, bot):
        self.bot = bot
        self.tasks = {}
        self.user_settings = {}  # RAM kesh (Firebase'dan yuklanadi)
        self.translation_cache = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    bot = Bot(token=CONFIG["BOT_TOKEN"])
    dp = Dispatcher(bot, storage=MemoryStorage())
    rt = RuntimeContext(bot)

    # 4. MODULLARNI YUKLASH
    try:
        from services.groq_service import init_groq
        from services.whisper_service import load_whisper_model
        from services.firebase import init_firebase, get_user_settings, save_user_settings
        from handlers.audio import register_audio_handlers
    except ImportError as e:
        logger.error(f"❌ Import xatosi: {e}")
        return

    # 5. XIZMATLARNI ISHGA TUSHIRISH
    services = {}
    
    # Firebase ulanishi
    try:
        services["db"] = init_firebase()
        logger.info("🔥 Firebase Firestore ulandi.")
    except Exception as e:
        logger.error(f"⚠️ Firebase ulanishda xato: {e}")
        services["db"] = None

    # Groq API
    services["groq"] = init_groq(CONFIG["GROQ_API_KEY"])
    
    # Whisper Local
    try:
        services["whisper"] = load_whisper_model("base")
    except:
        services["whisper"] = None

    # 6. HANDLERLARNI RO'YXATDAN O'TKAZISH
    await register_audio_handlers(dp, rt, CONFIG, services)

    # Foydalanuvchi boshlaganda Firebase'dan ma'lumotlarni yuklash
    @dp.message_handler(commands=['start'])
    async def cmd_start(message: types.Message):
        chat_id = message.chat.id
        # Firebase'dan sozlamalarni olish (agar mavjud bo'lsa)
        db_settings = await get_user_settings(services["db"], chat_id)
        
        if db_settings:
            rt.user_settings[chat_id] = db_settings.get("mode", CONFIG["DEFAULT_MODE"])
        else:
            # Yangi foydalanuvchini saqlash
            await save_user_settings(services["db"], chat_id, CONFIG["DEFAULT_MODE"])
            rt.user_settings[chat_id] = CONFIG["DEFAULT_MODE"]
            
        await message.answer(
            f"🤖 Bot ishga tushdi!\n\n"
            f"Sizning ID: `{chat_id}`\n"
            f"Joriy rejim: `{rt.user_settings[chat_id].upper()}`\n\n"
            f"Audio yuboring, men uni Firebase'da log qilib tahlil qilaman."
        )

    # 7. BOTNI ISHGA TUSHIRISH
    try:
        await dp.start_polling()
    finally:
        await bot.close()

if __name__ == '__main__':
    asyncio.run(main())
