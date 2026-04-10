"""Build printed page number map from OCR consistent runs.

Each consistent run (2+ consecutive pages with sequential OCR'd numbers)
is a local anchor. For any page, use the nearest run's offset to derive
the printed page number. This avoids the plate-counting problem entirely.

Input: data/derived/ocr_page_numbers.json
Output: data/derived/printed_pages.json

Usage:
    python tools/build_printed_pages.py
"""
import json
from pathlib import Path

from britannica.db.models import SourcePage
from britannica.db.session import SessionLocal

OCR_FILE = Path("data/derived/ocr_page_numbers.json")
OUT = Path("data/derived/printed_pages.json")

LEAF_OFFSET = {
    1: 7, 2: 7, 3: 9, 4: 9, 5: 12, 6: 12, 7: 7, 8: 7,
    9: 9, 10: 10, 11: 8, 12: 7, 13: 7, 14: 6, 15: 17, 16: 6,
    17: 9, 18: 6, 19: 7, 20: -14, 21: 6, 22: 6, 23: 7, 24: 4,
    25: 8, 26: 4, 27: 6, 28: 5, 29: 6,
}

# Manual anchors for volumes where OCR runs don't cover the start.
# Verified from scan inspection: {vol: (ws_page, printed_page)}
MANUAL_ANCHORS = {
    5: (14, 6),
    18: (17, 3),
}


def main():
    ocr = json.loads(OCR_FILE.read_text(encoding="utf-8"))
    sm_path = Path("data/derived/scan_map.json")
    sm = json.loads(sm_path.read_text(encoding="utf-8")) if sm_path.exists() else {}

    s = SessionLocal()
    result = {}

    for vol in range(1, 29):
        vk = str(vol)
        vol_ocr = ocr.get(vk, {})
        vol_sm = sm.get(vk, {})
        vol_offset = LEAF_OFFSET.get(vol, 0)

        all_ws = [r[0] for r in s.query(SourcePage.page_number).filter(
            SourcePage.volume == vol).order_by(SourcePage.page_number).all()]

        # Build leaf -> ws
        leaf_to_ws = {}
        for ws in all_ws:
            leaf = vol_sm.get(str(ws))
            if leaf is None:
                leaf = ws + vol_offset
            leaf_to_ws[leaf] = ws

        # Convert OCR to (ws, printed)
        ws_printed = []
        for leaf_str, printed in vol_ocr.items():
            ws = leaf_to_ws.get(int(leaf_str))
            if ws is not None:
                ws_printed.append((ws, printed))
        ws_printed.sort()

        # Find consistent runs (min length 2)
        runs = []
        if ws_printed:
            cur = [ws_printed[0]]
            for i in range(1, len(ws_printed)):
                ws, pr = ws_printed[i]
                pw, pp = ws_printed[i - 1]
                if pr == pp + (ws - pw):
                    cur.append(ws_printed[i])
                else:
                    if len(cur) >= 2:
                        runs.append(cur)
                    cur = [ws_printed[i]]
            if len(cur) >= 2:
                runs.append(cur)

        # Inject manual anchors as single-point runs
        if vol in MANUAL_ANCHORS:
            ws_a, pr_a = MANUAL_ANCHORS[vol]
            runs.append([(ws_a, pr_a)])

        # Build run spans: (start_ws, end_ws, offset, run_length)
        # offset = ws - printed, so printed = ws - offset
        run_spans = []
        for run in runs:
            start_ws = run[0][0]
            end_ws = run[-1][0]
            offset = run[0][0] - run[0][1]
            run_spans.append((start_ws, end_ws, offset, len(run)))
        run_spans.sort()

        # For each ws page, find the closest run edge on each side
        # and use that run's offset.  If inside a run, use it directly.
        vol_map = {}
        if run_spans:
            for ws in all_ws:
                # Check if inside a run
                inside = None
                before = None  # closest run ending at or before ws
                after = None   # closest run starting at or after ws
                for start, end, off, rlen in run_spans:
                    if start <= ws <= end:
                        inside = off
                        break
                    if end <= ws:
                        if before is None or end > before[0]:
                            before = (end, off, rlen)
                    if start >= ws:
                        if after is None or start < after[0]:
                            after = (start, off, rlen)

                if inside is not None:
                    best_off = inside
                elif before and after:
                    # Use the closer edge
                    dist_before = ws - before[0]
                    dist_after = after[0] - ws
                    if dist_before <= dist_after:
                        best_off = before[1]
                    else:
                        best_off = after[1]
                elif before:
                    best_off = before[1]
                elif after:
                    best_off = after[1]
                else:
                    continue

                printed = ws - best_off
                if printed > 0:
                    vol_map[str(ws)] = printed

        result[vk] = vol_map

        max_gap = 0
        sorted_runs = sorted(runs, key=lambda r: r[0][0])
        for i in range(1, len(sorted_runs)):
            gap = sorted_runs[i][0][0] - sorted_runs[i - 1][-1][0]
            max_gap = max(max_gap, gap)

        print(f"  Vol {vol:2d}: {len(runs)} runs, max_gap={max_gap}, "
              f"{len(vol_map)} pages mapped")

    s.close()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nWrote {sum(len(v) for v in result.values())} mappings to {OUT}")


if __name__ == "__main__":
    main()
