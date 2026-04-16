"""Build printed page number map using two sources:

1. PRIMARY: Wikisource `{{EB1911 Page Heading}}` templates, which encode
   the book's running-header printed page number hand-typed by
   transcribers.
2. FALLBACK: our OCR + monotonic-anchor algorithm, for volumes or pages
   where headings are absent (some volumes' transcribers used
   `Shoulder Heading` and never typed the page numbers).

Output:
    data/derived/printed_pages.json       — ws  -> printed (article exports)
    data/derived/printed_pages_leaf.json  — leaf -> printed (scan viewer)

Usage:
    python tools/build_printed_pages.py
"""
import json
import re
from pathlib import Path

from britannica.db.models import SourcePage
from britannica.db.session import SessionLocal

RAW_DIR = Path("data/raw/wikisource")
OCR_FILE = Path("data/derived/ocr_page_numbers.json")
OUT_WS = Path("data/derived/printed_pages.json")
OUT_LEAF = Path("data/derived/printed_pages_leaf.json")
SCAN_MAP = Path("data/derived/scan_map.json")

LEAF_OFFSET = {
    1: 7, 2: 7, 3: 9, 4: 9, 5: 12, 6: 12, 7: 7, 8: 7,
    9: 9, 10: 10, 11: 8, 12: 7, 13: 7, 14: 6, 15: 17, 16: 6,
    17: 9, 18: 6, 19: 7, 20: 0, 21: 6, 22: 6, 23: 7, 24: 4,
    25: 8, 26: 4, 27: 6, 28: 5, 29: 6,
}

# Manual first/last article anchors per volume (LEAF space).
# Format: (first_leaf, first_printed, last_leaf, last_printed)
VOL_RANGE: dict[int, tuple[int, int, int, int]] = {
    1: (39, 1, 1044, 976),
    2: (19, 1, 1048, 976),
    3: (21, 1, 1026, 992),
    4: (23, 1, 1048, 1004),
    5: (21, 1, 1024, 964),
    6: (23, 1, 1030, 992),
    7: (21, 1, 1016, 984),
    8: (21, 1, 1034, 1000),
    9: (21, 1, 1020, 960),
    10: (23, 1, 984, 944),
    11: (21, 1, 982, 944),
    12: (21, 1, 994, 960),
    13: (21, 1, 998, 960),
    14: (19, 1, 980, 920),
    15: (21, 1, 1030, 960),
    16: (21, 1, 1024, 992),
    17: (21, 1, 1058, 1020),
    18: (19, 1, 1018, 968),
    19: (21, 1, 1062, 996),
    20: (19, 1, 1044, 980),
    21: (21, 1, 1034, 984),
    22: (21, 1, 1002, 976),
    23: (21, 1, 1088, 1024),
    24: (19, 1, 1118, 1024),
    25: (21, 1, 1112, 1064),
    26: (21, 1, 1118, 1064),
    27: (21, 1, 1110, 1064),
    28: (21, 1, 1106, 1064),
}

# Verified-by-user internal anchor runs (LEAF space).
TRUSTED_RUNS: dict[int, list[tuple[int, int, int, int]]] = {
    3: [
        (21, 1, 24, 4),
        (29, 5, 128, 104),
    ],
    8: [(207, 183, 207, 183)],
    10: [(637, 603, 637, 603)],
    14: [(303, 281, 303, 281)],
    15: [(596, 550, 596, 550)],
    18: [
        (44, 20, 44, 20),
        (333, 305, 333, 305),
        (373, 345, 373, 345),
    ],
    19: [
        (538, 504, 538, 504),
        (800, 752, 800, 752),
    ],
    20: [
        (19, 1, 44, 26),
        (48, 27, 79, 58),
        (82, 59, 137, 114),
        (140, 115, 219, 194),
        (517, 471, 517, 471),
        (540, 492, 540, 492),
        (824, 770, 824, 770),
        (858, 800, 858, 800),
        (980, 920, 980, 920),
        (998, 934, 998, 934),
    ],
    23: [
        (46, 26, 46, 26),
        (370, 346, 370, 346),
        (425, 401, 425, 401),
    ],
    26: [(354, 324, 354, 324)],
    28: [(466, 440, 466, 440)],
}


# ─── Source 1: Wikisource Page Heading extraction ────────────────────────────

_HEADING_RE = re.compile(
    r"\{\{EB1911 Page Heading\|([^|]*)\|[^|]*\|[^|]*\|([^|}]*)\}?\}?",
    re.IGNORECASE,
)


