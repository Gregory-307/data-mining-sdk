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
# ## 📋 Navigation Menu
# 
# This notebook demonstrates the enhanced web-search-sdk capabilities:
# 
# ### 🔍 **Enhanced Search Functions**
# - **[A1: Enhanced DuckDuckGo Search](#A1)** - Structured results with titles, snippets, URLs
# - **[A2: Wikipedia Keywords](#A2)** - Reliable keyword extraction
# - **[A3: Semantic Expansion](#A3)** - Related words and concepts
# - **[A4: Google News RSS](#A4)** - Fresh headline keywords
# - **[A5: Article Content Extraction](#A5)** - Clean text from any URL
#   - **[A5.1: Before/After Extraction](#A5.1)** - Raw HTML vs Cleaned Text
# 
# ### 🛠️ **Toolkit & Utilities**
# - **[B1: Output Helpers](#B1)** - JSON/CSV utilities
# - **[B2: Text Processing](#B2)** - Tokenization and cleaning
# - **[B3: Rate Limiting](#B3)** - Controlled API usage
# - **[B4: Parallel Processing](#B4)** - Batch scraping
# - **[B5: Sentiment Analysis Pipeline](#B5)** - Complete example
# 
# ### 🎯 **Key Improvements in v0.2.0**
# - **Enhanced Search**: `search_and_parse()` now returns structured results
# - **Article Extraction**: `extract_article_content()` works with any URL
# - **Clean Text**: Removes navigation, ads, and HTML artifacts
# - **Sentiment Ready**: Perfect for NLP and sentiment analysis pipelines
# 
# ---
# 
# ## 2  Quick Smoke Test
# Verifies that the freshly-installed package is importable and that the
# built-in `smoke_test.py` script runs without network access.  
# **Expected output**: version string + import success message + smoke test
# results with clear banners showing top-tokens for "openai" (default term).
# This takes <2 s.

# %%
import runpy, importlib.metadata as md, pathlib
print("web_search_sdk version:", md.version("web-search-sdk"))
runpy.run_path(str((pathlib.Path.cwd() / "web-search-sdk" / "smoke_test.py")))

# %% [markdown]
# ## 3  ScraperContext Configuration
# 
# **What is ScraperContext?**
# 
# `ScraperContext` is the central configuration object that controls how every scraper behaves. Think of it as the "settings panel" for all web requests.
# 
# **What does it control?**
# 
# • **Network settings**: HTTP headers, timeouts, retry attempts  
# • **Identity management**: Custom User-Agent rotation, proxy support  
# • **Browser fallback**: When to use Selenium/Playwright vs plain HTTP  
# • **Debugging**: Verbose logging for troubleshooting  
# 
# **Why three different contexts?**
# 
# The cell below creates three pre-configured contexts for different scenarios:
# - `ctx_http`: Basic HTTP-only (fast, lightweight)
# - `ctx_selen`: Selenium browser (reliable, slower)
# - `ctx_play`: Playwright stealth (best for CAPTCHA-heavy sites)
# 
# You'll see these reused throughout the examples below.

# %%
from web_search_sdk.scrapers.base import ScraperContext
ctx_http  = ScraperContext()
ctx_selen = ScraperContext(use_browser=True, browser_type="selenium", debug=False)
ctx_play  = ScraperContext(use_browser=True, browser_type="playwright_stealth")
ctx_http, ctx_selen, ctx_play

# %% [markdown]
# ## Part A – Scraping Helpers
# ### A1 Enhanced Search – DuckDuckGo SERP with Structured Results
# Primary engine: zero CAPTCHA risk, lightweight HTML. Returns structured results
# with titles, snippets, URLs, and source information.

# %%
from web_search_sdk.scrapers.search import search_and_parse
import asyncio

def run_search_and_parse():
    async def _run():
        ddg_res = await search_and_parse("bitcoin rally", ctx_http, top_n=5)
        print("🔗 Links →")
        for l in ddg_res["links"]:
            print(" •", l)
        print("\n🏷️  Top tokens →", ddg_res["tokens"])
        print("\n📋 Structured Results →")
        for i, result in enumerate(ddg_res.get("results", []), 1):
            print(f"  {i}. {result.get('title', 'N/A')}")
            print(f"     Source: {result.get('source', 'N/A')}")
            print(f"     URL: {result.get('url', 'N/A')}")
            if result.get('snippet'):
                print(f"     Snippet: {result['snippet'][:100]}...")
            print()
    asyncio.run(_run())

run_search_and_parse()

# %% [markdown]
# ### A2 Keyword Extractors – Wikipedia Page
# Low-latency and highly reliable.  Good sanity-check source for any term.

# %%
from web_search_sdk.scrapers.wikipedia import wikipedia_top_words
import asyncio

def run_wikipedia_top_words():
    async def _run():
        wiki_tokens = await wikipedia_top_words("bitcoin", ctx_http, top_n=15)
        print("Page → https://en.wikipedia.org/wiki/Bitcoin")
        print("Top tokens →", wiki_tokens)
    asyncio.run(_run())

run_wikipedia_top_words()

# %% [markdown]
# ### A3 Semantic Expansion – RelatedWords
# Expands the seed term via semantic similarity API; useful for idea
# generation or keyword expansion.

