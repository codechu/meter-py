# Contributing to codechu-meter

Thanks for thinking about contributing. `codechu-meter` is a small
stdlib-only library of measurement primitives — `Stopwatch`,
`RateEstimator`, `ETAEstimator`. Its only runtime dependency is
[`codechu-fmt`](https://github.com/codechu/fmt-py), used for
human-readable `__str__`.

This library was originally extracted from [Disk Cleaner](https://github.com/codechu/disk-cleaner)
via [codechu/cli-py](https://github.com/codechu/cli-py), but is maintained
independently with its own release cadence.

## Development setup

```bash
git clone https://github.com/codechu/codechu-meter-py.git
cd codechu-meter-py
pip install -e ".[dev]"
pytest -q
ruff check src tests
```

## Workflow

- Branch names: `feature/<short>`, `fix/<short>`, `refactor/<short>`,
  `docs/<short>`, `test/<short>`.
- Commit messages: [Conventional Commits](https://www.conventionalcommits.org/)
  (`feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`).
- One change per PR.

## Tests

- `pytest -q` must pass; coverage stays at **≥90 %**.
- All time math must go through `time.monotonic`. Tests
  monkeypatch `time.monotonic` for determinism — please do the
  same when you add new clock-dependent code.
- Cover the edge cases: empty observations, zero elapsed, NaN
  guards, mode='ema' vs 'linear' divergence on bursty input.

## Public API discipline

The public surface is `Stopwatch`, `RateEstimator`, and
`ETAEstimator`. Anything else is internal.

No new runtime dependencies beyond `codechu-fmt`.

## Style

- `ruff check` + `ruff format` clean.
- Type hints on public APIs (`from __future__ import annotations`).

## Security

If you find a security issue, see [SECURITY.md](SECURITY.md) — do not
open a public issue for it.

## Developer Certificate of Origin (DCO)

Every commit must be signed off with the [DCO](https://developercertificate.org/).
The sign-off certifies that you wrote the patch, or otherwise have the
right to submit it under the project's license. Add a line to your
commit message:

```
Signed-off-by: Your Name <you@example.com>
```

`git commit -s` does this automatically. PRs without sign-off will
be asked to amend before merge.

Contributions are accepted under the project's license (see
[LICENSE](LICENSE)).
