from __future__ import annotations
import warnings

"""DEPRECATED: Rate limiting functionality has been merged into utils.http.

This module is kept for backward compatibility only. Import from utils.http instead.
"""

warnings.warn(
    "rate_limit module is deprecated and will be removed in a future version. "
    "Import from utils.http instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from the main http module
from .http import rate_limited

__all__ = ["rate_limited"] 