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

try:
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
except Exception as e:
    st.error(f"Token xatosi: {e}")
    st.stop()

# --- STATES ---
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

# --- 1. START VA TANISHUV ---
@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    update_user(m.from_user)
    
    # Adminga to'liq hisobot
    try:
        u_link = f"@{m.from_user.username}" if m.from_user.username else "Username yo'q"
        msg = (
            f"🆕 <b>YANGI USER QO'SHILDI:</b>\n"
            f"👤 Ismi: {m.from_user.full_name}\n"
            f"🆔 ID: <code>{m.from_user.id}</code>\n"
            f"🔗 Link: {u_link}"
        )
        await bot.send_message(ADMIN_ID, msg, parse_mode="HTML")
    except: pass

    welcome = (
        f"👋 <b>Assalomu alaykum, {m.from_user.first_name}!</b>\n\n"
        f"🎙 <b>Suxandon AI</b> botiga xush kelibsiz.\n"
        "Men har qanday audio xabarni, qo'shiqni yoki intervyuni yozma matnga aylantirib, kerakli tilga tarjima qilib beraman.\n\n"
        "🚀 <b>Ishni boshlash uchun menga audio fayl yoki ovozli xabar yuboring!</b>"
    )
    await m.answer(welcome, reply_markup=get_main_menu(m.from_user.id), parse_mode="HTML")

# --- 2. MUKAMMAL QO'LLANMA (SIZ SO'RAGAN MATN) ---
@dp.message(F.text == "ℹ️ Yordam")
async def help_h(m: types.Message):
    text = (
        "📚 <b>SUXANDON AI - QO'LLANMA</b>\n\n"
        "Bu bot orqali siz audio xabarlar, qo'shiqlar yoki intervyularni matn ko'rinishiga o'tkazishingiz mumkin.\n\n"
        "<b>Qanday ishlatiladi?</b>\n"
        "1️⃣ <b>Audio yuboring:</b> Botga mp3 fayl yoki voice (ovozli xabar) yuboring.\n"
        "2️⃣ <b>Tarjima tanlang:</b> Matnni o'z holicha qoldirish yoki o'zbek/rus/ingliz tiliga tarjima qilishni tanlang. Tarjima asl matn yonida (qavs ichida) beriladi.\n"
        "3️⃣ <b>Ko'rinishni tanlang:</b>\n"
        "   🔹 <i>Time Split:</i> Har bir gap oldida vaqt [00:15] ko'rsatiladi. Subtitr uchun qulay.\n"
        "   🔹 <i>Full Context:</i> Vaqtlarsiz, xuddi kitob matnidek yaxlit chiqadi.\n"
        "4️⃣ <b>Formatni tanlang:</b>\n"
        "   🔹 <i>TXT Fayl:</i> Matnni alohida fayl qilib tashlaydi (uzun matnlar uchun).\n"
        "   🔹 <i>Chat:</i> Matnni shu yerning o'ziga xabar qilib yozadi.\n\n"
        "⚠️ <b>Cheklovlar:</b> Fayl hajmi 20MB dan oshmasligi kerak.\n\n"
        "👨‍💻 <b>Muammo bormi?</b> 'Bog'lanish' tugmasi orqali adminga yozishingiz mumkin."
    )
    await m.answer(text, parse_mode="HTML")

# --- 3. ADMIN BILAN ALOQA (FEEDBACK) ---
@dp.message(F.text == "👨‍💻 Bog'lanish")
async def contact_h(m: types.Message):
    text = (
        "👨‍💻 <b>Admin bilan aloqa bo'limi</b>\n\n"
        "Agar bot ishlashida xatolik topsangiz yoki takliflaringiz bo'lsa, adminga to'g'ridan-to'g'ri xabar yozishingiz mumkin.\n\n"
        "👇 <i>Pastdagi tugmani bosib, xabaringizni yozing:</i>"
    )
    await m.answer(text, reply_markup=get_contact_kb(), parse_mode="HTML")

