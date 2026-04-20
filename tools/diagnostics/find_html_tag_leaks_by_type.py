"""Categorize html_tag leaks by context. Reports:
  * <br>/<sup> inside {{IMG:...}} captions
  * <td>/<tr> in body prose (table leak)
  * anything else
"""
import glob
import json
import re
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

TAG_RE = re.compile(
    r"<(?:table|tr|td|th|div|span|br|sub|sup|ref|poem|score|math)\b[^>]*>",
    re.IGNORECASE,
)

IMG_BLOCK_RE = re.compile(r"\{\{IMG:[^}]*\}\}")


def context(clean, pos, width=70):
    s = max(0, pos - width)
    e = min(len(clean), pos + width)
    snippet = clean[s:e].replace("\n", "\\n")
    return snippet


buckets = defaultdict(list)  # category -> list[(id, title, vol, tag, ctx)]

for f in sorted(glob.glob("data/derived/articles/*.json")):
    if "index.json" in f or "contributors.json" in f:
        continue
    try:
        a = json.load(open(f, encoding="utf-8"))
    except Exception:
        continue
    body = a.get("body", "")
    if not body:
        continue
    clean = re.sub(
        r"\u00abHTMLTABLE:.*?\u00ab/HTMLTABLE\u00bb", "",
        body, flags=re.DOTALL)
    clean = re.sub(
        r"\u00abMATH:.*?\u00ab/MATH\u00bb", "", clean, flags=re.DOTALL)

    # Identify IMG block ranges
    img_spans = [(m.start(), m.end()) for m in IMG_BLOCK_RE.finditer(clean)]

    def in_img(pos):
        for s, e in img_spans:
            if s <= pos < e:
                return True
        return False

    for m in TAG_RE.finditer(clean):
        tag = m.group(0)
        tag_name = re.match(r"<(\w+)", tag).group(1).lower()
        cat = "other"
        if in_img(m.start()):
            cat = f"{tag_name}_in_IMG"
        else:
            cat = f"{tag_name}_in_prose"
        buckets[cat].append(
            (a.get("id"), a.get("title"), a.get("volume"), tag,
             context(clean, m.start()))
        )

print("Category counts:")
for cat in sorted(buckets, key=lambda c: -len(buckets[c])):
    print(f"  {cat}: {len(buckets[cat])}")

for cat in sorted(buckets, key=lambda c: -len(buckets[c])):
    print(f"\n=== {cat} ({len(buckets[cat])}) ===")
    # Dedupe by article to show range of titles
    seen_arts = set()
    for aid, title, vol, tag, ctx in buckets[cat]:
        if (aid, title) in seen_arts:
            continue
        seen_arts.add((aid, title))
        print(f"  {aid} vol{vol} {title!r}")
        print(f"    {tag}  …{ctx}…")
        if len(seen_arts) >= 8:
            print(f"  ... and {len({x[0] for x in buckets[cat]}) - 8} more articles")
            break
