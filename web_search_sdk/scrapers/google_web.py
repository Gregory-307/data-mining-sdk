from __future__ import annotations

"""Google Web Search scraper (async) – web_search_sdk copy."""

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
from web_search_sdk.utils.logging import get_logger
logger = get_logger("GOOGLE")

__all__ = ["google_web_top_words", "fetch_serp_html"]

SEARCH_URL = "https://www.google.com/search?q={}&hl=en&gl=us&gbv=1&num=100&safe=off&start=0"
# When we spin up a real browser we can safely drop the `gbv=1` (basic HTML)
# switch so that Google serves the standard JS-enabled page. This
# significantly reduces the odds of getting the “enable javascript”
# interstitial that currently breaks parsing in headless mode.
SEARCH_URL_BROWSER = "https://www.google.com/search?q={}&hl=en&gl=us&num=100&safe=off&start=0"
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
# Public fetch helper (robust HTML retrieval)
# ---------------------------------------------------------------------------


async def fetch_serp_html(term: str, ctx: ScraperContext | None = None) -> str:
    """Return raw Google SERP HTML with automatic fallbacks.

    New logic (2025-07): when the caller explicitly asks for Selenium
    (`ctx.use_browser` and `ctx.browser_type == "selenium"`) we bypass the
    plain-HTTP attempt altogether because it is likely to hit 302/429 or a
    CAPTCHA page.  Selenium rendering is slow but markedly more reliable in
    low-volume scenarios.
    """
    import warnings

    ctx = ctx or ScraperContext()

    # ------------------------------------------------------------------
    # Enforce browser-only path (plain HTTP disabled). When caller did not
    # request a browser backend we emit a RuntimeWarning and return "" so
    # upstream code can decide how to proceed.
    # ------------------------------------------------------------------

    if not ctx.use_browser:
        warnings.warn(
            "Plain HTTP scraping for Google is disabled. Set ScraperContext(use_browser=True) ",
            RuntimeWarning,
            stacklevel=2,
        )
        return ""

    # ------------------------------------------------------------------
    # When *any* browser backend is requested we skip the plain-HTTP path
    # altogether.  This avoids the noisy 302/429 loops and "enable javascript"
    # placeholder pages Google serves.  It also aligns with the user's
    # requirement for zero initial HTTP requests.
    # ------------------------------------------------------------------

    if ctx.use_browser:
        if ctx.debug:
            engine = ctx.browser_type
            logger.info("browser_fast_path", engine=engine, term=term)

        # Choose SERP URL – rich markup for Playwright variants
        url_builder = lambda t: (
            SEARCH_URL_BROWSER.format(_uparse.quote(t))
            if ctx.browser_type.startswith("playwright") else SEARCH_URL.format(_uparse.quote(t))
        )

        html = await _browser_fetch_html(term, url_builder, ctx)
        if html:
            return html

        # If browser fetch fails we just return empty string; callers can
        # decide what to do rather than falling back to HTTP.
        return ""

    # ------------------------------------------------------------------
    # Legacy path: pure HTTP first → browser fallback (never reached when
    # ctx.use_browser=True due to early return above).
    # ------------------------------------------------------------------

    try:
        html = await _fetch_html(term, ctx)
        if html and not _looks_like_captcha(html):
            return html
    except Exception:
        html = ""

    # Browser fallback – use the *standard* Google markup (no gbv=1)
    if ctx.use_browser:
        if ctx.debug:
            logger.info("browser_fallback", term=term)

        # Use the richer SERP layout when we have JS rendering
        url_builder = lambda t: (
            SEARCH_URL_BROWSER.format(_uparse.quote(t))
            if ctx.browser_type.startswith("playwright") else SEARCH_URL.format(_uparse.quote(t))
        )

        html = await _browser_fetch_html(term, url_builder, ctx)
        if html:
            return html

    return ""


# ---------------------------------------------------------------------------
# Slow browser fallback (synchronous)
# ---------------------------------------------------------------------------

# local Selenium fallback now delegated to web_search_sdk.browser.fetch_html


async def google_web_top_words(
    term: str,
    ctx: ScraperContext | None = None,
    top_n: int = DEFAULT_TOP_N,
) -> List[str]:
    """Return the most frequent words/bigrams on a Google SERP.

    Uses `fetch_serp_html` under the hood so it benefits from the same
    HTTP → browser fallback cascade.
    """
    html = await fetch_serp_html(term, ctx)
    if not html:
        return []
    return _parse_html(html, top_n) 