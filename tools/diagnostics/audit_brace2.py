"""Corpus-wide audit of {{brace2|...}} usage.

Theory under test (task #31): tables containing {{brace2|N|side}} are
typography-crutch hierarchical layouts in disguise.  But most brace2
turn out to live in front-matter `{{EB1911 contributor table/...}}`
templates (the contributor index), processed by the contributor
extractor — NOT by the article-body pipeline.  Filter accordingly to
see what brace2 ACTUALLY reaches the body / table producers.

Usage:
    uv run python tools/diagnostics/audit_brace2.py
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

PAGES_ROOT = Path("data/raw/wikisource")

BRACE2_RE = re.compile(r"\{\{\s*brace2\s*\|([^{}|]+)\|([^{}]+)\}\}", re.IGNORECASE)
CONTRIB_TPL_RE = re.compile(r"\{\{\s*EB1911 contributor table", re.IGNORECASE)


def classify_context(raw: str, pos: int) -> str:
    """Where does this brace2 live?

    * `contributor`: inside a `{{EB1911 contributor table/…}}` template.
    * `in_wikitable`: inside a `{|`/`<table>` wikitable, not contributor.
    * `body`: outside both — directly in body prose / outline.
    """
    pre = raw[:pos]
    # Inside a contributor template if the nearest unclosed
    # `{{EB1911 contributor table` is more recent than its `}}`.
    # Heuristic: look back ~2000 chars (these templates are large).
    last_contrib = max(
        (m.start() for m in CONTRIB_TPL_RE.finditer(pre)), default=-1)
    if last_contrib >= 0:
        # See if the contributor template has closed before our pos
        # (counting brace depth from there).
        depth = 0
        i = last_contrib
        while i < pos:
            if raw[i:i + 2] == "{{":
                depth += 1
                i += 2
            elif raw[i:i + 2] == "}}":
                depth -= 1
                i += 2
                if depth == 0:
                    break
            else:
                i += 1
        if depth > 0:
            return "contributor"

    # Else: inside wikitable?
    last_table_open = max(pre.rfind("{|"), pre.rfind("<table"))
    last_table_close = max(pre.rfind("|}"), pre.rfind("</table>"))
    if last_table_open > last_table_close and last_table_open > 0:
        return "in_wikitable"
    return "body"


def main() -> int:
    sides: Counter[str] = Counter()
    by_context: Counter[str] = Counter()
    by_ctx_side: Counter[tuple[str, str]] = Counter()
    samples_by_ctx: dict[str, list[tuple[str, str]]] = defaultdict(list)

    for vol_dir in sorted(PAGES_ROOT.glob("vol_*")):
        for page_path in sorted(vol_dir.glob("*.json")):
            data = json.loads(page_path.read_text(encoding="utf-8"))
            raw = data.get("raw_text") or data.get("wikitext") or ""
            if "brace2" not in raw.lower():
                continue
            for m in BRACE2_RE.finditer(raw):
                side = m.group(2).strip().lower().replace("''", "")
                ctx = classify_context(raw, m.start())
                sides[side] += 1
                by_context[ctx] += 1
                by_ctx_side[(ctx, side)] += 1
                if len(samples_by_ctx[ctx]) < 4:
                    lo = max(0, m.start() - 100)
                    hi = min(len(raw), m.end() + 100)
                    snippet = raw[lo:hi].replace("\n", "\\n")[:300]
                    samples_by_ctx[ctx].append((page_path.name, snippet))

    total = sum(by_context.values())
    out: list[str] = []
    out.append(f"# brace2 corpus audit — {total} occurrences, classified by context")
    out.append("")
    out.append("## By context")
    for ctx, n in by_context.most_common():
        pct = 100 * n / total
        out.append(f"  {ctx:18s} {n:5d}  ({pct:.0f}%)")
    out.append("")
    out.append("## By context × side")
    for (ctx, side), n in sorted(by_ctx_side.items(), key=lambda kv: -kv[1]):
        out.append(f"  {ctx:18s} side={side!r:4s} {n:5d}")
    out.append("")
    out.append("## Samples by context")
    for ctx, samples in samples_by_ctx.items():
        out.append(f"\n### {ctx}")
        for fname, snippet in samples:
            out.append(f"  [{fname}]")
            out.append(f"    {snippet}")
    Path("tools/_scratch/brace2_audit.txt").write_text(
        "\n".join(out), encoding="utf-8")
    print(f"wrote tools/_scratch/brace2_audit.txt")
    print(f"{total} brace2 occurrences")
    for ctx, n in by_context.most_common():
        print(f"  {ctx}: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
