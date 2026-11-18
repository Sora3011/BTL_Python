import html
import math
from typing import List, Optional, Tuple
import pandas as pd
import streamlit as st
from backend.models.sentiment_model import DEFAULT_CONFIDENCE_THRESHOLD
from frontend.components.style_loader import render_html

SPOTLIGHT_ENTROPY_THRESHOLD = 0.75

_ENTROPY_RISK_LEVELS = (
    (
        0.65,
        "Phân hóa / Bất định cao",
        "#fbbf24",
        "rgba(251, 191, 36, 0.35)",
        "rgba(251, 191, 36, 0.12)",
        "Entropy TB H̄ = {h:.3f} (≥ 0.65): mức độ lưỡng lự và phân tán ý kiến cao, cần kiểm tra thêm các bình luận Hỗn hợp hoặc có độ tin cậy thấp."
    ),
    (
        0.40,
        "Phân hóa trung bình",
        "#c084fc",
        "rgba(192, 132, 252, 0.30)",
        "rgba(192, 132, 252, 0.10)",
        "Entropy TB H̄ = {h:.3f} (0.40–0.65): tồn tại một phần ý kiến đan xen hai chiều."
    ),
    (
        float("-inf"),
        "Đồng thuận rõ nét",
        "#34d399",
        "rgba(52, 211, 153, 0.30)",
        "rgba(52, 211, 153, 0.10)",
        "Entropy TB H̄ = {h:.3f} (< 0.40): cộng đồng thể hiện quan điểm nhất quán, độ bất định thấp."
    ),
)


def safe_float(value, default: float = 0.0) -> float:
    """Chuyển đổi giá trị số an toàn, tránh None/NaN/Inf làm hỏng giao diện."""
    try:
        parsed = float(value)
        return default if (math.isnan(parsed) or math.isinf(parsed)) else parsed
    except (TypeError, ValueError):
        return default


def classify_entropy_level(mean_entropy: float) -> Tuple[str, str, str, str, str]:
    """Phân loại mức độ bất định/phân tán từ Entropy trung bình H̄(P)."""
    h_val = safe_float(mean_entropy, 0.0)
    for min_h, label, color, border_color, bg_color, template in _ENTROPY_RISK_LEVELS:
        if h_val >= min_h:
            return label, color, border_color, bg_color, template.format(h=h_val)
    _, label, color, border_color, bg_color, template = _ENTROPY_RISK_LEVELS[-1]
    return label, color, border_color, bg_color, template.format(h=h_val)


def annotate_confidence_flags(
    df: Optional[pd.DataFrame],
    conf_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
) -> Tuple[pd.DataFrame, int]:
    """Tính độ tin cậy cực đại max(P) (%) và gắn cờ các bình luận dưới ngưỡng conf_threshold."""
    threshold = safe_float(conf_threshold, DEFAULT_CONFIDENCE_THRESHOLD)
    if df is None or df.empty:
        empty_df = pd.DataFrame() if df is None else df.copy()
        empty_df["confidence_pct"] = pd.Series(dtype="float64")
        empty_df["is_uncertain"] = pd.Series(dtype="bool")
        empty_df["confidence_flag"] = pd.Series(dtype="object")
        return empty_df, 0

    df_out = df.copy()
    prob_matrix = df_out[["pos_score", "neu_score", "neg_score"]].apply(pd.to_numeric, errors="coerce").fillna(0.0)
    confidence_pct = prob_matrix.max(axis=1).astype(float)
    is_uncertain = (confidence_pct / 100.0) < (threshold - 1e-12)

    df_out["confidence_pct"] = confidence_pct.round(2)
    df_out["is_uncertain"] = is_uncertain
    uncertain_label = f"⚠ Cần kiểm tra (< {threshold:.2f})"
    df_out["confidence_flag"] = is_uncertain.map(lambda flag: uncertain_label if flag else "Tin cậy")
    return df_out, int(is_uncertain.sum())

