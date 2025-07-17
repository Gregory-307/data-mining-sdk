#!/usr/bin/env python3
"""
Test script to check which search functions work with HTTP vs browser contexts.
"""

import asyncio
from web_search_sdk.scrapers.search import search_and_parse, search_and_parse_basic
from web_search_sdk.scrapers.duckduckgo_enhanced import duckduckgo_search_enhanced
from web_search_sdk.scrapers.duckduckgo_web import duckduckgo_top_words
from web_search_sdk.scrapers.google_web import google_web_top_words
from web_search_sdk.scrapers.base import ScraperContext
import json

def print_result_summary(func_name, result):
    if isinstance(result, dict):
        print(json.dumps(result, indent=2)[:1000])  # Print up to 1000 chars
        if not result or (isinstance(result, dict) and not any(result.values())):
            print("   ❌ FAILED: Empty or malformed result.")
            return False
        return True
    elif isinstance(result, list):
        print(result)
        if not result:
            print("   ❌ FAILED: Empty list result.")
            return False
        return True
    else:
        print(result)
        print("   ❌ FAILED: Unexpected result type.")
        return False

async def test_function_with_context(func_name, func, ctx, test_term="bitcoin"):
    print(f"\n🔍 Testing {func_name} with {ctx.use_browser and 'BROWSER' or 'HTTP'} context...")
    try:
        if func_name in ['search_and_parse', 'search_and_parse_basic', 'duckduckgo_search_enhanced']:
            result = await func(test_term, ctx, top_n=2)
        else:
            result = await func(test_term, ctx, top_n=5)
        print_result_summary(func_name, result)
        return True
    except Exception as e:
        print(f"   ❌ FAILED: {func_name} failed with {ctx.use_browser and 'browser' or 'HTTP'} context")
        print(f"      Error: {str(e)[:100]}...")
        return False

async def main():
    print("🧪 TESTING SEARCH FUNCTION CONTEXT COMPATIBILITY")
    print("=" * 60)
    
    ctx_http = ScraperContext(use_browser=False, debug=False)
    ctx_browser = ScraperContext(use_browser=True, browser_type="playwright_stealth", debug=False)
    
    functions = [
        ("search_and_parse", search_and_parse),
        ("search_and_parse_basic", search_and_parse_basic),
        ("duckduckgo_search_enhanced", duckduckgo_search_enhanced),
        ("duckduckgo_top_words", duckduckgo_top_words),
        ("google_web_top_words", google_web_top_words),
    ]
    
    results = {}
    
    for func_name, func in functions:
        print(f"\n{'='*20} {func_name.upper()} {'='*20}")
        http_works = await test_function_with_context(func_name, func, ctx_http)
        browser_works = await test_function_with_context(func_name, func, ctx_browser)
        results[func_name] = {
            'http_works': http_works,
            'browser_works': browser_works
        }
    
    print(f"\n{'='*60}")
    print("📊 SUMMARY")
    print("=" * 60)
    print("Function                | HTTP | Browser | Recommendation")
    print("-" * 60)
    for func_name, result in results.items():
        http_status = "✅" if result['http_works'] else "❌"
        browser_status = "✅" if result['browser_works'] else "❌"
        if result['http_works'] and result['browser_works']:
            recommendation = "HTTP (faster)"
        elif result['browser_works']:
            recommendation = "Browser only"
        elif result['http_works']:
            recommendation = "HTTP only"
        else:
            recommendation = "BROKEN"
        print(f"{func_name:<25} | {http_status:<4} | {browser_status:<7} | {recommendation}")

if __name__ == "__main__":
    asyncio.run(main()) 