"""Build the corpus-frequency dehyphenation map → data/hyphen_map.json.

A ONE-TIME build, committed as a fixed asset (beside data/corrections.json).  The
EB1911 source is static, and the verdicts ride on counts in the thousands, so a
few changed pages can't flip them — it is NOT regenerated each rebuild.  Re-run
by hand only if you ever want to re-derive it.

A word broken across a line/column wrap (`X-<break>Y`) leaves a hyphen the body
text producer must resolve: drop it (wrap artifact) or keep it (real compound).
The corpus is the dictionary.  For every wrap-candidate we compare how often the
joined word appears SOLID (`XY`) versus as a genuine mid-line hyphen (`X-Y`):

  * solid wins   -> "drop"  (sometimes, government, coefficient)
  * hyphen wins  -> "keep"  (well-known, horse-power, wave-length)
  * neither real -> omitted (the body producer leaves it: suspended hyphens
    like "basket- and mat-maker", rare coinages)

The map is keyed by the lowercased candidate `x-y`; absence means "leave".  The
body producer (`_produce_body`) loads it and applies it to every `X-<break>Y` it
meets — break-agnostic, because every wrap (hws/lps/<br>/newline/dual-line)
recurses to the body producer as the same shape.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from britannica.db.session import SessionLocal
from britannica.db.models import SourcePage

_SOLID = re.compile(r"[A-Za-z]{2,}")
_HYPH = re.compile(r"([A-Za-z]{2,})-([A-Za-z]{2,})")              # contiguous = genuine
_WRAP = re.compile(r"([A-Za-z]{2,})-\s*(?:<br[^>]*>|\n)\s*([A-Za-z]{2,})", re.I)

OUT = Path("data/hyphen_map.json")


def build() -> dict[str, str]:
    freq_solid: Counter = Counter()
    freq_hyph: Counter = Counter()
    candidates: set[tuple[str, str]] = set()

    session = SessionLocal()
    for p in session.query(SourcePage).all():
        wt = p.wikitext or ""
        if not wt:
            continue
        low = wt.lower()
        freq_solid.update(_SOLID.findall(low))
        freq_hyph.update(_HYPH.findall(low))
        candidates.update((x.lower(), y.lower()) for x, y in _WRAP.findall(wt))

    out: dict[str, str] = {}
    for x, y in candidates:
        solid = freq_solid.get(x + y, 0)
        hyph = freq_hyph.get((x, y), 0)
        if solid == 0 and hyph == 0:
            continue                                  # leave (absent)
        out[f"{x}-{y}"] = "drop" if solid > hyph else "keep"
    return out


if __name__ == "__main__":
    mp = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(mp, indent=0, sort_keys=True, ensure_ascii=False),
                   encoding="utf-8")
    from collections import Counter as C
    tally = C(mp.values())
    print(f"wrote {OUT}  ({len(mp)} entries: {dict(tally)})")
