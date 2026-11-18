import pandas as pd
import plotly.express as px
import streamlit as st

def render_sentiment_donut(df_detail: pd.DataFrame, total_cmt: int, color_palette: dict):
    with st.container(border=True):
        st.markdown("<div style='font-size:14px; font-weight:700; color:#f8fafc; margin-bottom:8px;'>Cơ Cấu Tỷ Lệ Cảm Xúc Toàn Diện</div>", unsafe_allow_html=True)

        fig_pie = px.pie(
            df_detail,
            names="sentiment_label",
            hole=0.64,
            color="sentiment_label",
            color_discrete_map=color_palette
        )
        fig_pie.update_traces(
            textposition='inside',
            textinfo='percent',
            marker=dict(line=dict(color='#0d121c', width=2.5)),
            hovertemplate="<b>%{label}</b><br>Số ý kiến: %{value}<br>Tỷ trọng: %{percent:.1%}<extra></extra>"
        )
        
        dominant_label = df_detail["sentiment_label"].value_counts().index[0]
        dominant_pct = (df_detail["sentiment_label"].value_counts().iloc[0] / total_cmt) * 100

        fig_pie.update_layout(
            margin=dict(t=12, b=12, l=12, r=12),
            height=280,
            showlegend=True,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Plus Jakarta Sans, sans-serif', color='#cbd5e1', size=12),
            legend=dict(orientation="h", yanchor="bottom", y=-0.22, xanchor="center", x=0.5),
            annotations=[dict(
                text=f'<span style="font-size:11px; color:#94a3b8; font-weight:500;">Ưu thế</span><br><b style="font-size:16px; color:#ffffff;">{dominant_label}</b><br><span style="font-size:12.5px; color:#38bdf8; font-family:JetBrains Mono, monospace; font-weight:700;">{dominant_pct:.1f}%</span>',
                x=0.5, y=0.5,
                showarrow=False
            )]
        )
        st.plotly_chart(fig_pie, use_container_width=True)

def render_score_histogram(df_detail: pd.DataFrame):
    with st.container(border=True):
        st.markdown("<div style='font-size:14px; font-weight:700; color:#f8fafc; margin-bottom:8px;'>Phân Bổ Mật Độ Điểm Cảm Xúc (0 - 100)</div>", unsafe_allow_html=True)

        bins = [0, 20, 40, 60, 80, 100]
        bin_labels = ["0-20 Rất xấu", "20-40 Tiêu cực", "40-60 Trung lập", "60-80 Tích cực", "80-100 Xuất sắc"]
        df_copy = df_detail.copy()
        df_copy["score_bin"] = pd.cut(df_copy["score_100"], bins=bins, labels=bin_labels, include_lowest=True)
        bin_counts = df_copy["score_bin"].value_counts().reindex(bin_labels, fill_value=0).reset_index()
        bin_counts.columns = ["Khoảng điểm", "Số lượng"]

        fig_hist = px.bar(
            bin_counts,
            x="Khoảng điểm",
            y="Số lượng",
            text="Số lượng",
            color="Khoảng điểm",
            color_discrete_sequence=["#f43f5e", "#fb7185", "#94a3b8", "#34d399", "#10b981"]
        )
        fig_hist.update_traces(
            textposition='outside',
            textfont=dict(family='JetBrains Mono, monospace', color='#cbd5e1', size=11),
            marker=dict(line=dict(color='#0d121c', width=1.5)),
            hovertemplate="Khoảng: <b>%{x}</b><br>Số bình luận: <b>%{y}</b><extra></extra>"
        )
        fig_hist.update_layout(
            margin=dict(t=16, b=10, l=10, r=10),
            height=280,
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Plus Jakarta Sans, sans-serif', color='#cbd5e1', size=11),
            xaxis_title="",
            yaxis_title="Số bình luận",
            yaxis=dict(gridcolor="rgba(255,255,255,0.06)")
        )
        st.plotly_chart(fig_hist, use_container_width=True)
