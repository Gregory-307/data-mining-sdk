"""Unit test (HTML parsing only) for google_web_top_words.

This test feeds a static HTML snippet into the internal _fetch_html monkeypatch;
it verifies token extraction and stop-word removal.  No live network calls.
"""

import pytest

from Data_Mining.scrapers import google_web_top_words
from Data_Mining.scrapers import google_web as gw
from Data_Mining.scrapers.base import ScraperContext
from Data_Mining.tests.conftest import show

HTML_SNIPPET = """
<html><body>
  <div class="yuRUbf"><a><h3>Python releases new version</h3></a></div>
  <div class="IsZvec">The Python Software Foundation announced...</div>
  <div class="yuRUbf"><a><h3>Learn programming with Python tutorials</h3></a></div>
  <div class="IsZvec">Comprehensive guide for beginners.</div>
</body></html>
"""


@pytest.mark.asyncio
async def test_google_web_html_parse(monkeypatch):
    """Parser extracts tokens from static HTML snippet."""

    async def fake_fetch(term: str, ctx: ScraperContext):  # noqa: D401
        return HTML_SNIPPET

    # Monkey-patch internal fetch to avoid network
    monkeypatch.setattr(gw, "_fetch_html", fake_fetch)

    ctx = ScraperContext(debug=False)
    words = await google_web_top_words("python", ctx=ctx, top_n=5)

    assert words, "Token list should not be empty"
    assert "python" in words[0:2]

    show("UNIT", "google_web_top_words (HTML)", "Input  : python", f"Output : {words}") 