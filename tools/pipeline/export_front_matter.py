"""Export front matter (dedication + editorial preface) to JSON."""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "src")

from britannica.db.session import SessionLocal
from britannica.db.models import SourcePage

session = SessionLocal()

fm = {
    "dedication": {"title": "Dedication", "pages": [5], "body": ""},
    "preface": {
        "title": "Editorial Preface",
        "author": "Hugh Chisholm",
        "date": "December 10, 1910",
        "pages": list(range(6, 24)),
        "body": "",
    },
}

p = session.query(SourcePage).filter(
    SourcePage.volume == 1, SourcePage.page_number == 5
).first()
if p:
    fm["dedication"]["body"] = (p.cleaned_text or p.raw_text or "").strip()

body = ""
for pg in range(6, 24):
    p = session.query(SourcePage).filter(
        SourcePage.volume == 1, SourcePage.page_number == pg
    ).first()
    if not p:
        continue
    text = (p.cleaned_text or p.raw_text or "").strip()
    if not text:
        continue
    if not body:
        body = text
    elif body.endswith(("\n", ".", "!", "?", ":")):
        body = body + "\n\n" + text
    else:
        body = body + " " + text

fm["preface"]["body"] = body

with open("data/derived/articles/front_matter.json", "w", encoding="utf-8") as f:
    json.dump(fm, f, indent=2, ensure_ascii=False)

print("Exported front matter.")
session.close()
