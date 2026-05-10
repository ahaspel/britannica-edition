"""Catalog articles with HTMLTABLE-leak markers (html_tag /
leaked_html_attr categories from quality_report.py).

The leaks generally fall into a few shapes:

1. **Incomplete wrapper** — content like `</td><td>...</td>` or
   `colspan=N` appears outside any `«HTMLTABLE:…«/HTMLTABLE»` block.
   The transformer captured part of the table but not all.
2. **Multiple adjacent HTMLTABLE blocks** that should have been one.
3. **Mixed wiki/html table** — wikitable markup (`{|`/`|}`) interleaved
   with HTML tags.
4. **Outside-wrapper trailing chunk** — table ended cleanly but a
   stranded `</td></tr>` shows up after the wrapper close.

For each flagged file: show context around the first leak, plus a
quick summary of HTMLTABLE block counts and whether the leak is
inside or outside any wrapper.

Usage:
    uv run python tools/diagnostics/htmltable_leak_audit.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ARTICLES_DIR = Path("data/derived/articles")

_HTMLTABLE_BLOCK_RE = re.compile(
    r"«HTMLTABLE:.*?«/HTMLTABLE»",
    re.DOTALL,
)
_HTML_TAG_RE = re.compile(
    r"<(?:table|tr|td|th|div|span|br|sub|sup|ref|poem|score|math)\b[^>]*>",
    re.IGNORECASE,
)
_LEAKED_ATTR_RE = re.compile(r"nowrap|colspan|rowspan|cellpadding")


def _excerpt(body: str, idx: int, span: int = 100) -> str:
    start = max(0, idx - span)
    end = min(len(body), idx + span)
    return body[start:end].replace("\n", " ").replace("\r", "")


def _classify_leak(body: str, idx: int) -> str:
    """Determine if the leak position is inside an HTMLTABLE block."""
    for m in _HTMLTABLE_BLOCK_RE.finditer(body):
        if m.start() <= idx < m.end():
            return "inside-htmltable"
    return "outside-htmltable"


def main() -> int:
    flagged: list[dict] = []
    for path in ARTICLES_DIR.glob("*.json"):
        if path.name.startswith(("index", "contributors", "front_matter")):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        body = data.get("body", "") or ""
        if not body:
            continue

        # Mirror quality_report.py exactly: strip HTMLTABLE / MATH /
        # IMG (length-preserving so positions stay aligned with the
        # original body for context excerpts) then look for leaks.
        def _blank(m):
            return " " * len(m.group(0))
        stripped = re.sub(r"«HTMLTABLE:.*?«/HTMLTABLE»",
                          _blank, body, flags=re.DOTALL)
        stripped = re.sub(r"«MATH:.*?«/MATH»",
                          _blank, stripped, flags=re.DOTALL)
        stripped_for_tag = re.sub(r"\{\{IMG:[^}]*\}\}",
                                   _blank, stripped)

        tag_match = _HTML_TAG_RE.search(stripped_for_tag)
        attr_match = _LEAKED_ATTR_RE.search(stripped)
        if not tag_match and not attr_match:
            continue

        leak_idx = -1
        leak_kind = []
        if tag_match:
            leak_idx = tag_match.start()
            leak_kind.append("html_tag")
        if attr_match:
            if leak_idx < 0 or attr_match.start() < leak_idx:
                leak_idx = attr_match.start()
            leak_kind.append("leaked_html_attr")

        # Count HTMLTABLE blocks
        n_blocks = len(_HTMLTABLE_BLOCK_RE.findall(body))
        # Distance from leak to nearest HTMLTABLE block boundary
        nearest_dist = float("inf")
        nearest_side = "?"
        for m in _HTMLTABLE_BLOCK_RE.finditer(body):
            if leak_idx < m.start():
                d = m.start() - leak_idx
                side = "before-block"
            elif leak_idx >= m.end():
                d = leak_idx - m.end()
                side = "after-block"
            else:
                d = 0
                side = "inside-block"
            if d < nearest_dist:
                nearest_dist = d
                nearest_side = side
        location = (
            f"{nearest_side} (dist {nearest_dist})"
            if n_blocks else "no-htmltable-block"
        )

        flagged.append({
            "filename": path.name,
            "title": data.get("title", ""),
            "vol": data.get("volume"),
            "kinds": leak_kind,
            "n_htmltable_blocks": n_blocks,
            "leak_location": location,
            "excerpt": _excerpt(body, leak_idx) if leak_idx >= 0 else "",
            "body_size": len(body),
        })

    # Group by leak_location for clarity.
    print(f"Total flagged files: {len(flagged)}\n")

    # Summary table.
    print("| vol | title | kinds | htmltable blocks | leak loc | size |")
    print("|---|---|---|---|---|---|")
    for r in sorted(flagged, key=lambda r: (r["vol"] or 0, r["filename"])):
        kinds = "+".join(r["kinds"])
        print(
            f"| {r['vol']} | {r['title']} | {kinds} | "
            f"{r['n_htmltable_blocks']} | {r['leak_location']} | "
            f"{r['body_size']:,} |"
        )

    print("\n\n## Excerpts\n")
    for r in sorted(flagged, key=lambda r: (r["vol"] or 0, r["filename"])):
        print(f"### {r['title']} (vol {r['vol']})")
        print(f"  {r['filename']}  [{'+'.join(r['kinds'])}]")
        print(f"  htmltable_blocks={r['n_htmltable_blocks']}  "
              f"leak_location={r['leak_location']}  "
              f"size={r['body_size']:,}")
        print(f"  excerpt:")
        print(f"    {r['excerpt']!r}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
