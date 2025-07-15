import asyncio
from typing import Dict, List
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


async def search_and_parse(term: str, ctx: ScraperContext, top_n: int = 10, return_links: bool = True) -> Dict[str, List[str]]:
    """Async search and parse: Fetch SERP (DDG→Google), extract links & tokens."""
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