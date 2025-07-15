# flake8: noqa
"""Draft source for Web-Search SDK walk-through notebook.

Each section below corresponds to a Jupyter *cell*; the converter script
(`scripts/convert_demo.py`) will read this file and build a `.ipynb` by
mapping:
    # %% [markdown]  → markdown cell
    # %%            → code cell

Keep code idempotent; avoid hidden state.
"""

# %% [markdown]
# # Web-Search SDK Walk-Through
# Simple, end-to-end demo showing installation, scraping helpers,
# debugging flags, and output utilities.
# 
# Repo: <https://github.com/.../web-search-sdk>
# Docs: README.md & Progress_Report_v0.2.0.md

# %% [markdown]
# ## 0  Bootstrap – clone repo if needed
# This notebook can run standalone (e.g., Colab). It clones the
# web-search-sdk repo into `./web-search-sdk` when it does not already
# exist and defines REPO_ROOT so subsequent imports work regardless of
# where the notebook is opened.

# %%
import os, sys, subprocess, pathlib, importlib

GIT_PRESENT = pathlib.Path(".git").exists()
if GIT_PRESENT:
    # Notebook already running inside a clone
    REPO_ROOT = str(pathlib.Path.cwd())
    print("Running inside repo – no clone needed")
else:
    REPO_URL = os.getenv("REPO_URL", "https://github.com/web-search-sdk/web-search-sdk.git")
    WORKDIR = pathlib.Path("web-search-sdk").resolve()
    if not WORKDIR.exists():
        print("Cloning repo …", REPO_URL)
        subprocess.check_call(["git", "clone", "--depth", "1", REPO_URL, str(WORKDIR)])
    REPO_ROOT = str(WORKDIR)

# Expose repo root to Python path for imports
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

print("REPO_ROOT:", REPO_ROOT)

# ------------------------------------------------------------------
# Install package (editable) and Playwright browsers – NB-02 & NB-03
# ------------------------------------------------------------------
import subprocess, sys

def _run(cmd):
    print("$", " ".join(cmd))
    subprocess.check_call(cmd)

# Upgrade pip quietly
_run([sys.executable, "-m", "pip", "install", "-qU", "pip"])

# Install repo in editable mode with extras
_run([sys.executable, "-m", "pip", "install", "-q", "-e", f"{REPO_ROOT}[browser,test]"])

# Install Playwright browsers once
try:
    import playwright  # type: ignore
    _run([sys.executable, "-m", "playwright", "install", "--with-deps"])
except Exception as exc:  # noqa: BLE001
    print("Playwright install skipped/failed:", exc)

# %% [markdown]
# ### Offline Mode (optional)
# When network access is restricted (e.g., CI or airplane mode) you can set
# the **OFFLINE_MODE** environment variable before running the demo.  All
# HTTP requests are then stubbed out and the scrapers return deterministic
# HTML fixtures bundled with the repo.  This keeps the notebook fast and
# fully reproducible offline.

# %%
import os as _os
if _os.getenv("OFFLINE_MODE") in {"1", "true", "True"}:
    print("Running in OFFLINE_MODE – external network calls are disabled")

# %% [markdown]
# ## 2  Smoke Test
# Quick import & built-in smoke test to verify the setup.

# %%
import importlib, runpy, asyncio, sys
print("web_search_sdk version:", importlib.import_module("web_search_sdk").__version__)
runpy.run_path("smoke_test.py")

# %% [markdown]
# ## 3  ScraperContext Basics
# Demonstrate the most common context configurations.

# %%
from web_search_sdk.scrapers.base import ScraperContext
ctx_http  = ScraperContext()
ctx_selen = ScraperContext(use_browser=True, browser_type="selenium", debug=True)
ctx_play  = ScraperContext(use_browser=True, browser_type="playwright_stealth")
ctx_http, ctx_selen, ctx_play

# %% [markdown]
# ## 4  DuckDuckGo Top-Words Demo (Primary Engine)

# %%
from web_search_sdk.scrapers.duckduckgo_web import duckduckgo_top_words
await duckduckgo_top_words("bitcoin swing", ctx_http, top_n=20)

# %% [markdown]
# ## 4.1  Wikipedia Top-Words Demo
# Wikipedia is a low-latency, high-coverage source that rarely blocks
# automated requests.  The helper fetches the page, strips boiler-plate
# and returns the top-N tokens.

