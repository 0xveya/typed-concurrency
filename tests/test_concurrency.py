"""Behaviour tests for the public concurrency helpers."""

from __future__ import annotations

import asyncio
from typing import cast

import pytest
from typed_errs import Nothing, Some

from typed_concurrency import Channel, ChannelClosed, Group, go, process, thread


def test_go_preserves_a_task_result() -> None:
    """go schedules a coroutine on the running event loop."""

    async def fetch() -> str:
        return "hello"

    async def run() -> str:
        return await go(fetch())

    assert asyncio.run(run()) == "hello"


def test_group_returns_completed_typed_tasks() -> None:
    """Tasks returned by Group.go are complete after the scope exits."""

    async def one() -> int:
        return 1

    async def two() -> str:
        return "two"

    async def run() -> tuple[int, str]:
        tasks: list[object] = []
        async with Group() as group:
            tasks.append(group.go(one()))
            tasks.append(group.go(two()))
        one_task = cast(asyncio.Task[int], tasks[0])
        two_task = cast(asyncio.Task[str], tasks[1])
        return one_task.result(), two_task.result()

    assert asyncio.run(run()) == (1, "two")


def test_group_rejects_tasks_outside_its_scope() -> None:
    """A group cannot create unstructured tasks."""

    async def work() -> None:
        return None

    group = Group()
    coroutine = work()
    with pytest.raises(RuntimeError, match="must be entered"):
        group.go(coroutine)
    coroutine.close()


def test_group_left_shift_discards_results() -> None:
    """The operator schedules work while returning the same group."""
    seen: list[int] = []

    async def worker(value: int) -> int:
        seen.append(value)
        return value

    async def run() -> None:
        async with Group() as group:
            assert (group << worker(1)) is group
            _ = group << worker(2)

    asyncio.run(run())
    assert seen == [1, 2]


def test_channel_returns_some_then_nothing_after_close() -> None:
    """Close drains queued values before receivers observe normal absence."""

    async def run() -> tuple[Some[int], Nothing]:
        channel = Channel[int](2)
        await channel.send(42)
        await channel.close()
        first = await channel.recv()
        second = await channel.recv()
        assert isinstance(first, Some)
        assert isinstance(second, Nothing)
        return first, second

    first, second = asyncio.run(run())
    assert first.value == 42
    assert second.is_none()


def test_channel_async_iteration_and_operators() -> None:
    """Operators are sugar over send and receive; iteration ends on close."""

    async def run() -> tuple[Some[int], list[int]]:
        channel = Channel[int]()
        await (channel << 1)
        first = await channel
        assert isinstance(first, Some)
        await (channel << 2)
        await (channel << 3)
        await channel.close()
        return first, [value async for value in channel]

    first, remaining = asyncio.run(run())
    assert first.value == 1
    assert remaining == [2, 3]


def test_channel_refuses_send_after_close() -> None:
    """A closed channel cannot accept another value."""

    async def run() -> None:
        channel = Channel[int]()
        await channel.close()
        with pytest.raises(ChannelClosed):
            await channel.send(1)

    asyncio.run(run())


def test_channel_rejects_negative_capacity() -> None:
    """Negative queue sizes are not meaningful channel capacities."""
    with pytest.raises(ValueError, match="cannot be negative"):
        Channel[int](-1)


def test_thread_runs_blocking_callable() -> None:
    """thread returns a blocking callable's result."""
    assert asyncio.run(thread(lambda value: value + 1, 41)) == 42


def test_process_runs_pickleable_callable() -> None:
    """process delegates substantial pickleable work to its pool."""
    assert asyncio.run(process(sum, [1, 2, 3])) == 6
