import html
from typing import Any, Dict, Optional, Tuple
import streamlit as st
from backend.database.db import get_posts_summary, get_post_comments
from backend.models.sentiment_model import COLOR_PALETTE, get_confidence_threshold
from frontend.components.cards import (
    SPOTLIGHT_ENTROPY_THRESHOLD,
    annotate_confidence_flags,
    classify_entropy_level,
    render_cockpit,
    render_spotlight,
    safe_float,
)
from frontend.components.charts import render_sentiment_donut, render_score_histogram

_SCORE_VERDICTS = (
    (
        75.0,
        "Đồng Thuận Tán Thưởng Rất Cao",
        "Đa số ý kiến cộng đồng bày tỏ sự ủng hộ, hài lòng và đánh giá tích cực với các chi tiết được đề cập.",
        "#10b981",
    ),
    (
        60.0,
        "Xu Hướng Đánh Giá Khả Quan",
        "Tỷ lệ tích cực chiếm ưu thế rõ nét; ý kiến tiêu cực chỉ xuất hiện rải rác ở một số khía cạnh nhỏ.",
        "#34d399",
    ),
    (
        45.0,
        "Cân Bằng & Đa Chiều",
        "Ý kiến ghi nhận sự phân hóa hoặc tập trung ở vùng trung dung; không có xu hướng cực đoan rõ rệt.",
        "#cbd5e1",
    ),
    (
        30.0,
        "Nhiều Ý Kiến Bất Bình & Phê Bình",
        "Cộng đồng ghi nhận nhiều phản ánh tiêu cực, tranh cãi hoặc bất đồng quan điểm đáng chú ý.",
        "#fb7185",
    ),
    (
        float("-inf"),
        "Phản Ứng Tiêu Cực Gay Gắt",
        "Tỷ lệ bình luận chỉ trích chiếm đa số áp đảo; mức độ hài lòng ở mức rất thấp.",
        "#f43f5e",
    ),
)


def evaluate_sentiment_verdict(mean_score: float, mean_entropy: float) -> Tuple[str, str, str]:
    """Đánh giá 5 cấp độ rủi ro từ Mean Score kết hợp mức độ bất định Entropy TB H̄(P)."""
    score_val = safe_float(mean_score, 50.0)
    _, _, _, _, entropy_note = classify_entropy_level(mean_entropy)
    for min_score, title, base_desc, color in _SCORE_VERDICTS:
        if score_val >= min_score:
            return title, f"{base_desc} {entropy_note}", color
    _, title, base_desc, color = _SCORE_VERDICTS[-1]
    return title, f"{base_desc} {entropy_note}", color


