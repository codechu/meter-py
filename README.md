# codechu-meter

```text
   ___          _           _
  / __\___   __| | ___  ___| |__  _   _
 / /  / _ \ / _\` |/ _ \/ __| '_ \| | | |
/ /__| (_) | (_| |  __/ (__| | | | |_| |
\____/\___/ \__,_|\___|\___|_| |_|\__,_|
```


Stdlib-only measurement primitives — stopwatch, rolling-window rate
estimator, ETA predictor — extracted from the [Disk Cleaner](https://github.com/codechu/disk-cleaner)
toolchain. Depends only on
[`codechu-fmt`](https://github.com/codechu/fmt-py) for pretty
`__str__` rendering. Python 3.10+.

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
print(sw)          # → '1m 30s'  (via codechu-fmt)
print(sw.elapsed)  # → float seconds

# Manual form
sw = Stopwatch().start()
do_work()
sw.stop()
```

### `RateEstimator`

```python
from codechu_meter import RateEstimator

re = RateEstimator(window_seconds=1.0)
for chunk in stream:
    re.observe(len(chunk))
print(re.rate())   # float per-second
print(re)          # → '1.2 MB/s' if unit='bytes'
```

Pass `unit='items'` (default), `'bytes'`, `'ops'`, or any custom
label — `__str__` delegates to `codechu_fmt.format_rate`.

### `ETAEstimator`

```python
from codechu_meter import ETAEstimator

eta = ETAEstimator(total=1000, mode="ema")
for current in progress:
    eta.update(current)
    print(eta)     # → '45s' or '?' if not enough samples yet
```

`mode='linear'` (default) uses overall throughput since
construction. `mode='ema'` blends an exponential moving average
of recent throughput for smoother numbers on bursty workloads.

`eta()` returns `None` until at least two updates with measurable
elapsed time and positive progress; `__str__` renders that as `'?'`.

## Design

- **Stdlib + codechu-fmt only.** No other dependencies.
- **Monotonic clock.** Wall-clock jumps don't break timing.
- **Defensive.** Zero progress, zero elapsed, NaN, and negative rates
  never raise.

## Tests

```bash
pip install -e ".[dev]"
pytest -q
```

Coverage gate: ≥90 %. Tests drive time via monkeypatching
`time.monotonic` for deterministic assertions.

## License

MIT — see [LICENSE](LICENSE).
