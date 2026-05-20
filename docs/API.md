# API Reference — codechu-meter 0.3.0

Stdlib-only measurement primitives. All numeric; formatting is the
caller's responsibility (pair with [`codechu-fmt`](https://github.com/codechu/fmt-py)
for human-readable output).

```python
from codechu_meter import (
    Stopwatch,
    RateEstimator,
    ETAEstimator,
    Counter,
    Histogram,
    PercentileEstimator,
    __version__,
)
```

| Symbol                | Kind     | Summary                                       |
| --------------------- | -------- | --------------------------------------------- |
| `Stopwatch`           | class    | Elapsed wall-time timer + named sections      |
| `RateEstimator`       | class    | Rolling-window per-second rate                |
| `ETAEstimator`        | class    | Remaining-time predictor (linear / EMA)       |
| `Counter`             | class    | Thread-safe inc/dec/reset counter             |
| `Histogram`           | class    | Bucketed distribution counter                 |
| `PercentileEstimator` | class    | Streaming p50/p95/p99 via reservoir sampling  |
| `__version__`         | str      | Package version (e.g. `"0.3.0"`)              |

All timing uses `time.monotonic()` — wall-clock jumps and DST shifts
do not affect measurements.

---

## `Stopwatch`

```python
class Stopwatch:
    def __init__(self) -> None
```

Context-manager / manual elapsed-time timer with optional named
sub-sections.

### Constructor

No parameters. State is initialized to "not started".

### Attributes

| Name          | Type                | Description                                       |
| ------------- | ------------------- | ------------------------------------------------- |
| `started_at`  | `float \| None`     | Monotonic timestamp of last `start()`; `None` if never started |
| `elapsed`     | `float`             | Seconds between `start()` and `stop()`; `0.0` before `stop()` |
| `sections`    | `dict[str, float]`  | Section name → accumulated seconds (v0.3.0+)      |

### Methods

#### `start() -> Stopwatch`

Begin timing. Resets `elapsed` to `0.0`, clears the stop marker, and
clears `sections`. Safe to call repeatedly — each call restarts.

| Returns | `self` (chainable) |
| ------- | ------------------ |

#### `stop() -> Stopwatch`

Stop timing and write the duration to `elapsed`. Calling `stop()`
before `start()` is a no-op. Calling `stop()` twice overwrites
`elapsed` with the latest value.

| Returns | `self` (chainable) |
| ------- | ------------------ |

#### `section(name: str) -> ContextManager[None]`  *(v0.3.0+)*

Context manager that accumulates time spent inside the `with` block
into `self.sections[name]`. Re-entering the same name **adds** to
the existing total. Sections may nest; each is measured independently
against `time.monotonic()`. Sections also accumulate when the block
exits via an exception.

Sections are independent of `elapsed` — time spent outside any
`section()` block still contributes to `elapsed` but to no section.

| Param  | Type  | Description                          |
| ------ | ----- | ------------------------------------ |
| `name` | `str` | Section label; reused names add up   |

```python
sw = Stopwatch().start()
with sw.section("parse"):
    parse(buf)
with sw.section("emit"):
    emit(result)
sw.stop()
sw.sections   # → {"parse": 0.012, "emit": 0.004}
```

**Thread-safety:** `section()` is **not** thread-safe. Use one
`Stopwatch` per thread, or guard externally.

### Context manager protocol

| Method      | Signature                          | Behavior                        |
| ----------- | ---------------------------------- | ------------------------------- |
| `__enter__` | `() -> Stopwatch`                  | Calls `start()`, returns `self` |
| `__exit__`  | `(exc_type, exc, tb) -> None`      | Calls `stop()`; does **not** suppress exceptions |

### Raises

None. All public methods are exception-safe.

---

## `RateEstimator`

```python
class RateEstimator:
    def __init__(
        self,
        window_seconds: float = 1.0,
        *,
        unit: str = "items",
    ) -> None
```

Rolling-window per-second rate. Observations older than
`window_seconds` are discarded at query time.

### Constructor

| Param            | Type    | Default    | Description                                       |
| ---------------- | ------- | ---------- | ------------------------------------------------- |
| `window_seconds` | `float` | `1.0`      | Rolling window length in seconds; clamped to `>= 1e-6` (NaN and negatives also clamp to floor — v0.3.0 fix) |
| `unit`           | `str`   | `"items"`  | Keyword-only label for downstream formatters; never used in math |

### Attributes

| Name             | Type    | Description                          |
| ---------------- | ------- | ------------------------------------ |
| `window_seconds` | `float` | Effective window length              |
| `unit`           | `str`   | Label only; pass to formatter        |

### Methods

#### `observe(n: float = 1) -> None`

Record `n` units at the current monotonic time.

#### `rate() -> float`

Return the average per-second rate over the live window. `0.0` if no
live samples. Calculation: `sum(n) / span`, where `span` is
`min(window_seconds, now - oldest_sample_time)`, clamped to `>= 1e-6`.

#### `reset() -> None`

Drop all samples. Window length and unit are preserved.

### Raises

None.

---

## `ETAEstimator`

```python
class ETAEstimator:
    def __init__(
        self,
        total: float,
        mode: str = "linear",
        *,
        alpha: float = 0.3,
    ) -> None
```

Predicts remaining seconds given monotonically-increasing progress.

### Constructor

