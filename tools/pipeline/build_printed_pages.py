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

SCAN_DIR = Path("data/derived/scans")


def _fm01_leaf(vol: int) -> int | None:
    """Find the leaf whose scan image matches ``vol{VV}_fm01.jpg``.

    fm-prefixed scan files cover only the front-matter content; the
    leaf index of fm01 varies per volume (vol 1: leaf 2, vol 24: leaf
    4, vol 20: leaf 1) because leading cover/blank leaves are skipped
    in the fm enumeration. Matching by file size is exact: the two
    files are byte-identical copies."""
    fm01 = SCAN_DIR / f"vol{vol:02d}_fm01.jpg"
    if not fm01.exists():
        return None
    target = fm01.stat().st_size
    for leaf in range(1, 25):
        p = SCAN_DIR / f"vol{vol:02d}_leaf{leaf:04d}.jpg"
        if p.exists() and p.stat().st_size == target:
            return leaf
    return None

RAW_DIR = Path("data/raw/wikisource")
OCR_FILE = Path("data/derived/ocr_page_numbers.json")
FM_FIRST_CONTENT_FILE = Path("data/derived/fm_first_content.json")
OUT_WS = Path("data/derived/printed_pages.json")
OUT_LEAF = Path("data/derived/printed_pages_leaf.json")
SCAN_MAP = Path("data/derived/scan_map.json")
OUT_SCAN_MAP = SCAN_MAP  # densified scan_map is written back in-place

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
    # SHIPBUILDING plates-and-blanks section: every anchor here is
    # a leaf-to-printed mapping visually verified against the IA
    # scans.  They constrain the monotonic-offset interpolation so
    # OCR and heading data place page numbers on the right leaves
    # rather than clustering them at gap starts.
    24: [
        (1035, 955, 1035, 955),
        (1048, 966, 1048, 966),
        (1054, 968, 1054, 968),
        (1059, 969, 1059, 969),
        (1060, 970, 1060, 970),
        (1063, 971, 1063, 971),
        (1075, 981, 1075, 981),
    ],
    26: [(354, 324, 354, 324)],
    28: [(466, 440, 466, 440)],
}


# Leaves the interpolation/OCR algorithm would label numbered but
# which are actually plates or blanks per visual verification of the
# IA scans.  Fix for the "one map" rule: any time we find the map
# labeled an unnumbered leaf with a page number, we add the leaf
# here.  Never edit the generated JSON directly (a rebuild would
# overwrite it) — always add the anchor here so the fix survives.
# Override of the first front-matter content leaf per volume when the
# auto-detection (fm_first_content + fm01-leaf match) disagrees with
# human inspection of the actual scans. Values are confirmed leaf
# numbers where "fm 1" should appear.
FIRST_FM_CONTENT_LEAF: dict[int, int] = {
    24: 7,  # leaves 5, 6 are blanks that is_blank() missed
}


UNNUMBERED_LEAVES: dict[int, list[int]] = {
    # Only leaves confirmed as unnumbered by visual inspection of
    # the IA scans. Listing a leaf here removes whatever printed
    # number the interpolation guessed for it. The remaining leaves
    # in each gap are left to the algorithm; add more here as errors
    # surface.
    # SHIPBUILDING (vol 24) confirmed unnumbered leaves:
    24: [1045, 1049, 1052, 1055, 1061, 1062],
    # Note: leaves 1056-1058 between 1054 (968) and 1059 (969) are
    # plates/blanks; the monotonic walk correctly leaves them null
    # so they don't need explicit entries here.
}


# ─── Source 1: Wikisource Page Heading extraction ────────────────────────────

_HEADING_RE = re.compile(
    r"\{\{EB1911 Page Heading\|([^|]*)\|[^|]*\|[^|]*\|([^|}]*)\}?\}?",
    re.IGNORECASE,
)

_RH_RE = re.compile(r"\{\{rh\s*\|", re.IGNORECASE)


_SPACING_TEMPLATE_RE = re.compile(
    r"\{\{(?:em|gap|nbsp|sp|hsp|thinsp)(?:\|[^}]*)?\}\}",
    re.IGNORECASE,
)


