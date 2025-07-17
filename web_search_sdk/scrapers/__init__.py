"""Scrapers included in the *Data-Mining* subset package.

Public helper functions:
    related_words(term, ctx=None, top_n=20)
    wikipedia_top_words(term, ctx=None, top_n=20)
    google_news_top_words(term, ctx=None, top_n=20)
    extract_article_content(url, ctx=None)  # NEW: General article extraction
    ddg_search_and_parse(term, ctx=None, top_n=10)  # NEW: Enhanced DuckDuckGo search
    ddg_search_raw(term, ctx=None)  # NEW: Raw DuckDuckGo HTML
    google_news(term, ctx=None, top_n=20)  # NEW: Structured Google News
    google_news_raw(term, ctx=None)  # NEW: Raw Google News RSS
    wikipedia(term, ctx=None, top_n=100)  # NEW: Structured Wikipedia
    wikipedia_raw(term, ctx=None)  # NEW: Raw Wikipedia HTML
"""

from .related import related_words  # noqa: F401
from .wikipedia import wikipedia_top_words, wikipedia, wikipedia_raw  # noqa: F401
from .news import google_news_top_words, google_news, google_news_raw  # noqa: F401
from .article_extractor import extract_article_content  # noqa: F401
from .duckduckgo_enhanced import ddg_search_and_parse, ddg_search_raw  # noqa: F401
from .search import search_and_parse  # noqa: F401

__all__ = [
    "related_words",
    "wikipedia_top_words",
    "wikipedia",
    "wikipedia_raw",
    "google_news_top_words",
    "google_news",
    "google_news_raw",
    "google_web_top_words",
    "duckduckgo_top_words",
    "extract_article_content",
    "ddg_search_and_parse",
    "ddg_search_raw",
    "search_and_parse",
]

# Legacy imports with deprecation warnings
import warnings

def _import_with_warning(module_name: str, function_name: str):
    """Import a function from a deprecated module with a warning."""
    warnings.warn(
        f"{module_name} module is deprecated and will be removed in a future version. "
        f"Use the enhanced modules instead.",
        DeprecationWarning,
        stacklevel=3
    )
    if module_name == "google_web":
        from .google_web import google_web_top_words
        return google_web_top_words
    elif module_name == "duckduckgo_web":
        from .duckduckgo_web import duckduckgo_top_words
        return duckduckgo_top_words
    else:
        raise ImportError(f"Unknown deprecated module: {module_name}")

# Import deprecated functions with warnings
google_web_top_words = _import_with_warning("google_web", "google_web_top_words")
duckduckgo_top_words = _import_with_warning("duckduckgo_web", "duckduckgo_top_words") 