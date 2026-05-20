"""Tests for codechu_meter.stopwatch."""

from __future__ import annotations

import codechu_meter.stopwatch as sw_mod
from codechu_meter import Stopwatch


class _FakeClock:
    def __init__(self, start: float = 1000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, dt: float) -> None:
        self.now += dt


def _patch(monkeypatch, clock):
    monkeypatch.setattr(sw_mod.time, "monotonic", clock)


def test_str_before_start(monkeypatch):
    clock = _FakeClock()
    _patch(monkeypatch, clock)
    sw = Stopwatch()
    assert sw.elapsed == 0.0
    # elapsed=0.0 → format_duration(0.0) → '0.0s'
    assert str(sw) == "0.0s"


def test_context_manager(monkeypatch):
    clock = _FakeClock()
    _patch(monkeypatch, clock)
    with Stopwatch() as sw:
        clock.advance(90)
    assert sw.elapsed == 90.0
    assert str(sw) == "1m 30s"


def test_manual_start_stop(monkeypatch):
    clock = _FakeClock()
    _patch(monkeypatch, clock)
    sw = Stopwatch().start()
    assert sw.started_at == 1000.0
    clock.advance(3700)
    sw.stop()
    assert sw.elapsed == 3700.0
    assert str(sw) == "1h 1m"


def test_running_str(monkeypatch):
    clock = _FakeClock()
    _patch(monkeypatch, clock)
    sw = Stopwatch().start()
    clock.advance(45)
    # Not stopped yet — should show running elapsed.
    assert str(sw) == "45.0s"


def test_stop_without_start_is_noop(monkeypatch):
    clock = _FakeClock()
    _patch(monkeypatch, clock)
    sw = Stopwatch()
    sw.stop()  # no-op
    assert sw.elapsed == 0.0
    assert sw.started_at is None
