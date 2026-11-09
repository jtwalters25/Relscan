"""CLI: python -m relscan <path> [--format text|json] [--fix] [--diff]

Exit codes: 0 = no error-severity findings, 1 = errors found (fails CI).
"""
import argparse
import difflib
import json
import sys
from pathlib import Path

from .scanner import fix_source, iter_cs_files, scan_source, to_dict


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="relscan", description="Reliability scanner for C# code")
    ap.add_argument("path", type=Path)
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument("--fix", action="store_true", help="write autofixes to disk")
    ap.add_argument("--diff", action="store_true", help="print autofixes as a unified diff, do not write")
    args = ap.parse_args(argv)

    findings = []
    for f in iter_cs_files(args.path):
        src = f.read_text(encoding="utf-8")
        if args.fix or args.diff:
            fixed = fix_source(src)
            if fixed != src:
                if args.diff:
                    sys.stdout.writelines(difflib.unified_diff(
                        src.splitlines(keepends=True), fixed.splitlines(keepends=True),
                        fromfile=f"a/{f}", tofile=f"b/{f}"))
                if args.fix:
                    f.write_text(fixed, encoding="utf-8")
                    src = fixed
        findings += scan_source(src, str(f))

    if args.format == "json":
        print(json.dumps([to_dict(x) for x in findings], indent=2))
    elif not args.diff:
        for x in findings:
            tag = " [autofix]" if x.fixable else ""
            print(f"{x.file}:{x.line}  {x.severity.upper():7} {x.rule_id}  {x.title}{tag}")
        errors = sum(x.severity == "error" for x in findings)
        print(f"\n{len(findings)} finding(s), {errors} error(s)")

    return 1 if any(x.severity == "error" for x in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
