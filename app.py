import streamlit as st
import sqlite3
import pandas as pd
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from youtube_comment_downloader import YoutubeCommentDownloader, SORT_BY_POPULAR
import plotly.express as px
import emoji
import re
from itertools import islice

# ==========================================
# 1. CẤU HÌNH & TỰ ĐỘNG TẠO DATABASE SQL (SQLite)
# ==========================================
DB_NAME = "sentiment_analytics.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Bảng 1: Lưu bài đăng (Posts)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            post_id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            post_url TEXT NOT NULL,
            analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Bảng 2: Lưu bình luận (Comments) liên kết khóa ngoại với Posts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            author TEXT,
            raw_text TEXT NOT NULL,
            pos_score REAL,
            neg_score REAL,
            sentiment_label TEXT,
            FOREIGN KEY (post_id) REFERENCES posts (post_id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 2. TẢI MODEL AI TỪ THƯ MỤC Model_viso_bert
# ==========================================
@st.cache_resource
def load_ai_model():
    model_path = "./Model_viso_bert"  # Đã khớp với tên thư mục trên máy bạn
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path).to(device)
    model.eval()
    return tokenizer, model, device

emoticon_dict = {
    ":)))": " rất vui ", ":))": " vui vẻ ", ":)": " vui ",
    "=)))": " cười rất vui ", "=))": " cười vui vẻ ", ":v": " vui vẻ ",
    "<3": " yêu thích ", ":3": " dễ thương ",
    ":(((": " rất buồn ", ":((": " rất buồn ", ":(": " buồn ", "-_-": " chán nản ",
    "buồn cười": "vui vẻ", "buồn ngủ": "hơi mệt cần nghỉ ngơi"
}

def clean_and_normalize_text(text):
    text = str(text).strip()
    for emo, meaning in emoticon_dict.items():
        text = re.sub(re.compile(re.escape(emo), re.IGNORECASE), meaning, text)
    text = emoji.demojize(text, delimiters=(" ", " ")).replace("_", " ")
    return re.sub(r'\s+', ' ', text).strip()

def predict_batch_comments(comments_list, tokenizer, model, device):
    results = []
    for item in comments_list:
        raw_text = item["text"]
        author = item.get("author", "Ẩn danh")
        processed = clean_and_normalize_text(raw_text)
        
        inputs = tokenizer(processed, return_tensors="pt", truncation=True, padding=True, max_length=128).to(device)
        with torch.no_grad():
            logits = model(**inputs).logits
            probs = F.softmax(logits / 1.3, dim=-1).squeeze()
            
        neg_p = round(probs[0].item() * 100, 2)
        pos_p = round(probs[1].item() * 100, 2)
        
        if pos_p >= 65:
            label = "Tích cực"
        elif pos_p >= 40:
            label = "Trung tính"
        else:
            label = "Tiêu cực"
            
        results.append((author, raw_text, pos_p, neg_p, label))
    return results

# ==========================================
# 3. GIAO DIỆN WEB & LUỒNG XỬ LÝ
# ==========================================
st.set_page_config(page_title="AI Social Sentiment Analytics", layout="wide")
st.title("📊 Hệ thống Phân tích Cảm xúc Bình luận Facebook & YouTube (ViSoBERT + SQL)")

tokenizer, model, device = load_ai_model()

tab1, tab2, tab3 = st.tabs(["🎥 Quét Link YouTube", "📘 Phân tích Bình luận Facebook (CSV/Text)", "🗄️ Truy vấn & Thống kê SQL"])

