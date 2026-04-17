"""Count files by leak type and overlap with queued fixes."""
import glob
import json
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")

TAG_RE = re.compile(
    r"<(?:table|tr|td|th|div|span|br|sub|sup|ref|poem|score|math)\b[^>]*>",
    re.IGNORECASE,
)

br_only = 0
sub_sup_only = 0
td_tr_only = 0
mixed = 0
unclassified = 0
by_context = Counter()

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
    matches = TAG_RE.findall(clean)
    if not matches:
        continue

    kinds = set()
    for m in matches:
        name = re.match(r"<(\w+)", m).group(1).lower()
        kinds.add(name)

    # Determine context: are br's in {{IMG:|caption}}? sub's near Langle?
    has_caption_br = bool(re.search(
        r"\{\{IMG:[^}]*<br[^>]*>", clean))
    has_chem_sub = bool(re.search(
        r"\{\{IMG:L(?:angle|Rangle|angleIT|RangleIT)\.svg\}\}",
        clean))

    if kinds == {"br"} and has_caption_br:
        br_only += 1
        by_context["caption_br (queued fix)"] += 1
    elif kinds <= {"sub", "sup"} and has_chem_sub:
        sub_sup_only += 1
        by_context["chem_formula_sub (queued fix)"] += 1
    elif kinds == {"br"}:
        br_only += 1
        by_context["caption_br_no_IMG_context"] += 1
    elif kinds <= {"sub", "sup"}:
        sub_sup_only += 1
        by_context["sub_sup_unclassified"] += 1
    elif kinds == {"td"} or kinds == {"tr"} or kinds == {"td", "tr"}:
        td_tr_only += 1
        by_context["table_escape"] += 1
    else:
        mixed += 1
        by_context[f"mixed: {sorted(kinds)}"] += 1

print(f"Total files with html_tag issue: {br_only + sub_sup_only + td_tr_only + mixed}")
print(f"\nBy category:")
for ctx, n in by_context.most_common():
    print(f"  {n:>3}  {ctx}")
