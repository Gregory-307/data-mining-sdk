import asyncio
from typing import Dict, List
from bs4 import BeautifulSoup
from .base import ScraperContext
from . import google_web as gw  # Reuse existing helper functions

async def search_and_parse(term: str, ctx: ScraperContext, top_n: int = 10, return_links: bool = True) -> Dict[str, List[str]]:
    """Async search and parse: Fetch from Google, extract links/text."""
    raw_html = await gw._fetch_html(term, ctx)  # Reuse internal fetch
    soup = BeautifulSoup(raw_html, 'html.parser')
    
    links = []
    tokens = []
    
    if return_links:
        links = [a['href'] for a in soup.find_all('a', href=True)][:top_n]
    
    # Simple token extraction (expand as needed per DRY)
    text = soup.get_text()
    tokens = text.split()[:top_n]  # Basic split; can integrate better parsing later
    
    return {'links': links, 'tokens': tokens} 