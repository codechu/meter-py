```text
        .--:--.          c o d e c h u
       /  12   \           ╔═════════╗
      |9   ●---3|  meter   ║ 00:42.7 ║   ETA  03:18
       \   6   /           ╚═════════╝
        '-----'          ─── tick · tock · tick · tock ───
```

[![PyPI](https://img.shields.io/pypi/v/codechu-meter.svg)](https://pypi.org/project/codechu-meter/)
[![Python](https://img.shields.io/pypi/pyversions/codechu-meter.svg)](https://pypi.org/project/codechu-meter/)
[![CI](https://github.com/codechu/meter-py/actions/workflows/ci.yml/badge.svg)](https://github.com/codechu/meter-py/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

> *Stopwatch, rolling-rate, and ETA — time things without lying about them.*

# codechu-meter

Stdlib-only measurement primitives — stopwatch, rolling-window rate
estimator, ETA predictor — extracted from the [Disk Cleaner](https://github.com/codechu/disk-cleaner)
toolchain. Zero dependencies. Python 3.10+.

## Install

```bash
pip install codechu-meter
```

## API

### `Stopwatch`

```python
from codechu_meter import Stopwatch

with Stopwatch() as sw:
    do_work()
print(sw.elapsed)  # → float seconds

# Manual form
sw = Stopwatch().start()
do_work()
sw.stop()
print(sw.elapsed)
```

Formatting is up to you. If you want pretty output, pair with
[`codechu-fmt`](https://github.com/codechu/fmt-py):

```python
from codechu_fmt import format_duration
print(format_duration(sw.elapsed))  # → '1m 30s'
```

### `RateEstimator`

```python
from codechu_meter import RateEstimator

re = RateEstimator(window_seconds=1.0, unit="bytes")
for chunk in stream:
    re.observe(len(chunk))
print(re.rate())   # float per-second
```

`unit` is just an attribute — it never affects the numeric `rate()`.
Use it as a label when formatting:

```python
from codechu_fmt import format_rate
print(format_rate(re.rate(), unit=re.unit))  # → '1.2 MB/s'
```

### `ETAEstimator`

```python
from codechu_meter import ETAEstimator

eta = ETAEstimator(total=1000, mode="ema", alpha=0.3)
for current in progress:
    eta.update(current)
    remaining = eta.eta()  # float seconds or None
```

`mode='linear'` (default) uses overall throughput since
construction. `mode='ema'` blends an exponential moving average
of recent throughput for smoother numbers on bursty workloads.
The `alpha` parameter (default `0.3`) controls EMA reactivity:
higher values weight recent samples more heavily.

`eta()` returns `None` until at least two updates with measurable
elapsed time and positive progress.

### `Counter` *(v0.3.0+)*

Thread-safe int counter. `inc` / `dec` / `reset` / `.value` are all
guarded by a `threading.Lock`.

```python
from codechu_meter import Counter

inflight = Counter()
inflight.inc()
try:
    serve(req)
finally:
    inflight.dec()
print(inflight.value)
```

### `Histogram` *(v0.3.0+)*

Bucketed distribution counter. Upper edges are inclusive; values
above the largest edge fall into a `math.inf` overflow bucket.
Thread-safe.

```python
from codechu_meter import Histogram

hist = Histogram([0.01, 0.05, 0.1, 0.5, 1.0])
for r in requests:
    hist.observe(r.latency_seconds)
print(hist.counts, hist.total)
```

### `PercentileEstimator` *(v0.3.0+)*

Streaming p50 / p95 / p99 via Vitter's reservoir sampling
(`max_samples` capped). Pure stdlib — no numpy. Thread-safe.

```python
from codechu_meter import PercentileEstimator

pe = PercentileEstimator(max_samples=5_000)
for r in requests:
    pe.observe(r.latency_seconds)
print(pe.p50, pe.p95, pe.p99)
```

### `Stopwatch` named sections *(v0.3.0+)*

`Stopwatch.section(name)` accumulates sub-timings into
`Stopwatch.sections`. Same name re-entered → values add. Not
thread-safe; use one Stopwatch per thread.

```python
sw = Stopwatch().start()
with sw.section("parse"):
    parse(buf)
with sw.section("emit"):
    emit(result)
sw.stop()
print(sw.sections)  # → {"parse": 0.012, "emit": 0.004}
```

## Design

- **Zero dependencies.** Stdlib only.
- **Monotonic clock.** Wall-clock jumps don't break timing.
- **No formatting coupling.** Numeric primitives only; pair with
  `codechu-fmt` (or roll your own) for display strings.
- **Defensive.** Zero progress, zero elapsed, NaN, and negative rates
  never raise.

## Migrating from 0.1.x

`__str__` methods were removed in 0.2.0. Replace `print(sw)` /
`str(re)` / `str(eta)` with explicit calls:

```python
# Before (0.1.x)
print(sw)
print(re)
print(eta)

# After (0.2.x)
from codechu_fmt import format_duration, format_rate
print(format_duration(sw.elapsed))
print(format_rate(re.rate(), unit=re.unit))
v = eta.eta()
print(format_duration(v) if v is not None else "?")
```

## Tests

```bash
pip install -e ".[dev]"
pytest -q
```

Coverage gate: ≥90 %. Tests drive time via monkeypatching
`time.monotonic` for deterministic assertions.

## Documentation

- [API reference](docs/API.md) — every public symbol, parameter,
  return value, and exception.
- [Migration guide](docs/MIGRATION.md) — 0.1.x → 0.2.0 (breaking
  `__str__` removal, new `alpha` parameter, dropped `codechu-fmt`
  dependency).
- [Recipes](docs/RECIPES.md) — patterns for timing blocks, tracking
  download speed, computing ETA, tuning EMA `alpha`, and pairing with
  `codechu-fmt`.

## Codechu family

Companion libraries from the Codechu Python ecosystem:

| Library | Purpose |
|---------|---------|
| [codechu-fmt](https://pypi.org/project/codechu-fmt/) | Human-readable formatting — sizes, durations, rates, percent |
| [codechu-spark](https://pypi.org/project/codechu-spark/) | Unicode sparklines, mini bar charts, heatmaps |
| [codechu-cli](https://pypi.org/project/codechu-cli/) | CLI primitives — colors, progress, spinners, prompts, table |
| [codechu-events](https://pypi.org/project/codechu-events/) | Thread-safe multi-channel pub/sub bus with replay |
| [codechu-xdg](https://pypi.org/project/codechu-xdg/) | XDG Base Directory helpers, vendor-namespaced |
| [codechu-treeviz](https://pypi.org/project/codechu-treeviz/) | Tree visualization — treemap, sunburst, icicle, flame |
| [codechu-fs](https://pypi.org/project/codechu-fs/) | Filesystem primitives — atomic write, XDG trash, safe walk |
| [codechu-term](https://pypi.org/project/codechu-term/) | Terminal capability detection, alt buffer, raw mode |
| [codechu-color](https://pypi.org/project/codechu-color/) | Color palettes, WCAG contrast, color-blind variants |
| [codechu-treedata](https://pypi.org/project/codechu-treedata/) | N-ary tree data structures and algorithms |
| [codechu-log](https://pypi.org/project/codechu-log/) | Structured logging — context, JSON, rotation, redaction |
| [codechu-i18n](https://pypi.org/project/codechu-i18n/) | Internationalization — locale, plural rules, RTL |
| [codechu-ipc](https://pypi.org/project/codechu-ipc/) | Local IPC — Unix socket, FIFO, JSON-line protocol |
| [codechu-config](https://pypi.org/project/codechu-config/) | Schema-driven config — atomic save, migrations |

## Credits

- Reservoir sampling per Jeffrey Vitter, "Random Sampling with a Reservoir" (1985)
- EMA convention follows standard exponential smoothing literature

## License

MIT — see [LICENSE](LICENSE).
