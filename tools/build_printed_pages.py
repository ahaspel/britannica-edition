"""Build printed page number map from OCR.

Algorithm (per volume, in LEAF space — i.e. physical scan page index):

1. Establish first and last offsets for the article pages manually
   (VOL_RANGE). These bound the valid offset range: every OCR reading
   whose implied offset (leaf - printed) falls outside this range is
   garbage and gets discarded.

2. Build OCR runs: groups of 2+ consecutive leaves with sequential
   printed numbers. These are the trustworthy OCR signal.

3. Forward monotonic walk. Offsets can only grow as you move through
   the volume: every unnumbered page (blank / plate / map) bumps the
   offset by 1, and numbered pages don't change it. So walking runs
   in leaf order, a run whose offset is LESS than the running offset
   is garbage.

4. User-provided TRUSTED_RUNS inject ground truth — they're never
   filtered and they override any OCR that falls inside their leaf
   range.

5. Leaves falling inside an accepted run get a printed number; leaves
   in gaps between accepted runs are unnumbered (that's what causes
   the offset to bump).

6. Convert leaf -> ws via scan_map for the final ws -> printed output.

Input:  data/derived/ocr_page_numbers.json  (leaf_str -> printed_int)
Output: data/derived/printed_pages.json     (ws_str   -> printed_int)

Usage:
    python tools/build_printed_pages.py
"""
import json
from pathlib import Path

from britannica.db.models import SourcePage
from britannica.db.session import SessionLocal

OCR_FILE = Path("data/derived/ocr_page_numbers.json")
OUT = Path("data/derived/printed_pages.json")

# Default ws -> leaf conversion when scan_map has no entry: leaf = ws + offset.
LEAF_OFFSET = {
    1: 7, 2: 7, 3: 9, 4: 9, 5: 12, 6: 12, 7: 7, 8: 7,
    9: 9, 10: 10, 11: 8, 12: 7, 13: 7, 14: 6, 15: 17, 16: 6,
    17: 9, 18: 6, 19: 7, 20: 0, 21: 6, 22: 6, 23: 7, 24: 4,
    25: 8, 26: 4, 27: 6, 28: 5, 29: 6,
}

# Manual first/last anchors per volume (LEAF space).
# Format: {vol: (first_leaf, first_printed, last_leaf, last_printed)}
# - first_leaf / first_printed: the first article page.
# - last_leaf / last_printed: the final article page.
# Derived offsets:
#   off_min = first_leaf - first_printed
#   off_max = last_leaf  - last_printed
# Every accepted OCR offset must satisfy off_min <= offset <= off_max.
VOL_RANGE: dict[int, tuple[int, int, int, int]] = {
    1: (39, 1, 1044, 976),   # offsets [38, 68]
    2: (19, 1, 1048, 976),   # offsets [18, 72]
    3: (21, 1, 1026, 992),   # offsets [20, 34]
    4: (23, 1, 1048, 1004),  # offsets [22, 44]
    5: (21, 1, 1024, 964),   # offsets [20, 60]
    6: (23, 1, 1030, 992),   # offsets [22, 38]
    7: (21, 1, 1016, 984),   # offsets [20, 32]
    8: (21, 1, 1034, 1000),  # offsets [20, 34]
    9: (21, 1, 1020, 960),   # offsets [20, 60]
    10: (23, 1, 984, 944),   # offsets [22, 40]
    11: (21, 1, 982, 944),   # offsets [20, 38]
    12: (21, 1, 994, 960),   # offsets [20, 34]
    13: (21, 1, 998, 960),   # offsets [20, 38]
    14: (19, 1, 980, 920),   # offsets [18, 60]
    15: (21, 1, 1030, 960),  # offsets [20, 70]
    16: (21, 1, 1024, 992),  # offsets [20, 32]
    17: (21, 1, 1058, 1020), # offsets [20, 38]
    18: (19, 1, 1018, 968),  # offsets [18, 50]
    19: (21, 1, 1062, 996),  # offsets [20, 66]
    20: (19, 1, 1044, 980),  # offsets [18, 64]
    21: (21, 1, 1034, 984),  # offsets [20, 50]
    22: (21, 1, 1002, 976),  # offsets [20, 26]
    23: (21, 1, 1088, 1024), # offsets [20, 64]
    24: (19, 1, 1118, 1024), # offsets [18, 94]
    25: (21, 1, 1112, 1064), # offsets [20, 48]
    26: (21, 1, 1118, 1064), # offsets [20, 54]
    27: (21, 1, 1110, 1064), # offsets [20, 46]
    28: (21, 1, 1106, 1064), # offsets [20, 42]
}

