"""Does any patch change the page beyond its own text?  For each patch ALONE,
the page is walked as the pipeline walks it (`supplied_gate.walked`) before
and after, and the two compared token by token.  A patch passes only if
everything that changed is its own: the changed stretch holds no marker
(«…»: italics, a paragraph, a table, a footnote …) that its own old and
new text, walked alone, do not hold, and runs no longer than they do.  A
patch cutting through Wikisource's italics changed the rest of the line
(THERMODYNAMICS, vol 26 p. 808: "done by''", live 2026-10-13) — a fault no
check keyed on one kind of markup had caught.  This one asks only: did
anything outside the patch change?

Writes data/staging/patches/leaks.json {stem: [{old, why}]}; prints the tally.
Usage: check_leaks.py [FILE in data/staging/patches, default kept.json] [--only STEM,…]  (book root)"""
import json
import re
import sys
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))
from paths import LEAKS_REVIEWED, WORK
sys.path.insert(0, "tools/diagnostics")
import supplied_gate as g

from wikikit.scan.patches import apply_patches
from wikikit.source_pages import fetched_text

#: a walker marker is «NAME, «/NAME, with its attributes and body read as text
#: after it — never OCR's stray «, which a Wikisource page holds as mojibake
#: ("Â«i"); read as a marker, it made a sentence one token
TOK = re.compile(r"«/?[A-Z][A-Z0-9_]*\b|[^\W\d_]+|\d+|\S")
#: tokens a patch's own rendering may differ by beyond its text (spacing
#: and punctuation settle differently at the edges)
SLACK = 6


def toks(s: str) -> list[str]:
    return TOK.findall(s)


def markers(ts) -> Counter:
    return Counter(t for t in ts if t.startswith("«"))


_DISPLAY = re.compile(r"\{\{\s*(?:center|centre|c|block center)\s*\||<table|<div|\n\s*\n")


def paragraph_allowance(x: dict) -> int:
    """Paragraph marks a patch may move: one for each display or paragraph
    break in its own text.  A display opens a paragraph in context that it
    does not open walked alone (Wikisource's {{center|…}} around a formula,
    ours {{block center|…}}; a break before a display Wikisource set and the
    print does not) — the change is the patch's own, at its own edge."""
    return len(_DISPLAY.findall(x["old"])) + len(_DISPLAY.findall(x["new"]))


def unexplained(lost: Counter, gained: Counter, allow_p: int) -> tuple[Counter, Counter]:
    """What a change in markers leaves unexplained: paragraph marks beyond
    the allowance; a link gained is the pipeline finding a cross-reference in
    corrected words ("artzl" -> "and", vol 27 p. 280) — a link lost never is."""
    lost, gained = Counter(lost), Counter(gained)
    for c in (lost, gained):
        c["«P"] = max(0, c["«P"] - allow_p)
    for k in ("«LN", "«/LN"):
        gained.pop(k, None)
    return +lost, +gained


def main():
    src = WORK / (sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "kept.json")
    patches = json.loads(src.read_text(encoding="utf-8"))
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1].split(","))
        patches = {k: v for k, v in patches.items() if k in only}
    bad, t = {}, Counter()
    reviewed = {(r["stem"], r["old"], r["new"])
                for r in json.loads(LEAKS_REVIEWED.read_text(encoding="utf-8"))} if LEAKS_REVIEWED.exists() else set()
    for stem, ps in sorted(patches.items()):
        v, p = int(stem[3:5]), int(stem[-4:])
        raw = fetched_text(v, p) or ""
        base = toks(g.walked(v, p, raw))
        expect = Counter()                     # the markers its patches, each alone, change
        for x in ps:
            t["patches"] += 1
            one = [{k: x[k] for k in ("start", "end", "old", "new", "kind")}]
            after = toks(g.walked(v, p, apply_patches(raw, one)))
            sm = SequenceMatcher(None, base, after, autojunk=False)
            gone = [tok for op, a1, a2, b1, b2 in sm.get_opcodes() if op != "equal" for tok in base[a1:a2]]
            came = [tok for op, a1, a2, b1, b2 in sm.get_opcodes() if op != "equal" for tok in after[b1:b2]]
            own_old = toks(g.walked(v, p, x["old"]))
            own_new = toks(g.walked(v, p, x["new"]))
            why = None
            extra_gone, extra_came = unexplained(markers(gone) - markers(own_old),
                                                 markers(came) - markers(own_new), paragraph_allowance(x))
            if extra_gone or extra_came:
                why = f"markers changed beyond the patch: lost {dict(extra_gone)} gained {dict(extra_came)}"
            elif len(gone) > len(own_old) + SLACK or len(came) > len(own_new) + SLACK:
                why = (f"changed {len(gone)}->{len(came)} tokens, the patch's own "
                       f"{len(own_old)}->{len(own_new)}")
            if why and (stem, x["old"], x["new"]) in reviewed:
                t["flagged, reviewed right"] += 1
            elif why:
                bad.setdefault(stem, []).append({"old": x["old"][:200], "new": x["new"][:200], "why": why})
                t["leaks"] += 1
            expect.update(markers(own_new))
            expect.subtract(markers(own_old))
        # together: the page with all its patches must change its markers by
        # exactly the sum of what each patch's own text changes — two patches
        # harmless alone and harmful together (vol 26 p. 671) show here
        everything = [{k: x[k] for k in ("start", "end", "old", "new", "kind")} for x in ps]
        got = markers(toks(g.walked(v, p, apply_patches(raw, everything))))
        got.subtract(markers(base))
        net = {k: got[k] - expect[k] for k in set(got) | set(expect) if got[k] != expect[k]}
        lost, gained = unexplained(Counter({k: -n for k, n in net.items() if n < 0}),
                                   Counter({k: n for k, n in net.items() if n > 0}),
                                   sum(paragraph_allowance(x) for x in ps))
        diff = {**{k: -n for k, n in lost.items()}, **gained}
        if diff:
            bad.setdefault(stem, []).append({"old": "(all the page's patches together)", "new": "",
                                             "why": f"together, markers change beyond the patches: {diff}"})
            t["pages leaking together"] += 1
    (WORK / "leaks.json").write_text(json.dumps(bad, indent=1, ensure_ascii=False), encoding="utf-8")
    print(dict(t), "on", len(bad), "pages")


if __name__ == "__main__":
    main()
