from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from config import ADMIN_ID

def get_main_menu(uid):
    kb = ReplyKeyboardBuilder()
    kb.button(text="🎧 Tahlil boshlash")
    kb.button(text="🌐 Saytga kirish")
    kb.button(text="👨‍💻 Bog'lanish")
    kb.button(text="ℹ️ Yordam")
    if uid == ADMIN_ID: kb.button(text="🔑 Admin Panel")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

# YANGI: To'g'ridan-to'g'ri Tarjima menyusi
def get_tr_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Shart emas (Original)", callback_data="tr_orig")
    kb.button(text="🇺🇿 O'zbekcha", callback_data="tr_uz")
    kb.button(text="🇷🇺 Ruscha", callback_data="tr_ru")
    kb.button(text="🇬🇧 Inglizcha", callback_data="tr_en")
    kb.adjust(1)
    return kb.as_markup()

def get_format_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="💬 Chat", callback_data="f_chat")
    kb.button(text="📁 TXT", callback_data="f_txt")
    kb.adjust(2)
    return kb.as_markup()

def get_admin_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Statistika", callback_data="adm_stats")
    kb.button(text="📋 Ro'yxat", callback_data="adm_list")
    kb.button(text="📢 Broadcast", callback_data="adm_bc")
    kb.adjust(1)
    return kb.as_markup()
    
