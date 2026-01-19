# admin_app.py
import streamlit as st
import asyncio
import threading
from config import load_config
from main import rt, start_bot, stop_bot  # main.py dagi tayyor instance larni olamiz

st.set_page_config(page_title="Neon Hybrid Admin", layout="centered")
st.title("🤖 Neon Hybrid Bot — Admin panel")

config = load_config()

# UI qismi
st.subheader("⚙️ Sozlamalar")
col1, col2 = st.columns(2)
with col1:
    st.write(f"**Admin ID:** `{config['ADMIN_ID']}`")
    st.write(f"**Default mode:** `{config['DEFAULT_MODE']}`")
with col2:
    st.write(f"**Groq API:** {'✅' if config['GROQ_API_KEY'] else '❌'}")
    st.write(f"**Bot token:** {'✅' if config['BOT_TOKEN'] else '❌'}")

st.divider()

# Botni alohida oqimda (Thread) yurgizish funksiyasi
def run_bot_in_thread():
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    new_loop.run_until_complete(start_bot())

st.subheader("📊 Holat")
status_color = "green" if rt.is_running else "red"
st.markdown(f"Bot holati: :{status_color}[{'ISHLAMOQDA' if rt.is_running else 'TO‘XTATILGAN'}]")
st.write(f"Faol topshiriqlar: {len(rt.tasks)}")

col_btn1, col_btn2 = st.columns(2)

with col_btn1:
    if st.button("▶️ Botni ishga tushirish", use_container_width=True):
        if not rt.is_running:
            # Yangi thread ochish
            thread = threading.Thread(target=run_bot_in_thread, daemon=True, name="BotThread")
            thread.start()
            st.success("Bot fon rejimida ishga tushirildi!")
            st.rerun()
        else:
            st.warning("Bot allaqachon ishlamoqda.")

with col_btn2:
    if st.button("⏹️ Botni to‘xtatish", use_container_width=True):
        if rt.is_running:
            asyncio.run(stop_bot())
            st.error("Bot to'xtatildi.")
            st.rerun()
        else:
            st.info("Bot allaqachon to'xtatilgan.")

st.divider()
st.subheader("📝 So'nggi loglar")
if rt.logs:
    st.code("\n".join(rt.logs[-15:]), language="text")
else:
    st.write("Loglar mavjud emas.")
