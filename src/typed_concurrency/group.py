"""A typed, compact facade over :class:`asyncio.TaskGroup`."""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from types import TracebackType
from typing import Any, Self, TypeVar, cast

T = TypeVar("T")


class Group:
    """Run related tasks with asyncio's structured-concurrency semantics."""

    def __init__(self) -> None:
        """Create a group, which must be entered before adding tasks."""
        self._group = asyncio.TaskGroup()
        self._entered = False

    async def __aenter__(self) -> Self:
        """Enter the underlying task group.

        Returns:
            This group, ready to accept tasks.
        """
        await self._group.__aenter__()
        self._entered = True
        return self

    async def __aexit__(
        self,
        exc_type: object,
        exc: object,
        tb: object,
    ) -> bool:
        """Wait for tasks and propagate TaskGroup failures unchanged."""
        try:
            await self._group.__aexit__(
                cast(type[BaseException], exc_type),
                cast(BaseException, exc),
                cast(TracebackType, tb),
            )
        finally:
            self._entered = False
        return False

    def go(self, coro: Coroutine[Any, Any, T]) -> asyncio.Task[T]:
        """Schedule a typed task within this group.

        Args:
            coro: Coroutine whose lifetime belongs to this group.

        Returns:
            A task typed with the coroutine's result.

        Raises:
            RuntimeError: If the group is not currently entered.
        """
        if not self._entered:
            raise RuntimeError("Group must be entered before scheduling tasks")
        return self._group.create_task(coro)

    def __lshift__(self, coro: Coroutine[Any, Any, object]) -> Self:
        """Schedule a task when its result is intentionally discarded."""
        self.go(coro)
        return self