# User-verified ground-truth runs (LEAF space).
# Format: {vol: [(leaf_a, printed_a, leaf_b, printed_b), ...]}
# Each tuple is a run with constant offset from leaf_a to leaf_b.
# These override OCR readings in their leaf range and are never filtered.
TRUSTED_RUNS: dict[int, list[tuple[int, int, int, int]]] = {
    8: [
        (207, 183, 207, 183),   # offset 24 (caps earlier false-high OCR)
    ],
    10: [
        (637, 603, 637, 603),   # offset 34
    ],
    14: [
        (303, 281, 303, 281),   # offset 22
    ],
    15: [
        (596, 550, 596, 550),   # offset 46
    ],
    18: [
        (44, 20, 44, 20),       # offset 24 (splits gap 19-69)
        (333, 305, 333, 305),   # offset 28
        (373, 345, 373, 345),   # offset 28 (4 plates cluster after here)
    ],
    19: [
        (538, 504, 538, 504),   # offset 34 (splits gap 516-561)
        (800, 752, 800, 752),   # offset 48 (4 plates cluster after here)
    ],
    23: [
        (46, 26, 46, 26),       # offset 20 (4 plates cluster after here)
        (370, 346, 370, 346),   # offset 24
        (425, 401, 425, 401),   # offset 24 (10 plates cluster after here)
    ],
    26: [
        (354, 324, 354, 324),   # offset 30
    ],
    28: [
        (466, 440, 466, 440),   # offset 26 (caps earlier false-high OCR)
    ],
    3: [
        (21, 1, 24, 4),       # offset 20
        (29, 5, 128, 104),    # offset 24
    ],
    20: [
        (19, 1, 44, 26),      # offset 18
        (48, 27, 79, 58),     # offset 21
        (82, 59, 137, 114),   # offset 23
        (140, 115, 219, 194), # offset 25
        (517, 471, 517, 471), # offset 46
        (540, 492, 540, 492), # offset 48 (splits big plate gap 494-586)
        (824, 770, 824, 770), # offset 54 (4 plates cluster after here)
        (858, 800, 858, 800), # offset 58 (splits gap 790-926)
        (980, 920, 980, 920), # offset 60
        (998, 934, 998, 934), # offset 64 (splits gap 963-1033)
    ],
}


def _build_ocr_runs(pairs: list[tuple[int, int]]) -> list[list[tuple[int, int]]]:
    """Group consecutive (leaf, printed) pairs with sequential printed
    numbers into runs of length >= 2."""
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


