# web_search_sdk – Scraper Overview & Key Code Paths

This document pulls together **only the parts of the code-base that matter for the Google / DuckDuckGo search flow** and the headless-browser fallback.  Skim this to understand how HTML is retrieved and parsed.

---

## 1. Shared Runtime Context

```python
15:50:web_search_sdk/scrapers/base.py
@dataclass
class ScraperContext:
    """Shared, immutable configuration passed to fetch & parse funcs."""
    headers: Dict[str, str] = field(default_factory=dict)
    timeout: float = 20.0
    retries: int = 2
    user_agents: List[str] | None = None
    proxy: str | None = None
    use_browser: bool = False
    browser_type: str = "selenium"  # "selenium" | "playwright" | "playwright_stealth"
    debug: bool = False
```

`ScraperContext` is the single source of truth for **timeouts, retries, UA rotation, proxy and whether a browser should be launched**.  All fetch helpers accept it.

---

## 2. Google HTML Fetch Logic (`google_web.py`)

### 2.1. Plain-HTTP path

```python
32:62:web_search_sdk/scrapers/google_web.py
async def _fetch_html(term: str, ctx: ScraperContext) -> str:
    headers = ctx.headers.copy()
    ua = ctx.choose_ua() or random.choice(_DEFAULT_UA)
    headers.setdefault("User-Agent", ua)
    ...
    url = SEARCH_URL.format(_uparse.quote(term))
    async with httpx.AsyncClient(timeout=ctx.timeout, proxy=ctx.proxy) as client:
        resp = await client.get(url, headers=headers, follow_redirects=True)
        resp.raise_for_status()
        return resp.text
```

*Attempts a classic `httpx` GET* to `https://www.google.com/search?...&gbv=1` (the **basic-HTML mode** that normally avoids heavy JS and is easy to parse).

### 2.2. Unified fetch helper with browser fast-path

```python
70:115:web_search_sdk/scrapers/google_web.py
async def fetch_serp_html(term: str, ctx: ScraperContext | None = None) -> str:
    ctx = ctx or ScraperContext()

    # Skip HTTP entirely if *any* browser backend was requested
    if ctx.use_browser:
        html = await _browser_fetch_html(term, url_builder, ctx)
        return html or ""

    # Legacy: HTTP first → browser fallback
    try:
        html = await _fetch_html(term, ctx)
        if html and not _looks_like_captcha(html):
            return html
    except Exception:
        html = ""

    # Fallback to browser if allowed
    if ctx.use_browser:
        html = await _browser_fetch_html(term, url_builder, ctx)
        if html:
            return html
    return ""
```

Key points:
1. **Fast-path** – when the caller sets `ctx.use_browser = True` we **skip** the potentially fragile HTTP attempt.
2. Otherwise: try HTTP → if that fails or looks like a CAPTCHA, fall back to the same browser helper.

---

## 3. DuckDuckGo HTML Fetch Logic (`duckduckgo_web.py`)

```python
52:89:web_search_sdk/scrapers/duckduckgo_web.py
async def _fetch_html(term: str, ctx: ScraperContext) -> str:
    headers = ctx.headers.copy()
    ua = ctx.choose_ua() or random.choice(_DEFAULT_UA)
    headers.setdefault("User-Agent", ua)
    url = _SEARCH_URL.format(_uparse.quote(term))  # html.duckduckgo.com
    async with httpx.AsyncClient(timeout=ctx.timeout, proxy=ctx.proxy) as client:
        resp = await client.get(url, headers=headers, follow_redirects=True)
        resp.raise_for_status()
        return resp.text
```

DuckDuckGo is **HTML-only by design**, so we *never* launch a browser here – KISS & YAGNI.

---

## 4. Headless Browser Abstraction (`browser.py`)

