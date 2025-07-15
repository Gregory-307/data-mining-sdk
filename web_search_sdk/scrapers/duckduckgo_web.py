"""
DuckDuckGo Web Search scraper (async)
------------------------------------
A lightweight HTML-only scraper that fetches the static DuckDuckGo search
results page and extracts the most frequent words and the outbound result
links.  Designed as a drop-in alternative to the Google scraper when
Google blocks or captchas become an issue.

The implementation purposely keeps the dependency footprint identical to
other scrapers in *web_search_sdk* (httpx + BeautifulSoup) and borrows the
same tokenisation helpers so we get consistent output across engines.
"""

from __future__ import annotations

import asyncio
import random
import re
from collections import Counter
from pathlib import Path
from typing import List
import urllib.parse as _uparse

import httpx
from bs4 import BeautifulSoup

from .base import ScraperContext
from ..utils.http import _DEFAULT_UA
from web_search_sdk.utils.logging import get_logger
logger = get_logger("DDG")

__all__ = [
    "fetch_serp_html",
    "duckduckgo_top_words",
]

# The HTML endpoint serves a fully rendered, JavaScript-free version of the
# SERP which is perfect for headless scraping.  We request *us-en* locale to
# keep results stable.
_SEARCH_URL = "https://html.duckduckgo.com/html/?q={}&kl=us-en"

_DEFAULT_TOP_N = 20
_TOKEN_RE = re.compile(r"[A-Za-z]{2,}")

# Re-use global stopwords list shared by google_web.py to stay DRY.
_stopwords_path = (
    Path(__file__).resolve().parent.parent / "resources" / "stopwords.txt"
)
try:
    _STOPWORDS: set[str] = {
        l.strip().lower()
        for l in _stopwords_path.read_text(encoding="utf-8").splitlines()
        if l.strip()
    }
except FileNotFoundError:
    _STOPWORDS = set()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _tokenise(text: str) -> List[str]:
    """Return simple word tokens (ASCII letters, length ≥2)."""
    return _TOKEN_RE.findall(text.lower())


def _tokenise_and_bigrams(text: str) -> List[str]:
    toks = _tokenise(text)
    bigrams = [f"{a} {b}" for a, b in zip(toks, toks[1:])]
    return toks + bigrams


async def _fetch_html(term: str, ctx: ScraperContext) -> str:
    headers = ctx.headers.copy()
    ua = ctx.choose_ua() or random.choice(_DEFAULT_UA)
    headers.setdefault("User-Agent", ua)
    headers.setdefault("Accept-Language", "en-US,en;q=0.9")
    headers.setdefault(
        "Accept",
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    )

    url = _SEARCH_URL.format(_uparse.quote(term))
    if ctx.debug:
        logger.info("http_get", url=url)

    for attempt in range(ctx.retries + 1):
        try:
            async with httpx.AsyncClient(timeout=ctx.timeout, proxy=ctx.proxy) as client:
                resp = await client.get(url, headers=headers, follow_redirects=True)
                resp.raise_for_status()
                return resp.text
        except Exception as exc:
            if attempt >= ctx.retries:
                raise exc
            await asyncio.sleep(0.3 * (attempt + 1))

    return ""  # Should not reach here


def _parse_html(html: str, top_n: int = _DEFAULT_TOP_N) -> List[str]:
    """Extract most frequent words/bigrams from a DDG SERP HTML."""

    soup = BeautifulSoup(html, "html.parser")

    # Each result is <a class="result__a">Title</a>
    titles = [a.get_text(" ").strip() for a in soup.select("a.result__a")]

    # Snippets live in <a class="result__snippet"> or <div class="result__snippet">.
    snippets = [
        n.get_text(" ").strip()
        for n in soup.select("a.result__snippet, div.result__snippet")
    ]

    combined = " ".join(titles + snippets)
    tokens = [t for t in _tokenise_and_bigrams(combined) if t not in _STOPWORDS]
    counter = Counter(tokens)
    return [tok for tok, _ in counter.most_common(top_n)]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def fetch_serp_html(term: str, ctx: ScraperContext | None = None) -> str:
    """Return raw DuckDuckGo SERP HTML.

    For DDG we always use the HTTP path as the html.duckduckgo.com endpoint
    is lightweight and rarely blocked.  Browser rendering offers no benefit
    here and is therefore skipped – if *ctx.use_browser* is True we simply
    proceed with the same HTTP request (KISS & YAGNI).
    """

    ctx = ctx or ScraperContext()
    return await _fetch_html(term, ctx)


async def duckduckgo_top_words(
    term: str,
    ctx: ScraperContext | None = None,
    top_n: int = _DEFAULT_TOP_N,
) -> List[str]:
    """Return the most frequent tokens/bigrams on a DDG SERP."""
    html = await fetch_serp_html(term, ctx)
    if not html:
        return []
    return _parse_html(html, top_n) 