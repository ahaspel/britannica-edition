"""Every patch in patches.json, checked mechanically (no sampling, no model):

  (c) agreement   Wikisource's page before and after patching, each compared
                  with our page by the judge's own tokens (disputes.tokens,
                  difflib): every patched page must differ from ours at FEWER
                  places, and at NO place where the unpatched page agreed —
                  a patch may only remove a disagreement, never make one
  (b) words       no patch takes out an ordinary word: Wikisource's text it
                  removes holds none of 3+ letters from the common-word list
                  that our replacement does not also hold
  (a) TeX         every formula a patch brings is collected as the pipeline
                  hands it to KaTeX (the walker's «MATH» bodies of the patched
                  page) — written to tex.json for katex_check.mjs

Writes validate.json {stem: [problems]}; prints the tally.
Usage: validate_patches.py  (book root)"""
import copy
import difflib
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from paths import WORK, reading
from patterns import RAW_MATH
sys.path.insert(0, "tools/diagnostics")
import supplied_gate as g
from disputes import MATH, latex_of, tokens
from apply import apply
from raw_tokens import SPLIT, norm
from build_words import COMMON

from wikikit.scan import supplied
from wikikit.source_pages import fetched_text

WORDS = {w for w in COMMON if len(w) >= 3}


def sites(a, b):
    """The disagreeing stretches of token lists a (Wikisource) and b (ours),
    each as (a tokens, b tokens, the 3 agreed tokens before in b)."""
    out = set()
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op != "equal":
            out.add((" ".join(a[i1:i2]), " ".join(b[j1:j2]), " ".join(b[max(0, j1 - 3):j1])))
    return out


def main():
    patches = json.loads((WORK / (sys.argv[1] if len(sys.argv) > 1 else "kept.json")).read_text(encoding="utf-8"))
    problems, tally, tex = {}, Counter(), {}
    for stem, ps in sorted(patches.items()):
        v, p = int(stem[3:5]), int(stem[-4:])
        ws = fetched_text(v, p) or ""
        patched = apply(ws, ps)
        d = json.loads((reading(stem)).read_text(encoding="utf-8"))
        ours = supplied.name_sections(copy.deepcopy(d))["raw_text"]
        O = tokens(v, p, ours)
        before, after = sites(tokens(v, p, ws), O), sites(tokens(v, p, patched), O)
        bad = []
        if len(after) >= len(before):
            bad.append(f"no fewer disagreements ({len(before)} -> {len(after)})")
        # a new disagreement: one whose OUR side and context did not disagree before
        old_ours = {(o, c) for _, o, c in before}
        new = [s for s in after if (s[1], s[2]) not in old_ours and s[1]]
        for s in new:
            bad.append(f"new disagreement: ws {s[0]!r} vs ours {s[1]!r} after {s[2]!r}")
        for x in ps:
            gone = {t for t in SPLIT.findall(norm(x["old"]))} & WORDS
            kept = {t for t in SPLIT.findall(norm(RAW_MATH.sub(" ", x["new"])))}
            if gone - kept:
                bad.append(f"removes word(s) {sorted(gone - kept)}: {x['old'][:60]!r}")
        # the formulas the pipeline will hand KaTeX, from the patched page
        walked = g.walked(v, p, patched)
        new_tex = [latex_of(m.group(0)) for m in MATH.finditer(walked)]
        tex[stem] = new_tex
        tally["pages"] += 1
        tally["patches"] += len(ps)
        tally["disagreements before"] += len(before)
        tally["disagreements after"] += len(after)
        if bad:
            problems[stem] = bad
            tally["pages with a problem"] += 1
            tally["problems"] += len(bad)
    (WORK / "validate.json").write_text(json.dumps(problems, indent=1, ensure_ascii=False), encoding="utf-8")
    (WORK / "tex.json").write_text(json.dumps(tex, ensure_ascii=False), encoding="utf-8")
    print(dict(tally))
    kinds = Counter(b.split(":")[0].split(" (")[0] for bs in problems.values() for b in bs)
    print(dict(kinds))


if __name__ == "__main__":
    main()
