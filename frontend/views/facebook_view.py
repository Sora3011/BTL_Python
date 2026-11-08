import pandas as pd
import streamlit as st
from backend.services.analysis_service import process_and_save_analysis
from backend.database.db import get_posts_summary
from frontend.components.cards import render_instant_summary
from frontend.components.style_loader import render_html

def render_facebook_view(tokenizer, model, device, inf_cfg):
    """
    Hiển thị Phân Hệ Facebook Studio:
    Bố cục Studio 2 cột bất đối xứng (Dual-Column Studio Workbench).
    Cột Trái: Trạm Nhập Liệu & Soạn Thảo Ý Kiến Đa Kênh.
    Cột Phải: Lăng Kính Giải Mã Tiền Xử Lý Ngôn Ngữ & Lịch Sử Bản Ghi.
    Hoàn toàn không dùng emoji AI rập khuôn.
    """
    col_input, col_intel = st.columns([1.35, 1.0], gap="medium")

    # ==========================================================================
    # CỘT TRÁI: TRẠM NHẬP LIỆU & SOẠN THẢO Ý KIẾN
    # ==========================================================================
    with col_input:
        with st.container(border=True):
            st.markdown("""
            <div class="studio-panel-header">
                <span class="studio-panel-title">Trạm Nhập Liệu Bình Luận Facebook</span>
                <span class="studio-panel-badge">INGESTION_STATION</span>
            </div>
            """, unsafe_allow_html=True)

            if "fb_post_title_field" not in st.session_state:
                st.session_state["fb_post_title_field"] = "Bài đăng Fanpage"

            # Callback an toàn cập nhật tên bài đăng từ gợi ý pills
            def on_fb_tag_selected():
                chosen = st.session_state.get("fb_preset_tag_pills")
                if chosen:
                    st.session_state["fb_post_title_field"] = chosen

            fb_src_title = st.text_input(
                "Định danh bài đăng / Fanpage:",
                placeholder="Nhập tên bài đăng hoặc chiến dịch...",
                key="fb_post_title_field"
            )

            # Gợi ý nhãn nguồn bài viết
            st.pills(
                "Gợi ý nhãn nhanh:",
                options=["Feedback Khách Hàng", "Chiến Dịch Truyền Thông", "Trải Nghiệm Dịch Vụ", "Review Sản Phẩm"],
                selection_mode="single",
                key="fb_preset_tag_pills",
                on_change=on_fb_tag_selected
            )

            st.write("")
            input_mode = st.segmented_control(
                "Phương thức cung cấp dữ liệu:",
                options=[":material/edit_note: Soạn thảo trực tiếp", ":material/upload_file: Tải lên tệp CSV"],
                default=":material/edit_note: Soạn thảo trực tiếp",
                label_visibility="collapsed"
            )

            parsed_fb_comments = []
            uploaded_csv_file = None
            fb_text_input = ""

            if "Soạn thảo" in input_mode:
                c_lbl, c_btn = st.columns([2.5, 1.2])
                with c_lbl:
                    st.caption("Dán các bình luận (mỗi bình luận đặt trên 1 dòng riêng biệt):")
                with c_btn:
                    if st.button("Nạp dữ liệu mẫu", icon=":material/playlist_add:", use_container_width=True):
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
                    height=180,
                    label_visibility="collapsed"
                )

                lines = [line.strip() for line in fb_text_input.split("\n") if line.strip()]
                parsed_fb_comments = [{"author": "Facebook User", "text": line} for line in lines]

                render_html(f"""
                <div style="display: flex; gap: 10px; margin-top: 6px; font-size: 11.5px; color: #94a3b8; font-family: 'JetBrains Mono', monospace;">
                    <span>Phát hiện: <strong style="color: #38bdf8;">{len(lines)} bình luận</strong></span>
                    <span>•</span>
                    <span>Chuẩn hóa: <strong style="color: #10b981;">Tự động làm sạch & map token</strong></span>
                </div>
                """)

            else:
                st.caption("Kéo thả hoặc chọn tệp tin CSV từ máy tính của bạn:")
                uploaded_csv_file = st.file_uploader("Tệp CSV:", type=["csv"], label_visibility="collapsed")
                if uploaded_csv_file is not None:
                    try:
                        df_upload = pd.read_csv(uploaded_csv_file)
                        first_col = df_upload.columns[0]
                        parsed_fb_comments = [
                            {"author": "Facebook User", "text": str(row)}
                            for row in df_upload[first_col].dropna()
                            if str(row).strip()
                        ]
                        st.caption(f"Đã phát hiện **{len(parsed_fb_comments)}** ý kiến trong cột `'{first_col}'`.")
                        st.dataframe(df_upload.head(3), hide_index=True, use_container_width=True)
                        uploaded_csv_file.seek(0)
                    except Exception as err:
                        st.error(f"Lỗi đọc file CSV: {str(err)}")

            st.write("")
            btn_run_fb = st.button("Khởi chạy suy luận ViSoBERT v2", icon=":material/play_arrow:", use_container_width=True)

        # Xử lý khi nhấn nút phân tích
        if btn_run_fb:
            if parsed_fb_comments:
                with st.spinner("Đang tiền xử lý ngôn ngữ xã hội, khử teencode và suy luận ViSoBERT v2..."):
                    try:
                        new_post_id_fb, df_res_fb = process_and_save_analysis(
                            platform="Facebook",
                            post_source=fb_src_title.strip(),
                            comments_data=parsed_fb_comments,
                            tokenizer=tokenizer,
                            model=model,
                            device=device,
                            inf_cfg=inf_cfg
                        )

                        st.success(f"Hoàn tất phân tích **{len(df_res_fb)}** ý kiến Facebook! Đã lưu CSDL với mã bản ghi **#{new_post_id_fb}**.")
                        render_instant_summary(new_post_id_fb, df_res_fb)
                    except Exception as err:
                        st.error(f"Lỗi trong quá trình phân tích: {str(err)}")
            else:
                st.warning("Vui lòng nhập ít nhất một bình luận văn bản hoặc tải lên tệp CSV hợp lệ.")

    # ==========================================================================
    # CỘT PHẢI: LĂNG KÍNH TIỀN XỬ LÝ & LỊCH SỬ DỮ LIỆU
    # ==========================================================================
    with col_intel:
        # Khối 1: Lăng kính Tiền Xử Lý Ngôn Ngữ Xã Hội
        with st.container(border=True):
            st.markdown("""
            <div class="studio-panel-header">
                <span class="studio-panel-title">Bộ Tiền Xử Lý Tiếng Việt (ViSoBERT)</span>
                <span class="studio-panel-badge" style="color: #34d399; border-color: rgba(16,185,129,0.3); background: rgba(16,185,129,0.1);">NLP_PREPROCESSOR</span>
            </div>
            <div style="font-size: 12.5px; color: #94a3b8; line-height: 1.5; margin-bottom: 12px;">
                Mô hình tự động bóc tách và chuyển dịch biểu cảm phi cấu trúc sang tokens ngữ nghĩa chuẩn hóa:
            </div>
            <div class="decoder-grid">
                <div class="decoder-item">
                    <span class="decoder-raw">😍 🥰</span>
                    <span class="decoder-arrow">➔</span>
                    <span class="decoder-token" style="color: #34d399;">yeu_thich</span>
                </div>
                <div class="decoder-item">
                    <span class="decoder-raw">=)) :))</span>
                    <span class="decoder-arrow">➔</span>
                    <span class="decoder-token" style="color: #38bdf8;">cuoi_vui</span>
                </div>
                <div class="decoder-item">
                    <span class="decoder-raw">😡 🤬</span>
                    <span class="decoder-arrow">➔</span>
                    <span class="decoder-token" style="color: #fb7185;">tuc_gian</span>
                </div>
                <div class="decoder-item">
                    <span class="decoder-raw">chán đời</span>
                    <span class="decoder-arrow">➔</span>
                    <span class="decoder-token" style="color: #f43f5e;">that_vong</span>
                </div>
                <div class="decoder-item">
                    <span class="decoder-raw">:3 ...</span>
                    <span class="decoder-arrow">➔</span>
                    <span class="decoder-token" style="color: #c084fc;">phan_van</span>
                </div>
                <div class="decoder-item">
                    <span class="decoder-raw">ngonnnn</span>
                    <span class="decoder-arrow">➔</span>
                    <span class="decoder-token" style="color: #cbd5e1;">ngon</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Khối 2: Lịch Sử Bài Đăng Facebook Trong SQLite
        with st.container(border=True):
            st.markdown("""
            <div class="studio-panel-header">
                <span class="studio-panel-title">Bản Ghi Facebook Đã Lưu Trữ</span>
                <span class="studio-panel-badge">SQLITE_STORE</span>
            </div>
            """, unsafe_allow_html=True)

            df_summary = get_posts_summary()
            fb_history = df_summary[df_summary["Nền tảng"] == "Facebook"] if not df_summary.empty else pd.DataFrame()

            if not fb_history.empty:
                for _, row in fb_history.head(4).iterrows():
                    render_html(f"""
                    <div class="history-mini-card">
                        <div>
                            <div class="history-card-title">#{row['post_id']} • {str(row['Nguồn dữ liệu'])}</div>
                            <div class="history-card-sub">{row['Thời điểm phân tích']}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-family: 'JetBrains Mono', monospace; font-size: 13.5px; font-weight: 700; color: #38bdf8;">
                                {row['Điểm TB']:.1f}<span style="font-size: 10px; color: #64748b;">/100</span>
                            </div>
                            <div style="font-size: 10.5px; color: #94a3b8;">{row['Tổng số ý kiến']} bình luận</div>
                        </div>
                    </div>
                    """)
            else:
                st.caption("Chưa có bản ghi Facebook nào được lưu trữ.")
