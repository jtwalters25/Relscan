"""Reliability rules for C# source.

Each rule is data: an id, a regex, a message, and an optional fix.
Adding a rule means adding one entry here plus a fixture folder in tests/fixtures/<ID>/.
"""
import re
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass(frozen=True)
class Rule:
    id: str
    severity: str  # "error" or "warning"
    title: str
    why: str
    pattern: re.Pattern
    # Optional filter to drop false positives: (source, match) -> keep?
    keep: Optional[Callable[[str, re.Match], bool]] = None
    # Optional autofix: (match) -> replacement text for the matched span
    fix: Optional[Callable[[re.Match], str]] = None


def _not_event_handler(src: str, m: re.Match) -> bool:
    # async void is acceptable for UI/event handlers: (object sender, XEventArgs e)
    line_end = src.find("\n", m.end())
    rest_of_line = src[m.end(): line_end if line_end != -1 else len(src)]
    return "EventArgs" not in rest_of_line


RULES = [
    Rule(
        id="REL001",
        severity="error",
        title="HttpClient created per call",
        why="Creating HttpClient per request exhausts sockets under load. Use IHttpClientFactory or a shared instance.",
        pattern=re.compile(r"new\s+HttpClient\s*\("),
    ),
    Rule(
        id="REL002",
        severity="error",
        title="Sync-over-async blocking call",
        why=".Result / .Wait() / GetAwaiter().GetResult() block a thread and can deadlock or starve the thread pool.",
        pattern=re.compile(r"\.(?:Result\b|Wait\(\s*\)|GetAwaiter\(\)\.GetResult\(\))"),
    ),
    Rule(
        id="REL003",
        severity="error",
        title="async void method",
        why="Exceptions in async void cannot be caught by callers and crash the process. Return Task instead.",
        pattern=re.compile(r"\basync\s+void\b"),
        keep=_not_event_handler,
        fix=lambda m: "async Task",
    ),
    Rule(
        id="REL004",
        severity="warning",
        title="Empty catch block",
        why="Swallowed exceptions hide failures from logs, alerts, and retries.",
        pattern=re.compile(r"catch\s*(?:\([^)]*\))?\s*\{\s*\}"),
    ),
]

RULES_BY_ID = {r.id: r for r in RULES}
