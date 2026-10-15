"""The proofreading desk's data for EB1911, through wikikit.scan.desk.

The pages here are the ones Wikisource left as raw OCR, whose whole reading of
ours waits in data/supplied until a person has proofread it (the door:
`supplied_replaces_text_at=3`, user 2026-10-15).  Each strip is a column of
the page beside our reading of it.

    uv run python tools/desk.py serve [PORT]
        -> the desk at http://localhost:PORT/desk (default 8020), on the site's
           own server: each page's strips beside the page rendered as it would
           enter, by the site's viewer.  Saving writes into data/supplied; a
           page whose strips are all checked is proofread and enters at the
           next rebuild.  Never save while a rebuild runs.
    uv run python tools/desk.py bundle [VOL:PAGE ...]
        -> data/derived/desk/: desk.json, strip images, desk_render.js, and
           seed/<strip id>.json, one document per text strip for the desk's
           store.  No pages named: every supplied page the door holds whose
           reading is complete (level 1) — the queue.  PAGE is the PRINTED page.
    uv run python tools/desk.py apply DIR
        DIR holds the desk's saved strips, one <strip id>.json each
        (as exported from its store): readings corrected, checks recorded,
        pages reassembled — a page fully checked is level 3 and enters.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from eb1911.scans import _printed, page_scan
from wikikit.scan import desk, supplied
from wikikit.source_pages import SUPPLIED_DIR, fetched_text, prefer

sys.stdout.reconfigure(encoding="utf-8")
OUT = Path("data/derived/desk")
PRINTED = _printed("printed_pages.json")


def label(vol: int, ws: int) -> str:
    return f"Vol. {vol}, p. {PRINTED[str(vol)][str(ws)]}"


def ws_for(vol: int, printed: int) -> int:
    return next(int(ws) for ws, p in PRINTED[str(vol)].items() if p == printed)


def queue(done: bool = False) -> list[tuple[int, int]]:
    """Every supplied page the door holds whose reading is complete: what
    waits to be proofread.  `done`: with the pages proofread since, so the
    desk keeps a page in view once it is finished."""
    keys = []
    for f in sorted(Path(SUPPLIED_DIR).glob("vol_*/*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        v, p = d["volume"], d["page_number"]
        ws = fetched_text(v, p)
        lv = supplied.level(d)
        held = prefer({"raw_text": ws} if ws is not None else None, d) is not d
        if (lv == 1 and held) or (done and lv >= 3):
            keys.append((v, p))
    return keys


def bundle(keys: list[tuple[int, int]]) -> None:
    path = desk.bundle(keys, {k: page_scan(*k) for k in keys}, OUT, label=label)
    shutil.copyfile(desk.DESK_RENDER_JS, OUT / "desk_render.js")
    seed = OUT / "seed"
    shutil.rmtree(seed, ignore_errors=True)
    seed.mkdir()
    data = json.loads(path.read_text(encoding="utf-8"))
    n = 0
    for pg in data["pages"]:
        for s in pg["strips"]:
            if s["kind"] == "figure":
                continue
            (seed / f"{s['id']}.json").write_text(json.dumps({
                "page": pg["id"], "name": s["name"], "text": s["text"], "model_text": s["text"],
                "status": "checked" if s["checked"] else "unchecked"},
                ensure_ascii=False), encoding="utf-8")
            n += 1
    print(f"{path}: {len(data['pages'])} pages, {n} text strips to seed")


def apply(src: Path) -> None:
    rows = {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in sorted(src.glob("*.json"))}
    for line in desk.apply(rows):
        print(line)


def main() -> int:
    if len(sys.argv) in (2, 3) and sys.argv[1] == "serve":
        import subprocess
        from wikikit.scan import desk_serve
        who = subprocess.run(["git", "config", "user.name"], capture_output=True, text=True).stdout.strip()
        desk_serve.serve_desk(lambda: queue(done=True), label, int(sys.argv[2]) if len(sys.argv) == 3 else 8020, who or "proofreader")
    elif len(sys.argv) >= 2 and sys.argv[1] == "bundle":
        keys = [(int(v), ws_for(int(v), int(p))) for v, p in (a.split(":") for a in sys.argv[2:])]
        bundle(keys or queue())
    elif len(sys.argv) == 3 and sys.argv[1] == "apply":
        apply(Path(sys.argv[2]))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