# --- TAB 1: CÀO VÀ PHÂN TÍCH YOUTUBE ---
with tab1:
    st.subheader("Tự động tải và phân tích bình luận từ Video YouTube")
    yt_url = st.text_input("Nhập đường link Video YouTube:", placeholder="https://www.youtube.com/watch?v=...")
    max_cmt = st.slider("Số lượng bình luận muốn lấy:", 10, 200, 30)
    
    if st.button("🚀 Quét & Phân tích YouTube"):
        if yt_url:
            with st.spinner("Đang tải bình luận từ YouTube và chạy mô hình ViSoBERT..."):
                downloader = YoutubeCommentDownloader()
                generator = downloader.get_comments_from_url(yt_url, sort_by=SORT_BY_POPULAR)
                raw_comments = [{"author": c["author"], "text": c["text"]} for c in islice(generator, max_cmt)]
                
                if raw_comments:
                    analyzed_data = predict_batch_comments(raw_comments, tokenizer, model, device)
                    
                    conn = sqlite3.connect(DB_NAME)
                    cur = conn.cursor()
                    cur.execute("INSERT INTO posts (platform, post_url) VALUES (?, ?)", ("YouTube", yt_url))
                    post_id = cur.lastrowid
                    
                    cur.executemany("""
                        INSERT INTO comments (post_id, author, raw_text, pos_score, neg_score, sentiment_label)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, [(post_id, *row) for row in analyzed_data])
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Đã phân tích và lưu {len(analyzed_data)} bình luận vào SQL (Mã bài đăng: #{post_id})! Hãy sang Tab 3 để xem biểu đồ.")
                else:
                    st.warning("Không tìm thấy bình luận nào hoặc video đã tắt bình luận.")

# --- TAB 2: PHÂN TÍCH FACEBOOK ---
with tab2:
    st.subheader("Phân tích bộ bình luận từ bài đăng Facebook")
    fb_source_name = st.text_input("Tên bài đăng / Link bài viết Facebook:", value="Bài đăng Fanpage BTL Python")
    uploaded_file = st.file_uploader("Cách 1: Tải lên file CSV chứa bình luận", type=["csv"])
    manual_text = st.text_area(
        "Cách 2: Hoặc dán trực tiếp danh sách bình luận Facebook vào đây (mỗi bình luận 1 dòng):", 
        value="Hàng dùng mượt phết, shop phục vụ nhiệt tình 😍\nGiao diện nhìn hơi phèn cơ mà dùng sướng tay phết =))\nLàm ăn chán đời, gọi điện không thèm nghe máy 😡\nTôi buồn ngủ quá\nQuảng cáo thì rầm rộ đấy nhưng chất lượng quá tệ",
        height=150
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
            analyzed_data = predict_batch_comments(fb_comments, tokenizer, model, device)
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("INSERT INTO posts (platform, post_url) VALUES (?, ?)", ("Facebook", fb_source_name))
            post_id = cur.lastrowid
            cur.executemany("""
                INSERT INTO comments (post_id, author, raw_text, pos_score, neg_score, sentiment_label)
                VALUES (?, ?, ?, ?, ?, ?)
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
            COUNT(c.comment_id) AS Tổng_bình_luận,
            ROUND(AVG(c.pos_score), 2) AS Điểm_Tích_Cực_TB,
            SUM(CASE WHEN c.sentiment_label = 'Tích cực' THEN 1 ELSE 0 END) AS Số_Tích_Cực,
            SUM(CASE WHEN c.sentiment_label = 'Trung tính' THEN 1 ELSE 0 END) AS Số_Trung_Tính,
            SUM(CASE WHEN c.sentiment_label = 'Tiêu cực' THEN 1 ELSE 0 END) AS Số_Tiêu_Cực
        FROM posts p
        JOIN comments c ON p.post_id = c.post_id
        GROUP BY p.post_id
        ORDER BY p.post_id DESC
    """
    df_summary = pd.read_sql_query(sql_summary, conn)
    st.write("**1. Bảng tổng hợp các bài đăng đã phân tích (Truy vấn `JOIN` & `GROUP BY`):**")
    st.dataframe(df_summary, use_container_width=True)
    
    if not df_summary.empty:
        selected_post = st.selectbox("Chọn Mã bài đăng (post_id) để xem biểu đồ và lọc bình luận:", df_summary["post_id"])
        df_detail = pd.read_sql_query(f"SELECT * FROM comments WHERE post_id = {selected_post}", conn)
        
        col1, col2 = st.columns([1, 2])
        with col1:
            fig = px.pie(df_detail, names="sentiment_label", title=f"Tỷ lệ Cảm xúc (Bài đăng #{selected_post})",
                         color="sentiment_label",
                         color_discrete_map={"Tích cực": "#2ecc71", "Trung tính": "#95a5a6", "Tiêu cực": "#e74c3c"})
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.write("**Danh sách bình luận chi tiết trong Database:**")
            st.dataframe(df_detail[["author", "raw_text", "pos_score", "neg_score", "sentiment_label"]], use_container_width=True)
            
    conn.close()