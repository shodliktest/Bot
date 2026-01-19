# main.py
"""
Saqlash: bu fayl botning asosiy jarayonini boshqaradi.
Xususiyatlar:
- Webhook o'chiriladi (delete_webhook) va polling skip_updates=True bilan boshlanadi.
- TerminatedByOtherGetUpdates uchun retry mexanizmi mavjud.
- start_bot / stop_bot asinxron funksiyalari eksport qilinadi.
- Fayl import qilinganda avtomatik ishga tushmaydi; faqat `python main.py` orqali ishga tushadi.
"""

import asyncio
import logging
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.utils.exceptions import TerminatedByOtherGetUpdates

from runtime import Runtime
from config import load_config
from services.firebase import init_firebase
from services.groq_service import init_groq
from services.whisper_service import init_whisper
from handlers.common import register_common_handlers
from handlers.audio import register_audio_handlers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global runtime singleton
rt = Runtime()
config = load_config()

# Keep references to services so handlers can use them
_services = {"db": None, "groq": None, "whisper": None}


async def _setup_bot_and_handlers():
    """
    Ichki yordamchi: bot, dispatcher va handlerlarni sozlaydi.
    Chaqarilishidan oldin rt.loop o'rnatilgan bo'lishi kerak.
    """
    # Bot va Dispatcher yaratish
    rt.bot = Bot(token=config["BOT_TOKEN"])
    rt.dp = Dispatcher(rt.bot)

    # Init services
    db = init_firebase(config["FIREBASE_CONF"])
    groq_client = init_groq(config["GROQ_API_KEY"])
    whisper_model = init_whisper()

    _services["db"] = db
    _services["groq"] = groq_client
    _services["whisper"] = whisper_model

    # Register handlers
    await register_common_handlers(rt.dp, rt, config, db)
    await register_audio_handlers(rt.dp, rt, config, _services)


async def _polling_loop(retry_delay: int = 5):
    """
    Pollingni boshlaydi va TerminatedByOtherGetUpdates holatida retry qiladi.
    Bu funksiya asinxron task sifatida ishga tushiriladi.
    """
    max_retries = 12
    attempt = 0
    while True:
        try:
            # O'tgan webhooklarni o'chirish va pending update'larni tozalash
            await rt.bot.delete_webhook(drop_pending_updates=True)
            # Start polling (bloklaydi, shuning uchun bu funksiya task ichida ishlaydi)
            await rt.dp.start_polling(skip_updates=True)
            # Agar start_polling qaytib kelsayu, chiqamiz
            break
        except TerminatedByOtherGetUpdates:
            attempt += 1
            logger.warning("Terminated by other getUpdates. Retry in %s seconds (attempt %s).", retry_delay, attempt)
            if attempt >= max_retries:
                logger.error("Max retries reached for polling. Exiting polling loop.")
                break
            await asyncio.sleep(retry_delay)
        except asyncio.CancelledError:
            logger.info("Polling task cancelled.")
            break
        except Exception as e:
            logger.exception("Unexpected error in polling loop: %s", e)
            # kichik tanaffusdan keyin qayta urin
            await asyncio.sleep(retry_delay)


async def start_bot():
    """
    Botni ishga tushiradi. Agar allaqachon ishlayotgan bo'lsa, hech narsa qilmaydi.
    Bu funksiya import qilinganda avtomatik chaqirilmaydi.
    """
    if rt.is_running:
        logger.info("Bot already running, start_bot() ignored.")
        return

    # O'z event loop'ini aniqlash
    try:
        rt.loop = asyncio.get_event_loop()
    except RuntimeError:
        rt.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(rt.loop)

    # Setup bot va handlerlar
    await _setup_bot_and_handlers()

    # Start polling in background task
    rt.polling_task = rt.loop.create_task(_polling_loop())
    rt.is_running = True
    rt.log("Bot started")
    logger.info("Bot started (background polling task created).")


async def stop_bot():
    """
    Botni to'xtatadi: polling task'ni bekor qiladi, dispatcher va bot sessiyasini yopadi.
    """
    if not rt.is_running:
        logger.info("Bot not running, stop_bot() ignored.")
        return

    rt.log("Stopping bot...")
    # Cancel polling task
    try:
        if hasattr(rt, "polling_task") and rt.polling_task:
            rt.polling_task.cancel()
            # await cancellation
            try:
                await rt.polling_task
            except asyncio.CancelledError:
                pass
    except Exception as e:
        logger.exception("Error cancelling polling task: %s", e)

    # Cancel active user tasks
    for chat_id, task in list(rt.tasks.items()):
        try:
            task.cancel()
        except Exception:
            pass
    rt.tasks.clear()

    # Close dispatcher storage and bot session
    try:
        if rt.dp:
            await rt.dp.storage.close()
            await rt.dp.storage.wait_closed()
    except Exception:
        pass

    try:
        if rt.bot:
            await rt.bot.session.close()
    except Exception:
        pass

    rt.is_running = False
    rt.log("Bot stopped")
    logger.info("Bot stopped.")


# Expose synchronous wrappers for convenience (useful for Streamlit admin)
def start_bot_sync():
    """
    Synchronous wrapper: chaqirilganda yangi event loopda start_bot ni ishga tushiradi.
    Eslatma: agar siz Streamlit ichida ishlatayotgan bo'lsangiz, asyncio.run bilan chaqirish mumkin.
    """
    asyncio.run(start_bot())


def stop_bot_sync():
    asyncio.run(stop_bot())


if __name__ == "__main__":
    # Agar fayl to'g'ridan-to'g'ri ishga tushirilsa, botni boshlaymiz.
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        asyncio.run(stop_bot())
