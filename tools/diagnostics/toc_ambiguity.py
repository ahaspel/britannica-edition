"""Count TOC entries that could benefit from LLM disambiguation."""
import json
import re
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

# Article index
article_idx = json.load(
    open("data/derived/articles/index.json", encoding="utf-8"))

# Map normalized title → list of (filename, title) candidates
def _norm(s):
    return re.sub(r"[^A-Z0-9]+", "", s.upper())

title_candidates = defaultdict(list)
for e in article_idx:
    if e.get("article_type") != "article":
        continue
    title = e["title"]
    filename = e["filename"]
    n = _norm(title)
    title_candidates[n].append((filename, title))
    # Also register the SURNAME part for "SURNAME, FIRSTNAME" titles
    if "," in title:
        surname = title.split(",", 1)[0].strip()
        title_candidates[_norm(surname)].append((filename, title))

toc = json.load(open("data/derived/classified_toc.json", encoding="utf-8"))

ambiguous = []
unresolved = []
def walk(node, path):
    name = node.get("name", "")
    cur = path + ("/" + name if name else "")
    for a in node.get("articles", []):
        target = a.get("target", "")
        filename = a.get("filename")
        n = _norm(target)
        cands = title_candidates.get(n, [])
        if len(cands) > 1:
            ambiguous.append((cur, target, filename, cands))
        elif not cands:
            unresolved.append((cur, target))
    for ch in node.get("children", []):
        walk(ch, cur)
    for sub in node.get("subsections", []):
        walk(sub, cur)

for cat in toc["categories"]:
    walk(cat, "")

print(f"Ambiguous TOC entries (multi-candidate): {len(ambiguous)}")
print(f"Unresolved TOC entries (no candidate): {len(unresolved)}")
print()

# Show distribution of ambiguity
from collections import Counter
by_target = Counter(x[1] for x in ambiguous)
print("Top ambiguous targets:")
for t, n in by_target.most_common(15):
    cands = title_candidates[_norm(t)]
    print(f"  {n:>4}  {t!r} — {len(cands)} candidates: {[c[1][:40] for c in cands[:4]]}")
