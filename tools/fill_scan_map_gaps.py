"""Fill gaps in data/derived/scan_map.json using neighbor interpolation.

For each consecutive pair of explicit ws→leaf entries (ws_a, leaf_a)
and (ws_b, leaf_b) in scan_map, if leaf_b - leaf_a == ws_b - ws_a
(same offset, i.e. no plate-insert between them), fill every missing
ws between them with leaf_a + (ws - ws_a).

Offset-change gaps (where a plate or unfoliated insert sits) are
left unfilled — scan viewers fall back to LEAF_OFFSET there, which
may still be wrong, but the ambiguity is genuine.
"""
import json
from pathlib import Path

PATH = Path("data/derived/scan_map.json")


def fill() -> None:
    sm = json.loads(PATH.read_text(encoding="utf-8"))
    total_added = 0
    for vol in sorted([int(k) for k in sm.keys()]):
        v = sm[str(vol)]
        entries = sorted([(int(k), v[k]) for k in v])
        added_vol = 0
        for i in range(len(entries) - 1):
            ws_a, leaf_a = entries[i]
            ws_b, leaf_b = entries[i + 1]
            offset = leaf_a - ws_a
            if leaf_b - ws_b != offset:
                continue  # offset change — unsafe to interpolate
            # Fill every missing ws strictly between ws_a and ws_b
            for ws in range(ws_a + 1, ws_b):
                if str(ws) not in v:
                    v[str(ws)] = ws + offset
                    added_vol += 1
        total_added += added_vol
        print(f"  vol {vol}: filled {added_vol} gap entries")
    PATH.write_text(json.dumps(sm, indent=2), encoding="utf-8")
    print(f"\nTotal gap entries filled: {total_added}")


if __name__ == "__main__":
    fill()
