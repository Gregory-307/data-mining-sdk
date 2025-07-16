# Web-Search SDK – Quick Reference Cheatsheet

> **Purpose**: Async Python toolkit for collecting publicly available web data for downstream analytics or trading pipelines.

---

## 🚀 Quick Start

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

**Expected output**: `['intelligence', 'ai', 'artificial', 'machine', 'learning', 'computer', 'systems', 'data', 'human', 'algorithm']`

---

## 📦 Installation

```bash
# Create environment
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate.bat     # Windows

# Install in editable mode
pip install -e .                 # Core package
pip install -e ".[browser]"      # + Playwright support
pip install -e ".[test]"         # + Testing tools
```

**Requirements**: Python ≥ 3.10

---

## 🔧 Core API Reference

### Available Scrapers

#### 🔍 Enhanced Search
| Source | Function | Output | Notes |
|--------|----------|--------|-------|
| **DuckDuckGo** | `search_and_parse(term, ctx)` | `{links, tokens, results}` | Enhanced with structured results |
| **DuckDuckGo** | `duckduckgo_search_enhanced(term, ctx)` | `{links, tokens, results}` | Direct enhanced search |

#### 📰 Article Extraction
| Source | Function | Output | Notes |
|--------|----------|--------|-------|
| **General** | `extract_article_content(url, ctx)` | `{title, content, summary, author, publish_date, source}` | Any URL, clean extraction |

#### 🔧 Basic Search (Legacy)
| Source | Function | Output | Notes |
|--------|----------|--------|-------|
| **DuckDuckGo** | `search_and_parse_basic(term, ctx)` | `{links, tokens}` | Legacy basic search |
| **Wikipedia** | `wikipedia_top_words(term, ctx)` | `list[str]` | Most reliable, fast |
| **RelatedWords** | `related_words(term, ctx)` | `list[str]` | Semantic expansion |
| **Google News** | `google_news_top_words(term, ctx)` | `list[str]` | RSS feed, lightweight |
| **Google Web** | `google_web_top_words(term, ctx)` | `list[str]` | May hit CAPTCHA |

### ScraperContext Configuration

```python
from web_search_sdk.scrapers.base import ScraperContext

# Basic HTTP-only
ctx_http = ScraperContext()

# Browser fallback (for CAPTCHAs/paywalls)
ctx_browser = ScraperContext(
    use_browser=True,
    browser_type="playwright_stealth",  # "selenium" | "playwright" | "playwright_stealth"
    debug=True,
    timeout=20.0,
    retries=2,
    proxy="http://user:pass@host:port",  # Optional
    user_agents=["Mozilla/5.0..."]       # Custom UA rotation
)
```

### Browser Engine Options

| Engine | Description | Use Case |
|--------|-------------|----------|
| `selenium` | Firefox via Geckodriver | Legacy, CI-friendly |
| `playwright` | Playwright-Firefox | Faster than Selenium |
| `playwright_stealth` | Chromium + anti-bot | Best for heavy CAPTCHA sites |

---

## 💡 Common Patterns

### 1. Basic Token Extraction

```python
from web_search_sdk.scrapers import wikipedia_top_words, related_words

# Single source
tokens = await wikipedia_top_words("bitcoin", ctx, top_n=20)

# Multiple sources
tasks = [
    wikipedia_top_words("bitcoin", ctx, top_n=10),
    related_words("bitcoin", ctx),
    google_news_top_words("bitcoin", ctx, top_n=10)
]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

### 2. Enhanced Search with Structured Results

```python
from web_search_sdk.scrapers.search import search_and_parse

result = await search_and_parse("bitcoin rally", ctx, top_n=10)
print("Links:", result["links"])
print("Tokens:", result["tokens"])
print("Structured Results:", result["results"])  # New!
```

### 3. Article Content Extraction

```python
from web_search_sdk.scrapers import extract_article_content

ctx = ScraperContext(use_browser=True, browser_type="playwright")

# Extract from any URL
article = await extract_article_content("https://www.cnbc.com/...", ctx)
print("Title:", article["title"])
print("Author:", article["author"])
print("Content:", article["content"][:500])  # First 500 chars
```

### 4. Legacy Basic Search

```python
from web_search_sdk.scrapers.search import search_and_parse_basic

