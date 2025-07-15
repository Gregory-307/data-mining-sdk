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
# ## 5  (Optional) Google SERP Fallback
# DuckDuckGo is reliable enough for most use-cases; a Google fallback adds
# extra latency and may hit CAPTCHA.  If you *really* need Google tokens you
# can uncomment the cell below, but it is skipped by default to keep the demo
# fast and API-key-free.
# ```python
# from web_search_sdk.scrapers.google_web import google_web_top_words
# tokens = await google_web_top_words("bitcoin swing", ctx_play, top_n=20)
# tokens
# ```
#
# *Tip:* When running in Colab, Google may block head-less requests; stick to
# DuckDuckGo unless you have Playwright-stealth + proxies configured.

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