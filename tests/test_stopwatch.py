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


def test_initial_state(monkeypatch):
    clock = _FakeClock()
    _patch(monkeypatch, clock)
    sw = Stopwatch()
    assert sw.elapsed == 0.0
    assert sw.started_at is None


def test_context_manager(monkeypatch):
    clock = _FakeClock()
    _patch(monkeypatch, clock)
    with Stopwatch() as sw:
        clock.advance(90)
    assert sw.elapsed == 90.0


def test_context_manager_returns_self(monkeypatch):
    clock = _FakeClock()
    _patch(monkeypatch, clock)
    sw = Stopwatch()
    with sw as inner:
        assert inner is sw


def test_context_manager_stops_on_exception(monkeypatch):
    clock = _FakeClock()
    _patch(monkeypatch, clock)
    sw = Stopwatch()
    try:
        with sw:
            clock.advance(5)
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    assert sw.elapsed == 5.0


def test_manual_start_stop(monkeypatch):
    clock = _FakeClock()
    _patch(monkeypatch, clock)
    sw = Stopwatch().start()
    assert sw.started_at == 1000.0
    clock.advance(3700)
    sw.stop()
    assert sw.elapsed == 3700.0


def test_stop_without_start_is_noop(monkeypatch):
    clock = _FakeClock()
    _patch(monkeypatch, clock)
    sw = Stopwatch()
    sw.stop()  # no-op
    assert sw.elapsed == 0.0
    assert sw.started_at is None


def test_no_str_format_coupling():
    # v0.2.0: Stopwatch has no __str__ override — uses object default.
    assert "Stopwatch" in str(Stopwatch())
