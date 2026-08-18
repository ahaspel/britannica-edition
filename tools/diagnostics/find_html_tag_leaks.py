import glob

from britannica.export.corpus import load_corpus
import json
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")

TAG_RE = re.compile(
    r"<(?:table|tr|td|th|div|span|br|sub|sup|ref|poem|score|math)\b[^>]*>",
    re.IGNORECASE,
)

hits = []
tag_counter = Counter()
# Read through the corpus loader, which is TOTAL: it applies NON_ARTICLE
# itself and RAISES on a file it cannot read, instead of skipping it.  A
# leak finder that skips an article reports it clean — the one failure a
# leak oracle must never have ([[feedback_honesty_surface_failures]]).
for _path, a in sorted(load_corpus()[0].items()):
    f = str(_path)
    body = a.get("body", "")
    if not body:
        continue
    clean = re.sub(
        r"\u00abTABLE:.*?\u00ab/TABLE\u00bb", "",
        body, flags=re.DOTALL)
    clean = re.sub(
        r"\u00abMATH:.*?\u00ab/MATH\u00bb", "", clean, flags=re.DOTALL)
    matches = TAG_RE.findall(clean)
    if matches:
        hits.append((a.get("id"), a.get("title"), a.get("volume"),
                     matches, clean))
        for m in matches:
            tag_name = re.match(r"<(\w+)", m).group(1).lower()
            tag_counter[tag_name] += 1

print(f"Total files with stray html tags: {len(hits)}")
print("\nBy tag type:")
for tag, n in tag_counter.most_common():
    print(f"  <{tag}>: {n}")

print("\nFirst 15 offenders with context:")
for aid, title, vol, matches, clean in hits[:15]:
    print(f"\n  {aid} vol{vol} {title!r}:")
    for m in matches[:3]:
        i = clean.find(m)
        print(f"    tag: {m}")
        print(f"    ctx: ...{clean[max(0,i-80):i+len(m)+80]!r}...")
