"""web-search-sdk demo (Batch-7)

Quick-start (no arguments):

    python demo.py

Or customise:

    python demo.py --term "btc rally" \
        --url "https://www.bloomberg.com/..." --url "https://www.cnbc.com/..." \
        --engine playwright

What it does:
1. Expands your term via **DuckDuckGo** (tokens + outbound links – far more reliable than Google without captchas).
2. Optionally fetches the full article text from a pay-walled Bloomberg or CNBC URL and prints a snippet.

All outbound HTTP requests and parsed outputs are echoed so you can inspect them.  Links are printed in plain form – click them in most terminals/IDEs to open in a browser.
"""
from __future__ import annotations

import argparse
import asyncio
from textwrap import indent, shorten

from web_search_sdk.scrapers.base import ScraperContext
from web_search_sdk.scrapers.search import search_and_parse
from web_search_sdk.scrapers.duckduckgo_web import duckduckgo_top_words
from web_search_sdk.scrapers.paywall import fetch_bloomberg, fetch_cnbc


DEFAULT_TERM = "superman box office"
# Two pay-walled articles (CNBC + Bloomberg) to showcase paywall helpers
DEFAULT_ARTICLES = [
    "https://www.cnbc.com/2025/07/11/superman-thursday-preview-box-office.html",
    "https://www.bloomberg.com/news/articles/2025-04-28/global-race-to-lure-us-researchers-intensifies-after-trump-cuts?embedded-checkout=true",
]


async def run(term: str | None, urls: list[str] | None, engine: str) -> None:
    """Run the *full* demo pipeline – a click-through of every public helper.

    The flow:
    1. search_and_parse  – DuckDuckGo links/token preview
    2. duckduckgo_top_words
    3. related_words
    4. wikipedia_top_words
    5. google_news_top_words
    6. fetch_bloomberg / fetch_cnbc for each hard-coded URL (paywall demo)
    """

    if not term:
        term = DEFAULT_TERM

    if not urls:
        urls = DEFAULT_ARTICLES.copy()

    browser_type = {
        "selenium": "selenium",
        "playwright": "playwright",
        "stealth": "playwright_stealth",
    }[engine]

    ctx = ScraperContext(
        debug=True,
        use_browser=True,  # demo always uses browser now
        browser_type=browser_type,
    )

    print("\n=== search_and_parse ===")
    res = await search_and_parse(term, ctx, top_n=10)
    print("Links (clickable):")
    for link in res["links"]:
        print("  -", link)
    print("Top tokens:", res["tokens"])

    print("\n=== duckduckgo_top_words ===")
    tokens = await duckduckgo_top_words(term, ctx, top_n=20)
    print(tokens)

    # ------------------------------------------------------------------
    # Additional helper demos ("other stuff")
    # ------------------------------------------------------------------
    from web_search_sdk.scrapers.related import related_words
    from web_search_sdk.scrapers.wikipedia import wikipedia_top_words
    from web_search_sdk.scrapers.news import google_news_top_words

    print("\n=== related_words ===")
    rel = await related_words(term, ctx)
    print(rel[:30])

    print("\n=== wikipedia_top_words ===")
    wiki_toks = await wikipedia_top_words(term, ctx, top_n=20)
    print(wiki_toks)

    print("\n=== google_news_top_words ===")
    news_toks = await google_news_top_words(term, ctx, top_n=20)
    print(news_toks)

    # ------------------------------------------------------------------
    # Paywall article fetches (Bloomberg + CNBC)
    # ------------------------------------------------------------------
    for u in urls:
        fetch_fn = fetch_bloomberg if "bloomberg.com" in u else fetch_cnbc
        name = "bloomberg" if "bloomberg.com" in u else "cnbc"
        print(f"\n=== fetch_{name} ===\nURL: {u}")
        html = await fetch_fn(u, ctx)
        snippet = indent(shorten(html, width=400, placeholder="…"), "    ")
        print("Article snippet:\n" + snippet)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="web-search-sdk demo – full click-through")
    ap.add_argument("--term", required=False, help="search term (default: 'superman box office')")
    ap.add_argument("--url", action="append", help="Article URL(s); can be given multiple times. Default includes CNBC & Bloomberg samples")

    ap.add_argument(
        "--engine",
        choices=["selenium", "playwright", "stealth"],
        default="selenium",
        help="browser engine to use (default: selenium)",
    )

    args = ap.parse_args()

    try:
        asyncio.run(run(args.term, args.url, args.engine))
    except KeyboardInterrupt:
        print("\nCancelled by user") 