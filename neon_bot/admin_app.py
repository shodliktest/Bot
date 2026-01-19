# admin_app.py
"""
Streamlit admin panel.
Eslatma: xavfsizlik nuqtai nazaridan bu panel botni avtomatik ishga tushirmaydi.
Agar xohlasangiz, quyidagi "Start/Stop" tugmalari orqali main.start_bot_sync / stop_bot_sync chaqirishingiz mumkin,
lekin bu Streamlit muhitida ikki instansiya muammosiga olib kelmasligi uchun ehtiyot bo'ling.
Agar botni alohida jarayonda (VPS yoki Docker) ishga tushirsangiz, admin panel faqat monitoring uchun ishlaydi.
"""

import streamlit as st
import asyncio
import time

from config import load_config
import main  # import main modulidan rt obyekti va start/stop funksiyalariga kirish

st.set_page_config(page_title="Neon Hybrid Admin", layout="wide")
st.title("🤖 Neon Hybrid Bot — Admin panel")

config = load_config()
rt = main.rt  # global runtime singleton from main.py

# Sidebar: konfiguratsiya
st.sidebar.header("⚙️ Sozlamalar")
st.sidebar.write(f"Admin ID: {config['ADMIN_ID']}")
st.sidebar.write(f"Default mode: {config['DEFAULT_MODE']}")
st.sidebar.write(f"Groq API: {'✅' if config['GROQ_API_KEY'] else '❌'}")
st.sidebar.write(f"Bot token: {'✅' if config['BOT_TOKEN'] else '❌'}")
st.sidebar.write(f"Firebase: {'✅' if config['FIREBASE_CONF'] else '❌'}")

# Top controls
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    start_btn = st.button("▶️ Botni ishga tushirish", use_container_width=True)
with col2:
    restart_btn = st.button("🔄 Botni qayta ishga tushirish", use_container_width=True)
with col3:
    stop_btn = st.button("⏹️ Botni to‘xtatish", use_container_width=True)

st.divider()

# Status
st.subheader("📊 Holat")
st.write(f"Bot running: **{rt.is_running}**")
st.write(f"Active tasks: **{len(rt.tasks)}**")
st.write(f"Cached translations: **{len(rt.translation_cache)}**")

# RAM loglar
st.subheader("📝 RAM loglar (so'nggi 100)")
st.code("\n".join(rt.logs[-100:]) or "Hozircha loglar yo'q.", language="text")

# Firestore ma'lumotlari (agar mavjud bo'lsa)
from services.firebase import init_firebase, list_users, list_logs

db = init_firebase(config["FIREBASE_CONF"])
st.divider()
st.subheader("👥 Firestore — Users")
if db:
    users = list_users(db, limit=200)
    if users:
        st.table(users)
    else:
        st.info("Hozircha userlar yo‘q.")
else:
    st.warning("Firebase ulanmadi yoki konfiguratsiya yo'q.")

st.subheader("📒 Firestore — Logs")
if db:
    logs = list_logs(db, limit=200)
    if logs:
        st.table(logs)
    else:
        st.info("Hozircha loglar yo‘q.")
else:
    st.warning("Firebase ulanmadi yoki konfiguratsiya yo'q.")

st.divider()
st.subheader("🔐 Eslatma va xavfsizlik")
st.info(
    "Agar siz botni Streamlit ichida ishga tushirsangiz, iltimos bitta instansiya ekanligiga ishonch hosil qiling. "
    "Agar bot allaqachon boshqa serverda ishlayotgan bo'lsa, shu panel orqali start qilish TerminatedByOtherGetUpdates xatosiga olib keladi."
)

# Start / Stop handling
def _start_bot_from_panel():
    """
    Ehtiyotkor start: agar bot allaqachon ishlamayotgan bo'lsa, start_bot_sync chaqiriladi.
    Agar siz Streamlit Cloud kabi muhitda bo'lsangiz va alohida jarayonni ishga tushirishni xohlasangiz,
    'python main.py' ni serverda ishga tushirishni tavsiya qilamiz.
    """
    if rt.is_running:
        st.warning("Bot allaqachon ishlamoqda.")
        return
    try:
        # Synchronous wrapper chaqirish (bloklaydi, shuning uchun qisqa xabar bilan cheklaymiz)
        st.info("Bot ishga tushirilmoqda... (bu jarayon bir necha soniya olishi mumkin)")
        main.start_bot_sync()
        time.sleep(1)
        st.success("Start buyruq yuborildi. Holatni tekshiring.")
    except Exception as e:
        st.error(f"Start paytida xatolik: {e}")

def _stop_bot_from_panel():
    if not rt.is_running:
        st.warning("Bot hozir ishlamayapti.")
        return
    try:
        st.info("Bot to'xtatilmoqda...")
        main.stop_bot_sync()
        time.sleep(1)
        st.success("Stop buyruq yuborildi. Holatni tekshiring.")
    except Exception as e:
        st.error(f"Stop paytida xatolik: {e}")

if start_btn:
    _start_bot_from_panel()

if stop_btn:
    _stop_bot_from_panel()

if restart_btn:
    if rt.is_running:
        _stop_bot_from_panel()
        time.sleep(1)
    _start_bot_from_panel()
