import torch
from frontend.components.style_loader import render_html

def render_lab_header(title: str, subtitle: str = ""):
    """
    Hiển thị Observatory HUD Header chuẩn phong cách trung tâm phân tích AI hiện đại.
    Tích hợp chip telemetry hiển thị trạng thái phần cứng, mô hình và độ trễ.
    """
    sub_markup = f"<p>{subtitle}</p>" if subtitle else ""
    device_label = "CUDA GPU" if torch.cuda.is_available() else "CPU"
    
    markup = f"""
    <div class="observatory-hud-header">
        <div class="hud-top-flex">
            <div class="hud-title-zone">
                <h1>{title}</h1>
                {sub_markup}
            </div>
            <div class="hud-telemetry-strip">
                <span class="hud-chip chip-status-online">
                    <span class="chip-dot"></span>
                    <span>ONLINE</span>
                </span>
                <span class="hud-chip">
                    <span>Mô hình:</span>
                    <strong style="color: #38bdf8;">ViSoBERT v2</strong>
                </span>
                <span class="hud-chip">
                    <span>Thiết bị:</span>
                    <strong style="color: #cbd5e1;">{device_label}</strong>
                </span>
                <span class="hud-chip">
                    <span>Hiệu chuẩn:</span>
                    <strong style="color: #cbd5e1;">T=1.3 Softmax</strong>
                </span>
            </div>
        </div>
    </div>
    """
    render_html(markup)
