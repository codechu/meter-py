"""Elapsed-time measurer."""

from __future__ import annotations

import time

from codechu_fmt import format_duration

__all__ = ["Stopwatch"]


class Stopwatch:
    """Context manager + manual API for measuring elapsed wall time.

    Usage::

        with Stopwatch() as sw:
            do_work()
        print(sw)          # → '1m 30s' (via codechu_fmt.format_duration)
        print(sw.elapsed)  # → float seconds

        sw = Stopwatch().start()
        ...
        sw.stop()
        sw.elapsed
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

    def __str__(self) -> str:
        # Use the running elapsed when active; the captured elapsed
        # otherwise. The captured value is 0.0 before start().
        if self.started_at is not None and self._stopped_at is None:
            return format_duration(time.monotonic() - self.started_at)
        return format_duration(self.elapsed)
