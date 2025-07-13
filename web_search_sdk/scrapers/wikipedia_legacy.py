from __future__ import annotations

"""Legacy Wikipedia scraper based on Newspaper3k Article extraction.
Falls back to original method for compatibility.
"""

from typing import List
from collections import Counter
import re, os

try:
    from newspaper import Article  # type: ignore
except ImportError:  # soft dependency
    Article = None  # type: ignore

STOPWORDS_PATH = __file__.replace("wikipedia_legacy.py", "../resources/stopwords.txt")

try:
    with open(STOPWORDS_PATH, "r", encoding="utf-8") as fh:
        _STOP = {line.strip().lower() for line in fh if line.strip()}
except FileNotFoundError:
    _STOP = set()

TOKEN_RE = re.compile(r"[A-Za-z]{2,}")

__all__ = ["top_words_sync"]


def top_words_sync(article_slug: str, top_n: int = 100, headers: dict | None = None, timeout: float = 20.0) -> List[str]:
    """Return *top_n* most common tokens from a Wikipedia page (blocking)."""
    if Article is None:
        raise RuntimeError("newspaper3k not installed – cannot use legacy wikipedia scraper")

    url = f"https://en.wikipedia.org/wiki/{article_slug}"
    if os.getenv("DEBUG_SCRAPERS") in {"1","true","True"}:
        print(f"[Wikipedia-Legacy] GET {url}")
    art = Article(url)
    if headers:
        art.headers = headers  # type: ignore[attr-defined]
    art.download()
    art.parse()
    text = art.text
    tokens = TOKEN_RE.findall(text.lower())
    tokens = [t for t in tokens if t not in _STOP]
    counter = Counter(tokens)
    return [tok for tok, _ in counter.most_common(top_n)] 