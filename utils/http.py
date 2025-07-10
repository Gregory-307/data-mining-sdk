"""HTTP helper utilities built around httpx.AsyncClient.

Goals
-----
1. Centralise retry/back-off logic so individual scrapers stay lean.
2. Provide random User-Agent rotation with an optional custom list.
3. Support optional proxy configuration.

All helpers are *functional*; no classes are exposed.
"""
from __future__ import annotations

import asyncio
import random
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, List, Optional

import httpx
from .logging import get_logger

logger = get_logger("utils.http")

__all__ = ["get_async_client", "fetch_text"]

# ---------------------------------------------------------------------------
# Default UA list (very small; caller can supply custom list)
# ---------------------------------------------------------------------------

_DEFAULT_UA = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]


@asynccontextmanager
async def get_async_client(
    *,
    timeout: float = 20.0,
    proxy: str | None = None,
    headers: Dict[str, str] | None = None,
    ca_file: str | None = None,
) -> AsyncIterator[httpx.AsyncClient]:
    """Yield a configured `httpx.AsyncClient`.

    Parameters
    ----------
    timeout:  connection/read timeout seconds (applies to both connect & read)
    proxy:    optional proxy URL  (e.g. "http://user:pass@proxy:port")
    headers:  base headers applied to every request (e.g. Accept-Language)
    """
    client = httpx.AsyncClient(
        timeout=timeout,
        proxies=proxy,
        headers=headers,
        follow_redirects=True,
        verify=ca_file or True,
    )
    try:
        yield client
    finally:
        await client.aclose()


async def fetch_text(
    url: str,
    *,
    retries: int = 2,
    timeout: float = 20.0,
    proxy: str | None = None,
    headers: Dict[str, str] | None = None,
    user_agents: List[str] | None = None,
    ca_file: str | None = None,
) -> str:
    """Fetch a URL and return `response.text` with retry/backoff.

    Automatically injects a random UA if provided.
    """
    headers = headers.copy() if headers else {}
    if user_agents is None:
        user_agents = _DEFAULT_UA
    headers.setdefault("User-Agent", random.choice(user_agents))

    for attempt in range(retries + 1):
        try:
            logger.debug("fetch", url=url, attempt=attempt)
            async with get_async_client(timeout=timeout, proxy=proxy, headers=headers, ca_file=ca_file) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                return resp.text
        except Exception as exc:
            logger.warning("fetch_error", url=url, attempt=attempt, error=str(exc))
            if attempt >= retries:
                raise
            # Exponential backoff: 0.5, 1.0, 2.0 …
            await asyncio.sleep(0.5 * 2**attempt)

    # Should never reach here
    raise RuntimeError("fetch_text: exceeded retries without exception") 