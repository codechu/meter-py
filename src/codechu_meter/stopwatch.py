"""Elapsed-time measurer."""

from __future__ import annotations

import time

__all__ = ["Stopwatch"]


class Stopwatch:
    """Context manager + manual API for measuring elapsed wall time.

    Usage::

        with Stopwatch() as sw:
            do_work()
        sw.elapsed  # → float seconds

        sw = Stopwatch().start()
        ...
        sw.stop()
        sw.elapsed

    Formatting is the caller's responsibility (e.g.
    ``codechu_fmt.format_duration(sw.elapsed)``).
    """

    def __init__(self) -> None:
        self.started_at: float | None = None
        self._stopped_at: float | None = None
        self.elapsed: float = 0.0

    def start(self) -> Stopwatch:
        self.started_at = time.monotonic()
        self._stopped_at = None
        self.elapsed = 0.0
        return self

    def stop(self) -> Stopwatch:
        if self.started_at is None:
            return self
        self._stopped_at = time.monotonic()
        self.elapsed = self._stopped_at - self.started_at
        return self

    def __enter__(self) -> Stopwatch:
        return self.start()

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()
