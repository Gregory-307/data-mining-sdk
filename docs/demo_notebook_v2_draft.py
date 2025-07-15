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
import subprocess, sys, pathlib, os, sys

# Clone repo when notebook is opened outside the repository tree (e.g. Colab)
REPO_URL = "https://github.com/Gregory-307/web-search-sdk.git"
REPO_DIR = pathlib.Path("web-search-sdk")

if not REPO_DIR.exists():
    print("Cloning repo …")
    subprocess.check_call(["git", "clone", "--depth", "1", REPO_URL, str(REPO_DIR)])

ROOT = REPO_DIR.resolve()

# Install SDK (editable) + Playwright package & browsers – always runs, safe and idempotent
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-e", f"{ROOT}[browser]"])
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "playwright"])
subprocess.check_call([sys.executable, "-m", "playwright", "install", "--with-deps"], stdout=subprocess.DEVNULL)

# Make repo importable
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
print("✅ Environment ready")

# %% [markdown]
# ## 2  Quick Smoke Test
# Verifies that the freshly-installed package is importable and that the
# built-in `smoke_test.py` script runs without network access.  
# **Expected output**: version string + a list of top-tokens for the term you
# pass on the CLI (defaults inside the script).  This takes <2 s.

# %%
import runpy, importlib.metadata as md, pathlib
print("web_search_sdk version:", md.version("web-search-sdk"))
runpy.run_path(str((pathlib.Path.cwd() / "web-search-sdk" / "smoke_test.py")))

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
# ## Part A – Scraping Helpers
# ### A1 Keyword Extractors – DuckDuckGo SERP
# Primary engine: zero CAPTCHA risk, lightweight HTML.  Returns top-N tokens
# from the SERP snippets.

# %%
from web_search_sdk.scrapers.duckduckgo_web import duckduckgo_top_words
print(await duckduckgo_top_words("bitcoin swing", ctx_http, top_n=15))

# %% [markdown]
# ### A2 Keyword Extractors – Wikipedia Page
# Low-latency and highly reliable.  Good sanity-check source for any term.

# %%
from web_search_sdk.scrapers.wikipedia import wikipedia_top_words
print(await wikipedia_top_words("bitcoin", ctx_http, top_n=15))

# %% [markdown]
# ### A3 Semantic Expansion – RelatedWords
# Expands the seed term via semantic similarity API; useful for idea
# generation or keyword expansion.

# %%
from web_search_sdk.scrapers.related import related_words
_syn = await related_words("bitcoin", ctx_http)
print(_syn[:15])

# %% [markdown]
# ### A4 Keyword Extractors – Google News RSS
# Headlines surface fresh jargon earlier than static pages – this parser
# extracts frequent tokens from the Google News RSS feed.

# %%
from web_search_sdk.scrapers.news import google_news_top_words
print(await google_news_top_words("bitcoin", ctx_http, top_n=15))

# %% [markdown]
# ### A4 Google SERP Fallback *(optional)*
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
# ### A5 Browser Fetch Example – CNBC (no paywall)
# Demonstrates Playwright-powered rendering for dynamic pages. Fetches the
# article HTML from CNBC (public, no paywall) and prints the first 400 chars.

# %%
from web_search_sdk.browser import fetch_html as _browser_fetch_html

def _cnbc_url(term:str)->str:
    return "https://www.cnbc.com/2023/12/01/bitcoin-rallies-above-40000.html"

html = await _browser_fetch_html("bitcoin", _cnbc_url, ctx_play)
print(html[:400], "…")

# %% [markdown]
# ## Part B – Toolkit Helpers
# ### B1 Output Utilities (JSON/CSV)
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
# ### B2 Text Helpers
# Tokenisation + stop-word removal + frequency counter in one line each.

# %%
from web_search_sdk.utils.text import tokenise, remove_stopwords, most_common
raw = "Bitcoin's all-time high price sparks FOMO!"
print("tokens:", tokenise(raw))
print("no stopwords:", remove_stopwords(tokenise(raw)))
print("top:", most_common(tokenise(raw), 3))

# %% [markdown]
# ### B3 Rate-Limit Decorator
# Async token-bucket decorator – guarantees you never exceed X calls / period.

# %%
import asyncio
from web_search_sdk.utils.rate_limit import rate_limited

@rate_limited(calls=2, period=1.0)
async def _ping(i: int):
    print("tick", i)

await asyncio.gather(*[_ping(i) for i in range(5)])

# %% [markdown]
# ### B4 Parallel Scraping Helper
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