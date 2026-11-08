import torch
import streamlit as st
from frontend.components.style_loader import render_html
from backend.database.db import get_system_stats

def render_sidebar():
    """
    Hiển thị Sidebar Chẩn Đoán Hệ Thống & Môi Trường Máy Chủ.
    Hoàn toàn không dùng emoji AI rập khuôn.
    """
    with st.sidebar:
        render_html("""
        <div class="sidebar-brand-card">
            <div class="brand-meta-badge">
                <span class="brand-pulse-dot"></span>
                <span>SYSTEM DIAGNOSTICS</span>
            </div>
            <h2 class="brand-hero-title">ViSoBERT Studio</h2>
            <div class="brand-hero-sub">Neural Social Intelligence & SQLite Relational Core</div>
        </div>
        """)

        nav_choice = st.radio(
            "Phân hệ làm việc:",
            options=[
                ":material/monitoring: Tổng Quan & Phân Tích",
                ":material/smart_display: Khai Thác YouTube",
                ":material/forum: Dữ Liệu Facebook"
            ],
            index=0,
            label_visibility="collapsed"
        )

        sb_total_posts, sb_total_comments = get_system_stats()
        device_name = "CUDA GPU" if torch.cuda.is_available() else "CPU Multi-Core"

        render_html(f"""
        <div class="sidebar-telemetry-pod">
            <div class="pod-title">
                <span>Thông Số Môi Trường</span>
                <span style="color: #38bdf8; font-size: 10px;">SYS_INFO</span>
            </div>
            <div class="pod-row">
                <span class="pod-label">Mô hình AI:</span>
                <span class="pod-val">ViSoBERT v2</span>
            </div>
            <div class="pod-row">
                <span class="pod-label">Kiến trúc:</span>
                <span class="pod-val">XLM-RoBERTa</span>
            </div>
            <div class="pod-row">
                <span class="pod-label">Thiết bị suy luận:</span>
                <span class="pod-val" style="color: #38bdf8;">{device_name}</span>
            </div>
            <div class="pod-row">
                <span class="pod-label">Hiệu chuẩn:</span>
                <span class="pod-val">T = 1.3 Softmax</span>
            </div>
            <div class="pod-row">
                <span class="pod-label">CSDL quan hệ:</span>
                <span class="pod-val">SQLite 3.x</span>
            </div>
            <div class="pod-row">
                <span class="pod-label">Tổng bài lưu trữ:</span>
                <span class="pod-val">{sb_total_posts} bài</span>
            </div>
            <div class="pod-row">
                <span class="pod-label">Tổng bình luận:</span>
                <span class="pod-val" style="color: #10b981;">{sb_total_comments} bản ghi</span>
            </div>
        </div>

        <div class="sidebar-telemetry-pod" style="margin-top: 12px;">
            <div class="pod-title">
                <span>Ghi Chú Phân Loại</span>
                <span style="color: #a855f7; font-size: 10px;">METHOD</span>
            </div>
            <div style="font-size: 11.5px; color: #94a3b8; line-height: 1.55;">
                • <strong>Thang điểm 0 - 100:</strong> Tính chuẩn hóa từ hiệu xác suất <code>P(pos) - P(neg)</code>.<br>
                • <strong>Hỗn hợp:</strong> Cả xác suất tích cực và tiêu cực cùng đạt ≥ 25%.<br>
                • <strong>Shannon Entropy:</strong> Đo độ bất định của phân phối cảm xúc.
            </div>
        </div>
        """)

    return nav_choice
