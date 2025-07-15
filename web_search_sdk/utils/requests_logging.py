from __future__ import annotations
"""Patch the *requests* library to emit structured logs for every outgoing
HTTP request/response when the environment variable ``DEBUG_SCRAPERS`` is set.

This mirrors the behaviour in ``utils.http_logging`` for httpx so that *all*
paths (async and legacy sync) are traceable from the same log stream.
"""

import os
from typing import Any, Dict

import requests

from .logging import get_logger

if os.getenv("DEBUG_SCRAPERS") in {"1", "true", "True"} and not getattr(requests, "_patched_for_logging", False):
    logger = get_logger("requests")

    _orig_request = requests.Session.request  # type: ignore[attr-defined]

    def _patched_request(self: requests.Session, method: str, url: str, *args: Any, **kwargs: Any):  # type: ignore[override]
        headers: Dict[str, str] | None = kwargs.get("headers")
        logger.info("request", method=method, url=url, headers=headers or {})

        resp: requests.Response = _orig_request(self, method, url, *args, **kwargs)

        body_len = len(resp.content) if resp.content is not None else 0
        log_kwargs: Dict[str, Any] = {
            "status": resp.status_code,
            "url": resp.url,
            "headers": dict(resp.headers),
            "body_len": body_len,
        }

        if os.getenv("DEBUG_TRACE") in {"1", "true", "True"}:
            preview = resp.text[:1024]
            log_kwargs["preview"] = preview

        logger.info("response", **log_kwargs)
        return resp

    requests.Session.request = _patched_request  # type: ignore[assignment]
    requests._patched_for_logging = True  # type: ignore[attr-defined] 