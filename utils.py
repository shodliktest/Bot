import os
import html
import pytz
from datetime import datetime
from moviepy.editor import VideoFileClip

# Konfiguratsiya
UZ_TZ = pytz.timezone('Asia/Tashkent')

def get_uz_time():
    """
    Hozirgi O'zbekiston vaqtini qaytaradi.
    Format: YYYY.MM.DD HH:MM:SS
    """
    return datetime.now(UZ_TZ).strftime('%Y.%m.%d %H:%M:%S')

def clean_text(text):
    """
    Telegram HTML formati uchun matnni tozalash.
    <, >, & kabi belgilarni xavfsiz holatga keltiradi.
    """
    if not text:
        return ""
    # Pastki chiziq va yulduzchalarni olib tashlaymiz (format buzilmasligi uchun)
    safe_text = text.replace("_", " ").replace("*", " ")
    # HTML belgilarni (escape) qilamiz
    return html.escape(safe_text)

def video_to_audio(video_path, audio_path):
    """
    Videodan (.mp4) audio (.mp3) ajratib oladi.
    MoviePy kutubxonasidan foydalanadi.
    """
    try:
        video_clip = VideoFileClip(video_path)
        # verbose=False va logger=None loglarni kamaytirish uchun
        video_clip.audio.write_audiofile(audio_path, verbose=False, logger=None)
        video_clip.close()
        return True
    except Exception as e:
        print(f"Video konvertatsiya xatosi: {e}")
        return False

def delete_temp_files(*file_paths):
    """
    Berilgan fayl manzillarini tekshirib, o'chirib tashlaydi.
    Server xotirasini tozalash uchun ishlatiladi.
    """
    for path in file_paths:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                print(f"Faylni o'chirishda xato ({path}): {e}")

def format_time_stamp(seconds):
    """
    Sekundlarni [MM:SS] formatiga o'tkazadi.
    Masalan: 75 sekund -> [01:15]
    """
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"[{minutes:02d}:{secs:02d}]"
  
