"""Structured logging helper using structlog."""
import logging, os

import structlog

__all__ = ["get_logger"]


# Configure on first import only
_handler = logging.StreamHandler()
_formatter = logging.Formatter("%(message)s")
_handler.setFormatter(_formatter)
root = logging.getLogger()
if not root.handlers:
    root.addHandler(_handler)
    root.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Optional file output when DEBUG_SCRAPERS or LOG_SCRAPERS env vars are set
# ---------------------------------------------------------------------------

_log_path = None

# Explicit path wins
if os.getenv("LOG_SCRAPERS"):
    _log_path = os.getenv("LOG_SCRAPERS")
# Otherwise use default file when debug mode active
elif os.getenv("DEBUG_SCRAPERS") in {"1", "true", "True"}:
    _log_path = "scraper_debug.log"

if _log_path:
    try:
        _file_handler = logging.FileHandler(_log_path, encoding="utf-8")
        _file_handler.setFormatter(_formatter)
        root.addHandler(_file_handler)
    except Exception as _e:  # pragma: no cover – file system errors shouldn’t crash app
        # Fallback silently; logs will still appear on stdout.
        root.error("file_handler_error", path=_log_path, error=str(_e))

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)


def get_logger(name: str | None = None):
    return structlog.get_logger(name) 