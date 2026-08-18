"""Propose `corrections.json` entries for the source-side brace/tag leaks.

`triage_render_leaks` says WHICH leaks are the transcription's fault
([[feedback_source_is_the_only_excuse]]); this turns each of those verdicts into
a literal `{from, to}` replacement ([[feedback_corrections_json]]).

EVERY `from` IS CUT FROM THE SOURCE, never typed.  A hand-transcribed context
string is a second chance to introduce the typo we are fixing, and a `from` that
does not match is a correction that silently does nothing — `apply_corrections`
is a plain `str.replace`, so a near-miss is indistinguishable from success.

UNIQUENESS IS THE SAFETY PROPERTY.  `corrections.json` keys are `vol:page`, but
lookup is BY VOLUME PREFIX — "the page number is informational" — so every entry
is applied to every page of its volume.  A `from` occurring twice would edit a
site nobody adjudicated.  So each context grows until it occurs EXACTLY ONCE in
the whole volume, and the tool refuses to emit one that never gets there.

Four defect shapes, and only two of them are deletions:

  * orphan ``}}``            -> delete.  A doubled close (`{{sc|Exhedra}}}}`) or a
                               close whose open was deleted / commented out.
  * stray ``</a>``/``</poem>`` -> delete.  Nothing opened them; MediaWiki shows
                               them literally too.
  * stray ``</table>``       -> ``|}`` when the wikitable it sits in is never
                               closed (LAMPROPHYRES has `{|` once and `|}` never,
                               so every consumer is guessing that table's extent),
                               DELETED when the table closes later on its own.
                               Which one is decided by a depth walk at the site,
                               never by a hand list: MALAY ARCHIPELAGO's sits
                               inside a table that closes 7,000 characters on —
                               our render already ends it in the right place — so
                               a `|}` there would inject a second close.
  * two one-offs             -> MINERALOGY's `HV2}}O.` is a mangled `H{{sub|2}}O.`
                               (the water in Apophyllite's +4½H₂O), and
                               PORTSMOUTH's `{Ts|ar}}` is missing one brace of its
                               open.  Both RESTORE markup rather than remove it.

Usage:
    uv run python tools/pipeline/propose_brace_corrections.py            # dry run
    uv run python tools/pipeline/propose_brace_corrections.py --apply    # write
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict

sys.path.insert(0, "src")
sys.stdout.reconfigure(encoding="utf-8")

from britannica.db.models import Article                    # noqa: E402
from britannica.db.session import SessionLocal              # noqa: E402
from britannica.source_pages import load_pages              # noqa: E402
from britannica.wikitext import mask_non_template, unmatched_closes  # noqa: E402

CORRECTIONS = "data/corrections.json"
CONTEXT_MIN, CONTEXT_MAX = 40, 220

# Articles whose SOURCE carries the defect, per triage_render_leaks.  The two
# one-offs name their own replacement; everything else is derived from the shape.
ORPHAN_BRACE = [
    "COBALT", "ELASTICITY", "ELECTROKINETICS", "EXEDRA", "KHALĪL IBN AḤMAD",
    "NORWEGIAN SEA", "OKLAHOMA", "PAPER", "PARASITIC DISEASES",
    "PINTO, FERNÃO MENDES", "POLYHEDRON", "SANA", "SOCIETIES, LEARNED",
    "SUMPTUARY LAWS", "TENNESSEE",
]
STRAY_TAG = {"BUDGELL, EUSTACE": "poem", "CONSTANTINOPLE": "a",
             "ELECTROMETER": "a", "GUNCOTTON": "a", "LEVITES": "a"}
WIKITABLE_CLOSE = ["LAMPROPHYRES", "MAGNETISM", "MAGNETISM, TERRESTRIAL",
                   "MALAY ARCHIPELAGO"]
ONE_OFFS = [("MINERALOGY", "HV2}}O.", "H{{sub|2}}O."),
            ("PORTSMOUTH", "|{Ts|ar}}|", "|{{Ts|ar}}|"),
            # `</br/>` — `<br>` is a VOID element, so a close tag cannot exist.
            # CONGO's shoulder heading is three lines ("The new / treaty of /
            # cession.") and the second break was typed as a close.
            ("CONGO FREE STATE", "treaty of</br/>cession.",
             "treaty of<br/>cession."),
            # `|width=7.5` is debris from an `{{EB1911 Shoulder Heading|width=7.5|…}}`
            # — ROME uses exactly that template elsewhere — pasted into the middle
            # of a `<ref>`, where nothing encloses it.  ONLY the demonstrable
            # debris goes: `(2)` stays, because "Ranke iv.(2) 285" is a plausible
            # volume/part/page citation and I cannot prove otherwise
            # ([[feedback_when_in_doubt_carry]]).
            ("ROME", "iv.|width=7.5(2) 285", "iv.(2) 285")]

# Left alone on purpose: SLAVS, SPHERICAL HARMONICS, TIDE, TRIGONOMETRY,
# VARIATIONS CALCULUS OF.  Their unmatched `<t` / `<I` / `<s` / `<Q` are OCR
# debris inside math on unproofread pages ([[project_unproofed_math_impact]]).
# "Correcting" those means transcribing the mathematics, which is Wikisource-side
# work and not a literal replacement ([[project_quality_deferred]]).


def grow_unique(vol_src: str, src: str, pos: int, length: int):
    """Smallest leading context making `src[pos:pos+length]` unique in the volume.

    Returns the matched text or None if even CONTEXT_MAX chars are ambiguous —
    which is a refusal, not a fallback: a correction that might fire twice is
    worse than one that does not exist.
    """
    for pad in range(CONTEXT_MIN, CONTEXT_MAX + 1, 20):
        frm = src[max(0, pos - pad):pos + length]
        if vol_src.count(frm) == 1:
            return frm
    return None


def main() -> int:
    apply = "--apply" in sys.argv
    session = SessionLocal()
    vol_cache: dict[int, str] = {}

    def volume_src(v):
        if v not in vol_cache:
            vol_cache[v] = "\n".join(p.text for p in load_pages(v)[0])
        return vol_cache[v]

    proposals, refused = [], []

    def add(title, tag_desc, frm, to, vol, page):
        proposals.append((title, tag_desc, vol, page, frm, to))

    def article(title):
        a = session.query(Article).filter(Article.title == title).first()
        pages, _ = load_pages(a.volume, pages=range(a.page_start, a.page_end + 1))
        return a, pages

    def page_of(pages, pos):
        """Which source page a character offset falls on (pages joined by \\n)."""
        run = 0
        for p in pages:
            run += len(p.text) + 1
            if pos < run:
                return p.page
        return pages[-1].page

    for title in ORPHAN_BRACE:
        a, pages = article(title)
        src = "\n".join(p.text for p in pages)
        for pos in unmatched_closes(mask_non_template(src), r"\{\{", r"\}\}"):
            frm = grow_unique(volume_src(a.volume), src, pos, 2)
            if frm is None:
                refused.append((title, "orphan }} not uniquely locatable")); continue
            add(title, "delete orphan }}", frm, frm[:-2], a.volume, page_of(pages, pos))

    for title, tag in STRAY_TAG.items():
        a, pages = article(title)
        src = "\n".join(p.text for p in pages)
        for pos in unmatched_closes(mask_non_template(src), r"<%s\b" % tag, r"</%s\b" % tag):
            m = re.compile(r"</%s\s*>" % tag).match(src, pos)
            if not m:
                refused.append((title, "stray </%s> malformed" % tag)); continue
            frm = grow_unique(volume_src(a.volume), src, pos, len(m.group(0)))
            if frm is None:
                refused.append((title, "stray </%s> not uniquely locatable" % tag)); continue
            add(title, "delete stray </%s>" % tag, frm,
                frm[:-len(m.group(0))], a.volume, page_of(pages, pos))

    for title in WIKITABLE_CLOSE:
        a, pages = article(title)
        src = "\n".join(p.text for p in pages)
        wiki = sorted([(m.start(), 1) for m in re.finditer(r"^\{\|", src, re.M)] +
                      [(m.start(), -1) for m in re.finditer(r"^\|\}", src, re.M)])

        def enclosing_closes_later(at: int) -> bool:
            """Does the wikitable containing `at` get closed after it?

            Depth-walked at the SITE, not tallied over the article
            ([[feedback_measure_at_decision_site]]).  "Is there any later `|}`"
            was the loose version and it was wrong for a long article: MAGNETISM,
            TERRESTRIAL has 21 wikitables, so SOME `|}` follows every position in
            it, including the ones whose own table never closes.  The question is
            whether depth ever falls BELOW the level this stray sits at.
            """
            depth = sum(k for p, k in wiki if p < at)
            if depth <= 0:
                return True          # not inside a wikitable at all — stray text
            cur = depth
            for p, k in wiki:
                if p <= at:
                    continue
                cur += k
                if cur < depth:
                    return True
            return False
        for pos in unmatched_closes(mask_non_template(src), r"<table\b", r"</table\b"):
            m = re.compile(r"</table\s*>").match(src, pos)
            if not m:
                refused.append((title, "stray </table> malformed")); continue
            frm = grow_unique(volume_src(a.volume), src, pos, len(m.group(0)))
            if frm is None:
                refused.append((title, "stray </table> not uniquely locatable")); continue
            # DELETE or REPAIR, decided by the text rather than by a hand list:
            # if a real `|}` comes later, the wikitable is already terminated and
            # this `</table>` is stray text inside it — MALAY ARCHIPELAGO's sits
            # inside a table that closes 7,000 characters on, and our render
            # already ends that table in the right place, so a `|}` here would
            # inject a second close.  With no later `|}` the table is genuinely
            # unterminated (LAMPROPHYRES has `{|` once and `|}` never) and every
            # consumer is guessing its extent — there, `|}` is the repair.
            later = enclosing_closes_later(pos)
            add(title,
                "delete stray </table> (wikitable closes later)" if later
                else "</table> -> |} (wikitable is unterminated)",
                frm,
                frm[:-len(m.group(0))] + ("" if later else "|}"),
                a.volume, page_of(pages, pos))

    for title, frag, repl in ONE_OFFS:
        a, pages = article(title)
        src = "\n".join(p.text for p in pages)
        pos = src.find(frag)
        if pos < 0:
            # `load_pages` returns CORRECTED text, so once an entry is written its
            # `from` stops matching.  Saying "not in source" then reads as a
            # failure when it is the success signal; distinguish the two.
            refused.append((title, "already corrected (no-op)" if repl in src
                            else "%r not in source" % frag))
            continue
        frm = grow_unique(volume_src(a.volume), src, pos, len(frag))
        if frm is None:
            refused.append((title, "%r not uniquely locatable" % frag)); continue
        add(title, "repair %r -> %r" % (frag, repl), frm,
            frm[:-len(frag)] + repl, a.volume, page_of(pages, pos))

    # Every proposal re-checked against the volume it will be applied to, because
    # that is the text `apply_corrections` actually sees.
    print("%d proposal(s), %d refused\n" % (len(proposals), len(refused)))
    for title, desc, vol, page, frm, to in proposals:
        n = volume_src(vol).count(frm)
        flag = "OK " if n == 1 else "AMBIGUOUS(%d)" % n
        print("%s vol%-2d %-4d %-34s %s" % (flag, vol, page, title[:34], desc))
        print("      from: ...%s" % re.sub(r"\s+", " ", frm)[-84:])
        print("      to  : ...%s" % re.sub(r"\s+", " ", to)[-84:])
    for title, why in refused:
        print("REFUSED %-28s %s" % (title[:28], why))

    if apply:
        existing = json.loads(open(CORRECTIONS, encoding="utf-8").read())
        added = 0
        for _t, _d, vol, page, frm, to in proposals:
            key = "%d:%d" % (vol, page)
            entries = existing.setdefault(key, [])
            if any(e.get("from") == frm for e in entries):
                continue
            entries.append({"from": frm, "to": to})
            added += 1
        with open(CORRECTIONS, "w", encoding="utf-8") as fh:
            json.dump(existing, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        print("\nwrote %d new entry/entries to %s" % (added, CORRECTIONS))
    else:
        print("\n(dry run; pass --apply to write %s)" % CORRECTIONS)
    session.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
