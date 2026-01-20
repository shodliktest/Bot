import asyncio
import os
import re
import streamlit as st
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

import whisper
from deep_translator import GoogleTranslator

# MODULLAR
from config import BOT_TOKEN, ADMIN_ID
from database import update_user, update_stats, load_db
from utils import get_uz_time, clean_text, delete_temp_files, format_time_stamp
from keyboards import (
    get_main_menu, get_tr_kb, get_split_kb, get_format_kb, 
    get_admin_kb, get_contact_kb
)

# --- BOTNI YARATISH ---
try:
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
except Exception as e:
    st.error(f"Token xatosi: {e}")
    st.stop()

# --- HOLATLAR ---
class UserStates(StatesGroup):
    waiting_for_contact_msg = State()

class AdminStates(StatesGroup):
    waiting_for_bc = State()

async_lock = asyncio.Lock()
waiting_users = 0
user_data = {}

@st.cache_resource
def load_whisper():
    return whisper.load_model("base")

model_local = load_whisper()

# ==========================================
#              HANDLERLAR
# ==========================================

@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    update_user(m.from_user)
    try:
        u_link = f"@{m.from_user.username}" if m.from_user.username else "Username yo'q"
        msg = (
            f"🆕 <b>YANGI USER:</b> {m.from_user.full_name}\n"
            f"🆔 <code>{m.from_user.id}</code>\n"
            f"👤 {u_link}"
        )
        await bot.send_message(ADMIN_ID, msg, parse_mode="HTML")
    except: pass

    welcome = (
        f"👋 <b>Assalomu alaykum, {m.from_user.first_name}!</b>\n\n"
        f"🎙 <b>Suxandon AI</b> botiga xush kelibsiz.\n"
        "Audio fayllarni matnga aylantirib, tarjima qilib beraman.\n\n"
        "👇 <b>Boshlash uchun audio fayl yuboring!</b>"
    )
    await m.answer(welcome, reply_markup=get_main_menu(m.from_user.id), parse_mode="HTML")

@dp.message(F.text == "ℹ️ Yordam")
async def help_h(m: types.Message):
    text = (
        "📚 <b>SUXANDON AI - QO'LLANMA</b>\n\n"
        "1️⃣ <b>Audio yuboring:</b> Mp3 yoki voice yuboring.\n"
        "2️⃣ <b>Tarjima tanlang:</b> Tarjima asl matn ostida (<i>italic</i>) chiqadi.\n"
        "3️⃣ <b>Ko'rinish:</b> Time Split (vaqt bilan) yoki Full Context (abzasli matn).\n"
        "4️⃣ <b>Format:</b> TXT fayl yoki to'g'ridan-to'g'ri Chat xabari.\n\n"
        "⚠️ <b>Cheklov:</b> Fayl hajmi 20MB gacha."
    )
    await m.answer(text, parse_mode="HTML")

@dp.message(F.text == "👨‍💻 Bog'lanish")
async def contact_h(m: types.Message):
    await m.answer("Admin bilan aloqa uchun xabar yuboring:", reply_markup=get_contact_kb(), parse_mode="HTML")

@dp.callback_query(F.data == "msg_to_admin")
async def feedback_start(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.waiting_for_contact_msg)
    await call.message.answer("📝 <b>Xabaringizni yozing:</b>", parse_mode="HTML")
    await call.answer()

@dp.message(UserStates.waiting_for_contact_msg)
async def feedback_send(m: types.Message, state: FSMContext):
    await state.clear()
    u_link = f"@{m.from_user.username}" if m.from_user.username else "yo'q"
    admin_msg = (
        f"📩 <b>YANGI MUROJAAT:</b>\n"
        f"👤 User: {m.from_user.full_name}\n"
        f"🆔 ID: <code>{m.from_user.id}</code>\n"
        f"🔗 Link: {u_link}\n\n"
        f"📝 <b>Xabar:</b>\n{m.text}"
    )
    await bot.send_message(ADMIN_ID, admin_msg, parse_mode="HTML")
    await m.answer("✅ <b>Yuborildi!</b>", parse_mode="HTML")

@dp.message(F.chat.id == ADMIN_ID, F.reply_to_message)
async def admin_reply_handler(m: types.Message):
    id_match = re.search(r"ID: (\d+)", m.reply_to_message.text)
    if id_match:
        user_id = int(id_match.group(1))
        try:
            await bot.send_message(user_id, f"💬 <b>Admin javobi:</b>\n\n{m.text}", parse_mode="HTML")
            await m.answer(f"✅ Javob {user_id} ga yuborildi.")
        except: await m.answer("❌ Yuborishda xatolik.")

# --- AUDIO PROCESS ---

