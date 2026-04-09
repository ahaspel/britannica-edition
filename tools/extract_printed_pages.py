"""Extract printed page numbers from wikitext page headings.

Parses {{EB1911 Page Heading|...|N}} and {{rh|...|N}} templates to get
the printed page number for each Wikisource page.  Interpolates gaps
between known values.

Output: data/derived/printed_pages.json
Format: {"vol": {"ws_page": printed_page, ...}, ...}

Usage:
    python tools/extract_printed_pages.py
"""
import json
import re
from pathlib import Path

from sqlalchemy import text as sqlt

from britannica.db.session import SessionLocal

OUT = Path("data/derived/printed_pages.json")


def _extract_printed_page(txt: str) -> int | None:
    """Extract printed page number from wikitext heading templates."""
    if not txt:
        return None
    # {{EB1911 Page Heading|...|N}} — N is always the last field
    m = re.search(r'\{\{EB1911 Page Heading\|[^}]*\|(\d+)\s*\}\}', txt[:500])
    if m:
        return int(m.group(1))
    # {{rh|...|{{x-larger|N}}}} or {{rh|...|N}}
    # The page number is in the first or last positional arg, often
    # wrapped in {{x-larger|...}}.  Try both ends.
    rh = re.search(r'\{\{rh\|(.+)', txt[:500])
    if rh:
        content = rh.group(1)
        # Find all bare numbers or numbers inside {{x-larger|N}}
        nums = re.findall(r'(?:\{\{x-larger\|)?\s*(\d{1,4})\s*(?:\}\})?', content)
        # Filter to plausible page numbers (1-2000)
        nums = [int(n) for n in nums if 1 <= int(n) <= 2000]
        if nums:
            # Page number is typically the first or last number
            # If there's a number at the start and end, prefer the one
            # that looks like a page number (even = left page, odd = right)
            return nums[0] if len(nums) == 1 else nums[-1]
    return None


def main():
    s = SessionLocal()

    result = {}
    total_direct = 0
    total_interpolated = 0

    for vol in range(1, 29):
        rows = s.execute(sqlt(
            "SELECT page_number, coalesce(wikitext, raw_text) as txt "
            "FROM source_pages WHERE volume = :v ORDER BY page_number"
        ), {"v": vol}).fetchall()

        # Extract known values
        known = {}  # ws_page -> printed_page
        for pg, txt in rows:
            printed = _extract_printed_page(txt)
            if printed is not None:
                known[pg] = printed

        # Validate: remove outliers where the offset differs wildly
        # from neighbors.  Build a list of (ws, printed, offset) and
        # reject points whose offset disagrees with both neighbors.
        sorted_known = sorted(known.items())
        clean = {}
        for i, (ws, pr) in enumerate(sorted_known):
            off = ws - pr
            # Check neighbors
            neighbor_offsets = []
            for j in range(max(0, i - 3), min(len(sorted_known), i + 4)):
                if j != i:
                    nws, npr = sorted_known[j]
                    neighbor_offsets.append(nws - npr)
            if neighbor_offsets:
                # Accept if within 2 of any neighbor's offset
                if any(abs(off - noff) <= 2 for noff in neighbor_offsets):
                    clean[ws] = pr
            else:
                clean[ws] = pr

        # Interpolate gaps: for each ws page, find nearest known values
        # on either side and linearly interpolate
        all_ws = sorted(r[0] for r in rows)
        vol_map = {}
        clean_list = sorted(clean.items())

        if clean_list:
            for pg in all_ws:
                if pg in clean:
                    vol_map[str(pg)] = clean[pg]
                    total_direct += 1
                else:
                    # Find bracketing known values
                    before = None
                    after = None
                    for ws, pr in clean_list:
                        if ws <= pg:
                            before = (ws, pr)
                        if ws >= pg and after is None:
                            after = (ws, pr)
                    if before and after and before != after:
                        # Linear interpolation
                        frac = (pg - before[0]) / (after[0] - before[0])
                        printed = round(before[1] + frac * (after[1] - before[1]))
                        if printed > 0:
                            vol_map[str(pg)] = printed
                            total_interpolated += 1
                    elif before:
                        # Extrapolate from last known
                        off = before[0] - before[1]
                        printed = pg - off
                        if printed > 0:
                            vol_map[str(pg)] = printed
                            total_interpolated += 1
                    elif after:
                        # Extrapolate from first known
                        off = after[0] - after[1]
                        printed = pg - off
                        if printed > 0:
                            vol_map[str(pg)] = printed
                            total_interpolated += 1

        result[str(vol)] = vol_map
        direct = sum(1 for p in all_ws if p in clean)
        interp = len(vol_map) - direct
        print(f"  Vol {vol:2d}: {len(known)} extracted, {len(clean)} validated, "
              f"{interp} interpolated, {len(vol_map)} total")

    s.close()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nWrote {total_direct + total_interpolated} mappings "
          f"({total_direct} direct, {total_interpolated} interpolated) to {OUT}")


if __name__ == "__main__":
    main()
