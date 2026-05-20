"""Elapsed-time measurer with named sub-sections."""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Iterator

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

    Named sections (v0.3.0+) accumulate sub-timings into
    :attr:`sections`::

        sw = Stopwatch().start()
        with sw.section("parse"):
            parse(buf)
        with sw.section("emit"):
            emit(result)
        sw.stop()
        sw.sections  # → {"parse": 0.012, "emit": 0.004}

    The same section name can be entered repeatedly; durations add up.
    Sections may nest; each one is measured against its own
    ``time.monotonic()`` start. Sections are **not** thread-safe — use
    one ``Stopwatch`` per thread, or guard ``section()`` externally.

    Formatting is the caller's responsibility (e.g.
    ``codechu_fmt.format_duration(sw.elapsed)``).
    """

    def __init__(self) -> None:
        self.started_at: float | None = None
        self._stopped_at: float | None = None
        self.elapsed: float = 0.0
        self.sections: dict[str, float] = {}

    def start(self) -> Stopwatch:
        self.started_at = time.monotonic()
        self._stopped_at = None
        self.elapsed = 0.0
        self.sections = {}
        return self

    def stop(self) -> Stopwatch:
        if self.started_at is None:
            return self
        self._stopped_at = time.monotonic()
        self.elapsed = self._stopped_at - self.started_at
        return self

    @contextmanager
    def section(self, name: str) -> Iterator[None]:
        """Accumulate time spent inside the ``with`` block into
        ``self.sections[name]``. Re-entering the same name adds.

        Not thread-safe. Independent of :attr:`elapsed`.
        """
        t0 = time.monotonic()
        try:
            yield
        finally:
            dt = time.monotonic() - t0
            self.sections[name] = self.sections.get(name, 0.0) + dt

    def __enter__(self) -> Stopwatch:
        return self.start()

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()
