# backend/models/__init__.py
from .sentiment_model import (
    MODEL_PATH,
    DEFAULT_CONFIDENCE_THRESHOLD,
    COLOR_PALETTE,
    get_confidence_threshold,
    load_ai_model,
    predict_batch_comments
)

