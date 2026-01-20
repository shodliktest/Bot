import json
import os
from datetime import datetime
from config import UZ_TZ

DB_FILE = "database.json"

# Boshlang'ich shablon
EMPTY_DB = {
    "users": {},       # {id: {name, username, joined_at, last_active}}
    "stats": {
        "total_processed": 0,
        "video": 0,
        "audio": 0,
        "format_txt": 0,
        "format_chat": 0
    }
}

def load_db():
    if not os.path.exists(DB_FILE):
        save_db(EMPTY_DB)
        return EMPTY_DB
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

def update_user(user):
    """Foydalanuvchini qo'shish yoki vaqtini yangilash"""
    db = load_db()
    uid = str(user.id)
    now = datetime.now(UZ_TZ).strftime("%Y-%m-%d %H:%M:%S")
    
    if uid not in db["users"]:
        db["users"][uid] = {
            "name": user.full_name,
            "username": f"@{user.username}" if user.username else "Yo'q",
            "joined_at": now,
            "last_active": now
        }
    else:
        db["users"][uid]["last_active"] = now
        # Ismi o'zgargan bo'lsa yangilaymiz
        db["users"][uid]["name"] = user.full_name 
    
    save_db(db)

def update_stats(file_type, output_format):
    """Statistikani oshirish (video/audio, txt/chat)"""
    db = load_db()
    db["stats"]["total_processed"] += 1
    
    # Fayl turi bo'yicha
    if file_type in ["video", "video_note"]:
        db["stats"]["video"] += 1
    else:
        db["stats"]["audio"] += 1
        
    # Format bo'yicha
    if output_format == "txt":
        db["stats"]["format_txt"] += 1
    else:
        db["stats"]["format_chat"] += 1
        
    save_db(db)

def get_dashboard_data():
    """Streamlit uchun tayyor raqamlar"""
    db = load_db()
    users = db["users"]
    stats = db["stats"]
    
    today = datetime.now(UZ_TZ).strftime("%Y-%m-%d")
    current_month = datetime.now(UZ_TZ).strftime("%Y-%m")
    
    daily_active = sum(1 for u in users.values() if u["last_active"].startswith(today))
    monthly_active = sum(1 for u in users.values() if u["last_active"].startswith(current_month))
    
    return {
        "total_users": len(users),
        "daily_active": daily_active,
        "monthly_active": monthly_active,
        "stats": stats,
        "user_list": users # Ro'yxat uchun
  }
  