@dp.callback_query(F.data == "msg_to_admin")
async def feedback_start(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.waiting_for_contact_msg)
    await call.message.answer("📝 <b>Marhamat, xabaringizni yozib qoldiring:</b>", parse_mode="HTML")
    await call.answer()

@dp.message(UserStates.waiting_for_contact_msg)
async def feedback_send(m: types.Message, state: FSMContext):
    await state.clear()
    
    # Adminga boradigan to'liq xabar
    u_link = f"@{m.from_user.username}" if m.from_user.username else "yo'q"
    admin_msg = (
        f"📩 <b>YANGI MUROJAAT KELDI:</b>\n"
        f"👤 User: {m.from_user.full_name}\n"
        f"🆔 ID: <code>{m.from_user.id}</code>\n"
        f"🔗 Link: {u_link}\n\n"
        f"📝 <b>Xabar matni:</b>\n{m.text}"
    )
    
    await bot.send_message(ADMIN_ID, admin_msg, parse_mode="HTML")
    await m.answer("✅ <b>Xabaringiz adminga muvaffaqiyatli yuborildi!</b>\nTez orada javob olasiz.", parse_mode="HTML")

# --- 4. ADMIN REPLY (JAVOB QAYTARISH) ---
@dp.message(F.chat.id == ADMIN_ID, F.reply_to_message)
async def admin_reply_handler(m: types.Message):
    # Admin reply qilgan xabarni tekshiramiz
    original_msg = m.reply_to_message.text
    id_match = re.search(r"ID: (\d+)", original_msg)
    
    if id_match:
        user_id = int(id_match.group(1))
        try:
            await bot.send_message(
                user_id,
                f"💬 <b>Admin javobi:</b>\n\n{m.text}",
                parse_mode="HTML"
            )
            await m.answer(f"✅ Javob ID: {user_id} ga yuborildi.")
        except Exception as e:
            await m.answer(f"❌ Xatolik: User botni bloklagan bo'lishi mumkin.\n{e}")
    else:
        await m.answer("❌ User ID si topilmadi. Iltimos, faqat botdan kelgan murojaat xabariga reply qiling.")

# --- 5. AUDIO QABUL QILISH VA SOZLAMALAR ---