def _printed_from_heading(raw_text: str) -> int | None:
    """Extract printed page number from `{{EB1911 Page Heading|L|...|R}}`."""
    if not raw_text:
        return None
    m = _HEADING_RE.search(raw_text[:600])
    if not m:
        return None
    for val in (m.group(1), m.group(2)):
        mn = re.search(r"\b(\d{1,4})\b", val)
        if mn:
            n = int(mn.group(1))
            if 1 <= n <= 1200:
                return n
    return None


def _harvest_headings(vol: int, all_ws: list[int]) -> dict[int, int]:
    """Scan every ws page's raw wikitext for a heading-embedded printed page."""
    vol_dir = RAW_DIR / f"vol_{vol:02d}"
    result: dict[int, int] = {}
    for ws in all_ws:
        f = vol_dir / f"vol{vol:02d}-page{ws:04d}.json"
        if not f.exists():
            continue
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        printed = _printed_from_heading(d.get("raw_text", ""))
        if printed is not None:
            result[ws] = printed
    return result


# ─── Source 2: OCR + monotonic-anchor algorithm (leaf space) ─────────────────


def _build_ocr_runs(pairs: list[tuple[int, int]]) -> list[list[tuple[int, int]]]:
    runs = []
    if not pairs:
        return runs
    cur = [pairs[0]]
    for i in range(1, len(pairs)):
        leaf, printed = pairs[i]
        pl, pp = pairs[i - 1]
        if printed == pp + (leaf - pl):
            cur.append(pairs[i])
        else:
            if len(cur) >= 2:
                runs.append(cur)
            cur = [pairs[i]]
    if len(cur) >= 2:
        runs.append(cur)
    return runs


def _leaf_algorithm(
    vol_ocr: dict[str, int],
    vol_range: tuple[int, int, int, int] | None,
    trusted: list[tuple[int, int, int, int]],
) -> dict[int, int]:
    """Return leaf -> printed produced by the OCR + anchors algorithm."""
    if vol_range is not None:
        first_leaf, first_printed, last_leaf, last_printed = vol_range
        off_min = first_leaf - first_printed
        off_max = last_leaf - last_printed
    else:
        first_leaf, first_printed, last_leaf, last_printed = 0, 0, 0, 0
        off_min, off_max = 0, 10_000

    trusted_ranges = [(r[0], r[2]) for r in trusted]

    def in_trusted(leaf: int) -> bool:
        return any(a <= leaf <= b for a, b in trusted_ranges)

    ocr_pairs: list[tuple[int, int]] = []
    for leaf_s, printed in vol_ocr.items():
        leaf = int(leaf_s)
        offset = leaf - printed
        if offset < off_min or offset > off_max:
            continue
        if in_trusted(leaf):
            continue
        ocr_pairs.append((leaf, printed))
    ocr_pairs.sort()

    ocr_runs = _build_ocr_runs(ocr_pairs)
    trusted_run_list = [[(la, pa), (lb, pb)] for la, pa, lb, pb in trusted]

    if vol_range is not None:
        has_first = any(r[0][0] == first_leaf for r in trusted_run_list)
        has_last = any(r[-1][0] == last_leaf for r in trusted_run_list)
        if not has_first:
            trusted_run_list.append([(first_leaf, first_printed)])
        if not has_last:
            trusted_run_list.append([(last_leaf, last_printed)])

    all_runs = ocr_runs + trusted_run_list
    all_runs.sort(key=lambda r: r[0][0])

    trusted_points: list[tuple[int, int]] = []
    for run in trusted_run_list:
        for leaf, printed in [(run[0][0], run[0][1]), (run[-1][0], run[-1][1])]:
            trusted_points.append((leaf, leaf - printed))
    trusted_points.sort()

    def _cap_at(leaf: int) -> int:
        cap = off_max
        for tl, to in trusted_points:
            if tl >= leaf and to < cap:
                cap = to
        return cap

    accepted = []
    running = off_min
    for run in all_runs:
        offset = run[0][0] - run[0][1]
        if offset < running:
            continue
        if offset > _cap_at(run[0][0]):
            continue
        accepted.append(run)
        if offset > running:
            running = offset

    if vol_range is not None:
        fl_bound, ll_bound = first_leaf, last_leaf
    else:
        fl_bound, ll_bound = 0, 10_000

    def _in_bounds(leaf: int) -> bool:
        return fl_bound <= leaf <= ll_bound

    leaf_to_printed: dict[int, int] = {}
    for run in accepted:
        leaf_start, printed_start = run[0]
        leaf_end, _ = run[-1]
        for leaf in range(leaf_start, leaf_end + 1):
            if _in_bounds(leaf):
                leaf_to_printed[leaf] = printed_start + (leaf - leaf_start)

    # Extend runs across gaps: numbered-extra leaves at run A's offset,
    # unnumbered leaves at the gap end.
    for i in range(len(accepted) - 1):
        run_a = accepted[i]
        run_b = accepted[i + 1]
        leaf_a_end = run_a[-1][0]
        leaf_b_start = run_b[0][0]
        offset_a = run_a[0][0] - run_a[0][1]
        offset_b = run_b[0][0] - run_b[0][1]
        gap_size = leaf_b_start - leaf_a_end - 1
        offset_bump = offset_b - offset_a
        numbered_extra = gap_size - offset_bump
        for k in range(1, numbered_extra + 1):
            leaf = leaf_a_end + k
            printed = leaf - offset_a
            if printed >= 1 and _in_bounds(leaf):
                leaf_to_printed[leaf] = printed

    return leaf_to_printed


