"""Rule validation harness.

Contract every rule must meet, driven by tests/fixtures/<RULE_ID>/:
  bad.cs    -> rule MUST fire (no false negatives)
  good.cs   -> rule MUST NOT fire (no false positives)
  fixed.cs  -> if the rule has an autofix: fix(bad) == fixed, and fixed scans clean
"""
from pathlib import Path

import pytest

from relscan.rules import RULES, RULES_BY_ID
from relscan.scanner import fix_source, scan_source

FIXTURES = Path(__file__).parent / "fixtures"
RULE_IDS = [r.id for r in RULES]


def ids_found(src, rule_id):
    return [f for f in scan_source(src, rules=[RULES_BY_ID[rule_id]])]


@pytest.mark.parametrize("rule_id", RULE_IDS)
def test_every_rule_has_fixtures(rule_id):
    assert (FIXTURES / rule_id / "bad.cs").exists(), f"{rule_id} missing bad.cs"
    assert (FIXTURES / rule_id / "good.cs").exists(), f"{rule_id} missing good.cs"
    if RULES_BY_ID[rule_id].fix:
        assert (FIXTURES / rule_id / "fixed.cs").exists(), f"{rule_id} has autofix but no fixed.cs"


@pytest.mark.parametrize("rule_id", RULE_IDS)
def test_fires_on_bad(rule_id):
    assert ids_found((FIXTURES / rule_id / "bad.cs").read_text(), rule_id)


@pytest.mark.parametrize("rule_id", RULE_IDS)
def test_silent_on_good(rule_id):
    assert not ids_found((FIXTURES / rule_id / "good.cs").read_text(), rule_id)


@pytest.mark.parametrize("rule_id", [r.id for r in RULES if r.fix])
def test_autofix_matches_expected_and_scans_clean(rule_id):
    rule = [RULES_BY_ID[rule_id]]
    bad = (FIXTURES / rule_id / "bad.cs").read_text()
    expected = (FIXTURES / rule_id / "fixed.cs").read_text()
    fixed = fix_source(bad, rules=rule)
    assert fixed == expected
    assert not scan_source(fixed, rules=rule)


def test_autofix_is_idempotent():
    src = (FIXTURES / "REL003" / "bad.cs").read_text()
    once = fix_source(src)
    assert fix_source(once) == once


def test_line_numbers_are_correct():
    findings = scan_source((FIXTURES / "REL002" / "bad.cs").read_text())
    assert [f.line for f in findings] == [3, 4, 5]