@dp.message(F.audio | F.voice)
async def handle_audio(m: types.Message):
    fid = m.audio.file_id if m.audio else m.voice.file_id
    fsize = m.audio.file_size if m.audio else m.voice.file_size

    if fsize > 20 * 1024 * 1024:
        await m.answer("❌ <b>Kechirasiz, fayl hajmi 20MB dan oshmasligi kerak!</b>\nIltimos, kichikroq fayl yuboring.", parse_mode="HTML")
        return

    user_data[m.chat.id] = {
        'fid': fid, 'uname': m.from_user.full_name, 'tr_lang': None, 'view': None
    }
    
    text = (
        "🌍 <b>Audio qabul qilindi. Uni tarjima qilaymi?</b>\n\n"
        "<i>Agarda tarjima tilini tanlasangiz, asl matn qoladi va uning ostida (qavs ichida) tarjimasi yoziladi.</i>"
    )
    await m.answer(text, reply_markup=get_tr_kb(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("tr_"))
async def tr_lang_cb(call: types.CallbackQuery):
    lang = call.data.replace("tr_", "")
    user_data[call.message.chat.id]['tr_lang'] = lang
    
    text = (
        "📄 <b>Matn ko'rinishi qanday bo'lsin?</b>\n\n"
        "⏱ <b>Time Split:</b> Har bir gap boshida vaqt [00:15] ko'rsatiladi (Subtitr uchun).\n"
        "📖 <b>Full Context:</b> Vaqtlarsiz, yaxlit kitob matni shaklida (O'qish uchun)."
    )
    await call.message.edit_text(text, reply_markup=get_split_kb(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("v_"))
async def view_cb(call: types.CallbackQuery):
    user_data[call.message.chat.id]['view'] = call.data.replace("v_", "")
    
    text = (
        "💾 <b>Natijani qaysi formatda olishni xohlaysiz?</b>\n\n"
        "📁 <b>TXT Fayl:</b> Hujjat sifatida tashlanadi (yuklab olish va saqlash uchun).\n"
        "💬 <b>Chat:</b> Oddiy xabar sifatida shu yerga yoziladi."
    )
    await call.message.edit_text(text, reply_markup=get_format_kb(), parse_mode="HTML")

# --- 6. PROCESSOR (PROGRESS BAR BILAN) ---
@dp.callback_query(F.data.startswith("f_"))
async def start_process(call: types.CallbackQuery):
    global waiting_users
    chat_id = call.message.chat.id
    fmt = call.data.replace("f_", "")
    data = user_data.get(chat_id)
    await call.message.delete()

    waiting_users += 1
    wait_msg = await call.message.answer(f"⏳ <b>So'rovingiz navbatga qo'yildi...</b>\nSizning navbatingiz: {waiting_users}", parse_mode="HTML")

    async with async_lock:
        audio_path = f"audio_{chat_id}.mp3"
        result_path = f"res_{chat_id}.txt"
        
        # Progress Bar funksiyasi (Batafsil ma'lumot bilan)
        async def show_progress(percent, status_text):
            blocks = int(percent // 5) 
            bar = "🟩" * blocks + "⬜" * (20 - blocks)
            try:
                await wait_msg.edit_text(
                    f"⚙️ <b>Jarayon ketmoqda...</b>\n"
                    f"ℹ️ {status_text}\n\n"
                    f"{bar} <b>{percent}%</b>",
                    parse_mode="HTML"
                )
            except: pass

        try:
            # 1. YUKLASH
            for p in range(0, 26, 5):
                await show_progress(p, "Audio fayl serverga yuklanmoqda...")
                await asyncio.sleep(0.1)
            
            file = await bot.get_file(data['fid'])
            await bot.download_file(file.file_path, audio_path)

            # 2. TAHLIL
            await show_progress(30, "Sun'iy intellekt ovozni tahlil qilmoqda...")
            res = await asyncio.to_thread(model_local.transcribe, audio_path)
            segments = res['segments']
            
            await show_progress(70, "Matn tayyor. Tarjima va formatlash boshlandi...")

            # 3. FORMATLASH
            tr_code = data.get('tr_lang') if data.get('tr_lang') != "orig" else None
            paragraph_list = []
            
            total_segs = len(segments)
            for i, s in enumerate(segments):
                # Matnni tozalash
                orig = clean_text(s['text'].strip())
                if not orig: continue
                
                block = orig
                # Tarjima
                if tr_code:
                    try:
                        tr = await asyncio.to_thread(GoogleTranslator(source='auto', target=tr_code).translate, s['text'])
                        # DIZAYN: Asl matn + (Italic tarjima)
                        block = f"{orig}\n<i>({clean_text(tr)})</i>"
                    except: pass
                
                # Split vaqtini qo'shish
                if data.get('view') == "split":
                    block = f"<b>{format_time_stamp(s['start'])}</b> {block}"
                
                paragraph_list.append(block)
                
                # Progress yangilash (Har 5 ta segmentda)
                if i % 5 == 0 or i == total_segs - 1:
                    prog = 75 + int(((i+1) / total_segs) * 20)
                    await show_progress(prog, f"Formatlash: {i+1}/{total_segs} qism...")

            # Yakuniy matnni yig'ish (Abzaslar bilan)
            final_text = "\n\n".join(paragraph_list)
            
            creator = data['uname']
            if not creator.startswith('@'): creator = f"@{creator.replace(' ', '_')}"
            imzo = f"\n\n---\n👤 <b>Yaratuvchi:</b> {creator}\n🤖 <b>Bot:</b> @{(await bot.get_me()).username}\n⏰ <b>Vaqt:</b> {get_uz_time()}"
            final_text += imzo

            update_stats('audio', fmt)

            # 4. YUBORISH
            await show_progress(99, "Fayl sizga yuborilmoqda...")

            if fmt == "txt":
                with open(result_path, "w", encoding="utf-8") as f: f.write(final_text)
                await call.message.answer_document(
                    types.FSInputFile(result_path), 
                    caption="✅ <b>Mana, natija tayyor!</b>\nFaylni yuklab olib, bemalol o'qishingiz mumkin.", 
                    parse_mode="HTML"
                )
            else:
                if len(final_text) > 4000:
                    for i in range(0, len(final_text), 4000):
                        await call.message.answer(final_text[i:i+4000], parse_mode="HTML")
                else: 
                    await call.message.answer(final_text, parse_mode="HTML")

            await wait_msg.delete()

        except Exception as e:
            await call.message.answer(f"❌ <b>Jarayonda xatolik yuz berdi:</b>\n{str(e)}", parse_mode="HTML")
        finally:
            delete_temp_files(audio_path, result_path)
            waiting_users -= 1
            if chat_id in user_data: del user_data[chat_id]

# --- 7. ADMIN PANEL (FULL) ---
@dp.message(F.text == "🔑 Admin Panel", F.chat.id == ADMIN_ID)
async def admin_panel(m: types.Message):
    await m.answer("🚀 <b>Admin Panelga xush kelibsiz!</b>\nQuyidagi menyudan kerakli bo'limni tanlang:", reply_markup=get_admin_kb(), parse_mode="HTML")

@dp.callback_query(F.data == "adm_stats")
async def stats_cb(call: types.CallbackQuery):
    db = load_db()
    await call.message.answer(f"📊 <b>Statistika:</b>\n\nJami foydalanuvchilar: {len(db['users'])} ta", parse_mode="HTML")

@dp.callback_query(F.data == "adm_list")
async def list_cb(call: types.CallbackQuery):
    db = load_db()
    users = db['users']
    if not users:
        await call.message.answer("❌ Ro'yxat bo'sh")
        return
    msg = f"📋 <b>FOYDALANUVCHILAR RO'YXATI ({len(users)}):</b>\n\n"
    i = 1
    for uid, u in users.items():
        msg += f"<b>{i}. {u['name']}</b>\n👤 {u['username']}\n🆔 <code>{uid}</code>\n📅 {u['joined_at']}\n---\n"
        i += 1
    if len(msg) > 4000:
        for x in range(0, len(msg), 4000): await call.message.answer(msg[x:x+4000], parse_mode="HTML")
    else: await call.message.answer(msg, parse_mode="HTML")

@dp.callback_query(F.data == "adm_bc")
async def bc_cb(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("📢 <b>Broadcast (Habar tarqatish):</b>\n\nBarcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni (matn, rasm, video) shu yerga tashlang.", parse_mode="HTML")
    await state.set_state(AdminStates.waiting_for_bc)

@dp.message(AdminStates.waiting_for_bc)
async def bc_process(m: types.Message, state: FSMContext):
    await state.clear()
    db = load_db()
    users = db['users']
    cnt = 0
    msg = await m.answer("⏳ <b>Xabar tarqatilmoqda...</b>")
    for uid in users:
        try:
            await bot.copy_message(chat_id=uid, from_chat_id=ADMIN_ID, message_id=m.message_id)
            cnt += 1
            await asyncio.sleep(0.05)
        except: pass
    await msg.edit_text(f"✅ <b>Muvaffaqiyatli yakunlandi!</b>\n\nJami {cnt} ta foydalanuvchiga xabar bordi.", parse_mode="HTML")

# --- 8. SAYTGA KIRISH ---
@dp.message(F.text == "🌐 Saytga kirish")
async def web_h(m: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="Saytga o'tish", url="https://shodlikai.github.io/new_3/dastur.html")
    await m.answer("🌐 <b>Bizning rasmiy veb-saytimiz:</b>\n\nQuyidagi tugma orqali loyiha sahifasiga o'tishingiz mumkin:", reply_markup=kb.as_markup(), parse_mode="HTML")
    
