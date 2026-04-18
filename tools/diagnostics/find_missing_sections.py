"""Find `<section begin="Title Case, Name">` markers whose articles
aren't in the DB — candidates for swallowing by the lowercase-section-name
continuation rule in detect_boundaries."""
import glob
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

from britannica.db.models import Article
from britannica.db.session import SessionLocal

s = SessionLocal()
# Map (vol, normalized_title) → True for every article in the corpus.
# An article is "missing" only when its section name normalized to
# title form doesn't match any actual article title in its volume.
import unicodedata
def _norm(name: str) -> str:
    # Strip parenthetical and bracketed qualifiers ("ALPHEGE [Ælfheah]",
    # "BARBON (Barebone or Barebones)") so section-name comparison
    # matches the DB title variants. Also fold diacritics (É→E, Ö→O)
    # so "BLANCHE, JACQUES ÉMILE" matches "Blanche, Jacques Emile".
    s = re.sub(r"\([^)]*\)|\[[^\]]*\]", " ", name)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^A-Z0-9]+", " ", s.upper()).strip()
by_title = set()
for a in s.query(Article).all():
    by_title.add((a.volume, _norm(a.title)))
s.close()

# Each (vol, page) has a set of section names that became articles.
# Any section begin on that page whose name ISN'T in the set got absorbed.
candidates = []
for f in sorted(glob.glob("data/raw/wikisource/vol_*/vol*-page*.json")):
    try:
        d = json.load(open(f, encoding="utf-8"))
    except Exception:
        continue
    raw = d.get("raw_text", "")
    vol = d.get("volume")
    pg = d.get("page_number")
    for m in re.finditer(r'<section\s+begin="([^"]+)"\s*/?>', raw):
        sec_name = m.group(1)
        if re.match(r"^s\d+$|^part\d+$|^text\d+$", sec_name, re.IGNORECASE):
            continue
        # Adjacent begin/end = empty section marker, skip.
        rest = raw[m.end():m.end() + 1200]
        next_end = re.search(
            rf'<section\s+end="{re.escape(sec_name)}"\s*/?>',
            rest,
        )
        if next_end and next_end.start() < 50:
            continue

        # If NO article with this section_name exists anywhere in
        # this volume, it's actually missing (absorbed).
        # Narrow to biographical-article form: "Surname, Firstname"
        # (comma-separated), which is always a real article, never a
        # subsection continuation.
        if not re.match(r"^[A-Z][a-zA-Z\u00C0-\u017F'\- ]+,\s*[A-Z]", sec_name):
            continue
        sec_norm = _norm(sec_name)
        # Match if the section name is a prefix/substring of ANY
        # article title in the volume (covers titles with extra
        # "BARON" / duplicated-surname suffixes).
        sec_first = sec_norm.split(" ", 1)[0] if sec_norm else ""
        matched = False
        for title_norm in by_title:
            if title_norm[0] != vol:
                continue
            t = title_norm[1]
            if not sec_first or sec_first not in t:
                continue
            if sec_norm == t or sec_norm in t or t in sec_norm:
                matched = True
                break
        if not matched:
            candidates.append({
                "vol": vol,
                "pg": pg,
                "section": sec_name,
            })

print(f"Missing section articles: {len(candidates)}")
print()
for c in candidates[:25]:
    print(f"  vol{c['vol']} ws{c['pg']}: {c['section']!r}")
if len(candidates) > 25:
    print(f"  ... and {len(candidates) - 25} more")
