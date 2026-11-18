from itertools import islice
from typing import List, Dict, Optional, Callable
from youtube_comment_downloader import YoutubeCommentDownloader, SORT_BY_RECENT
def crawl_youtube_comments(
    url: str,
    max_comments: Optional[int] = None,
    on_progress: Optional[Callable[[int, Optional[int]], None]] = None
) -> List[Dict[str, str]]:
    downloader = YoutubeCommentDownloader()
    generator = downloader.get_comments_from_url(url.strip(), sort_by=SORT_BY_RECENT)
    stream = generator if max_comments is None else islice(generator, max_comments)

    comments: List[Dict[str, str]] = []
    for idx, c in enumerate(stream, start=1):
        comments.append({"author": c["author"], "text": c["text"]})
        if on_progress is not None:
            on_progress(idx, max_comments)
    return comments
