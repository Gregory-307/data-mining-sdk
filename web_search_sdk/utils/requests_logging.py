from __future__ import annotations
import warnings

"""DEPRECATED: Requests logging functionality has been merged into utils.logging.

This module is kept for backward compatibility only. Import from utils.logging instead.
"""

warnings.warn(
    "requests_logging module is deprecated and will be removed in a future version. "
    "Import from utils.logging instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from the main logging module
from .logging import get_logger

__all__ = ["get_logger"] 