# %%
from web_search_sdk.scrapers.wikipedia import wikipedia_top_words
await wikipedia_top_words("bitcoin", ctx_http, top_n=20)

# %% [markdown]
# ## 4.2  RelatedWords Synonym Demo
# Uses the RelatedWords.org API (with HTML fallback) to pull semantically
# similar terms.  Useful for expanding keyword seed lists.

# %%
from web_search_sdk.scrapers.related import related_words
await related_words("bitcoin", ctx_http)

# %% [markdown]
# ## 4.3  Google News RSS Demo
# Headlines often surface fresh jargon sooner than static pages.  The helper
# parses the Google News RSS feed and extracts the most frequent tokens.

# %%
from web_search_sdk.scrapers.news import google_news_top_words
await google_news_top_words("bitcoin", ctx_http, top_n=20)

# %% [markdown]
# ## 4.4  Google Trends Interest Over Time *(Optional)*
# Eye-ball seasonal spikes quickly with the PyTrends wrapper.  Disabled in
# OFFLINE_MODE environments.

# %%
if _os.getenv("OFFLINE_MODE") not in {"1", "true", "True"}:
    from web_search_sdk.scrapers.trends import interest_over_time
    import pandas as pd
    df = await interest_over_time("bitcoin", ctx_http)
    display(df.tail())
else:
    print("Google Trends skipped – offline mode.")

# %% [markdown]
# ## 4.5  Stock Price Fetch *(Optional)*
# Quick OHLCV pull via yfinance for context charts.  Skipped when OFFLINE_MODE.

# %%
if _os.getenv("OFFLINE_MODE") not in {"1", "true", "True"}:
    from web_search_sdk.scrapers.stock import fetch_stock_data
    df_price = await fetch_stock_data("BTC-USD", ctx_http)
    display(df_price.tail())
else:
    print("Stock price fetch skipped – offline mode.")

# %% [markdown]
# ## 4.6  Parallel Scraping with `gather_scrapers`
# Fetch top DuckDuckGo tokens for multiple terms concurrently in a single call.

# %%
from web_search_sdk.scrapers.base import gather_scrapers
from web_search_sdk.scrapers.duckduckgo_web import _fetch_html as _ddg_fetch, _parse_html as _ddg_parse

terms = ["bitcoin", "ethereum", "dogecoin"]

async def _parse_wrapper(html: str, term: str, ctx):
    return _ddg_parse(html, top_n=5)

result_map = await gather_scrapers(
    terms,
    fetch=_ddg_fetch,
    parse=_parse_wrapper,
    ctx=ctx_http,
)
result_map

# %% [markdown]
# ## 5  Google SERP Fallback *(Optional)*
# DuckDuckGo is reliable enough for most use-cases; a Google fallback adds
# extra latency and may hit CAPTCHA.  The cell below only runs when the
# environment variable **RUN_GOOGLE=1** is set *and* OFFLINE_MODE is not.

# ```python
# export RUN_GOOGLE=1  # bash
# ```

# %%
import os as _os
if _os.getenv("RUN_GOOGLE") in {"1", "true", "True"} and _os.getenv("OFFLINE_MODE") not in {"1", "true", "True"}:
    from web_search_sdk.scrapers.google_web import google_web_top_words
    tokens = await google_web_top_words("bitcoin swing", ctx_play, top_n=20)
    print(tokens)
else:
    print("Google fallback skipped – set RUN_GOOGLE=1 to enable.")

# %% [markdown]
# ## 6  Combined Helper: `search_and_parse`

# %%
from web_search_sdk.scrapers.search import search_and_parse
res = await search_and_parse("btc rally", ctx_play, top_n=10)
res

# %% [markdown]
# ## 7  Paywall Article Retrieval

# %%
from web_search_sdk.scrapers.paywall import fetch_bloomberg
article_html = await fetch_bloomberg("https://www.bloomberg.com/...", ctx_play)
print(article_html[:800])

# %% [markdown]
# ## 8  Output Utilities

# %%
from web_search_sdk.utils.output import to_json
import pathlib, json, os
pathlib.Path("out").mkdir(exist_ok=True)
json_path = "out/tokens.json"
to_json(res["tokens"], json_path, append=True)
print(json_path, "->", os.path.getsize(json_path), "bytes")

