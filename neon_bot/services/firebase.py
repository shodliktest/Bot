# services/firebase.py
import firebase_admin
from firebase_admin import credentials, firestore

def init_firebase(firebase_conf: dict):
    if not firebase_conf:
        return None
    try:
        cred = credentials.Certificate(firebase_conf)
        firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception:
        return None

def save_user_mode(db, chat_id: int, mode: str):
    if not db:
        return
    db.collection("users").document(str(chat_id)).set({
        "mode": mode
    }, merge=True)

def get_user_mode(db, chat_id: int, default_mode: str = "groq"):
    if not db:
        return default_mode
    doc = db.collection("users").document(str(chat_id)).get()
    if doc.exists:
        return doc.to_dict().get("mode", default_mode)
    return default_mode

def save_log(db, entry: dict):
    if not db:
        return
    db.collection("logs").add(entry)

def list_users(db, limit: int = 100):
    if not db:
        return []
    return [d.to_dict() | {"id": d.id} for d in db.collection("users").limit(limit).stream()]

def list_logs(db, limit: int = 100):
    if not db:
        return []
    return [d.to_dict() | {"id": d.id} for d in db.collection("logs").order_by("ts", direction=firestore.Query.DESCENDING).limit(limit).stream()]
