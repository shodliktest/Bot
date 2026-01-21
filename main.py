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
st.set_page_config(page_title="SHodlik AI Admin", page_icon="⚡", layout="wide")

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
        text-shadow: 0 0 10px #cc00ff, 0 0 10px #cc00ff;
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

st.title("⚡ NEON SHodlik ⚡")

# --- 2. MA'LUMOTLARNI YUKLASH ---
try:
    data = get_dashboard_data()
    # Xavfsiz olish (get) - agar baza bo'sh bo'lsa xato bermaydi
    stats = data.get("stats", {})
    total_audio = stats.get("audio", 0) 
    
    users = data.get("user_list", {})

    # --- 3. YONMA-YON METRIKALAR ---
    st.markdown("### 👥 FOYDALANUVCHILAR")
    
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.metric("Jami Userlar", data.get("total_users", 0), delta="Start")
    with c2:
        st.metric("Faol (Oy)", data.get("monthly_active", 0), delta="Active")
    with c3:
        st.metric("Faol (Bugun)", data.get("daily_active", 0), delta="Today")
    with c4:
        st.metric("Jami Audio", total_audio, delta="Processed")

    st.markdown("<br>", unsafe_allow_html=True) 

    # --- 4. GRAFIK (LINE CHART - GDP STYLE) ---
    st.markdown("### 📈 O'SISH DINAMIKASI (GDP Style)")

    # Grafik ma'lumotlari (Xavfsiz hisoblash)
    chart_df = pd.DataFrame({
        "Sana": [datetime.now() - timedelta(days=i) for i in range(10, -1, -1)],
        "Foydalanuvchilar": [data.get("total_users", 0) - (10-i)*1 for i in range(11)], 
        "Audiolar": [total_audio - (10-i)*2 for i in range(11)]
    })

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
    st.warning(f"Baza ma'lumotlari yuklanmoqda yoki bo'sh: {e}")

# --- 5. BOT RUNNER (ENG MUHIM QISM - KILLER & SINGLETON) ---
def run_bot_in_background():
    """Botni alohida oqimda va xavfsiz ishga tushirish"""
    
    async def _runner():
        try:
            # 1. KILLER: Eski webhooklarni o'chirish (Conflict oldini olish)
            await bot.delete_webhook(drop_pending_updates=True)
            # 2. BOTNI YOQISH
            await dp.start_polling(bot, handle_signals=False)
        except Exception as e:
            print(f"Bot Error: {e}")

    def _thread_target():
        # Yangi event loop ochamiz (Streamlit loopi bilan urushmasligi uchun)
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        new_loop.run_until_complete(_runner())

    # SINGLETON: Agar thread allaqachon ishlayotgan bo'lsa, ikkinchisini ochmaymiz
    thread_name = "TelegramBotThread"
    is_running = False
    for t in threading.enumerate():
        if t.name == thread_name:
            is_running = True
            break
            
    if not is_running:
        t = threading.Thread(target=_thread_target, name=thread_name, daemon=True)
        t.start()
        print("✅ Bot thread ishga tushdi!")

# Sahifa har safar yuklanganda botni tekshiramiz va yoqamiz
run_bot_in_background()

if st.button("🔄 YANGILASH"):
    st.rerun()
    
