"""List articles with stray '' wiki italic markers."""
import glob
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

for f in sorted(glob.glob("data/derived/articles/*.json")):
    if "index.json" in f or "contributors.json" in f:
        continue
    try:
        a = json.load(open(f, encoding="utf-8"))
    except Exception:
        continue
    body = a.get("body", "")
    clean = re.sub(
        r"\u00abHTMLTABLE:.*?\u00ab/HTMLTABLE\u00bb", "",
        body, flags=re.DOTALL)
    clean = re.sub(
        r"\u00abMATH:.*?\u00ab/MATH\u00bb", "", clean, flags=re.DOTALL)
    if "''" not in clean:
        continue

    occs = [m.start() for m in re.finditer(r"''", clean)]
    print(f"\n{a.get('stable_id')} — {a.get('title')} ({len(occs)} occurrences)")
    for i in occs[:3]:
        lo = max(0, i - 60)
        hi = min(len(clean), i + 80)
        print(f"  ...{clean[lo:hi]!r}...")
