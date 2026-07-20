"""Triage every render leak into PRODUCER BUG vs RAW-SOURCE ERROR.

The leak audit answers "what came out looking like markup?".  It does not answer
the question that decides who fixes it: *was the source well-formed?*  That is the
discriminator ([[feedback_source_is_the_only_excuse]]): a wrong render is faithful
ONLY if the raw source really had it; otherwise it is a producer bug.

For each leaking article this walks back to the raw wikitext pages behind it and
asks whether the leaking construct is well-formed THERE:

  * an unclosed `{{name|` / an orphan `</math>` / a `{{{param}}}` with no default
    → the SOURCE is malformed; a faithful pipeline surfaces it.  Fix belongs in
      `data/corrections.json` ([[feedback_corrections_json]]).
  * the construct is balanced and ordinary in the source but still leaked
    → the PRODUCER failed to recognize/recurse it.  Fix belongs in the pipeline.

Emits a ranked report so the producer bugs can be worked first and the source
errors batched for last.

Usage:  uv run python tools/diagnostics/triage_render_leaks.py [--limit N]
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, "src")

from britannica.export.corpus import load_corpus            # noqa: E402
from britannica.render.leaks import find_render_leaks       # noqa: E402

RAW_GLOB = "data/raw/wikisource/vol_{vol:02d}/*.json"

# What the leaking fragment looks like, and how to test the SOURCE for it.
_TEMPLATE_OPEN = re.compile(r"\{\{\s*([^|{}\n]{1,30})")
_TRIPLE = re.compile(r"\{\{\{")


def _raw_for_volume(vol: int, _cache: dict = {}) -> str:
    if vol not in _cache:
        blob = []
        for f in sorted(glob.glob(RAW_GLOB.format(vol=vol))):
            try:
                blob.append(json.load(open(f, encoding="utf-8")).get("raw_text") or "")
            except Exception:
                continue
        _cache[vol] = "\n".join(blob)
    return _cache[vol]


def _mask_nontemplate(text: str) -> str:
    """Blank out math bodies and `{{{param}}}` so their braces can't be mistaken
    for template delimiters (LaTeX `x^{y^{z}}` ends in `}}`)."""
    s = re.sub(r"<math\b.*?</math\s*>", lambda m: " " * len(m.group(0)),
               text, flags=re.DOTALL | re.IGNORECASE)
    return re.sub(r"\{\{\{.*?\}\}\}", lambda m: " " * len(m.group(0)), s, flags=re.DOTALL)


def _closes_at(raw: str, opener: str) -> bool | None:
    """Does THIS occurrence close?  Finds `opener` (the leaked `{{name|` plus the
    literal content that followed it, so it identifies one specific site rather
    than every use of the template) and scans forward for its matching `}}`.

    Per-occurrence on purpose: keying on the template NAME alone would mark a real
    producer bug as a source error whenever some other page in the volume happened
    to leave the same template unclosed.  → True closed / False unclosed / None
    not found."""
    s = _mask_nontemplate(raw)
    i = s.find(opener)
    if i < 0:
        return None
    depth = 0
    for m in re.finditer(r"\{\{|\}\}", s[i:]):
        depth += 1 if m.group(0) == "{{" else -1
        if depth == 0:
            return True
    return False


def classify(snippet: str, raw: str) -> tuple[str, str]:
    """→ (verdict, why).  verdict ∈ {SOURCE, PRODUCER, UNKNOWN}."""
    if _TRIPLE.search(snippet):
        return ("PRODUCER", "template PARAM `{{{x|default}}}` — MediaWiki renders "
                            "the default; leaking the raw form is ours")
    m = _TEMPLATE_OPEN.search(snippet)
    if m:
        name = m.group(1).strip().lower()
        # identify the SITE: the opener plus the content that followed it in the
        # render, minus marker noise the producer introduced.
        tail = re.sub(r"«[^»]*»", "", snippet[m.start():])[:48]
        closed = _closes_at(raw, tail[:24]) if tail else None
        if closed is False:
            return ("SOURCE", f"`{{{{{name}` UNCLOSED at this site in the transcription")
        if closed is True:
            return ("PRODUCER", f"`{{{{{name}` is well-formed at this site but leaked")
        return ("UNKNOWN", f"`{{{{{name}` — site not locatable in raw source")
    if "</math" in snippet or "<math" in snippet:
        return ("SOURCE", "unbalanced <math> in the transcription")
    return ("UNKNOWN", "no recognizable construct in the snippet")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="stop after N leaking articles")
    args = ap.parse_args()

    payloads, _ = load_corpus()
    verdicts: dict[str, list] = defaultdict(list)
    n_art = 0
    for path, d in sorted(payloads.items()):
        html = d.get("rendered_html") or ""
        leaks = find_render_leaks(html)
        if not leaks:
            continue
        n_art += 1
        raw = _raw_for_volume(int(d.get("volume") or 0))
        seen = set()
        for cat, snip in leaks:
            s = re.sub(r"\s+", " ", snip).strip()
            if s[:44] in seen:
                continue
            seen.add(s[:44])
            verdict, why = classify(s, raw)
            verdicts[verdict].append((d.get("title", "")[:30], path.name, cat, why, s[:70]))
        if args.limit and n_art >= args.limit:
            break

    print(f"leaking articles: {n_art}")
    for v in ("PRODUCER", "UNKNOWN", "SOURCE"):
        rows = verdicts.get(v) or []
        print(f"\n{'=' * 78}\n{v}: {len(rows)} leak site(s)\n{'=' * 78}")
        for why, n in Counter(r[3] for r in rows).most_common():
            print(f"  [{n:3}] {why}")
        for title, fn, cat, why, s in rows[:25]:
            print(f"    {title:30} {cat:8} {s!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
