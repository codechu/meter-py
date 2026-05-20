# Migration Guide — 0.1.x → 0.2.0

codechu-meter 0.2.0 narrows the package to its numeric primitives.
Display is now exclusively the caller's job. The package is also
fully zero-dependency.

## TL;DR

| Change                                            | Impact   |
| ------------------------------------------------- | -------- |
| `__str__` removed from all three classes          | Breaking |
| `codechu-fmt` is no longer a runtime dependency   | Breaking (if you relied on it transitively) |
| `Stopwatch` documented as a context manager       | Additive |
| `ETAEstimator.alpha` is now configurable          | Additive |

---

## BREAKING — `__str__` removed

In 0.1.x, each class formatted itself when coerced to `str`. In
0.2.0, the classes are numeric-only — `str(sw)` returns the default
Python object repr.

### Before (0.1.x)

```python
from codechu_meter import Stopwatch, RateEstimator, ETAEstimator

with Stopwatch() as sw:
    do_work()
print(sw)                          # → '1m 30s'

re = RateEstimator(unit="bytes")
re.observe(1_048_576)
print(re)                          # → '1.0 MB/s'

eta = ETAEstimator(total=100)
eta.update(50)
print(eta)                         # → 'ETA 0m 12s' or '?'
```

### After (0.2.0)

```python
from codechu_meter import Stopwatch, RateEstimator, ETAEstimator
from codechu_fmt import format_duration, format_rate

with Stopwatch() as sw:
    do_work()
print(format_duration(sw.elapsed))                       # → '1m 30s'

re = RateEstimator(unit="bytes")
re.observe(1_048_576)
print(format_rate(re.rate(), unit=re.unit))              # → '1.0 MB/s'

eta = ETAEstimator(total=100)
eta.update(50)
v = eta.eta()
print(format_duration(v) if v is not None else "?")
```

### Why

- The two responsibilities — measuring numbers and rendering them —
  evolve independently. Coupling them forced every caller to inherit
  whatever locale / unit decisions the formatter made.
- Tests get deterministic numeric assertions instead of string
  fixtures that drift with the formatter.
- Removing `codechu-fmt` from `install_requires` lets meter ship as a
  tiny stdlib-only wheel.

---

## REMOVED dependency — `codechu-fmt`

0.1.x declared `codechu-fmt` in `install_requires`. 0.2.0 does not.

If your project depended on meter pulling `codechu-fmt` in
transitively, add it to your own dependencies:

```toml
# pyproject.toml
dependencies = [
    "codechu-meter>=0.2,<0.3",
    "codechu-fmt>=0.4,<0.5",   # add explicitly if you format meter output
]
```

---

## NEW — `Stopwatch` context manager (now documented)

The `__enter__` / `__exit__` protocol existed in 0.1.x but was not
part of the documented surface. It is now a supported public API:

```python
from codechu_meter import Stopwatch

with Stopwatch() as sw:
    do_work()
# sw.elapsed is set even if do_work() raises
print(sw.elapsed)
```

`__exit__` does not suppress exceptions.

---

## NEW — `ETAEstimator.alpha` parameter

In 0.1.x the EMA smoothing factor was hardcoded at `0.3`. In 0.2.0
it is a keyword-only constructor parameter with the same default,
so no code change is required to keep old behavior.

### Before (0.1.x)

```python
eta = ETAEstimator(total=1_000, mode="ema")
# alpha implicitly 0.3
```

### After (0.2.0)

```python
# Identical behavior — default unchanged
eta = ETAEstimator(total=1_000, mode="ema")

# Smoother ETA for noisy throughput
eta = ETAEstimator(total=1_000, mode="ema", alpha=0.1)

# More reactive ETA for phased workloads
eta = ETAEstimator(total=1_000, mode="ema", alpha=0.5)
```

See [API.md](API.md#ema-math--when-to-tune-alpha) for tuning
guidance.

---

## Upgrade checklist

- [ ] Remove any `print(sw) / print(re) / print(eta)` style calls;
      route through `codechu_fmt` (or your own formatter).
- [ ] Add `codechu-fmt` to your project's own dependencies if you
      were relying on the transitive install.
- [ ] (Optional) Pass an explicit `alpha=` to `ETAEstimator` if you
      want a non-default smoothing factor.
- [ ] Bump the version pin: `codechu-meter>=0.2,<0.3`.
