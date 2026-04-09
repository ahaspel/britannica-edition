"""Find articles with leaked HTML attributes in the body text."""
import json, re, sys, io, os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

attr_re = re.compile(
    r'(?:style|class|align|valign|bgcolor|cellpadding|cellspacing|border|width|height)\s*=\s*["\x27]?[^"\x27>\s]+',
    re.IGNORECASE,
)

for f in sorted(os.listdir("data/derived/articles")):
    if f in ("index.json", "contributors.json", "front_matter.json"):
        continue
    if not f.endswith(".json"):
        continue
    data = json.loads(open(os.path.join("data/derived/articles", f), encoding="utf-8").read())
    body = data.get("body", "")
    matches = attr_re.findall(body)
    if matches:
        print(f"{f}:")
        for m in matches[:5]:
            idx = body.find(m)
            ctx = body[max(0, idx - 40) : idx + len(m) + 40]
            print(f"  ...{ctx}...")
        if len(matches) > 5:
            print(f"  ({len(matches)} total)")
        print()
