from itertools import islice
from typing import List, Dict
from youtube_comment_downloader import YoutubeCommentDownloader, SORT_BY_POPULAR

def crawl_youtube_comments(url: str, max_comments: int = 30) -> List[Dict[str, str]]:
    """
    Cào danh sách bình luận từ liên kết YouTube công khai.
    Trả về danh sách dict: [{"author": ..., "text": ...}, ...]
    """
    downloader = YoutubeCommentDownloader()
    generator = downloader.get_comments_from_url(url.strip(), sort_by=SORT_BY_POPULAR)
    comments = [{"author": c["author"], "text": c["text"]} for c in islice(generator, max_comments)]
    return comments
