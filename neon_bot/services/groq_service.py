# services/groq_service.py
from groq import Groq

def init_groq(api_key: str):
    if not api_key:
        return None
    try:
        return Groq(api_key=api_key)
    except Exception:
        return None

def transcribe_groq(client_groq, tmp_path: str):
    with open(tmp_path, "rb") as f:
        res = client_groq.audio.transcriptions.create(
            file=(tmp_path, f.read()),
            model="whisper-large-v3-turbo",
            response_format="verbose_json"
        )
    return res.segments
