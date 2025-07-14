"""Structured logging helper using structlog."""
# If structlog is unavailable (e.g., minimal runtime env) we fall back to a
# no-op shim that preserves the public API (get_logger) so callers continue
# to work without installing the extra dependency.

import logging
import os

try:
    import structlog  # type: ignore
except ModuleNotFoundError:  # pragma: no cover – optional dependency
    import types

    _shim_mod = types.ModuleType("structlog.processors")

    def _noop_processor(*_a, **_kw):
        return lambda logger, name, event_dict: event_dict  # type: ignore

    _shim_mod.TimeStamper = lambda *a, **kw: _noop_processor  # type: ignore
    _shim_mod.JSONRenderer = lambda *a, **kw: _noop_processor  # type: ignore

    _stdlib_mod = types.ModuleType("structlog.stdlib")

    class _LoggerFactory:  # noqa: D401 – simple shim
        def __call__(self, *args, **kwargs):  # type: ignore
            return logging.getLogger("shim")

    _stdlib_mod.LoggerFactory = _LoggerFactory

    class _StructlogShim(types.ModuleType):
        def get_logger(self, name=None):  # type: ignore
            return logging.getLogger(name)

        def configure(self, *args, **kwargs):  # type: ignore
            # No-op configuration in shim environment
            return None

        processors = _shim_mod  # type: ignore
        stdlib = _stdlib_mod  # type: ignore

    import sys

    structlog = _StructlogShim("structlog")  # type: ignore
    sys.modules["structlog"] = structlog
    sys.modules["structlog.processors"] = _shim_mod
    sys.modules["structlog.stdlib"] = _stdlib_mod

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