# %% [markdown]
# ### CSV helper
# The `to_csv` utility creates or appends rows to a CSV file – handy for quick
# dumps that Excel/Sheets can open.

# %%
from web_search_sdk.utils.output import to_csv
rows = [{"term": t, "top5": ",".join(result_map[t])} for t in result_map]
csv_path = "out/tokens.csv"
to_csv(rows, csv_path, append=False)  # overwrite for demo
print(csv_path, "->", os.path.getsize(csv_path), "bytes")

# %%
# Append another record to tokens.json using to_json(..., append=True)
more_tokens = {"source": "google_news", "tokens": await google_news_top_words("ethereum", ctx_http, top_n=10)}
to_json(more_tokens, json_path, append=True)
print("Appended second record to", json_path)

# %% [markdown]
# ## 4.7  Rate-Limit Decorator Example
# The `utils.rate_limit.rate_limiter` decorator provides an async token-bucket
# to cap outbound request rates.  Below we allow just **2 calls per second**.

# %%
import asyncio
from web_search_sdk.utils.rate_limit import rate_limiter

@rate_limiter(max_calls=2, period=1.0)
async def _echo(i: int):
    print("tick", i)

await asyncio.gather(*[_echo(i) for i in range(5)])

# %% [markdown]
# ## 4.8  Text Utility Helpers
# A grab-bag of small string helpers used across scrapers.

# %%
from web_search_sdk.utils.text import slugify, strip_symbols

raw = "Bitcoin's all-time high!"
print("slugify:", slugify(raw))
print("strip_symbols:", strip_symbols(raw))

# %% [markdown]
# ## 4.9  Custom User-Agent Rotation
# `ScraperContext` can pick a random UA from a list each request – handy when
# hitting rate-limited APIs.

# %%
custom_uas = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/123.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Edge/123.0",
]
ctx_ua = ScraperContext(user_agents=custom_uas)
print([ctx_ua.choose_ua() for _ in range(5)])

# %% [markdown]
# ## 4.10  File Logging with `LOG_SCRAPERS`
# Enable structured JSON logs to a file for post-mortem analysis.

# %%
import pathlib as _pl
import os
log_file = "scraper_debug.log"
os.environ["LOG_SCRAPERS"] = log_file
# Trigger one request to generate log line
await duckduckgo_top_words("litecoin", ctx_http, top_n=5)
print(log_file, "->", _pl.Path(log_file).stat().st_size, "bytes")

# %% [markdown]
# ### Body preview with `DEBUG_TRACE`

# %%
import os
os.environ["DEBUG_TRACE"] = "1"
await duckduckgo_top_words("xrp", ctx_http, top_n=3)
print("DEBUG_TRACE complete – see structured preview in log output")

# %% [markdown]
# ## 9  Debugging & Telemetry
# Enable DEBUG_SCRAPERS to emit structured httpx logs.

# %%
import os, importlib
os.environ["DEBUG_SCRAPERS"] = "1"
# Re-import to trigger patch
importlib.reload(importlib.import_module("web_search_sdk.utils.http_logging"))
await duckduckgo_top_words("ethereum merge", ctx_http, top_n=5)

# %% [markdown]
# ## 10  Browser Engine Benchmark *(Optional)*

# %%
import time, asyncio
for ctx in (ctx_selen, ctx_play):
    start = time.perf_counter()
    await duckduckgo_top_words("btc", ctx, top_n=5)
    print(ctx.browser_type, int((time.perf_counter() - start)*1000), "ms")

# %% [markdown]
# ## 11  Cleanup Helpers

# %%
import shutil, glob
print("Log files:", glob.glob("*.log"))
# !rm scraper_debug.log  # uncomment to clear

# %% [markdown]
# ## 12  FAQ / Troubleshooting
# - **CAPTCHA / consent page?** Switch to `use_browser=True` with Playwright.
# - **Need proxies?** Pass `proxy="http://user:pass@host:port"` to `ScraperContext`.
# - **Timeouts?** Increase `timeout` in `fetch_text` helpers.

# %% [markdown]
# ## 13  Next Steps
# • Explore twitter-sdk → `docs/new_dev_kickoff_plan.md`.
# • Check Progress_Report_v0.2.0.md for roadmap. 