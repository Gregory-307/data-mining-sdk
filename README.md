# Data-Mining SDK

**Async-friendly scraper & keyword-analysis toolkit** distilled from the original *Stock-Algorithm* monorepo.

---

### Why use this SDK?
*   **Unified API** – every scraper exposes a single `async def` with the same signature and shares a common `ScraperContext`.
*   **Resilient by design** – automatic retries, UA rotation, proxy support and multiple fall-back strategies (legacy HTML, Selenium, etc.).
*   **Zero boilerplate** – functional helpers, no heavyweight classes to subclass.
*   **Batteries included** – built-in stop-word list, token utilities, Google Trends, stock data via *yfinance*, structured logging with *structlog*.
*   **100 % self-contained** – no imports from the legacy repo, ready to drop into any codebase.

> *The SDK is ideal for quick prototyping, keyword expansion, due-diligence research, and market-sentiment experiments.*

---

## Feature Matrix

| Source / Provider        | Public Helper                               | Typical Output                 | Notes                                           |
|--------------------------|---------------------------------------------|--------------------------------|-------------------------------------------------|
| RelatedWords.org         | `scrapers.related_words`                    | `list[str]`                    | JSON API with HTML & Selenium fall-backs        |
| Wikipedia                | `scrapers.wikipedia_top_words`              | top-N tokens                   | Legacy Newspaper3k → raw HTML → JSON API        |
| Google News RSS          | `scrapers.google_news_top_words`            | top-N tokens                   | No CAPTCHA risk; RSS is lightweight             |
| Google Web Search        | `scrapers.google_web_top_words`             | top-N tokens + bigrams         | Multi-step fall-back incl. headless Firefox     |
| Google Trends            | `scrapers.interest_over_time`               | `pandas.DataFrame`             | Async wrapper around *pytrends*                 |
| Yahoo Finance            | `scrapers.fetch_stock_data`                 | OHLCV `pandas.DataFrame`       | Async wrapper around *yfinance*                 |

For details see the [API Reference](#api-reference).

---

## Installation

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

---

## Quick Example

```python
# examples/basic_usage.py
import asyncio
from Data_Mining.scrapers import google_web_top_words
from Data_Mining.scrapers.base import ScraperContext

async def main():
    ctx = ScraperContext(use_browser=False, debug=True)
    words = await google_web_top_words("openai", ctx=ctx, top_n=10)
    print(words)

asyncio.run(main())
```

> Want an even quicker test?  Run the built-in **smoke-test** straight from the repo root:
>
> ```bash
> python smoke_test.py "openai"
> ```
> 
> It works **before or after** installation thanks to a self-contained import shim.

---

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

---

## Architecture Diagram

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

> The diagram shows how each high-level scraper communicates with shared utilities and, where necessary, optional third-party libraries. The dashed edge marks the Selenium fallback path that only engages when `use_browser=True`.

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