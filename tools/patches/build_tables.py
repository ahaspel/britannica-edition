"""Table patches: our table set where Wikisource's page has only OCR text for
it — a table flattened into lines of figures (TIDE's schedules, vol 26
p. 954).  The table comes from the page's re-reading for its tables
(data/readings/tables/: rules, headings, alignment, braces); its words and
figures must be the judged reading's, so the judge stands behind every
figure and only the table's setting is new.

For each table of the re-reading (not a chemical grid):
  1. placed between the real words the two pages share around it, aligned
     as the formula patches align (`build_formulas.prose`): Wikisource's text
     between them is replaced by the table;
  2. refused — Wikisource's text stays — when that text holds structure of
     its own (a table, a note, a link, an image, a heading, a template not a
     formula's), when a real word of Wikisource's there is not the table's,
     when our text between the words holds anything but the table, or when
     the table's words and figures are not the judged reading's.

Writes data/staging/patches/tables.json; prints each page's outcome.
Usage: build_tables.py  (book root)"""
import copy
import json
import re
import sys
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))
from build_formulas import displays, lost_words, prose, quotes_open, structure, vocabulary, words_of
from build_words import find, locate
from paths import DISPUTES, RULINGS, TABLE_READINGS, WORK, reading
from patterns import TOKEN
from raw_tokens import tokens

from wikikit.scan import supplied
from wikikit.scan.carry import markup_balance
from wikikit.scan.patches import MISSING_TABLE, patches_for
from wikikit.scan.vocabulary import FORMULA_CLASS, TABLE_CLOSES, TABLE_OPENS
from wikikit.source_pages import fetched_text


def tables_of(text: str) -> list[tuple[int, int]]:
    """Each top-level table's span, a chemical grid aside."""
    out, at = [], 0
    while (m := TABLE_OPENS.search(text, at)):
        c = TABLE_CLOSES.search(text, m.end())
        if not c:
            break
        if FORMULA_CLASS not in text[m.start():text.find("\n", m.start())]:
            out.append((m.start() + len(m.group(0)) - 2, c.end()))
        at = c.end()
    return out


def page_body(text: str) -> tuple[int, int]:
    """Where a page's own text begins and ends: inside its noinclude header
    and footer."""
    lo = text.find("</noinclude>")
    lo = lo + len("</noinclude>") if 0 <= lo < 400 else 0
    hi = text.rfind("<noinclude>")
    hi = hi if hi > lo else len(text)
    return lo, hi


def lines(text: str, a: int, b: int) -> tuple[int, int]:
    """The whole lines between a..b: a table is a block, so its patch begins
    after the line holding the word before (`a`) and ends where the line
    holding the word after (`b`) begins — never inside the markup around a
    word (a heading's `{{c|B.—''` before the next schedule), and never short
    of a row the OCR ran onto the next shared word's paragraph."""
    lo = text.find("\n", a, b)
    lo = lo + 1 if lo >= 0 else a
    hi = text.rfind("\n", lo, b)
    return lo, (hi if hi >= 0 else b)


def cells(text: str) -> str:
    """A table's text with its openings' settings ({| class=…) on lines of
    their own: `words_of` reads a setting's value to the next pipe, which
    for a table's opening is the whole heading row after it."""
    return re.sub(r"(?m)^(\{\|[^\n]*)$", "\\1\n|", text)


def figures(text: str) -> list[str]:
    """A table's words and figures, as tokens: joined, what must match the judged
    reading — its setting (rules, headings, alignment, the opening's class or
    style, a fraction's size) may differ."""
    text = re.sub(r"(?m)^\{\|[^\n]*", "{|", text)
    text = re.sub(r"\\[td]frac\b", r"\\frac", text)
    # a letter set upright in a formula or as plain text is one letter: the
    # markup's own names are no part of what the table prints
    text = re.sub(r"</?math[^>]*>|\\(?:text|mathrm)\b", " ", text)
    text = re.sub(r"\{\{\s*(?:Ts|brace2)\s*\|[^{}]*\}\}|(?:rowspan|colspan)\s*=\s*\d+", " ", text)
    return [t.lower() for t in TOKEN.findall(text)]


def judged_table(old: str, toks: list[str]) -> str | None:
    """The judged reading's table these tokens are, or None."""
    best = max(tables_of(old), default=None,
               key=lambda s: SequenceMatcher(None, figures(old[s[0]:s[1]]), toks).ratio())
    return old[best[0]:best[1]] if best else None


