# Web-Search SDK

This repository houses an **async Python toolkit** for collecting and preprocessing publicly available web data that can later feed into downstream analytics or trading pipelines.

The helpers here grew out of our internal *Stock-Algorithm* work-bench; they have been extracted and cleaned up so that they can operate **stand-alone** and slot easily into other code-bases.

Primary objective
-----------------
Provide an automated way to pull *related terms*, *recent news snippets*, *Wikipedia context*, *search-engine SERP keywords*, *Google Trends curves* and *basic price history* for any set of seed terms we are researching. The data will later be correlated with additional signals (Twitter sentiment, on-chain metrics, etc.) to decide hedge ratios and spot inflection points.

Design principles
-----------------
• **Uniform API** – every scraper is an async function that accepts `(term, ctx)` and returns structured data.  
• **Fail-safe** – built-in retries, multiple fall-backs (legacy HTML, headless browser) and optional proxy support.  
• **Minimal ceremony** – functional helpers, no inheritance tree.  
• **Self-contained** – no dependency on the old monorepo; can be vendor-dropped or installed from PyPI.  

If you only need a quick data pull you can copy-paste one function; if you need an automated pipeline you can orchestrate everything with `asyncio.gather`.

## Available pull-helpers

| Source / Provider        | Public Helper                               | Typical Output                 | Notes                                           |
|--------------------------|---------------------------------------------|--------------------------------|-------------------------------------------------|
| RelatedWords.org         | `scrapers.related_words`                    | `list[str]`                    | JSON API with HTML & Selenium fall-backs        |
| Wikipedia                | `scrapers.wikipedia_top_words`              | top-N tokens                   | Legacy Newspaper3k → raw HTML → JSON API        |
| Google News RSS          | `scrapers.google_news_top_words`            | top-N tokens                   | No CAPTCHA risk; RSS is lightweight             |
| Google Web Search (links)| `scrapers.search.search_and_parse`          | `{links, tokens}`              | Returns outbound links **and** tokens in one call |
| Google Trends            | ~~`scrapers.interest_over_time`~~ *(deprecated – see trends-sdk)* | `pandas.DataFrame` | Will be removed in v0.3 – migrate to **trends-sdk** |
| Yahoo Finance            | `scrapers.fetch_stock_data`                 | OHLCV `pandas.DataFrame`       | Async wrapper around *yfinance*                 |
| Bloomberg / CNBC         | `scrapers.paywall.fetch_*`                 | full article text              | Quick HTTP → Playwright fallback for paywalls   |

