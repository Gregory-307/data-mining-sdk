import pytest
import asyncio

from web_search_sdk.scrapers.search import search_and_parse
from web_search_sdk.scrapers.base import ScraperContext

HTML_SNIPPET = """
<html><body>
    <a href=\"http://example.com\">Example</a>
    <p>Bitcoin rally news today</p>
</body></html>
"""

@pytest.mark.asyncio
async def test_search_and_parse(monkeypatch):

    async def _dummy_serp(term, ctx):
        return HTML_SNIPPET

    from web_search_sdk.scrapers import google_web as gw
    monkeypatch.setattr(gw, "fetch_serp_html", _dummy_serp)

    ctx = ScraperContext()
    result = await search_and_parse("bitcoin", ctx, top_n=5)

    assert "links" in result and "tokens" in result
    assert result["links"] == ["http://example.com"]
    assert len(result["tokens"]) > 0 