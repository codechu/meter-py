"""Tests for codechu_meter.counter."""

from __future__ import annotations

import threading

from codechu_meter import Counter


def test_initial_zero():
    c = Counter()
    assert c.value == 0


def test_initial_value():
    assert Counter(initial=5).value == 5


def test_inc_default():
    c = Counter()
    c.inc()
    assert c.value == 1


def test_inc_amount():
    c = Counter()
    c.inc(7)
    assert c.value == 7


def test_dec_default():
    c = Counter(initial=3)
    c.dec()
    assert c.value == 2


def test_dec_amount():
    c = Counter(initial=10)
    c.dec(4)
    assert c.value == 6


def test_dec_below_zero_allowed():
    c = Counter()
    c.dec(5)
    assert c.value == -5


def test_reset():
    c = Counter(initial=42)
    c.inc(8)
    c.reset()
    assert c.value == 0


def test_concurrent_inc_dec_stress():
    c = Counter()
    n_threads = 8
    iters = 5_000

    def worker():
        for _ in range(iters):
            c.inc()
            c.dec()
            c.inc(2)

    threads = [threading.Thread(target=worker) for _ in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Net per iteration: +1 -1 +2 = +2 → total = n_threads * iters * 2
    assert c.value == n_threads * iters * 2


def test_int_coercion():
    c = Counter(initial=1.7)  # type: ignore[arg-type]
    assert c.value == 1
    c.inc(2.9)  # type: ignore[arg-type]
    assert c.value == 3
