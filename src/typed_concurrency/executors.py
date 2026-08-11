"""Adapters for running synchronous work from asyncio."""

from __future__ import annotations

import asyncio
import functools
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")

_process_pool = ProcessPoolExecutor()


async def thread(fn: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
    """Run blocking work in asyncio's shared thread pool."""
    return await asyncio.to_thread(fn, *args, **kwargs)


async def process(fn: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
    """Run CPU-bound work in the shared process pool.

    Functions, arguments, and returned values must be pickle-compatible.
    """
    call = functools.partial(fn, *args, **kwargs)
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_process_pool, call)
