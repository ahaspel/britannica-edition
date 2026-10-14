"""Each patch tested ALONE against our page, by the judge's own tokens: kept
only if applying it to Wikisource's page removes at least one disagreement
with ours and creates none (no stretch of ours that agreed before disagrees
after) — a formula patch that changes only the notation is kept too: ours
stands (2026-10-13).  This catches what the structure proof cannot: a patch in the wrong
place ("the functions so determined are called Lamé's functions" replaced by
a formula: vol 25 p. 682), an equation number swallowed.  Also refused: a
word patch turning a real word into a non-word (a misprint of the print kept
by our reading: "that" -> "thac", vol 27 p. 277) — a word is real if it
occurs 5+ times in the corpus.

Writes kept.json (the kept patches) and filter_report.json.
Usage: filter_patches.py  (book root)"""
import copy
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from paths import FILTER_VOCAB, WORK, reading
from patterns import WORD, WORD2
from disputes import tokens
from apply import apply
from validate_patches import sites

from wikikit.export.corpus import load_corpus
from wikikit.scan import supplied
from wikikit.source_pages import fetched_text


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
    kept, report, t = {}, {}, Counter()
    for stem, ps in sorted(patches.items()):
        v, p = int(stem[3:5]), int(stem[-4:])
        ws = fetched_text(v, p) or ""
        d = json.loads((reading(stem)).read_text(encoding="utf-8"))
        O = tokens(v, p, supplied.name_sections(copy.deepcopy(d))["raw_text"])
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
                after = sites(tokens(v, p, apply(ws, [x])), O)
                new = [s for s in after if (s[1], s[2]) not in old_ours and s[1]]
                if x["kind"] == "table":
                    # a table's words are the judged reading's figure for figure
                    # (build_tables.py); a word our two reads split differently
                    # ("fort nightly", TIDE) is no disagreement
                    new = [s for s in new if re.sub(r"\W", "", s[0]) != re.sub(r"\W", "", s[1])]
                if new:
                    why = f"creates a disagreement: ws {new[0][0][:40]!r} vs ours {new[0][1][:40]!r}"
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
                good.append(x)
                t[f"kept ({x['kind']})"] += 1
        if good:
            kept[stem] = good
    (WORK / "kept.json").write_text(json.dumps(kept, indent=1, ensure_ascii=False), encoding="utf-8")
    (WORK / "filter_report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    print(len(kept), "pages;", dict(t))


if __name__ == "__main__":
    main()
