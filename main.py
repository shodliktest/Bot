import streamlit as st
import threading
import asyncio
import pandas as pd
from aiogram import Bot, Dispatcher

# BIZNING MODULLAR
from config import BOT_TOKEN
from bot_handlers import dp, bot  # <--- Bot va DP ni import qilamiz
from database import get_dashboard_data

# --- WEB DASHBOARD ---
st.set_page_config(page_title="Suxandon AI Admin", page_icon="📊", layout="wide")

st.title("🤖 Suxandon AI — Boshqaruv Markazi")

# Statistikani yuklash
try:
    data = get_dashboard_data()
    stats = data["stats"]

    # 1. FOYDALANUVCHILAR
    st.subheader("👥 Foydalanuvchilar")
    c1, c2, c3 = st.columns(3)
    c1.metric("Jami Userlar", data["total_users"])
    c2.metric("Oy davomida faol", data["monthly_active"])
    c3.metric("Bugun faol", data["daily_active"])

    st.markdown("---")

    # 2. FAYLLAR
    st.subheader("📂 Fayl Statistikasi")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Jami Ishlangan", stats["total_processed"])
    c2.metric("📹 Video", stats["video"])
    c3.metric("🎙 Audio", stats["audio"])
    c4.metric("📄 TXT / Chat", f"{stats['format_txt']} / {stats['format_chat']}")

    # 3. GRAFIKLAR
    st.markdown("---")
    g1, g2 = st.columns(2)
    with g1:
        st.bar_chart(pd.DataFrame({"Soni": [stats["video"], stats["audio"]]}, index=["Video", "Audio"]))
    with g2:
        st.bar_chart(pd.DataFrame({"Soni": [stats['format_txt'], stats['format_chat']]}, index=["TXT", "Chat"]))

except Exception as e:
    st.warning("Statistika bazasi hali yaratilmagan (Botga start bosing).")

# --- BOTNI ORQA FONDA ISHLATISH (Daemon Thread) ---
@st.cache_resource
def launch_bot():
    async def _runner():
        try:
            # Konfliktni o'ldirish
            await bot.delete_webhook(drop_pending_updates=True)
            # Botni yoqish
            await dp.start_polling(bot, handle_signals=False)
        except Exception as e:
            print(f"Bot Error: {e}")

    def _thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_runner())

    # Alohida oqimda ishga tushiramiz
    t = threading.Thread(target=_thread, daemon=True)
    t.start()

# Funksiyani chaqiramiz
launch_bot()

st.success("✅ Bot Server Barqaror Ishlamoqda!")
if st.button("🔄 Yangilash"):
    st.rerun()
    
