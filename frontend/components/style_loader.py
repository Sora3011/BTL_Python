import os
import re
from pathlib import Path
import streamlit as st

def render_html(raw_html: str):
    """
    Ket xuat khoi HTML tuy chinh vao giao dien Streamlit.
    Su dung st.html neu co san de bo qua trinh phan tich Markdown,
    fallback ve st.markdown neu can.
    """
    clean = re.sub(r'>\s+<', '><', raw_html)
    clean = re.sub(r'\n\s*', ' ', clean).strip()
    if hasattr(st, "html"):
        st.html(clean)
    else:
        st.markdown(clean, unsafe_allow_html=True)

def load_custom_css(css_file: str = "frontend/assets/style.css"):
    """
    Doc file CSS Design System va nap vao Streamlit.
    Bao toan 100% cu phap va format cua stylesheet.
    """
    path = Path(css_file)
    if not path.exists():
        path = Path(__file__).resolve().parent.parent / "assets" / "style.css"

    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            css_content = f.read()

        # Nap truc tiep the style qua st.markdown
        st.markdown(f"<style>\n{css_content}\n</style>", unsafe_allow_html=True)
        if hasattr(st, "html"):
            try:
                st.html(path)
            except Exception:
                pass
