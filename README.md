# typed-concurrency

Typed structured concurrency with Go-ish ergonomics on top of Python's
`asyncio`.

```bash
uv add typed-concurrency
```

## Status

This repository is scaffolded but intentionally contains no implementation
yet. The planned public API is:

```python
from typed_concurrency import Channel, Group, go, process, thread
```

- `go()` creates a typed `asyncio.Task[T]`.
- `Group` wraps `asyncio.TaskGroup` with a typed `.go()` and `<<` fire-and-forget
  syntax.
- `Channel[T]` provides buffered communication, close semantics, and async
  iteration.
- `thread()` and `process()` adapt blocking and CPU-bound callables for async
  code.

The first version will keep the scope deliberately small. Likely later
additions are `select()`, a true rendezvous channel, and cancellation/timeouts.

## Development

Run `mise run check` for linting, type checks, tests, and a package build.
The package requires Python 3.10 or newer and has no runtime dependencies.

## License

MIT
