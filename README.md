# relscan

A small reliability scanner for C# services. It finds patterns that cause production incidents, validates its own rules with a test harness, proposes safe autofixes, and runs as a gated CI pipeline.

Standalone, clean-room implementation of the ideas behind static-analysis reliability work: **detect, validate, remediate, gate.**

## Architecture

```
rules.py      Rules are data: id, severity, regex, false-positive filter, optional autofix
scanner.py    Runs rules over source, maps matches to line numbers, applies fixes right-to-left
cli.py        relscan <path> [--format json] [--diff] [--fix]   exit 1 on errors
tests/        Harness: every rule proves itself against fixtures before it can judge real code
.github/      Pipeline: validate rules -> scan -> publish findings + patch -> gate
```

## Rules

| ID | Severity | Catches | Why it matters | Autofix |
|---|---|---|---|---|
| REL001 | error | `new HttpClient()` per call | Socket exhaustion under load | No |
| REL002 | error | `.Result`, `.Wait()`, `.GetAwaiter().GetResult()` | Deadlocks, thread pool starvation | No |
| REL003 | error | `async void` (non event handler) | Unobservable exceptions crash the process | Yes, `async Task` |
| REL004 | warning | Empty `catch {}` | Failures vanish from logs and alerts | No |

## Test harness (rule validation)

Each rule has a fixture folder, `tests/fixtures/<ID>/`, and the harness enforces a contract:

- `bad.cs` must trigger the rule (no false negatives)
- `good.cs` must not trigger it (no false positives)
- `fixed.cs` must equal the autofix output, and must scan clean
- Autofix must be idempotent, line numbers must be exact
- A rule with no fixtures fails the build

Adding a rule = one entry in `rules.py` + one fixture folder. The harness picks it up automatically.

## Pipeline

1. **validate-rules**: run the harness. If the scanner's rules are wrong, nothing downstream runs.
2. **scan**: scan the code, publish `findings.json` and `autofix.patch` as artifacts, fail on error-severity findings.

## Demo

```bash
python -m pytest -q                  # 15 passing: rules validated
python -m relscan samples            # 5 findings in a legacy-style service, exit 1
python -m relscan samples --diff     # proposed remediation as a reviewable patch
python -m relscan samples --format json
```

## Design decisions and tradeoffs

- **Regex, not Roslyn.** Fast to build, zero dependencies, easy to read. Cost: no semantic understanding, so `.Result` on a non-Task property is a false positive, and multi-line block comments are not excluded. Next step is a Roslyn analyzer for type-aware rules; the harness and fixtures carry over unchanged.
- **Autofix only when the fix is mechanical and safe.** `async void` to `async Task` is a signature change with no behavior risk in the method body. HttpClient and sync-over-async fixes need human judgment (DI wiring, async all the way up), so they are report-only.
- **Fixes are proposed as a patch by default.** `--diff` for review, `--fix` only when explicitly asked. Remediation stays human-approved.
- **Warnings don't fail the build.** Lets a legacy codebase adopt the scanner without a flag day. Promote rules to error as the backlog burns down.
- **The harness found a real bug during development:** a comment containing "async void" tripped REL003. The good.cs fixture caught it, and comment lines are now skipped for every rule.

## What I'd add next

- Roslyn analyzer port for type-aware rules
- SARIF output so findings show inline on PRs
- Baseline file so legacy findings are tracked but only new ones fail the build
- Bot that opens a PR with the autofix patch