For exact signatures see the [API reference](#api-reference).

## Installation (5 min)

```bash
# 1 – create an isolated environment (recommended)
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate.bat     # Windows PowerShell

# 2 – install the core package in **editable** mode
pip install -e .                 # or ".[test]", ".[browser]" (see below)
```

Optional extras (quick): `browser` for headless Playwright, `test` for pytest.  Full matrix → see [Progress_Report_v0.2.0.md](Progress_Report_v0.2.0.md).

Run (choose browser engine):
    python demo.py --term "btc rally" --url "https://www.bloomberg.com/..." --engine selenium

Available engines:

| Engine flag | Description | Notes |
|-------------|-------------|-------|
| `selenium` *(default)* | Firefox via Geckodriver | No extra install on CI
| `playwright` | Playwright-Firefox | Faster than Selenium
| `stealth` | Playwright-Chromium with anti-bot patches | Best for heavy CAPTCHA sites |

The SDK requires **Python ≥ 3.10**.

## Quick start

```python
import asyncio
from web_search_sdk.scrapers import wikipedia_top_words
from web_search_sdk.scrapers.base import ScraperContext


async def main():
    ctx = ScraperContext(debug=True)
    tokens = await wikipedia_top_words("artificial intelligence", ctx=ctx, top_n=15)
    print(tokens)


asyncio.run(main())
```

Expected console output (truncated):

```text
['intelligence', 'ai', 'artificial', 'machine', 'learning', 'computer', 'systems', 'data', 'human', 'algorithm']
```

The Wikipedia helper uses a public HTML endpoint (and a JSON fallback) and is therefore the most reliable first test.

Need a one-liner?  A smoke-test script is provided:

```bash
python smoke_test.py "openai"
```

It runs without installation (the script injects the repo root into `sys.path`).

> **Heads-up** The `google_web_top_words` helper can be throttled or CAPTCHA-blocked by Google. The module has legacy and Selenium fallbacks, but reliability is currently lower than the other helpers; use it with that expectation or route it through proxies.

Parameter note
--------------
Most helpers accept `top_n` (default varies by source).  Setting `top_n=10` returns the ten most frequent tokens after stop-word removal.  For helpers that do not support ranking (e.g. `related_words`) the parameter is ignored.

## API Reference (cheat-sheet)

```python
from web_search_sdk.scrapers import (
    related_words,
    wikipedia_top_words,
    google_news_top_words,
    google_web_top_words,
)
from web_search_sdk.scrapers.trends import interest_over_time
from web_search_sdk.scrapers.stock import fetch_stock_data

# Shared runtime configuration object
from web_search_sdk.scrapers.base import ScraperContext, gather_scrapers
```

### ScraperContext
Key parameters you can tweak:

| Argument        | Default | Description                                                 |
|-----------------|---------|-------------------------------------------------------------|
| `headers`       | `{}`    | Base HTTP headers merged into every request                 |
| `timeout`       | `20.0`  | Connect & read timeout (seconds)                            |
| `retries`       | `2`     | Automatic HTTP retry count                                  |
| `user_agents`   | `None`  | Custom UA rotation list (falls back to 2 builtin strings)   |
| `proxy`         | `None`  | e.g. `http://user:pass@host:port`                           |
| `use_browser`   | `False` | Enable Selenium fallback where supported                    |
| `debug`         | `False` | Verbose logging via *structlog*                             |

Combine scrapers easily:

```python
terms = ["openai", "chatgpt", "generative ai"]
ctx   = ScraperContext(user_agents=my_pool, proxy="http://proxy.local:8080")
words_per_term = await gather_scrapers(
    terms,
    fetch=google_web_top_words._fetch_html,
    parse=lambda html, term, ctx: google_web_top_words._parse_html(html, 20),
    ctx=ctx,
)
```

## High-level architecture

```mermaid
graph TD
  subgraph "Scrapers"
    RW["related_words"]
    WP["wikipedia_top_words"]
    GN["google_news_top_words"]
    GW["google_web_top_words"]
    TR["interest_over_time"]
    ST["fetch_stock_data"]
  end

  utils_http["utils.http"]
  utils_logging["utils.logging"]
  browser["browser (Selenium)"]

  RW --> utils_http
  WP --> utils_http
  GN --> utils_http
  GW --> utils_http
  GW -.optional fallback .-> browser
  utils_http --> utils_logging
  TR -->|"pytrends"| ExternalPytrends[("pytrends")]
  ST -->|"yfinance"| ExternalYF[("yfinance")]
```

Dashed edge = optional Selenium path activated when `ScraperContext(use_browser=True)`.

---
### Browser & Paywalls (one-liner)
`ScraperContext(use_browser=True, browser_type="playwright")` enables JS rendering for Google CAPTCHAs & paywalls (Bloomberg/CNBC).  Selenium remains as a legacy option.

## Offline Mode
When you need to run the toolkit in an **air-gapped** environment (CI without
external network or airplane-mode laptop) set:

```bash
export OFFLINE_MODE=1                 # or "true"
```

All outbound HTTP calls are short-circuited and the helpers return deterministic
HTML fixtures packaged under `tests/fixtures/`.  This keeps the demo notebook
and unit-tests fully reproducible with **zero** network.

---
## Demo notebook (Colab-friendly)
The repo contains a draft source file at
`docs/demo_notebook_draft.py` which is converted into a Jupyter notebook via:

```bash
scripts/convert_demo.py    # generates docs/demo.ipynb
scripts/run_demo.py        # executes it head-less (used in CI)
```

The notebook is **self-bootstrapping** – when opened in Colab it clones the repo
(if missing), installs the package in editable mode, Playwright browsers and
then runs through several real-world scrapes (DuckDuckGo, paywall fetches,
telemetry debug etc.).  When `OFFLINE_MODE=1` the notebook falls back to the
fixture HTML so it stays lightning-fast.

---
### Testing & Coverage (local)

```bash
# run tests + coverage
pytest --cov=web_search_sdk --cov-report=term -q
```

The CI pipeline always uploads a `coverage.xml` artifact; currently it does **not
fail** the build on coverage percentage (we’re still adding new tests), but the
report is available for inspection in GitHub Actions.

---
## Contributing

1. **Fork** → **create branch** → **PR**.  PRs must pass CI (tests + coverage).
2. Respect *PEP 8*; run `black` / `ruff` locally before pushing.
3. Update or add tests for any new scraper.
4. Document the new feature in this README.

---
For roadmap & detailed progress see **Progress_Report_v0.2.0.md**.

---
## License

MIT – see [LICENSE](LICENSE) for full text. 

---
## Paywall Handling (Bloomberg & CNBC)

Some premium outlets require full JS rendering to reveal the article body.  When you
set `ScraperContext(use_browser=True, browser_type="playwright")` the helper
`web_search_sdk.scrapers.paywall` will transparently spin up a headless
Playwright-Firefox session, navigate, wait for `<article>` and return the cleaned
text.  Example:

```python
from web_search_sdk.scrapers.paywall import fetch_bloomberg
from web_search_sdk.scrapers.base import ScraperContext

ctx = ScraperContext(use_browser=True, browser_type="playwright", debug=True)
article = await fetch_bloomberg("https://www.bloomberg.com/news/articles/...", ctx)
print(article[:400], "…")
```

If `use_browser=False` a quick HTTP fetch is attempted first—fast and cheap for
pages without heavy paywall JS.

---
## Output Utilities
Lightweight helpers live in `web_search_sdk.utils.output`.

```python
from web_search_sdk.utils.output import to_json, to_csv

data = {"term": "btc rally", "score": 0.87}
# overwrite
to_json(data, "out/latest.json")
# append (keeps a JSON list)
to_json(data, "out/history.json", append=True)

rows = [{"term": "btc", "hits": 120}, {"term": "eth", "hits": 95}]
# create or overwrite CSV
to_csv(rows, "out/stats.csv")
# append more rows later
to_csv(rows, "out/stats.csv", append=True)
```

The helpers are idempotent and create parent folders automatically.

---
## Deprecated Module – trends
`web_search_sdk.scrapers.trends` is now **deprecated** in favour of the separate
`trends-sdk` repo.  Importing it raises a `DeprecationWarning` and prints a
reminder so you can migrate without surprises.
```python
import warnings, web_search_sdk.scrapers.trends  # warning printed once
```
--- 
---
## Demo Notebook Contents (v0.3)
The generated notebook (`docs/demo.ipynb`) now walks through **ten** focused
examples – each runnable offline via fixtures:

1. DuckDuckGo top-words (primary engine)
2. Wikipedia top-words
3. RelatedWords synonym expansion
4. Google News RSS keywords
5. Google Trends interest‐over-time *(optional online)*
6. Stock OHLCV fetch via yfinance *(optional online)*
7. Parallel scraping with `gather_scrapers`
8. Output helpers – `to_json`, `to_csv`, append
9. Utility helpers – rate-limiter, tokenise / remove_stopwords / most_common, custom UA rotation
10. Advanced debugging – `LOG_SCRAPERS` file output + `DEBUG_TRACE` body preview

Set `OFFLINE_MODE=1` to skip network-dependent cells; set `RUN_GOOGLE=1` to
activate the Google SERP fallback cell.

---
### New Helper Reference
Added since v0.2:

| Helper | Purpose |
|--------|---------|
| `scrapers.wikipedia_top_words` | Token frequency from Wikipedia page |
| `scrapers.related.related_words` | Synonyms via RelatedWords.org |
| `scrapers.news.google_news_top_words` | Keywords from Google News headlines |
| `scrapers.trends.interest_over_time` | PyTrends time-series curve |
| `scrapers.stock.fetch_stock_data` | OHLCV DataFrame via yfinance |
| `utils.rate_limit.rate_limiter` | Async token-bucket decorator |
| `utils.text.tokenise / remove_stopwords / most_common` | Text helpers used by scrapers |
| `utils.output.to_csv` | CSV writer/append utility |
| `ScraperContext.choose_ua()` | Random UA pick from custom list |

All of these are showcased in the notebook. 