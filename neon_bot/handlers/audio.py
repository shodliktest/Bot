import os
import re
import asyncio
import logging
from aiogram import types
from util import safe_remove, limit_cache

# Loglarni sozlash
logger = logging.getLogger(__name__)

async def register_audio_handlers(dp, rt, config, services):
    bot = rt.bot
    client_groq = services.get("groq")
    whisper_model = services.get("whisper")

    async def translate_text(txt: str, lang_code: str = "uz"):
        """Matnni keshni hisobga olgan holda tarjima qilish"""
        key = (txt, lang_code)
        if key in rt.translation_cache:
            return rt.translation_cache[key]
        
        try:
            from deep_translator import GoogleTranslator
            # Bloklanishning oldini olish uchun run_in_executor ishlatish mumkin
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
        # Foydalanuvchi rejimini aniqlash
        mode = rt.user_settings.get(chat_id, config.get("DEFAULT_MODE", "whisper"))

        # Fayl ma'lumotlarini olish
        file_id = message.voice.file_id if message.voice else message.audio.file_id
        file = await bot.get_file(file_id)
        
        # Noyob vaqtinchalik fayl nomi (konfliktlarning oldini oladi)
        tmp_path = f"tmp_{chat_id}_{message.message_id}.ogg"
        
        status_msg = await message.answer(f"⏳ **Tahlil boshlandi...**\nRejim: `{mode.upper()}`", parse_mode="Markdown")

        async def process_audio():
            try:
                # 1. Faylni yuklab olish
                await bot.download_file(file.file_path, tmp_path)

                # 2. Transkripsiya (Matnga aylantirish)
                segments = []
                if mode == "groq":
                    if not client_groq:
                        return await status_msg.edit_text("⚠️ Groq API sozlanmagan!")
                    
                    from services.groq_service import transcribe_groq
                    # Groq API orqali transkripsiya
                    segments = await asyncio.get_event_loop().run_in_executor(
                        None, transcribe_groq, client_groq, tmp_path
                    )
                else:
                    if not whisper_model:
                        return await status_msg.edit_text("⚠️ Local Whisper modeli yuklanmagan!")
                    
                    from services.whisper_service import transcribe_local
                    # Local Whisper orqali transkripsiya
                    segments = await asyncio.get_event_loop().run_in_executor(
                        None, transcribe_local, whisper_model, tmp_path
                    )

                if not segments:
                    return await status_msg.edit_text("❌ Audio tahlilida matn topilmadi.")

                await status_msg.edit_text("✍️ **Matn tayyor, tarjima qilinmoqda...**", parse_mode="Markdown")

                # 3. Matnni qayta ishlash va tarjima qilish
                raw_full = " ".join([s["text"].strip() for s in segments])
                # Gaplarga bo'lish (regex orqali)
                sentences = re.split(r'(?<=[.!?])\s+', raw_full)

                final_lines = []
                for sent in sentences:
                    if not sent.strip():
                        continue
                    translated = await translate_text(sent, "uz")
                    final_lines.append(f"🔹 {sent}\n🔸 *{translated}*")

                # Natijani birlashtirish
                final_text = "\n\n".join(final_lines)

                # 4. Natijani yuborish (Telegram cheklovlarini hisobga olgan holda)
                if len(final_text) > 4096:
                    for i in range(0, len(final_text), 4000):
                        await message.answer(final_text[i:i+4000], parse_mode="Markdown")
                else:
                    await message.answer(final_text, parse_mode="Markdown")

                # Jarayon tugagach status xabarini o'chirish
                await bot.delete_message(chat_id, status_msg.message_id)

            except asyncio.TimeoutError:
                await message.answer("⏱ Vaqt tugadi. Audio juda uzun yoki server band.")
            except Exception as e:
                logger.exception(f"Processing error: {e}")
                await message.answer(f"❌ Xatolik yuz berdi: {str(e)}")
            finally:
                # Vaqtinchalik faylni o'chirish
                safe_remove(tmp_path)
                rt.tasks.pop(chat_id, None)

        # Taskni yaratish va boshqarish
        task = asyncio.create_task(
            asyncio.wait_for(process_audio(), timeout=config.get("TASK_TIMEOUT_SEC", 300))
        )
        rt.tasks[chat_id] = task
