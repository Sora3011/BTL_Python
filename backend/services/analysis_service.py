from typing import List, Dict, Any, Tuple, Optional, Callable
import pandas as pd
from backend.models.sentiment_model import predict_batch_comments
from backend.database.db import save_analysis_results

def process_and_save_comments(
    platform: str,
    source_name: str,
    comments_data: List[Dict[str, Any]],
    tokenizer: Any,
    model: Any,
    device: Any,
    inf_cfg: Dict[str, Any],
    on_progress: Optional[Callable[[int, str], None]] = None,
    model_progress: Optional[Callable[[int, int], None]] = None
) -> Tuple[Optional[int], Optional[pd.DataFrame]]:
    if not comments_data:
        return None, None

    if on_progress is not None:
        on_progress(2, "Chuẩn hóa ngữ cảnh tiếng Việt")

    analyzed_results = predict_batch_comments(
        comments_data,
        tokenizer,
        model,
        device,
        inf_cfg,
        model_progress=model_progress
    )
    if on_progress is not None:
        on_progress(4, "Đang đồng bộ hóa vào SQLite...")
    new_post_id = save_analysis_results(platform, source_name, analyzed_results)
    
    df_results = pd.DataFrame(analyzed_results, columns=[
        "author", "raw_text", "pos_score", "neu_score", "neg_score", "score_100", "entropy", "sentiment_label"
    ])
    
    return new_post_id, df_results
