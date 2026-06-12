r"""Corpus crash-check for the generic `{{…}}` walker flip.

Walks every `SourcePage.wikitext` exactly as PRODUCTION does — `preprocess`
first (so page-chrome `{{nop}}`/`{{EB1911 Page Heading}}`/`{{hws}}` are gone and
`<math>` opacity is in force), then the genericized `walk` + `classify` — and
reports every distinct `{{…}}` opener whose classify `raise`s.

Mirroring production (rather than synthesising `{{opener}}` / `{{opener|x}}`
strings) is the point: a `{{…}}` that only ever appears INSIDE an opaque
`<math>` (LaTeX fragments like `{{1\over 2}` or `{{x^p}`) is never extracted as
a DOUBLE_BRACE in production, so it must not show as a straggler here either —
the old synthetic probe produced exactly those false positives.

Run: uv run python tools/diagnostics/double_brace_crash_check.py
"""
from __future__ import annotations

import re
import sys
from collections import Counter

from britannica.db.session import SessionLocal
from britannica.db.models import SourcePage
from britannica.pipeline.stages.preprocess import preprocess
from britannica.pipeline.stages.elements._walker import walk
from britannica.pipeline.stages.elements._classifier import classify

_OPENER_RE = re.compile(r"\{\{\s*([^|{}\n]+?)\s*(?=[|}])")


def scan() -> tuple[Counter, dict[str, tuple[str, str]]]:
    """Walk+classify every page as production does.  Returns:
      * ``opener_counts`` — every distinct `{{…}}` opener seen in raw wikitext
        (so the report can show how common a straggler is), and
      * ``raises`` — ``{error_message: (count, sample_raw)}`` for every classify
        that raised on a REAL walked DOUBLE_BRACE extract.
    """
    s = SessionLocal()
    opener_counts: Counter = Counter()
    raises: dict[str, list] = {}
    try:
        q = s.query(SourcePage.wikitext).yield_per(200)
        for (wt,) in q:
            if not wt:
                continue
            for m in _OPENER_RE.finditer(wt):
                opener_counts[m.group(1)] += 1
            try:
                text = preprocess(wt)
                _ph, extracts = walk(text)
            except Exception as e:  # noqa: BLE001 — a walk failure is itself a finding
                key = f"WALK {type(e).__name__}: {e}"[:90]
                raises.setdefault(key, [0, wt[:90]])[0] += 1
                continue
            for _ph, shape, raw in extracts:
                try:
                    classify(shape, raw)
                except Exception as e:  # noqa: BLE001
                    key = f"{type(e).__name__}: {e}"
                    raises.setdefault(key, [0, raw[:90]])[0] += 1
    finally:
        s.close()
    return opener_counts, {k: (v[0], v[1]) for k, v in raises.items()}


def main() -> int:
    opener_counts, raises = scan()
    print(f"distinct openers: {len(opener_counts)}", file=sys.stderr)
    if not raises:
        print("ZERO raise across all corpus openers.")
        return 0
    total = sum(n for n, _ in raises.values())
    print(f"STRAGGLERS ({len(raises)} distinct, {total} occurrences):")
    for msg, (n, sample) in sorted(raises.items(), key=lambda kv: -kv[1][0]):
        print(f"  [{n:>6}] {msg}")
        print(f"           sample: {sample!r}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
