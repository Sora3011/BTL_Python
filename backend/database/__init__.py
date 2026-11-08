# backend/database/__init__.py
from .db import (
    DB_NAME,
    init_db,
    get_connection,
    get_system_stats,
    get_posts_summary,
    get_post_comments,
    save_post_and_comments,
)

