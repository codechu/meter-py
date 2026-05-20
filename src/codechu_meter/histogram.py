"""Bucketed histogram."""

from __future__ import annotations

import bisect
import math
import threading

__all__ = ["Histogram"]


class Histogram:
    """Bucket counter for distributions (latencies, sizes, …).

    Buckets are defined by their **upper** edges. An observation ``v``
    increments the count of the smallest bucket whose edge is
    ``>= v``. Values strictly greater than the largest edge go to a
    dedicated overflow bucket keyed by ``math.inf``.

    Edge convention: a value exactly on an edge belongs to **that**
    bucket (inclusive upper bound).

    Thread-safe via :class:`threading.Lock`.

    Example::

        h = Histogram([0.001, 0.01, 0.1, 1.0])
        h.observe(0.0005)   # → bucket 0.001
        h.observe(0.001)    # → bucket 0.001 (inclusive edge)
        h.observe(5.0)      # → bucket math.inf (overflow)
        h.counts            # → {0.001: 2, 0.01: 0, 0.1: 0, 1.0: 0, inf: 1}
        h.total             # → 3
    """

    def __init__(self, buckets: list[float]) -> None:
        if not buckets:
            raise ValueError("buckets must be non-empty")
        edges = [float(b) for b in buckets]
        if any(math.isnan(e) for e in edges):
            raise ValueError("buckets must not contain NaN")
        if edges != sorted(edges):
            raise ValueError("buckets must be sorted ascending")
        if any(a == b for a, b in zip(edges, edges[1:])):
            raise ValueError("buckets must be strictly increasing")
        self._edges: list[float] = edges
        self._counts: list[int] = [0] * (len(edges) + 1)  # +1 overflow
        self._total = 0
        self._lock = threading.Lock()

    def observe(self, value: float) -> None:
        v = float(value)
        # bisect_left: returns index of first edge >= v → inclusive upper bound.
        idx = bisect.bisect_left(self._edges, v)
        with self._lock:
            if idx >= len(self._edges):
                self._counts[-1] += 1
            else:
                self._counts[idx] += 1
            self._total += 1

    @property
    def counts(self) -> dict[float, int]:
        with self._lock:
            out: dict[float, int] = {e: self._counts[i] for i, e in enumerate(self._edges)}
            out[math.inf] = self._counts[-1]
            return out

    @property
    def total(self) -> int:
        with self._lock:
            return self._total

    def reset(self) -> None:
        with self._lock:
            for i in range(len(self._counts)):
                self._counts[i] = 0
            self._total = 0
