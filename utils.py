import os
import html
import pytz
from datetime import datetime

# MoviePy importi uchun ultra-xavfsiz blok
try:
    from moviepy.editor import VideoFileClip
except (ImportError, ModuleNotFoundError):
    try:
        from moviepy.video.io.VideoFileClip import VideoFileClip
    except Exception:
        # Agar moviepy umuman o'rnatilmagan bo'lsa, xato bermasligi uchun
        VideoFileClip = None

# Konfiguratsiya
UZ_TZ = pytz.timezone('Asia/Tashkent')

def get_uz_time():
    """
    O'zbekiston vaqtini qaytaradi (YYYY.MM.DD HH:MM:SS)
    """
    return datetime.now(UZ_TZ).strftime('%Y.%m.%d %H:%M:%S')

def clean_text(text):
    """
    Telegram HTML formati uchun matnni xavfsiz holatga keltiradi.
    """
    if not text:
        return ""
    # Formatni buzuvchi belgilarni tozalash
    safe_text = text.replace("_", " ").replace("*", " ")
    return html.escape(safe_text)

def video_to_audio(video_path, audio_path):
    """
    Videodan audio ajratib oladi. 
    Agar MoviePy o'rnatilmagan bo'lsa, xabar beradi.
    """
    if VideoFileClip is None:
        print("Xato: MoviePy kutubxonasi o'rnatilmagan!")
        return False
        
    try:
        video_clip = VideoFileClip(video_path)
        # verbose va logger o'chirilgan (loglar serverda xalaqit bermasligi uchun)
        video_clip.audio.write_audiofile(audio_path, verbose=False, logger=None)
        video_clip.close()
        return True
    except Exception as e:
        print(f"Video konvertatsiya xatosi: {str(e)}")
        return False

def delete_temp_files(*file_paths):
    """
    Vaqtinchalik yaratilgan fayllarni o'chirib, server xotirasini tozalaydi.
    """
    for path in file_paths:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                print(f"Faylni o'chirishda xatolik ({path}): {e}")

def format_time_stamp(seconds):
    """
    Whisper sekundlarini [MM:SS] ko'rinishiga o'tkazadi.
    """
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"[{minutes:02d}:{secs:02d}]"
    
