"""Scraper for Wikipedia article text.

Given a seed term, downloads the Wikipedia page and returns the *most
common* tokens (minus stop-words).

We rely on the project-wide stop-word file stored in
`migration_package/resources/stopwords.txt`.
"""
from __future__ import annotations

import asyncio
import re
from collections import Counter
from pathlib import Path
from typing import List

import httpx
from bs4 import BeautifulSoup

from ..resources import stopwords  # runtime import via module created below
from .wikipedia_legacy import top_words_sync

from .base import ScraperContext, run_scraper, run_in_thread

__all__ = ["wikipedia_top_words"]

BASE_URL = "https://en.wikipedia.org/wiki/{}"
DEFAULT_TOP_N = 100


# ---------------------------------------------------------------------------
# Stop-word loader (executed on import)
# ---------------------------------------------------------------------------

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
# Fetch & parse helpers
# ---------------------------------------------------------------------------

async def _fetch_html(term: str, ctx: ScraperContext) -> str:
    headers = ctx.headers.copy()
    ua = ctx.choose_ua()
    if ua:
        headers["User-Agent"] = ua

    url = BASE_URL.format(term.replace(" ", "_"))
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
    # Simple tokeniser: split on non-alphabetic, lowercase.
    return re.findall(r"[A-Za-z]{2,}", text.lower())


def _parse_html(raw: str, term: str, ctx: ScraperContext, top_n: int = DEFAULT_TOP_N) -> List[str]:
    soup = BeautifulSoup(raw, "html.parser")
    content_div = soup.find("div", {"id": "mw-content-text"}) or soup.find("main", {"id": "content"})
    if content_div is None:
        return []

    tokens = _tokenise(content_div.get_text(" "))
    filtered = [tok for tok in tokens if tok not in _STOPWORDS]
    if not filtered:
        filtered = tokens  # fallback if stop-list removes everything
    counter = Counter(filtered)
    return [tok for tok, _ in counter.most_common(top_n)]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def wikipedia_top_words(
    term: str,
    ctx: ScraperContext | None = None,
    top_n: int = DEFAULT_TOP_N,
) -> List[str]:
    """Return a list of the *top_n* most common words from a Wikipedia article."""

    # Attempt legacy Newspaper3k path first
    try:
        words = await run_in_thread(top_words_sync, term, top_n=top_n, headers=ctx.headers if ctx else None, timeout=ctx.timeout if ctx else 20.0)
        if ctx and ctx.debug:
            print(f"[Wikipedia-Legacy] {term} -> {len(words)} words")
        if words:
            return words
    except Exception as e:
        if ctx and ctx.debug:
            print(f"[Wikipedia-Legacy] skipped due to {e}")
        # Continue to HTTP fallback

    def _parse_wrapper(raw: str, t: str, c: ScraperContext):
        return _parse_html(raw, t, c, top_n)

    try:
        words = await run_scraper(term, _fetch_html, _parse_wrapper, ctx)
        if ctx and ctx.debug:
            print(f"[Wikipedia-HTTP] {term} -> {len(words)} words")
    except Exception as e:
        # Log but continue to API fallback
        if ctx and ctx.debug:
            print(f"[Wikipedia-HTTP] failed due to {e}")
        words = []

    # If HTTP scrape produced nothing, use MediaWiki Extracts API -------------
    if not words:
        api_url = (
            "https://en.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=true"
            f"&titles={term}&format=json" )
        if ctx and ctx.debug:
            print(f"[Wikipedia-API] GET {api_url}")

        import httpx, random
        headers = ctx.headers.copy() if ctx else {}
        ua = ctx.choose_ua() if ctx and hasattr(ctx, "choose_ua") else None
        if not ua:
            from ..utils.http import _DEFAULT_UA
            ua = random.choice(_DEFAULT_UA)
        headers["User-Agent"] = ua

        try:
            async with httpx.AsyncClient(timeout=ctx.timeout if ctx else 20.0) as client:
                resp = await client.get(api_url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    pages = data.get("query", {}).get("pages", {})
                    extract = " ".join(p.get("extract", "") for p in pages.values())
                    if extract:
                        tokens = [t for t in _tokenise(extract) if t not in _STOPWORDS]
                        counter = Counter(tokens)
                        words = [tok for tok, _ in counter.most_common(top_n)]
                        if ctx and ctx.debug:
                            print(f"[Wikipedia-API] {term} -> {len(words)} words")
        except Exception as e:
            if ctx and ctx.debug:
                print(f"[Wikipedia-API] failed {e}")

    return words  # may be empty list if all fallbacks failed 