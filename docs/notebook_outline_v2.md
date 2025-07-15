# Notebook V2 – Detailed Outline

_This outline maps **one markdown header → one code cell**.  Each bullet below becomes a markdown cell followed by its corresponding code cell._

---
## 0. Title & Overview
- Markdown: Project banner, purpose of SDK, notebook goals, link to README.
- No code.

## 1. Environment & Installation (Skippable)
- Markdown:
  - Explain editable install (`pip install -e .[browser]`).
  - Warn readers they can skip if running inside repo dev env.
- Code:
  - Shell magic to install package & Playwright _only if_ `!pip show web-search-sdk` is empty. Use `os.getenv("SKIP_INSTALL")` guard.

## 2. Quick Smoke Test
- Markdown: Verify installation & version.
- Code: Print `web_search_sdk.__version__` and run `smoke_test.py`.

## 3. ScraperContext Cheatsheet
- Markdown: Explain context params with table.
- Code: Instantiate 3 contexts (HTTP, Selenium, Playwright).

## 4. Core Scrapers (Primary flow)
### 4.1 DuckDuckGo Top Words
- Markdown: Why DDG first, expected output.
- Code: `await duckduckgo_top_words(...)` ➜ print top 15.

### 4.2 Wikipedia Top Words
- Similar structure.

### 4.3 RelatedWords Synonyms
- Similar structure.

### 4.4 Google News RSS Keywords
- Similar structure.

## 5. Optional Google SERP Fallback
- Markdown: Heavy, may CAPTCHA; skip unless `RUN_GOOGLE=1` env var.
- Code: Guarded by env var.

## 6. Paywall Article Retrieval
- Markdown: Demonstrates browser usage; show trimmed article body.
- Code: Fetch Bloomberg fixture if offline.

## 7. Twitter Login & Sample Scrape (NEW)
- Markdown: Explain requirement for env vars `TW_EMAIL`, `TW_PASS`. Bold warning.
- Code: If vars missing ➜ print "Skipped". Else use Playwright to log in and fetch user timeline HTML snippet.

## 8. Output Utilities
- Markdown & code for `to_json`, `to_csv`.

## 9. Text Helpers Showcase
- Markdown & code for `tokenise`, `remove_stopwords`, `most_common`.

## 10. Rate-Limit Decorator Example
- Markdown & short code.

## 11. Parallel Scraping Example
- Markdown & `gather_scrapers` demo.

## 12. Closing Notes & Next Steps
- Markdown summary, links to API docs, how to contribute.

---

### Notes for Implementation
1. All optional heavy cells are wrapped in env guards.
2. Each code cell prints **trimmed** outputs to keep notebook compact.
3. Use fixtures (`tests/fixtures/...`) when `OFFLINE_MODE=1`.
4. Total execution target < 3 minutes in CI.

---
_Outline authored for PLAN-03_ 