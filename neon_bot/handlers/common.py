# handlers/common.py
from aiogram import types
from keyboards import main_menu, admin_inline

async def register_common_handlers(dp, rt, config, db):
    @dp.message_handler(commands=["start"])
    async def start_cmd(message: types.Message):
        chat_id = message.chat.id
        # Firebase’dan mode olish (ixtiyoriy)
        mode = rt.user_settings.get(chat_id, None)
        if mode is None:
            mode = config["DEFAULT_MODE"]
            if db:
                from services.firebase import get_user_mode
                mode = await dp.loop.run_in_executor(None, get_user_mode, db, chat_id, config["DEFAULT_MODE"])
            rt.user_settings[chat_id] = mode

        await message.answer(
            f"👋 Assalomu alaykum, {message.from_user.first_name}!\n"
            "Men audio xabarlarni matnga aylantiruvchi botman.\n"
            "Rejimni tanlang va audio yuboring.",
            reply_markup=main_menu(message.from_user.id, config["ADMIN_ID"])
        )

    @dp.message_handler(lambda m: m.text in ["⚡ Groq Rejimi", "🎧 Whisper Rejimi"])
    async def change_mode(message: types.Message):
        chat_id = message.chat.id
        if "Groq" in message.text:
            rt.user_settings[chat_id] = "groq"
            await message.answer("✅ Groq rejimi tanlandi!")
        else:
            rt.user_settings[chat_id] = "local"
            await message.answer("✅ Whisper rejimi tanlandi!")

        # Firebase’ga yozish (ixtiyoriy)
        if db:
            from services.firebase import save_user_mode
            await dp.loop.run_in_executor(None, save_user_mode, db, chat_id, rt.user_settings[chat_id])

    @dp.message_handler(lambda m: m.text == "ℹ️ Yordam")
    async def help_msg(message: types.Message):
        await message.answer(
            "🎧 Audio yuboring—men uni matnga aylantiraman.\n"
            "Rejimlar:\n"
            "- ⚡ Groq: bulutda tez va aniq.\n"
            "- 🎧 Whisper: lokal model (internetga kam bog‘liq).\n"
            "Admin uchun: 🔑 Admin Panel tugmasi."
        )

    @dp.message_handler(lambda m: m.text == "🔑 Admin Panel" and m.chat.id == config["ADMIN_ID"])
    async def admin_panel(message: types.Message):
        await message.answer("Admin panelga xush kelibsiz!", reply_markup=admin_inline())

    @dp.callback_query_handler(lambda c: c.data.startswith("adm_"))
    async def admin_callbacks(call: types.CallbackQuery):
        data = call.data
        if data == "adm_status":
            active_tasks = len(rt.tasks)
            await call.message.answer(
                f"📊 Holat:\n"
                f"- Bot running: {rt.is_running}\n"
                f"- Active tasks: {active_tasks}\n"
                f"- Default mode: {config['DEFAULT_MODE']}\n"
            )
        elif data == "adm_clear_cache":
            rt.translation_cache.clear()
            await call.message.answer("🧹 Tarjima cache tozalandi.")
        elif data == "adm_restart":
            await call.message.answer("🔄 Bot qayta ishga tushirilmoqda...")
            await rt.stop_bot()
            await rt.start_bot()
        elif data == "adm_stop":
            await call.message.answer("⏹️ Bot to‘xtatilmoqda...")
            await rt.stop_bot()
