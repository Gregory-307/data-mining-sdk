#!/usr/bin/env python3
"""Debug script to test imports that are failing in Colab."""

import sys
import importlib

def test_imports():
    print("Testing imports...")
    
    # Test basic module import
    try:
        import web_search_sdk.scrapers.news
        print("✅ web_search_sdk.scrapers.news imported successfully")
    except Exception as e:
        print(f"❌ web_search_sdk.scrapers.news failed: {e}")
    
    # Test specific function imports
    functions_to_test = [
        "google_web_top_words",
        "wikipedia_top_words", 
        "wikipedia",
        "related_words",
        "google_news_top_words",
        "google_news",
        "google_news_raw",
        "ddg_search_and_parse",
        "extract_article_content"
    ]
    
    for func_name in functions_to_test:
        try:
            exec(f"from web_search_sdk.scrapers import {func_name}")
            print(f"✅ {func_name} imported successfully")
        except Exception as e:
            print(f"❌ {func_name} failed: {e}")
    
    # Test what's actually in the scrapers module
    print("\nChecking what's available in web_search_sdk.scrapers:")
    try:
        import web_search_sdk.scrapers as scrapers
        print(f"Available: {dir(scrapers)}")
    except Exception as e:
        print(f"Failed to inspect scrapers module: {e}")

if __name__ == "__main__":
    test_imports() 