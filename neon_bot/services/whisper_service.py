# services/whisper_service.py
import whisper
import os

# Modelni xotirada bir marta saqlash uchun global o'zgaruvchi
_cached_model = None

def load_whisper_model(model_name: str = "base"):
    global _cached_model
    if _cached_model is not None:
        return _cached_model
    
    try:
        print(f"--- Whisper modeli yuklanmoqda: {model_name} ---")
        _cached_model = whisper.load_model(model_name)
        return _cached_model
    except Exception as e:
        print(f"❌ Whisper yuklashda xato: {e}")
        return None

def transcribe_local(model, tmp_path: str):
    if model is None:
        return "Model yuklanmagan, transkripsiya qilib bo'lmaydi."
        
    try:
        # Fayl mavjudligini tekshirish
        if not os.path.exists(tmp_path):
            return "Fayl topilmadi!"
            
        # fp16=False - CPU da ishlash uchun juda muhim!
        res = model.transcribe(tmp_path, fp16=False)
        return res.get("text", "") # Faqat matnni qaytarish osonroq bo'lishi mumkin
    except Exception as e:
        print(f"❌ Transkripsiya xatosi: {e}")
        return None
