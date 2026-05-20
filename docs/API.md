# API Reference — codechu-meter 0.2.0

Stdlib-only measurement primitives. All numeric; formatting is the
caller's responsibility (pair with [`codechu-fmt`](https://github.com/codechu/fmt-py)
for human-readable output).

```python
from codechu_meter import Stopwatch, RateEstimator, ETAEstimator, __version__
```

| Symbol           | Kind     | Summary                                   |
| ---------------- | -------- | ----------------------------------------- |
| `Stopwatch`      | class    | Elapsed wall-time timer (context manager) |
| `RateEstimator`  | class    | Rolling-window per-second rate            |
| `ETAEstimator`   | class    | Remaining-time predictor (linear / EMA)   |
| `__version__`    | str      | Package version (e.g. `"0.2.0"`)          |

All timing uses `time.monotonic()` — wall-clock jumps and DST shifts
do not affect measurements.

---

## `Stopwatch`

```python
class Stopwatch:
    def __init__(self) -> None
```

Context-manager / manual elapsed-time timer.

### Constructor

No parameters. State is initialized to "not started".

### Attributes

| Name          | Type             | Description                                       |
| ------------- | ---------------- | ------------------------------------------------- |
| `started_at`  | `float \| None`  | Monotonic timestamp of last `start()`; `None` if never started |
| `elapsed`     | `float`          | Seconds between `start()` and `stop()`; `0.0` before `stop()` |

### Methods

#### `start() -> Stopwatch`

Begin timing. Resets `elapsed` to `0.0` and clears the stop marker.
Safe to call repeatedly — each call restarts the clock.

| Returns | `self` (chainable)         |
| ------- | -------------------------- |

```python
sw = Stopwatch().start()
```

#### `stop() -> Stopwatch`

Stop timing and write the duration to `elapsed`. Calling `stop()`
before `start()` is a no-op (no exception). Calling `stop()` twice
overwrites `elapsed` with the latest value.

| Returns | `self` (chainable) |
| ------- | ------------------ |

```python
sw.stop()
print(sw.elapsed)  # → 1.234
```

### Context manager protocol

`Stopwatch` implements `__enter__` / `__exit__`:

| Method      | Signature                                  | Behavior                                   |
| ----------- | ------------------------------------------ | ------------------------------------------ |
| `__enter__` | `() -> Stopwatch`                          | Calls `start()`, returns `self`            |
| `__exit__`  | `(exc_type, exc, tb) -> None`              | Calls `stop()`; does **not** suppress exceptions |

```python
with Stopwatch() as sw:
    do_work()
print(sw.elapsed)
```

If `do_work()` raises, `stop()` still runs and `elapsed` is populated
before the exception propagates.

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
| `window_seconds` | `float` | `1.0`      | Rolling window length in seconds; clamped to `>= 1e-6` |
| `unit`           | `str`   | `"items"`  | Keyword-only label for downstream formatters; never used in math |

### Attributes

| Name             | Type    | Description                          |
| ---------------- | ------- | ------------------------------------ |
| `window_seconds` | `float` | Effective window length              |
| `unit`           | `str`   | Label only; pass to formatter        |

### Methods

#### `observe(n: float = 1) -> None`

Record `n` units at the current monotonic time. Trims expired
samples after appending.

| Param | Type    | Default | Description                          |
| ----- | ------- | ------- | ------------------------------------ |
| `n`   | `float` | `1`     | Quantity to record (bytes, items, …) |

```python
re = RateEstimator(window_seconds=2.0, unit="bytes")
for chunk in stream:
    re.observe(len(chunk))
```

#### `rate() -> float`

Return the average per-second rate over the live window.

| Returns | `float` — units per second; `0.0` if no live samples |
| ------- | --------------------------------------------------- |

Calculation: `sum(n) / span`, where `span` is
`min(window_seconds, now - oldest_sample_time)`, clamped to `>= 1e-6`.

```python
print(re.rate())  # → 1_048_576.0
```

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
| `alpha` | `float` | `0.3`       | Keyword-only; EMA smoothing factor in `(0, 1]`; higher = more reactive |

### Raises (constructor)

| Exception    | When                                |
| ------------ | ----------------------------------- |
| `ValueError` | `mode` is not `"linear"` or `"ema"` |

### Attributes

| Name     | Type    | Description           |
| -------- | ------- | --------------------- |
| `total`  | `float` | Completion target     |
| `mode`   | `str`   | `"linear"` or `"ema"` |
| `alpha`  | `float` | EMA smoothing factor  |

### Methods

#### `update(current: float) -> None`

Record the latest cumulative progress value. Call repeatedly during
the job. Internally maintains an EMA of instantaneous throughput
`(dn/dt)` when `dt > 0` and `dn > 0`.

| Param     | Type    | Description                                |
| --------- | ------- | ------------------------------------------ |
| `current` | `float` | Cumulative progress so far (≤ `total`)     |

```python
eta = ETAEstimator(total=1_000, mode="ema")
for i, item in enumerate(jobs, start=1):
    process(item)
    eta.update(i)
```

#### `eta() -> float | None`

Return remaining seconds, or `None` if not yet computable.

| Returns | `float \| None` — seconds remaining; `0.0` when complete; `None` when fewer than two updates, no positive progress, or no measurable elapsed time |
| ------- | --------------------------------------------------- |

Calculation:

- `linear_rate = current / elapsed_since_construction`
- If `mode == "ema"` and an EMA rate exists and is positive, use it;
  otherwise fall back to `linear_rate`.
- `return (total - current) / rate`

#### `reset() -> None`

Restart all internal state (start time, last sample, EMA, update
counter). `total`, `mode`, and `alpha` are preserved.

### Raises (methods)

None.

### EMA math — when to tune `alpha`

The EMA recurrence is:

```
ema_rate ← alpha * inst + (1 - alpha) * ema_rate
```

where `inst = dn / dt` is the instantaneous throughput between the
last two `update()` calls.

| `alpha` | Behavior                                      | Use when …                                  |
| ------- | --------------------------------------------- | ------------------------------------------- |
| `0.1`   | Heavy smoothing; ETA reacts slowly            | Throughput is noisy but mean-stationary     |
| `0.3`   | Default; balanced reactivity                  | General progress bars                       |
| `0.5`   | Recent samples dominate                       | Throughput shifts in clear phases           |
| `1.0`   | No smoothing; ETA = remaining / last instant  | Debugging; rarely useful in production      |

Lower `alpha` → smoother ETA, slower to adapt to real changes.
Higher `alpha` → jumpier ETA, fast to follow shifts.

---

## `__version__`

```python
from codechu_meter import __version__
print(__version__)  # → '0.2.0'
```
