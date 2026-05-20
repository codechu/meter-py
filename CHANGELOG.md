# Changelog

[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) + [SemVer](https://semver.org/).

## [Unreleased]

## [0.3.0] — 2026-05-20

### Added
- `Counter` — thread-safe `inc` / `dec` / `reset` int counter
  (`threading.Lock` guarded).
- `Histogram(buckets)` — bucketed distribution counter with inclusive
  upper edges and a `math.inf` overflow bucket. Thread-safe.
- `PercentileEstimator(max_samples)` — streaming p50 / p95 / p99 via
  Vitter's reservoir sampling (algorithm R). Pure stdlib, no numpy.
  Thread-safe.
- `Stopwatch.section(name)` — context-manager API for accumulating
  named sub-timings into `Stopwatch.sections: dict[str, float]`.
  Same-named sections add; nesting works; sections are independent
  of `Stopwatch.elapsed`. Documented as **not thread-safe** — use
  one Stopwatch per thread.

### Fixed
- `RateEstimator(window_seconds=...)` clamp also handles NaN and
  negative inputs: previously `max(1e-6, nan) → nan`, now both clamp
  to the `1e-6` floor.

## [0.2.0] — 2026-05-20

### Changed (breaking)
- Removed `__str__` from `Stopwatch`, `RateEstimator`, and
  `ETAEstimator`. Callers must format explicitly (e.g. via
  `codechu_fmt.format_duration(sw.elapsed)`).
- Dropped the `codechu-fmt` dependency — `codechu-meter` is now
  zero-dependency.

### Added
- `ETAEstimator(..., alpha=0.3)` — configurable EMA smoothing factor
  (previously hardcoded to `0.3`).

## [0.1.0] — 2026-05-20

### Added
- Initial extraction from [codechu/cli-py](https://github.com/codechu/cli-py)
- `Stopwatch` — context manager + manual elapsed timer; pretty
  `__str__` via `codechu-fmt`
- `RateEstimator(window_seconds, unit)` — rolling-window per-second
  rate with auto-eviction of old samples
- `ETAEstimator(total, mode)` — `linear` or `ema` remaining-time
  prediction; returns `None` until enough samples
- Depends on `codechu-fmt>=0.1,<0.2` for human-readable `__str__`
