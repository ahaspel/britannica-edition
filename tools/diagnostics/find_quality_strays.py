"""Find the actual articles flagged by quality_report.py's file-level
issue checks, with the offending substring excerpt for each.

quality_report.py only counts; this surfaces the files + samples so
we can spot patterns in the strays.

Usage:
    uv run python tools/diagnostics/find_quality_strays.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ARTICLES_DIR = Path("data/derived/articles")


def _excerpt(body: str, idx: int, span: int = 60) -> str:
    start = max(0, idx - span)
    end = min(len(body), idx + span)
    return body[start:end].replace("\n", " ").replace("\r", "")


def main() -> int:
    by_issue: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    # (filename, title, excerpt)

    for path in ARTICLES_DIR.glob("*.json"):
        # Skip the index.json / contributors.json / etc.
        if path.name.startswith(("index", "contributors", "front_matter")):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        body = data.get("body", "") or ""
        title = data.get("title", "")
        if not body:
            continue

        # Strip HTMLTABLE / MATH for noise-stripped checks (mirrors
        # quality_report.py's logic).
        clean = re.sub(r"«HTMLTABLE:.*?«/HTMLTABLE»",
                       "", body, flags=re.DOTALL)
        clean = re.sub(r"«MATH:.*?«/MATH»",
                       "", clean, flags=re.DOTALL)

        # stray_braces: {{ but no known marker
        if "{{" in clean and not any(
            m in clean for m in ["{{IMG:", "{{TABLE", "{{FN:", "{{VERSE:"]
        ):
            idx = clean.find("{{")
            by_issue["stray_braces"].append(
                (path.name, title, _excerpt(clean, idx))
            )

        # stray_close_braces: }} but not from known markers
        if "}}" in clean and "TABLE}" not in clean and \
                "IMG:" not in clean and "VERSE}" not in clean:
            idx = clean.find("}}")
            by_issue["stray_close_braces"].append(
                (path.name, title, _excerpt(clean, idx))
            )

        # stray_wiki_italic
        if "''" in clean:
            idx = clean.find("''")
            by_issue["stray_wiki_italic"].append(
                (path.name, title, _excerpt(clean, idx))
            )

        # html_tag (strip IMG markers first since they legitimately use HTML)
        tag_clean = re.sub(r"\{\{IMG:[^}]*\}\}", "", clean)
        m = re.search(
            r"<(?:table|tr|td|th|div|span|br|sub|sup|ref|poem|score|math)\b[^>]*>",
            tag_clean, re.I,
        )
        if m:
            by_issue["html_tag"].append(
                (path.name, title, _excerpt(tag_clean, m.start()))
            )

        # pipe_leak
        bare = re.sub(r"\{\{TABLE.*?\}TABLE\}", "", body, flags=re.DOTALL)
        bare = re.sub(r"\{\{VERSE:.*?\}VERSE\}", "", bare, flags=re.DOTALL)
        bare = re.sub(r"«MATH:.*?«/MATH»",
                      "", bare, flags=re.DOTALL)
        pipe_lines = [
            line for line in bare.split("\n")
            if re.match(r"\s*\|{1,2}\s*\S", line)
            or "figure |" in line or "figure|" in line
        ]
        if len(pipe_lines) > 3:
            by_issue["pipe_leak"].append(
                (path.name, title, " | ".join(pipe_lines[:3])[:120])
            )

        # leaked_html_attr: cell-table attribute names leaking outside
        check = re.sub(r"«HTMLTABLE:.*?«/HTMLTABLE»",
                       "", body, flags=re.DOTALL)
        m = re.search(r"nowrap|colspan|rowspan|cellpadding", check)
        if m:
            by_issue["leaked_html_attr"].append(
                (path.name, title, _excerpt(check, m.start()))
            )

        # stray_control_x06
        for i in range(9):
            if chr(i) in body and i not in (1, 2):
                # locate
                idx = body.find(chr(i))
                by_issue[f"stray_control_x0{i}"].append(
                    (path.name, title,
                     _excerpt(body, idx).replace(chr(i), "\\x0" + str(i)))
                )
                break

    # Render
    for issue, items in by_issue.items():
        print(f"\n=== {issue} ({len(items)}) ===")
        for fn, title, ex in items[:20]:
            print(f"  {fn}  ({title})")
            print(f"    {ex!r}")
        if len(items) > 20:
            print(f"  … and {len(items) - 20} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
