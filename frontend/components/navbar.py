import torch
import streamlit as st
from backend.database.db import get_system_stats
from frontend.components.style_loader import render_html

def render_top_header():
    """
    Hien thi Thanh Thuong Hieu va Telemetry He Thong o dinh trang.
    Su dung bieu tuong vector SVG hinh hoc va chip telemetry phat quang.
    """
    total_posts, total_comments = get_system_stats()
    device_label = "CUDA GPU" if torch.cuda.is_available() else "CPU Multi-Core"

    markup = f"""
    <div class="top-brand-dock">
        <div class="nav-brand-section">
            <div class="nav-brand-icon">
                <span class="nav-brand-pulse"></span>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
                </svg>
            </div>
            <div>
                <div class="nav-brand-title">ViSoBERT Studio</div>
                <div class="nav-brand-sub">Neural Social Intelligence Observatory</div>
            </div>
        </div>
        <div class="nav-telemetry-cluster">
            <span class="nav-telemetry-chip">
                <span class="nav-dot-online"></span>
                <span>ONLINE</span>
            </span>
            <span class="nav-telemetry-chip">
                <span>Thiet bi:</span>
                <strong style="color: #38bdf8;">{device_label}</strong>
            </span>
            <span class="nav-telemetry-chip">
                <span>Mo hinh:</span>
                <strong style="color: #cbd5e1;">ViSoBERT v2</strong>
            </span>
            <span class="nav-telemetry-chip">
                <span>CSDL:</span>
                <strong style="color: #10b981;">{total_posts} bai | {total_comments} cmt</strong>
            </span>
        </div>
    </div>
    """
    render_html(markup)