@dp.message(F.audio | F.voice)
async def handle_audio(m: types.Message):
    fid = m.audio.file_id if m.audio else m.voice.file_id
    fsize = m.audio.file_size if m.audio else m.voice.file_size

    if fsize > 20 * 1024 * 1024:
        await m.answer("❌ <b>Maksimal hajm 20MB!</b>", parse_mode="HTML")
        return

    user_data[m.chat.id] = {
        'fid': fid, 'uname': m.from_user.full_name, 'src_lang': 'auto', 'tr_lang': None, 'view': None
    }
    await m.answer("🌍 <b>Tarjima qilinsinmi?</b>", reply_markup=get_tr_kb(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("tr_"))
async def tr_lang_cb(call: types.CallbackQuery):
    user_data[call.message.chat.id]['tr_lang'] = call.data.replace("tr_", "")
    await call.message.edit_text("📄 <b>Ko'rinishni tanlang:</b>", reply_markup=get_split_kb(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("v_"))
async def view_cb(call: types.CallbackQuery):
    user_data[call.message.chat.id]['view'] = call.data.replace("v_", "")
    await call.message.edit_text("💾 <b>Formatni tanlang:</b>", reply_markup=get_format_kb(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("f_"))
async def start_process(call: types.CallbackQuery):
    global waiting_users
    chat_id = call.message.chat.id
    fmt = call.data.replace("f_", "")
    data = user_data.get(chat_id)
    await call.message.delete()

    waiting_users += 1
    wait_msg = await call.message.answer(f"⏳ Navbat: {waiting_users}", parse_mode="HTML")

    async with async_lock:
        audio_path, result_path = f"audio_{chat_id}.mp3", f"res_{chat_id}.txt"
        
        async def show_progress(percent, status):
            blocks = int(percent // 5)
            bar = "🟩" * blocks + "⬜" * (20 - blocks)
            try:
                await wait_msg.edit_text(f"⚙️ <b>{status}</b>\n\n{bar} <b>{percent}%</b>", parse_mode="HTML")
            except: pass

        try:
            # 1. YUKLASH (5% qadam bilan)
            for p in range(0, 26, 5):
                await show_progress(p, "Audio yuklanmoqda...")
                await asyncio.sleep(0.1)
            
            file = await bot.get_file(data['fid'])
            await bot.download_file(file.file_path, audio_path)

            # 2. TAHLIL
            await show_progress(50, "Sun'iy intellekt tahlil qilmoqda...")
            res = await asyncio.to_thread(model_local.transcribe, audio_path)
            segments = res['segments']

            # 3. FORMATLASH
            tr_code = data['tr_lang'] if data['tr_lang'] != "orig" else None
            paragraph_list = []
            
            total_segs = len(segments)
            for i, s in enumerate(segments):
                orig = clean_text(s['text'].strip())
                if not orig: continue
                
                block = orig
                if tr_code:
                    try:
                        tr = await asyncio.to_thread(GoogleTranslator(source='auto', target=tr_code).translate, s['text'])
                        block = f"{orig}\n<i>({clean_text(tr)})</i>"
                    except: pass
                
                if data['view'] == "split":
                    block = f"{format_time_stamp(s['start'])} {block}"
                
                paragraph_list.append(block)
                
                # Progress update (har 5 segmentda)
                if i % 5 == 0 or i == total_segs - 1:
                    prog = 75 + int(((i+1) / total_segs) * 20)
                    await show_progress(prog, "Matn tayyorlanmoqda...")

            final_text = "\n\n".join(paragraph_list)
            imzo = f"\n\n---\n👤 <b>Yaratuvchi:</b> {data['uname']}\n🤖 Bot: @{(await bot.get_me()).username}\n⏰ Vaqt: {get_uz_time()}"
            final_text += imzo

            update_stats('audio', fmt)

            if fmt == "txt":
                with open(result_path, "w", encoding="utf-8") as f: f.write(final_text)
                await call.message.answer_document(types.FSInputFile(result_path), caption="✅ <b>Natija tayyor!</b>", parse_mode="HTML")
            else:
                if len(final_text) > 4000:
                    for x in range(0, len(final_text), 4000):
                        await call.message.answer(final_text[x:x+4000], parse_mode="HTML")
                else: await call.message.answer(final_text, parse_mode="HTML")

            await wait_msg.delete()
        except Exception as e:
            await call.message.answer(f"❌ Xatolik: {str(e)}", parse_mode="HTML")
        finally:
            delete_temp_files(audio_path, result_path)
            waiting_users -= 1
            if chat_id in user_data: del user_data[chat_id]

# --- ADMIN PANEL ---
@dp.message(F.text == "🔑 Admin Panel", F.chat.id == ADMIN_ID)
async def admin_panel(m: types.Message):
    await m.answer("🚀 Admin Panel", reply_markup=get_admin_kb(), parse_mode="HTML")

@dp.callback_query(F.data == "adm_stats")
async def stats_cb(call: types.CallbackQuery):
    db = load_db()
    await call.message.answer(f"📊 Jami userlar: {len(db['users'])}", parse_mode="HTML")

@dp.callback_query(F.data == "adm_bc")
async def bc_cb(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("📢 Xabarni yuboring:", parse_mode="HTML")
    await state.set_state(AdminStates.waiting_for_bc)

@dp.message(AdminStates.waiting_for_bc)
async def bc_process(m: types.Message, state: FSMContext):
    await state.clear()
    db = load_db()
    cnt = 0
    msg = await m.answer("⏳ Yuborilmoqda...")
    for uid in db['users']:
        try:
            await bot.copy_message(chat_id=uid, from_chat_id=ADMIN_ID, message_id=m.message_id)
            cnt += 1
            await asyncio.sleep(0.05)
        except: pass
    await msg.edit_text(f"✅ {cnt} kishiga bordi.")

@dp.message(F.text == "🌐 Saytga kirish")
async def web_h(m: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="Sayt", url="https://shodlikai.github.io/new_3/dastur.html")
    await m.answer("Link:", reply_markup=kb.as_markup(), parse_mode="HTML")
            
