# services/whisper_service.py
import whisper

def init_whisper():
    try:
        # Streamlit Cloud uchun 'base' yoki 'tiny' modeli tavsiya etiladi
        return whisper.load_model("base")
    except Exception:
        return None

def transcribe_local(model, tmp_path: str):
    # fp16=False - CPU da ishlash uchun shart!
    res = model.transcribe(tmp_path, fp16=False)
    return res["segments"]
