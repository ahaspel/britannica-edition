import glob
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ATTR_RE = re.compile(r"nowrap|colspan|rowspan|cellpadding")

for f in sorted(glob.glob("data/derived/articles/*.json")):
    if "index.json" in f or "contributors.json" in f:
        continue
    try:
        a = json.load(open(f, encoding="utf-8"))
    except Exception:
        continue
    body = a.get("body", "")
    check = re.sub(
        r"\u00abHTMLTABLE:.*?\u00ab/HTMLTABLE\u00bb", "",
        body, flags=re.DOTALL)
    if ATTR_RE.search(check):
        occs = list(ATTR_RE.finditer(check))
        print(f"\n{a.get('stable_id')} — {a.get('title')} ({len(occs)} matches)")
        for m in occs[:2]:
            i = m.start()
            print(f"  {check[max(0, i-100):i+100]!r}")
