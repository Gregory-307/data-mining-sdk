#!/usr/bin/env python3
"""Test script for the new duckduckgo_search_enhanced function."""

import asyncio
import json
from web_search_sdk.scrapers import duckduckgo_search_enhanced
from web_search_sdk.scrapers.base import ScraperContext

SEARCH_TERMS = [
    "bitcoin rally",
    "artificial intelligence",
    "climate change",
    "python programming"
]

async def test_ddg_enhanced():
    ctx = ScraperContext(debug=True, timeout=30.0)
    for term in SEARCH_TERMS:
        print(f"\n🧪 Testing: {term}")
        result = await duckduckgo_search_enhanced(term, ctx, top_n=5)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        # Save to file for inspection
        with open(f'test_ddg_enhanced_{term.replace(" ", "_")}.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        # Check structure
        assert "links" in result and isinstance(result["links"], list)
        assert "tokens" in result and isinstance(result["tokens"], list)
        assert "results" in result and isinstance(result["results"], list)
        print(f"✅ Structure OK for '{term}'")

if __name__ == "__main__":
    asyncio.run(test_ddg_enhanced()) 