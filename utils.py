import os
import html
import pytz
from datetime import datetime

# Konfiguratsiya
UZ_TZ = pytz.timezone('Asia/Tashkent')

def get_uz_time():
    """O'zbekiston vaqti"""
    return datetime.now(UZ_TZ).strftime('%Y.%m.%d %H:%M:%S')

def clean_text(text):
    """HTML belgilarni tozalash"""
    if not text: return ""
    return html.escape(text.replace("_", " ").replace("*", " "))

def delete_temp_files(*file_paths):
    """Fayllarni o'chirish"""
    for path in file_paths:
        if path and os.path.exists(path):
            try: os.remove(path)
            except: pass

def format_time_stamp(seconds):
    """[MM:SS] format"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"[{minutes:02d}:{secs:02d}]"
    
