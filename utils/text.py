"""Text processing helpers."""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Iterable, List

# Load stopwords
_STOPWORDS_FILE = Path(__file__).resolve().parent.parent / "resources" / "stopwords.txt"
try:
    _STOPWORDS: set[str] = {
        l.strip().lower() for l in _STOPWORDS_FILE.read_text(encoding="utf-8").splitlines() if l.strip()
    }
except FileNotFoundError:
    _STOPWORDS = set()

TOKEN_RE = re.compile(r"[A-Za-z]{2,}")

__all__ = ["tokenise", "remove_stopwords", "most_common"]


def tokenise(text: str) -> List[str]:
    """Return lowercase word tokens from *text*."""
    return TOKEN_RE.findall(text.lower())


def remove_stopwords(tokens: Iterable[str]) -> List[str]:
    """Filter out stop-words from *tokens*."""
    return [t for t in tokens if t not in _STOPWORDS]


def most_common(tokens: Iterable[str], n: int) -> List[str]:
    """Return the *n* most common tokens after stop-word removal."""
    filtered = remove_stopwords(tokens)
    return [tok for tok, _ in Counter(filtered).most_common(n)] 