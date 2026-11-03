import os
import json
import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from youtube_comment_downloader import YoutubeCommentDownloader, SORT_BY_POPULAR
import plotly.express as px
import emoji
import re
from itertools import islice

# ==========================================
# 0. CẤU HÌNH TRANG & GIAO DIỆN
# ==========================================
st.set_page_config(page_title="AI Social Sentiment Analytics", page_icon="📊", layout="wide")

st.markdown("""
<style>
    .hero-box {
        background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
        padding: 20px 26px;
        border-radius: 12px;
        color: white;
        margin-bottom: 20px;
    }
    .hero-box h1 { margin: 0; font-size: 25px; font-weight: 700; color: white; }
    .hero-box p { margin: 5px 0 0 0; font-size: 14px; opacity: 0.9; }
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 12px 16px;
        border-radius: 10px;
    }
    div.stButton > button {
        background: #2563eb;
        color: white; border: none; border-radius: 8px;
        padding: 10px 20px; font-weight: 600; width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. KHỞI TẠO CƠ SỞ DỮ LIỆU SQL (SQLite)
# ==========================================
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

# ==========================================
# 2. TẢI MODEL VISOBERT V2 & HÀM DỰ ĐOÁN
# ==========================================
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

def clean_text(text, emoji_mode="keep"):
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

# ==========================================
# 3. GIAO DIỆN WEB CHÍNH (3 TAB)
# ==========================================
tokenizer, model, device, inf_cfg = load_ai_model()

st.markdown("""
<div class="hero-box">
    <h1>📊 Hệ thống Phân tích Cảm xúc Bình luận Facebook & YouTube (ViSoBERT v2 + SQL)</h1>
    <p>Bài tập lớn Python: Phân loại 3 nhãn & Hỗn hợp • Quản trị Cơ sở dữ liệu SQLite</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs([
    "🎥 Quét Link YouTube", 
    "📘 Phân tích Bình luận Facebook", 
    "🗄️ Truy vấn & Thống kê SQL"
])

# --- TAB 1: YOUTUBE ---
with tab1:
    st.subheader("Tự động tải và phân tích bình luận từ Video YouTube")
    c1, c2 = st.columns([2, 1])
    with c1:
        yt_url = st.text_input("Nhập đường link Video YouTube:", placeholder="https://www.youtube.com/watch?v=...")
    with c2:
        max_cmt = st.slider("Số lượng bình luận muốn lấy:", 10, 200, 30)
    
    if st.button("🚀 Quét & Phân tích YouTube"):
        if yt_url:
            with st.spinner("Đang tải bình luận và chạy mô hình ViSoBERT v2..."):
                downloader = YoutubeCommentDownloader()
                generator = downloader.get_comments_from_url(yt_url, sort_by=SORT_BY_POPULAR)
                raw_comments = [{"author": c["author"], "text": c["text"]} for c in islice(generator, max_cmt)]
                
                if raw_comments:
                    analyzed_data = predict_batch_comments(raw_comments, tokenizer, model, device, inf_cfg)
                    conn = sqlite3.connect(DB_NAME)
                    cur = conn.cursor()
                    cur.execute("INSERT INTO posts (platform, post_url) VALUES (?, ?)", ("YouTube", yt_url))
                    post_id = cur.lastrowid
                    cur.executemany("""
                        INSERT INTO comments (post_id, author, raw_text, pos_score, neu_score, neg_score, score_100, entropy, sentiment_label)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, [(post_id, *row) for row in analyzed_data])
                    conn.commit()
                    conn.close()

                    st.success(f"✅ Đã lưu {len(analyzed_data)} bình luận vào SQL (Mã bài đăng: #{post_id})! Hãy sang Tab 3 để xem biểu đồ.")
                else:
                    st.warning("Không tìm thấy bình luận nào hoặc video đã tắt bình luận.")

# --- TAB 2: FACEBOOK ---
with tab2:
    st.subheader("Phân tích bộ bình luận từ bài đăng Facebook")
    fb_source_name = st.text_input("Tên bài đăng / Link bài viết Facebook:", value="Bài đăng Fanpage BTL Python")
    uploaded_file = st.file_uploader("Cách 1: Tải lên file CSV chứa bình luận", type=["csv"])
    manual_text = st.text_area(
        "Cách 2: Hoặc dán trực tiếp danh sách bình luận Facebook vào đây (mỗi bình luận 1 dòng):", 
        value="Hàng dùng mượt phết, shop phục vụ nhiệt tình 😍\nGiao diện nhìn hơi phèn cơ mà dùng sướng tay phết =))\nChán nhưng thực sự rất vui\nLàm ăn chán đời, gọi điện không thèm nghe máy 😡\nTôi buồn ngủ quá\nQuảng cáo thì rầm rộ đấy nhưng chất lượng quá tệ",
        height=160
    )
    
    if st.button("🚀 Phân tích Dữ liệu Facebook"):
        fb_comments = []
        if uploaded_file is not None:
            df_up = pd.read_csv(uploaded_file)
            col_name = df_up.columns[0]
            fb_comments = [{"author": "FB User", "text": str(row)} for row in df_up[col_name].dropna()]
        elif manual_text.strip():
            lines = [line.strip() for line in manual_text.split("\n") if line.strip()]
            fb_comments = [{"author": "FB User", "text": line} for line in lines]
            
        if fb_comments:
            analyzed_data = predict_batch_comments(fb_comments, tokenizer, model, device, inf_cfg)
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("INSERT INTO posts (platform, post_url) VALUES (?, ?)", ("Facebook", fb_source_name))
            post_id = cur.lastrowid
            cur.executemany("""
                INSERT INTO comments (post_id, author, raw_text, pos_score, neu_score, neg_score, score_100, entropy, sentiment_label)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [(post_id, *row) for row in analyzed_data])
            conn.commit()
            conn.close()

            st.success(f"✅ Đã lưu {len(analyzed_data)} bình luận Facebook vào SQL (Mã bài đăng: #{post_id})! Hãy sang Tab 3 để xem thống kê.")

# --- TAB 3: DASHBOARD & TRUY VẤN SQL ---
with tab3:
    st.subheader("📊 Thống kê dữ liệu từ SQL bằng truy vấn JOIN & GROUP BY")
    conn = sqlite3.connect(DB_NAME)
    
    sql_summary = """
        SELECT 
            p.post_id,
            p.platform AS Nền_tảng,
            p.post_url AS Nguồn_bài_đăng,
            COUNT(c.comment_id) AS Tổng_BL,
            ROUND(AVG(c.score_100), 1) AS Điểm_TB_100,
            SUM(CASE WHEN c.sentiment_label = 'Tích cực' THEN 1 ELSE 0 END) AS Số_Tích_Cực,
            SUM(CASE WHEN c.sentiment_label = 'Trung tính' THEN 1 ELSE 0 END) AS Số_Trung_Tính,
            SUM(CASE WHEN c.sentiment_label = 'Hỗn hợp' THEN 1 ELSE 0 END) AS Số_Hỗn_Hợp,
            SUM(CASE WHEN c.sentiment_label = 'Tiêu cực' THEN 1 ELSE 0 END) AS Số_Tiêu_Cực
        FROM posts p
        JOIN comments c ON p.post_id = c.post_id
        GROUP BY p.post_id
        ORDER BY p.post_id DESC
    """
    df_summary = pd.read_sql_query(sql_summary, conn)
    st.write("**1. Bảng tổng hợp các bài đăng đã phân tích (Truy vấn `JOIN` & `GROUP BY`):**")
    st.dataframe(df_summary, use_container_width=True, hide_index=True)
    
    if not df_summary.empty:
        selected_post = st.selectbox("Chọn Mã bài đăng (post_id) để xem biểu đồ và lọc bình luận:", df_summary["post_id"])
        df_detail = pd.read_sql_query(f"SELECT * FROM comments WHERE post_id = {selected_post}", conn)
        
        mean_sc = float(df_detail["score_100"].mean()) if not df_detail.empty else 50.0
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🎯 Điểm Cảm xúc TB", f"{mean_sc:.1f} / 100")
        m2.metric("🟢 Tích cực", f"{sum(df_detail['sentiment_label']=='Tích cực')} câu")
        m3.metric("⚪ Trung tính & 🟣 Hỗn hợp", f"{sum(df_detail['sentiment_label'].isin(['Trung tính', 'Hỗn hợp']))} câu")
        m4.metric("🔴 Tiêu cực", f"{sum(df_detail['sentiment_label']=='Tiêu cực')} câu")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            fig = px.pie(
                df_detail, names="sentiment_label", hole=0.4,
                title=f"Tỷ lệ Cảm xúc (Bài đăng #{selected_post})",
                color="sentiment_label",
                color_discrete_map={
                    "Tích cực": "#2ecc71", 
                    "Trung tính": "#95a5a6", 
                    "Hỗn hợp": "#8b5cf6",
                    "Tiêu cực": "#e74c3c"
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.write("**Danh sách bình luận chi tiết trong Database:**")
            st.dataframe(
                df_detail[["author", "raw_text", "score_100", "pos_score", "neu_score", "neg_score", "sentiment_label"]],
                column_config={
                    "author": "Người dùng",
                    "raw_text": st.column_config.TextColumn("Nội dung bình luận", width="large"),
                    "score_100": st.column_config.ProgressColumn("Điểm (0-100)", format="%.1f", min_value=0, max_value=100),
                    "pos_score": "% Tích cực",
                    "neu_score": "% Trung tính",
                    "neg_score": "% Tiêu cực",
                    "sentiment_label": "Nhãn Cảm xúc"
                },
                use_container_width=True, hide_index=True
            )
            
    conn.close()
