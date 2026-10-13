"""The word judge's tokens (`disputes.tokens`) WITH their places: the same
pipeline — captions out, the walk, formulas as their letters, footnotes,
tables' and verse's markers, margin headings out, markers_to_text, NFKC and
SAME — but every token keeps its span in the plain text (before NFKC/SAME,
so a span gives the page's own characters, its case and punctuation), and a
formula's tokens carry the formula's number on the page.

flat_tokens(v, p, text) -> (plain, [(token, start, end, formula or None)], formulas)
where `formulas` is each «MATH» body in page order."""
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, "tools/diagnostics")
import supplied_gate as g
from disputes import CAPTION_LINE, MATH, SAME, SPLIT, latex_of, math_letters, running_text

from wikikit.markers import markers_to_text

OPEN, CLOSE = "⟪", "⟫"        # ⟪ ⟫: not letters, not digits, survive markers_to_text


def flat_tokens(v, p, text):
    text = CAPTION_LINE.sub("", text)
    formulas = []

    def keep(m):
        latex = latex_of(m.group(0))
        formulas.append(latex)
        return f" {OPEN}{len(formulas) - 1}{CLOSE} {math_letters(latex)} {OPEN}{CLOSE} "

    plain = markers_to_text(running_text(MATH.sub(keep, g.walked(v, p, text))))
    # normalised text with a map back to `plain`
    norm, back = [], []
    for i, ch in enumerate(plain):
        for c in unicodedata.normalize("NFKC", ch):
            for c2 in SAME.get(c, c):
                norm.append(c2)
                back.append(i)
    norm = "".join(norm)
    toks, formula = [], None
    for m in re.finditer(rf"{OPEN}(\d*){CLOSE}|[^\W\d_]+|\d+", norm):
        if m.group(0).startswith(OPEN):
            formula = int(m.group(1)) if m.group(1) else None
            continue
        toks.append((m.group(0).lower(), back[m.start()], back[m.end() - 1] + 1, formula))
    return plain, toks, formulas
