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
# ## 1  Environment Setup  
# This cell **bootstraps a completely fresh Colab**:
# 1. Installs the Web-Search SDK in *editable* mode (if missing).
# 2. Installs the Playwright Python package (if missing).
# 3. Downloads headless browser binaries (idempotent).
#
# Feel free to run it multiple times – each step is safe and will be skipped
# when already satisfied.

# %%
import subprocess, sys, pathlib, importlib.util, importlib

ROOT = pathlib.Path(".").resolve()

# 1️⃣ SDK install ------------------------------------------------------------
try:
    importlib.util.find_spec("web_search_sdk")  # type: ignore
    print("web_search_sdk already present – install skipped ✅")
except ImportError:
    print("Installing Web-Search SDK …")
    subprocess.check_call([
        sys.executable,
        "-m",
        "pip",
        "install",
        "-q",
        "-e",
        f"{ROOT}[browser]",
    ])

# 2️⃣ Playwright package -----------------------------------------------------
try:
    import playwright  # type: ignore
    print("playwright Python package present – install skipped ✅")
except ImportError:
    print("Installing Playwright Python package …")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "playwright"])
    playwright = importlib.import_module("playwright")  # type: ignore

# 3️⃣ Browser binaries -------------------------------------------------------
try:
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "--with-deps"], stdout=subprocess.DEVNULL)
    print("Playwright browsers installed ✅")
except Exception as exc:  # noqa: BLE001
    print("Playwright browser install skipped/failed:", exc)

# %% [markdown]
# ## 2  Quick Smoke Test
# Verifies that the freshly-installed package is importable and that the
# built-in `smoke_test.py` script runs without network access.  
# **Expected output**: version string + a list of top-tokens for the term you
# pass on the CLI (defaults inside the script).  This takes <2 s.

# %%
import runpy, importlib
print("web_search_sdk version:", importlib.import_module("web_search_sdk").__version__)
runpy.run_path("smoke_test.py")

# %% [markdown]
# ## 3  ScraperContext Cheatsheet
# `ScraperContext` is the _single_ configuration object shared by every helper
# in the SDK.  It controls:
# • HTTP headers, timeouts & retries  
# • Proxy / custom User-Agent pools  
# • Whether to launch a headless browser fallback (Selenium / Playwright)  
# • Verbose logging for debugging
#
# The cell below instantiates three ready-made contexts to reuse in later
# examples.

# %%
from web_search_sdk.scrapers.base import ScraperContext
ctx_http  = ScraperContext()
ctx_selen = ScraperContext(use_browser=True, browser_type="selenium", debug=False)
ctx_play  = ScraperContext(use_browser=True, browser_type="playwright_stealth")
ctx_http, ctx_selen, ctx_play

# %% [markdown]
# ### 4.1 DuckDuckGo – Top Words
# Primary engine: zero CAPTCHA risk, lightweight HTML.  Returns top-N tokens
# from the SERP snippets.

# %%
from web_search_sdk.scrapers.duckduckgo_web import duckduckgo_top_words
print(await duckduckgo_top_words("bitcoin swing", ctx_http, top_n=15))

# %% [markdown]
# ### 4.2 Wikipedia – Top Words
# Low-latency and highly reliable.  Good sanity-check source for any term.

# %%
from web_search_sdk.scrapers.wikipedia import wikipedia_top_words
print(await wikipedia_top_words("bitcoin", ctx_http, top_n=15))

# %% [markdown]
# ### 4.3 RelatedWords – Synonyms
# Expands the seed term via semantic similarity API; useful for idea
# generation or keyword expansion.

# %%
from web_search_sdk.scrapers.related import related_words
_syn = await related_words("bitcoin", ctx_http)
print(_syn[:15])

# %% [markdown]
# ### 4.4 Google News RSS – Keywords
# Headlines surface fresh jargon earlier than static pages – this parser
# extracts frequent tokens from the Google News RSS feed.

# %%
from web_search_sdk.scrapers.news import google_news_top_words
print(await google_news_top_words("bitcoin", ctx_http, top_n=15))

# %% [markdown]
# ## 5  Google SERP Fallback *(optional)*
# Heavy and may hit CAPTCHA – **runs by default**. Set `DISABLE_GOOGLE=1` to skip in CI.

# %%
import os
# Skip only when explicitly disabled
if os.getenv("DISABLE_GOOGLE") == "1":
    print("[skipped] DISABLE_GOOGLE env var set")
else:
    from web_search_sdk.scrapers.google_web import google_web_top_words
    print(await google_web_top_words("bitcoin swing", ctx_play, top_n=15))

# %% [markdown]
# ## 6  Paywall Article Retrieval
# Shows automatic switch to Playwright when a JS-heavy paywall blocks simple
# HTTP.  Trimmed article body is printed to keep output concise.  Skips when
# `OFFLINE_MODE=1`.

# %%
from web_search_sdk.scrapers.paywall import fetch_bloomberg
if os.getenv("OFFLINE_MODE"):
    print("[skipped] Offline mode – using fixtures")
else:
    art = await fetch_bloomberg("https://www.bloomberg.com/news/articles/2023-12-01/bitcoin-price-breaks-40k", ctx_play)
    print(art[:400], "…")

# %% [markdown]
# ## 7  Twitter Login & Sample Scrape *(experimental)*
# **Requires** env vars `TW_EMAIL`, `TW_PASS`.  Runs automatically when creds are present; otherwise skipped.

# %%
# Run when credentials are provided (no extra flag needed)
tw_user = os.getenv("TW_EMAIL")
tw_pass = os.getenv("TW_PASS")

if tw_user and tw_pass:
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
    print("[skipped] Provide TW_EMAIL and TW_PASS env vars to enable Twitter demo")

# %% [markdown]
# ## 8  Output Utilities
# Lightweight helpers that write structured results to JSON/CSV.  Both create
# parent folders automatically and support **append** mode for easy logging.

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
# Tokenisation + stop-word removal + frequency counter in one line each.

# %%
from web_search_sdk.utils.text import tokenise, remove_stopwords, most_common
raw = "Bitcoin's all-time high price sparks FOMO!"
print("tokens:", tokenise(raw))
print("no stopwords:", remove_stopwords(tokenise(raw)))
print("top:", most_common(tokenise(raw), 3))

# %% [markdown]
# ## 10  Rate-Limit Decorator
# Async token-bucket decorator – guarantees you never exceed X calls / period.

# %%
import asyncio
from web_search_sdk.utils.rate_limit import rate_limited

@rate_limited(calls=2, period=1.0)
async def _ping(i: int):
    print("tick", i)

await asyncio.gather(*[_ping(i) for i in range(5)])

# %% [markdown]
# ## 11  Parallel Scraping Example
# Uses `gather_scrapers` to fan-out N async tasks with a bounded semaphore.
# Total runtime ≈ max(single request latency) instead of sum.

# %%
from web_search_sdk.scrapers.base import gather_scrapers
from web_search_sdk.scrapers.duckduckgo_web import _fetch_html as _ddg_fetch, _parse_html as _ddg_parse

terms = ["bitcoin", "ethereum", "solana"]
async def _parse_wrapper(html: str, term: str, ctx):
    return _ddg_parse(html, top_n=5)

print(await gather_scrapers(terms, fetch=_ddg_fetch, parse=_parse_wrapper, ctx=ctx_http))

# %% [markdown]
# ## 12  Closing Notes
# • Roadmap → `Progress_Report_v0.2.0.md`  
# • Found it useful? **Star** the repo ⭐ & consider contributing – guidelines
#   in `CONTRIBUTING.md`. 