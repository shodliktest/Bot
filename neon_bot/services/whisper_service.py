# services/whisper_service.py
import whisper

def init_whisper():
    try:
        return whisper.load_model("base")
    except Exception:
        return None

def transcribe_local(model, tmp_path: str):
    res = model.transcribe(tmp_path)
    return res["segments"]
