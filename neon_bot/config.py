# config.py
import streamlit as st

def load_config():
    return {
        "BOT_TOKEN": st.secrets.get("BOT_TOKEN", ""),
        "GROQ_API_KEY": st.secrets.get("GROQ_API_KEY", ""),
        "FIREBASE_CONF": st.secrets.get("firebase", None),
        "ADMIN_ID": int(st.secrets.get("ADMIN_ID", 1416457518)),
        "DEFAULT_MODE": st.secrets.get("DEFAULT_MODE", "groq"),  # "groq" | "local"
        "KEEPALIVE_INTERVAL": int(st.secrets.get("KEEPALIVE_INTERVAL", 25)),
        "TASK_TIMEOUT_SEC": int(st.secrets.get("TASK_TIMEOUT_SEC", 3600)),
        "WEB_APP_URL": st.secrets.get("WEB_APP_URL", "https://script1232.streamlit.app"),
    }
