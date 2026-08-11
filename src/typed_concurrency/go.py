"""Small typed helpers for creating asyncio tasks."""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any, TypeVar

T = TypeVar("T")


def go(coro: Coroutine[Any, Any, T]) -> asyncio.Task[T]:
    """Schedule a coroutine and preserve its result type.

    Args:
        coro: Coroutine to run on the current event loop.

    Returns:
        The scheduled task, typed with the coroutine's result.
    """
    return asyncio.create_task(coro)
