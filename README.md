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

Stdlib-only measurement primitives. Time things. Estimate rates.
Predict remaining duration. Track counters, histograms, and
streaming percentiles when one number is not enough. All numeric
— formatting is somebody else's problem (see `codechu-fmt`).

| Primitive | What it returns |
|-----------|-----------------|
| `Stopwatch` | elapsed seconds (with `with` or `.start()`/`.stop()`) |
| `RateEstimator` | rolling-window per-second rate |
| `ETAEstimator` | remaining seconds (linear or EMA) |
| `Counter` | thread-safe int counter |
| `Histogram` | bucketed distribution |
| `PercentileEstimator` | streaming p50 / p95 / p99 |

## Install

```bash
pip install codechu-meter
```

Python 3.10+. Zero third-party dependencies.

## Quick example

```python
from codechu_meter import Stopwatch, RateEstimator, ETAEstimator

with Stopwatch() as sw:
    re = RateEstimator(window_seconds=1.0, unit="bytes")
    eta = ETAEstimator(total=len(items), mode="ema", alpha=0.3)

    for i, chunk in enumerate(items, 1):
        process(chunk)
        re.observe(len(chunk))
        eta.update(i)

    print("done in", sw.elapsed, "s")
    print("avg rate", re.rate(), re.unit, "/s")
```

Pair with [`codechu-fmt`](https://pypi.org/project/codechu-fmt/) for
human-readable strings:

```python
from codechu_fmt import format_duration, format_rate

print(format_duration(sw.elapsed))               # '1m 30s'
print(format_rate(re.rate(), unit=re.unit))      # '1.5 MB/s'
```

## What you get

- **`Stopwatch`** — context-manager or manual timer. Optional
  named sections for per-stage timing.
- **`RateEstimator`** — rolling-window per-second rate. `unit` is a
  label only, never affects the numeric result. Bucketed for low
  jitter on bursty workloads.
- **`ETAEstimator`** — `mode="linear"` uses overall throughput;
  `mode="ema"` blends recent throughput (controllable via
  `alpha`). Returns `None` until two updates have elapsed.
- **`Counter`** — thread-safe int with `inc` / `dec` / `reset` /
  `.value`.
- **`Histogram`** — fixed-bucket distribution counter with
  percentile interpolation.
- **`PercentileEstimator`** — streaming p50 / p95 / p99 via
  reservoir sampling (no full sample retention).

## Read more

- [API reference](docs/API.md) — every public symbol with full
  signatures and bucket conventions.
- [Recipes](docs/RECIPES.md) — typical patterns for CLIs, batch
  jobs, services, and benchmarks.
- [Migration guide](docs/MIGRATION.md) — 0.1 → 0.2 → 0.3.
- [Changelog](CHANGELOG.md)

## Family

| Library | Purpose |
|---------|---------|
| [codechu-fmt](https://pypi.org/project/codechu-fmt/) | Human-readable sizes, durations, rates |
| [codechu-cli](https://pypi.org/project/codechu-cli/) | CLI primitives — colors, progress, prompts |
| [codechu-spark](https://pypi.org/project/codechu-spark/) | Unicode sparklines, mini bar charts, heatmaps |
| [codechu-log](https://pypi.org/project/codechu-log/) | Structured logging — context, JSON, rotation |
| [codechu-events](https://pypi.org/project/codechu-events/) | Thread-safe multi-channel pub/sub bus |

Full ecosystem: [github.com/codechu](https://github.com/codechu).

## Credits

- EMA-based ETA convention informed by Linux `pv` and similar
  progress tools.
- Reservoir sampling per Vitter (1985), *ACM TOMS*.

## License

MIT — see [LICENSE](LICENSE).

Part of [Codechu](https://github.com/codechu).
