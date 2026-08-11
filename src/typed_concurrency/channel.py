"""Buffered async channels with explicit close semantics."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Coroutine, Generator
from typing import Any, Generic, TypeVar, cast

from typed_errs import Nothing, Option, Some

T = TypeVar("T")

_CLOSED = object()


class _Receive:
    """Private type for the public ``recv`` operator marker."""


recv = _Receive()
RECV = recv


class ChannelClosed(Exception):
    """Raised when a value is sent after its channel has closed."""


class Channel(Generic[T]):
    """A buffered channel where receiving after close yields ``Nothing``.

    ``capacity=0`` uses asyncio's unbounded queue semantics. It is not a Go
    rendezvous channel.
    """

    def __init__(self, capacity: int = 0) -> None:
        """Create a channel with an optional bounded buffer.

        Args:
            capacity: Maximum buffered values. Zero means unbounded.

        Raises:
            ValueError: If ``capacity`` is negative.
        """
        if capacity < 0:
            raise ValueError("Channel capacity cannot be negative")
        self._queue: asyncio.Queue[object] = asyncio.Queue(maxsize=capacity)
        self._closed = False

    async def send(self, value: T) -> None:
        """Put a value into the channel.

        Raises:
            ChannelClosed: If the channel was already closed.
        """
        if self._closed:
            raise ChannelClosed("Cannot send to a closed channel")
        await self._queue.put(value)

    async def recv(self) -> Option[T]:
        """Receive the next value, or ``Nothing`` after the channel closes."""
        value = await self._queue.get()
        if value is _CLOSED:
            await self._queue.put(_CLOSED)
            return Nothing()
        return Some(cast(T, value))

    async def close(self) -> None:
        """Close the channel after queued values have been received.

        Calling close repeatedly is harmless. A bounded, full channel waits
        until there is room to enqueue its close marker.
        """
        if self._closed:
            return
        self._closed = True
        await self._queue.put(_CLOSED)

    def __lshift__(self, value: T) -> Coroutine[Any, Any, None]:
        """Return the awaitable form of :meth:`send`."""
        return self.send(value)

    def __await__(self) -> Generator[Any, None, Option[T]]:
        """Await the channel as shorthand for :meth:`recv`."""
        return self.recv().__await__()

    def __rshift__(self, marker: _Receive) -> Coroutine[Any, Any, Option[T]]:
        """Return the Go-ish ``await (channel >> recv)`` receive form.

        Args:
            marker: The exported ``recv`` marker.

        Raises:
            TypeError: If an object other than ``recv`` is used.
        """
        if marker is not recv:
            raise TypeError("Channel receive uses `channel >> recv`")
        return self.recv()

    async def __aiter__(self) -> AsyncIterator[T]:
        """Yield values until the channel closes."""
        while True:
            value = await self.recv()
            if isinstance(value, Nothing):
                return
            yield value.value
