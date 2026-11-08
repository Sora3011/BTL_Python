from itertools import islice
from typing import List, Dict, Optional, Callable
from youtube_comment_downloader import YoutubeCommentDownloader, SORT_BY_POPULAR

def crawl_youtube_comments(
    url: str,
    max_comments: Optional[int] = None,
    on_progress: Optional[Callable[[int, Optional[int]], None]] = None
) -> List[Dict[str, str]]:
    """
    Cào danh sách bình luận từ liên kết YouTube công khai.
    - max_comments = None (Full Mode): Lấy toàn bộ bình luận trên video.
    - max_comments = int (Config Mode): Lấy theo số lượng chỉ định.
    Hỗ trợ callback on_progress(current_count, max_comments) để cập nhật thanh tiến trình thời gian thực.
    """
    downloader = YoutubeCommentDownloader()
    generator = downloader.get_comments_from_url(url.strip(), sort_by=SORT_BY_POPULAR)
    stream = generator if max_comments is None else islice(generator, max_comments)

    comments: List[Dict[str, str]] = []
    for idx, c in enumerate(stream, start=1):
        comments.append({"author": c["author"], "text": c["text"]})
        if on_progress is not None:
            on_progress(idx, max_comments)
    return comments