# ─── Anchor-based interpolation (headings + manual anchors) ─────────────────


def _interpolate_ws_anchors(
    anchors: list[tuple[int, int]],
) -> dict[int, int]:
    """ws-space interpolation between consecutive (ws, printed) anchors.

    Uses the same monotonic-offset rule: between two anchors, `gap_size
    - offset_bump` ws pages continue the earlier offset, the remaining
    `offset_bump` pages are unnumbered.
    """
    by_ws: dict[int, int] = {}
    conflicts: set[int] = set()
    for ws, printed in anchors:
        if ws in by_ws and by_ws[ws] != printed:
            conflicts.add(ws)
            continue
        by_ws[ws] = printed
    for c in conflicts:
        by_ws.pop(c, None)

    if not by_ws:
        return {}

    sorted_ws = sorted(by_ws)
    result = dict(by_ws)  # anchors themselves

    for i in range(len(sorted_ws) - 1):
        wa, wb = sorted_ws[i], sorted_ws[i + 1]
        pa, pb = by_ws[wa], by_ws[wb]
        off_a = wa - pa
        off_b = wb - pb
        if off_b < off_a:
            continue  # non-monotonic — skip
        gap_size = wb - wa - 1
        offset_bump = off_b - off_a
        if offset_bump > gap_size:
            continue
        numbered_extra = gap_size - offset_bump
        for k in range(1, numbered_extra + 1):
            ws = wa + k
            printed = ws - off_a
            if printed >= 1 and ws not in result:
                result[ws] = printed

    return result


def _interpolate_from_anchors(
    anchors: list[tuple[int, int]],
    vol_range: tuple[int, int, int, int] | None,
) -> dict[int, int]:
    """Build leaf -> printed from a set of (leaf, printed) anchors.

    Between consecutive anchors A and B (by leaf), the offset
    (leaf - printed) can only grow. `gap_size - offset_bump` leaves
    continue A's offset; the remaining `offset_bump` leaves are
    unnumbered (convention: they sit at the gap end, just before B).
    """
    # Deduplicate and sort. If two anchors disagree on the same leaf,
    # drop both — one of them is wrong and we shouldn't guess.
    by_leaf: dict[int, int] = {}
    conflicts: set[int] = set()
    for leaf, printed in anchors:
        if leaf in by_leaf and by_leaf[leaf] != printed:
            conflicts.add(leaf)
            continue
        by_leaf[leaf] = printed
    for c in conflicts:
        by_leaf.pop(c, None)

    if not by_leaf:
        return {}

    # Bounds from VOL_RANGE
    if vol_range is not None:
        fl_bound, _, ll_bound, _ = vol_range
    else:
        fl_bound = min(by_leaf)
        ll_bound = max(by_leaf)

    sorted_leaves = sorted(by_leaf)
    result: dict[int, int] = {}

    # Every anchor itself
    for leaf, printed in by_leaf.items():
        if fl_bound <= leaf <= ll_bound and printed >= 1:
            result[leaf] = printed

    # Fill between consecutive anchors
    for i in range(len(sorted_leaves) - 1):
        la, lb = sorted_leaves[i], sorted_leaves[i + 1]
        pa, pb = by_leaf[la], by_leaf[lb]
        offset_a = la - pa
        offset_b = lb - pb
        # Monotonic: offset can only grow forward. If B's offset is
        # LESS than A's, one of them is wrong — drop the intermediate
        # gap's interpolation (leave leaves unmapped between them).
        if offset_b < offset_a:
            continue
        gap_size = lb - la - 1
        offset_bump = offset_b - offset_a
        if offset_bump > gap_size:
            # Shouldn't happen (anchor offsets are too spread apart).
            continue
        numbered_extra = gap_size - offset_bump
        for k in range(1, numbered_extra + 1):
            leaf = la + k
            printed = leaf - offset_a
            if fl_bound <= leaf <= ll_bound and printed >= 1:
                result[leaf] = printed

    return result


# ─── Combine sources ─────────────────────────────────────────────────────────


