"""Find articles where `<section begin="…">` should have started a new
article but the Author wikilink spans multiple lines, causing
has_bold_heading to miss the bold title."""
import glob
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

from britannica.db.models import Article
from britannica.db.session import SessionLocal

s = SessionLocal()
existing = {
    (a.volume, a.page_start, a.section_name or "")
    for a in s.query(Article).all()
}
s.close()

candidates = []
for f in sorted(glob.glob("data/raw/wikisource/vol_*/vol*-page*.json")):
    try:
        d = json.load(open(f, encoding="utf-8"))
    except Exception:
        continue
    raw = d.get("raw_text", "")
    # Find each section begin
    for m in re.finditer(
        r'<section\s+begin="([^"]+)"\s*/?>',
        raw,
    ):
        sec_name = m.group(1)
        start = m.end()
        # Get next 400 chars of content after the section begin
        chunk = raw[start:start + 500]
        # Does it open with [[Author:...|'''...''' …]] that spans lines?
        author_open = re.search(
            r"\[\[Author:[^\]|]+\|'''",
            chunk,
        )
        if not author_open:
            continue
        # Is there a newline before the next ]] ?
        link_content = chunk[author_open.end():]
        first_nl = link_content.find("\n")
        first_close = link_content.find("]]")
        if first_nl >= 0 and (first_close < 0 or first_nl < first_close):
            candidates.append({
                "file": f.rsplit("\\", 1)[-1],
                "volume": d.get("volume"),
                "page": d.get("page_number"),
                "section": sec_name,
                "context": chunk[:250],
            })

print(f"Multi-line Author-wrap candidates: {len(candidates)}")
print()
for c in candidates[:25]:
    # Check if an article with this section name exists in DB
    key = (c["volume"], c["page"], c["section"])
    in_db = key in existing
    marker = "✓" if in_db else "✗ MISSING"
    print(f"  {marker}  vol{c['volume']} ws{c['page']}: section={c['section']!r}")
