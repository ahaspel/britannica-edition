"""Each patch tested ALONE against our page, by the judge's own tokens: kept
only if applying it to Wikisource's page removes at least one disagreement
with ours and creates none (no stretch of ours that agreed before disagrees
after) — a formula patch that changes only the notation is kept too: ours
stands (2026-10-13).  This catches what the structure proof cannot: a patch in the wrong
place ("the functions so determined are called Lamé's functions" replaced by
a formula: vol 25 p. 682), an equation number swallowed.  Also refused: a
word patch turning a real word into a non-word (a misprint of the print kept
by our reading: "that" -> "thac", vol 27 p. 277) — a word is real if it
occurs 5+ times in the corpus.  And a patch that sets text TWICE: words it
brings that Wikisource's page already has elsewhere (where ours and
Wikisource's set a caption or a paragraph in different places, a patch adding
it at ours leaves Wikisource's own copy standing; its sole disagreement
counts as removed: Fig. 7's curve legend inserted mid-sentence, vol 27
p. 176; "3. National Standards" over "Totals", vol 28 p. 478).

Kept but doubted (`doubt`, laid by install.py only on a person's ruling): a
word patch replacing clean text with text unlike it, or adding many words —
where our reading is itself wrong, Wikisource's right words count as the
disagreement a patch removes.

Our page is the text the judge compared (`paths.judged_text`).

Writes kept.json (the kept patches) and filter_report.json.
Usage: filter_patches.py  (book root)"""
import difflib
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from paths import DISPUTES, FILTER_VOCAB, WORK, judged_text
from patterns import ALNUM, TOKEN, WORD, WORD2
from disputes import tokens
from apply import apply
from validate_patches import sites

from wikikit.export.corpus import load_corpus
from wikikit.source_pages import fetched_text

#: Words in a row a patch brings that make a copy, not a coincidence
RUN = 8
#: A word patch resembling what it replaces less than this (letters and
#: figures, difflib), where what it replaces is clean — real words, numbers —
#: is a reading's text for the print's, not an OCR correction ...
LIKE = 0.5
#: ... and one adding this many words over what it replaces sets text where
#: the two pages' texts do not line up.  Either waits for a person's ruling.
INSERT = 8
#: Characters clean text is made of besides letters and figures
_CLEAN = re.compile(r"[\w\s.,;:'’()\-–—&]*")


def doubt(v: int, p: int, x: dict, vocab: set[str]) -> str | None:
    """Why a word patch the checks pass must still wait for a person, or None.
    The checks count disagreements with our reading, so where our reading is
    itself wrong and clean, Wikisource's right words "disagree" and a patch
    replacing them passes: a bibliography's entries spliced and swapped (ten
    patches, vol 24 p. 797), a paragraph laid over a figure key's "H" (vol 26
    p. 68), "Martha's Vineyard" -> "Fire Island" (vol 25 p. 851), all
    installed and built (2026-11-03)."""
    if x["kind"] != "word":
        return None
    added = len(tokens(v, p, x["new"])) - len(tokens(v, p, x["old"]))
    if added >= INSERT:
        return f"adds {added} words"
    a, b = (re.sub(r"[\W_]", "", s.lower()) for s in (x["old"], x["new"]))
    pieces = ALNUM.findall(x["old"])
    # clean: every piece a corpus word or a number.  A piece mixing letters
    # and figures is OCR ("Cr89o", "Io0"); figures alone becoming letters are
    # a formula's OCR ("2502" -> "2SO4")
    clean = pieces and _CLEAN.fullmatch(x["old"]) and all(
        w.isdigit() or (w.isalpha() and w.lower() in vocab) for w in pieces)
    formula = all(w.isdigit() for w in pieces) and re.search(r"[^\W\d_]", x["new"])
    if len(a) >= 4 and clean and not formula \
            and difflib.SequenceMatcher(None, a, b, autojunk=False).ratio() < LIKE:
        return "replaces clean text with text unlike it"
    return None