result = await search_and_parse_basic("bitcoin rally", ctx, top_n=10)
print("Links:", result["links"])
print("Tokens:", result["tokens"])
```

### 5. Parallel Processing

```python
from web_search_sdk.scrapers.base import gather_scrapers
from web_search_sdk.scrapers.duckduckgo_web import _fetch_html, _parse_html

terms = ["bitcoin", "ethereum", "solana"]

def parse_wrapper(html: str, term: str, ctx):
    return _parse_html(html, top_n=5)

results = await gather_scrapers(
    terms, 
    fetch=_fetch_html, 
    parse=parse_wrapper, 
    ctx=ctx
)
```

---

## 🛠️ Utility Functions

### Output Helpers

```python
from web_search_sdk.utils.output import to_json, to_csv

# JSON output
data = {"term": "btc", "score": 0.87}
to_json(data, "out/latest.json")                    # Overwrite
to_json(data, "out/history.json", append=True)      # Append

# CSV output
rows = [{"term": "btc", "hits": 120}, {"term": "eth", "hits": 95}]
to_csv(rows, "out/stats.csv")                       # Create/overwrite
to_csv(rows, "out/stats.csv", append=True)          # Append rows
```

### Text Processing

```python
from web_search_sdk.utils.text import tokenise, remove_stopwords, most_common

raw = "Bitcoin's all-time high price sparks FOMO!"
tokens = tokenise(raw)                              # ['bitcoin', 'all', 'time', 'high', 'price', 'sparks', 'fomo']
clean = remove_stopwords(tokens)                    # ['bitcoin', 'time', 'high', 'price', 'sparks', 'fomo']
top = most_common(tokens, 3)                        # [('bitcoin', 1), ('time', 1), ('high', 1)]
```

### Rate Limiting

```python
from web_search_sdk.utils.rate_limit import rate_limited

@rate_limited(calls=2, period=1.0)  # 2 calls per second
async def my_scraper():
    # Your scraping logic here
    pass
```

---

## 🔍 Debugging & Troubleshooting

### Enable Debug Logging

```python
ctx = ScraperContext(debug=True)
# Shows HTTP requests, responses, browser actions
```

### Offline Mode (for testing)

```bash
export OFFLINE_MODE=1
# Uses fixture HTML instead of live requests
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Google CAPTCHA | Use `browser_type="playwright_stealth"` |
| Network timeouts | Increase `timeout` in ScraperContext |
| Rate limiting | Add delays or use `@rate_limited` decorator |
| Import errors | Run `pip install -e .` in repo root |

---

## 🧪 Testing

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=web_search_sdk --cov-report=term

# Specific test file
pytest tests/test_google_web.py
```

### Smoke Test

```bash
python smoke_test.py "openai"
# Tests all scrapers with a single term
```

### Demo Notebook

```bash
# Generate notebook
python scripts/convert_demo.py

# Run notebook
python scripts/run_demo.py --nb docs/demo_v2.ipynb
```

---

## 📚 Examples

### Complete Pipeline Example

```python
import asyncio
from web_search_sdk.scrapers import (
    search_and_parse, wikipedia_top_words, related_words
)
from web_search_sdk.scrapers.base import ScraperContext
from web_search_sdk.utils.output import to_json

async def analyze_term(term: str):
    ctx = ScraperContext(debug=False)
    
    # Gather data from multiple sources
    tasks = [
        search_and_parse(term, ctx, top_n=15),
        wikipedia_top_words(term, ctx, top_n=20),
        related_words(term, ctx)
    ]
    
    serp, wiki, related = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Save results
    results = {
        "term": term,
        "serp_links": serp["links"] if not isinstance(serp, Exception) else [],
        "serp_tokens": serp["tokens"] if not isinstance(serp, Exception) else [],
        "wiki_tokens": wiki if not isinstance(wiki, Exception) else [],
        "related_words": related if not isinstance(related, Exception) else []
    }
    
    to_json(results, f"out/{term}_analysis.json")
    return results

# Usage
asyncio.run(analyze_term("artificial intelligence"))
```

---

## 🔗 Related Documentation

- **README.md** - Full installation and API documentation
- **Progress_Report_v0.2.0.md** - Technical details and roadmap
- **docs/demo_v2.ipynb** - Interactive Jupyter notebook demo
- **scraper_overview.md** - Detailed code path documentation

---

## 📋 Version Info

- **Current Version**: 0.2.0
- **Python**: ≥ 3.10
- **Key Dependencies**: httpx, beautifulsoup4, playwright, selenium
- **License**: MIT 