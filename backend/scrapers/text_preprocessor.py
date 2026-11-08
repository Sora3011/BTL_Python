import re
import emoji

URL_RE     = re.compile(r"(?:https?://|www\.)\S+")
MENTION_RE = re.compile(r"@[\w.]+")
REPEAT_RE  = re.compile(r"(?!\d)(.)\1{2,}")

EMOTICONS = [
    (re.compile(r"[:=]-?\){3,}"), " rất vui "),
    (re.compile(r"[:=]-?\)\)"),   " vui vẻ "),
    (re.compile(r"[:=]-?\)"),     " vui "),
    (re.compile(r"[:=]-?\({2,}"), " rất buồn "),
    (re.compile(r"[:=]-?\("),     " buồn "),
    (re.compile(r"<3"),           " yêu thích "),
    (re.compile(r"(?<!\w):3(?!\w)"), " dễ thương "),
    (re.compile(r"(?<!\w):v(?!\w)"), " vui vẻ "),
    (re.compile(r"-_-"),          " chán nản "),
]

def clean_text(text: str, emoji_mode: str = "keep") -> str:
    """Tiền xử lý chuỗi văn bản: khử URL, mention, dịch emoticon tiếng Việt, emoji, ký tự lặp."""
    t = str(text)
    t = URL_RE.sub(" ", t)
    t = MENTION_RE.sub(" ", t)
    for rx, rep in EMOTICONS:
        t = rx.sub(rep, t)
    if emoji_mode == "en":
        t = emoji.demojize(t, delimiters=(" ", " ")).replace("_", " ")
    t = REPEAT_RE.sub(r"\1\1", t)
    return re.sub(r"\s+", " ", t).strip()

