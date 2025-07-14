"""Shared headless-browser helper for web_search_sdk scrapers.

This module intentionally duplicates (rather than imports) the logic from
`migration_package.browser` so that **web_search_sdk remains self-contained**.

Public API:
    * _SEL_AVAILABLE – bool flag indicating whether Selenium stack is importable
    * fetch_html(term, url_fn, ctx) – async coroutine returning rendered HTML
"""
from __future__ import annotations

import asyncio
import random
from typing import Callable

from web_search_sdk.scrapers.base import ScraperContext, run_in_thread

# ---------------------------------------------------------------------------
# Lazy Playwright import guard (optional dependency)
# ---------------------------------------------------------------------------
try:
    import importlib
    _pl_mod = importlib.import_module("playwright.async_api")  # type: ignore
    _PW_AVAILABLE = True
except Exception:  # pragma: no cover – playwright not installed or unavailable
    _PW_AVAILABLE = False

# ---------------------------------------------------------------------------
# Lazy Selenium import guard (keeps dependency optional)
# ---------------------------------------------------------------------------
try:
    from selenium import webdriver  # type: ignore
    from selenium.webdriver.firefox.options import Options as _FxOptions  # type: ignore
    from selenium.webdriver.firefox.service import Service as _FxService  # type: ignore
    from selenium.webdriver.common.by import By  # type: ignore
    from selenium.webdriver.support import expected_conditions as EC  # type: ignore
    from selenium.webdriver.support.ui import WebDriverWait  # type: ignore
    from webdriver_manager.firefox import GeckoDriverManager  # type: ignore

    _SEL_AVAILABLE = True
except Exception:  # pragma: no cover – environment without Selenium stack
    _SEL_AVAILABLE = False

__all__ = ["_SEL_AVAILABLE", "fetch_html"]

# ---------------------------------------------------------------------------
# Internal blocking function (runs in a thread)
# ---------------------------------------------------------------------------

def _fetch_sync(term: str, url_fn: Callable[[str], str], ctx: ScraperContext) -> str:
    if not _SEL_AVAILABLE:
        if ctx.debug:
            print("[browser:DM] Selenium not available – skipping")
        return ""

    options = _FxOptions()
    options.add_argument("--headless")

    ua = ctx.choose_ua() or random.choice(ctx.user_agents or []) if ctx.user_agents else None
    if ua:
        options.set_preference("general.useragent.override", ua)

    try:
        service = _FxService(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=options)
    except Exception as exc:  # pragma: no cover – driver launch failed
        if ctx.debug:
            print(f"[browser:DM] Failed to launch Firefox driver: {exc}")
        return ""

    try:
        driver.set_page_load_timeout(ctx.timeout)
        url = url_fn(term)
        if ctx.debug:
            print(f"[browser:DM] GET {url}")
        driver.get(url)

        try:
            WebDriverWait(driver, min(10, int(ctx.timeout))).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except Exception:  # pragma: no cover – wait failed; continue anyway
            pass

        return driver.page_source or ""
    finally:
        try:
            driver.quit()
        except Exception:
            pass

# ---------------------------------------------------------------------------
# Public async API
# ---------------------------------------------------------------------------

async def fetch_html(term: str, url_fn: Callable[[str], str], ctx: ScraperContext) -> str:
    """Return rendered HTML via the configured headless browser backend.

    Backends:
        - Selenium (default): Firefox via geckodriver.
        - Playwright: ctx.browser_type == "playwright".

    Returns an empty string on any failure so callers can try alternative
    fallbacks without exceptions.
    """

    if ctx.browser_type == "playwright":
        if not _PW_AVAILABLE:
            if ctx.debug:
                print("[browser:PW] Playwright not available – skipping")
            return ""

        # Import locally to avoid import cost when not used
        from playwright.async_api import async_playwright  # type: ignore

        try:
            async with async_playwright() as p:
                browser = await p.firefox.launch(headless=True)
                page = await browser.new_page()
                url = url_fn(term)
                if ctx.debug:
                    print(f"[browser:PW] GET {url}")
                await page.goto(url, timeout=int(ctx.timeout * 1000))
                html = await page.content()
                await browser.close()
                return html or ""
        except Exception as exc:  # pragma: no cover – runtime error
            if ctx.debug:
                print(f"[browser:PW] Error: {exc}")
            return ""

    # Fallback to Selenium (threaded) for all other cases
    return await run_in_thread(_fetch_sync, term, url_fn, ctx) 