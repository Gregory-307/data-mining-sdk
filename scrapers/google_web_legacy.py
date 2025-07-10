from __future__ import annotations

"""Legacy Google Web-Search scraper (synchronous).
(Copied from migration_package for Data_Mining subset.)
"""

from typing import List
from collections import Counter
import os, random, re
from pathlib import Path
import requests
from bs4 import BeautifulSoup

from ..utils.http import _DEFAULT_UA

SEARCH_URL = "https://www.google.com/search?q={}&hl=en&gl=us&gbv=1&num=100&safe=off&start=0"
TOKEN_RE = re.compile(r"[A-Za-z]{2,}")

_stopwords_path = (
    Path(__file__).resolve().parent.parent / "resources" / "stopwords.txt"
)
try:
    _STOPWORDS: set[str] = {
        l.strip().lower() for l in _stopwords_path.read_text(encoding="utf-8").splitlines() if l.strip()
    }
except FileNotFoundError:
    _STOPWORDS = set()

__all__ = ["top_words_sync"]

def _tokenise(text: str) -> List[str]:
    return TOKEN_RE.findall(text.lower())

def _tokenise_and_bigrams(text: str) -> List[str]:
    toks = _tokenise(text)
    bigrams = [f"{a} {b}" for a, b in zip(toks, toks[1:])]
    return toks + bigrams

def top_words_sync(term: str, *, top_n: int = 20, headers: dict | None = None, timeout: float = 20.0) -> List[str]:
    url = SEARCH_URL.format(requests.utils.quote(term))
    if os.getenv("DEBUG_SCRAPERS") in {"1", "true", "True"}:
        print(f"[GoogleWeb-Legacy] GET {url}")
    hdrs = headers.copy() if headers else {}
    hdrs.setdefault("User-Agent", random.choice(_DEFAULT_UA))
    hdrs.setdefault("Accept-Language", "en-US,en;q=0.9")
    # Explicit Accept header matching real browser requests
    hdrs.setdefault(
        "Accept",
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    )
    resp = requests.get(url, headers=hdrs, timeout=timeout)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    titles = [h.get_text(" ").strip() for h in soup.select("div.yuRUbf > a > h3")]
    if not titles:
        titles = [h.get_text(" ").strip() for h in soup.find_all("h3")]

    snippet_nodes = soup.select(
        "div.IsZvec, span.aCOpRe, div.VwiC3b, div.BNeawe.s3v9rd, div.bVj5Zb, div.GI74Re"
    )
    snippets = [n.get_text(" ").strip() for n in snippet_nodes]
    combined_text = " ".join(titles + snippets)
    tokens = [t for t in _tokenise_and_bigrams(combined_text) if t not in _STOPWORDS]
    if not tokens:
        return []
    counter = Counter(tokens)
    return [tok for tok, _ in counter.most_common(top_n)] 