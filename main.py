import streamlit as st
import threading
import asyncio
import pandas as pd
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from bot_handlers import dp, bot  # Bot mantiqini import qilamiz (pastda tushuntirilgan)
from database import get_dashboard_data

# --- 1. WEB DASHBOARD QISMI ---
st.set_page_config(page_title="Suxandon AI Admin", page_icon="📊", layout="wide")

st.title("🤖 Suxandon AI — Boshqaruv Markazi")

# Ma'lumotlarni bazadan olish
data = get_dashboard_data()
stats = data["stats"]

# 1-QATOR: FOYDALANUVCHI STATISTIKASI
st.subheader("👥 Foydalanuvchilar Statistikasi")
col1, col2, col3 = st.columns(3)
col1.metric("Jami Foydalanuvchilar", data["total_users"], delta="Start bosganlar")
col2.metric("Bu oyda faol", data["monthly_active"], delta="Active Users")
col3.metric("Bugun faol", data["daily_active"], delta="Bugungi")

st.markdown("---")

# 2-QATOR: FAYL TAHLILLARI
st.subheader("📂 Fayl Tahlili Statistikasi")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Jami Fayllar", stats["total_processed"])
c2.metric("📹 Videolar", stats["video"])
c3.metric("🎙 Audiolar", stats["audio"])
c4.metric("📄 TXT vs Chat", f"{stats['format_txt']} / {stats['format_chat']}")

# GRAFIKLAR (Visualizatsiya)
st.markdown("---")
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.caption("Fayl turlari bo'yicha")
    chart_data = pd.DataFrame({
        "Tur": ["Video", "Audio"],
        "Soni": [stats["video"], stats["audio"]]
    })
    st.bar_chart(chart_data.set_index("Tur"))

with col_chart2:
    st.caption("Chiqarish formati bo'yicha")
    format_data = pd.DataFrame({
        "Format": ["TXT Fayl", "Chat Xabar"],
        "Soni": [stats['format_txt'], stats['format_chat']]
    })
    st.bar_chart(format_data.set_index("Format"))

# 3. BACKGROUND RUNNER (Botni ishga tushirish)
@st.cache_resource
def launch_bot():
    async def _runner():
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, handle_signals=False)

    def _thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_runner())

    t = threading.Thread(target=_thread, daemon=True)
    t.start()

launch_bot()

st.success("✅ Bot orqa fonda ishlamoqda!")
if st.button("🔄 Statistikani yangilash"):
    st.rerun()
  
