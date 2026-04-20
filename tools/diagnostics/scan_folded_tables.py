"""Scan raw wikisource for 'folded multi-row' tables — where a single
wikitext row's cells each contain N ``<br>``-separated values, representing
N logical rows collapsed into one physical row.

Detection: a ``|-``-delimited row of a ``{|…|}`` table where ≥ 2 cells each
contain ≥ 2 ``<br>`` tags (so each cell has ≥ 3 stacked values). Lower
thresholds catch noise (headers with a single line break).

Output: one line per affected page with a count of folded rows found.
"""
from __future__ import annotations

import io
import json
import os
import re
import sys
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                              errors="replace")

RAW_DIR = "data/raw/wikisource"
BR_RE = re.compile(r"<br\s*/?>", re.IGNORECASE)
TABLE_RE = re.compile(r"\{\|[\s\S]*?\n\|\}", re.MULTILINE)
ROW_SPLIT_RE = re.compile(r"^\|-[^\n]*$", re.MULTILINE)


def count_br_in_cell(cell: str) -> int:
    return len(BR_RE.findall(cell))


def cells_of_row(row_text: str) -> list[str]:
    """Return cell contents for one wikitable row.

    Handles both newline-separated ``|`` lines and inline ``||`` separators.
    Attributes before the final ``|`` are dropped.
    """
    cells = []
    for line in row_text.split("\n"):
        line = line.strip()
        if not line or line.startswith("|+"):
            continue
        if not (line.startswith("|") or line.startswith("!")):
            continue
        body = line[1:]
        sep = "!!" if line.startswith("!") else "||"
        for chunk in body.split(sep):
            if "|" in chunk:
                # strip attrs (everything before last `|`)
                _, _, content = chunk.rpartition("|")
            else:
                content = chunk
            cells.append(content)
    return cells


_TRAILING_BR_RE = re.compile(r"(?:\s*<br\s*/?>\s*)+$", re.IGNORECASE)


def split_count(cell: str) -> int:
    """Number of `<br>`-separated values in the cell, ignoring a
    purely-trailing `<br>` (wikisource authors often add one for visual
    padding — it shouldn't add a phantom empty value)."""
    trimmed = _TRAILING_BR_RE.sub("", cell)
    return len(BR_RE.findall(trimmed)) + 1


def row_is_foldable(cells: list[str]) -> list[int] | None:
    """Return split-counts if this row structurally admits a fold.

    A folded row is one where N logical rows have been stacked into
    one physical row with `<br>` within each cell. The structural test:
    let N = max split count across cells; require N ≥ 2, every cell
    splits into exactly 1 (constant column) or N (unfolded column),
    and ≥ 2 cells split into N. Any cell with a split count other than
    1 or N breaks the fold interpretation → reject.
    """
    if not cells:
        return None
    splits = [split_count(c) for c in cells]
    n = max(splits)
    if n < 2:
        return None
    if any(s != 1 and s != n for s in splits):
        return None
    if sum(1 for s in splits if s == n) < 2:
        return None
    return splits


def scan_table(table_text: str) -> list[list[int]]:
    """Return split-counts per folded row, but only if the table as a
    whole is a folded table.

    A genuine folded table has folds as the dominant mode — a lone
    folded row among many plain-data siblings (e.g. a battleship row
    with a multi-line engine-description cell in a 20-ship table)
    is an in-cell line-wrap, not a fold. Require folded rows to be
    ≥ 50% of the table's non-empty `|-`-delimited rows.
    """
    parts = ROW_SPLIT_RE.split(table_text)
    row_splits = []
    fold_candidates = []
    for part in parts:
        cells = cells_of_row(part)
        if not cells:
            continue
        row_splits.append(cells)
        foldable = row_is_foldable(cells)
        if foldable is not None:
            fold_candidates.append(foldable)
    if not fold_candidates:
        return []
    # A genuine folded table has its data compressed into ONE physical
    # data row. Two structural boundary tests:
    #   a. ≤ 1 fold candidate per table — multiple candidates indicate
    #      intra-cell formatting repeating across sibling data rows
    #      (e.g. "1500°F<br>(815.5°C)" unit conversions).
    #   b. The fold candidate must be at least half of the table's
    #      non-empty rows — a lone fold in a 20-row table is a quirky
    #      multi-line cell, not a fold.
    if len(fold_candidates) > 1:
        return []
    if len(fold_candidates) * 2 < len(row_splits):
        return []
    return fold_candidates


def main() -> int:
    per_vol = defaultdict(int)
    per_page: dict[tuple[int, int], list] = {}
    total_rows = 0
    total_pages = 0
    for volname in sorted(os.listdir(RAW_DIR)):
        vol_dir = os.path.join(RAW_DIR, volname)
        if not os.path.isdir(vol_dir):
            continue
        try:
            vol = int(volname.replace("vol_", ""))
        except ValueError:
            continue
        for fname in sorted(os.listdir(vol_dir)):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(vol_dir, fname)
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
            except (OSError, json.JSONDecodeError):
                continue
            raw = data.get("raw_text") or ""
            if "<br" not in raw or "{|" not in raw:
                continue
            page_rows = []
            for m in TABLE_RE.finditer(raw):
                hits = scan_table(m.group(0))
                page_rows.extend(hits)
            if page_rows:
                page = data.get("page_number") or 0
                per_vol[vol] += len(page_rows)
                per_page[(vol, page)] = page_rows
                total_rows += len(page_rows)
                total_pages += 1

    print(f"Folded rows found: {total_rows}")
    print(f"Pages affected: {total_pages}")
    print()
    print("By volume:")
    for vol in sorted(per_vol):
        print(f"  vol {vol:02d}: {per_vol[vol]:4d} folded rows")
    print()
    print("Top 20 pages by folded-row count:")
    top = sorted(per_page.items(), key=lambda kv: -len(kv[1]))[:20]
    for (vol, page), rows in top:
        counts_summary = ",".join(str(max(r)) for r in rows[:6])
        print(f"  vol{vol:02d} p{page:04d}  rows={len(rows):2d}  "
              f"max-br per row: [{counts_summary}{'...' if len(rows) > 6 else ''}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
