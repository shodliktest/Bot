import os
import re
import asyncio
import logging
import gc  # RAM tozalash uchun
from aiogram import types
from util import safe_remove, limit_cache

# Firebase funksiyalarini import qilamiz
from services.firebase import save_transcription, save_log 

logger = logging.getLogger(__name__)

async def register_audio_handlers(dp, rt, config, services):
    bot = rt.bot
    client_groq = services.get("groq")
    whisper_model = services.get("whisper")
    db = services.get("db") # Firebase bazasi

    async def translate_text(txt: str, lang_code: str = "uz"):
        key = (txt, lang_code)
        if key in rt.translation_cache:
            return rt.translation_cache[key]
        
        try:
            from deep_translator import GoogleTranslator
            loop = asyncio.get_event_loop()
            tr = await loop.run_in_executor(
                None, 
                lambda: GoogleTranslator(source="auto", target=lang_code).translate(txt)
            )
            rt.translation_cache[key] = tr
            await limit_cache(rt.translation_cache)
            return tr
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return txt

    @dp.message_handler(content_types=["voice", "audio"])
    async def audio_handler(message: types.Message):
        chat_id = message.chat.id
        mode = rt.user_settings.get(chat_id, config.get("DEFAULT_MODE", "whisper"))
        file_id = message.voice.file_id if message.voice else message.audio.file_id
        file = await bot.get_file(file_id)
        
        tmp_path = f"tmp_{chat_id}_{message.message_id}.ogg"
        status_msg = await message.answer(f"⏳ **Tahlil boshlandi...**\nRejim: `{mode.upper()}`", parse_mode="Markdown")

        async def process_audio():
            try:
                # 1. Faylni yuklab olish
                await bot.download_file(file.file_path, tmp_path)

                # 2. Transkripsiya
                segments = []
                if mode == "groq":
                    if not client_groq:
                        return await status_msg.edit_text("⚠️ Groq API sozlanmagan!")
                    from services.groq_service import transcribe_groq
                    segments = await asyncio.get_event_loop().run_in_executor(
                        None, transcribe_groq, client_groq, tmp_path
                    )
                else:
                    if not whisper_model:
                        return await status_msg.edit_text("⚠️ Local Whisper modeli yuklanmagan!")
                    from services.whisper_service import transcribe_local
                    segments = await asyncio.get_event_loop().run_in_executor(
                        None, transcribe_local, whisper_model, tmp_path
                    )

                if not segments:
                    return await status_msg.edit_text("❌ Audio tahlilida matn topilmadi.")

                await status_msg.edit_text("✍️ **Matn tayyor, tarjima qilinmoqda...**", parse_mode="Markdown")

                # 3. Matnni qayta ishlash va tarjima
                raw_full = " ".join([s["text"].strip() for s in segments])
                sentences = re.split(r'(?<=[.!?])\s+', raw_full)

                final_lines = []
                for sent in sentences:
                    if not sent.strip(): continue
                    translated = await translate_text(sent, "uz")
                    final_lines.append(f"🔹 {sent}\n🔸 *{translated}*")

                final_text = "\n\n".join(final_lines)

                # --- FIREBASE'GA SAQLASH QISMI ---
                if db:
                    save_transcription(db, chat_id, raw_full) # Original matnni saqlash
                    save_log(db, chat_id, "audio_processed", f"Mode: {mode}")

                # 4. Natijani yuborish
                if len(final_text) > 4096:
                    for i in range(0, len(final_text), 4000):
                        await message.answer(final_text[i:i+4000], parse_mode="Markdown")
                else:
                    await message.answer(final_text, parse_mode="Markdown")

                await bot.delete_message(chat_id, status_msg.message_id)

            except Exception as e:
                logger.exception(f"Processing error: {e}")
                await message.answer(f"❌ Xatolik yuz berdi: {str(e)}")
            finally:
                # --- AVTO-TOZALASH (RAM va Fayl) ---
                safe_remove(tmp_path) # Faylni o'chirish
                gc.collect()          # Python RAMni tozalash
                rt.tasks.pop(chat_id, None)

        task = asyncio.create_task(
            asyncio.wait_for(process_audio(), timeout=config.get("TASK_TIMEOUT_SEC", 300))
        )
        rt.tasks[chat_id] = task
