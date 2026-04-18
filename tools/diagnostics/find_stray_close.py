import glob
import json
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")

ctx_samples = Counter()
count = 0
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
    if "}}" not in clean:
        continue
    if "TABLE}" in clean or "IMG:" in clean or "VERSE}" in clean:
        # quality check has these exclusions; if body only has these, skip
        pass
    # Find first stray }} and classify
    for m in re.finditer(r"\}\}", clean):
        i = m.start()
        # Skip if it's part of a recognized marker
        ctx = clean[max(0, i-40):i]
        if "TABLE" in ctx[-8:] or "IMG:" in ctx[-20:] or "VERSE" in ctx[-8:]:
            continue
        ctx_snip = clean[max(0, i-60):i+4]
        # Extract preceding ~30 chars as "what looks before }}"
        pre = clean[max(0, i-30):i].strip()
        ctx_samples[pre[-30:]] += 1
        if count < 10:
            print(f"{a.get('stable_id')} — {a.get('title')}")
            print(f"  ctx: {ctx_snip!r}")
            count += 1
        break

print(f"\nTop preceding patterns (last 30 chars before }}}}):")
for pat, n in ctx_samples.most_common(15):
    print(f"  {n:>4}  {pat!r}")