def render_overview_view(inf_cfg: Optional[Dict[str, Any]] = None):
    """Hiển thị Phân Hệ Tổng Quan: Bảng Điều Khiển Cảm Xúc & Phân Tích Dữ Liệu."""
    conf_threshold = get_confidence_threshold(inf_cfg)
    df_summary = get_posts_summary()

    if df_summary.empty:
        st.info("Chưa ghi nhận dữ liệu phân tích nào trong cơ sở dữ liệu SQLite. Vui lòng chuyển sang phân hệ 'YouTube' hoặc 'Facebook' ở thanh điều hướng phía trên để bắt đầu nạp dữ liệu.")
        return

    with st.container(border=True):
        c_pick, c_btn, c_dl = st.columns([3.5, 1.2, 1.3], vertical_alignment="center")
        with c_pick:
            post_opts = df_summary["post_id"].tolist()
            post_labels = {}
            for _, row in df_summary.iterrows():
                src_str = str(row["Nguồn dữ liệu"]).strip()
                clean_title = "Video YouTube" if src_str.startswith("http") else src_str[:45]
                post_labels[row["post_id"]] = f"Bản ghi #{row['post_id']} • [{row['Nền tảng']}] {clean_title} ({row['Tổng số ý kiến']} bình luận)"
            selected_post_id = st.selectbox(
                "Tập dữ liệu đang kiểm chứng:",
                options=post_opts,
                format_func=lambda pid: post_labels.get(pid, f"Bản ghi #{pid}"),
                label_visibility="collapsed"
            )
        with c_btn:
            if st.button("Làm mới", icon=":material/refresh:", use_container_width=True):
                st.rerun()

        df_detail = get_post_comments(int(selected_post_id))
        post_meta = df_summary[df_summary["post_id"] == int(selected_post_id)].iloc[0]

        with c_dl:
            csv_bytes = df_detail.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="Xuất file CSV",
                icon=":material/download:",
                data=csv_bytes,
                file_name=f"sentiment_post_{selected_post_id}.csv",
                mime="text/csv",
                use_container_width=True
            )

    if not df_detail.empty:
        total_cmt = len(df_detail)
        mean_score = safe_float(df_detail["score_100"].mean(), 50.0)
        mean_entropy = safe_float(df_detail["entropy"].mean(), 0.0)

        pos_count = int(sum(df_detail["sentiment_label"] == "Tích cực"))
        neu_count = int(sum(df_detail["sentiment_label"] == "Trung tính"))
        mix_count = int(sum(df_detail["sentiment_label"] == "Hỗn hợp"))
        neg_count = int(sum(df_detail["sentiment_label"] == "Tiêu cực"))

        pos_pct = (pos_count / total_cmt * 100) if total_cmt else 0
        neu_pct = (neu_count / total_cmt * 100) if total_cmt else 0
        mix_pct = (mix_count / total_cmt * 100) if total_cmt else 0
        neg_pct = (neg_count / total_cmt * 100) if total_cmt else 0

        verdict_title, verdict_desc, verdict_color = evaluate_sentiment_verdict(mean_score, mean_entropy)
        df_flagged, uncertain_count = annotate_confidence_flags(df_detail, conf_threshold)

        render_cockpit(
            total_cmt=total_cmt,
            mean_score=mean_score,
            mean_entropy=mean_entropy,
            pos_count=pos_count,
            neu_count=neu_count,
            mix_count=mix_count,
            neg_count=neg_count,
            pos_pct=pos_pct,
            neu_pct=neu_pct,
            mix_pct=mix_pct,
            neg_pct=neg_pct,
            verdict_title=verdict_title,
            verdict_desc=verdict_desc,
            verdict_color=verdict_color,
            platform=post_meta["Nền tảng"]
        )

        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            render_sentiment_donut(df_detail, total_cmt, COLOR_PALETTE)
        with col_chart2:
            render_score_histogram(df_detail)

        pos_top = df_detail.sort_values(by="score_100", ascending=False).iloc[0]
        neg_top = df_detail.sort_values(by="score_100", ascending=True).iloc[0]
        mix_candidates = df_detail[df_detail["entropy"] > SPOTLIGHT_ENTROPY_THRESHOLD]
        mix_top = mix_candidates.sort_values(by="entropy", ascending=False).iloc[0] if not mix_candidates.empty else None
        render_spotlight(pos_top, neg_top, mix_top)

        with st.container(border=True):
            confidence_badge = (
                f"⚠ {uncertain_count}/{total_cmt} câu cần kiểm tra (< {conf_threshold:.2f})"
                if uncertain_count > 0
                else f"100% đạt độ tin cậy ≥ {conf_threshold:.2f}"
            )
            st.markdown(f"""
            <div class="studio-panel-header">
                <span class="studio-panel-title">Duyệt & Tra Cứu Toàn Bộ Ý Kiến Đã Phân Tích</span>
                <span class="studio-panel-badge">{html.escape(confidence_badge)}</span>
            </div>
            """, unsafe_allow_html=True)

            col_flt_label, col_flt_kw, col_flt_range = st.columns([1.5, 2.2, 1.8])
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
            with col_flt_range:
                flt_score_range = st.slider(
                    "Khoảng điểm (0 - 100):",
                    min_value=0,
                    max_value=100,
                    value=(0, 100),
                    step=1,
                    key="view_filter_score_slider"
                )

            only_uncertain = st.checkbox(
                f"Chỉ xem câu không chắc chắn (độ tin cậy < {conf_threshold:.2f}) — {uncertain_count} câu",
                key="view_filter_uncertain"
            )

            df_show = df_flagged.copy()
            if flt_label != "Tất cả phân lớp":
                df_show = df_show[df_show["sentiment_label"] == flt_label]
            if flt_kw.strip():
                df_show = df_show[df_show["raw_text"].str.contains(flt_kw.strip(), case=False, na=False, regex=False)]
            df_show = df_show[(df_show["score_100"] >= flt_score_range[0]) & (df_show["score_100"] <= flt_score_range[1])]
            if only_uncertain:
                df_show = df_show[df_show["is_uncertain"]]

            st.dataframe(
                df_show[[
                    "author",
                    "raw_text",
                    "score_100",
                    "confidence_pct",
                    "confidence_flag",
                    "pos_score",
                    "neu_score",
                    "neg_score",
                    "entropy",
                    "sentiment_label",
                ]],
                column_config={
                    "author": st.column_config.TextColumn("Người đăng", width="medium"),
                    "raw_text": st.column_config.TextColumn("Nội dung bình luận", width="large"),
                    "score_100": st.column_config.ProgressColumn("Điểm (0-100)", min_value=0, max_value=100, format="%.1f"),
                    "confidence_pct": st.column_config.NumberColumn("Độ tin cậy", format="%.2f%%"),
                    "confidence_flag": st.column_config.TextColumn("Cờ kiểm tra", width="medium"),
                    "pos_score": st.column_config.NumberColumn("% Tích cực", format="%.1f%%"),
                    "neu_score": st.column_config.NumberColumn("% Trung tính", format="%.1f%%"),
                    "neg_score": st.column_config.NumberColumn("% Tiêu cực", format="%.1f%%"),
                    "entropy": st.column_config.NumberColumn("Entropy", format="%.3f"),
                    "sentiment_label": st.column_config.TextColumn("Phân loại", width="small")
                },
                hide_index=True,
                use_container_width=True
            )
