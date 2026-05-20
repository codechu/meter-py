"""Tests for codechu_meter.rate."""

from __future__ import annotations

import codechu_meter.rate as rate_mod
from codechu_meter import RateEstimator


class _FakeClock:
    def __init__(self, start: float = 1000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, dt: float) -> None:
        self.now += dt


def _patch(monkeypatch, clock):
    monkeypatch.setattr(rate_mod.time, "monotonic", clock)


def test_empty(monkeypatch):
    _patch(monkeypatch, _FakeClock())
    re = RateEstimator()
    assert re.rate() == 0.0


def test_window_floor():
    re = RateEstimator(window_seconds=0)
    assert re.window_seconds == 1e-6


def test_single_observation(monkeypatch):
    clock = _FakeClock()
    _patch(monkeypatch, clock)
    re = RateEstimator(window_seconds=1.0)
    re.observe(10)
    # Same instant → span is 1e-6 floor → rate is enormous. Just
    # assert it's positive.
    assert re.rate() > 0


def test_rolling_observations(monkeypatch):
    clock = _FakeClock()
    _patch(monkeypatch, clock)
    re = RateEstimator(window_seconds=1.0)
    re.observe(10)
    clock.advance(0.5)
    re.observe(10)
    # Span = 0.5s, total = 20 → 40/s
    assert abs(re.rate() - 40.0) < 1e-6


def test_window_evicts_old(monkeypatch):
    clock = _FakeClock()
    _patch(monkeypatch, clock)
    re = RateEstimator(window_seconds=1.0)
    re.observe(100)
    clock.advance(2.0)  # past window
    re.observe(5)
    r = re.rate()
    assert r > 0


def test_reset(monkeypatch):
    clock = _FakeClock()
    _patch(monkeypatch, clock)
    re = RateEstimator()
    re.observe(5)
    re.reset()
    assert re.rate() == 0.0


def test_unit_attribute():
    re = RateEstimator(unit="bytes")
    assert re.unit == "bytes"


def test_no_str_format_coupling():
    # v0.2.0: RateEstimator has no __str__ override.
    assert "RateEstimator" in str(RateEstimator())