| Param   | Type    | Default     | Description                                                 |
| ------- | ------- | ----------- | ----------------------------------------------------------- |
| `total` | `float` | (required)  | Target value of `current` at completion                     |
| `mode`  | `str`   | `"linear"`  | `"linear"` (overall throughput) or `"ema"` (recent-weighted) |
| `alpha` | `float` | `0.3`       | Keyword-only; EMA smoothing factor in `(0, 1]`              |

### Raises (constructor)

| Exception    | When                                |
| ------------ | ----------------------------------- |
| `ValueError` | `mode` is not `"linear"` or `"ema"` |

### Methods

#### `update(current: float) -> None`

Record the latest cumulative progress value. Internally maintains an
EMA of instantaneous throughput when applicable.

#### `eta() -> float | None`

Return remaining seconds, or `None` if not yet computable.

#### `reset() -> None`

Restart internal state. `total`, `mode`, and `alpha` are preserved.

---

## `Counter`  *(v0.3.0+)*

```python
class Counter:
    def __init__(self, initial: int = 0) -> None
```

Thread-safe integer counter. All mutations and reads are guarded by a
`threading.Lock`.

### Constructor

| Param     | Type  | Default | Description                            |
| --------- | ----- | ------- | -------------------------------------- |
| `initial` | `int` | `0`     | Starting value; coerced via `int()`    |

### Attributes / properties

| Name    | Type  | Description                                        |
| ------- | ----- | -------------------------------------------------- |
| `value` | `int` | Current count (property; lock-protected read)      |

### Methods

#### `inc(amount: int = 1) -> None`

Atomically add `amount` to the count.

#### `dec(amount: int = 1) -> None`

Atomically subtract `amount`. Going negative is allowed.

#### `reset() -> None`

Atomically set the count to `0`.

### Raises

None.

```python
from codechu_meter import Counter

inflight = Counter()
def handler(req):
    inflight.inc()
    try:
        return serve(req)
    finally:
        inflight.dec()
```

---

## `Histogram`  *(v0.3.0+)*

```python
class Histogram:
    def __init__(self, buckets: list[float]) -> None
```

Bucketed distribution counter. Each `observe(v)` increments the
smallest bucket whose **upper edge** is `>= v`. Values strictly above
the largest edge fall into a dedicated overflow bucket keyed by
`math.inf`.

**Edge convention:** a value exactly on an edge belongs to that
bucket (inclusive upper bound).

Thread-safe via `threading.Lock`.

### Constructor

| Param     | Type           | Description                                            |
| --------- | -------------- | ------------------------------------------------------ |
| `buckets` | `list[float]`  | Strictly-increasing upper edges; must be non-empty     |

### Raises (constructor)

| Exception    | When                                              |
| ------------ | ------------------------------------------------- |
| `ValueError` | `buckets` is empty, not sorted ascending, has duplicates, or contains NaN |

### Attributes / properties

| Name      | Type                | Description                                    |
| --------- | ------------------- | ---------------------------------------------- |
| `counts`  | `dict[float, int]`  | Edge → count; includes `math.inf` overflow key |
| `total`   | `int`               | Total observations                             |

### Methods

#### `observe(value: float) -> None`

Record one observation. Edges are inclusive upper bounds.

#### `reset() -> None`

Zero all buckets and `total`.

```python
from codechu_meter import Histogram

h = Histogram([0.001, 0.01, 0.1, 1.0])
for r in requests:
    h.observe(r.latency_seconds)
```

---

## `PercentileEstimator`  *(v0.3.0+)*

```python
class PercentileEstimator:
    def __init__(self, max_samples: int = 10_000) -> None
```

Streaming percentile estimator using **Vitter's reservoir sampling
algorithm R**. Stores at most `max_samples` observations. After
the reservoir fills, each new observation replaces a random existing
slot with probability `max_samples / n`, yielding an unbiased uniform
sample of the full stream regardless of length.

Percentiles use linear interpolation between the two nearest ranks.

Thread-safe via `threading.Lock`. Pure stdlib (no numpy / scipy).

### Constructor

| Param         | Type  | Default   | Description                       |
| ------------- | ----- | --------- | --------------------------------- |
| `max_samples` | `int` | `10_000`  | Reservoir capacity (must be `>= 1`) |

### Raises (constructor)

| Exception    | When                  |
| ------------ | --------------------- |
| `ValueError` | `max_samples < 1`     |

### Attributes / properties

| Name           | Type             | Description                                        |
| -------------- | ---------------- | -------------------------------------------------- |
| `max_samples`  | `int`            | Reservoir capacity                                 |
| `count`        | `int`            | Total observations seen (may exceed `max_samples`) |
| `p50`          | `float \| None`  | 50th percentile (median); `None` if empty          |
| `p95`          | `float \| None`  | 95th percentile                                    |
| `p99`          | `float \| None`  | 99th percentile                                    |

### Methods

#### `observe(value: float) -> None`

Record one sample.

#### `percentile(p: float) -> float | None`

Return the `p`-th percentile (`0 <= p <= 100`). `None` when no
samples have been recorded.

| Exception    | When                  |
| ------------ | --------------------- |
| `ValueError` | `p` outside `[0, 100]`|

#### `reset() -> None`

Drop all samples and reset `count`.

```python
from codechu_meter import PercentileEstimator

pe = PercentileEstimator(max_samples=5_000)
for r in requests:
    pe.observe(r.latency_ms)
print(pe.p95, pe.p99)
```

---

## `__version__`

```python
from codechu_meter import __version__
print(__version__)  # → '0.3.0'
```
