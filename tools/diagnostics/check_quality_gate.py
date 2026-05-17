"""Pre-deploy quality gate.  Reads the most recent quality_report JSON
and aborts (exit non-zero) if key counters regress past hard thresholds.

Thresholds are set ABOVE the post-rebuild expected values for the
2026-05-14 clean baseline, with headroom for legitimate improvement.
Tightening them later is fine; loosening them in response to a regression
defeats the gate — fix the underlying issue instead.
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

REPORTS = sorted(glob.glob("data/derived/quality_reports/report_*.json"))
if not REPORTS:
    print("FAIL: no quality report found", file=sys.stderr)
    sys.exit(2)

with open(REPORTS[-1], encoding="utf-8") as f:
    r = json.load(f)

db = r.get("db", {})
files = r.get("files", {}).get("issues", {})

# Thresholds based on the 2026-05-14 clean deploy:
#   total_articles      = 36,663
#   xrefs_resolved      = 31,954
#   xrefs_unresolved    =  5,131
#   stray_close_braces  =      9
#   stray_wiki_italic   =      2
THRESHOLDS = {
    # (field_path, comparison, threshold)
    ("db", "total_articles"):       ("min", 36_000),
    ("db", "xrefs_resolved"):       ("min", 28_000),
    ("db", "xrefs_unresolved"):     ("max", 10_000),
    ("files", "stray_close_braces"):("max",    50),
    ("files", "stray_wiki_italic"): ("max",   200),
    ("files", "stray_braces"):      ("max",    50),
    ("files", "pipe_leak"):         ("max",    50),
    ("files", "html_tag"):          ("max",    50),
}

failures: list[str] = []

def get(field: tuple[str, str]) -> int | None:
    if field[0] == "db":
        return db.get(field[1])
    return files.get(field[1])

print(f"Quality gate vs report: {Path(REPORTS[-1]).name}")
for field, (cmp, threshold) in THRESHOLDS.items():
    value = get(field)
    if value is None:
        print(f"  WARN  {'/'.join(field):35s} no value in report")
        continue
    if cmp == "min":
        ok = value >= threshold
        op = ">="
    else:
        ok = value <= threshold
        op = "<="
    status = "OK  " if ok else "FAIL"
    print(f"  {status}  {'/'.join(field):35s} {value:>7d}  {op} {threshold}")
    if not ok:
        failures.append(f"{'/'.join(field)} = {value}, expected {op} {threshold}")

if failures:
    print()
    print("DEPLOY BLOCKED — fix these and re-run rebuild:")
    for fail in failures:
        print(f"  - {fail}")
    sys.exit(1)

print("\nAll gates passed.")
