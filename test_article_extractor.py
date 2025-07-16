#!/usr/bin/env python3
"""Test script for the new extract_article_content function."""

import asyncio
import json
from web_search_sdk.scrapers.article_extractor import extract_article_content
from web_search_sdk.scrapers.base import ScraperContext

# Test URL from our TODO list
CNBC_URL = "https://www.cnbc.com/2025/07/14/bitcoin-hits-new-all-time-high-above-120000-fueled-by-etf-inflows-crypto.html"

async def test_article_extraction():
    """Test the extract_article_content function on the CNBC article."""
    
    print("🧪 Testing extract_article_content function...")
    print(f"📰 URL: {CNBC_URL}")
    print("-" * 80)
    
    # Create context with debug enabled
    ctx = ScraperContext(debug=True, timeout=30.0)
    
    try:
        # Extract article content
        result = await extract_article_content(CNBC_URL, ctx)
        
        # Pretty print the results
        print("✅ Extraction successful!")
        print("\n📋 Results:")
        print(f"Title: {result.get('title', 'N/A')}")
        print(f"Author: {result.get('author', 'N/A')}")
        print(f"Date: {result.get('publish_date', 'N/A')}")
        print(f"Source: {result.get('source', 'N/A')}")
        print(f"URL: {result.get('url', 'N/A')}")
        
        print(f"\n📝 Summary ({len(result.get('summary', ''))} chars):")
        print(result.get('summary', 'No summary available'))
        
        print(f"\n📄 Content ({len(result.get('content', ''))} chars):")
        content = result.get('content', '')
        if content:
            # Show first 500 characters
            preview = content[:500] + "..." if len(content) > 500 else content
            print(preview)
        else:
            print("No content extracted")
        
        # Check for errors
        if 'error' in result:
            print(f"\n❌ Error: {result['error']}")
        
        # Validate expected format
        expected_keys = ['title', 'content', 'summary', 'publish_date', 'author', 'source', 'url']
        missing_keys = [key for key in expected_keys if key not in result]
        if missing_keys:
            print(f"\n⚠️  Missing keys: {missing_keys}")
        else:
            print(f"\n✅ All expected keys present")
        
        # Save results to file for inspection
        with open('test_article_results.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Results saved to test_article_results.json")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_article_extraction()) 