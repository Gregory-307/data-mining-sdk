import asyncio
from typing import Dict, List, Any
from bs4 import BeautifulSoup
from .base import ScraperContext
from . import google_web as gw  # Google fallback
from . import duckduckgo_web as ddg  # Preferred engine


async def _fetch_serp_html(term: str, ctx: ScraperContext) -> str:
    """Fetch SERP HTML using DuckDuckGo first, Google as fallback."""
    # Primary: DuckDuckGo – far less likely to captcha or throttle.
    html = await ddg.fetch_serp_html(term, ctx)
    if html:
        return html

    # Fallback: Google (respecting ctx browser rules inside gw.fetch_serp_html)
    return await gw.fetch_serp_html(term, ctx)


def _validate_context(func_name: str, ctx: ScraperContext):
    """Validate context and warn users about suboptimal configurations."""
    if func_name.startswith("google_") and not ctx.use_browser:
        print(f"⚠️  Warning: {func_name} works better with browser context. Consider using ScraperContext(use_browser=True)")
    elif func_name.startswith("duckduckgo_") and ctx.use_browser:
        print(f"💡 Tip: {func_name} works fine with HTTP context (faster). Browser context is optional.")


async def search_and_parse_basic(term: str, ctx: ScraperContext = None, top_n: int = 10, return_links: bool = True) -> Dict[str, List[str]]:
    """Basic search and parse: Fetch SERP (DDG→Google), extract links & tokens (legacy)."""
    if ctx is None:
        ctx = ScraperContext(use_browser=False)  # HTTP context works fine for DuckDuckGo
    
    _validate_context("search_and_parse_basic", ctx)
    
    raw_html = await _fetch_serp_html(term, ctx)
    soup = BeautifulSoup(raw_html, 'html.parser')
    
    links = []
    tokens = []
    
    if return_links:
        links = [a['href'] for a in soup.find_all('a', href=True)][:top_n]
    
    # Simple token extraction (expand as needed per DRY)
    text = soup.get_text()
    tokens = text.split()[:top_n]  # Basic split; can integrate better parsing later
    
    return {'links': links, 'tokens': tokens} 


async def search_and_parse(term: str, ctx: ScraperContext = None, top_n: int = 10, return_links: bool = True) -> Dict[str, Any]:
    """Enhanced search and parse: Fetch SERP (DDG→Google), extract links, tokens & structured results."""
    if ctx is None:
        ctx = ScraperContext(use_browser=False)  # HTTP context works fine for DuckDuckGo
    
    _validate_context("search_and_parse", ctx)
    
    # Try enhanced DuckDuckGo first
    try:
        from .duckduckgo_enhanced import ddg_search_and_parse
        result = await ddg_search_and_parse(term, ctx, top_n)
        if result and result.get('results') and len(result['results']) > 1:
            return result
    except Exception as e:
        if ctx.debug:
            print(f"Enhanced DDG failed, falling back to basic: {e}")
    
    # Fallback to basic version
    return await search_and_parse_basic(term, ctx, top_n, return_links) 