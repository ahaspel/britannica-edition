"""Readings that set a system of equations in \\begin{align}…\\end{align},
which KaTeX parses only in display mode — the site hands every formula
inline, and the formula fails (vol 28 p. 426, vol 25 pp. 204, 657).
\\begin{aligned} sets the same lines inline.  Corrected in each reading
(recorded in provenance.corrected) and in the patches made from it
(data/staging/patches/kept.json), so the installed patch and the reading
agree.  Usage: fix_align.py  (book root)"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))
from paths import READINGS, WORK

from wikikit.scan import supplied

NOTE = "\\begin{align} set as \\begin{aligned}: KaTeX parses align only in display mode (2026-10-13)"


BEGIN, END = "\\begin{align}", "\\end{align}"


def fix(s: str) -> str:
    return s.replace(BEGIN, "\\begin{aligned}").replace(END, "\\end{aligned}")


fixed = []
for f in sorted(READINGS.glob("vol_*/vol*-page*.json")):
    d = json.loads(f.read_text(encoding="utf-8"))
    p = d["provenance"]
    items = [k for k, v in p["readings"].items() if isinstance(v, str) and BEGIN in v]
    if not items:
        continue
    for k in items:
        p["readings"][k] = fix(p["readings"][k])
    if NOTE not in p.setdefault("corrected", []):
        p["corrected"].append(NOTE)
    supplied.reassemble(d, carried=False)
    assert BEGIN not in d["raw_text"], f.stem
    f.write_bytes((json.dumps(d, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    fixed.append(f.stem)
kept = WORK / "kept.json"
n = 0
if kept.exists():
    ok = json.loads(kept.read_text(encoding="utf-8"))
    for ps in ok.values():
        for x in ps:
            if BEGIN in x["new"]:
                x["new"] = fix(x["new"])
                n += 1
    kept.write_text(json.dumps(ok, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"readings corrected: {fixed}; patches corrected: {n}")
