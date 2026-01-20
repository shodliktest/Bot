import asyncio
import os
import threading
import streamlit as st
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# KUTUBXONALAR
import whisper
from deep_translator import GoogleTranslator

# MODULLAR
from config import BOT_TOKEN, ADMIN_ID
from database import update_user, update_stats, load_db
from utils import get_uz_time, clean_text, video_to_audio, delete_temp_files, format_time_stamp
# Keyboards faylidan importlar
from keyboards import get_main_menu, get_lang_kb, get_format_kb, get_admin_kb

# --- MUHIM: BOT VA DP NI TEPADA YARATAMIZ ---
try:
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
except Exception as e:
    st.error(f"Bot token xatosi: {e}")
    st.stop()

# --- SOZLAMALAR ---
class UserStates(StatesGroup):
    waiting_for_contact_msg = State()

class AdminStates(StatesGroup):
    waiting_for_bc = State()

async_lock = asyncio.Lock()
waiting_users = 0
user_data = {}

# WHISPER YUKLASH
@st.cache_resource
def load_whisper():
    return whisper.load_model("base")

model_local = load_whisper()

# ---------------------------------------------------
# HANDLERLAR
# ---------------------------------------------------

# 1. START
@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    update_user(m.from_user)
    try:
        await bot.send_message(
            ADMIN_ID, 
            f"🆕 <b>YANGI USER:</b> {clean_text(m.from_user.full_name)} (ID: {m.from_user.id})", 
            parse_mode="HTML"
        )
    except: pass

    welcome = (
        f"👋 <b>Assalomu alaykum, {m.from_user.first_name}!</b>\n\n"
        f"🎙 <b>Suxandon AI</b> botiga xush kelibsiz!\n\n"
        "Men <b>Audio</b> va <b>Video</b> fayllarni matnga aylantiraman.\n"
        "👇 <b>Boshlash uchun fayl yuboring!</b>"
    )
    await m.answer(welcome, reply_markup=get_main_menu(m.from_user.id), parse_mode="HTML")

# 2. MEDIA HANDLER
@dp.message(F.audio | F.voice | F.video | F.video_note)
async def handle_media(m: types.Message):
    if m.audio: fid, fsize, ftype = m.audio.file_id, m.audio.file_size, "audio"
    elif m.voice: fid, fsize, ftype = m.voice.file_id, m.voice.file_size, "voice"
    elif m.video: fid, fsize, ftype = m.video.file_id, m.video.file_size, "video"
    elif m.video_note: fid, fsize, ftype = m.video_note.file_id, m.video_note.file_size, "video_note"
    else: return

    if fsize > 20 * 1024 * 1024:
        await m.answer("❌ <b>Fayl juda katta!</b> (Maks 20MB)", parse_mode="HTML")
        return

    u_h = f"@{m.from_user.username}" if m.from_user.username else m.from_user.full_name
    user_data[m.chat.id] = {
        'fid': fid, 'uname': u_h, 'type': ftype,
        'src_lang': 'auto', 'tr_lang': None, 'view': None
    }
    await m.answer("🗣 <b>Videodagi/Audiodagi til qaysi?</b>", reply_markup=get_lang_kb(), parse_mode="HTML")

# 3. CALLBACKS (Manba tili)
@dp.callback_query(F.data.startswith("src_"))
async def src_lang_cb(call: types.CallbackQuery):
    lang = call.data.replace("src_", "")
    user_data[call.message.chat.id]['src_lang'] = lang
    
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Tarjima kerak emas", callback_data="tr_orig")
    kb.button(text="🇺🇿 O'zbekcha", callback_data="tr_uz")
    kb.button(text="🇷🇺 Ruscha", callback_data="tr_ru")
    kb.button(text="🇬🇧 Inglizcha", callback_data="tr_en")
    kb.adjust(1)
    await call.message.edit_text("🌍 <b>Tarjima kerakmi?</b>", reply_markup=kb.as_markup(), parse_mode="HTML")