def clean_author(name, max_len: int = 24) -> str:
    s = str(name).strip()
    return s[:max_len] + "..." if len(s) > max_len else s

def render_terminal_console(placeholder, theme: str, steps: List[Tuple[str, str]], pct: float):
    """
    Hiển thị Thanh tiến trình Phương Án 3: Live Terminal Pipeline Console.
    - theme: 'yt' hoặc 'fb'
    - steps: Danh sách tuple (state, text) với state in {'done', 'active', 'pending'}
    - pct: Tiến độ từ 0 đến 100
    """
    pct_clamped = min(max(float(pct), 0.0), 100.0)
    theme_cls = "yt-theme" if theme == "yt" else "fb-theme"
    fill_cls = "terminal-bar-fill-yt" if theme == "yt" else "terminal-bar-fill-fb"
    active_cls = "active-yt" if theme == "yt" else "active-fb"

    lines_html = []
    for state, text in steps:
        if state == "done":
            prefix = "[✓]"
            cls = "done"
        elif state == "active":
            prefix = "[●]"
            cls = active_cls
        else:
            prefix = "[ ]"
            cls = "pending"
        lines_html.append(f'<div class="term-line {cls}"><span>{prefix}</span><span>{html.escape(text)}</span></div>')

    joined_lines = "".join(lines_html)
    markup = f"""
    <div class="terminal-pipeline-wrap {theme_cls}">
        <div class="terminal-console-box">
            {joined_lines}
        </div>
        <div class="terminal-bar-track">
            <div class="{fill_cls}" style="width: {pct_clamped:.1f}%;"></div>
        </div>
    </div>
    """
    with placeholder.container():
        render_html(markup)

