import streamlit as st
import threading
import asyncio
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# BIZNING MODULLAR
from config import BOT_TOKEN
from bot_handlers import dp, bot
from database import get_dashboard_data

# --- 1. PAGE CONFIG & NEON CSS ---
st.set_page_config(page_title="Suxandon AI Admin", page_icon="⚡", layout="wide")

# NEON CSS STYLES
st.markdown("""
    <style>
    /* Asosiy Fon */
    .stApp {
        background-color: #0e1117;
        color: #00ffcc;
    }
    
    /* Neon Metrika Kartochkalari */
    div[data-testid="stMetric"] {
        background-color: #1c1f26;
        border: 2px solid #00ffcc;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 0 10px #00ffcc, 0 0 20px #00ffcc inset;
        text-align: center;
    }
    
    /* Metrika yozuvlari */
    div[data-testid="stMetricLabel"] {
        color: #ff00ff !important;
        font-weight: bold;
        text-shadow: 0 0 5px #ff00ff;
    }
    div[data-testid="stMetricValue"] {
        color: #ffffff !important;
        text-shadow: 0 0 10px #ffffff;
    }

    /* Sarlavha */
    h1 {
        color: #cc00ff;
        text-shadow: 0 0 10px #cc00ff, 0 0 20px #cc00ff;
        text-align: center;
        font-family: 'Courier New', Courier, monospace;
    }
    h3 {
        color: #00ccff;
        text-shadow: 0 0 5px #00ccff;
        border-bottom: 2px solid #00ccff;
        padding-bottom: 10px;
    }
    
    /* Tugmalar */
    .stButton>button {
        background-color: #000000;
        color: #00ff00;
        border: 2px solid #00ff00;
        box-shadow: 0 0 5px #00ff00;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #00ff00;
        color: #000000;
        box-shadow: 0 0 15px #00ff00;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ SUXANDON AI - NEON DASHBOARD ⚡")

# --- 2. MA'LUMOTLARNI YUKLASH ---
try:
    data = get_dashboard_data()
    stats = data["stats"]
    users = data.get("user_list", {})  # Userlar ro'yxati (database.py dan keladi)

    # --- 3. YONMA-YON METRIKALAR (ROW LAYOUT) ---
    st.markdown("### 👥 FOYDALANUVCHILAR")
    
    # 4 ta ustun yaratamiz (Yonma-yon turishi uchun)
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.metric("Jami Userlar", data["total_users"], delta="Start")
    with c2:
        st.metric("Faol (Oy)", data["monthly_active"], delta="Active")
    with c3:
        st.metric("Faol (Bugun)", data["daily_active"], delta="Today")
    with c4:
        st.metric("Jami Audio", stats["audio"], delta="Processed")

    st.markdown("<br>", unsafe_allow_html=True) # Joy tashlash

    # --- 4. GRAFIK (LINE CHART - RASMDAGIDEK) ---
    st.markdown("### 📈 O'SISH DINAMIKASI (GDP Style)")

    # Grafik uchun soxta ma'lumot generatsiyasi (Sizda real ma'lumot to'planganda buni o'zgartirasiz)
    # Hozircha vizual ko'rinish uchun:
    chart_df = pd.DataFrame({
        "Sana": [datetime.now() - timedelta(days=i) for i in range(10, -1, -1)],
        "Foydalanuvchilar": [data["total_users"] - (10-i)*2 for i in range(11)], # Taxminiy o'sish
        "Audiolar": [stats["audio"] - (10-i)*5 for i in range(11)]
    })

    # Plotly Neon Grafik
    fig = go.Figure()

    # User chizig'i (Ko'k Neon)
    fig.add_trace(go.Scatter(
        x=chart_df["Sana"], y=chart_df["Foydalanuvchilar"],
        mode='lines+markers',
        name='Userlar',
        line=dict(color='#00ccff', width=4),
        marker=dict(size=8, color='#ffffff', line=dict(width=2, color='#00ccff'))
    ))

    # Audio chizig'i (Qizil Neon)
    fig.add_trace(go.Scatter(
        x=chart_df["Sana"], y=chart_df["Audiolar"],
        mode='lines+markers',
        name='Audiolar',
        line=dict(color='#ff0055', width=4),
        marker=dict(size=8, color='#ffffff', line=dict(width=2, color='#ff0055'))
    ))

    # Grafik dizayni (Qora fon, panjarasiz)
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#00ffcc'),
        xaxis=dict(showgrid=False, linecolor='#00ffcc'),
        yaxis=dict(showgrid=True, gridcolor='#333333', linecolor='#00ffcc'),
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor='center'),
        margin=dict(l=20, r=20, t=40, b=20),
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.warning(f"Baza hali bo'sh yoki xatolik: {e}")

# --- 5. BOT RUNNER ---
@st.cache_resource
def launch_bot():
    async def _runner():
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            await dp.start_polling(bot, handle_signals=False)
        except Exception as e:
            print(f"Bot Error: {e}")

    def _thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_runner())

    t = threading.Thread(target=_thread, daemon=True)
    t.start()

launch_bot()

if st.button("🔄 YANGILASH"):
    st.rerun()
    
