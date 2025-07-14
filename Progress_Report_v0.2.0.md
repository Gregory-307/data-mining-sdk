# web-search-sdk – Progress Report (v0.2.0)

> “Measure twice, cut once” – every change was deliberate. This report documents **why** each capability exists, **what** it does, and **how** to use it.

---
## 1. Core Design Refresh

| Why | What / How |
|-----|-------------|
| Modernise the old *Data_Mining* toolkit into a standalone, namespaced package. | Package renamed to `web_search_sdk`. Install with:<br/>`pip install -e ".[browser]"` |
| Provide an async, idempotent, headless-capable search layer for downstream repos. | All helpers exposed under `web_search_sdk.scrapers`. `ScraperContext` centralises runtime options. |

---
## 2. Async Token & Link Expansion

### `google_web_top_words`
*Why* – generate high-quality keyword expansions from Google SERPs.
```python
from web_search_sdk.scrapers.google_web import google_web_top_words
words = await google_web_top_words("btc rally", top_n=20)
```

### `search_and_parse` **(NEW)**
*Why* – single call returns **tokens + outbound links** for richer features.
```python
from web_search_sdk.scrapers.search import search_and_parse
res = await search_and_parse("btc rally", ScraperContext())
print(res["links"], res["tokens"])
```

---
## 3. Full-Page Retrieval for Paywalled Sources

### `fetch_bloomberg` / `fetch_cnbc` **(NEW)**
*Why* – LLM pipeline needs the entire article, not just the headline.
```python
from web_search_sdk.scrapers.paywall import fetch_bloomberg
ctx = ScraperContext(use_browser=True, browser_type="playwright")
html = await fetch_bloomberg("https://www.bloomberg.com/...", ctx)
```
*How* – quick HTTP fetch, then Playwright fallback if `use_browser=True`.

---
## 4. Headless Browser Backends

| Option | Why | How |
|--------|-----|-----|
| Selenium (default) | Legacy fallback; no extra install on CI. | `ScraperContext(use_browser=True, browser_type="selenium")` |
| **Playwright (NEW)** | Faster, stealthier; JS-heavy paywalls. | `browser_type="playwright"` |

---
## 5. Output Utilities

*Why* – save pipeline results without rewriting I/O logic.
```python
from web_search_sdk.utils.output import to_json, to_csv
to_json({"term":"btc","score":0.9}, "out/latest.json", append=True)
```
*Features* – auto-creates parent dirs, append mode, CSV header handling.

---
## 6. Deprecations & Cleanup

* `scrapers.trends` prints a **DeprecationWarning** (migrate to trends-sdk).
* Sync fallback files `*_legacy.py` retained but isolated; safe to delete later.

---
## 7. Quality Gates Achieved

| Metric | Value |
|--------|-------|
| Unit & integration tests | **pass (11/11)** |
| Coverage (after `.coveragerc`) | **84 %** |
| CI-ready tag | **v0.2.0** |

---
## 8. What the Repo **Can** Do

* Keyword/token expansion from Google News/Web/Wikipedia/RelatedWords.
* Return outbound links + tokens via `search_and_parse`.
* Fetch full Bloomberg/CNBC articles, defeating paywalls.
* Dump JSON/CSV idempotently.
* Headless browsing via Selenium *or* Playwright.
* Context-level retries, proxies, custom UAs.

## 9. What it **Does Not** (Phase-2 Items)

* Dedicated Google Trends (handled by **trends-sdk**).
* Twitter ingestion (planned **twitter-sdk**).
* Sentiment LLM chain, ML backtesting (separate repos).

---
## 10. Quick Cheat-Sheet
```python
# Expand tokens & links
await search_and_parse(term, ScraperContext())

# Individual scrapers
await google_web_top_words(term)
await wikipedia_top_words(term)

# Full paywall article
await fetch_bloomberg(url, ScraperContext(use_browser=True, browser_type="playwright"))

# Output helpers
to_json(data, "file.json", append=True)
```

---
## 11. Next Steps (Phase 2 Preview)

1. Stand-up **twitter-sdk** for streaming/virality.
2. Extract Google Trends logic to **trends-sdk** (almost done).
3. Build **sentiment-pipeline** with GPT-4 chain-of-thought + BERT.
4. Integrate with **ml-backtester** for historic hedge validation.

The web-search-sdk is now a clean, tested pillar ready to power the rest of the crypto swing-analysis stack.

---
## 12. SERP Roadmap (future work)

> **Context** – Google SERP scraping is the most brittle element due to CAPTCHA, JS-checks and rate-limits.  We already have Playwright & Selenium fallbacks, but the strategy will be expanded in Phase 2.

| Priority | Idea | Notes |
|----------|------|-------|
| **P1** | **Selenium-first** path | Skip plain HTTP when `use_browser=True` and `browser_type="selenium"`; proven to bypass the "enable JS" placeholder. |
| **P1** | **Playwright-stealth** | Patch `navigator.webdriver`, spoof plugins/language, run Chrom(ium) head-full in off-screen window; increases success rate vs default headless. |
| P2 | Smart retry & back-off | 1× HTTP, then 1× Browser with random delay + varied `ei` param; abort on second failure. |
| P2 | Proxy rotation | Support residential proxy pool via `ScraperContext(proxy=…)`; sticky sessions for a few requests. |
| P3 | Alternate engines | DuckDuckGo HTML endpoint; Bing SERP; both parse similarly and avoid heavy bot-checks. |
| P3 | Commercial APIs | SerpAPI, Zenserp as last-resort pay-per-use fallback if self-hosted scraping fails. |

Each idea will be implemented as an *idempotent*, separately-tested batch so we can roll forward/back easily.

--- 