"""Asynchronous token-bucket rate limiter.

Usage::

    from migration_package.utils.rate_limit import rate_limited

    @rate_limited(calls=5, period=1)  # 5 calls per second
    async def fetch(...):
        ...
"""
from __future__ import annotations

import asyncio
import time
from functools import wraps
from typing import Awaitable, Callable, TypeVar

T = TypeVar("T")

__all__ = ["rate_limited"]


def rate_limited(*, calls: int, period: float):
    """Decorator limiting *calls* within *period* seconds per coroutine group."""

    bucket = calls
    reset_at = time.monotonic() + period
    lock = asyncio.Lock()

    def decorator(fn: Callable[..., Awaitable[T]]):
        @wraps(fn)
        async def wrapper(*args, **kwargs) -> T:  # type: ignore[override]
            nonlocal bucket, reset_at
            async with lock:
                now = time.monotonic()
                if now >= reset_at:
                    bucket = calls
                    reset_at = now + period
                if bucket == 0:
                    sleep_for = reset_at - now
                    await asyncio.sleep(max(sleep_for, 0))
                    bucket = calls - 1
                    reset_at = time.monotonic() + period
                else:
                    bucket -= 1
            return await fn(*args, **kwargs)

        return wrapper

    return decorator 