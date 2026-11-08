import html
import streamlit as st
from frontend.components.style_loader import render_html

def clean_author(name, max_len: int = 24) -> str:
    s = str(name).strip()
    return s[:max_len] + "..." if len(s) > max_len else s

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
    marker_pos = min(max(mean_score, 0), 100)
    
    # Tính Vector kéo cảm xúc (Polarity Momentum)
    net_sentiment = pos_pct - neg_pct
    momentum_label = f"+{net_sentiment:.1f}% Tích cực" if net_sentiment >= 0 else f"{net_sentiment:.1f}% Tiêu cực"
    momentum_color = "#10b981" if net_sentiment >= 0 else "#f43f5e"

    cockpit_markup = f"""
    <div class="cockpit-matrix">
        <!-- Cánh Trái: Thước đo Điểm Cảm xúc Tổng hợp & Phổ Phân cực -->
        <div class="core-gauge-cockpit">
            <div>
                <div class="cockpit-head-row">
                    <span class="head-eyebrow">Chỉ Số Tâm Lý Cộng Đồng</span>
                    <span class="head-pill-count">N = {total_cmt} ý kiến</span>
                </div>
                <div class="gauge-hero-body">
                    <div class="score-num-wrapper">
                        <span class="score-display-val" style="color: {verdict_color};">{mean_score:.1f}</span>
                        <span class="score-display-max">/ 100</span>
                    </div>
                    <div class="score-verdict-heading" style="color: {verdict_color};">{verdict_title}</div>
                    <div class="score-verdict-summary">{verdict_desc}</div>
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
                <div class="cockpit-foot-meta">
                    <span>Độ bất định (Entropy): <strong style="color: #cbd5e1;" class="mono-data">{mean_entropy:.3f}</strong></span>
                    <span>Độ lệch thuần: <strong style="color: {momentum_color};" class="mono-data">{momentum_label}</strong></span>
                    <span>Kênh dữ liệu: <strong style="color: #38bdf8;">{platform}</strong></span>
                </div>
            </div>
        </div>

        <!-- Cánh Phải: Danh Sách 4 Phân Lớp Cảm Xúc Xã Hội -->
        <div class="horizon-sentiment-deck">
            <div class="cockpit-head-row">
                <span class="head-eyebrow">Cơ Cấu 4 Phân Lớp Ý Kiến</span>
                <span style="font-size: 11px; font-family: 'JetBrains Mono', monospace; color: #94a3b8;">ViSoBERT v2 Classification</span>
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

def render_spotlight(pos_top, neg_top, mix_top):
    """Hiển thị Lăng kính tiếng nói đại diện (Audience Voice Spotlight) 3 thái cực đặc trưng."""
    st.markdown("""
    <div style="font-size:15px; font-weight:700; color:#f8fafc; margin-top:22px; margin-bottom:4px; letter-spacing:-0.01em;">
        Lăng Kính Tiếng Nói Đại Diện (Audience Voice Spotlight)
    </div>
    <div style="font-size:12.5px; color:#94a3b8; margin-bottom:14px;">
        Trích xuất 3 thái cực ý kiến tiêu biểu nhất từ tập dữ liệu nhằm phục vụ đối soát định tính và kiểm chứng mô hình:
    </div>
    """, unsafe_allow_html=True)

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
                <span class="mono-data" style="color: #34d399;">Xác suất +: {pos_top['pos_score']:.1f}%</span>
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
                <span class="mono-data" style="color: #fb7185;">Xác suất -: {neg_top['neg_score']:.1f}%</span>
            </div>
        </div>

        <!-- Ý kiến đa chiều lưỡng lự -->
        <div class="voice-transcript-card voice-card-mix">
            <div>
                <div class="voice-card-head">
                    <span class="voice-persona-badge" style="color: #c084fc;">● Ý Kiến Đa Chiều / Phân Vân</span>
                    <span class="voice-score-pill" style="background: rgba(168,85,247,0.15); color: #c084fc;">Entropy {mix_top['entropy']:.2f}</span>
                </div>
                <div class="voice-quote-text">"{html.escape(str(mix_top['raw_text']))}"</div>
            </div>
            <div class="voice-card-foot">
                <span>Tác giả: <strong style="color:#ffffff;">{html.escape(clean_author(mix_top['author']))}</strong></span>
                <span style="color: #c084fc; font-weight: 600;">Vừa khen vừa chê</span>
            </div>
        </div>
    </div>
    """
    render_html(spotlight_markup)

def render_instant_summary(new_post_id: int, df_res):
    """Hiển thị khối tóm tắt kết quả phân tích tức thì sau khi cào hoặc nhập dữ liệu mới."""
    total_items = len(df_res)
    mean_score = df_res['score_100'].mean()
    pos_count = sum(df_res['sentiment_label'] == 'Tích cực')
    neg_count = sum(df_res['sentiment_label'] == 'Tiêu cực')
    
    markup = f"""
    <div class="instant-receipt-wrap">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="font-size: 15px; font-weight: 700; color: #ffffff;">
                Biên Bản Phân Tích Dữ Liệu Tức Thì
            </div>
            <span class="hud-chip" style="background: rgba(14, 165, 233, 0.15); border-color: rgba(56, 189, 248, 0.4); color: #38bdf8;">
                BẢN GHI #{new_post_id}
            </span>
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
        df_res[["author", "raw_text", "score_100", "sentiment_label"]].head(6),
        column_config={
            "author": st.column_config.TextColumn("Người đăng", width="medium"),
            "raw_text": st.column_config.TextColumn("Nội dung bình luận", width="large"),
            "score_100": st.column_config.ProgressColumn("Điểm (0-100)", min_value=0, max_value=100, format="%.0f"),
            "sentiment_label": st.column_config.TextColumn("Nhãn phân loại", width="small")
        },
        hide_index=True,
        use_container_width=True
    )
