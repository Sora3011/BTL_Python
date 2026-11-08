import streamlit as st
from backend.database.db import init_db
from backend.models.sentiment_model import load_ai_model
from frontend.components.style_loader import load_custom_css
from frontend.components.navbar import render_top_header
from frontend.views.overview_view import render_overview_view
from frontend.views.youtube_view import render_youtube_view
from frontend.views.facebook_view import render_facebook_view

# ==============================================================================
# THIẾT LẬP HỆ THỐNG & ROUTER TRUNG TÂM
# ==============================================================================
st.set_page_config(
    page_title="ViSoBERT Studio • Phân Tích Cảm Xúc Mạng Xã Hội",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Nạp phông chữ và CSS Design System từ file tĩnh
load_custom_css("frontend/assets/style.css")

# Khởi tạo CSDL SQLite (bảo toàn schema posts ↔ comments)
init_db()

# Tải tài nguyên mô hình AI ViSoBERT v2
tokenizer, model, device, inf_cfg = load_ai_model()

# Hiển thị Thanh Thương Hiệu & Telemetry Hệ Thống
render_top_header()

# Bộ chuyển phân hệ Zero-Latency Tabs (Chuyển tab tức thì 0ms, không lag, giữ nguyên dữ liệu)
tab_overview, tab_youtube, tab_facebook = st.tabs([
    ":material/insights: Tổng Quan & Phân Tích",
    ":material/smart_display: Khai Thác YouTube",
    ":material/forum: Dữ Liệu Facebook"
])

with tab_overview:
    render_overview_view()

with tab_youtube:
    render_youtube_view(tokenizer, model, device, inf_cfg)

with tab_facebook:
    render_facebook_view(tokenizer, model, device, inf_cfg)
