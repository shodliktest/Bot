# keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_menu(uid: int, admin_id: int):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("⚡ Groq Rejimi"), KeyboardButton("🎧 Whisper Rejimi"))
    kb.add(KeyboardButton("ℹ️ Yordam"))
    if uid == admin_id:
        kb.add(KeyboardButton("🔑 Admin Panel"))
    return kb

def admin_inline():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📊 Holat", callback_data="adm_status"),
        InlineKeyboardButton("🧹 Cache tozalash", callback_data="adm_clear_cache"),
    )
    kb.add(
        InlineKeyboardButton("🔄 Botni qayta ishga tushirish", callback_data="adm_restart"),
        InlineKeyboardButton("⏹️ Botni to‘xtatish", callback_data="adm_stop"),
    )
    return kb
