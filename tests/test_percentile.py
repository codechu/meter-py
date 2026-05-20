"""Tests for codechu_meter.percentile."""

from __future__ import annotations

import random
import statistics
import threading

import pytest

from codechu_meter import PercentileEstimator


def test_empty_returns_none():
    pe = PercentileEstimator()
    assert pe.percentile(50) is None
    assert pe.p50 is None
    assert pe.p95 is None
    assert pe.p99 is None


def test_single_sample():
    pe = PercentileEstimator()
    pe.observe(42.0)
    assert pe.percentile(0) == 42.0
    assert pe.percentile(50) == 42.0
    assert pe.percentile(100) == 42.0


def test_p_out_of_range():
    pe = PercentileEstimator()
    pe.observe(1.0)
    with pytest.raises(ValueError):
        pe.percentile(-1)
    with pytest.raises(ValueError):
        pe.percentile(101)


def test_max_samples_minimum():
    with pytest.raises(ValueError):
        PercentileEstimator(max_samples=0)


def test_basic_percentiles_within_capacity():
    pe = PercentileEstimator(max_samples=1000)
    for i in range(1, 101):  # 1..100
        pe.observe(float(i))
    # Linear interp on 100 sorted samples: p50 at pos 49.5 → 50.5
    assert abs(pe.p50 - 50.5) < 1e-9
    # p99: pos = 0.99 * 99 = 98.01 → between data[98]=99 and data[99]=100
    assert abs(pe.p99 - (99 + 0.01)) < 1e-9
    assert pe.count == 100


def test_reservoir_sampling_p50_close_to_median():
    """Stress: 10k random samples, p50 should be near true median."""
    rng = random.Random(12345)
    pe = PercentileEstimator(max_samples=10_000)
    raw = [rng.gauss(100.0, 15.0) for _ in range(10_000)]
    for v in raw:
        pe.observe(v)
    true_median = statistics.median(raw)
    # Within capacity → exact (no reservoir replacement)
    assert abs(pe.p50 - true_median) < 1e-9


def test_reservoir_unbiased_over_capacity():
    """Stream more than max_samples → p50 still close to true median."""
    rng = random.Random(987)
    pe = PercentileEstimator(max_samples=500)
    raw = [rng.gauss(0.0, 1.0) for _ in range(20_000)]
    for v in raw:
        pe.observe(v)
    true_median = statistics.median(raw)
    # Reservoir of 500 from N(0,1): standard error of median ~ 1/sqrt(500) ≈ 0.045
    # Allow 5x for CI flake tolerance.
    assert abs(pe.p50 - true_median) < 0.25
    assert pe.count == 20_000


def test_reset():
    pe = PercentileEstimator()
    pe.observe(1.0)
    pe.observe(2.0)
    pe.reset()
    assert pe.p50 is None
    assert pe.count == 0


def test_thread_safety_no_corruption():
    pe = PercentileEstimator(max_samples=2_000)

    def worker(seed: int):
        rng = random.Random(seed)
        for _ in range(2_000):
            pe.observe(rng.random())

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert pe.count == 4 * 2_000
    # p50 of uniform [0,1) ≈ 0.5
    assert pe.p50 is not None
    assert 0.3 < pe.p50 < 0.7


def test_p95_p99_monotonic():
    pe = PercentileEstimator()
    for v in range(1000):
        pe.observe(float(v))
    assert pe.p50 < pe.p95 < pe.p99
