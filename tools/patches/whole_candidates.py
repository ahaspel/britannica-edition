"""Which judged pages may enter WHOLE — our reading for Wikisource's — because
Wikisource's page carries nothing a person set: raw OCR, with no structure to
anchor a patch on and none to lose (TIDE p. 954: its schedules, margin notes,
display formula and footnote all OCR junk, which patches cannot reach).

A page qualifies when Wikisource's page body (its noinclude header and footer
aside) holds no markup but section tags and `{{missing table}}` placeholders:
  - no element as the pipeline walks it (the supplied gate's `elements`:
    formulas, figures, tables, cells, footnotes, links, margin headings,
    poems), and
  - no template, real HTML tag, italic or bold run, wiki table or link at
    all — every one tallied by name, never a chosen list: OCR's stray `<`
    ("<t", "<sin") is not a tag.
The rest stay patched.  A page carrying a little (one shoulder heading) is
listed with what it carries, so whether ours carries the same can be read.

Read-only.  Usage: whole_candidates.py [-v]   (book root)"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parents[1] / "diagnostics"))
from paths import PAGES
from supplied_gate import elements

from eb1911.scans import _printed
from wikikit.db.models import Article
from wikikit.db.session import SessionLocal
from wikikit.source_pages import fetched_text

#: the HTML tags wikitext renders; anything else after `<` is OCR's text
TAGS = ("ref|references|math|chem|ce|table|tr|td|th|caption|sub|sup|span|div|br|hr|poem|i|b|u|s|"
        "small|big|center|font|p|blockquote|ol|ul|li|dl|dt|dd|pre|code|nowiki|score|section|abbr|"
        "includeonly|onlyinclude|noinclude|gallery|imagemap|timeline|hiero|syntaxhighlight|tt|var|del|ins|q")
#: a tag as written: bare, or with attributes `name=…` — OCR's "<s- s>",
#: "<s-a>", "<p, z = cr cos 0 … >" (formula salad, vol 25 p. 659) are text
TAG = re.compile(rf"<\s*/?\s*({TAGS})(?:\s+[a-z-]+\s*=\s*[^<>]*)?\s*/?\s*>", re.I)
TEMPLATE = re.compile(r"\{\{\s*([^|{}\n]+?)\s*(?=[|}])")
ALLOWED = {"<section", "{{missing table"}


def markup(body: str) -> Counter:
    """Every piece of markup a person (or a bot) set on the page body, by name."""
    c = Counter("{{" + m.lower() for m in TEMPLATE.findall(body))
    c.update("<" + m.lower() for m in TAG.findall(body))
    # exactly two or three: OCR reads a garbled exponent as "''''" (vol 28 p. 429)
    c["'''"] += len(re.findall(r"(?<!')'''(?!')", body))
    c["''"] += len(re.findall(r"(?<!')''(?!')", body))
    c["[["] += len(re.findall(r"\[\[", body))
    c["{|"] += len(re.findall(r"(?m)^\s*\{\|", body))
    return +c


def main():
    verbose = "-v" in sys.argv
    pp = _printed("printed_pages.json")
    s = SessionLocal()
    whole, carries, patched = [], [], 0
    try:
        for stem in PAGES.read_text().split():
            v, p = int(stem[3:5]), int(stem[-4:])
            ws = fetched_text(v, p) or ""
            body = re.sub(r"<noinclude>[\s\S]*?</noinclude>", "", ws)
            mk = Counter({k: n for k, n in markup(body).items() if k not in ALLOWED})
            el = +elements(v, p, body)
            arts = ", ".join(a.title for a in s.query(Article).filter(
                Article.volume == v, Article.page_start <= p, Article.page_end >= p))
            row = (f"vol {v} p. {pp[str(v)][str(p)]}", stem, arts)
            if not mk and not el:
                whole.append(row)
            elif sum(mk.values()) <= 6 and not el.get("tables") and not el.get("footnotes"):
                carries.append(row + (dict(mk), dict(el)))
            else:
                patched += 1
    finally:
        s.close()
    print(f"WHOLE — Wikisource's page carries nothing a person set: {len(whole)}")
    for r in whole:
        print(f"  {r[0]:16} {r[1]}  {r[2]}")
    print(f"\nNEARLY — a little markup; whole only if ours carries the same: {len(carries)}")
    for r in carries:
        print(f"  {r[0]:16} {r[1]}  {r[2][:40]:40} markup {r[3]} elements {r[4]}")
    print(f"\npatched (Wikisource's page carries structure): {patched}")


if __name__ == "__main__":
    main()
