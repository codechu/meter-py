"""Remaining-time prediction."""

from __future__ import annotations

import time

from codechu_fmt import format_duration

__all__ = ["ETAEstimator"]


class ETAEstimator:
    """Predicts remaining seconds based on observed progress.

    ``mode='linear'`` (default) uses overall throughput since
    construction / :meth:`reset` — ``elapsed / current * (total - current)``.

    ``mode='ema'`` blends an exponential moving average of recent
    throughput with the linear estimate for smoother numbers on
    bursty workloads.

    Returns ``None`` until at least two updates with measurable
    elapsed time and positive progress.

    ``__str__`` renders via :func:`codechu_fmt.format_duration`, or
    ``'?'`` if no estimate is available yet.
    """

    def __init__(self, total: float, mode: str = "linear") -> None:
        if mode not in ("linear", "ema"):
            raise ValueError(f"unknown mode {mode!r}")
        self.total = float(total)
        self.mode = mode
        self._t_start = time.monotonic()
        self._last_t: float | None = None
        self._last_current: float = 0.0
        self._current: float = 0.0
        self._ema_rate: float | None = None
        self._updates = 0

    def update(self, current: float) -> None:
        now = time.monotonic()
        if self._last_t is not None:
            dt = now - self._last_t
            dn = current - self._last_current
            if dt > 0 and dn > 0:
                inst = dn / dt
                if self._ema_rate is None:
                    self._ema_rate = inst
                else:
                    # alpha=0.3 — smooths noise without lagging too far
                    self._ema_rate = 0.3 * inst + 0.7 * self._ema_rate
        self._last_t = now
        self._last_current = current
        self._current = current
        self._updates += 1

    def eta(self) -> float | None:
        if self._updates < 2 or self._current <= 0:
            return None
        remaining = self.total - self._current
        if remaining <= 0:
            return 0.0
        elapsed = time.monotonic() - self._t_start
        if elapsed <= 0:
            return None
        linear_rate = self._current / elapsed
        if self.mode == "ema" and self._ema_rate is not None and self._ema_rate > 0:
            rate = self._ema_rate
        else:
            rate = linear_rate
        if rate <= 0:
            return None
        return remaining / rate

    def reset(self) -> None:
        self._t_start = time.monotonic()
        self._last_t = None
        self._last_current = 0.0
        self._current = 0.0
        self._ema_rate = None
        self._updates = 0

    def __str__(self) -> str:
        v = self.eta()
        if v is None:
            return "?"
        return format_duration(v)
