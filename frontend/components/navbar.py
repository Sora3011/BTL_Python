import base64
from frontend.components.style_loader import render_html

_ICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" '
    'fill="none" stroke="#38bdf8" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M2 10v3"/><path d="M6 6v11"/><path d="M10 3v18"/><path d="M14 8v7"/>'
    '<path d="M18 5v13"/><path d="M22 10v3"/></svg>'
)
_ICON_B64 = base64.b64encode(_ICON_SVG.encode("utf-8")).decode("ascii")

def render_top_header():
    markup = f"""
    <div class="top-brand-dock">
        <div class="nav-brand-section">
            <div class="nav-brand-icon">
                <span class="nav-brand-pulse"></span>
                <img src="data:image/svg+xml;base64,{_ICON_B64}" width="20" height="20" alt="Sounds of Social" style="display: block;" />
            </div>
            <div>
                <div class="nav-brand-title">Sounds of Social</div>
            </div>
        </div>
    </div>
    """
    render_html(markup)
