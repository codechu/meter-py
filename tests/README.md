# Tests — codechu-meter

Run the suite from the repo root:

```bash
pytest -q
```

With coverage:

```bash
pytest --cov=codechu_meter --cov-report=term-missing
```

## Coverage gate

The coverage floor is **90 %**. PRs that drop below it are rejected;
add tests with your change.

## Conventions

- **Deterministic clock.** All time-dependent tests monkeypatch
  `time.monotonic` via a tiny fake clock. Don't sleep — advance the
  fake clock instead. That keeps the suite fast and free of
  flakes.
- Cover the cold-start cases: empty rate estimator, ETA with
  zero / one / two updates, EMA vs linear divergence on bursty
  input.
