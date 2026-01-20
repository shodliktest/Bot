import os
import pytz
from datetime import datetime

# Konfiguratsiya
UZ_TZ = pytz.timezone('Asia/Tashkent')

def get_uz_time():
    """O'zbekiston vaqti (YYYY.MM.DD HH:MM:SS)"""
    return datetime.now(UZ_TZ).strftime('%Y.%m.%d %H:%M:%S')

def clean_text(text):
    """
    Telegram HTML formati uchun matnni xavfsiz holatga keltirish.
    Apostrofni (&#x27;) kodga aylantirmaslik uchun faqat asosiy belgilarni o'zgartiradi.
    """
    if not text:
        return ""
    # Telegram HTML rejimi uchun faqat bularni escape qilish shart
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def delete_temp_files(*file_paths):
    """Vaqtinchalik fayllarni o'chirish"""
    for path in file_paths:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except:
                pass

def format_time_stamp(seconds):
    """Whisper sekundlarini [MM:SS] ko'rinishiga o'tkazish"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"[{minutes:02d}:{secs:02d}]"
