import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

_db = None

def init_firebase(firebase_conf: dict):
    global _db
    if _db: return _db
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(firebase_conf)
            firebase_admin.initialize_app(cred)
        _db = firestore.client()
        return _db
    except Exception as e:
        print(f"Firebase Init Error: {e}")
        return None

def save_transcription(db, chat_id: int, text: str, audio_url: str = None):
    """Natijani Firebase'ga saqlash va log yuritish"""
    if not db: return
    
    # Foydalanuvchi ma'lumotlarini yangilash
    db.collection("users").document(str(chat_id)).set({
        "last_transcription": text,
        "last_seen": datetime.now()
    }, merge=True)
    
    # Tarix (History) bo'limiga qo'shish
    db.collection("history").add({
        "chat_id": chat_id,
        "text": text,
        "ts": firestore.SERVER_TIMESTAMP
    })
