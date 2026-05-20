"""Tests for codechu_meter.eta."""

from __future__ import annotations

import pytest

import codechu_meter.eta as eta_mod
from codechu_meter import ETAEstimator


class _FakeClock:
    def __init__(self, start: float = 1000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, dt: float) -> None:
        self.now += dt


def _patch(monkeypatch, clock):
    monkeypatch.setattr(eta_mod.time, "monotonic", clock)


def test_not_enough_samples(monkeypatch):
    _patch(monkeypatch, _FakeClock())
    eta = ETAEstimator(100)
    assert eta.eta() is None
    eta.update(1)
    assert eta.eta() is None  # only one update


def test_linear_half_done(monkeypatch):
    clock = _FakeClock()
    _patch(monkeypatch, clock)
    eta = ETAEstimator(100, mode="linear")
    eta.update(0)
    clock.advance(10)
    eta.update(50)
    # elapsed=10, current=50, rate=5/s, remaining=50 → 10s
    assert eta.eta() == pytest.approx(10.0)


def test_linear_complete(monkeypatch):
    clock = _FakeClock()
    _patch(monkeypatch, clock)
    eta = ETAEstimator(100)
    eta.update(0)
    clock.advance(10)
    eta.update(100)
    # Remaining=0 → eta=0
    assert eta.eta() == 0.0


def test_ema_mode(monkeypatch):
    clock = _FakeClock()
    _patch(monkeypatch, clock)
    eta = ETAEstimator(100, mode="ema")
    eta.update(0)
    clock.advance(1)
    eta.update(10)  # inst = 10/s
    clock.advance(1)
    eta.update(30)  # inst = 20/s; ema blends
    v = eta.eta()
    assert v is not None
    assert v > 0


def test_bad_mode():
    with pytest.raises(ValueError):
        ETAEstimator(100, mode="bogus")


def test_reset(monkeypatch):
    clock = _FakeClock()
    _patch(monkeypatch, clock)
    eta = ETAEstimator(100)
    eta.update(0)
    clock.advance(5)
    eta.update(50)
    assert eta.eta() is not None
    eta.reset()
    assert eta.eta() is None


def test_zero_elapsed_guard(monkeypatch):
    clock = _FakeClock()
    _patch(monkeypatch, clock)
    eta = ETAEstimator(100)
    eta.update(0)
    eta.update(50)  # no time advance — elapsed=0
    # Two updates, but elapsed=0 → linear rate path returns None
    assert eta.eta() is None


def test_negative_progress_no_ema_update(monkeypatch):
    clock = _FakeClock()
    _patch(monkeypatch, clock)
    eta = ETAEstimator(100, mode="ema")
    eta.update(50)
    clock.advance(1)
    eta.update(40)  # progress went backwards — EMA shouldn't update
    clock.advance(1)
    eta.update(60)
    # Should still produce a value via the linear fallback / EMA seeded now.
    assert eta.eta() is not None


def test_default_alpha():
    eta = ETAEstimator(100)
    assert eta.alpha == 0.3


def test_custom_alpha(monkeypatch):
    clock = _FakeClock()
    _patch(monkeypatch, clock)
    eta = ETAEstimator(100, mode="ema", alpha=0.5)
    assert eta.alpha == 0.5
    eta.update(0)
    clock.advance(1)
    eta.update(10)  # ema seeded at 10
    clock.advance(1)
    eta.update(30)  # inst=20, ema=0.5*20 + 0.5*10 = 15
    assert eta._ema_rate == pytest.approx(15.0)


def test_alpha_one_uses_only_latest(monkeypatch):
    clock = _FakeClock()
    _patch(monkeypatch, clock)
    eta = ETAEstimator(100, mode="ema", alpha=1.0)
    eta.update(0)
    clock.advance(1)
    eta.update(10)  # ema = 10
    clock.advance(1)
    eta.update(30)  # alpha=1 → ema = inst = 20
    assert eta._ema_rate == pytest.approx(20.0)


def test_no_str_format_coupling():
    # v0.2.0: ETAEstimator has no __str__ override.
    assert "ETAEstimator" in str(ETAEstimator(100))
