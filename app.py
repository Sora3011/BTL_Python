import os
import json
import html
import re
from itertools import islice
import sqlite3
import pandas as pd
import numpy as np
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from youtube_comment_downloader import YoutubeCommentDownloader, SORT_BY_POPULAR
import plotly.express as px
import plotly.graph_objects as go
import emoji
import streamlit as st

# ==============================================================================
# 0. THIẾT LẬP HỆ THỐNG & DESIGN SYSTEM: "ATELIER DATA OBSERVATORY"
# Phong cách: Phòng Nghiên Cứu & Báo Chí Dữ Liệu Khoa Học (Academic Data Studio)
# Tuân thủ: /design-taste-frontend (Chống AI slop, màu trung tính sang trọng, trật tự thị giác rõ rệt)
# ==============================================================================

st.set_page_config(
    page_title="Hệ Thống Phân Tích Cảm Xúc Mạng Xã Hội • ViSoBERT v2 & SQLite",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

def render_html(raw_html: str):
    """
    Hàm kết xuất HTML an toàn cho Streamlit:
    Loại bỏ triệt để khoảng trắng thụt lề và ký tự xuống dòng thừa
    để bộ dịch Markdown không bao giờ hiểu nhầm HTML thành khối mã thụt lề (indented code block).
    """
    clean = re.sub(r'>\s+<', '><', raw_html)
    clean = re.sub(r'\n\s*', ' ', clean).strip()
    st.markdown(clean, unsafe_allow_html=True)

# Nhúng phông chữ tiếng Việt chuẩn học thuật và CSS Atelier Data Studio
render_html("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    /* 1. Thiết lập Typography toàn diện */
    html, body, input, textarea, select, button, div, p, span, label {
        font-family: 'Be Vietnam Pro', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    code, pre, .mono-data {
        font-family: 'JetBrains Mono', SFMono-Regular, Menlo, Monaco, Consolas, monospace !important;
    }

    /* Bảo vệ nghiêm ngặt biểu tượng Material Symbols gốc của Streamlit */
    [data-testid="stIconMaterial"], 
    span[data-testid="stIconMaterial"],
    .material-symbols-rounded,
    .material-symbols-outlined {
        font-family: 'Material Symbols Rounded', 'Material Symbols Outlined' !important;
        font-weight: normal !important;
        font-style: normal !important;
        line-height: 1 !important;
        display: inline-block !important;
        text-transform: none !important;
        letter-spacing: normal !important;
        word-wrap: normal !important;
        white-space: nowrap !important;
        direction: ltr !important;
        -webkit-font-smoothing: antialiased !important;
        text-rendering: optimizeLegibility !important;
        font-feature-settings: 'liga' 1 !important;
    }

    /* 2. Bảng màu Nền & Bề mặt (Canvas: Deep Obsidian Graphite #0b0f17) */
    .stApp {
        background-color: #0b0f17 !important;
        color: #e2e8f0 !important;
    }

    /* Ẩn chỉ các thành phần quản trị phụ của Streamlit, giữ nguyên khung điều khiển */
    #MainMenu, [data-testid="stMainMenu"] { display: none !important; }
    footer { display: none !important; }
    [data-testid="stAppDeployButton"] { display: none !important; }
    div[data-testid="stDecoration"] { display: none !important; }
    header[data-testid="stHeader"] {
        background-color: transparent !important;
    }

    /* 3. Tối ưu nút Mở / Đóng Sidebar (Streamlit 1.66+) */
    button[data-testid="stExpandSidebarButton"],
    [data-testid="stExpandSidebarButton"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"] {
        display: inline-flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        z-index: 999999 !important;
        background: #141b29 !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4) !important;
        width: 36px !important;
        height: 36px !important;
        align-items: center !important;
        justify-content: center !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
    }
    button[data-testid="stExpandSidebarButton"]:hover,
    [data-testid="stSidebarCollapsedControl"]:hover {
        background: #2563eb !important;
        border-color: #3b82f6 !important;
    }

    [data-testid="stSidebarCollapseButton"] button {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        color: #cbd5e1 !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stSidebarCollapseButton"] button:hover {
        background: rgba(255, 255, 255, 0.12) !important;
        color: #ffffff !important;
    }

    /* 4. Giới hạn chiều rộng và đệm khối nội dung trung tâm */
    .block-container {
        padding-top: 1.25rem !important;
        padding-bottom: 3.5rem !important;
        max-width: 1360px !important;
    }

    /* 5. Banner Tiêu đề Học thuật & Phòng Nghiên cứu */
    .lab-header {
        background: #111724;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 16px;
    }
    .lab-title-area h1 {
        margin: 0;
        font-size: 21px;
        font-weight: 700;
        color: #f8fafc;
        letter-spacing: -0.02em;
        line-height: 1.3;
    }
    .lab-title-area p {
        margin: 4px 0 0 0;
        font-size: 13.5px;
        color: #94a3b8;
    }
    .spec-pills {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
    }
    .spec-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 11.5px;
        font-family: 'JetBrains Mono', monospace;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.09);
        color: #cbd5e1;
    }
    .spec-dot-green {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background-color: #10b981;
    }

    /* 6. Sidebar Phòng Thí Nghiệm */
    section[data-testid="stSidebar"] {
        background-color: #0e131d !important;
        border-right: 1px solid rgba(255, 255, 255, 0.07) !important;
    }
    .sidebar-brand-box {
        padding-bottom: 14px;
        margin-bottom: 16px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }
    .brand-tag {
        font-size: 10.5px;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #3b82f6;
        margin-bottom: 4px;
    }
    .brand-title {
        font-size: 17px;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: -0.01em;
        margin: 0;
    }
    .brand-subtitle {
        font-size: 12px;
        color: #94a3b8;
        margin-top: 3px;
    }

    /* Tùy biến Menu điều hướng Radio thành Navigation List thanh lịch */
    div[data-testid="stRadioGroup"] {
        gap: 6px !important;
        display: flex !important;
        flex-direction: column !important;
    }
    div[data-testid="stRadioGroup"] input[type="radio"],
    div[data-testid="stRadioGroup"] label[data-testid="stRadioOption"] > div > div:first-child {
        display: none !important;
    }
    div[data-testid="stRadioGroup"] label[data-testid="stRadioOption"] {
        width: 100% !important;
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 8px !important;
        padding: 9px 12px !important;
        cursor: pointer !important;
        transition: all 0.15s ease !important;
    }
    div[data-testid="stRadioGroup"] label[data-testid="stRadioOption"]:hover {
        background: rgba(255, 255, 255, 0.06) !important;
        border-color: rgba(255, 255, 255, 0.15) !important;
    }
    div[data-testid="stRadioGroup"] div[data-selected="true"] label[data-testid="stRadioOption"],
    div[data-testid="stRadioGroup"] label[data-testid="stRadioOption"][data-selected="true"] {
        background: rgba(37, 99, 235, 0.18) !important;
        border: 1px solid #3b82f6 !important;
    }
    div[data-testid="stRadioGroup"] label[data-testid="stRadioOption"] p {
        color: #94a3b8 !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        margin: 0 !important;
    }
    div[data-testid="stRadioGroup"] div[data-selected="true"] label[data-testid="stRadioOption"] p,
    div[data-testid="stRadioGroup"] label[data-testid="stRadioOption"][data-selected="true"] p {
        color: #ffffff !important;
        font-weight: 600 !important;
    }

    /* Khối Thông số CSDL và Ghi chú Phương pháp Luận ở Sidebar */
    .sidebar-panel {
        background: #111724;
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 8px;
        padding: 14px;
        margin-top: 14px;
    }
    .panel-header {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #94a3b8;
        margin-bottom: 10px;
    }
    .meta-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 12px;
        padding: 4px 0;
        border-bottom: 1px dashed rgba(255, 255, 255, 0.05);
    }
    .meta-row:last-child {
        border-bottom: none;
    }
    .meta-label { color: #94a3b8; }
    .meta-value { color: #f1f5f9; font-weight: 600; font-family: 'JetBrains Mono', monospace; font-size: 11.5px; }

    /* 7. Asymmetric Sentiment Cockpit (Bố cục Bất đối xứng trung tâm) */
    .cockpit-grid {
        display: grid;
        grid-template-columns: 5fr 7fr;
        gap: 16px;
        margin-bottom: 20px;
    }
    @media (max-width: 992px) {
        .cockpit-grid { grid-template-columns: 1fr; }
    }

    /* Thẻ Điểm Cảm Xúc Tổng Hợp (Hero Gauge Card) */
    .hero-gauge-card {
        background: #121824;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px 22px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .card-eyebrow {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #94a3b8;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .gauge-main {
        margin: 16px 0;
    }
    .gauge-score-row {
        display: flex;
        align-items: baseline;
        gap: 8px;
    }
    .gauge-score-value {
        font-size: 42px;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        line-height: 1;
        letter-spacing: -0.03em;
    }
    .gauge-score-max {
        font-size: 16px;
        color: #64748b;
        font-family: 'JetBrains Mono', monospace;
    }
    .gauge-verdict-title {
        font-size: 15px;
        font-weight: 600;
        margin-top: 6px;
        letter-spacing: -0.01em;
    }
    .gauge-verdict-desc {
        font-size: 12.5px;
        color: #94a3b8;
        margin-top: 3px;
        line-height: 1.45;
    }

    /* Thước đo Phổ Cảm Xúc Liên Tục */
    .spectrum-track {
        width: 100%;
        height: 7px;
        border-radius: 4px;
        background: linear-gradient(to right, #f43f5e 0%, #cbd5e1 50%, #10b981 100%);
        position: relative;
        margin: 14px 0 6px 0;
    }
    .spectrum-marker {
        position: absolute;
        top: -4px;
        width: 15px;
        height: 15px;
        border-radius: 50%;
        background: #ffffff;
        border: 2px solid #0b0f17;
        box-shadow: 0 0 6px rgba(255, 255, 255, 0.6);
        transform: translateX(-50%);
    }
    .spectrum-labels {
        display: flex;
        justify-content: space-between;
        font-size: 10.5px;
        color: #64748b;
        font-family: 'JetBrains Mono', monospace;
    }

    /* 4 Phân Lớp Cảm Xúc (Semantic Horizon List) */
    .horizon-panel {
        background: #121824;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px 22px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .horizon-list {
        display: flex;
        flex-direction: column;
        gap: 9px;
        margin-top: 12px;
    }
    .horizon-item {
        background: #0f1520;
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 10px 14px;
        transition: border-color 0.15s ease;
    }
    .horizon-item:hover {
        border-color: rgba(255, 255, 255, 0.14);
    }
    .horizon-item-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 6px;
    }
    .horizon-tag-group {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .horizon-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
    }
    .horizon-name {
        font-size: 13px;
        font-weight: 600;
        color: #f1f5f9;
    }
    .horizon-numbers {
        display: flex;
        align-items: baseline;
        gap: 8px;
    }
    .horizon-count {
        font-size: 12px;
        color: #94a3b8;
    }
    .horizon-pct {
        font-size: 13.5px;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
    }
    .horizon-bar-bg {
        width: 100%;
        height: 5px;
        background: rgba(255, 255, 255, 0.06);
        border-radius: 3px;
        overflow: hidden;
    }
    .horizon-bar-fill {
        height: 100%;
        border-radius: 3px;
    }

    /* 8. Thẻ Trích Dẫn Ý Kiến Tiêu Biểu (Editorial Voice Cards) */
    .spotlight-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 14px;
        margin: 14px 0 22px 0;
    }
    @media (max-width: 900px) {
        .spotlight-grid { grid-template-columns: 1fr; }
    }
    .voice-card {
        background: #121824;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 16px 18px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 160px;
        position: relative;
    }
    .voice-card-pos { border-left: 3px solid #10b981; }
    .voice-card-neg { border-left: 3px solid #f43f5e; }
    .voice-card-mix { border-left: 3px solid #8b5cf6; }

    .voice-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    .voice-role-tag {
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }
    .voice-badge-pill {
        font-size: 11px;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        padding: 2px 7px;
        border-radius: 4px;
    }
    .voice-quote {
        font-size: 13px;
        color: #e2e8f0;
        line-height: 1.55;
        font-style: normal;
        margin-bottom: 12px;
        flex-grow: 1;
        word-break: break-word;
    }
    .voice-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 11.5px;
        color: #94a3b8;
        border-top: 1px solid rgba(255, 255, 255, 0.06);
        padding-top: 8px;
        margin-top: auto;
    }

    /* 9. Tinh Chỉnh Form, Input, Select, Container của Streamlit */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: #111724 !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
    }
    .stTextInput input, .stTextArea textarea, div[data-baseweb="select"] {
        border-radius: 8px !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        background-color: #0c1018 !important;
        color: #f8fafc !important;
        font-size: 13.5px !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 1px #3b82f6 !important;
    }

    /* Nút bấm Kỹ thuật (Technical Action Buttons) */
    div.stButton > button {
        background: #2563eb !important;
        color: #ffffff !important;
        border: 1px solid #3b82f6 !important;
        border-radius: 8px !important;
        padding: 9px 18px !important;
        font-weight: 600 !important;
        font-size: 13.5px !important;
        transition: all 0.15s ease !important;
    }
    div.stButton > button:hover {
        background: #1d4ed8 !important;
        border-color: #60a5fa !important;
    }
</style>
""")

# ==============================================================================
# 1. KHỞI TẠO CƠ SỞ DỮ LIỆU SQLITE
# Schema bảo toàn: posts (1) ↔ comments (N)
# ==============================================================================
DB_NAME = "sentiment_analytics.db"
MODEL_PATH = "./Model_viso_bert_v2"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            post_id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            post_url TEXT NOT NULL,
            analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            author TEXT,
            raw_text TEXT NOT NULL,
            pos_score REAL,
            neu_score REAL,
            neg_score REAL,
            score_100 REAL,
            entropy REAL,
            sentiment_label TEXT,
            FOREIGN KEY (post_id) REFERENCES posts (post_id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ==============================================================================
# 2. TẢI MODEL VISOBERT V2 & BỘ TIỀN XỬ LÝ NGÔN NGỮ TIẾNG VIỆT
# ==============================================================================
@st.cache_resource
def load_ai_model():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH).to(device)
    model.eval()
    
    cfg_file = os.path.join(MODEL_PATH, "inference_config.json")
    if os.path.exists(cfg_file):
        with open(cfg_file, encoding="utf-8") as f:
            inf_cfg = json.load(f)
    else:
        inf_cfg = {"temperature": 1.3, "emoji_mode": "keep", "max_len": 128}
        
    return tokenizer, model, device, inf_cfg

URL_RE     = re.compile(r"(?:https?://|www\.)\S+")
MENTION_RE = re.compile(r"@[\w.]+")
REPEAT_RE  = re.compile(r"(?!\d)(.)\1{2,}")

EMOTICONS = [
    (re.compile(r"[:=]-?\){3,}"), " rất vui "),
    (re.compile(r"[:=]-?\)\)"),   " vui vẻ "),
    (re.compile(r"[:=]-?\)"),     " vui "),
    (re.compile(r"[:=]-?\({2,}"), " rất buồn "),
    (re.compile(r"[:=]-?\("),     " buồn "),
    (re.compile(r"<3"),           " yêu thích "),
    (re.compile(r"(?<!\w):3(?!\w)"), " dễ thương "),
    (re.compile(r"(?<!\w):v(?!\w)"), " vui vẻ "),
    (re.compile(r"-_-"),          " chán nản "),
]

def clean_text(text: str, emoji_mode="keep") -> str:
    t = str(text)
    t = URL_RE.sub(" ", t)
    t = MENTION_RE.sub(" ", t)
    for rx, rep in EMOTICONS:
        t = rx.sub(rep, t)
    if emoji_mode == "en":
        t = emoji.demojize(t, delimiters=(" ", " ")).replace("_", " ")
    t = REPEAT_RE.sub(r"\1\1", t)
    return re.sub(r"\s+", " ", t).strip()

def predict_batch_comments(comments_list, tokenizer, model, device, inf_cfg):
    """
    Suy luận dự đoán nhãn cảm xúc với Temperature Scaling (T=1.3)
    Phân loại 4 nhãn: Tích cực, Trung tính, Hỗn hợp, Tiêu cực
    Tính toán: Score 0-100 và Shannon Entropy đo mức độ hỗn loạn thông tin
    """
    T = float(inf_cfg.get("temperature", 1.3))
    emoji_mode = inf_cfg.get("emoji_mode", "keep")
    max_len = int(inf_cfg.get("max_len", 128))
    
    results = []
    for item in comments_list:
        raw_text = item["text"]
        author = item.get("author", "Ẩn danh")
        processed = clean_text(raw_text, emoji_mode=emoji_mode) or "..."
        
        inputs = tokenizer(processed, return_tensors="pt", truncation=True, padding=True, max_length=max_len).to(device)
        with torch.no_grad():
            logits = model(**inputs).logits
            probs = F.softmax(logits.float() / T, dim=-1).squeeze().cpu().numpy()
            
        neg_prob, neu_prob, pos_prob = float(probs[0]), float(probs[1]), float(probs[2])
        score_100 = round(50.0 + 50.0 * (pos_prob - neg_prob), 1)
        entropy = round(float(-(probs * np.log(probs + 1e-9)).sum()), 3)
        
        if min(neg_prob, pos_prob) >= 0.25:
            label = "Hỗn hợp"
        elif neu_prob >= 0.50:
            label = "Trung tính"
        elif score_100 >= 60:
            label = "Tích cực"
        elif score_100 > 40:
            label = "Trung tính"
        else:
            label = "Tiêu cực"
            
        results.append((
            author, raw_text,
            round(pos_prob * 100, 2),
            round(neu_prob * 100, 2),
            round(neg_prob * 100, 2),
            score_100,
            entropy,
            label
        ))
    return results

# Tải tài nguyên AI
tokenizer, model, device, inf_cfg = load_ai_model()

# Bản đồ màu Muted Semantic chuẩn khoa học
COLOR_PALETTE = {
    "Tích cực": "#10b981",  # Emerald Green
    "Trung tính": "#64748b", # Slate Slate
    "Hỗn hợp": "#8b5cf6",   # Iris Muted
    "Tiêu cực": "#f43f5e"   # Crimson Terracotta
}

# ==============================================================================
# 3. SIDEBAR NAVIGATION & SYSTEM HEALTH PANEL
# ==============================================================================
with st.sidebar:
    render_html("""
    <div class="sidebar-brand-box">
        <div class="brand-tag">BÀI TẬP LỚN PYTHON</div>
        <h2 class="brand-title">Sentiment Analytics</h2>
        <div class="brand-subtitle">ViSoBERT v2 & SQLite Relational DB</div>
    </div>
    """)

    nav_choice = st.radio(
        "Phân hệ làm việc:",
        options=[
            "📊 Tổng Quan & Phân Tích Dữ Liệu",
            "🎥 Thu Thập & Phân Tích YouTube",
            "📘 Phân Tích Bình Luận Facebook"
        ],
        index=0,
        label_visibility="collapsed"
    )

    # Đọc nhanh trạng thái từ CSDL
    conn_sb = sqlite3.connect(DB_NAME)
    cur_sb = conn_sb.cursor()
    cur_sb.execute("SELECT COUNT(*) FROM posts")
    sb_total_posts = cur_sb.fetchone()[0]
    cur_sb.execute("SELECT COUNT(*) FROM comments")
    sb_total_comments = cur_sb.fetchone()[0]
    conn_sb.close()

    render_html(f"""
    <div class="sidebar-panel">
        <div class="panel-header">Thông Số Môi Trường</div>
        <div class="meta-row">
            <span class="meta-label">Mô hình:</span>
            <span class="meta-value">ViSoBERT v2</span>
        </div>
        <div class="meta-row">
            <span class="meta-label">Kiến trúc:</span>
            <span class="meta-value">XLM-RoBERTa</span>
        </div>
        <div class="meta-row">
            <span class="meta-label">Thiết bị suy luận:</span>
            <span class="meta-value">{"CUDA GPU" if torch.cuda.is_available() else "CPU"}</span>
        </div>
        <div class="meta-row">
            <span class="meta-label">Hiệu chuẩn:</span>
            <span class="meta-value">T = 1.3 Softmax</span>
        </div>
        <div class="meta-row">
            <span class="meta-label">CSDL quan hệ:</span>
            <span class="meta-value">SQLite 3.x</span>
        </div>
        <div class="meta-row">
            <span class="meta-label">Tổng bài lưu trữ:</span>
            <span class="meta-value">{sb_total_posts} bài</span>
        </div>
        <div class="meta-row">
            <span class="meta-label">Tổng bình luận:</span>
            <span class="meta-value">{sb_total_comments} bản ghi</span>
        </div>
    </div>
    <div class="sidebar-panel" style="margin-top: 10px;">
        <div class="panel-header">Ghi Chú Phân Loại</div>
        <div style="font-size: 11.5px; color: #94a3b8; line-height: 1.5;">
            • <strong>Điểm 0-100:</strong> Tính từ hiệu số xác suất <code>P(pos) - P(neg)</code>.<br>
            • <strong>Hỗn hợp:</strong> Cả xác suất tích cực và tiêu cực cùng đạt ≥ 25%.<br>
            • <strong>Entropy:</strong> Đo độ bất định của phân phối cảm xúc.
        </div>
    </div>
    """)

# ==============================================================================
# 4. VIEW 1: BẢNG ĐIỀU KHIỂN & PHÂN TÍCH DỮ LIỆU SQL
# ==============================================================================
if nav_choice == "📊 Tổng Quan & Phân Tích Dữ Liệu":
    # Banner Header Học Thuật
    render_html("""
    <div class="lab-header">
        <div class="lab-title-area">
            <h1>Hệ Thống Phân Tích Cảm Xúc Ngôn Ngữ Mạng Xã Hội</h1>
        </div>
        <div class="spec-pills">
        </div>
    </div>
    """)

    conn = sqlite3.connect(DB_NAME)
    sql_summary = """
        SELECT 
            p.post_id,
            p.platform AS "Nền tảng",
            p.post_url AS "Nguồn dữ liệu",
            p.analyzed_at AS "Thời điểm phân tích",
            COUNT(c.comment_id) AS "Tổng số ý kiến",
            ROUND(AVG(c.score_100), 1) AS "Điểm TB",
            SUM(CASE WHEN c.sentiment_label = 'Tích cực' THEN 1 ELSE 0 END) AS "Tích cực",
            SUM(CASE WHEN c.sentiment_label = 'Trung tính' THEN 1 ELSE 0 END) AS "Trung tính",
            SUM(CASE WHEN c.sentiment_label = 'Hỗn hợp' THEN 1 ELSE 0 END) AS "Hỗn hợp",
            SUM(CASE WHEN c.sentiment_label = 'Tiêu cực' THEN 1 ELSE 0 END) AS "Tiêu cực"
        FROM posts p
        JOIN comments c ON p.post_id = c.post_id
        GROUP BY p.post_id
        ORDER BY p.post_id DESC
    """
    df_summary = pd.read_sql_query(sql_summary, conn)

    if df_summary.empty:
        st.info("Chưa ghi nhận dữ liệu phân tích nào trong cơ sở dữ liệu SQLite. Vui lòng chuyển sang phân hệ 'Thu Thập YouTube' hoặc 'Phân Tích Facebook' ở menu bên trái để bắt đầu nạp dữ liệu.")
    else:
        # Thanh chọn nguồn dữ liệu phân tích
        c_pick, c_btn = st.columns([4, 1])
        with c_pick:
            post_opts = df_summary["post_id"].tolist()
            post_labels = {
                row["post_id"]: f"Bản ghi #{row['post_id']} • [{row['Nền tảng']}] {str(row['Nguồn dữ liệu'])[:60]}... ({row['Tổng số ý kiến']} bình luận)"
                for _, row in df_summary.iterrows()
            }
            selected_post_id = st.selectbox(
                "Chọn tập dữ liệu bài đăng cần phân tích:",
                options=post_opts,
                format_func=lambda pid: post_labels.get(pid, f"Bản ghi #{pid}"),
                label_visibility="collapsed"
            )
        with c_btn:
            if st.button("Làm mới dữ liệu", use_container_width=True):
                st.rerun()

        # Truy vấn thông tin chi tiết của bài đăng được chọn
        df_detail = pd.read_sql_query(f"SELECT * FROM comments WHERE post_id = {selected_post_id}", conn)
        post_meta = df_summary[df_summary["post_id"] == selected_post_id].iloc[0]

        if not df_detail.empty:
            total_cmt = len(df_detail)
            mean_score = float(df_detail["score_100"].mean())
            mean_entropy = float(df_detail["entropy"].mean())

            pos_count = int(sum(df_detail["sentiment_label"] == "Tích cực"))
            neu_count = int(sum(df_detail["sentiment_label"] == "Trung tính"))
            mix_count = int(sum(df_detail["sentiment_label"] == "Hỗn hợp"))
            neg_count = int(sum(df_detail["sentiment_label"] == "Tiêu cực"))

            pos_pct = (pos_count / total_cmt * 100) if total_cmt else 0
            neu_pct = (neu_count / total_cmt * 100) if total_cmt else 0
            mix_pct = (mix_count / total_cmt * 100) if total_cmt else 0
            neg_pct = (neg_count / total_cmt * 100) if total_cmt else 0

            # Diễn giải ngữ nghĩa khách quan cho điểm số
            if mean_score >= 75:
                verdict_title = "Đồng Thuận Tán Thưởng Rất Cao"
                verdict_desc = "Đa số ý kiến cộng đồng bày tỏ sự ủng hộ, hài lòng và đánh giá tích cực với các chi tiết được đề cập."
                verdict_color = "#10b981"
            elif mean_score >= 60:
                verdict_title = "Xu Hướng Đánh Giá Khả Quan"
                verdict_desc = "Tỷ lệ tích cực chiếm ưu thế rõ nét; ý kiến tiêu cực chỉ xuất hiện rải rác ở một số khía cạnh nhỏ."
                verdict_color = "#34d399"
            elif mean_score >= 45:
                verdict_title = "Cân Bằng & Đa Chiều"
                verdict_desc = "Ý kiến ghi nhận sự phân hóa hoặc tập trung ở vùng trung dung; không có xu hướng cực đoan rõ rệt."
                verdict_color = "#cbd5e1"
            elif mean_score >= 30:
                verdict_title = "Nhiều Ý Kiến Bất Bình & Phê Bình"
                verdict_desc = "Cộng đồng ghi nhận nhiều phản ánh tiêu cực, tranh cãi hoặc bất đồng quan điểm đáng chú ý."
                verdict_color = "#fb7185"
            else:
                verdict_title = "Phản Ứng Tiêu Cực Gay Gắt"
                verdict_desc = "Tỷ lệ bình luận chỉ trích chiếm đa số áp đảo; mức độ hài lòng ở mức rất thấp."
                verdict_color = "#f43f5e"

            # 4.1 BỐ CỤC BẤT ĐỐI XỨNG: ASYMMETRIC SENTIMENT COCKPIT
            cockpit_markup = f"""
            <div class="cockpit-grid">
                <!-- Cột Trái: Thước đo Điểm Cảm xúc Tổng hợp -->
                <div class="hero-gauge-card">
                    <div>
                        <div class="card-eyebrow">
                            <span>Chỉ Số Tâm Lý Cộng Đồng</span>
                            <span class="mono-data" style="color: #64748b;">N={total_cmt}</span>
                        </div>
                        <div class="gauge-main">
                            <div class="gauge-score-row">
                                <span class="gauge-score-value" style="color: {verdict_color};">{mean_score:.1f}</span>
                                <span class="gauge-score-max">/ 100</span>
                            </div>
                            <div class="gauge-verdict-title" style="color: {verdict_color};">{verdict_title}</div>
                            <div class="gauge-verdict-desc">{verdict_desc}</div>
                        </div>
                    </div>
                    <div>
                        <div class="spectrum-track">
                            <div class="spectrum-marker" style="left: {min(max(mean_score, 0), 100)}%;"></div>
                        </div>
                        <div class="spectrum-labels">
                            <span>0 Tiêu cực</span>
                            <span>50 Trung lập</span>
                            <span>100 Tích cực</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-top: 14px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.06); font-size: 11.5px; color: #94a3b8;">
                            <span>Độ bất định: <strong style="color: #cbd5e1;" class="mono-data">{mean_entropy:.3f}</strong></span>
                            <span>Kênh: <strong style="color: #cbd5e1;">{post_meta['Nền tảng']}</strong></span>
                        </div>
                    </div>
                </div>

                <!-- Cột Phải: Danh Sách 4 Phân Lớp Cảm Xúc Xã Hội -->
                <div class="horizon-panel">
                    <div class="card-eyebrow">
                        <span>Cơ Cấu 4 Phân Lớp Ý Kiến</span>
                        <span class="mono-data" style="color: #64748b;"></span>
                    </div>
                    <div class="horizon-list">
                        <!-- Tích cực -->
                        <div class="horizon-item">
                            <div class="horizon-item-top">
                                <div class="horizon-tag-group">
                                    <div class="horizon-dot" style="background: #10b981;"></div>
                                    <span class="horizon-name">Tích cực </span>
                                </div>
                                <div class="horizon-numbers">
                                    <span class="horizon-count">{pos_count} bình luận</span>
                                    <span class="horizon-pct" style="color: #34d399;">{pos_pct:.1f}%</span>
                                </div>
                            </div>
                            <div class="horizon-bar-bg">
                                <div class="horizon-bar-fill" style="width: {pos_pct}%; background: #10b981;"></div>
                            </div>
                        </div>
                        <!-- Trung tính -->
                        <div class="horizon-item">
                            <div class="horizon-item-top">
                                <div class="horizon-tag-group">
                                    <div class="horizon-dot" style="background: #64748b;"></div>
                                    <span class="horizon-name">Trung tính</span>
                                </div>
                                <div class="horizon-numbers">
                                    <span class="horizon-count">{neu_count} bình luận</span>
                                    <span class="horizon-pct" style="color: #cbd5e1;">{neu_pct:.1f}%</span>
                                </div>
                            </div>
                            <div class="horizon-bar-bg">
                                <div class="horizon-bar-fill" style="width: {neu_pct}%; background: #64748b;"></div>
                            </div>
                        </div>
                        <!-- Hỗn hợp -->
                        <div class="horizon-item">
                            <div class="horizon-item-top">
                                <div class="horizon-tag-group">
                                    <div class="horizon-dot" style="background: #8b5cf6;"></div>
                                    <span class="horizon-name">Hỗn hợp</span>
                                </div>
                                <div class="horizon-numbers">
                                    <span class="horizon-count">{mix_count} bình luận</span>
                                    <span class="horizon-pct" style="color: #c084fc;">{mix_pct:.1f}%</span>
                                </div>
                            </div>
                            <div class="horizon-bar-bg">
                                <div class="horizon-bar-fill" style="width: {mix_pct}%; background: #8b5cf6;"></div>
                            </div>
                        </div>
                        <!-- Tiêu cực -->
                        <div class="horizon-item">
                            <div class="horizon-item-top">
                                <div class="horizon-tag-group">
                                    <div class="horizon-dot" style="background: #f43f5e;"></div>
                                    <span class="horizon-name">Tiêu cực</span>
                                </div>
                                <div class="horizon-numbers">
                                    <span class="horizon-count">{neg_count} bình luận</span>
                                    <span class="horizon-pct" style="color: #fb7185;">{neg_pct:.1f}%</span>
                                </div>
                            </div>
                            <div class="horizon-bar-bg">
                                <div class="horizon-bar-fill" style="width: {neg_pct}%; background: #f43f5e;"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """
            render_html(cockpit_markup)

            # 4.2 WORKBENCH TRỰC QUAN HÓA KÉP (PLOTLY BIỂU DIỄN SÂU)
            col_chart1, col_chart2 = st.columns(2)

            with col_chart1:
                with st.container(border=True):
                    st.markdown("<div style='font-size:13.5px; font-weight:600; color:#f8fafc; margin-bottom:2px;'>Cơ Cấu Tỷ Lệ Cảm Xúc Toàn Diện</div>", unsafe_allow_html=True)
                    st.caption(f"Tỷ lệ % của 4 nhóm nhãn trên tập mẫu N = {total_cmt} ý kiến")

                    fig_pie = px.pie(
                        df_detail,
                        names="sentiment_label",
                        hole=0.62,
                        color="sentiment_label",
                        color_discrete_map=COLOR_PALETTE
                    )
                    fig_pie.update_traces(
                        textposition='inside',
                        textinfo='percent',
                        hovertemplate="<b>%{label}</b><br>Số ý kiến: %{value}<br>Tỷ trọng: %{percent:.1%}<extra></extra>"
                    )
                    # Xác định nhãn chiếm đa số
                    dominant_label = df_detail["sentiment_label"].value_counts().index[0]
                    dominant_pct = (df_detail["sentiment_label"].value_counts().iloc[0] / total_cmt) * 100

                    fig_pie.update_layout(
                        margin=dict(t=10, b=10, l=10, r=10),
                        height=265,
                        showlegend=True,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(family='Be Vietnam Pro', color='#cbd5e1', size=12),
                        legend=dict(orientation="h", yanchor="bottom", y=-0.22, xanchor="center", x=0.5),
                        annotations=[dict(
                            text=f'<span style="font-size:11px; color:#94a3b8;">Ưu thế</span><br><b style="font-size:15px; color:#ffffff;">{dominant_label}</b><br><span style="font-size:12px; color:#3b82f6;">{dominant_pct:.1f}%</span>',
                            x=0.5, y=0.5,
                            showarrow=False
                        )]
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)

            with col_chart2:
                with st.container(border=True):
                    st.markdown("<div style='font-size:13.5px; font-weight:600; color:#f8fafc; margin-bottom:2px;'>Phân Bổ Mật Độ Điểm Cảm Xúc (0 - 100)</div>", unsafe_allow_html=True)
                    st.caption("Khảo sát mức độ phân cực ý kiến theo 5 phân khoảng chuẩn hóa")

                    bins = [0, 20, 40, 60, 80, 100]
                    bin_labels = ["0-20 Rất xấu", "20-40 Tiêu cực", "40-60 Trung lập", "60-80 Tích cực", "80-100 Xuất sắc"]
                    df_detail["score_bin"] = pd.cut(df_detail["score_100"], bins=bins, labels=bin_labels, include_lowest=True)
                    bin_counts = df_detail["score_bin"].value_counts().reindex(bin_labels, fill_value=0).reset_index()
                    bin_counts.columns = ["Khoảng điểm", "Số lượng"]

                    fig_hist = px.bar(
                        bin_counts,
                        x="Khoảng điểm",
                        y="Số lượng",
                        text="Số lượng",
                        color="Khoảng điểm",
                        color_discrete_sequence=["#f43f5e", "#fb7185", "#94a3b8", "#34d399", "#10b981"]
                    )
                    fig_hist.update_traces(
                        textposition='outside',
                        hovertemplate="Khoảng: <b>%{x}</b><br>Số bình luận: <b>%{y}</b><extra></extra>"
                    )
                    fig_hist.update_layout(
                        margin=dict(t=10, b=10, l=10, r=10),
                        height=265,
                        showlegend=False,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(family='Be Vietnam Pro', color='#cbd5e1', size=11),
                        xaxis_title="",
                        yaxis_title="Số bình luận",
                        yaxis=dict(gridcolor="rgba(255,255,255,0.05)")
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)

            # 4.3 LĂNG KÍNH TIẾNG NÓI CỘNG ĐỒNG (REPRESENTATIVE SPOTLIGHT)
            st.markdown("""
            <div style="font-size:14.5px; font-weight:700; color:#f8fafc; margin-top:20px; margin-bottom:4px; letter-spacing:-0.01em;">
                Lăng Kính Tiếng Nói Đại Diện (Audience Voice Spotlight)
            </div>
            <div style="font-size:12.5px; color:#94a3b8; margin-bottom:12px;">
                Trích xuất 3 thái cực ý kiến tiêu biểu nhất để phục vụ công tác đối soát chất lượng dữ liệu:
            </div>
            """, unsafe_allow_html=True)

            # Lấy 3 bình luận điển hình
            pos_top = df_detail.sort_values(by="score_100", ascending=False).iloc[0]
            neg_top = df_detail.sort_values(by="score_100", ascending=True).iloc[0]
            mix_top = df_detail.sort_values(by="entropy", ascending=False).iloc[0]

            def clean_author(name, max_len=24):
                s = str(name).strip()
                return s[:max_len] + "..." if len(s) > max_len else s

            spotlight_markup = f"""
            <div class="spotlight-grid">
                <!-- Tán thưởng cao nhất -->
                <div class="voice-card voice-card-pos">
                    <div>
                        <div class="voice-header">
                            <span class="voice-role-tag" style="color: #34d399;">● Tán Thưởng Cao Nhất</span>
                            <span class="voice-badge-pill" style="background: rgba(16,185,129,0.15); color: #34d399;">{pos_top['score_100']:.1f}/100</span>
                        </div>
                        <div class="voice-quote">"{html.escape(str(pos_top['raw_text']))}"</div>
                    </div>
                    <div class="voice-footer">
                        <span>Tác giả: <strong style="color:#ffffff;">{html.escape(clean_author(pos_top['author']))}</strong></span>
                        <span class="mono-data" style="color: #34d399;">Xác suất +: {pos_top['pos_score']:.1f}%</span>
                    </div>
                </div>

                <!-- Phê bình / Bất bình cần lưu tâm -->
                <div class="voice-card voice-card-neg">
                    <div>
                        <div class="voice-header">
                            <span class="voice-role-tag" style="color: #fb7185;">● Ý Kiến Bất Bình Đáng Chú Ý</span>
                            <span class="voice-badge-pill" style="background: rgba(244,63,94,0.15); color: #fb7185;">{neg_top['score_100']:.1f}/100</span>
                        </div>
                        <div class="voice-quote">"{html.escape(str(neg_top['raw_text']))}"</div>
                    </div>
                    <div class="voice-footer">
                        <span>Tác giả: <strong style="color:#ffffff;">{html.escape(clean_author(neg_top['author']))}</strong></span>
                        <span class="mono-data" style="color: #fb7185;">Xác suất -: {neg_top['neg_score']:.1f}%</span>
                    </div>
                </div>

                <!-- Ý kiến đa chiều lưỡng lự -->
                <div class="voice-card voice-card-mix">
                    <div>
                        <div class="voice-header">
                            <span class="voice-role-tag" style="color: #c084fc;">● Ý Kiến Đa Chiều / Phân Vân</span>
                            <span class="voice-badge-pill" style="background: rgba(139,92,246,0.15); color: #c084fc;">Entropy {mix_top['entropy']:.2f}</span>
                        </div>
                        <div class="voice-quote">"{html.escape(str(mix_top['raw_text']))}"</div>
                    </div>
                    <div class="voice-footer">
                        <span>Tác giả: <strong style="color:#ffffff;">{html.escape(clean_author(mix_top['author']))}</strong></span>
                        <span style="color: #c084fc; font-weight: 500;">Vừa khen vừa chê</span>
                    </div>
                </div>
            </div>
            """
            render_html(spotlight_markup)

            # 4.4 BỘ DUYỆT BÌNH LUẬN CHI TIẾT & BỘ LỌC TƯƠNG TÁC
            st.markdown("<div style='font-size:14.5px; font-weight:700; color:#f8fafc; margin-top:20px; margin-bottom:8px;'>Duyệt & Tra Cứu Toàn Bộ Ý Kiến Đã Phân Tích</div>", unsafe_allow_html=True)
            
            with st.container(border=True):
                col_flt_label, col_flt_kw, col_exp_btn = st.columns([1.5, 2.5, 1.2])
                with col_flt_label:
                    flt_label = st.selectbox(
                        "Lọc theo phân lớp:",
                        options=["Tất cả phân lớp", "Tích cực", "Trung tính", "Hỗn hợp", "Tiêu cực"],
                        key="view_filter_label"
                    )
                with col_flt_kw:
                    flt_kw = st.text_input(
                        "Tìm kiếm từ khóa nội dung:",
                        placeholder="Nhập từ cần tìm...",
                        key="view_search_kw"
                    )
                with col_exp_btn:
                    st.write("")
                    st.write("")
                    csv_bytes = df_detail.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="📥 Xuất báo cáo CSV",
                        data=csv_bytes,
                        file_name=f"sentipulse_post_{selected_post_id}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

                df_show = df_detail.copy()
                if flt_label != "Tất cả phân lớp":
                    df_show = df_show[df_show["sentiment_label"] == flt_label]
                if flt_kw.strip():
                    df_show = df_show[df_show["raw_text"].str.contains(flt_kw.strip(), case=False, na=False)]

                st.caption(f"Đang hiển thị **{len(df_show)}** trên tổng số **{total_cmt}** bình luận phù hợp tiêu chí tra cứu.")

                st.dataframe(
                    df_show[["author", "raw_text", "score_100", "pos_score", "neu_score", "neg_score", "entropy", "sentiment_label"]],
                    column_config={
                        "author": st.column_config.TextColumn("Người đăng", width="medium"),
                        "raw_text": st.column_config.TextColumn("Nội dung bình luận", width="large"),
                        "score_100": st.column_config.ProgressColumn("Điểm (0-100)", min_value=0, max_value=100, format="%.1f"),
                        "pos_score": st.column_config.NumberColumn("% Tích cực", format="%.1f%%"),
                        "neu_score": st.column_config.NumberColumn("% Trung tính", format="%.1f%%"),
                        "neg_score": st.column_config.NumberColumn("% Tiêu cực", format="%.1f%%"),
                        "entropy": st.column_config.NumberColumn("Entropy", format="%.2f"),
                        "sentiment_label": st.column_config.TextColumn("Phân loại", width="small")
                    },
                    hide_index=True,
                    use_container_width=True
                )

            # 4.5 CỬA SỔ MINH BẠCH TRUY VẤN SQL (SQL TRANSPARENCY LENS)
            with st.expander("🔍 Cửa Sổ Minh Bạch Truy Vấn SQL Quan Hệ (SQLite JOIN & GROUP BY)", expanded=False):
                st.markdown("""
                Đoạn mã SQL sau được ứng dụng sử dụng để thực thi liên kết quan hệ 1-N giữa bảng `posts` và bảng `comments`,
                tính toán điểm trung bình và phân nhóm số lượng ý kiến theo 4 phân lớp:
                """)
                st.code("""
SELECT 
    p.post_id,
    p.platform AS "Nền tảng",
    p.post_url AS "Nguồn dữ liệu",
    p.analyzed_at AS "Thời điểm phân tích",
    COUNT(c.comment_id) AS "Tổng số ý kiến",
    ROUND(AVG(c.score_100), 1) AS "Điểm TB",
    SUM(CASE WHEN c.sentiment_label = 'Tích cực' THEN 1 ELSE 0 END) AS "Tích cực",
    SUM(CASE WHEN c.sentiment_label = 'Trung tính' THEN 1 ELSE 0 END) AS "Trung tính",
    SUM(CASE WHEN c.sentiment_label = 'Hỗn hợp' THEN 1 ELSE 0 END) AS "Hỗn hợp",
    SUM(CASE WHEN c.sentiment_label = 'Tiêu cực' THEN 1 ELSE 0 END) AS "Tiêu cực"
FROM posts p
JOIN comments c ON p.post_id = c.post_id
GROUP BY p.post_id
ORDER BY p.post_id DESC;
                """, language="sql")

                st.markdown("<div style='font-size:13px; font-weight:600; color:#cbd5e1; margin-top:12px; margin-bottom:6px;'>Bảng Dữ Liệu Kết Xuất Tổng Thể Từ CSDL:</div>", unsafe_allow_html=True)
                st.dataframe(
                    df_summary,
                    column_config={
                        "post_id": st.column_config.NumberColumn("Mã Bài", width="small"),
                        "Nền tảng": st.column_config.TextColumn("Nền tảng", width="small"),
                        "Nguồn dữ liệu": st.column_config.TextColumn("Nguồn dữ liệu / URL", width="large"),
                        "Thời điểm phân tích": st.column_config.TextColumn("Thời gian", width="medium"),
                        "Điểm TB": st.column_config.ProgressColumn("Điểm TB", min_value=0, max_value=100, format="%.1f")
                    },
                    hide_index=True,
                    use_container_width=True
                )

    conn.close()

# ==============================================================================
# 5. VIEW 2: THU THẬP & PHÂN TÍCH BÌNH LUẬN YOUTUBE
# ==============================================================================
elif nav_choice == "🎥 Thu Thập & Phân Tích YouTube":
    render_html("""
    <div class="lab-header">
        <div class="lab-title-area">
            <h1>Thu Thập & Phân Tích Bình Luận YouTube</h1>
            <p>Trích xuất bình luận công khai từ liên kết video YouTube và chạy phân tích cảm xúc thời gian thực qua ViSoBERT v2.</p>
        </div>
        <div class="spec-pills">
        </div>
    </div>
    """)

    with st.container(border=True):
        st.markdown("<div style='font-size:15px; font-weight:700; color:#f8fafc; margin-bottom:2px;'>Thiết Lập Thu Thập Dữ Liệu Video</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:12.5px; color:#94a3b8; margin-bottom:16px;'>Cung cấp URL video YouTube công khai và chỉ định số lượng bình luận tối đa cần thu thập.</div>", unsafe_allow_html=True)

        col_yt_url, col_yt_sample = st.columns([4, 1.2])
        with col_yt_url:
            yt_input_url = st.text_input(
                "Đường dẫn video YouTube:",
                value=st.session_state.get("cached_yt_url", ""),
                placeholder="https://www.youtube.com/watch?v=...",
                key="yt_link_input_field"
            )
        with col_yt_sample:
            st.write("")
            st.write("")
            if st.button("🔗 Nạp link video mẫu", use_container_width=True):
                st.session_state["cached_yt_url"] = "https://www.youtube.com/watch?v=tpOkBUamk6M"
                st.rerun()

        max_yt_comments = st.slider(
            "Giới hạn số bình luận thu thập (xếp theo độ phổ biến):",
            min_value=10, max_value=200, value=30, step=10
        )

        btn_run_youtube = st.button("🚀 Bắt Đầu Thu Thập & Phân Tích", use_container_width=True)

    if btn_run_youtube:
        if yt_input_url.strip():
            with st.spinner("Đang kết nối API YouTube, cào dữ liệu bình luận và tính toán suy luận với ViSoBERT v2..."):
                try:
                    downloader = YoutubeCommentDownloader()
                    generator = downloader.get_comments_from_url(yt_input_url.strip(), sort_by=SORT_BY_POPULAR)
                    raw_comments = [{"author": c["author"], "text": c["text"]} for c in islice(generator, max_yt_comments)]
                    
                    if raw_comments:
                        analyzed_results = predict_batch_comments(raw_comments, tokenizer, model, device, inf_cfg)
                        
                        # Lưu dữ liệu vào CSDL SQLite
                        conn = sqlite3.connect(DB_NAME)
                        cur = conn.cursor()
                        cur.execute("INSERT INTO posts (platform, post_url) VALUES (?, ?)", ("YouTube", yt_input_url.strip()))
                        new_post_id = cur.lastrowid
                        cur.executemany("""
                            INSERT INTO comments (post_id, author, raw_text, pos_score, neu_score, neg_score, score_100, entropy, sentiment_label)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, [(new_post_id, *r) for r in analyzed_results])
                        conn.commit()
                        conn.close()

                        df_res_yt = pd.DataFrame(analyzed_results, columns=[
                            "author", "raw_text", "pos_score", "neu_score", "neg_score", "score_100", "entropy", "sentiment_label"
                        ])

                        st.success(f"✅ Hoàn tất thu thập và phân tích **{len(df_res_yt)}** bình luận! Đã lưu trữ thành công vào CSDL với mã bản ghi **#{new_post_id}**.")

                        # Khối Tóm Tắt Nhanh (Inline Executive Briefing)
                        with st.container(border=True):
                            st.markdown(f"<div style='font-size:14px; font-weight:700; color:#f8fafc; margin-bottom:10px;'>Tóm Tắt Kết Quả Phân Tích Tức Thì (Bản ghi #{new_post_id})</div>", unsafe_allow_html=True)
                            
                            c_kpi1, c_kpi2, c_kpi3, c_kpi4 = st.columns(4)
                            c_kpi1.metric("Tổng ý kiến", f"{len(df_res_yt)}")
                            c_kpi2.metric("Điểm TB", f"{df_res_yt['score_100'].mean():.1f} / 100")
                            c_kpi3.metric("Tích cực", f"{sum(df_res_yt['sentiment_label']=='Tích cực')} câu")
                            c_kpi4.metric("Tiêu cực", f"{sum(df_res_yt['sentiment_label']=='Tiêu cực')} câu")

                            st.caption("Xem trước 5 bình luận đầu tiên trong tập dữ liệu vừa cào:")
                            st.dataframe(
                                df_res_yt[["author", "raw_text", "score_100", "sentiment_label"]].head(5),
                                column_config={
                                    "author": "Người đăng",
                                    "raw_text": st.column_config.TextColumn("Nội dung", width="large"),
                                    "score_100": st.column_config.ProgressColumn("Điểm (0-100)", min_value=0, max_value=100, format="%.0f"),
                                    "sentiment_label": "Nhãn"
                                },
                                hide_index=True,
                                use_container_width=True
                            )
                    else:
                        st.warning("Không tìm thấy bình luận nào trên video này, hoặc video đã bị chủ sở hữu tắt tính năng bình luận.")
                except Exception as err:
                    st.error(f"Xảy ra lỗi trong quá trình thu thập hoặc phân tích: {str(err)}")
        else:
            st.error("Vui lòng nhập đường dẫn video YouTube hợp lệ trước khi bắt đầu.")

