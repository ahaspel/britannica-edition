"""Which `<section begin="...">` markers never became an article?

Wikisource brackets each EB1911 article with `<section begin="Title"/>`, so the
markers are an INDEPENDENT census of what the volumes contain — the one oracle
that does not come from our own boundary detection.  A marker with no article
behind it is a candidate for swallowing by the lowercase-section-name
continuation rule in `detect_boundaries` ([[project_baseline_article_gaps]]).

IT USED TO REPORT 67, AND EVERY ONE I CHECKED WAS FALSE.  The test was a
hand-rolled substring match — first word must occur in the title, then
`sec in title or title in sec` — and EB1911 titles routinely carry an alternate
spelling INSIDE the name: section `Alecsandri, Vasile` against title
`ALECSANDRI, or ALEXANDRI, VASILE`, `Barthez, Paul Joseph` against
`BARTHEZ, or BARTHÈS, PAUL JOSEPH`, `Blandrata, Giorgio` against
`BLANDRATA, or BIANDRATA, GIORGIO`.  Neither string contains the other, so every
one of them read as MISSING.  All six I looked up were in the DB.

`britannica.name_index.NameIndex` is the project's recall engine and already
answers this exactly — word-set, diacritic fold, subset, superset, and an
OCR-tolerant fuzzy rung — so the tool now asks it instead of keeping a private,
worse copy ([[feedback_tune_dont_fork]]).  7,123 comma-form markers tested,
7,099 matched by a rung, 20 unresolved after page-span dedup — small enough to
print in FULL with each one's nearest article beside it, which is what makes the
residual adjudicable instead of merely countable.

WHAT THE RESIDUAL TURNED OUT TO BE: name discrepancies, not swallowed articles.
Seventeen are the article under a differently-spelled name (`Canitz, Frederich`
vs `CANITZ, FRIEDRICH`; `Erroll, Francis Hay, 9th Earl of` vs `ERROLL (or
ERROL), FRANCIS HAY`).  The three with no first-word match at all — `Bāanffy,
Dezsö`, `Chasseriau, Theodore`, `Congelton, Henry Brooke Parnell` — are all
present too, and one of them is a find in the other direction: the section name
is right and the HEADWORD is the typo (`CHASSÉSRIAU` for Chassériau), so the
article ships under a misspelt title.  That is corrections.json work
([[feedback_corrections_json]]).

KNOWN LIMIT, stated because it bounds the claim: a `Head, Qualifier` section
counts as present when a bare `Head` article exists, so two sections sharing one
head (`Colon, Cuba` / `Colon, Panama`) both pass against a single COLON article.
Multiplicity is a different question from existence and this tool answers only
existence.

COVERAGE IS PART OF THE REPORT.  This tool tests only comma-form names
(`Surname, Forename`, `Colon, Panama`) — a deliberate narrowing, because a
one-word section name is as often a subsection continuation as an article — and
it says so, with the count it skipped.  A net that prints a number without
saying what the number is OVER is how "and 42 more" became a silent truncation.
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict

sys.path.insert(0, "src")
sys.stdout.reconfigure(encoding="utf-8")

from britannica.db.models import Article          # noqa: E402
from britannica.db.session import SessionLocal    # noqa: E402
from britannica.name_index import NameIndex       # noqa: E402
from britannica.source_pages import load_pages    # noqa: E402

_SECTION = re.compile(r'<section\s+begin="([^"]+)"\s*/?>')
# Wikisource's own structural section names, never article titles.
_STRUCTURAL = re.compile(r"^(?:s\d+|part\d+|text\d+)$", re.IGNORECASE)
# `Surname, Forename` / `Place, Region` — the shape that is an article, not a
# subsection continuation.
_COMMA_FORM = re.compile(r"^[A-Z][a-zA-ZÀ-ſ'\- ]+,\s*[A-Z]")
# Rungs, tightest first.  A hit on any of them means the article exists.
_RUNGS = ("exact", "fold_match", "subset", "superset")


def build_indexes(session):
    """One NameIndex per volume: a section can only become an article in its own
    volume, so cross-volume namesakes must not answer for each other."""
    per_vol = defaultdict(list)
    for aid, vol, title in session.query(Article.id, Article.volume, Article.title):
        per_vol[vol].append({"filename": str(aid), "title": title})
    return {v: NameIndex(rows) for v, rows in per_vol.items()}


def main() -> int:
    session = SessionLocal()
    try:
        idx = build_indexes(session)
    finally:
        session.close()

    pages, _ = load_pages()          # total: raises rather than skipping a page
    seen = 0
    skipped = defaultdict(int)
    matched = defaultdict(int)
    fuzzy: dict[tuple[int, str], list[int]] = {}
    unresolved: dict[tuple[int, str], list[int]] = {}

    for page in pages:
        for m in _SECTION.finditer(page.text):
            name = m.group(1)
            seen += 1
            if _STRUCTURAL.match(name):
                skipped["structural section name"] += 1
                continue
            # An immediately following `end` is an empty marker, not an article.
            rest = page.text[m.end():m.end() + 1200]
            e = re.search(r'<section\s+end="%s"\s*/?>' % re.escape(name), rest)
            if e and e.start() < 50:
                skipped["empty section (begin/end adjacent)"] += 1
                continue
            if not _COMMA_FORM.match(name):
                skipped["not comma-form (out of scope, see docstring)"] += 1
                continue
            ix = idx.get(page.volume)
            if ix is None:
                skipped["volume has no articles in the DB (vol 29)"] += 1
                continue
            for rung in _RUNGS:
                # `single_head_ok` is CORRECT here and nowhere else by default:
                # every name that reaches this point is comma-form, which is the
                # `Head, Qualifier` inversion the flag exists for.  EB titles the
                # article by its head and lets the section name qualify it —
                # `Bizet, Georges` -> BIZET, `Lepanto, Battle of` -> LEPANTO,
                # `Como, Lake of` -> COMO.  Without it, 40-odd present articles
                # read as missing.  It stays tight: the flag requires the title's
                # content words to EQUAL the head, so VICTORIA FALLS cannot
                # answer for `Victoria, Queen`.
                kw = {"single_head_ok": True} if rung == "superset" else {}
                if getattr(ix, rung)(name, **kw):
                    matched[rung] += 1
                    break
            else:
                # The OCR rung, reported SEPARATELY and never silently: the
                # residual is dominated by typos in the section NAME —
                # `Canitz, Frederich` for `CANITZ, FRIEDRICH`, `Clanricarde,
                # Ulrick` for `ULICK`, `Chuchill` for `CHURCHILL`.  Folding those
                # into "matched" would hide a real transcription defect; leaving
                # them in "unresolved" would bury the genuine gaps this tool
                # exists to find.  So they get their own bucket
                # ([[feedback_fill_dumb_fish_smart]] — recall broadly, then let
                # the report do the discriminating).
                if ix.fuzzy(name, aggressive=True):
                    fuzzy.setdefault((page.volume, name), []).append(page.page)
                    continue
                # A section spanning a page break emits its `begin` on each page;
                # that is ONE section, so collect the pages instead of counting
                # the article twice.
                unresolved.setdefault((page.volume, name), []).append(page.page)

    print("source pages read      : %d" % len(pages))
    print("section markers seen   : %d" % seen)
    for why, n in sorted(skipped.items(), key=lambda kv: -kv[1]):
        print("  skipped %6d  %s" % (n, why))
    tested = seen - sum(skipped.values())
    print("comma-form tested      : %d" % tested)
    for rung in _RUNGS:
        print("  matched %6d  by %s" % (matched[rung], rung))
    print("  matched %6d  by fuzzy (OCR) - section-name typos, listed below"
          % sum(len(v) for v in fuzzy.values()))
    print("UNRESOLVED sections    : %d  (%d marker(s) before page-span dedup)"
          % (len(unresolved), sum(len(v) for v in unresolved.values())))
    print()
    print("-- section names that only an OCR-tolerant match resolves "
          "(%d) --" % len(fuzzy))
    for (vol, name), pgs in sorted(fuzzy.items()):
        span = "ws%d" % pgs[0] if len(pgs) == 1 else "ws%d-%d" % (pgs[0], pgs[-1])
        near = idx[vol].firstword(name)[:2]
        print("  vol%-2d %-10s %-46r -> %s"
              % (vol, span, name, ", ".join(t for _f, t in near) or "(fuzzy only)"))
    print()
    print("-- UNRESOLVED: no rung matched (%d) --" % len(unresolved))
    # Printed in FULL.  The old tool cut the list at 25 and said "and 42 more",
    # which is the same silence this arc is about — a finding you cannot see is a
    # finding the report did not make.
    for (vol, name), pgs in sorted(unresolved.items()):
        span = "ws%d" % pgs[0] if len(pgs) == 1 else "ws%d-%d" % (pgs[0], pgs[-1])
        near = idx[vol].firstword(name)[:3]
        hint = ("  nearest: " + ", ".join(t for _f, t in near)) if near else \
               "  nearest: (no article in vol %d shares its first word)" % vol
        print("  vol%-2d %-10s %r" % (vol, span, name))
        print("       %s" % hint)
    return 0


if __name__ == "__main__":
    sys.exit(main())
