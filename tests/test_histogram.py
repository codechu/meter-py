"""Tests for codechu_meter.histogram."""

from __future__ import annotations

import math
import threading

import pytest

from codechu_meter import Histogram


def test_basic_bucketing():
    h = Histogram([0.001, 0.01, 0.1, 1.0])
    h.observe(0.0005)
    h.observe(0.05)
    h.observe(0.5)
    assert h.counts == {0.001: 1, 0.01: 0, 0.1: 1, 1.0: 1, math.inf: 0}
    assert h.total == 3


def test_inclusive_upper_edge():
    """Value exactly on an edge belongs to that bucket."""
    h = Histogram([1.0, 2.0, 3.0])
    h.observe(1.0)
    h.observe(2.0)
    h.observe(3.0)
    assert h.counts == {1.0: 1, 2.0: 1, 3.0: 1, math.inf: 0}


def test_overflow_bucket():
    h = Histogram([1.0, 2.0])
    h.observe(5.0)
    h.observe(100.0)
    h.observe(2.0001)
    counts = h.counts
    assert counts[math.inf] == 3
    assert h.total == 3


def test_below_smallest_edge():
    h = Histogram([1.0, 2.0])
    h.observe(-100.0)
    h.observe(0.0)
    assert h.counts[1.0] == 2


def test_reset():
    h = Histogram([1.0])
    h.observe(0.5)
    h.observe(10.0)
    h.reset()
    assert h.total == 0
    assert h.counts == {1.0: 0, math.inf: 0}


def test_empty_buckets_rejected():
    with pytest.raises(ValueError):
        Histogram([])


def test_unsorted_buckets_rejected():
    with pytest.raises(ValueError):
        Histogram([1.0, 0.5, 2.0])


def test_duplicate_buckets_rejected():
    with pytest.raises(ValueError):
        Histogram([1.0, 1.0, 2.0])


def test_nan_bucket_rejected():
    with pytest.raises(ValueError):
        Histogram([1.0, float("nan")])


def test_single_bucket():
    h = Histogram([0.0])
    h.observe(-1.0)
    h.observe(0.0)
    h.observe(1.0)
    assert h.counts == {0.0: 2, math.inf: 1}


def test_thread_safety():
    h = Histogram([1.0, 10.0, 100.0])
    n_threads = 8
    per_thread = 1_000

    def worker():
        for i in range(per_thread):
            h.observe(0.5)
            h.observe(50.0)
            h.observe(500.0)

    threads = [threading.Thread(target=worker) for _ in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert h.total == n_threads * per_thread * 3
    counts = h.counts
    assert counts[1.0] == n_threads * per_thread
    assert counts[100.0] == n_threads * per_thread
    assert counts[math.inf] == n_threads * per_thread