# ==============================================================================
# 6. VIEW 3: PHÂN TÍCH BÌNH LUẬN FACEBOOK
# ==============================================================================
elif nav_choice == "📘 Phân Tích Bình Luận Facebook":
    render_html("""
    <div class="lab-header">
        <div class="lab-title-area">
            <h1>Phân Tích Dữ Liệu Bình Luận Facebook</h1>
            <p>Hỗ trợ phân tích dữ liệu bài viết Fanpage/Nhóm qua tải tệp CSV hoặc nhập trực tiếp văn bản tiếng Việt.</p>
        </div>
        <div class="spec-pills">
        </div>
    </div>
    """)

    with st.container(border=True):
        st.markdown("<div style='font-size:15px; font-weight:700; color:#f8fafc; margin-bottom:2px;'>Nguồn Dữ Liệu Facebook</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:12.5px; color:#94a3b8; margin-bottom:16px;'>Nhập tên định danh nguồn bài đăng và chọn phương thức cung cấp nội dung bình luận.</div>", unsafe_allow_html=True)

        fb_src_title = st.text_input(
            "Tên định danh bài đăng hoặc nguồn Fanpage:",
            value="Bài đăng Fanpage",
            key="fb_post_title_field"
        )

        tab_manual, tab_csv = st.tabs(["✏️ Nhập trực tiếp nhiều dòng", "📁 Tải lên tệp CSV"])

        with tab_manual:
            c_label, c_sample_btn = st.columns([3, 1.2])
            with c_label:
                st.caption("Dán các bình luận cần phân tích (mỗi bình luận đặt trên một dòng riêng biệt):")
            with c_sample_btn:
                if st.button("📝 Nạp dữ liệu tiếng Việt mẫu", use_container_width=True):
                    st.session_state["cached_fb_text"] = (
                        "Hàng dùng mượt mà, nhân viên hỗ trợ nhiệt tình lắm ạ 😍\n"
                        "Giao diện nhìn hơi đơn giản cơ mà dùng sướng tay phết =))\n"
                        "Làm ăn chán đời, gọi điện hotline không thèm nghe máy 😡\n"
                        "Sản phẩm tạm ổn, mức giá này thì chấp nhận được\n"
                        "Quảng cáo thì rầm rộ nhưng chất lượng thực tế quá tệ\n"
                        "Chán nhưng thực sự rất vui :3"
                    )
                    st.rerun()

            fb_text_input = st.text_area(
                "Nội dung văn bản:",
                value=st.session_state.get(
                    "cached_fb_text",
                    "Hàng dùng mượt mà, nhân viên hỗ trợ nhiệt tình lắm ạ 😍\nGiao diện nhìn hơi đơn giản cơ mà dùng sướng tay phết =))\nLàm ăn chán đời, gọi điện hotline không thèm nghe máy 😡\nSản phẩm tạm ổn, mức giá này thì chấp nhận được\nQuảng cáo thì rầm rộ nhưng chất lượng thực tế quá tệ\nChán nhưng thực sự rất vui :3"
                ),
                height=150,
                label_visibility="collapsed"
            )

        with tab_csv:
            st.caption("Tải tệp CSV (Cột dữ liệu văn bản đầu tiên sẽ được hệ thống trích xuất làm bình luận):")
            uploaded_csv_file = st.file_uploader("Chọn file CSV:", type=["csv"], label_visibility="collapsed")

        btn_run_fb = st.button("🚀 Bắt Đầu Phân Tích Dữ Liệu Facebook", use_container_width=True)

    if btn_run_fb:
        parsed_fb_comments = []
        if uploaded_csv_file is not None:
            try:
                df_upload = pd.read_csv(uploaded_csv_file)
                first_col = df_upload.columns[0]
                parsed_fb_comments = [
                    {"author": "Facebook User", "text": str(row)}
                    for row in df_upload[first_col].dropna()
                    if str(row).strip()
                ]
            except Exception as err:
                st.error(f"Lỗi khi đọc file CSV: {str(err)}")
        elif fb_text_input.strip():
            raw_lines = [line.strip() for line in fb_text_input.split("\n") if line.strip()]
            parsed_fb_comments = [{"author": "Facebook User", "text": line} for line in raw_lines]

        if parsed_fb_comments:
            with st.spinner("Đang tiền xử lý emoticon tiếng Việt, emoji và suy luận ViSoBERT v2..."):
                analyzed_fb_results = predict_batch_comments(parsed_fb_comments, tokenizer, model, device, inf_cfg)
                
                # Lưu vào SQLite
                conn = sqlite3.connect(DB_NAME)
                cur = conn.cursor()
                cur.execute("INSERT INTO posts (platform, post_url) VALUES (?, ?)", ("Facebook", fb_src_title.strip()))
                new_post_id_fb = cur.lastrowid
                cur.executemany("""
                    INSERT INTO comments (post_id, author, raw_text, pos_score, neu_score, neg_score, score_100, entropy, sentiment_label)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [(new_post_id_fb, *r) for r in analyzed_fb_results])
                conn.commit()
                conn.close()

                df_res_fb = pd.DataFrame(analyzed_fb_results, columns=[
                    "author", "raw_text", "pos_score", "neu_score", "neg_score", "score_100", "entropy", "sentiment_label"
                ])

                st.success(f"✅ Hoàn tất phân tích **{len(df_res_fb)}** bình luận Facebook! Đã lưu trữ thành công vào CSDL với mã bản ghi **#{new_post_id_fb}**.")

                with st.container(border=True):
                    st.markdown(f"<div style='font-size:14px; font-weight:700; color:#f8fafc; margin-bottom:10px;'>Tóm Tắt Kết Quả Phân Tích Tức Thì (Bản ghi #{new_post_id_fb})</div>", unsafe_allow_html=True)
                    
                    c_fb1, c_fb2, c_fb3, c_fb4 = st.columns(4)
                    c_fb1.metric("Tổng ý kiến", f"{len(df_res_fb)}")
                    c_fb2.metric("Điểm TB", f"{df_res_fb['score_100'].mean():.1f} / 100")
                    c_fb3.metric("Tích cực", f"{sum(df_res_fb['sentiment_label']=='Tích cực')} câu")
                    c_fb4.metric("Tiêu cực", f"{sum(df_res_fb['sentiment_label']=='Tiêu cực')} câu")

                    st.caption("Xem trước 5 bình luận vừa phân tích:")
                    st.dataframe(
                        df_res_fb[["author", "raw_text", "score_100", "sentiment_label"]].head(5),
                        column_config={
                            "author": "Người đăng",
                            "raw_text": st.column_config.TextColumn("Nội dung", width="large"),
                            "score_100": st.column_config.ProgressColumn("Điểm (0-100)", min_value=0, max_value=100, format="%.0f"),
                            "sentiment_label": "Nhãn"
                        },
                        hide_index=True,
                        use_container_width=True
                    )
        else:
            st.warning("Vui lòng nhập ít nhất một bình luận văn bản hoặc tải lên tệp CSV hợp lệ.")
