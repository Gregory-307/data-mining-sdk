# Data-Mining SDK

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
| Google Web Search        | `scrapers.google_web_top_words`             | top-N tokens + bigrams         | Multi-step fall-back incl. headless Firefox     |
| Google Trends            | `scrapers.interest_over_time`               | `pandas.DataFrame`             | Async wrapper around *pytrends*                 |
| Yahoo Finance            | `scrapers.fetch_stock_data`                 | OHLCV `pandas.DataFrame`       | Async wrapper around *yfinance*                 |

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

Optional extras:

* `pip install -e ".[test]"`     – pytest & pytest-asyncio for the test-suite.
* `pip install -e ".[browser]"` – Selenium 4 + webdriver-manager for the headless-Firefox fall-back.

The SDK requires **Python ≥ 3.10**.

## Quick start

```python
import asyncio
from Data_Mining.scrapers import wikipedia_top_words
from Data_Mining.scrapers.base import ScraperContext


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
from Data_Mining.scrapers import (
    related_words,
    wikipedia_top_words,
    google_news_top_words,
    google_web_top_words,
)
from Data_Mining.scrapers.trends import interest_over_time
from Data_Mining.scrapers.stock import fetch_stock_data

# Shared runtime configuration object
from Data_Mining.scrapers.base import ScraperContext, gather_scrapers
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

## Browser fall-back (optional)
Some Google SERP requests are served as JS-only shells and will defeat pure HTTP scraping.  Setting `use_browser=True` in `ScraperContext` activates a **headless-Firefox** fallback that:
1. Downloads the latest compatible Geckodriver on first use (cached under `~/.wdm/`).
2. Launches Firefox in headless mode, navigates to the target URL, waits for `<body>`.

Make sure you have installed the *browser* extra or Selenium will stay disabled.

---

## Testing & Coverage

```bash
# run fast offline & network tests
python -m pytest tests -q

# run with coverage (pytest-cov)
python -m pytest tests --cov=. --cov-config=.coveragerc -q
```

Coverage is expected to be **95 %+** for the core logic; Selenium & legacy code paths are excluded.

---

## Contributing

1. **Fork** → **create branch** → **PR**.  PRs must pass CI (tests + coverage).
2. Respect *PEP 8*; run `black` / `ruff` locally before pushing.
3. Update or add tests for any new scraper.
4. Document the new feature in this README.

---

## Roadmap & Ideas
* Playwright-stealth driver to bypass bot detection while staying headless.
* Rotating residential proxy integration.
* Incremental cache layer to re-use HTTP responses during local experiments.
* Additional language support – stop-word list & tokeniser tweaks.

Comments, issues and PRs are welcome!

---

## License

MIT – see [LICENSE](LICENSE) for full text. 