"""web-search-sdk demo

Run:
    python demo.py --term "btc rally" --url "https://www.bloomberg.com/..." --browser

The script:
1. Expands your term via Google (tokens + links).
2. Fetches full article text from a paywalled URL (Bloomberg/CNBC).
All HTTP requests and parsed outputs are printed so you can inspect
what was sent/received.  Links are printed as plain URLs – click them
in most terminals/IDEs to open in a browser.
"""
from __future__ import annotations

import argparse
import asyncio
from textwrap import indent, shorten

from web_search_sdk.scrapers.base import ScraperContext
from web_search_sdk.scrapers.search import search_and_parse
from web_search_sdk.scrapers.google_web import google_web_top_words
from web_search_sdk.scrapers.paywall import fetch_bloomberg, fetch_cnbc


async def run(term: str, url: str | None, engine: str) -> None:
    """Run demo with the selected browser *engine*.

    engine: 'selenium' | 'playwright' | 'stealth'
    """

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

    print("\n=== google_web_top_words ===")
    tokens = await google_web_top_words(term, ctx, top_n=20)
    print(tokens)

    if url:
        fetch_fn = fetch_bloomberg if "bloomberg.com" in url else fetch_cnbc
        print(f"\n=== fetch_{fetch_fn.__name__.split('_')[-1]} ===")
        html = await fetch_fn(url, ctx)
        snippet = indent(shorten(html, width=400, placeholder="…"), "    ")
        print("Article snippet:\n" + snippet)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="web-search-sdk demo")
    ap.add_argument("--term", required=True, help="search term, e.g. 'btc rally'")
    ap.add_argument("--url", help="Bloomberg or CNBC article URL (optional)")

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