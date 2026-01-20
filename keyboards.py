from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from config import ADMIN_ID

# 1. ASOSIY MENYU (get_main_menu)
def get_main_menu(uid):
    kb = ReplyKeyboardBuilder()
    kb.button(text="🎧 Tahlil boshlash")
    kb.button(text="🌐 Saytga kirish")
    kb.button(text="👨‍💻 Bog'lanish")
    kb.button(text="ℹ️ Yordam")
    if uid == ADMIN_ID: 
        kb.button(text="🔑 Admin Panel")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

# 2. TIL TANLASH (get_lang_kb)
def get_lang_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="🇺🇿 O'zbekcha", callback_data="src_uz")
    kb.button(text="🇷🇺 Ruscha", callback_data="src_ru")
    kb.button(text="🇬🇧 Inglizcha", callback_data="src_en")
    kb.button(text="🌍 Auto (Aniqlash)", callback_data="src_auto")
    kb.adjust(2)
    return kb.as_markup()

# 3. FORMAT TANLASH (get_format_kb)
def get_format_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="💬 Chat", callback_data="f_chat")
    kb.button(text="📁 TXT", callback_data="f_txt")
    kb.adjust(2)
    return kb.as_markup()

# 4. ADMIN PANEL (get_admin_kb)
def get_admin_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Statistika", callback_data="adm_stats")
    kb.button(text="📋 Ro'yxat", callback_data="adm_list")
    kb.button(text="📢 Broadcast", callback_data="adm_bc")
    kb.adjust(1)
    return kb.as_markup()
    
