"""Scrapers included in the *Data-Mining* subset package.

Public helper functions:
    related_words(term, ctx=None, top_n=20)
    wikipedia_top_words(term, ctx=None, top_n=20)
    google_news_top_words(term, ctx=None, top_n=20)
    extract_article_content(url, ctx=None)  # NEW: General article extraction
"""

from .related import related_words  # noqa: F401
from .wikipedia import wikipedia_top_words  # noqa: F401
from .news import google_news_top_words  # noqa: F401
from .article_extractor import extract_article_content  # noqa: F401
from .duckduckgo_enhanced import duckduckgo_search_enhanced  # noqa: F401
from .search import search_and_parse  # noqa: F401

__all__ = [
    "related_words",
    "wikipedia_top_words",
    "google_news_top_words",
    "google_web_top_words",
    "duckduckgo_top_words",
    "extract_article_content",  # NEW
    "duckduckgo_search_enhanced",  # NEW
    "search_and_parse",  # NEW
]

from .google_web import google_web_top_words  # noqa: F401
from .duckduckgo_web import duckduckgo_top_words  # noqa: F401 