# %%
from web_search_sdk.scrapers.related import related_words
import asyncio

def run_related_words():
    async def _run():
        _syn = await related_words("bitcoin", ctx_http)
        print(_syn[:15])
    asyncio.run(_run())

run_related_words()

# %% [markdown]
# ### A4 Keyword Extractors – Google News RSS
# Headlines surface fresh jargon earlier than static pages – this parser
# extracts frequent tokens from the Google News RSS feed.

# %%
from web_search_sdk.scrapers.news import google_news_top_words
import asyncio

def run_google_news_top_words():
    async def _run():
        news_tokens = await google_news_top_words("bitcoin", ctx_http, top_n=15)
        print("Top headline tokens →", news_tokens)
    asyncio.run(_run())

run_google_news_top_words()

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
    import asyncio
    def run_google_web_top_words():
        async def _run():
            print(await google_web_top_words("bitcoin swing", ctx_play, top_n=15))
        asyncio.run(_run())
    run_google_web_top_words()

# %% [markdown]
# ### A5 Article Content Extraction – Clean Text from Any URL
# Demonstrates the new general article extractor that can handle any URL,
# not just specific sites. Perfect for sentiment analysis pipelines.

# %%
import httpx

cnbc_url = "https://www.cnbc.com/2025/07/14/bitcoin-hits-new-all-time-high-above-120000-fueled-by-etf-inflows-crypto.html"

async def main():
    from web_search_sdk.scrapers import extract_article_content
    # Fetch raw HTML for before/after comparison
    raw_html = httpx.get(cnbc_url, timeout=20).text
    article = await extract_article_content(cnbc_url, ctx_play)
    print("📰 Article Details:")
    print(f"Title: {article.get('title', 'N/A')}")
    print(f"Author: {article.get('author', 'N/A')}")
    print(f"Date: {article.get('publish_date', 'N/A')}")
    print(f"Source: {article.get('source', 'N/A')}")
    print(f"\n📝 Summary ({len(article.get('summary', ''))} chars):")
    print(article.get('summary', 'No summary available'))
    print(f"\n📄 Content Preview ({len(article.get('content', ''))} chars total):")
    content = article.get('content', '')
    if content:
        print(content[:300] + "..." if len(content) > 300 else content)
    else:
        print("No content extracted")
    print("\n=== RAW HTML (first 500 chars) ===\n")
    print(raw_html[:500] + ("..." if len(raw_html) > 500 else ""))
    print("\n=== CLEANED ARTICLE TEXT (first 500 chars) ===\n")
    print((article.get('content') or '')[:500] + ("..." if len(article.get('content', '')) > 500 else ""))

import asyncio
asyncio.run(main())

# %% [markdown]
# #### A5.1 Before/After: Raw HTML vs Cleaned Article Text
# This cell shows the difference between the raw HTML and the cleaned, extracted article content.

# %%


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

def _parse_wrapper(html: str, term: str, ctx):
    """Synchronous parse function expected by gather_scrapers."""
    return _ddg_parse(html, top_n=5)

print(await gather_scrapers(terms, fetch=_ddg_fetch, parse=_parse_wrapper, ctx=ctx_http))

# %% [markdown]
# ### B5 Sentiment Analysis Pipeline Example
# Demonstrates how to use the new enhanced functions for sentiment analysis:
# 1. Search for articles about a topic
# 2. Extract clean content from the URLs
# 3. Prepare data for sentiment analysis

# %%
from web_search_sdk.scrapers.search import search_and_parse
from web_search_sdk.scrapers import extract_article_content
import asyncio

def run_sentiment_analysis_pipeline():
    async def sentiment_analysis_pipeline(topic: str, ctx: ScraperContext):
        print(f"🔍 Step 1: Search for articles about '{topic}'")
        search_results = await search_and_parse(topic, ctx, top_n=3)
        print(f"📋 Found {len(search_results.get('results', []))} articles")
        articles_for_analysis = []
        for i, result in enumerate(search_results.get('results', [])[:2]):
            if result.get('url'):
                print(f"\n📰 Step 2: Extracting content from article {i+1}")
                try:
                    article = await extract_article_content(result['url'], ctx)
                    articles_for_analysis.append({
                        'title': article.get('title'),
                        'content': article.get('content'),
                        'summary': article.get('summary'),
                        'source': article.get('source'),
                        'sentiment_ready': len(article.get('content', '')) > 100
                    })
                    print(f"   ✅ Extracted {len(article.get('content', ''))} chars")
                except Exception as e:
                    print(f"   ❌ Failed to extract: {e}")
        print(f"\n📊 Step 3: Prepared {len(articles_for_analysis)} articles for sentiment analysis")
        for i, article in enumerate(articles_for_analysis, 1):
            print(f"   {i}. {article['title']} ({article['source']}) - Ready: {article['sentiment_ready']}")
        return articles_for_analysis
    asyncio.run(sentiment_analysis_pipeline("bitcoin rally", ctx_play))

run_sentiment_analysis_pipeline()

# %% [markdown]
# ## 12  Closing Notes
# • Roadmap → `Progress_Report_v0.2.0.md`  
# • Found it useful? **Star** the repo ⭐ & consider contributing – guidelines
#   in `CONTRIBUTING.md`. 