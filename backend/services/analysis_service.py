from typing import List, Dict, Any, Tuple, Optional, Callable
import pandas as pd
from backend.models.sentiment_model import predict_batch_comments
from backend.database.db import save_post_and_comments

def process_and_save_analysis(
    platform: str,
    post_source: str,
    comments_data: List[Dict[str, Any]],
    tokenizer: Any,
    model: Any,
    device: Any,
    inf_cfg: Dict[str, Any],
    on_inference_progress: Optional[Callable[[int, int], None]] = None,
    on_before_save: Optional[Callable[[], None]] = None
) -> Tuple[Optional[int], Optional[pd.DataFrame]]:
    """
    Pipeline chung: nhận danh sách comment thô -> suy luận ViSoBERT v2 -> lưu SQLite -> trả về new_post_id & DataFrame.
    Hỗ trợ callback cập nhật tiến trình theo thời gian thực.
    """
    if not comments_data:
        return None, None
        
    analyzed_results = predict_batch_comments(
        comments_data,
        tokenizer,
        model,
        device,
        inf_cfg,
        on_progress=on_inference_progress
    )
    if on_before_save is not None:
        on_before_save()
    new_post_id = save_post_and_comments(platform, post_source, analyzed_results)
    
    df_results = pd.DataFrame(analyzed_results, columns=[
        "author", "raw_text", "pos_score", "neu_score", "neg_score", "score_100", "entropy", "sentiment_label"
    ])
    
    return new_post_id, df_results