def _build_volume_map(
    vol_ocr: dict[str, int],
    vol_range: tuple[int, int, int, int] | None,
    trusted: list[tuple[int, int, int, int]],
) -> tuple[dict[int, int], int, int]:
    """Return leaf -> printed map, plus stats (n_runs, max_gap)."""
    # Offset bounds
    if vol_range is not None:
        first_leaf, first_printed, last_leaf, last_printed = vol_range
        off_min = first_leaf - first_printed
        off_max = last_leaf - last_printed
    else:
        first_leaf, first_printed, last_leaf, last_printed = 0, 0, 0, 0
        off_min, off_max = 0, 10_000  # unbounded (no anchor provided)

    # Trusted leaf ranges — OCR inside these is discarded
    trusted_ranges = [(r[0], r[2]) for r in trusted]

    def in_trusted(leaf: int) -> bool:
        return any(a <= leaf <= b for a, b in trusted_ranges)

    # Collect OCR pairs with valid offsets, outside trusted ranges
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

    # Build OCR runs
    ocr_runs = _build_ocr_runs(ocr_pairs)

    # Trusted runs become [(leaf_a, pr_a), (leaf_b, pr_b)] form
    trusted_run_list = [[(la, pa), (lb, pb)] for la, pa, lb, pb in trusted]

    # If VOL_RANGE is provided, inject anchor runs at the very start and
    # end of the article span — unless a trusted run already covers those
    # endpoints. These single-point runs guarantee coverage at the
    # extremes.
    if vol_range is not None:
        has_first = any(r[0][0] == first_leaf for r in trusted_run_list)
        has_last = any(r[-1][0] == last_leaf for r in trusted_run_list)
        if not has_first:
            trusted_run_list.append([(first_leaf, first_printed)])
        if not has_last:
            trusted_run_list.append([(last_leaf, last_printed)])

    # Merge and sort
    all_runs = ocr_runs + trusted_run_list
    all_runs.sort(key=lambda r: r[0][0])

    # Build "upper cap" at each leaf from trusted anchors: since offset
    # is monotonic, offset at any leaf L can't exceed the offset of any
    # trusted anchor at a leaf >= L. This bounds OCR inflation errors.
    trusted_points: list[tuple[int, int]] = []
    for run in trusted_run_list:
        for leaf, printed in [(run[0][0], run[0][1]), (run[-1][0], run[-1][1])]:
            trusted_points.append((leaf, leaf - printed))
    trusted_points.sort()

    def _cap_at(leaf: int) -> int:
        # Minimum offset among trusted anchors at leaves >= leaf
        cap = off_max
        for tl, to in trusted_points:
            if tl >= leaf and to < cap:
                cap = to
        return cap

    # Forward monotonic walk — offset can only grow, never exceeds the
    # cap implied by later trusted anchors.
    accepted: list[list[tuple[int, int]]] = []
    running = off_min
    for run in all_runs:
        offset = run[0][0] - run[0][1]
        if offset < running:
            continue  # can't go down — discard
        if offset > _cap_at(run[0][0]):
            continue  # would block reaching a later trusted anchor
        accepted.append(run)
        if offset > running:
            running = offset

    # Hard bounds: only leaves in [first_leaf, last_leaf] are article
    # pages. Anything before is front matter, anything after is
    # back matter / blanks / binding — discard.
    if vol_range is not None:
        fl_bound, ll_bound = first_leaf, last_leaf
    else:
        fl_bound, ll_bound = 0, 10_000

    def _in_bounds(leaf: int) -> bool:
        return fl_bound <= leaf <= ll_bound

    # Expand each accepted run into leaf -> printed
    leaf_to_printed: dict[int, int] = {}
    for run in accepted:
        leaf_start, printed_start = run[0]
        leaf_end, _ = run[-1]
        for leaf in range(leaf_start, leaf_end + 1):
            if _in_bounds(leaf):
                leaf_to_printed[leaf] = printed_start + (leaf - leaf_start)

    # Extend each run forward into its gap. In the gap between runs A
    # and B (offset_bump = offset_B - offset_A, gap_size = leaves in
    # gap), exactly offset_bump leaves are unnumbered and the remaining
    # gap_size - offset_bump leaves are numbered continuations of run A.
    # Convention: numbered leaves come first in the gap (extending run A),
    # unnumbered leaves come last (immediately before run B). This
    # matches the common physical layout where plates appear at the end
    # of a signature, just before the next article starts.
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

    # Stats
    max_gap = 0
    for i in range(1, len(accepted)):
        gap = accepted[i][0][0] - accepted[i - 1][-1][0]
        if gap > max_gap:
            max_gap = gap

    return leaf_to_printed, len(accepted), max_gap


def main() -> None:
    ocr = json.loads(OCR_FILE.read_text(encoding="utf-8"))
    sm_path = Path("data/derived/scan_map.json")
    sm = json.loads(sm_path.read_text(encoding="utf-8")) if sm_path.exists() else {}

    s = SessionLocal()
    result: dict[str, dict[str, int]] = {}

    for vol in range(1, 29):
        vk = str(vol)
        vol_ocr = ocr.get(vk, {})
        vol_sm = sm.get(vk, {})
        vol_offset = LEAF_OFFSET.get(vol, 0)

        all_ws = [
            r[0] for r in s.query(SourcePage.page_number)
            .filter(SourcePage.volume == vol)
            .order_by(SourcePage.page_number).all()
        ]

        # leaf -> ws, using scan_map where available
        leaf_to_ws: dict[int, int] = {}
        for ws in all_ws:
            leaf = vol_sm.get(str(ws))
            if leaf is None:
                leaf = ws + vol_offset
            leaf_to_ws[leaf] = ws

        leaf_to_printed, n_runs, max_gap = _build_volume_map(
            vol_ocr,
            VOL_RANGE.get(vol),
            TRUSTED_RUNS.get(vol, []),
        )

        # leaf -> printed becomes ws -> printed
        vol_map: dict[str, int] = {}
        for leaf, printed in leaf_to_printed.items():
            ws = leaf_to_ws.get(leaf)
            if ws is not None and printed >= 1:
                vol_map[str(ws)] = printed

        result[vk] = vol_map
        bound_note = ""
        if vol in VOL_RANGE:
            fl, fp, ll, lp = VOL_RANGE[vol]
            bound_note = f" bounds=[{fl - fp},{ll - lp}]"
        print(f"  Vol {vol:2d}: {n_runs} runs, max_gap={max_gap}, "
              f"{len(vol_map)} pages mapped{bound_note}")

    s.close()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    total = sum(len(v) for v in result.values())
    print(f"\nWrote {total} mappings to {OUT}")


if __name__ == "__main__":
    main()