def _int_in_range(val: str) -> int | None:
    """Find the first plausible page number (1–1200) in ``val``.

    Strip spacing templates first — ``{{em|4}}`` is "4 em-spaces", not
    a page number; it sits in the outer rh cell of plates alongside
    ``Plate II.`` style labels.  Without this guard the rh parser
    treats 4 as the page number for the plate leaf."""
    val = _SPACING_TEMPLATE_RE.sub("", val)
    for m in re.finditer(r"\b(\d{1,4})\b", val):
        n = int(m.group(1))
        if 1 <= n <= 1200:
            return n
    return None


def _rh_cells(raw_text: str) -> list[str] | None:
    """Parse ``{{rh|A|B|C}}`` with brace-depth awareness.

    Unlike EB1911 Page Heading (plain-text cells), rh cells commonly
    contain nested templates like ``{{x-larger|949}}`` that a simple
    ``[^|]*`` regex would eat past.  Walk the string tracking brace
    depth and split on top-level ``|``.
    """
    m = _RH_RE.search(raw_text[:600])
    if not m:
        return None
    i = m.end()  # position right after the opening pipe of ``{{rh|``
    cells: list[str] = []
    cur: list[str] = []
    depth = 1
    while i < len(raw_text):
        if raw_text[i:i + 2] == "{{":
            depth += 1
            cur.append("{{")
            i += 2
        elif raw_text[i:i + 2] == "}}":
            depth -= 1
            if depth == 0:
                cells.append("".join(cur))
                return cells
            cur.append("}}")
            i += 2
        elif raw_text[i] == "|" and depth == 1:
            cells.append("".join(cur))
            cur = []
            i += 1
        else:
            cur.append(raw_text[i])
            i += 1
    return None


def _printed_from_rh(raw_text: str) -> int | None:
    """Extract the printed page number from ``{{rh|L|C|R}}`` by
    checking the LEFT and RIGHT cells (verso / recto — numbers
    alternate between them).  Skip the center cell, which holds the
    article subject, not the page number."""
    cells = _rh_cells(raw_text)
    if not cells or len(cells) < 3:
        return None
    for val in (cells[0], cells[-1]):
        n = _int_in_range(val)
        if n is not None:
            return n
    return None


