import os
import json
import re
from typing import Tuple, List, Dict, Any, Optional, Callable
import torch
import torch.nn.functional as F
import numpy as np
import streamlit as st
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from backend.scrapers.text_preprocessor import clean_text

MODEL_PATH = "./Model_viso_bert_v3"
DEFAULT_CONFIDENCE_THRESHOLD = 0.70

COLOR_PALETTE = {
    "Tích cực": "#10b981",   # Emerald Green
    "Trung tính": "#64748b",  # Slate
    "Hỗn hợp": "#8b5cf6",    # Iris Muted
    "Tiêu cực": "#f43f5e"    # Crimson Terracotta
}

NAMES = ["Tiêu cực", "Trung tính", "Tích cực"]

CRISIS_KEYWORDS = [
    "cực kỳ tồi", "quá tồi", "rất tồi", "thái độ tồi", "tồi tệ",
    "giao hàng chậm", "giao chậm", "ship chậm", "lừa đảo",
    "tẩy chay", "gian dối", "thất vọng", "vô trách nhiệm", "coi thường"
]

CLAUSE_SPLIT_RE = re.compile(
    r"\s+(?:nhưng|tuy nhiên|tuy vậy|mà|chỉ tiếc|có điều|đáng tiếc)\s+|[.;]\s*",
    re.IGNORECASE
)
MIN_CLAUSE_LEN = 4


def _get_score_100(neg_prob: float, pos_prob: float) -> float:
    return round(50.0 + 50.0 * (pos_prob - neg_prob), 1)


def get_confidence_threshold(inf_cfg: Optional[Dict[str, Any]] = None) -> float:
    if isinstance(inf_cfg, dict) and inf_cfg.get("confidence_threshold") is not None:
        try:
            val = float(inf_cfg["confidence_threshold"])
            if 0.0 <= val <= 1.0:
                return val
        except (TypeError, ValueError):
            pass
    return DEFAULT_CONFIDENCE_THRESHOLD


@st.cache_resource
def load_ai_model() -> Tuple[Any, Any, torch.device, Dict[str, Any]]:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH).to(device)
    model.eval()

    cfg_file = os.path.join(MODEL_PATH, "inference_config.json")
    if os.path.exists(cfg_file):
        with open(cfg_file, encoding="utf-8") as f:
            inf_cfg = json.load(f)
    else:
        inf_cfg = {
            "temperature": 1.3,
            "neutral_bias": 0.0,
            "confidence_threshold": DEFAULT_CONFIDENCE_THRESHOLD,
            "emoji_mode": "keep",
            "max_len": 256,
        }

    return tokenizer, model, device, inf_cfg


def predict_batch_comments(
    comments_list: List[Dict[str, str]],
    tokenizer: Any,
    model: Any,
    device: torch.device,
    inf_cfg: Dict[str, Any],
    model_progress: Optional[Callable[[int, int], None]] = None,
    on_progress: Optional[Callable[[int, int], None]] = None,
) -> List[Tuple[str, str, float, float, float, float, float, str]]:
    T = float(inf_cfg.get("temperature", 1.3))
    neutral_bias = float(inf_cfg.get("neutral_bias", 0.0))
    emoji_mode = inf_cfg.get("emoji_mode", "keep")
    max_len = int(inf_cfg.get("max_len", 256))
    total = len(comments_list)
    progress_cb = model_progress if model_progress is not None else on_progress

    id2label = getattr(model.config, "id2label", {})
    is_5cd_order = str(id2label.get(1, id2label.get("1", ""))).upper().startswith("POS")
    neu_idx = 2 if is_5cd_order else 1
    pos_idx = 1 if is_5cd_order else 2

    results = []
    for idx, item in enumerate(comments_list, start=1):
        raw_text = item["text"]
        author = item.get("author", "Ẩn danh")
        processed = clean_text(raw_text, emoji_mode=emoji_mode) or "..."
        inputs = tokenizer(processed, return_tensors="pt", truncation=True, padding=True, max_length=max_len).to(device)
        with torch.no_grad():
            logits = model(**inputs).logits.float()

            cleaned_lower = processed.lower()
            hit_count = sum(1 for kw in CRISIS_KEYWORDS if kw in cleaned_lower)
            if neutral_bias != 0.0 or hit_count > 0:
                logits = logits.clone()
                if neutral_bias != 0.0:
                    logits[:, neu_idx] += neutral_bias
                if hit_count > 0:
                    logits[:, 0] += 1.5 * hit_count
                    logits[:, neu_idx] -= 1.0 * hit_count

            probs = F.softmax(logits / T, dim=-1).squeeze(0).cpu().numpy()

        neg_prob = float(probs[0])
        neu_prob = float(probs[neu_idx])
        pos_prob = float(probs[pos_idx])

        score_100_main = _get_score_100(neg_prob, pos_prob)
        entropy = round(float(-(probs * np.log(probs + 1e-9)).sum()), 3)

        label = NAMES[int(np.argmax([neg_prob, neu_prob, pos_prob]))]
        final_score = score_100_main
        clauses = [p.strip() for p in CLAUSE_SPLIT_RE.split(processed) if p and len(p.strip()) >= MIN_CLAUSE_LEN]

        is_mixed_by_clause = False
        if len(clauses) >= 2:
            clause_inputs = tokenizer(clauses, return_tensors="pt", truncation=True, padding=True, max_length=max_len).to(device)
            with torch.no_grad():
                clause_logits = model(**clause_inputs).logits.float()
                if neutral_bias != 0.0:
                    clause_logits = clause_logits.clone()
                    clause_logits[:, neu_idx] += neutral_bias
                clause_probs = F.softmax(clause_logits / T, dim=-1).cpu().numpy()

            clause_scores = []
            for cp in clause_probs:
                c_neg, c_pos = float(cp[0]), float(cp[pos_idx])
                clause_scores.append(_get_score_100(c_neg, c_pos))

            if max(clause_scores) >= 60.0 and min(clause_scores) <= 40.0:
                is_mixed_by_clause = True
                final_score = round(float(np.mean(clause_scores)), 1)

        if is_mixed_by_clause:
            label = "Hỗn hợp"
        elif min(neg_prob, pos_prob) >= 0.28 and abs(pos_prob - neg_prob) <= 0.25:
            label = "Hỗn hợp"

        results.append((
            author, raw_text,
            round(pos_prob * 100, 2),
            round(neu_prob * 100, 2),
            round(neg_prob * 100, 2),
            final_score,
            entropy,
            label
        ))

        if progress_cb is not None:
            progress_cb(idx, total)

    return results