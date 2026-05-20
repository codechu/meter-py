"""codechu-meter — stdlib-only measurement primitives.

Re-exports:

- :class:`Stopwatch`      — context-manager / manual elapsed timer
- :class:`RateEstimator`  — rolling-window per-second rate
- :class:`ETAEstimator`   — remaining-time prediction (linear / EMA)
"""

from __future__ import annotations

from .eta import ETAEstimator
from .rate import RateEstimator
from .stopwatch import Stopwatch

__version__ = "0.1.0"

__all__ = [
    "ETAEstimator",
    "RateEstimator",
    "Stopwatch",
    "__version__",
]
