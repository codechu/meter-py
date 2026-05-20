# Recipes — codechu-meter

Practical patterns. All snippets are runnable as-is on Python 3.10+
(the `codechu-fmt` recipe needs `pip install codechu-fmt`).

## 1. Time a block of code

Use `Stopwatch` as a context manager. `elapsed` is populated on exit
even if the block raises.

```python
from codechu_meter import Stopwatch

with Stopwatch() as sw:
    total = sum(i * i for i in range(1_000_000))

print(f"computed in {sw.elapsed:.3f}s")
```

Manual form, useful when start and stop happen in different scopes:

```python
sw = Stopwatch().start()
try:
    do_work()
finally:
    sw.stop()
    log.info("work took %.3fs", sw.elapsed)
```

---

## 2. Track download speed with a rolling window

`RateEstimator` aggregates observations into a sliding time window.
Observe byte counts as chunks arrive; query `rate()` whenever you
want to render speed.

```python
import urllib.request
from codechu_meter import RateEstimator

re = RateEstimator(window_seconds=2.0, unit="bytes")

with urllib.request.urlopen("https://example.com/big.bin") as r:
    while chunk := r.read(64 * 1024):
        re.observe(len(chunk))
        print(f"\r{re.rate() / 1_048_576:6.2f} MiB/s", end="", flush=True)
```

A wider `window_seconds` (e.g. `5.0`) yields steadier numbers at the
cost of slower reaction to throughput changes.

---

## 3. Compute ETA for a long-running job

`ETAEstimator.update(current)` takes the cumulative progress (not a
delta). `eta()` returns `None` until two updates have happened with
real elapsed time and positive progress.

```python
from codechu_meter import ETAEstimator

items = load_work_queue()
eta = ETAEstimator(total=len(items), mode="linear")

for i, item in enumerate(items, start=1):
    process(item)
    eta.update(i)
    remaining = eta.eta()
    if remaining is not None:
        print(f"\r{i}/{len(items)}  ETA {remaining:6.1f}s", end="", flush=True)
```

For byte-based work, pass byte counts instead of item counts —
`total` and `current` just need to share units.

---

## 4. Tune EMA alpha for stable vs reactive ETA

`mode="ema"` blends recent throughput into the prediction. The
`alpha` parameter controls how reactive the EMA is.

```python
from codechu_meter import ETAEstimator

# Stable: ETA changes slowly, ignores brief stalls / bursts.
stable = ETAEstimator(total=1_000, mode="ema", alpha=0.1)

# Default: balanced reactivity.
default = ETAEstimator(total=1_000, mode="ema", alpha=0.3)

# Reactive: ETA tracks the latest sample closely.
reactive = ETAEstimator(total=1_000, mode="ema", alpha=0.6)
```

Rule of thumb:

- Throughput is noisy but mean-stationary  →  `alpha ≈ 0.1`
- Throughput shifts in phases (warm-up, steady, cool-down)  →  `alpha ≈ 0.5`
- General-purpose progress bar  →  leave `alpha=0.3`

If `mode="ema"` has not yet collected an EMA sample (i.e. first
`update()`), `eta()` transparently falls back to the linear estimate.

---

## 5. Track p95 latency in a request handler

`PercentileEstimator` keeps a bounded reservoir of samples, so memory
stays constant no matter how long the service runs. Observe each
request's duration; query `p95` / `p99` whenever you scrape metrics.

```python
from codechu_meter import PercentileEstimator, Stopwatch

latency = PercentileEstimator(max_samples=5_000)

def handle(request):
    with Stopwatch() as sw:
        response = route(request)
    latency.observe(sw.elapsed)
    return response

# In your /metrics endpoint:
print(f"p50={latency.p50:.3f}s  p95={latency.p95:.3f}s  p99={latency.p99:.3f}s")
```

The reservoir is unbiased over the full stream (Vitter's algorithm R),
so old samples remain in the mix — not a sliding window. For
windowed percentiles, hold one estimator per window and rotate them.

---

## 6. Bucketed latency histogram for SLO reporting

Histograms answer "what fraction of requests met the budget?"
without storing per-request data. Choose bucket edges that match your
SLO thresholds.

```python
from codechu_meter import Histogram

# SLO: 95 % of requests under 100 ms, 99 % under 500 ms.
hist = Histogram([0.010, 0.025, 0.050, 0.100, 0.250, 0.500, 1.000])

for r in requests:
    hist.observe(r.latency_seconds)

# Fraction at or below each edge:
counts = hist.counts
total = hist.total
cumulative = 0
for edge, c in counts.items():
    cumulative += c
    print(f"<= {edge:>5}s  {cumulative / total:6.2%}")
```

Edge convention is **inclusive**: an observation of exactly `0.100`
falls into the `0.100` bucket, not the next one. Anything above the
largest edge lands in the `math.inf` overflow bucket.

---

## 7. Named-section timing within a single Stopwatch

Use `Stopwatch.section(name)` to break a single timed block into
sub-phases without spinning up multiple Stopwatches. Same-named
sections accumulate.

```python
from codechu_meter import Stopwatch

sw = Stopwatch().start()

with sw.section("load"):
    data = load()

for chunk in data:
    with sw.section("parse"):
        rec = parse(chunk)
    with sw.section("emit"):
        emit(rec)

sw.stop()
print(f"total {sw.elapsed:.3f}s")
for name, secs in sw.sections.items():
    print(f"  {name:<6} {secs:.3f}s")
```

`elapsed` measures the full `start()`-to-`stop()` interval; sections
measure only the time inside their `with` blocks. Time spent outside
any section contributes to `elapsed` only.

`section()` is **not** thread-safe. Use one `Stopwatch` per thread,
or guard externally.

---

## 8. Count in-flight requests with `Counter`

`Counter` is a thread-safe int with `inc` / `dec` / `reset`. Wrap a
handler to track concurrent requests:

```python
from codechu_meter import Counter

inflight = Counter()

def handle(req):
    inflight.inc()
    try:
        return serve(req)
    finally:
        inflight.dec()

# Anywhere else (incl. other threads):
print(f"in-flight: {inflight.value}")
```

`Counter` is intentionally not a context manager — the `try/finally`
pattern above is explicit and works under exceptions.

---

## 9. Pair meter with codechu-fmt for human output

meter is numeric-only. For human-readable strings, pipe its outputs
through [`codechu-fmt`](https://github.com/codechu/fmt-py).

```python
from codechu_meter import Stopwatch, RateEstimator, ETAEstimator
from codechu_fmt import format_duration, format_rate

with Stopwatch() as sw:
    payload = download()
print(format_duration(sw.elapsed))                 # → '1m 30s'

re = RateEstimator(unit="bytes")
re.observe(len(payload))
print(format_rate(re.rate(), unit=re.unit))        # → '1.2 MB/s'

eta = ETAEstimator(total=100, mode="ema")
eta.update(50)
v = eta.eta()
print(format_duration(v) if v is not None else "?")
```

Keep formatting at the edge of your program (CLI, log line, GUI
label). Internal state, tests, and metrics should stay in floats.
