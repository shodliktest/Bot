import os
import sys
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# 1. YO'LLARNI SOZLASH (ImportError ning oldini olish uchun)
# Bu kod main.py turgan papkani Python uchun "asosiy" papka qilib belgilaydi
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# 2. KONFIGURATSIYA (O'z ma'lumotlaringizni kiriting)
CONFIG = {
    "BOT_TOKEN": "SIZNING_BOT_TOKENINGIZ", # Bu yerga bot tokenini qo'ying
    "GROQ_API_KEY": "SIZNING_GROQ_KALITINGIZ", # Bu yerga Groq API kalitini qo'ying
    "DEFAULT_MODE": "groq", 
    "TASK_TIMEOUT_SEC": 300
}

# 3. RUNTIME VA LOGGING
class RuntimeContext:
    def __init__(self, bot):
        self.bot = bot
        self.tasks = {}
        self.user_settings = {}
        self.translation_cache = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Bot obyektlarini yaratish
    bot = Bot(token=CONFIG["BOT_TOKEN"])
    dp = Dispatcher(bot, storage=MemoryStorage())
    rt = RuntimeContext(bot)

    # 4. MODULLARNI IMPORT QILISH (Try-Except ichida xavfsiz yuklash)
    try:
        from services.groq_service import init_groq
        from services.whisper_service import load_whisper_model
        from handlers.audio import register_audio_handlers
        logger.info("✅ Barcha ichki modullar yuklandi.")
    except ImportError as e:
        logger.error(f"❌ Modullarni yuklashda xatolik: {e}")
        return

    # 5. XIZMATLARNI ISHGA TUSHIRISH
    services = {}
    
    # Groq API
    try:
        services["groq"] = init_groq(CONFIG["GROQ_API_KEY"])
        logger.info("🚀 Groq API ulandi.")
    except Exception as e:
        logger.error(f"⚠️ Groq xatosi: {e}")
        services["groq"] = None

    # Whisper Local (Streamlit RAM yetishmasa xato berishi mumkin)
    try:
        services["whisper"] = load_whisper_model("base")
        logger.info("🎙 Whisper modeli yuklandi.")
    except Exception as e:
        logger.error(f"⚠️ Whisper xatosi: {e}")
        services["whisper"] = None

    # 6. HANDLERLARNI RO'YXATDAN O'TKAZISH
    await register_audio_handlers(dp, rt, CONFIG, services)

    # Start buyrug'i
    @dp.message_handler(commands=['start'])
    async def cmd_start(message: types.Message):
        await message.answer("🤖 Bot ishga tushdi! Audio yoki ovozli xabar yuboring.")

    # 7. BOTNI POLLING REJIMIDA BOSHLASH
    try:
        logger.info("🤖 Bot polling rejimida ishlamoqda...")
        await dp.start_polling()
    finally:
        await bot.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