def render_cockpit(
    total_cmt: int,
    mean_score: float,
    mean_entropy: float,
    pos_count: int,
    neu_count: int,
    mix_count: int,
    neg_count: int,
    pos_pct: float,
    neu_pct: float,
    mix_pct: float,
    neg_pct: float,
    verdict_title: str,
    verdict_desc: str,
    verdict_color: str,
    platform: str
):
    """Bố cục bất đối xứng: Asymmetric Sentiment Cockpit chuẩn phòng nghiên cứu hiện đại."""
    safe_score = safe_float(mean_score, 50.0)
    safe_entropy = safe_float(mean_entropy, 0.0)
    marker_pos = min(max(safe_score, 0.0), 100.0)
    entropy_label, ent_color, ent_border, ent_bg, _ = classify_entropy_level(safe_entropy)

    cockpit_markup = f"""
    <div class="cockpit-matrix">
        <!-- Cánh Trái: Thước đo Điểm Cảm xúc Tổng hợp & Phổ Phân cực -->
        <div class="core-gauge-cockpit">
            <div>
                <div class="cockpit-head-row">
                    <span class="head-eyebrow">Chỉ Số Tâm Lý Cộng Đồng</span>
                    <div style="display: flex; gap: 6px; align-items: center; flex-wrap: wrap;">
                        <span class="head-pill-count">N = {total_cmt} ý kiến</span>
                        <span class="head-pill-count" title="{html.escape(entropy_label)}" style="color: {ent_color}; border-color: {ent_border}; background: {ent_bg};">Entropy TB: {safe_entropy:.3f}</span>
                    </div>
                </div>
                <div class="gauge-hero-body">
                    <div class="score-num-wrapper">
                        <span class="score-display-val" style="color: {verdict_color};">{safe_score:.1f}</span>
                        <span class="score-display-max">/ 100</span>
                    </div>
                    <div class="score-verdict-heading" style="color: {verdict_color};">{html.escape(verdict_title)}</div>
                    <div class="score-verdict-summary">{html.escape(verdict_desc)}</div>
                </div>
            </div>
            <div>
                <div class="spectrum-chassis">
                    <div class="spectrum-rail">
                        <div class="spectrum-pin" style="left: {marker_pos}%;"></div>
                    </div>
                    <div class="spectrum-notches">
                        <span>0 Tiêu cực</span>
                        <span>50 Trung lập</span>
                        <span>100 Tích cực</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Cánh Phải: Danh Sách 4 Phân Lớp Cảm Xúc Xã Hội -->
        <div class="horizon-sentiment-deck">
            <div class="cockpit-head-row">
                <span class="head-eyebrow">Cơ Cấu 4 Phân Lớp Ý Kiến</span>
            </div>
            <div class="horizon-stack">
                <!-- Tích cực -->
                <div class="sentiment-slot">
                    <div class="slot-header-flex">
                        <div class="slot-identity">
                            <div class="slot-beacon" style="background: #10b981; box-shadow: 0 0 8px rgba(16, 185, 129, 0.4);"></div>
                            <span class="slot-label">Tích cực</span>
                        </div>
                        <div class="slot-metrics">
                            <span class="slot-count-str">{pos_count} ý kiến</span>
                            <span class="slot-pct-str" style="color: #34d399;">{pos_pct:.1f}%</span>
                        </div>
                    </div>
                    <div class="slot-meter-track">
                        <div class="slot-meter-fluid" style="width: {pos_pct}%; background: linear-gradient(90deg, #059669, #10b981);"></div>
                    </div>
                </div>
                <!-- Trung tính -->
                <div class="sentiment-slot">
                    <div class="slot-header-flex">
                        <div class="slot-identity">
                            <div class="slot-beacon" style="background: #94a3b8; box-shadow: 0 0 8px rgba(148, 163, 184, 0.3);"></div>
                            <span class="slot-label">Trung tính</span>
                        </div>
                        <div class="slot-metrics">
                            <span class="slot-count-str">{neu_count} ý kiến</span>
                            <span class="slot-pct-str" style="color: #cbd5e1;">{neu_pct:.1f}%</span>
                        </div>
                    </div>
                    <div class="slot-meter-track">
                        <div class="slot-meter-fluid" style="width: {neu_pct}%; background: linear-gradient(90deg, #475569, #94a3b8);"></div>
                    </div>
                </div>
                <!-- Hỗn hợp -->
                <div class="sentiment-slot">
                    <div class="slot-header-flex">
                        <div class="slot-identity">
                            <div class="slot-beacon" style="background: #a855f7; box-shadow: 0 0 8px rgba(168, 85, 247, 0.4);"></div>
                            <span class="slot-label">Hỗn hợp</span>
                        </div>
                        <div class="slot-metrics">
                            <span class="slot-count-str">{mix_count} ý kiến</span>
                            <span class="slot-pct-str" style="color: #c084fc;">{mix_pct:.1f}%</span>
                        </div>
                    </div>
                    <div class="slot-meter-track">
                        <div class="slot-meter-fluid" style="width: {mix_pct}%; background: linear-gradient(90deg, #7c3aed, #a855f7);"></div>
                    </div>
                </div>
                <!-- Tiêu cực -->
                <div class="sentiment-slot">
                    <div class="slot-header-flex">
                        <div class="slot-identity">
                            <div class="slot-beacon" style="background: #f43f5e; box-shadow: 0 0 8px rgba(244, 63, 94, 0.4);"></div>
                            <span class="slot-label">Tiêu cực</span>
                        </div>
                        <div class="slot-metrics">
                            <span class="slot-count-str">{neg_count} ý kiến</span>
                            <span class="slot-pct-str" style="color: #fb7185;">{neg_pct:.1f}%</span>
                        </div>
                    </div>
                    <div class="slot-meter-track">
                        <div class="slot-meter-fluid" style="width: {neg_pct}%; background: linear-gradient(90deg, #e11d48, #f43f5e);"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
    render_html(cockpit_markup)

def render_spotlight(pos_top, neg_top, mix_top=None):
    """Hiển thị Top comments 3 thái cực đặc trưng (ý kiến phân vân lọc theo H(P) > 0.75)."""
    st.markdown("""
    <div style="font-size:15px; font-weight:700; color:#f8fafc; margin-top:22px; margin-bottom:14px; letter-spacing:-0.01em;">
        Top comments:
    </div>
    """, unsafe_allow_html=True)

    if mix_top is not None:
        mix_card_html = f"""
        <div class="voice-transcript-card voice-card-mix">
            <div>
                <div class="voice-card-head">
                    <span class="voice-persona-badge" style="color: #c084fc;">● Ý Kiến Đa Chiều / Phân Vân</span>
                    <span class="voice-score-pill" style="background: rgba(168,85,247,0.15); color: #c084fc;">Entropy {safe_float(mix_top['entropy']):.3f}</span>
                </div>
                <div class="voice-quote-text">"{html.escape(str(mix_top['raw_text']))}"</div>
            </div>
            <div class="voice-card-foot">
                <span>Tác giả: <strong style="color:#ffffff;">{html.escape(clean_author(mix_top['author']))}</strong></span>
            </div>
        </div>
        """
    else:
        mix_card_html = f"""
        <div class="voice-transcript-card voice-card-mix">
            <div>
                <div class="voice-card-head">
                    <span class="voice-persona-badge" style="color: #c084fc;">● Ý Kiến Đa Chiều / Phân Vân</span>
                    <span class="voice-score-pill" style="background: rgba(148,163,184,0.14); color: #cbd5e1;">H(P) ≤ {SPOTLIGHT_ENTROPY_THRESHOLD:.2f}</span>
                </div>
                <div class="voice-quote-text" style="color: #94a3b8; font-style: italic;">Không ghi nhận ý kiến phân vân nổi bật (chưa có bình luận đạt Entropy &gt; {SPOTLIGHT_ENTROPY_THRESHOLD:.2f}).</div>
            </div>
            <div class="voice-card-foot">
                <span>Trạng thái: <strong style="color:#cbd5e1;">Cộng đồng đồng thuận / phân cực rõ nét</strong></span>
            </div>
        </div>
        """

    spotlight_markup = f"""
    <div class="audience-spotlight-matrix">
        <!-- Tán thưởng cao nhất -->
        <div class="voice-transcript-card voice-card-pos">
            <div>
                <div class="voice-card-head">
                    <span class="voice-persona-badge" style="color: #34d399;">● Tán Thưởng Cao Nhất</span>
                    <span class="voice-score-pill" style="background: rgba(16,185,129,0.15); color: #34d399;">{pos_top['score_100']:.1f}/100</span>
                </div>
                <div class="voice-quote-text">"{html.escape(str(pos_top['raw_text']))}"</div>
            </div>
            <div class="voice-card-foot">
                <span>Tác giả: <strong style="color:#ffffff;">{html.escape(clean_author(pos_top['author']))}</strong></span>
            </div>
        </div>

        <!-- Phê bình / Bất bình cần lưu tâm -->
        <div class="voice-transcript-card voice-card-neg">
            <div>
                <div class="voice-card-head">
                    <span class="voice-persona-badge" style="color: #fb7185;">● Ý Kiến Bất Bình Đáng Chú Ý</span>
                    <span class="voice-score-pill" style="background: rgba(244,63,94,0.15); color: #fb7185;">{neg_top['score_100']:.1f}/100</span>
                </div>
                <div class="voice-quote-text">"{html.escape(str(neg_top['raw_text']))}"</div>
            </div>
            <div class="voice-card-foot">
                <span>Tác giả: <strong style="color:#ffffff;">{html.escape(clean_author(neg_top['author']))}</strong></span>
            </div>
        </div>

        <!-- Ý kiến đa chiều lưỡng lự -->
        {mix_card_html}
    </div>
    """
    render_html(spotlight_markup)

def render_instant_summary(new_post_id: int, df_res, conf_threshold: Optional[float] = None):
    """Hiển thị khối tóm tắt kết quả phân tích tức thì sau khi cào hoặc nhập dữ liệu mới."""
    if df_res is None or df_res.empty:
        return

    threshold = safe_float(conf_threshold, DEFAULT_CONFIDENCE_THRESHOLD) if conf_threshold is not None else DEFAULT_CONFIDENCE_THRESHOLD
    df_flagged, uncertain_count = annotate_confidence_flags(df_res, threshold)

    total_items = len(df_flagged)
    mean_score = safe_float(df_flagged['score_100'].mean(), 50.0)
    pos_count = sum(df_flagged['sentiment_label'] == 'Tích cực')
    neg_count = sum(df_flagged['sentiment_label'] == 'Tiêu cực')

    if uncertain_count > 0:
        conf_pill_html = (
            f'<span class="studio-panel-badge" style="background: rgba(245, 158, 11, 0.14); '
            f'border-color: rgba(251, 191, 36, 0.45); color: #fbbf24;">'
            f'⚠ {uncertain_count}/{total_items} câu cần kiểm tra (&lt; {threshold:.2f})</span>'
        )
    else:
        conf_pill_html = (
            f'<span class="studio-panel-badge" style="background: rgba(16, 185, 129, 0.14); '
            f'border-color: rgba(52, 211, 153, 0.4); color: #34d399;">'
            f'✓ 100% đạt độ tin cậy ≥ {threshold:.2f}</span>'
        )

    markup = f"""
    <div class="instant-receipt-wrap">
        <div style="display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap;">
            <div style="font-size: 15px; font-weight: 700; color: #ffffff;">
                Biên Bản Phân Tích Dữ Liệu Tức Thì
            </div>
            <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
                {conf_pill_html}
                <span class="studio-panel-badge" style="background: rgba(14, 165, 233, 0.15); border-color: rgba(56, 189, 248, 0.4); color: #38bdf8;">
                    BẢN GHI #{new_post_id}
                </span>
            </div>
        </div>
        <div class="kpi-quad-row">
            <div class="kpi-mini-pod">
                <div class="kpi-mini-label">Tổng số ý kiến</div>
                <div class="kpi-mini-val">{total_items}</div>
            </div>
            <div class="kpi-mini-pod">
                <div class="kpi-mini-label">Điểm trung bình</div>
                <div class="kpi-mini-val" style="color: #38bdf8;">{mean_score:.1f} <span style="font-size: 12px; color: #64748b;">/ 100</span></div>
            </div>
            <div class="kpi-mini-pod">
                <div class="kpi-mini-label">Ý kiến tích cực</div>
                <div class="kpi-mini-val" style="color: #10b981;">{pos_count}</div>
            </div>
            <div class="kpi-mini-pod">
                <div class="kpi-mini-label">Ý kiến tiêu cực</div>
                <div class="kpi-mini-val" style="color: #f43f5e;">{neg_count}</div>
            </div>
        </div>
    </div>
    """
    render_html(markup)

    st.caption("Xem trước các ý kiến đầu tiên trong tập dữ liệu vừa nạp:")
    st.dataframe(
        df_flagged[["author", "raw_text", "score_100", "confidence_pct", "confidence_flag", "sentiment_label"]].head(6),
        column_config={
            "author": st.column_config.TextColumn("Người đăng", width="medium"),
            "raw_text": st.column_config.TextColumn("Nội dung bình luận", width="large"),
            "score_100": st.column_config.ProgressColumn("Điểm (0-100)", min_value=0, max_value=100, format="%.0f"),
            "confidence_pct": st.column_config.NumberColumn("Độ tin cậy", format="%.2f%%"),
            "confidence_flag": st.column_config.TextColumn("Cờ kiểm tra", width="medium"),
            "sentiment_label": st.column_config.TextColumn("Nhãn phân loại", width="small")
        },
        hide_index=True,
        use_container_width=True
    )
