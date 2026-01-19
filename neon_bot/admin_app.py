# admin_app.py
import streamlit as st
import threading
import asyncio
from main import rt, start_bot, stop_bot # main.py dan obyektlarni olamiz

st.title("🤖 Neon Bot Boshqaruv Paneli")

# Botni alohida oqimda ishga tushirish funksiyasi
def bot_worker():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_bot())

if st.button("Botni ishga tushirish"):
    if not rt.is_running:
        t = threading.Thread(target=bot_worker, daemon=True)
        t.start()
        st.success("Bot yoqildi!")
    else:
        st.warning("Bot allaqachon ishlamoqda")

st.write(f"Hozirgi holat: {'Ishlamoqda' if rt.is_running else 'Toxtatilgan'}")
