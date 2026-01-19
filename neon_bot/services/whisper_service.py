import whisper
import gc
import os
import torch

_model_cache = None

def load_whisper_model(model_name: str = "base"):
    global _model_cache
    if _model_cache is None:
        print(f"--- Model yuklanmoqda: {model_name} ---")
        _model_cache = whisper.load_model(model_name)
    return _model_cache

def transcribe_and_clean(tmp_path: str):
    """Tahlil qiladi va RAM/Diskni darhol tozalaydi"""
    model = load_whisper_model()
    result_text = ""
    
    try:
        # 1. Tahlil qilish
        if os.path.exists(tmp_path):
            res = model.transcribe(tmp_path, fp16=False)
            result_text = res.get("text", "")
    except Exception as e:
        print(f"Transkripsiya xatosi: {e}")
    finally:
        # 2. AVTO-TOZALASH
        # Diskni tozalash
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        
        # RAMni tozalash
        gc.collect() 
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        print("♻️ RAM va Vaqtinchalik fayllar tozalandi.")
        
    return result_text
