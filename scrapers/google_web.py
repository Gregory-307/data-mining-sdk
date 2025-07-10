from __future__ import annotations

"""Google Web Search scraper (async) – Data_Mining copy."""

import asyncio
from collections import Counter
from pathlib import Path
from typing import List
import re

import httpx
from bs4 import BeautifulSoup
import urllib.parse as _uparse

from .google_web_legacy import top_words_sync as legacy_sync
from .base import ScraperContext, run_scraper, run_in_thread
import random
from ..utils.http import _DEFAULT_UA
from ..browser import fetch_html as _browser_fetch_html, _SEL_AVAILABLE

__all__ = ["google_web_top_words"]

SEARCH_URL = "https://www.google.com/search?q={}&hl=en&gl=us&gbv=1&num=100&safe=off&start=0"
DEFAULT_TOP_N = 20
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


def _tokenise(text: str) -> List[str]:
    return TOKEN_RE.findall(text.lower())


def _tokenise_and_bigrams(text: str) -> List[str]:
    toks = _tokenise(text)
    bigrams = [f"{a} {b}" for a, b in zip(toks, toks[1:])]
    return toks + bigrams


async def _fetch_html(term: str, ctx: ScraperContext) -> str:
    headers = ctx.headers.copy()
    ua = ctx.choose_ua()
    if not ua:
        ua = random.choice(_DEFAULT_UA)
    headers.setdefault("User-Agent", ua)
    headers.setdefault("Accept-Language", "en-US,en;q=0.9")
    # Explicit Accept header to mimic real browsers and avoid JS shell pages
    headers.setdefault(
        "Accept",
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    )
    url = SEARCH_URL.format(_uparse.quote(term))
    if ctx.debug:
        print(f"[GoogleWeb-HTTP] GET {url}")
    for attempt in range(ctx.retries + 1):
        try:
            async with httpx.AsyncClient(timeout=ctx.timeout, proxies=ctx.proxy) as client:
                resp = await client.get(url, headers=headers, follow_redirects=True)
                resp.raise_for_status()
                return resp.text
        except Exception as exc:
            if attempt >= ctx.retries:
                raise exc
            await asyncio.sleep(0.3 * (attempt + 1))


def _parse_html(html: str, top_n: int = DEFAULT_TOP_N) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    # Robust extraction – handle both desktop and gbv=1 mobile markups
    titles = [h.get_text(" ").strip() for h in soup.select("div.yuRUbf > a > h3")]
    if not titles:
        titles = [h.get_text(" ").strip() for h in soup.find_all("h3")]

    snippet_nodes = soup.select(
        "div.IsZvec, span.aCOpRe, div.VwiC3b, div.BNeawe.s3v9rd, div.bVj5Zb, div.GI74Re"
    )
    snippets = [n.get_text(" ").strip() for n in snippet_nodes]

    if _looks_like_captcha(html):
        return []

    combined = " ".join(titles + snippets)
    tokens = [t for t in _tokenise_and_bigrams(combined) if t not in _STOPWORDS]
    if not tokens:
        # If Google served a consent/captcha page, tokenise full body text
        tokens = [t for t in _tokenise_and_bigrams(soup.get_text(" ")) if t not in _STOPWORDS]
    counter = Counter(tokens)
    return [tok for tok, _ in counter.most_common(top_n)]


def _looks_like_captcha(html: str) -> bool:
    return ("detected unusual traffic" in html.lower() or "captcha-form" in html.lower())


# ---------------------------------------------------------------------------
# Slow browser fallback (synchronous)
# ---------------------------------------------------------------------------

# local Selenium fallback now delegated to Data_Mining.browser.fetch_html


async def google_web_top_words(term: str, ctx: ScraperContext | None = None, top_n: int = DEFAULT_TOP_N) -> List[str]:
    ctx = ctx or ScraperContext()
    def _parse_wrapper(html: str, t: str, c: ScraperContext):
        return _parse_html(html, top_n)
    try:
        words = await run_scraper(term, _fetch_html, _parse_wrapper, ctx)
        if words:
            return words
    except Exception:
        pass
    # Fallback 2: legacy blocking implementation in a thread
    try:
        words = await run_in_thread(legacy_sync, term, top_n=top_n, headers=ctx.headers, timeout=ctx.timeout)
        if ctx.debug:
            print(f"[GoogleWeb-Legacy] {term} -> {len(words)} words")
        if words:
            return words
    except Exception:
        pass

    # Fallback 3: Selenium browser (optional)
    if ctx.use_browser:
        if ctx.debug:
            print(f"[GoogleWeb] Trying Selenium fallback for '{term}'…")
        html = await _browser_fetch_html(term, lambda t: SEARCH_URL.format(_uparse.quote(t)), ctx)
        if html:
            words = _parse_html(html, top_n)
            if ctx.debug:
                print(f"[GoogleWeb-Selenium] {term} -> {len(words)} words")
            return words

    if ctx.debug:
        print(f"[GoogleWeb] {term} – no data found after all fallbacks")
    return [] 