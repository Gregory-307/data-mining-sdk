from __future__ import annotations

"""Runtime monkey-patch that logs every httpx.AsyncClient request/response
   when the environment variable DEBUG_SCRAPERS=1 is set.

   The patch is intentionally simple: we wrap ``AsyncClient.send`` so *all*
   code paths—whether the client is created via our helpers or directly—are
   captured without touching every call-site.

   Logged fields: HTTP method, full URL, status code, request headers, first
   200 bytes of the response body.  Output goes through our structlog helper
   so users can filter/redirect as needed.
"""
import os
import asyncio
from types import MethodType

import httpx

from .logging import get_logger

if os.getenv("DEBUG_SCRAPERS") not in {"1", "true", "True"}:
    # No-op when debugging disabled.
    DEBUG_ENABLED = False
else:
    DEBUG_ENABLED = True

# Apply patch once ---------------------------------------------------------------------------
if DEBUG_ENABLED and not getattr(httpx, "_patched_for_logging", False):
    logger = get_logger("httpx")

    _orig_send = httpx.AsyncClient.send

    async def _patched_send(self: httpx.AsyncClient, request: httpx.Request, *args, **kwargs):  # type: ignore[override]
        logger.info(
            "request",
            method=request.method,
            url=str(request.url),
            headers=dict(request.headers),
        )
        response = await _orig_send(self, request, *args, **kwargs)

        # read() consumes the stream only once – cache content, then assign back
        content = await response.aread()
        preview = content[:200]
        try:
            preview_text = preview.decode("utf-8", errors="replace")
        except Exception:
            preview_text = str(preview)

        logger.info(
            "response",
            status=response.status_code,
            url=str(response.request.url),
            headers=dict(response.headers),
            preview=preview_text,
        )

        # Restore body for downstream consumers
        response._content = content  # type: ignore[attr-defined]
        response._content_consumed = True  # type: ignore[attr-defined]
        return response

    # Override class attribute directly; Python binds functions to instances automatically.
    httpx.AsyncClient.send = _patched_send  # type: ignore[assignment]
    httpx._patched_for_logging = True  # type: ignore[attr-defined] 