def _printed_from_heading(raw_text: str) -> int | None:
    """Extract printed page number from any supported heading template
    (``{{EB1911 Page Heading|…}}`` primary, ``{{rh|…}}`` fallback).
    A large share of volumes use ``{{rh|…}}`` exclusively — without
    this fallback those pages fall through to OCR-anchor interpolation
    and produce wildly wrong leaf→printed mappings (seen on
    SHIPBUILDING, vol 24)."""
    if not raw_text:
        return None
    head = raw_text[:600]
    m = _HEADING_RE.search(head)
    if m:
        for val in (m.group(1), m.group(2)):
            n = _int_in_range(val)
            if n is not None:
                return n
    return _printed_from_rh(head)


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
    """Group consecutive OCR pairs with matching offset into runs.

    Includes singletons: an isolated correct OCR reading in a
    plate-heavy region is often the only clue that a given leaf is
    numbered. The monotonic-offset accept-filter downstream still
    rejects singletons whose offset contradicts the volume's running
    offset, so OCR noise doesn't leak through."""
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
            runs.append(cur)
            cur = [pairs[i]]
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
    # fm_first_content[vol] is the first-content index among fm-prefixed
    # scan files.  fm01.jpg corresponds to leaf 2 (leaf 1 is the cover),
    # so first_content_leaf = fm_first_content[vol] + 1.
    fm_first_content = (
        json.loads(FM_FIRST_CONTENT_FILE.read_text(encoding="utf-8"))
        if FM_FIRST_CONTENT_FILE.exists() else {}
    )

    s = SessionLocal()
    ws_result: dict[str, dict[str, int]] = {}
    leaf_result: dict[str, dict[str, int]] = {}
    scan_result: dict[str, dict[str, int]] = {}

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
        # Build ws→leaf directly from scan_map; fall back to offset
        # only for ws pages scan_map doesn't know about.  The previous
        # loop-based construction (``for ws in all_ws: leaf_to_ws[…] =
        # ws``) had fallback leaf numbers collide with scan_map'd leaves
        # from other ws pages, which overwrote correct mappings and
        # caused heading values to be written to wrong leaves
        # (SHIPBUILDING: ws 1022→leaf 1032 page 954 got clobbered by
        # ws 1028→leaf 1039's page 959 spilling over to leaf 1032 via a
        # fallback-inverse lookup).
        # Build ws↔leaf mappings strictly from scan_map.  The previous
        # ``ws + offset`` fallback assumed a linear ws→leaf relationship,
        # which breaks wherever blank/plate leaves are interspersed —
        # the fallback lands on blank leaves and writes bogus page
        # numbers there.  TRUSTED_RUNS is the mechanism for injecting
        # ground-truth anchors that scan_map doesn't know about.
        ws_to_leaf: dict[int, int] = {}
        for ws_s, leaf in vol_sm.items():
            ws_to_leaf[int(ws_s)] = int(leaf)
        leaf_to_ws: dict[int, int] = {leaf: ws for ws, leaf in ws_to_leaf.items()}

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

        # Leaf-space OCR interpolation.  Handles plate-heavy regions
        # that ws-space interpolation + scan_map translation can't
        # resolve: e.g. SHIPBUILDING p. 973 lives at leaf 1067 (per
        # IA OCR), but scan_map has no entry for its ws page, so the
        # ws-space path leaves it unplaced.  _leaf_algorithm runs a
        # monotonic-offset walk in leaf space using OCR-recognized
        # page numbers anchored by VOL_RANGE and TRUSTED_RUNS.
        leaf_from_ocr = _leaf_algorithm(
            ocr.get(str(vol), {}),
            VOL_RANGE.get(vol),
            TRUSTED_RUNS.get(vol, []),
        )

        # Translate ws_combined through scan_map for any additional
        # heading-derived leaf entries the OCR walk missed.  Headings
        # are the ground truth for numbered pages that actually carry
        # a running header number.
        leaf_from_algo: dict[int, int] = dict(leaf_from_ocr)
        for ws, printed in ws_combined.items():
            leaf = ws_to_leaf.get(ws)
            if leaf is None:
                continue
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

        # First-article pin in ws space: the first article page never
        # prints its running-header number (it's implicit), so heading
        # extraction always returns None for it. Without this pin the
        # export's walk-back fallback returns the ws page index as the
        # "printed" value, which cascades through article page_start /
        # page_end and makes every subsequent page number read wrong.
        if vol in VOL_RANGE:
            fl = VOL_RANGE[vol][0]
            fp = VOL_RANGE[vol][1]
            first_article_ws = leaf_to_ws.get(fl, fl - offset)
            combined_ws.setdefault(first_article_ws, fp)

        # Combined leaf -> printed: algorithm output is already based
        # on heading anchors, so this is self-consistent.
        combined_leaf: dict[int, int] = dict(leaf_from_algo)
        for ws, printed in ws_from_heading.items():
            leaf = ws_to_leaf.get(ws)
            if leaf is None:
                continue  # no scan_map entry — don't fall back
            combined_leaf[leaf] = printed

        # Apply TRUSTED_RUNS as direct leaf→printed overrides.  These
        # are user-confirmed ground-truth anchors: they win over any
        # derived value.  Useful when scan_map has no entry for the
        # leaf (so nothing reaps it via ws-space) or has a wrong
        # entry (so a bogus page number landed there).
        for la, pa, lb, pb in TRUSTED_RUNS.get(vol, []):
            for leaf in range(la, lb + 1):
                combined_leaf[leaf] = pa + (leaf - la)

        # Remove confirmed-unnumbered leaves. These are the authoritative
        # "leaf is plate/blank, don't guess a printed number" overrides.
        for leaf in UNNUMBERED_LEAVES.get(vol, []):
            combined_leaf.pop(leaf, None)

        # Densify scan_map (ws→leaf) by cross-referencing printed
        # numbers.  For any ws whose printed page is known and whose
        # printed value appears in combined_leaf, derive ws→leaf via
        # the common printed number.  This fills the holes scan_map
        # has at plates/blanks that no Css-image-crop reference
        # covered — without it the viewer's `ws + LEAF_OFFSET` fallback
        # lands on wildly wrong leaves inside articles with heavy
        # plate clusters (SHIPBUILDING grew from offset 10 to 18
        # across its plate section).
        printed_to_leaf: dict[int, int] = {}
        for leaf, printed in combined_leaf.items():
            # Keep the smallest leaf for a given printed number so
            # recto/verso duplicates (shouldn't happen, but safe) don't
            # produce ambiguous reverse lookups.
            if printed not in printed_to_leaf or leaf < printed_to_leaf[printed]:
                printed_to_leaf[printed] = leaf
        ws_to_leaf_dense: dict[int, int] = dict(ws_to_leaf)
        for ws, printed in combined_ws.items():
            if ws in ws_to_leaf_dense:
                continue
            leaf = printed_to_leaf.get(printed)
            if leaf is not None:
                ws_to_leaf_dense[ws] = leaf

        ws_result[str(vol)] = {str(k): v for k, v in combined_ws.items() if v >= 1}

        # Build a DENSE per-leaf map from leaf 1 through the volume's
        # last_leaf. Every leaf gets an entry:
        #   int  — printed page number
        #   str  — "fm N" for front matter
        #   None — unnumbered (plate / blank / unknown)
        # This is the "one map" the scan viewer consults: a leaf
        # either has a label or explicitly doesn't. Missing keys would
        # be ambiguous; null is explicit.
        leaf_entries: dict[int, int | str | None] = {}
        if vol in VOL_RANGE:
            first_article_leaf, first_printed, last_leaf, _ = VOL_RANGE[vol]
        else:
            first_article_leaf, first_printed = 1, 1
            last_leaf = max(
                [*combined_leaf.keys(), *ws_to_leaf_dense.values(), 1]
            )
        # The first article page never prints a running-header page
        # number — the number is implicit. Pin it to first_printed
        # so the scan viewer labels it correctly without requiring a
        # per-volume TRUSTED_RUN for each.
        combined_leaf.setdefault(first_article_leaf, first_printed)
        # Front-matter labeling. fm_first_content.json gives the
        # fm-file index of the first non-blank fm scan. Match fm01.jpg
        # to a leaf by file size to get the fm-to-leaf offset for this
        # volume, then translate. Leaves before first_content_leaf are
        # cover / leading blanks (null); from there the non-blank fm
        # pages get serial "fm N" labels up to the first article leaf.
        fm_idx = fm_first_content.get(str(vol))
        fm01_leaf = _fm01_leaf(vol)
        if vol in FIRST_FM_CONTENT_LEAF:
            first_content_leaf = FIRST_FM_CONTENT_LEAF[vol]
        elif fm_idx is not None and fm01_leaf is not None:
            first_content_leaf = fm01_leaf + (fm_idx - 1)
        else:
            first_content_leaf = 1
        for leaf in range(1, last_leaf + 1):
            if leaf < first_article_leaf:
                if leaf < first_content_leaf:
                    leaf_entries[leaf] = None
                else:
                    leaf_entries[leaf] = f"fm {leaf - first_content_leaf + 1}"
            else:
                v = combined_leaf.get(leaf)
                leaf_entries[leaf] = v if (v is not None and v >= 1) else None
        leaf_result[str(vol)] = {str(k): v for k, v in sorted(leaf_entries.items())}
        scan_result[str(vol)] = {str(k): v for k, v in sorted(ws_to_leaf_dense.items())}

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
    OUT_SCAN_MAP.write_text(json.dumps(scan_result, indent=2), encoding="utf-8")
    total_ws = sum(len(v) for v in ws_result.values())
    total_leaf = sum(len(v) for v in leaf_result.values())
    total_scan = sum(len(v) for v in scan_result.values())
    print(f"\nWrote {total_ws} ws mappings -> {OUT_WS}")
    print(f"Wrote {total_leaf} leaf mappings -> {OUT_LEAF}")
    print(f"Wrote {total_scan} ws->leaf mappings -> {OUT_SCAN_MAP}")


if __name__ == "__main__":
    main()
