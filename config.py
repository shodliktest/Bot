import streamlit as st
import pytz

# Token va ID ni shu yerdan olamiz
try:
    BOT_TOKEN = st.secrets["BOT_TOKEN"]
except:
    BOT_TOKEN = "TOKEN_YOQ"

ADMIN_ID = 1416457518
UZ_TZ = pytz.timezone('Asia/Tashkent')