def main() -> None:
    ocr = json.loads(OCR_FILE.read_text(encoding="utf-8")) if OCR_FILE.exists() else {}
    sm = json.loads(SCAN_MAP.read_text(encoding="utf-8")) if SCAN_MAP.exists() else {}

    s = SessionLocal()
    ws_result: dict[str, dict[str, int]] = {}
    leaf_result: dict[str, dict[str, int]] = {}

    for vol in range(1, 29):
        all_ws = [
            r[0] for r in s.query(SourcePage.page_number)
            .filter(SourcePage.volume == vol)
            .order_by(SourcePage.page_number).all()
        ]
        if not all_ws:
            continue

        # 1. Primary source: headings (source of truth).
        ws_from_heading = _harvest_headings(vol, all_ws)

        # Translate heading ws→printed to leaf→printed for use as
        # anchors in the monotonic walk.
        vol_sm = sm.get(str(vol), {})
        offset = LEAF_OFFSET.get(vol, 0)
        leaf_to_ws: dict[int, int] = {}
        for ws in all_ws:
            leaf = vol_sm.get(str(ws))
            if leaf is None:
                leaf = ws + offset
            leaf_to_ws[int(leaf)] = ws
        ws_to_leaf = {v: k for k, v in leaf_to_ws.items()}

        # Build ws-space anchors (no leaf detour — keeps things clean
        # and avoids scan_map translation errors).
        #
        # Headings are truth in ws space. For ws pages without a
        # heading, interpolate between consecutive heading-having
        # neighbors using the monotonic-offset rule.
        ws_anchors: list[tuple[int, int]] = list(ws_from_heading.items())
        # Add VOL_RANGE endpoints translated into ws via scan_map
        if vol in VOL_RANGE:
            fl, fp, ll, lp = VOL_RANGE[vol]
            ws_first = leaf_to_ws.get(fl, fl - offset)
            ws_last = leaf_to_ws.get(ll, ll - offset)
            ws_anchors.append((ws_first, fp))
            ws_anchors.append((ws_last, lp))
        # Add user's manual trusted runs (translated to ws)
        for la, pa, lb, pb in TRUSTED_RUNS.get(vol, []):
            ws_anchors.append((leaf_to_ws.get(la, la - offset), pa))
            ws_anchors.append((leaf_to_ws.get(lb, lb - offset), pb))

        ws_from_interp = _interpolate_ws_anchors(ws_anchors)
        # Merge: heading values win, interpolation fills gaps
        ws_combined = {**ws_from_interp, **ws_from_heading}

        # Build leaf_from_algo for the leaf-keyed output by translating
        # ws_combined through leaf_to_ws inverse.
        leaf_from_algo: dict[int, int] = {}
        for ws, printed in ws_combined.items():
            leaf = ws_to_leaf.get(ws, ws + offset)
            leaf_from_algo[leaf] = printed

        # Translate leaf results back to ws.
        ws_from_algo: dict[int, int] = {}
        for leaf, printed in leaf_from_algo.items():
            ws = leaf_to_ws.get(leaf)
            if ws is not None:
                ws_from_algo[ws] = printed

        # Combined ws -> printed: headings win (they are truth),
        # algorithm fills ws pages without headings.
        combined_ws: dict[int, int] = {**ws_from_algo, **ws_from_heading}

        # Combined leaf -> printed: algorithm output is already based
        # on heading anchors, so this is self-consistent.
        combined_leaf: dict[int, int] = dict(leaf_from_algo)
        for ws, printed in ws_from_heading.items():
            leaf = ws_to_leaf.get(ws, ws + offset)
            combined_leaf[leaf] = printed

        ws_result[str(vol)] = {str(k): v for k, v in combined_ws.items() if v >= 1}
        leaf_result[str(vol)] = {str(k): v for k, v in combined_leaf.items() if v >= 1}

        h = len(ws_from_heading)
        a = len(ws_from_algo)
        total = len(combined_ws)
        h_cov = 100 * h // max(1, len(all_ws))
        tot_cov = 100 * total // max(1, len(all_ws))
        print(f"  Vol {vol:2d}: {total:4d}/{len(all_ws)} mapped "
              f"({tot_cov}% total; headings {h}/{h_cov}%, algo {a})")

    s.close()

    OUT_WS.write_text(json.dumps(ws_result, indent=2), encoding="utf-8")
    OUT_LEAF.write_text(json.dumps(leaf_result, indent=2), encoding="utf-8")
    total_ws = sum(len(v) for v in ws_result.values())
    total_leaf = sum(len(v) for v in leaf_result.values())
    print(f"\nWrote {total_ws} ws mappings -> {OUT_WS}")
    print(f"Wrote {total_leaf} leaf mappings -> {OUT_LEAF}")


if __name__ == "__main__":
    main()
