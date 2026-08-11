# typed-concurrency

[![PyPI](https://img.shields.io/pypi/v/typed-concurrency)](https://pypi.org/project/typed-concurrency/)
[![CI](https://github.com/0xveya/typed-concurrency/actions/workflows/ci.yml/badge.svg)](https://github.com/0xveya/typed-concurrency/actions/workflows/ci.yml)

**[View typed-concurrency on PyPI](https://pypi.org/project/typed-concurrency/)**

Typed structured concurrency with Go-ish ergonomics on top of `asyncio`.

```bash
uv add typed-concurrency
```

```python
from typed_concurrency import Channel, Group, go, process, thread
```

Python 3.11 or newer is required. There are no dependencies beyond
[typed-errs](https://github.com/0xveya/typed-errs), which supplies the explicit
`Option` value used when a channel closes.

## Tasks and groups

`go()` is deliberately boring: it creates an `asyncio.Task[T]` without losing
the coroutine's result type.

```python
user = go(fetch_user())
config = go(fetch_config())

# Other async work happens here.
name: str = await user
settings: Config = await config
```

`Group` is a compact wrapper around `asyncio.TaskGroup`; it keeps the standard
structured-concurrency cancellation and exception behaviour.

```python
async with Group() as group:
    users = group.go(fetch_users())
    config = group.go(fetch_config())

# Both tasks have completed here.
print(users.result())
print(config.result())
```

When a result is intentionally irrelevant, `<<` makes that clear:

```python
async with Group() as group:
    group << report_progress()
    group << refresh_cache()
```

## Channels

`Channel[T]` is a buffered async queue with close semantics. `recv()` and
`await channel` return `Option[T]`: queued values are `Some(value)`, and a
closed, drained channel returns `Nothing()`. This avoids a nullable receive
protocol while keeping normal closure distinct from an error.

```python
from typed_concurrency import Channel, recv
from typed_errs import Some

channel = Channel[int](16)
await channel.send(42)

received = await channel.recv()
if isinstance(received, Some):
    print(received.value)

await channel.close()
```

Channels are async iterable, which is usually the pleasant producer/consumer
form:

```python
async def producer(channel: Channel[int]) -> None:
    for value in range(10):
        await channel.send(value)
    await channel.close()


async def consumer(channel: Channel[int]) -> None:
    async for value in channel:
        print(value)


async with Group() as group:
    channel = Channel[int](10)
    group << producer(channel)
    group << consumer(channel)
```

`await (channel << value)` sends and `await (channel >> recv)` receives. The
compact `await channel` receive form is also available. They are sugar over
`send()` and `recv()`, which remain the canonical API.

```python
from typed_concurrency import recv

await (channel << 42)
value = await (channel >> recv)
```

`capacity=0` follows `asyncio.Queue` and means an unbounded buffer. It is not a
Go-style rendezvous channel.

## Blocking and CPU work

`thread()` runs a blocking callable using `asyncio.to_thread()`. `process()`
runs pickle-compatible CPU-bound work in a shared process pool.

```python
data = await thread(read_file, path)
result = await process(expensive_parse, data)
```

Use `process()` only for substantial CPU work: process startup and argument
serialization have a real cost.

## Examples and development

Run the small end-to-end example with `uv run python examples/basic.py`.

## Ecosystem

- [typed-errs](https://github.com/0xveya/typed-errs) provides the `Option`
  values used by channel receives after normal closure.
- [python-crimes](https://github.com/0xveya/python-crimes) provides the
  complementary pipe, deferred-cleanup, and matching helpers.
- [typed-file-io](https://github.com/0xveya/typed-file-io) supplies typed file
  I/O that combines naturally with `thread()` for blocking reads and writes.

## Dependencies

- [typed-errs](https://pypi.org/project/typed-errs/)

## Use and contributions

This is a personal library, but it is not private or locked to my projects.
You may use it in general Python work and in 42 projects under the MIT license;
just follow the rules that apply to your campus and assignment.

Contributions are welcome: open an issue or send a pull request. I do not care
whether a contribution is written by hand, AI-assisted, or generated another
way; I care about whether it is correct, tested, understandable, and a good
fit. Because this is opinionated personal infrastructure, pull requests are
reviewed selectively and are likely to be rejected unless they clearly improve
the library without making it harder to maintain.

## Development and release

Run `mise run check` for linting, type checks, tests, and a package build.
Every push to `master` publishes a unique `0.0.<CI run>` ZeroVer version through
PyPI Trusted Publishing. `mise run publish` remains available for manual
publishing.

## License

MIT
