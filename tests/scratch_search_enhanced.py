#!/usr/bin/env python3
"""Test script for the enhanced search_and_parse function."""

import asyncio
import json
from web_search_sdk.scrapers.search import search_and_parse, search_and_parse_basic
from web_search_sdk.scrapers.base import ScraperContext

async def test_search_functions():
    ctx = ScraperContext(debug=True, timeout=30.0)
    term = "bitcoin rally"
    
    print("🧪 Testing enhanced search_and_parse...")
    enhanced_result = await search_and_parse(term, ctx, top_n=5)
    print("Enhanced result keys:", list(enhanced_result.keys()))
    print("Enhanced result structure:", json.dumps(enhanced_result, indent=2, ensure_ascii=False))
    
    print("\n🧪 Testing basic search_and_parse_basic...")
    basic_result = await search_and_parse_basic(term, ctx, top_n=5)
    print("Basic result keys:", list(basic_result.keys()))
    print("Basic result structure:", json.dumps(basic_result, indent=2, ensure_ascii=False))
    
    # Verify both functions work
    assert "links" in enhanced_result
    assert "tokens" in enhanced_result
    assert "links" in basic_result
    assert "tokens" in basic_result
    print("✅ Both functions work correctly!")

if __name__ == "__main__":
    asyncio.run(test_search_functions()) 