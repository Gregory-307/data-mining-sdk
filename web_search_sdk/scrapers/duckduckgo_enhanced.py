"""Enhanced DuckDuckGo search with structured result extraction.

Returns titles, snippets, URLs, and source for each result.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
import random
import urllib.parse as _uparse
import httpx
from bs4 import BeautifulSoup
from .base import ScraperContext
from web_search_sdk.utils.logging import get_logger
from urllib.parse import urlparse
import asyncio
from web_search_sdk.utils.text import tokenise, most_common

logger = get_logger("DDG-Enhanced")

__all__ = ["ddg_search_and_parse", "ddg_search_raw"]

_DDG_SEARCH_URL = "https://html.duckduckgo.com/html/?q={}&kl=us-en"

async def _fetch_html(term: str, ctx: ScraperContext) -> str:
    headers = ctx.headers.copy()
    ua = ctx.choose_ua() or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    headers.setdefault("User-Agent", ua)
    headers.setdefault("Accept-Language", "en-US,en;q=0.9")
    url = _DDG_SEARCH_URL.format(_uparse.quote(term))
    if ctx.debug:
        logger.info("http_get", url=url)
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
    return ""

def _extract_source(url: str) -> str:
    try:
        domain = urlparse(url).netloc
        source = domain.replace("www.", "").split(".")[0]
        return source.upper()
    except Exception:
        return "Unknown"

def _parse_html(html: str, top_n: int = 10) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    results = []
    links = []
    all_text = []
    # DuckDuckGo result blocks
    for result in soup.select("div.result"):  # Each result block
        title_node = result.select_one("a.result__a")
        snippet_node = result.select_one("a.result__snippet, div.result__snippet")
        url_node = result.select_one("a.result__a")
        title = title_node.get_text(" ", strip=True) if title_node else None
        snippet = snippet_node.get_text(" ", strip=True) if snippet_node else None
        url = url_node["href"] if url_node and url_node.has_attr("href") else None
        if url:
            links.append(url)
        if title or snippet or url:
            results.append({
                "title": title,
                "snippet": snippet,
                "url": url,
                "source": _extract_source(url) if url else None
            })
        # Collect all text for frequency analysis
        if title:
            all_text.append(title)
        if snippet:
            all_text.append(snippet)
        if len(results) >= top_n:
            break
    
    # Extract frequency-based tokens
    combined_text = " ".join(all_text)
    tokens = tokenise(combined_text)
    top_words = most_common(tokens, top_n)
    
    return {
        "links": links[:top_n],
        "tokens": top_words,  # Frequency-based tokens
        "top_words": top_words,  # Alias for consistency with menu
        "results": results[:top_n]
    }

async def ddg_search_raw(
    term: str,
    ctx: ScraperContext = None
) -> BeautifulSoup:
    """Return raw BeautifulSoup object from DuckDuckGo search."""
    if ctx is None:
        ctx = ScraperContext(use_browser=False)  # HTTP context works fine for DuckDuckGo
    
    # Validate context
    if ctx.use_browser:
        print("💡 Tip: ddg_search_raw works fine with HTTP context (faster). Browser context is optional.")
    
    html = await _fetch_html(term, ctx)
    if not html:
        return BeautifulSoup("", "html.parser")
    return BeautifulSoup(html, "html.parser")


async def ddg_search_and_parse(
    term: str,
    ctx: ScraperContext = None,
    top_n: int = 10
) -> Dict[str, Any]:
    """Enhanced DuckDuckGo search with structured results."""
    if ctx is None:
        ctx = ScraperContext(use_browser=False)  # HTTP context works fine for DuckDuckGo
    
    # Validate context
    if ctx.use_browser:
        print("💡 Tip: ddg_search_and_parse works fine with HTTP context (faster). Browser context is optional.")
    
    html = await _fetch_html(term, ctx)
    if not html:
        return {"links": [], "tokens": [], "results": []}
    return _parse_html(html, top_n=top_n) 