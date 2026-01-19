# handlers/audio.py
import os
import re
import time
import asyncio
from aiogram import types
from util import safe_remove, limit_cache

async def register_audio_handlers(dp, rt, config, services):
    bot = rt.bot
    client_groq = services.get("groq")
    whisper_model = services.get("whisper")
    db = services.get("db")

    async def translate_text(txt: str, lang_code: str = "uz"):
        key = (txt, lang_code)
        if key in rt.translation_cache:
            return rt.translation_cache[key]
        try:
            from deep_translator import GoogleTranslator
            tr = GoogleTranslator(source="auto", target=lang_code).translate(txt)
            rt.translation_cache[key] = tr
            await limit_cache(rt.translation_cache)
            return tr
        except Exception:
            return txt

    @dp.message_handler(content_types=["voice", "audio"])
    async def audio_handler(message: types.Message):
        chat_id = message.chat.id
        mode = rt.user_settings.get(chat_id, config["DEFAULT_MODE"])

        file_id = message.voice.file_id if message.voice else message.audio.file_id
        file = await bot.get_file(file_id)
        downloaded = await bot.download_file(file.file_path)
        tmp_path = f"tmp_{chat_id}.ogg"
        with open(tmp_path, "wb") as f:
            f.write(downloaded.read())

        status_msg = await message.answer(f"⏳ Tahlil boshlandi... Rejim: {mode.upper()}")

        async def process_audio():
            try:
                segments = []
                if mode == "groq":
                    if not client_groq:
                        await bot.edit_message_text("⚠️ Groq API kaliti topilmadi. Admin paneldan kiriting yoki Local rejimni tanlang.",
                                                    chat_id, status_msg.message_id)
                        return
                    from services.groq_service import transcribe_groq
                    segments = transcribe_groq(client_groq, tmp_path)
                else:
                    if not whisper_model:
                        await bot.edit_message_text("⚠️ Local Whisper modeli yuklanmagan. Admin paneldan qayta ishga tushiring.",
                                                    chat_id, status_msg.message_id)
                        return
                    from services.whisper_service import transcribe_local
                    segments = transcribe_local(whisper_model, tmp_path)

                await bot.edit_message_text("✍️ Matn yig‘ilmoqda va tarjima qilinmoqda...", chat_id, status_msg.message_id)

                raw_full = " ".join([s["text"].strip() for s in segments])
                sentences = re.split(r'(?<=[.!?])\s+', raw_full)

                final_lines = []
                last_ping = time.time()

                for sent in sentences:
                    if not sent:
                        continue
                    tr = await translate_text(sent, "uz")
                    final_lines.append(f"{sent} ({tr})")
                    if time.time() - last_ping > config["KEEPALIVE_INTERVAL"]:
                        try:
                            await bot.edit_message_text(
                                f"⏳ Jarayon davom etmoqda...\nHozircha {len(final_lines)} gap tayyor.",
                                chat_id, status_msg.message_id
                            )
                        except Exception:
                            pass
                        last_ping = time.time()

                final_text = "\n".join(final_lines)
                if len(final_text) > 4000:
                    await message.answer(final_text[:4000])
                    await message.answer(final_text[4000:])
                else:
                    await message.answer(final_text)

                # Firebase log (ixtiyoriy)
                if db:
                    from services.firebase import save_log
                    await dp.loop.run_in_executor(None, save_log, db, {
                        "chat_id": chat_id,
                        "mode": mode,
                        "len_segments": len(segments),
                        "ts": time.time()
                    })

                try:
                    await bot.delete_message(chat_id, status_msg.message_id)
                except Exception:
                    pass

            except Exception as e:
                await message.answer(f"❌ Xatolik: {e}")
            finally:
                safe_remove(tmp_path)
                rt.tasks.pop(chat_id, None)

        task = rt.loop.create_task(asyncio.wait_for(process_audio(), timeout=config["TASK_TIMEOUT_SEC"]))
        rt.tasks[chat_id] = task
