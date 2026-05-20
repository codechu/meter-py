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


# --- v0.3.0: named sections ---


def test_sections_initially_empty():
    sw = Stopwatch()
    assert sw.sections == {}


def test_section_records_elapsed(monkeypatch):
    clock = _FakeClock()
    _patch(monkeypatch, clock)
    sw = Stopwatch().start()
    with sw.section("parse"):
        clock.advance(0.5)
    assert sw.sections == {"parse": 0.5}


def test_section_accumulates(monkeypatch):
    clock = _FakeClock()
    _patch(monkeypatch, clock)
    sw = Stopwatch().start()
    with sw.section("io"):
        clock.advance(1.0)
    with sw.section("io"):
        clock.advance(2.0)
    assert sw.sections["io"] == 3.0


def test_section_sequential(monkeypatch):
    clock = _FakeClock()
    _patch(monkeypatch, clock)
    sw = Stopwatch().start()
    with sw.section("a"):
        clock.advance(1.0)
    with sw.section("b"):
        clock.advance(2.0)
    assert sw.sections == {"a": 1.0, "b": 2.0}


def test_section_nested(monkeypatch):
    clock = _FakeClock()
    _patch(monkeypatch, clock)
    sw = Stopwatch().start()
    with sw.section("outer"):
        clock.advance(1.0)
        with sw.section("inner"):
            clock.advance(2.0)
        clock.advance(0.5)
    # outer measures wall time including inner: 1.0 + 2.0 + 0.5 = 3.5
    assert sw.sections["outer"] == 3.5
    assert sw.sections["inner"] == 2.0


def test_section_records_even_on_exception(monkeypatch):
    clock = _FakeClock()
    _patch(monkeypatch, clock)
    sw = Stopwatch().start()
    try:
        with sw.section("risky"):
            clock.advance(0.25)
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    assert sw.sections == {"risky": 0.25}


def test_start_clears_sections(monkeypatch):
    clock = _FakeClock()
    _patch(monkeypatch, clock)
    sw = Stopwatch().start()
    with sw.section("a"):
        clock.advance(1.0)
    sw.start()
    assert sw.sections == {}


def test_section_independent_of_elapsed(monkeypatch):
    clock = _FakeClock()
    _patch(monkeypatch, clock)
    sw = Stopwatch().start()
    clock.advance(10.0)  # untracked
    with sw.section("part"):
        clock.advance(1.0)
    clock.advance(10.0)  # untracked
    sw.stop()
    assert sw.elapsed == 21.0
    assert sw.sections == {"part": 1.0}
