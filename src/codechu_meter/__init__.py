"""codechu-meter — stdlib-only measurement primitives.

Re-exports:

- :class:`Stopwatch`            — context-manager / manual elapsed timer (with named sections)
- :class:`RateEstimator`        — rolling-window per-second rate
- :class:`ETAEstimator`         — remaining-time prediction (linear / EMA)
- :class:`Counter`              — thread-safe inc/dec/reset counter
- :class:`Histogram`            — bucketed distribution counter
- :class:`PercentileEstimator`  — streaming p50/p95/p99 via reservoir sampling
"""

from __future__ import annotations

from .counter import Counter
from .eta import ETAEstimator
from .histogram import Histogram
from .percentile import PercentileEstimator
from .rate import RateEstimator
from .stopwatch import Stopwatch

__version__ = "0.3.0"

__all__ = [
    "Counter",
    "ETAEstimator",
    "Histogram",
    "PercentileEstimator",
    "RateEstimator",
    "Stopwatch",
    "__version__",
]
