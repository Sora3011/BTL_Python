import re
import pandas as pd
import streamlit as st
from backend.scrapers.youtube_scraper import crawl_youtube_comments
from backend.services.analysis_service import process_and_save_analysis
from backend.database.db import get_posts_summary
from frontend.components.cards import render_instant_summary
from frontend.components.style_loader import render_html

def extract_youtube_id(url: str):
    """Trích xuất Video ID 11 ký tự chuẩn từ URL YouTube bất kỳ."""
    match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11})', url)
    return match.group(1) if match else None

def render_youtube_view(tokenizer, model, device, inf_cfg):
    """
    Hiển thị Phân Hệ YouTube Studio:
    Bố cục Studio 2 cột bất đối xứng (Dual-Column Studio Workbench).
    Cột Trái: Trạm Khai Thác & Điều Khiển Độ Sâu Thu Thập YouTube.
    Cột Phải: Cơ Chế Kiến Trúc Scraper & Lịch Sử Bản Ghi Video.
    Hoàn toàn không dùng emoji AI rập khuôn.
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
                <span class="studio-panel-badge" style="color: #f87171; border-color: rgba(239, 68, 68, 0.35); background: rgba(239, 68, 68, 0.1);">YOUTUBE_CRAWLER</span>
            </div>
            """, unsafe_allow_html=True)

            if "yt_link_input_field" not in st.session_state:
                st.session_state["yt_link_input_field"] = "https://www.youtube.com/watch?v=tpOkBUamk6M"

            # Callback an toàn cập nhật URL video từ gợi ý pills
            def on_yt_preset_selected():
                chosen = st.session_state.get("yt_preset_pills")
                if chosen:
                    if "tpOkBUamk6M" in chosen:
                        st.session_state["yt_link_input_field"] = "https://www.youtube.com/watch?v=tpOkBUamk6M"
                    elif "etcYBI7L1D8" in chosen:
                        st.session_state["yt_link_input_field"] = "https://www.youtube.com/watch?v=etcYBI7L1D8"

            yt_input_url = st.text_input(
                "Đường dẫn video YouTube:",
                placeholder="https://www.youtube.com/watch?v=...",
                key="yt_link_input_field"
            )

            # Gợi ý video mẫu 1-click
            st.pills(
                "Video thử nghiệm nhanh:",
                options=["Review Công Nghệ (tpOkBUamk6M)", "Bản Tin Xã Hội (etcYBI7L1D8)"],
                selection_mode="single",
                key="yt_preset_pills",
                on_change=on_yt_preset_selected
            )

            # Dynamic Cinema Preview Card
            video_id = extract_youtube_id(yt_input_url.strip()) if yt_input_url.strip() else None
            if video_id:
                thumb_url = f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
                col_th, col_in = st.columns([1.5, 3])
                with col_th:
                    st.image(thumb_url, use_container_width=True)
                with col_in:
                    render_html(f"""
                    <div style="background: rgba(10, 14, 22, 0.6); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px; padding: 12px 14px;">
                        <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 4px;">
                            <span style="background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.35); color: #f87171; font-size: 10.5px; font-weight: 700; padding: 2px 7px; border-radius: 9999px;">ID: {video_id}</span>
                            <span style="font-size: 11px; color: #10b981;">● Sẵn sàng kết nối</span>
                        </div>
                        <div style="font-size: 11.5px; color: #cbd5e1; word-break: break-all; margin-top: 4px;">
                            <code>{yt_input_url.strip()[:48]}...</code>
                        </div>
                    </div>
                    """)

            st.write("")
            st.markdown("<div style='font-size:12.5px; font-weight:600; color:#cbd5e1; margin-bottom:4px;'>Độ sâu thu thập bình luận:</div>", unsafe_allow_html=True)
            depth_preset = st.segmented_control(
                "Độ sâu thu thập:",
                options=["20 ý kiến", "50 ý kiến", "100 ý kiến", "200 ý kiến"],
                default="50 ý kiến",
                label_visibility="collapsed",
                key="yt_depth_preset_ctrl"
            )

            depth_map = {"20 ý kiến": 20, "50 ý kiến": 50, "100 ý kiến": 100, "200 ý kiến": 200}
            max_yt_comments = depth_map.get(depth_preset, 50)

            st.write("")
            btn_run_youtube = st.button("Bắt đầu thu thập & phân tích", icon=":material/play_arrow:", use_container_width=True)

        if btn_run_youtube:
            if yt_input_url.strip():
                with st.spinner("Đang kết nối API YouTube, cào luồng bình luận và tính toán suy luận ViSoBERT v2..."):
                    try:
                        raw_comments = crawl_youtube_comments(yt_input_url.strip(), max_yt_comments)
                        
                        if raw_comments:
                            new_post_id, df_res_yt = process_and_save_analysis(
                                platform="YouTube",
                                post_source=yt_input_url.strip(),
                                comments_data=raw_comments,
                                tokenizer=tokenizer,
                                model=model,
                                device=device,
                                inf_cfg=inf_cfg
                            )

                            st.success(f"Hoàn tất thu thập và phân tích **{len(df_res_yt)}** ý kiến YouTube! Đã lưu CSDL với mã bản ghi **#{new_post_id}**.")
                            render_instant_summary(new_post_id, df_res_yt)
                        else:
                            st.warning("Không tìm thấy bình luận nào trên video này, hoặc video đã bị chủ sở hữu tắt tính năng bình luận.")
                    except Exception as err:
                        st.error(f"Xảy ra lỗi trong quá trình thu thập hoặc phân tích: {str(err)}")
            else:
                st.error("Vui lòng nhập đường dẫn video YouTube hợp lệ trước khi bắt đầu.")

    # ==========================================================================
    # CỘT PHẢI: KIẾN TRÚC SCRAPER & LỊCH SỬ VIDEO
    # ==========================================================================
    with col_yt_right:
        # Khối 1: Cơ Chế Khai Thác
        with st.container(border=True):
            st.markdown("""
            <div class="studio-panel-header">
                <span class="studio-panel-title">Cơ Chế Scraper YouTube Tự Động</span>
                <span class="studio-panel-badge">HEADLESS_STREAM</span>
            </div>
            <div style="font-size: 12px; color: #94a3b8; line-height: 1.6;">
                • <strong>Không phụ thuộc Quota:</strong> Thu thập qua stream luồng công khai, không bị chặn bởi hạn ngạch 10.000 units/ngày của Google Cloud API.<br>
                • <strong>Sắp xếp ưu tiên:</strong> Tự động bóc tách theo thứ tự phổ biến (Sort by Popularity) để bắt kịp các ý kiến đại diện nhất.<br>
                • <strong>Bảo vệ định danh:</strong> Tự động ẩn danh hóa và chuẩn hóa mã định danh tác giả.
            </div>
            """, unsafe_allow_html=True)

        # Khối 2: Bản Ghi YouTube Đã Lưu Trữ
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
                    v_id = extract_youtube_id(str(row['Nguồn dữ liệu'])) or "..."
                    render_html(f"""
                    <div class="history-mini-card">
                        <div>
                            <div class="history-card-title">#{row['post_id']} • Video [{v_id}]</div>
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
