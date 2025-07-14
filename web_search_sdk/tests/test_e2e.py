import pytest
import asyncio
from web_search_sdk.scrapers.search import search_and_parse
from web_search_sdk.scrapers.paywall import fetch_bloomberg
from web_search_sdk.scrapers.base import ScraperContext
from web_search_sdk import scrapers as sc

HTML_SERP = """
<html><body>
  <a href=\"http://example.com\">link</a>
  <p>bitcoin rally analysis fundamentals bullish</p>
</body></html>
"""

HTML_ARTICLE = """
<html><body><article><h1>Headline</h1><p>Full article about BTC fundamentals.</p></article></body></html>
"""

@pytest.mark.asyncio
async def test_e2e_search_and_paywall(monkeypatch):
    # Patch Google SERP fetch
    async def _dummy_serp(term, ctx):
        return HTML_SERP
    monkeypatch.setattr(sc.google_web, "fetch_serp_html", _dummy_serp)
    # Patch paywall quick fetch
    async def _dummy_article(url, ctx):
        return HTML_ARTICLE
    monkeypatch.setattr(sc.paywall, "_quick_http_get", _dummy_article)

    ctx = ScraperContext(use_browser=False)
    search_res, article_text = await asyncio.gather(
        search_and_parse("btc rally", ctx, top_n=5),
        fetch_bloomberg("http://example.com/article", ctx),
    )

    assert search_res["links"] == ["http://example.com"]
    assert "bitcoin" in " ".join(search_res["tokens"]).lower()
    assert "Full article" in article_text 