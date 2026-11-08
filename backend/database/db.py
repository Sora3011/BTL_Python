import sqlite3
from typing import Tuple, List, Any
import pandas as pd

DB_NAME = "sentiment_analytics.db"

def get_connection() -> sqlite3.Connection:
    """Tạo và trả về kết nối SQLite3."""
    return sqlite3.connect(DB_NAME)

def init_db() -> None:
    """Khởi tạo schema cơ sở dữ liệu nếu chưa tồn tại."""
    conn = get_connection()
    try:
        with conn:
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
    finally:
        conn.close()

def get_system_stats() -> Tuple[int, int]:
    """Lấy tổng số bài đăng và tổng số bình luận đã lưu trữ."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM posts")
        total_posts = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM comments")
        total_comments = cur.fetchone()[0]
        return total_posts, total_comments
    finally:
        conn.close()

def get_posts_summary() -> pd.DataFrame:
    """Truy vấn tổng hợp số liệu bài đăng và thống kê phân bổ cảm xúc từ SQLite."""
    conn = get_connection()
    try:
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
        df = pd.read_sql_query(sql_summary, conn)
        return df
    finally:
        conn.close()

def get_post_comments(post_id: int) -> pd.DataFrame:
    """Lấy toàn bộ bình luận chi tiết của một bài đăng theo post_id."""
    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM comments WHERE post_id = ?", conn, params=(int(post_id),))
        return df
    finally:
        conn.close()

def save_post_and_comments(platform: str, post_url: str, analyzed_results: List[Any]) -> int:
    """
    Lưu thông tin bài đăng và danh sách kết quả phân tích bình luận vào CSDL.
    Trả về post_id mới tạo.
    """
    conn = get_connection()
    try:
        with conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO posts (platform, post_url) VALUES (?, ?)", (platform, post_url))
            new_post_id = cur.lastrowid
            cur.executemany("""
                INSERT INTO comments (post_id, author, raw_text, pos_score, neu_score, neg_score, score_100, entropy, sentiment_label)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [(new_post_id, *r) for r in analyzed_results])
        return new_post_id
    finally:
        conn.close()
