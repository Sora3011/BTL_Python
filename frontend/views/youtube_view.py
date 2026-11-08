import html
import re
import time
from typing import Optional
import pandas as pd
import streamlit as st
from backend.scrapers.youtube_scraper import crawl_youtube_comments
from backend.services.analysis_service import process_and_save_analysis
from backend.database.db import get_posts_summary
from frontend.components.cards import render_instant_summary, render_terminal_console
from frontend.components.style_loader import render_html

def extract_youtube_id(url: str):
    """Trích xuất Video ID 11 ký tự chuẩn từ URL YouTube bất kỳ (phục vụ tải ảnh thumbnail)."""
    match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11})', url)
    return match.group(1) if match else None

def render_youtube_view(tokenizer, model, device, inf_cfg):
    """
    Hiển thị Phân Hệ YouTube Studio:
    Bố cục Studio 2 cột bất đối xứng (Dual-Column Studio Workbench).
    Cột Trái: Trạm Khai Thác & Điều Khiển Độ Sâu Thu Thập YouTube + Live Terminal Pipeline Console.
    Cột Phải: Lịch Sử Bản Ghi Video YouTube Đã Lưu Trữ.
    """
    col_yt_left, col_yt_right = st.columns([1.35, 1.0], gap="medium")

    # ==========================================================================
    # CỘT TRÁI: TRẠM KHAI THÁC & ĐIỀU KHIỂN CÀO DỮ LIỆU
    # ==========================================================================
    with col_yt_left:
        with st.container(border=True):
            st.markdown("""
            <div class="studio-panel-header">
                <span class="studio-panel-title">Trạm Khai Thác Bình Luận YouTube</span>
            </div>
            """, unsafe_allow_html=True)

            if "yt_video_title_field" not in st.session_state:
                st.session_state["yt_video_title_field"] = "Video YouTube"

            yt_video_title = st.text_input(
                "Đặt tên video lưu vào CSDL:",
                placeholder="Nhập tên gợi nhớ cho video...",
                key="yt_video_title_field"
            )

            if "yt_link_input_field" not in st.session_state:
                st.session_state["yt_link_input_field"] = "https://www.youtube.com/watch?v=tpOkBUamk6M"

            yt_input_url = st.text_input(
                "Đường dẫn video YouTube:",
                placeholder="https://www.youtube.com/watch?v=...",
                key="yt_link_input_field"
            )

            # Dynamic Cinema Preview Card (không hiển thị ID)
            video_id = extract_youtube_id(yt_input_url.strip()) if yt_input_url.strip() else None
            if video_id:
                thumb_url = f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
                col_th, col_in = st.columns([1.5, 3])
                with col_th:
                    st.image(thumb_url, use_container_width=True)
                with col_in:
                    display_title = html.escape(yt_video_title.strip() or "Video YouTube")
                    render_html(f"""
                    <div style="background: rgba(10, 14, 22, 0.6); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px; padding: 12px 14px;">
                        <div style="font-size: 13px; font-weight: 700; color: #f8fafc; margin-bottom: 4px;">
                            {display_title}
                        </div>
                        <div style="font-size: 11.5px; color: #cbd5e1; word-break: break-all;">
                            <code>{html.escape(yt_input_url.strip()[:52])}...</code>
                        </div>
                    </div>
                    """)

            st.write("")
            st.markdown("<div style='font-size:12.5px; font-weight:600; color:#cbd5e1; margin-bottom:4px;'>Độ sâu thu thập bình luận:</div>", unsafe_allow_html=True)
            crawl_mode = st.segmented_control(
                "Chế độ thu thập:",
                options=["Full Mode (Lấy hết bình luận)", "Config Mode (Tùy chỉnh số lượng)"],
                default="Config Mode (Tùy chỉnh số lượng)",
                label_visibility="collapsed",
                key="yt_crawl_mode_ctrl"
            )

            max_yt_comments: Optional[int] = None
            if crawl_mode and "Config Mode" in crawl_mode:
                max_yt_comments = int(
                    st.number_input(
                        "Số bình luận muốn lấy:",
                        min_value=1,
                        max_value=50000,
                        value=50,
                        step=10,
                        key="yt_custom_comment_limit"
                    )
                )

            st.write("")
            btn_run_youtube = st.button("Bắt đầu thu thập & phân tích", icon=":material/play_arrow:", use_container_width=True)

        if btn_run_youtube:
            if yt_input_url.strip():
                saved_video_name = yt_video_title.strip() or "Video YouTube"
                target_desc = "toàn bộ bình luận (Full Mode)" if max_yt_comments is None else f"tối đa {max_yt_comments} ý kiến"
                progress_slot = st.empty()
                try:
                    # Chặng 01: Kết nối HTTP Stream YouTube
                    render_terminal_console(
                        progress_slot,
                        theme="yt",
                        steps=[
                            ("active", f"01. Kết nối HTTP Stream YouTube ({saved_video_name})..."),
                            ("pending", f"02. Cào luồng bình luận ({target_desc})"),
                            ("pending", "03. Suy luận cảm xúc ViSoBERT v2"),
                            ("pending", "04. Ghi bản ghi vào cơ sở dữ liệu SQLite")
                        ],
                        pct=8.0
                    )

                    def on_yt_crawl_progress(curr: int, target: Optional[int]):
                        if target is not None:
                            crawl_pct = 10.0 + (curr / max(target, 1)) * 35.0
                            step2_msg = f"02. Đang cào bình luận từ luồng Stream: {curr}/{target} ý kiến..."
                        else:
                            crawl_pct = 10.0 + min(35.0, (curr / (curr + 80.0)) * 35.0)
                            step2_msg = f"02. Đang cào toàn bộ bình luận (Full Mode): đã lấy {curr} ý kiến..."

                        render_terminal_console(
                            progress_slot,
                            theme="yt",
                            steps=[
                                ("done", f"01. Kết nối HTTP Stream YouTube ({saved_video_name})"),
                                ("active", step2_msg),
                                ("pending", "03. Suy luận cảm xúc ViSoBERT v2"),
                                ("pending", "04. Ghi bản ghi vào cơ sở dữ liệu SQLite")
                            ],
                            pct=crawl_pct
                        )

                    raw_comments = crawl_youtube_comments(
                        yt_input_url.strip(),
                        max_yt_comments,
                        on_progress=on_yt_crawl_progress
                    )

                    if raw_comments:
                        total_crawled = len(raw_comments)
                        step2_done_msg = (
                            f"02. Cào thành công toàn bộ {total_crawled} bình luận (Full Mode)"
                            if max_yt_comments is None
                            else f"02. Cào thành công {total_crawled}/{max_yt_comments} bình luận phổ biến nhất"
                        )

                        def on_yt_infer_progress(curr: int, total: int):
                            inf_pct = 45.0 + (curr / max(total, 1)) * 47.0
                            pct_label = int(round((curr / max(total, 1)) * 100))
                            render_terminal_console(
                                progress_slot,
                                theme="yt",
                                steps=[
                                    ("done", f"01. Kết nối HTTP Stream YouTube ({saved_video_name})"),
                                    ("done", step2_done_msg),
                                    ("active", f"03. Đang chạy ViSoBERT v2: {curr}/{total} bình luận ({pct_label}%)..."),
                                    ("pending", "04. Ghi bản ghi vào cơ sở dữ liệu SQLite")
                                ],
                                pct=inf_pct
                            )

                        def on_yt_before_save():
                            render_terminal_console(
                                progress_slot,
                                theme="yt",
                                steps=[
                                    ("done", f"01. Kết nối HTTP Stream YouTube ({saved_video_name})"),
                                    ("done", step2_done_msg),
                                    ("done", f"03. Hoàn tất suy luận ViSoBERT v2 ({total_crawled}/{total_crawled} bình luận)"),
                                    ("active", "04. Đang ghi bản ghi vào cơ sở dữ liệu SQLite...")
                                ],
                                pct=96.0
                            )

                        new_post_id, df_res_yt = process_and_save_analysis(
                            platform="YouTube",
                            post_source=saved_video_name,
                            comments_data=raw_comments,
                            tokenizer=tokenizer,
                            model=model,
                            device=device,
                            inf_cfg=inf_cfg,
                            on_inference_progress=on_yt_infer_progress,
                            on_before_save=on_yt_before_save
                        )

                        # Hoàn tất 100% và tự động thu gọn thanh tiến trình
                        render_terminal_console(
                            progress_slot,
                            theme="yt",
                            steps=[
                                ("done", f"01. Kết nối HTTP Stream YouTube ({saved_video_name})"),
                                ("done", step2_done_msg),
                                ("done", f"03. Hoàn tất suy luận ViSoBERT v2 ({total_crawled}/{total_crawled} bình luận)"),
                                ("done", f"04. Đã lưu bản ghi #{new_post_id} vào cơ sở dữ liệu SQLite")
                            ],
                            pct=100.0
                        )
                        time.sleep(0.35)
                        progress_slot.empty()

                        st.success(f"Hoàn tất thu thập và phân tích **{len(df_res_yt)}** ý kiến YouTube! Đã lưu CSDL với mã bản ghi **#{new_post_id}**.")
                        render_instant_summary(new_post_id, df_res_yt)
                    else:
                        progress_slot.empty()
                        st.warning("Không tìm thấy bình luận nào trên video này, hoặc video đã bị chủ sở hữu tắt tính năng bình luận.")
                except Exception as err:
                    progress_slot.empty()
                    st.error(f"Xảy ra lỗi trong quá trình thu thập hoặc phân tích: {str(err)}")
            else:
                st.error("Vui lòng nhập đường dẫn video YouTube hợp lệ trước khi bắt đầu.")

    # ==========================================================================
    # CỘT PHẢI: LỊCH SỬ VIDEO YOUTUBE ĐÃ PHÂN TÍCH (HIỂN THỊ TÊN ĐÃ ĐẶT, BỎ ID)
    # ==========================================================================
    with col_yt_right:
        with st.container(border=True):
            st.markdown("""
            <div class="studio-panel-header">
                <span class="studio-panel-title">Video YouTube Đã Phân Tích</span>
                <span class="studio-panel-badge">SQLITE_STORE</span>
            </div>
            """, unsafe_allow_html=True)

            df_summary = get_posts_summary()
            yt_history = df_summary[df_summary["Nền tảng"] == "YouTube"] if not df_summary.empty else pd.DataFrame()

            if not yt_history.empty:
                for _, row in yt_history.head(4).iterrows():
                    raw_src = str(row['Nguồn dữ liệu']).strip()
                    display_name = "Video YouTube" if raw_src.startswith("http") else raw_src
                    render_html(f"""
                    <div class="history-mini-card">
                        <div>
                            <div class="history-card-title">#{row['post_id']} • {html.escape(display_name)}</div>
                            <div class="history-card-sub">{row['Thời điểm phân tích']}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-family: 'JetBrains Mono', monospace; font-size: 13.5px; font-weight: 700; color: #10b981;">
                                {row['Điểm TB']:.1f}<span style="font-size: 10px; color: #64748b;">/100</span>
                            </div>
                            <div style="font-size: 10.5px; color: #94a3b8;">{row['Tổng số ý kiến']} bình luận</div>
                        </div>
                    </div>
                    """)
            else:
                st.caption("Chưa có video YouTube nào được lưu trữ.")