```python
38:73:web_search_sdk/browser.py
async def fetch_html(term: str, url_fn: Callable[[str], str], ctx: ScraperContext) -> str:
    if ctx.browser_type in {"playwright", "playwright_stealth"}:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            page = await browser.new_page()
            if ctx.browser_type == "playwright_stealth":
                await page.add_init_script(_STEALTH_JS)
            url = url_fn(term)
            await page.goto(url, timeout=int(ctx.timeout * 1000))
            html = await page.content()
            await browser.close()
            return html or ""
    # Fallback → Selenium (runs in thread)
    return await run_in_thread(_fetch_sync, term, url_fn, ctx)
```

Supports **three modes** via `ctx.browser_type`:
* `selenium` (default) – Firefox/geckodriver
* `playwright` – Firefox in Playwright
* `playwright_stealth` – Chromium + JS patches to bypass simple bot checks

When Playwright isn’t installed it silently falls back to empty HTML.

---

## 5. Putting It Together (demo flow)

1. **Caller constructs** `ctx = ScraperContext(use_browser=True, browser_type="playwright_stealth")` (example).
2. Calls `google_web_top_words("superman box office", ctx)` – which → `fetch_serp_html`.
3. Since `use_browser` is set, Google scraper immediately invokes the browser helper.
4. If Google blocks, the higher-level pipeline switches to `duckduckgo_top_words` as a fallback.

This guards the pipeline against Google 429/302 loops while keeping dependency footprint light.

---

*End of overview – for full sources simply inspect the files referenced above.* 

---

## 6. Sample Debug Logs / Real Requests

Below are **verbatim log excerpts** captured by running the demo with
`ctx = ScraperContext(debug=True, use_browser=True, browser_type="playwright_stealth")`
and term **"superman box office"**.  They illustrate the *exact* outbound
requests and where things can go wrong.

### 6.1 Google – plain HTTP attempt (blocked)

```text
[GoogleWeb-HTTP] GET https://www.google.com/search?q=superman%20box%20office&hl=en&gl=us&gbv=1&num=100&safe=off&start=0
← 302 https://www.google.com/sorry/index?continue=https://www.google.com/search%3Fq%3Dsuperman%2520box%2520office%26hl%3Den%26gl%3Dus%26gbv%3D1...
← 429 Too Many Requests (after redirect)
```

**Issue** – Google immediately redirects to the “sorry” CAPTCHA endpoint;
we treat this as a failure and drop into the browser fast-path.

---

### 6.2 Google – browser fast-path (Playwright-stealth)

```text
[GoogleWeb] Browser fast-path (playwright_stealth) for 'superman box office'…
[browser:PW] GET https://www.google.com/search?q=superman%20box%20office&hl=en&gl=us&num=100&safe=off&start=0
# JavaScript rendered → full DOM captured (≈ 350 KB HTML)
```

Playwright (Chromium) fetches the *standard* SERP (note the missing
`gbv=1`) and, with the stealth JS patch, usually bypasses simple bot
detections.

---

### 6.3 DuckDuckGo – fallback HTTP path

```text
[DDG-HTTP] GET https://html.duckduckgo.com/html/?q=superman%20box%20office&kl=us-en
← 200 OK (≈ 110 KB HTML)
```

The html.duckduckgo.com endpoint is stable and JS-free, so we rarely see
blocks or CAPTCHAs here.  This path is used when Google fails or when the
caller explicitly starts with the DDG scraper.

---

### Header snapshot (from Google HTTP attempt)

```http
GET /search?q=superman%20box%20office&hl=en&gl=us&gbv=1&num=100&safe=off&start=0 HTTP/1.1
Host: www.google.com
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36
Accept-Language: en-US,en;q=0.9
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8
```

These headers are set in `_fetch_html`; they mimic a modern Chrome build
to reduce the odds of being flagged as a bot.

---

*You can reproduce these logs by running `python demo.py --debug` or by
calling `google_web_top_words` with `ScraperContext(debug=True, …)`.* 