"""Run with: uv run python examples/basic.py."""

from __future__ import annotations

import asyncio

from typed_concurrency import Channel, Group, go, thread


async def fetch_name() -> str:
    """Pretend to fetch a name."""
    await asyncio.sleep(0.01)
    return "Pac-Man"


def read_setting(name: str) -> str:
    """Pretend to make a blocking read."""
    return f"{name}=enabled"


async def producer(channel: Channel[int]) -> None:
    """Send a few values, then close the channel."""
    for value in range(3):
        await channel.send(value)
    await channel.close()


async def consumer(channel: Channel[int]) -> None:
    """Print channel values until normal closure."""
    async for value in channel:
        print(f"channel: {value}")


async def main() -> None:
    """Show one-off tasks, threads, and structured channel work."""
    name = go(fetch_name())
    setting = go(thread(read_setting, "music"))
    print(await name)
    print(await setting)

    channel = Channel[int](3)
    async with Group() as group:
        group << producer(channel)
        group << consumer(channel)


if __name__ == "__main__":
    asyncio.run(main())
