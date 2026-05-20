"""Rolling-window rate estimator."""

from __future__ import annotations

import math
import time
from collections import deque
from typing import Deque

__all__ = ["RateEstimator"]


class RateEstimator:
    """Rolling-window per-second rate.

    Observations older than ``window_seconds`` are dropped at query
    time. :meth:`rate` returns ``0.0`` when no observations exist or
    no time has elapsed.

    Formatting is the caller's responsibility (e.g.
    ``codechu_fmt.format_rate(re.rate(), unit=re.unit)``).
    """

    def __init__(self, window_seconds: float = 1.0, *, unit: str = "items") -> None:
        w = float(window_seconds)
        # NaN propagates through max(); fall back to floor explicitly.
        if math.isnan(w) or w < 1e-6:
            w = 1e-6
        self.window_seconds = w
        self.unit = unit
        self._samples: Deque[tuple[float, float]] = deque()

    def observe(self, n: float = 1) -> None:
        self._samples.append((time.monotonic(), float(n)))
        self._trim()

    def _trim(self) -> None:
        if not self._samples:
            return
        cutoff = time.monotonic() - self.window_seconds
        while self._samples and self._samples[0][0] < cutoff:
            self._samples.popleft()

    def rate(self) -> float:
        self._trim()
        if not self._samples:
            return 0.0
        total = sum(n for _, n in self._samples)
        now = time.monotonic()
        oldest = self._samples[0][0]
        span = max(1e-6, min(self.window_seconds, now - oldest))
        return total / span

    def reset(self) -> None:
        self._samples.clear()
