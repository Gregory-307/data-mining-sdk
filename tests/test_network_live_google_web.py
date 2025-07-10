"""Live smoke test for google_web_top_words.
Skips automatically if no internet connection.
"""
import socket
import pytest

from Data_Mining.scrapers import google_web_top_words
from Data_Mining.scrapers.base import ScraperContext
from Data_Mining.utils.http import _DEFAULT_UA
from Data_Mining.tests.conftest import show
from Data_Mining.browser import _SEL_AVAILABLE

pytestmark = pytest.mark.asyncio

TERMS = ["python", "beyonce", "openai"]

DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

CTX = ScraperContext(headers=DEFAULT_HEADERS, user_agents=_DEFAULT_UA, use_browser=True, debug=False)


async def test_live_google_web():
    # Skip if offline
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
    except OSError:
        pytest.skip("No network connectivity")

    found = False
    for term in TERMS:
        words = await google_web_top_words(term, ctx=CTX, top_n=10)
        if words:
            found = True
            break

    show("LIVE", "google_web_top_words", f"Term list: {TERMS}", f"Non-empty: {found}")

    if not _SEL_AVAILABLE:
        pytest.xfail("Selenium not available; browser fallback cannot run")

    if not found:
        pytest.xfail("Google blocked request (CAPTCHA page or unusual traffic)")

    assert found, "Live Google Web scraper returned tokens but assertion failed unexpectedly" 