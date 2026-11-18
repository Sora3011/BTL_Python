import streamlit as st
from backend.database.db import init_db
from backend.models.sentiment_model import load_ai_model
from frontend.components.style_loader import load_custom_css
from frontend.components.navbar import render_top_header
from frontend.views.overview_view import render_overview_view
from frontend.views.youtube_view import render_youtube_view
from frontend.views.facebook_view import render_facebook_view

st.set_page_config(
    page_title="Sounds of Social • Phân Tích Cảm Xúc Mạng Xã Hội",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

load_custom_css("frontend/assets/style.css")

init_db()

tokenizer, model, device, inf_cfg = load_ai_model()

render_top_header()

tab_overview, tab_youtube, tab_facebook = st.tabs([
    ":material/insights: Tổng Quan và Phân Tích",
    ":material/smart_display: Khai Thác YouTube",
    ":material/forum: Dữ Liệu Facebook"
])

with tab_overview:
    render_overview_view(inf_cfg)

with tab_youtube:
    render_youtube_view(tokenizer, model, device, inf_cfg)

with tab_facebook:
    render_facebook_view(tokenizer, model, device, inf_cfg)