def main():
    vocab = vocabulary()
    out, tally = {}, Counter()
    dis = json.loads(DISPUTES.read_text(encoding="utf-8"))
    rul = json.loads(RULINGS.read_text(encoding="utf-8"))
    for f in sorted(TABLE_READINGS.glob("vol_*/vol*-page*.json")):
        stem = f.stem
        d = json.loads(f.read_text(encoding="utf-8"))
        v, p = d["volume"], d["page_number"]
        ours = supplied.name_sections(copy.deepcopy(d))["raw_text"]
        old = json.loads(reading(stem).read_text(encoding="utf-8"))["raw_text"]
        ws = fetched_text(v, p) or ""
        OT, WT = tokens(ours), tokens(ws)
        # words inside our displayed formulas' lines are no anchors (as for
        # the formula patches): an edge there cut the display's wrapper
        op, wp = prose(OT, vocab, ours, displays(ours)), prose(WT, vocab, ws)
        sm = SequenceMatcher(None, [k for _, k in op], [k for _, k in wp], autojunk=False)
        pairs = [(op[b.a + k][0], wp[b.b + k][0]) for b in sm.get_matching_blocks() if b.size >= 2
                 for k in range(b.size)]
        # a page's own edges stand for a shared word when a table opens or
        # ends the page's text
        o_lo, o_hi = page_body(ours)
        w_lo, w_hi = page_body(ws)
        # Wikisource's words the judge gave us, where they stand: only these
        # may go with the junk a table replaces (as for the formula patches)
        W = [t for t in WT if t[3] != "barrier"]
        # Inside a junk span the agreed words around a site are junk too, so
        # a site the context cannot place counts where its whole run of
        # Wikisource tokens stands once, inside the span (`within`)
        given = []
        for i, site in enumerate(dis.get(stem, {}).get("sites", [])):
            ws_words = site["ws"].split()
            if rul.get(stem, {}).get(str(i)) == "ours" and ws_words:
                j = locate(W, ws_words, site["before"].split(), site["after"].split())
                places = [j] if j is not None else find(W, ws_words)
                given.append(([(W[k][1], W[k + len(ws_words) - 1][2]) for k in places],
                              Counter(w for w in ws_words if len(w) >= 3)))

        def within(w0, w1):
            """The words given at sites standing in w0..w1 — every place a
            site's tokens stand must be inside, so none counts twice."""
            return sum((c for at, c in given if at and all(w0 <= x and y <= w1 for x, y in at)),
                       Counter())

        page = []
        for a, b in tables_of(ours):
            tally["tables"] += 1
            before = [(OT[o][2], WT[w][2]) for o, w in pairs if OT[o][2] <= a] or [(o_lo, w_lo)]
            after = [(OT[o][1], WT[w][1]) for o, w in pairs if OT[o][1] >= b] or [(o_hi, w_hi)]
            why = None
            n0, n1 = lines(ours, before[-1][0], after[0][0])
            w0, w1 = lines(ws, before[-1][1], after[0][1])
            table, ours_span, old_span = ours[a:b], ours[n0:n1], ws[w0:w1]
            # beside the table, our text there may hold only what a formula
            # patch may: formulas, their display lines, words
            rest = ours_span.replace(table.strip(), "", 1)
            judged = judged_table(old, figures(table))
            if w1 <= w0:
                why = "the shared words are out of order"
            elif table.strip() not in ours_span:
                why = "the table is not whole between the words"
            elif structure(rest) or quotes_open(rest):
                why = "our text beside the table holds " + (structure(rest) or "open italics")
            elif structure(MISSING_TABLE.sub("", old_span)):
                why = "Wikisource's text there holds " + structure(MISSING_TABLE.sub("", old_span))
            elif markup_balance(old_span) != markup_balance(ours_span.replace(table.strip(), "", 1)):
                why = "markup unbalanced at an edge"
            elif (lost := lost_words(MISSING_TABLE.sub("", old_span), cells(ours_span), vocab, within(w0, w1))):
                why = f"a word of Wikisource's would be lost: {sorted(lost)[:5]}"
            elif judged is None or "".join(figures(judged)) != "".join(figures(table)):
                diff = [] if judged is None else [
                    (x, y) for op_, i1, i2, j1, j2 in SequenceMatcher(
                        None, figures(judged), figures(table), autojunk=False).get_opcodes()
                    if op_ != "equal" for x, y in [(" ".join(figures(judged)[i1:i2]),
                                                   " ".join(figures(table)[j1:j2]))]][:4]
                why = f"its words or figures are not the judged reading's: {diff}"
            if why:
                tally["refused: " + why.split(":")[0]] += 1
                print(f"  {stem} table at {a}: REFUSED — {why}")
                continue
            # the table replaces the text, not the breaks around it: the span's
            # own blank lines stay at either end (TEXTILE-PRINTING p. 701 lost
            # the paragraph before its nitrite table)
            lead = old_span[:len(old_span) - len(old_span.lstrip())]
            trail = old_span[len(old_span.rstrip()):]
            new = lead + ours_span.strip() + trail
            page.append({"kind": "table", "start": w0, "end": w1, "old": old_span, "new": new})
            tally["table patches"] += 1
            print(f"  {stem} table at {a}: patch over {w1 - w0} chars of Wikisource's text")
        # two tables over one stretch of Wikisource's text, or a table cutting
        # an installed patch, place neither: one of them was anchored wrongly
        # (TUNNEL p. 409's two tables found the same words around them)
        installed = patches_for(v, p)

        def collides(x, others):
            return any(x is not y and x["start"] < y["end"] and y["start"] < x["end"] for y in others)

        def cuts(x):
            return any(x["start"] < y["end"] and y["start"] < x["end"]
                       and not (x["start"] <= y["start"] and y["end"] <= x["end"]) for y in installed)

        for x in [x for x in page if collides(x, page) or cuts(x)]:
            tally["table patches"] -= 1
            tally["refused: collides"] += 1
            print(f"  {stem} patch at {x['start']}: REFUSED — collides with "
                  + ("another table's span" if collides(x, page) else "an installed patch"))
        page = [x for x in page if not collides(x, page) and not cuts(x)]
        if page:
            out[stem] = page
    (WORK / "tables.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(dict(tally))


if __name__ == "__main__":
    main()
