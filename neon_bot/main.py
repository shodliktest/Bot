import sys
import os

# Loyiha joylashgan papkani tizim yo'liga qo'shish
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# O'z xizmatlaringizni import qilish
from handlers.audio import register_audio_handlers
from services.groq_service import init_groq
from services.whisper_service import load_whisper_model

# 1. KONFIGURATSIYA
CONFIG = {
    "BOT_TOKEN": "SIZNING_BOT_TOKENINGIZ",
    "GROQ_API_KEY": "SIZNING_GROQ_KALITINGIZ",
    "DEFAULT_MODE": "groq",  # yoki 'whisper'
    "TASK_TIMEOUT_SEC": 300,
    "MAX_CACHE_SIZE": 1000
}

# 2. RUNTIME CLASS (Barcha holatlarni bitta obyektda saqlash)
class RuntimeContext:
    def __init__(self, bot):
        self.bot = bot
        self.tasks = {}              # Faol vazifalar
        self.user_settings = {}      # Foydalanuvchi rejimlari (groq/whisper)
        self.translation_cache = {}  # Tarjima keshi

# Loglarni sozlash
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Bot va Dispatcher obyektlarini yaratish
    bot = Bot(token=CONFIG["BOT_TOKEN"])
    storage = MemoryStorage()
    dp = Dispatcher(bot, storage=storage)

    # Runtime obyektini yaratish
    rt = RuntimeContext(bot)

    # 3. XIZMATLARNI INIZIALIZATSIYA QILISH
    services = {}
    
    # Groq xizmatini yoqish
    try:
        services["groq"] = init_groq(CONFIG["GROQ_API_KEY"])
        logger.info("✅ Groq API muvaffaqiyatli ulandi.")
    except Exception as e:
        logger.error(f"❌ Groq xatosi: {e}")
        services["groq"] = None

    # Whisper modelini yuklash (Local rejim uchun)
    try:
        # Agar kompyuteringiz kuchi yetsa 'base' yoki 'small' ishlating
        services["whisper"] = load_whisper_model("base")
        logger.info("✅ Whisper modeli yuklandi.")
    except Exception as e:
        logger.error(f"❌ Whisper xatosi: {e}")
        services["whisper"] = None

    # 4. HANDLERLARNI RO'YXATDAN O'TKAZISH
    # Audio handler (biz yangilagan fayl)
    await register_audio_handlers(dp, rt, CONFIG, services)

    # Oddiy buyruqlar uchun handler
    @dp.message_handler(commands=['start', 'help'])
    async def send_welcome(message: types.Message):
        await message.answer(
            "👋 Salom! Men audio xabarlarni matnga aylantirib, tarjima qilaman.\n\n"
            "⚙️ **Rejimni tanlash:** /mode_groq yoki /mode_whisper\n"
            "🎙 Shunchaki audio yoki ovozli xabar yuboring."
        )

    @dp.message_handler(commands=['mode_groq', 'mode_whisper'])
    async def set_mode(message: types.Message):
        mode = "groq" if "groq" in message.text else "whisper"
        rt.user_settings[message.chat.id] = mode
        await message.answer(f"✅ Rejim o'zgardi: **{mode.upper()}**", parse_mode="Markdown")

    # 5. BOTNI ISHGA TUSHIRISH
    try:
        logger.info("🚀 Bot ishga tushdi...")
        await dp.start_polling()
    finally:
        await bot.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("🤖 Bot to'xtatildi.")
