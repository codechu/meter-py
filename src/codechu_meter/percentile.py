"""Streaming percentile estimator (reservoir sampling)."""

from __future__ import annotations

import random
import threading

__all__ = ["PercentileEstimator"]


class PercentileEstimator:
    """Streaming percentile estimator using reservoir sampling.

    Holds up to ``max_samples`` observations. The first ``max_samples``
    observations are stored verbatim; subsequent observations replace
    a random existing slot with probability ``max_samples / n``
    (Vitter's algorithm R). This yields an unbiased uniform sample of
    the full stream regardless of length.

    Percentiles are computed on-demand by sorting the current
    reservoir (``O(k log k)`` per query, ``k <= max_samples``).

    Thread-safe via :class:`threading.Lock`.

    No numpy / scipy — stdlib only.
    """

    def __init__(self, max_samples: int = 10_000) -> None:
        if max_samples < 1:
            raise ValueError("max_samples must be >= 1")
        self.max_samples = int(max_samples)
        self._samples: list[float] = []
        self._n = 0  # total observations ever
        self._rand = random.Random()
        self._lock = threading.Lock()

    def observe(self, value: float) -> None:
        v = float(value)
        with self._lock:
            self._n += 1
            if len(self._samples) < self.max_samples:
                self._samples.append(v)
            else:
                # Vitter's algorithm R: replace with probability k/n.
                j = self._rand.randrange(self._n)
                if j < self.max_samples:
                    self._samples[j] = v

    def percentile(self, p: float) -> float | None:
        """Return the ``p``-th percentile (``0 <= p <= 100``).

        Linear interpolation between the two nearest ranks. Returns
        ``None`` when no samples have been recorded.
        """
        if not 0.0 <= p <= 100.0:
            raise ValueError("p must be in [0, 100]")
        with self._lock:
            if not self._samples:
                return None
            data = sorted(self._samples)
        if len(data) == 1:
            return data[0]
        # Linear interpolation rank: pos in [0, n-1]
        pos = (p / 100.0) * (len(data) - 1)
        lo = int(pos)
        hi = min(lo + 1, len(data) - 1)
        frac = pos - lo
        return data[lo] + (data[hi] - data[lo]) * frac

    @property
    def p50(self) -> float | None:
        return self.percentile(50.0)

    @property
    def p95(self) -> float | None:
        return self.percentile(95.0)

    @property
    def p99(self) -> float | None:
        return self.percentile(99.0)

    @property
    def count(self) -> int:
        """Total observations seen (may exceed ``max_samples``)."""
        with self._lock:
            return self._n

    def reset(self) -> None:
        with self._lock:
            self._samples.clear()
            self._n = 0


