"""Thread-safe counter."""

from __future__ import annotations

import threading

__all__ = ["Counter"]


class Counter:
    """Thread-safe integer counter with inc / dec / reset.

    All mutations are guarded by a :class:`threading.Lock`. Reads via
    the :attr:`value` property also take the lock so concurrent
    inc/dec/value calls observe a consistent count.

    Counters are *not* context managers — wrap calls explicitly if you
    want scoped semantics::

        c = Counter()
        c.inc()
        try:
            do_work()
        finally:
            c.dec()
    """

    def __init__(self, initial: int = 0) -> None:
        self._value = int(initial)
        self._lock = threading.Lock()

    def inc(self, amount: int = 1) -> None:
        with self._lock:
            self._value += int(amount)

    def dec(self, amount: int = 1) -> None:
        with self._lock:
            self._value -= int(amount)

    def reset(self) -> None:
        with self._lock:
            self._value = 0

    @property
    def value(self) -> int:
        with self._lock:
            return self._value
