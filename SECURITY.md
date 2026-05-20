# Security policy

`codechu-meter` is a pure-stdlib measurement library (with a single
dependency on `codechu-fmt`). Its public classes accept floats and
return floats / strings — no I/O, no subprocess, no deserialization.

## Supported versions

| Version | Supported |
|---|:---:|
| `main` branch | ✅ |
| Latest minor release (0.x) | ✅ |
| Older releases | ❌ |

## Reporting a vulnerability

### Preferred path — GitHub Security Advisory (private)

Open a **private** advisory at
[github.com/codechu/codechu-meter-py/security/advisories/new](https://github.com/codechu/codechu-meter-py/security/advisories/new).

### Alternative — Email

Write to `security@codechu.com`.

## Scope — what to report

**In scope:**

- Uncaught exceptions on valid float inputs (NaN, ±inf, 0, very
  large values).
- Resource exhaustion — bounded-time operations that become
  unbounded on adversarial inputs (e.g. observe loops, rolling-window
  trimming).
- Incorrect monotonic-clock handling that could mislead a caller
  into security-sensitive decisions (e.g. rate-limiting heuristics).

**Out of scope:**

- Rate or ETA "inaccuracy" within reasonable bounds — these are
  estimates, not measurements of ground truth.

## Process

Reports are reviewed on a best-effort basis — no fixed SLA. We aim
for coordinated disclosure within **90 days** of the report.

## Public disclosure

Once a confirmed fix is released:

- A summary is added to the CHANGELOG under the `### Security`
  category.
- A GitHub Security Advisory is published.
- If a CVE was assigned, its number is referenced.
