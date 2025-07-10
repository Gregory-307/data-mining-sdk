"""Scrapers included in the *Data-Mining* subset package.

Public helper functions:
    related_words(term, ctx=None, top_n=20)
    wikipedia_top_words(term, ctx=None, top_n=20)
    google_news_top_words(term, ctx=None, top_n=20)
"""

from .related import related_words  # noqa: F401
from .wikipedia import wikipedia_top_words  # noqa: F401
from .news import google_news_top_words  # noqa: F401

__all__ = [
    "related_words",
    "wikipedia_top_words",
    "google_news_top_words",
    "google_web_top_words",
]

from .google_web import google_web_top_words  # noqa: F401 