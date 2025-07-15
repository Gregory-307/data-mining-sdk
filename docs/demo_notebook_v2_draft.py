# flake8: noqa
# ruff: noqa
"""Draft source for Web-Search SDK demo notebook **V2**.

Each `# %%` marker defines one notebook cell.  Markdown cells use
`# %% [markdown]`.

Execute conversion via:
    python scripts/convert_demo.py --v2
(or auto-detect v2 pattern once converter is updated.)
"""

# %% [markdown]
# # Web-Search SDK – End-to-End Demo (V2)
# 
# This notebook shows **how to install, configure and use** the SDK to pull
# publicly-available web signals – from simple keyword extraction to
# paywall handling and Twitter scraping – in **under 3 minutes**.
# 
# <https://github.com/Gregory-307/web-search-sdk>
# 
# ---
# **Tip** Set `OFFLINE_MODE=1` to run everything against fixture HTML – great
# for CI or airplane mode!

# %% [markdown]
# ## 1  Environment & Installation *(skippable)*
# Use the editable install for local development.  Skip this cell when the
# SDK is already in your environment or running on GitHub Codespaces.

# %%
import os, subprocess, sys, pathlib, importlib.util

# Allow users / CI to opt-out
if not os.getenv("SKIP_INSTALL"):
    ROOT = pathlib.Path(".").resolve()
    try:
        importlib.util.find_spec("web_search_sdk")  # type: ignore
        print("web_search_sdk already importable – skipping install")
    except ImportError:
        print("Installing package in editable mode…")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-e", f"{ROOT}[browser]"])

    # Install Playwright browsers once (idempotent)
    try:
        import playwright  # type: ignore
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "--with-deps"])
    except Exception as exc:  # noqa: BLE001
        print("Playwright setup skipped/failed:", exc)

# %% [markdown]
# ## 2  Quick Smoke Test
# Confirms the SDK imports and basic smoke test passes.

# %%
import runpy, importlib
print("web_search_sdk version:", importlib.import_module("web_search_sdk").__version__)
runpy.run_path("smoke_test.py")

# %% [markdown]
# ## 3  ScraperContext Cheatsheet
# `ScraperContext` controls headers, timeouts, proxies and browser fallback.

# %%
from web_search_sdk.scrapers.base import ScraperContext
ctx_http  = ScraperContext()
ctx_selen = ScraperContext(use_browser=True, browser_type="selenium", debug=False)
ctx_play  = ScraperContext(use_browser=True, browser_type="playwright_stealth")
ctx_http, ctx_selen, ctx_play

# %% [markdown]
# ## 4  Core Scrapers
# ### 4.1 DuckDuckGo – Top Words

# %%
from web_search_sdk.scrapers.duckduckgo_web import duckduckgo_top_words
print(await duckduckgo_top_words("bitcoin swing", ctx_http, top_n=15))

# %% [markdown]
# ### 4.2 Wikipedia – Top Words

# %%
from web_search_sdk.scrapers.wikipedia import wikipedia_top_words
print(await wikipedia_top_words("bitcoin", ctx_http, top_n=15))

# %% [markdown]
# ### 4.3 RelatedWords – Synonyms

# %%
from web_search_sdk.scrapers.related import related_words
print(await related_words("bitcoin", ctx_http)[:15])

# %% [markdown]
# ### 4.4 Google News RSS – Keywords

# %%
from web_search_sdk.scrapers.news import google_news_top_words
print(await google_news_top_words("bitcoin", ctx_http, top_n=15))

# %% [markdown]
# ## 5  Google SERP Fallback *(optional)*
# Heavy and may hit CAPTCHA – set `RUN_GOOGLE=1` to enable.

# %%
if os.getenv("RUN_GOOGLE") == "1":
    from web_search_sdk.scrapers.google_web import google_web_top_words
    print(await google_web_top_words("bitcoin swing", ctx_play, top_n=15))
else:
    print("[skipped] Set RUN_GOOGLE=1 to scrape Google SERP")

# %% [markdown]
# ## 6  Paywall Article Retrieval
# Demonstrates browser rendering fallback. Skips offline.

# %%
from web_search_sdk.scrapers.paywall import fetch_bloomberg
if os.getenv("OFFLINE_MODE"):
    print("[skipped] Offline mode – using fixtures")
else:
    art = await fetch_bloomberg("https://www.bloomberg.com/news/articles/2023-12-01/bitcoin-price-breaks-40k", ctx_play)
    print(art[:400], "…")

# %% [markdown]
# ## 7  Twitter Login & Sample Scrape *(experimental)*
# **Requires** env vars `TW_EMAIL`, `TW_PASS`.  Skips when absent.

# %%
if os.getenv("RUN_TWITTER") == "1":
    tw_user = os.getenv("TW_EMAIL")
    tw_pass = os.getenv("TW_PASS")
    if not tw_user or not tw_pass:
        print("[env missing] Provide TW_EMAIL/TW_PASS to run Twitter demo")
    else:
        # Minimal inline Playwright demo (pseudo-code for brevity)
        from playwright.async_api import async_playwright  # type: ignore
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://twitter.com/login")
            await page.fill("input[name='text']", tw_user)
            await page.press("input[name='text']", "Enter")
            await page.fill("input[name='password']", tw_pass)
            await page.press("input[name='password']", "Enter")
            await page.wait_for_selector("article")
            html = await page.content()
            print(html[:500], "…")
            await browser.close()
else:
    print("[skipped] Set RUN_TWITTER=1 with creds to enable Twitter demo")

# %% [markdown]
# ## 8  Output Utilities

# %%
from web_search_sdk.utils.output import to_json, to_csv
import json, pathlib
pathlib.Path("out").mkdir(exist_ok=True)

json_path = "out/demo_tokens.json"
to_json(["btc", "eth", "doge"], json_path, append=False)
print("Wrote", json_path, "bytes:", pathlib.Path(json_path).stat().st_size)

csv_path = "out/demo_tokens.csv"
to_csv([{"term": "btc", "hits": 120}], csv_path, append=False)
print("Wrote", csv_path, "bytes:", pathlib.Path(csv_path).stat().st_size)

# %% [markdown]
# ## 9  Text Helpers

# %%
from web_search_sdk.utils.text import tokenise, remove_stopwords, most_common
raw = "Bitcoin's all-time high price sparks FOMO!"
print("tokens:", tokenise(raw))
print("no stopwords:", remove_stopwords(tokenise(raw)))
print("top:", most_common(tokenise(raw), 3))

# %% [markdown]
# ## 10  Rate-Limit Decorator

# %%
import asyncio
from web_search_sdk.utils.rate_limit import rate_limited

@rate_limited(calls=2, period=1.0)
async def _ping(i: int):
    print("tick", i)

await asyncio.gather(*[_ping(i) for i in range(5)])

# %% [markdown]
# ## 11  Parallel Scraping Example

# %%
from web_search_sdk.scrapers.base import gather_scrapers
from web_search_sdk.scrapers.duckduckgo_web import _fetch_html as _ddg_fetch, _parse_html as _ddg_parse

terms = ["bitcoin", "ethereum", "solana"]
async def _parse_wrapper(html: str, term: str, ctx):
    return _ddg_parse(html, top_n=5)

print(await gather_scrapers(terms, fetch=_ddg_fetch, parse=_parse_wrapper, ctx=ctx_http))

# %% [markdown]
# ## 12  Closing Notes
# - SDK roadmap in `Progress_Report_v0.2.0.md`
# - Star the repo if you find it useful ⭐
# - PRs welcome – see `CONTRIBUTING.md` 