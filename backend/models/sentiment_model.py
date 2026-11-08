import os
import json
from typing import Tuple, List, Dict, Any
import torch
import torch.nn.functional as F
import numpy as np
import streamlit as st
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from backend.scrapers.text_preprocessor import clean_text

MODEL_PATH = "./Model_viso_bert_v2"

COLOR_PALETTE = {
    "Tích cực": "#10b981",  # Emerald Green
    "Trung tính": "#64748b", # Slate Slate
    "Hỗn hợp": "#8b5cf6",   # Iris Muted
    "Tiêu cực": "#f43f5e"   # Crimson Terracotta
}

@st.cache_resource
def load_ai_model() -> Tuple[Any, Any, torch.device, Dict[str, Any]]:
    """Tải và lưu trữ bộ nhớ cache mô hình ViSoBERT v2 cùng tokenizer."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH).to(device)
    model.eval()
    
    cfg_file = os.path.join(MODEL_PATH, "inference_config.json")
    if os.path.exists(cfg_file):
        with open(cfg_file, encoding="utf-8") as f:
            inf_cfg = json.load(f)
    else:
        inf_cfg = {"temperature": 1.3, "emoji_mode": "keep", "max_len": 128}
        
    return tokenizer, model, device, inf_cfg

def predict_batch_comments(
    comments_list: List[Dict[str, str]],
    tokenizer: Any,
    model: Any,
    device: torch.device,
    inf_cfg: Dict[str, Any]
) -> List[Tuple[str, str, float, float, float, float, float, str]]:
    """
    Suy luận dự đoán nhãn cảm xúc với Temperature Scaling (T=1.3).
    Phân loại 4 nhãn: Tích cực, Trung tính, Hỗn hợp, Tiêu cực.
    Tính toán: Score 0-100 và Shannon Entropy đo mức độ hỗn loạn thông tin.
    """
    T = float(inf_cfg.get("temperature", 1.3))
    emoji_mode = inf_cfg.get("emoji_mode", "keep")
    max_len = int(inf_cfg.get("max_len", 128))
    
    results = []
    for item in comments_list:
        raw_text = item["text"]
        author = item.get("author", "Ẩn danh")
        processed = clean_text(raw_text, emoji_mode=emoji_mode) or "..."
        
        inputs = tokenizer(processed, return_tensors="pt", truncation=True, padding=True, max_length=max_len).to(device)
        with torch.no_grad():
            logits = model(**inputs).logits
            probs = F.softmax(logits.float() / T, dim=-1).squeeze().cpu().numpy()
            
        neg_prob, neu_prob, pos_prob = float(probs[0]), float(probs[1]), float(probs[2])
        score_100 = round(50.0 + 50.0 * (pos_prob - neg_prob), 1)
        entropy = round(float(-(probs * np.log(probs + 1e-9)).sum()), 3)
        
        if min(neg_prob, pos_prob) >= 0.25:
            label = "Hỗn hợp"
        elif neu_prob >= 0.50:
            label = "Trung tính"
        elif score_100 >= 60:
            label = "Tích cực"
        elif score_100 > 40:
            label = "Trung tính"
        else:
            label = "Tiêu cực"
            
        results.append((
            author, raw_text,
            round(pos_prob * 100, 2),
            round(neu_prob * 100, 2),
            round(neg_prob * 100, 2),
            score_100,
            entropy,
            label
        ))
    return results
