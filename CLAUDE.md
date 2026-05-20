# CLAUDE.md — codechu-meter

Bootstrap per `codechu-org/ai/AGENTS.md` §0 before any work. Prefer
the local clone at `$org_home/codechu-org/ai/AGENTS.md` (if
`~/.config/codechu/config.toml` has `org_home` set); otherwise
WebFetch the public raw URL
<https://raw.githubusercontent.com/codechu/codechu-org/main/ai/AGENTS.md>.
This file lists only product-local overrides.

## Product-local notes

- Pure stdlib + a single dependency on `codechu-fmt` for `__str__`.
  Do not introduce any other runtime dependency.
- Public API: `Stopwatch`, `RateEstimator`, `ETAEstimator`.
- All time math goes through `time.monotonic` — never `time.time` —
  so wall-clock jumps don't poison the measurement. Tests
  monkeypatch `time.monotonic` for determinism; preserve that.
- `ETAEstimator.eta()` returns `None` until enough samples; never
  raise on cold start.
- Coverage target: ≥90 %.

## Discipline reminders (org rules apply)

- Conventional Commits, no AI signature.
- No `--no-verify`, no force push, no unapproved publish.
- See `codechu-org/ai/AGENTS.md` for the full list.
