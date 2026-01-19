# admin_app.py
import streamlit as st
import asyncio
from config import load_config
from runtime import Runtime
from services.firebase import init_firebase, list_users, list_logs

st.set_page_config(page_title="Neon Hybrid Admin", layout="wide")
st.title("🤖 Neon Hybrid Bot — Admin panel")

if "rt" not in st.session_state:
    st.session_state.rt = Runtime()

rt = st.session_state.rt
config = load_config()

st.sidebar.header("⚙️ Sozlamalar")
st.sidebar.write(f"Admin ID: {config['ADMIN_ID']}")
st.sidebar.write(f"Default mode: {config['DEFAULT_MODE']}")
st.sidebar.write(f"Groq API: {'✅' if config['GROQ_API_KEY'] else '❌'}")
st.sidebar.write(f"Bot token: {'✅' if config['BOT_TOKEN'] else '❌'}")
st.sidebar.write(f"Firebase: {'✅' if config['FIREBASE_CONF'] else '❌'}")

col1, col2, col3 = st.columns(3)
with col1:
    start_btn = st.button("▶️ Botni ishga tushirish", use_container_width=True)
with col2:
    restart_btn = st.button("🔄 Botni qayta ishga tushirish", use_container_width=True)
with col3:
    stop_btn = st.button("⏹️ Botni to‘xtatish", use_container_width=True)

st.divider()
st.subheader("📊 Holat")
st.write(f"Bot running: {rt.is_running}")
st.write(f"Active tasks: {len(rt.tasks)}")

st.subheader("📝 RAM loglar")
st.code("\n".join(rt.logs[-50:]), language="text")

# Firebase ma'lumotlari
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
    st.warning("Firebase ulanmadi.")

st.subheader("📒 Firestore — Logs")
if db:
    logs = list_logs(db, limit=200)
    if logs:
        st.table(logs)
    else:
        st.info("Hozircha loglar yo‘q.")
else:
    st.warning("Firebase ulanmadi.")

async def start():
    from main import start_bot  # ensure same Runtime instance
    rt.start_bot = start_bot
    await rt.start_bot()

async def stop():
    from main import stop_bot
    rt.stop_bot = stop_bot
    await rt.stop_bot()

if start_btn and config["BOT_TOKEN"]:
    asyncio.run(start())

if restart_btn:
    asyncio.run(stop())
    if config["BOT_TOKEN"]:
        asyncio.run(start())

if stop_btn:
    asyncio.run(stop())