# Tarjima tili
@dp.callback_query(F.data.startswith("tr_"))
async def tr_lang_cb(call: types.CallbackQuery):
    lang = call.data.replace("tr_", "")
    user_data[call.message.chat.id]['tr_lang'] = lang
    
    kb = InlineKeyboardBuilder()
    kb.button(text="⏱ Split (Vaqt bilan)", callback_data="v_split")
    kb.button(text="📖 Full Context (Butun)", callback_data="v_full")
    await call.message.edit_text("📄 <b>Ko'rinishni tanlang:</b>", reply_markup=kb.as_markup(), parse_mode="HTML")

# Format
@dp.callback_query(F.data.startswith("v_"))
async def view_cb(call: types.CallbackQuery):
    user_data[call.message.chat.id]['view'] = call.data.replace("v_", "")
    await call.message.edit_text("💾 <b>Qanday formatda yuboray?</b>", reply_markup=get_format_kb(), parse_mode="HTML")

# 4. PROCESSOR (Asosiy ish)
@dp.callback_query(F.data.startswith("f_"))
async def start_process(call: types.CallbackQuery):
    global waiting_users
    chat_id = call.message.chat.id
    fmt = call.data.replace("f_", "")
    data = user_data.get(chat_id)
    await call.message.delete()

    waiting_users += 1
    wait_msg = await call.message.answer(f"⏳ Navbat: {waiting_users-1}")

    async with async_lock:
        input_path = ""
        audio_path = ""
        result_path = f"res_{chat_id}.txt"
        
        try:
            async def update_progress(p, txt):
                bar = "🟩" * (p // 10) + "⬜" * (10 - (p // 10))
                try: await wait_msg.edit_text(f"🚀 {txt}\n{bar} {p}%", parse_mode="HTML")
                except: pass

            await update_progress(10, "Yuklanmoqda...")
            is_video = data['type'] in ['video', 'video_note']
            ext = ".mp4" if is_video else ".mp3"
            input_path = f"input_{chat_id}{ext}"
            audio_path = f"audio_{chat_id}.mp3"

            file = await bot.get_file(data['fid'])
            await bot.download_file(file.file_path, input_path)

            if is_video:
                await update_progress(30, "Ovoz ajratilmoqda...")
                if not video_to_audio(input_path, audio_path): raise Exception("Video xatosi")
                delete_temp_files(input_path)
                input_path = "" 
            else:
                os.rename(input_path, audio_path)
                input_path = ""

            await update_progress(50, "AI Tahlil qilmoqda...")
            options = {}
            if data['src_lang'] != 'auto': options['language'] = data['src_lang']
            
            res = await asyncio.to_thread(model_local.transcribe, audio_path, **options)
            segments = res['segments']

            await update_progress(80, "Formatlash...")
            tr_code = data.get('tr_lang') if data.get('tr_lang') != "orig" else None
            final_text = ""

            if data.get('view') == "full":
                full_text = ""
                for s in segments:
                    seg_text = clean_text(s['text'].strip())
                    if tr_code:
                        try:
                            tr = GoogleTranslator(source='auto', target=tr_code).translate(seg_text)
                            full_text += f"{seg_text} ({clean_text(tr)}) "
                        except: full_text += f"{seg_text} "
                    else: full_text += f"{seg_text} "
                final_text = full_text.strip()
            else:
                for s in segments:
                    tm = format_time_stamp(s['start'])
                    seg_text = clean_text(s['text'].strip())
                    if tr_code:
                        try:
                            tr = GoogleTranslator(source='auto', target=tr_code).translate(seg_text)
                            final_text += f"{tm} {seg_text}\n<i>({clean_text(tr)})</i>\n\n"
                        except: final_text += f"{tm} {seg_text}\n\n"
                    else: final_text += f"{tm} {seg_text}\n\n"

            creator = data['uname']
            if not creator.startswith('@'): creator = f"@{creator.replace(' ', '_')}"
            imzo = f"\n\n---\n👤 <b>Yaratuvchi:</b> {creator}\n🤖 <b>Bot:</b> @{(await bot.get_me()).username}\n⏰ <b>Vaqt:</b> {get_uz_time()}"
            final_text += imzo

            update_stats(data['type'], fmt)

            if fmt == "txt":
                with open(result_path, "w", encoding="utf-8") as f: f.write(final_text)
                await call.message.answer_document(types.FSInputFile(result_path), caption="✅ Fayl tayyor!")
            else:
                if len(final_text) > 4000:
                    for i in range(0, len(final_text), 4000):
                        await call.message.answer(final_text[i:i+4000], parse_mode="HTML")
                else: await call.message.answer(final_text, parse_mode="HTML")

            await wait_msg.delete()

        except Exception as e:
            await call.message.answer(f"❌ Xatolik: {str(e)}")
        finally:
            delete_temp_files(input_path, audio_path, result_path)
            waiting_users -= 1
            if chat_id in user_data: del user_data[chat_id]

# 5. ADMIN
@dp.message(F.text == "🔑 Admin Panel", F.chat.id == ADMIN_ID)
async def admin_panel(m: types.Message):
    await m.answer("🚀 Admin Panel", reply_markup=get_admin_kb())

@dp.callback_query(F.data == "adm_stats")
async def stats_cb(call: types.CallbackQuery):
    db = load_db()
    await call.message.answer(f"📊 Jami userlar: {len(db['users'])}")

@dp.callback_query(F.data == "adm_list")
async def list_cb(call: types.CallbackQuery):
    db = load_db()
    users = db['users']
    if not users:
        await call.message.answer("❌ Ro'yxat bo'sh")
        return
    msg = f"📋 <b>USERS ({len(users)}):</b>\n\n"
    i = 1
    for uid, u in users.items():
        msg += f"<b>{i}. {u['name']}</b>\n👤 {u['username']}\n🆔 <code>{uid}</code>\n📅 {u['joined_at']}\n---\n"
        i += 1
    if len(msg) > 4000:
        for x in range(0, len(msg), 4000): await call.message.answer(msg[x:x+4000], parse_mode="HTML")
    else: await call.message.answer(msg, parse_mode="HTML")

@dp.callback_query(F.data == "adm_bc")
async def bc_cb(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("📢 Xabarni yuboring:")
    await state.set_state(AdminStates.waiting_for_bc)

@dp.message(AdminStates.waiting_for_bc)
async def bc_process(m: types.Message, state: FSMContext):
    await state.clear()
    db = load_db()
    users = db['users']
    cnt = 0
    msg = await m.answer("⏳ Yuborilmoqda...")
    for uid in users:
        try:
            await bot.copy_message(chat_id=uid, from_chat_id=ADMIN_ID, message_id=m.message_id)
            cnt += 1
            await asyncio.sleep(0.05)
        except: pass
    await msg.edit_text(f"✅ {cnt} kishiga bordi.")

# Feedback
@dp.message(F.text == "👨‍💻 Bog'lanish")
async def contact_h(m: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="✍️ Bot orqali yozish", callback_data="msg_to_admin")
    kb.adjust(1)
    await m.answer("Admin bilan aloqa:", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "msg_to_admin")
async def feedback_start(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.waiting_for_contact_msg)
    await call.message.answer("📝 Xabarni yozing:")

@dp.message(UserStates.waiting_for_contact_msg)
async def feedback_send(m: types.Message, state: FSMContext):
    await state.clear()
    await bot.send_message(ADMIN_ID, f"📩 #Aloqa\n👤 {m.from_user.full_name} ({m.from_user.id})\n\n{m.text}")
    await m.answer("✅ Yuborildi!")

@dp.message(F.text == "🌐 Saytga kirish")
async def web_h(m: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="Sayt", url="https://shodlikai.github.io/new_3/dastur.html")
    await m.answer("Link:", reply_markup=kb.as_markup())

@dp.message(F.text == "ℹ️ Yordam")
async def help_h(m: types.Message):
    await m.answer("Audio/Video yuboring va ko'rsatmalarga amal qiling.")
    
