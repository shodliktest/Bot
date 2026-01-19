import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Global o'zgaruvchi db ni keshlab qo'yish uchun
_db = None

def init_firebase(firebase_conf: dict):
    global _db
    if _db:
        return _db
    
    if not firebase_conf:
        print("Firebase configuration is missing!")
        return None
        
    try:
        # App allaqachon init bo'lganini tekshirish
        if not firebase_admin._apps:
            cred = credentials.Certificate(firebase_conf)
            firebase_admin.initialize_app(cred)
        
        _db = firestore.client()
        return _db
    except Exception as e:
        print(f"Firebase Initialization Error: {e}")
        return None

def save_user_mode(db, chat_id: int, mode: str):
    if not db: return
    
    user_ref = db.collection("users").document(str(chat_id))
    user_ref.set({
        "mode": mode,
        "last_active": datetime.now() # Oxirgi faollik vaqtini saqlash foydali
    }, merge=True)

def delete_user(db, chat_id: int):
    """Foydalanuvchini o'chirish funksiyasi"""
    if not db: return
    db.collection("users").document(str(chat_id)).delete()

def get_stats(db):
    """Statistika uchun: foydalanuvchilar sonini qaytaradi"""
    if not db: return 0
    # Eslatma: Katta bazalarda .stream() o'rniga count() ishlatish tavsiya etiladi
    docs = db.collection("users").list_documents()
    return len(list(docs))

def save_log(db, user_id: int, action: str, details: str = ""):
    """Yaxshilangan log saqlash"""
    if not db: return
    db.collection("logs").add({
        "user_id": user_id,
        "action": action,
        "details": details,
        "ts": firestore.SERVER_TIMESTAMP # Server vaqti bilan saqlash
    })
