# flake8: noqa
# ruff: noqa
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
    REPO_URL = os.getenv("REPO_URL", "https://github.com/Gregory-307/web-search-sdk.git")
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
# ### Offline Mode (info)
# This section previously documented an environment stub. Network calls now run
# directly, so no setup is required.

# %%
# Offline mode guard removed; network calls will execute normally

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
# ## 4.4  Google Trends Interest Over Time
# Historical interest curve via the PyTrends wrapper.

# %%
from web_search_sdk.scrapers.trends import interest_over_time
import pandas as pd
df = await interest_over_time("bitcoin")
display(df.tail())

# %% [markdown]
# ## 4.5  Stock Price Fetch
# Fetch OHLCV data via yfinance for context charts.

# %%
from web_search_sdk.scrapers.stock import fetch_stock_data
df_price = await fetch_stock_data("BTC-USD", ctx_http)
display(df_price.tail())

# %% [markdown]
# ## 4.6  Parallel Scraping with `gather_scrapers`
# Fetch top DuckDuckGo tokens for multiple terms concurrently in a single call.

# %%
from web_search_sdk.scrapers.base import gather_scrapers
from web_search_sdk.scrapers.duckduckgo_web import _fetch_html as _ddg_fetch, _parse_html as _ddg_parse

terms = ["bitcoin", "ethereum", "dogecoin"]

async def _parse_wrapper(html: str, term: str, ctx):
    return _ddg_parse(html, top_n=5)

tokens_list = await gather_scrapers(
    terms,
    fetch=_ddg_fetch,
    parse=_parse_wrapper,
    ctx=ctx_http,
)
result_map = dict(zip(terms, tokens_list))
result_map

# %% [markdown]
# ## 5  Google SERP Fallback
# DuckDuckGo is reliable enough for most use-cases; a Google fallback adds
# extra latency and may hit CAPTCHA but is now always executed for demo purposes.

# %%
from web_search_sdk.scrapers.google_web import google_web_top_words
tokens = await google_web_top_words("bitcoin swing", ctx_play, top_n=20)
print(tokens)

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
def _first_five_tokens(tok):
    """Return up to first five token strings regardless of collection type."""
    if isinstance(tok, dict):
        seq = list(tok.keys())
    elif isinstance(tok, (list, tuple, set)):
        seq = list(tok)
    else:
        seq = [str(tok)]
    return ",".join(map(str, seq[:5]))

rows = [{"term": term, "top5": _first_five_tokens(tokens)} for term, tokens in result_map.items()]
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
from web_search_sdk.utils.rate_limit import rate_limited

@rate_limited(calls=2, period=1.0)
async def _echo(i: int):
    print("tick", i)

await asyncio.gather(*[_echo(i) for i in range(5)])

# %% [markdown]
# ## 4.8  Text Utility Helpers
# A grab-bag of small string helpers used across scrapers.

# %%
from web_search_sdk.utils.text import tokenise, remove_stopwords, most_common

raw = "Bitcoin's all-time high price sparks FOMO!"
tokens = tokenise(raw)
print("tokens:", tokens)
print("no stopwords:", remove_stopwords(tokens))
print("top words:", most_common(tokens, 3))

# %% [markdown]
# ## 4.9  Custom User-Agent Rotation
# `ScraperContext`