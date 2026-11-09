# relscan

A reliability scanner for C# services. It detects code patterns that cause production incidents, validates its own rules with a test harness, proposes safe fixes, and gates CI.

The pattern: **detect, validate, remediate, gate.**

This is a clean-room implementation of an approach to static analysis and rule validation. The domain here is common reliability issues in older .NET services.

```
relscan/rules.py      What to detect: rules defined as data
relscan/scanner.py    How detection and fixing work
relscan/cli.py        How people and CI use it
tests/                How the rules prove they are correct
.github/workflows/    How it runs on every change
samples/              A legacy-style service to scan
```

---

## 1. Rules are data

`relscan/rules.py`

Each rule is a frozen dataclass: an ID, a severity, a pattern, the reason it matters, and two optional hooks.

| ID | Severity | Catches | Why it matters | Autofix |
|---|---|---|---|---|
| REL001 | error | `new HttpClient()` per call | Socket exhaustion under load | No |
| REL002 | error | `.Result`, `.Wait()`, `.GetAwaiter().GetResult()` | Thread pool starvation and deadlocks | No |
| REL003 | error | `async void` outside event handlers | Exceptions cannot be caught, process crashes | Yes |
| REL004 | warning | Empty `catch {}` | Failures disappear from logs and alerts | No |

- **`keep`** is an optional false-positive filter. `async void` is acceptable on UI event handlers, so REL003 skips any match where the line contains `EventArgs`.
- **`fix`** is an optional function that returns replacement text. Only REL003 has one.
- Adding a rule means one entry in this file plus one fixture folder. No other code changes.

## 2. Rules prove themselves before they judge code

`tests/fixtures/<RULE_ID>/` and `tests/test_rules.py`

Every rule must satisfy a contract:

| Fixture | Requirement | Guards against |
|---|---|---|
| `bad.cs` | Rule must fire | False negatives |
| `good.cs` | Rule must stay silent | False positives |
| `fixed.cs` | Autofix output must match exactly, then scan clean | Broken or partial fixes |

Additional checks: autofix is idempotent (running it twice changes nothing), line numbers are exact, and a rule with no fixtures fails the build.

Tests are parametrized over the rule list, so a new rule is tested automatically.

```bash
python3 -m pytest -q        # 15 passed
```

**Why this matters:** during development, a comment containing the words "async void" triggered REL003. The `good.cs` fixture caught it. Comment lines are now skipped for every rule. A scanner is only as useful as its false positive rate, because noisy rules get ignored.

## 3. Detection and remediation

`relscan/scanner.py`

- **Line numbers:** count newlines before the match offset.
- **Comment skipping:** a match is ignored if `//` appears earlier on the same line.
- **Applying fixes right to left:** each fix can change the length of the text. Applying edits from the end of the file backwards keeps every earlier offset valid.

## 4. Running it

`relscan/cli.py` and `samples/ServicePro/WorkOrderService.cs`

```bash
python3 -m relscan samples                  # 5 findings, exit code 1
python3 -m relscan samples --diff           # proposed fix as a reviewable patch
python3 -m relscan samples --format json    # machine-readable output
python3 -m relscan samples --fix            # apply fixes to disk
```

- **Exit code** is 1 only when error-severity findings exist. That is the CI gate.
- **`--diff` by default, `--fix` only on request.** Remediation stays human-reviewed.
- **Only mechanical fixes are automated.** `async void` to `async Task` is a signature change with no behavior risk. Fixing HttpClient needs dependency injection wiring, and fixing sync-over-async means making the whole call chain async. Those need judgment, so they are report-only.
- **JSON output** is the integration point for dashboards, APIs, or other tools.

## 5. Pipeline

`.github/workflows/relscan.yml`

```
validate-rules  ->  scan  ->  publish findings.json + autofix.patch  ->  gate
```

- `needs: validate-rules` means the scan only runs if the rules pass their harness.
- The report and patch steps use `|| true` so artifacts are always published, even though the scanner exits 1.
- The final step has no `|| true`. That step is the gate.
- Results are build outputs, not committed files. They are downloadable from each run under Artifacts.

A failing scan job is the expected result on the sample: the gate is blocking a service with deadlock and socket exhaustion risks.

## 6. Design decisions

- **Regex instead of Roslyn.** No dependencies, fast to build, easy to read. The cost is no type awareness: `.Result` on something that is not a Task is a false positive, and block comments are not excluded.
- **Warnings do not fail the build.** A legacy codebase can adopt the scanner without a flag day. Rules get promoted to errors as the backlog burns down.
- **Contract tests over example tests.** Fixtures define what correct means for each rule, and the harness enforces it for every rule.

## 7. Next steps

- **Roslyn analyzer port** for type-aware rules. Fixtures and harness carry over unchanged.
- **Baseline file** so existing findings are tracked and only new findings fail the build.
- **SARIF output** so findings appear inline on pull requests.
- **Agent-assisted remediation** for fixes that need judgment. An LLM proposes the patch, then it runs through the same harness and rescan before human review. The harness is what makes generated fixes trustworthy.
- **Peak-load readiness rules** such as outbound calls with no retry policy, no 429 handling, or retries without jitter.