def doubled(new: list[str], old: list[str], patched: list[str], ours: list[str]) -> str | None:
    """A run of RUN words the patch brings (`new`, not all in what it
    replaces, `old`) that the patched page holds twice or more, and more
    often than our page does: text set twice.  A phrase our page itself
    prints twice may stand twice; a table's words, from its re-reading, may
    stand once where our judged page has none."""
    have = set(old)
    page, ourpage = " " + " ".join(patched) + " ", " " + " ".join(ours) + " "
    for i in range(len(new) - RUN + 1):
        run = new[i:i + RUN]
        if all(w in have for w in run):
            continue
        r = " " + " ".join(run) + " "
        if page.count(r) > max(1, ourpage.count(r)):
            return " ".join(run)
    return None


def vocabulary():
    """The corpus's real words (2+ letters, 5+ uses), from the stored snapshot
    (`FILTER_VOCAB`) — computed from the corpus and stored only when there is
    none: drawn fresh each run, it changed with every build the patches went
    into, and the chain stopped reproducing its own result (2026-10-13)."""
    if FILTER_VOCAB.exists():
        return set(json.loads(FILTER_VOCAB.read_text(encoding="utf-8")))
    corpus, _ = load_corpus()
    c = Counter()
    for a in corpus.values():
        c.update(w.lower() for w in WORD2.findall(a.get("body", "")))
    words = sorted(w for w, n in c.items() if n >= 5)
    FILTER_VOCAB.write_text(json.dumps(words), encoding="utf-8")
    return set(words)


def main():
    vocab = vocabulary()
    patches = json.loads((WORK / "merged.json").read_text(encoding="utf-8"))
    dis = json.loads(DISPUTES.read_text(encoding="utf-8"))
    kept, report, t = {}, {}, Counter()
    for stem, ps in sorted(patches.items()):
        v, p = int(stem[3:5]), int(stem[-4:])
        ws = fetched_text(v, p) or ""
        O = tokens(v, p, judged_text(stem, dis))
        before = sites(tokens(v, p, ws), O)
        old_ours = {(o, c) for _, o, c in before}
        good = []
        for x in ps:
            why = None
            if x["kind"] == "word":
                ow, nw = x["old"].strip().lower(), x["new"].strip().lower()
                if WORD.fullmatch(ow) and WORD.fullmatch(nw) \
                        and ow in vocab and nw not in vocab:
                    why = f"real word to non-word: {x['old']!r} -> {x['new']!r}"
            if why is None:
                P = tokens(v, p, apply(ws, [x]))
                after = sites(P, O)
                new = [s for s in after if (s[1], s[2]) not in old_ours and s[1]]
                if x["kind"] == "table":
                    # a table's words are the judged reading's figure for figure
                    # (build_tables.py); a word our two reads split differently
                    # ("fort nightly", TIDE) is no disagreement
                    new = [s for s in new if re.sub(r"\W", "", s[0]) != re.sub(r"\W", "", s[1])]
                twice = len(TOKEN.findall(x["new"])) >= RUN and \
                    doubled(tokens(v, p, x["new"]), tokens(v, p, x["old"]), P, O)
                if new:
                    why = f"creates a disagreement: ws {new[0][0][:40]!r} vs ours {new[0][1][:40]!r}"
                elif twice:
                    why = f"sets text twice: {twice!r}"
                elif len(after) >= len(before):
                    if x["kind"] == "table":
                        # a table's gain is its setting, which no word measures:
                        # kept when it creates no disagreement
                        t["kept (table, setting only)"] += 1
                    elif x["kind"] == "formula":
                        # our notation where Wikisource's says the same: ours
                        # stands (user, 2026-10-13: "I prefer our notations")
                        t["kept (formula, notation only)"] += 1
                    else:
                        why = "removes no disagreement"
            if why:
                report.setdefault(stem, []).append({"old": x["old"][:80], "new": x["new"][:80], "why": why})
                t[f"dropped ({x['kind']})"] += 1
                t["dropped: " + why.split(":")[0]] += 1
            else:
                # kept for the desk's patch screen, flagged; install.py lays it
                # only on a person's ruling
                if d := doubt(v, p, x, vocab):
                    x = {**x, "doubt": d}
                    t["kept, waiting for a ruling: " + d.split(" ")[0]] += 1
                good.append(x)
                t[f"kept ({x['kind']})"] += 1
        if good:
            kept[stem] = good
    (WORK / "kept.json").write_text(json.dumps(kept, indent=1, ensure_ascii=False), encoding="utf-8")
    (WORK / "filter_report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    print(len(kept), "pages;", dict(t))


if __name__ == "__main__":
    main()
