"""Scan C# files with the rule set and optionally apply autofixes."""
from dataclasses import dataclass, asdict
from pathlib import Path

from .rules import RULES


@dataclass
class Finding:
    rule_id: str
    severity: str
    file: str
    line: int
    title: str
    why: str
    fixable: bool


def _line_of(src: str, offset: int) -> int:
    return src.count("\n", 0, offset) + 1


def _in_line_comment(src: str, offset: int) -> bool:
    line_start = src.rfind("\n", 0, offset) + 1
    return "//" in src[line_start:offset]


def _matches(src: str, rules=RULES):
    for rule in rules:
        for m in rule.pattern.finditer(src):
            if _in_line_comment(src, m.start()):
                continue
            if rule.keep is None or rule.keep(src, m):
                yield rule, m


def scan_source(src: str, file: str = "<memory>", rules=RULES) -> list[Finding]:
    findings = [
        Finding(r.id, r.severity, file, _line_of(src, m.start()), r.title, r.why, r.fix is not None)
        for r, m in _matches(src, rules)
    ]
    return sorted(findings, key=lambda f: (f.line, f.rule_id))


def fix_source(src: str, rules=RULES) -> str:
    """Apply every available autofix. Edits are applied right-to-left so offsets stay valid."""
    edits = [(m.start(), m.end(), r.fix(m)) for r, m in _matches(src, rules) if r.fix]
    for start, end, text in sorted(edits, reverse=True):
        src = src[:start] + text + src[end:]
    return src


def iter_cs_files(path: Path):
    if path.is_file():
        yield path
    else:
        yield from sorted(p for p in path.rglob("*.cs") if "bin" not in p.parts and "obj" not in p.parts)


def to_dict(f: Finding) -> dict:
    return asdict(f)
