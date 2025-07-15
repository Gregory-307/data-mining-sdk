"""Google News scraper (functional).

Downloads the Google News search results page for a term and returns the
*top_n* most common tokens from all article headlines.  Stop-words are
removed using the shared list in resources/stopwords.txt.
"""
from __future__ import annotations

import asyncio
import re
from collections import Counter
from pathlib import Path
from typing import List

import httpx
from bs4 import BeautifulSoup

from .news_legacy import top_words_sync

from .base import ScraperContext, run_scraper, run_in_thread
from web_search_sdk.utils.logging import get_logger
logger = get_logger("NEWS")

__all__ = ["google_news_top_words"]

RSS_URL = "https://news.google.com/rss/search?q={}&hl=en-US&gl=US&ceid=US:en"
DEFAULT_TOP_N = 20

# Load stop-word list once ----------------------------------------------------
_stopwords_path = (
    Path(__file__).resolve().parent.parent / "resources" / "stopwords.txt"
)

try:
    _STOPWORDS: set[str] = {
        line.strip().lower() for line in _stopwords_path.read_text(encoding="utf-8").splitlines() if line.strip()
    }
except FileNotFoundError:
    _STOPWORDS = set()

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _fetch_rss(term: str, ctx: ScraperContext) -> str:
    headers = ctx.headers.copy()
    ua = ctx.choose_ua()
    if ua:
        headers["User-Agent"] = ua

    url = RSS_URL.format(httpx.utils.quote(term))
    for attempt in range(ctx.retries + 1):
        try:
            async with httpx.AsyncClient(timeout=ctx.timeout, proxies=ctx.proxy) as client:
                resp = await client.get(url, headers=headers, follow_redirects=True)
                resp.raise_for_status()
                return resp.text
        except Exception as exc:
            if attempt >= ctx.retries:
                raise exc
            await asyncio.sleep(0.5 * (attempt + 1))


def _tokenise(text: str) -> List[str]:
    return re.findall(r"[A-Za-z]{2,}", text.lower())


def _parse_rss(xml: str, top_n: int = DEFAULT_TOP_N) -> List[str]:
    soup = BeautifulSoup(xml, "xml")
    titles = [item.title.get_text() for item in soup.find_all("item")]
    tokens: list[str] = []
    for title in titles:
        tokens.extend(_tokenise(title))
    filtered = [t for t in tokens if t not in _STOPWORDS]
    if not filtered:
        filtered = tokens
    counter = Counter(filtered)
    return [tok for tok, _ in counter.most_common(top_n)]

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def google_news_top_words(
    term: str,
    ctx: ScraperContext | None = None,
    top_n: int = DEFAULT_TOP_N,
) -> List[str]:
    """Return most common words from Google News headlines for *term*."""

    # Legacy HTML search page first
    try:
        words = await run_in_thread(top_words_sync, term, top_n=top_n, headers=ctx.headers if ctx else None, timeout=ctx.timeout if ctx else 20.0)
        if ctx and ctx.debug:
            logger.info("legacy_html", term=term, words=len(words))
        if words:
            return words
    except Exception:
        pass

    def _parse_wrapper(xml: str, t: str, c: ScraperContext):
        return _parse_rss(xml, top_n)

    try:
        words = await run_scraper(term, _fetch_rss, _parse_wrapper, ctx)
        if ctx and ctx.debug:
            logger.info("rss_parse", term=term, words=len(words))
        return words
    except Exception:
        if ctx and ctx.debug:
            logger.info("no_data", term=term)
        return [] 