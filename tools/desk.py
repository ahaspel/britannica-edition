"""The proofreading desk's data for EB1911, through wikikit.scan.desk.

The pages here are those whose Wikisource text is lousy — first the ones it
left as raw OCR — whose whole reading of ours waits in data/supplied until a
person has proofread it (the door: `supplied_replaces_text_at=3`, user
2026-10-15), proofread on Wikisource or not ("if we encounter any other lousy
pages, proofread or not, we can simply fix them here": `add`, recording why).
Each page is proofread whole: its scan beside its text, one text to correct
and one check for the page (`wikikit.scan.desk_serve`).

    uv run --env-file .env python tools/desk.py serve [PORT]
        -> the desk at http://localhost:PORT/desk (default 8020), on the site's
           own server: each page's strips beside the page rendered as it would
           enter, by the site's viewer, its links resolved as the build
           resolves them (from the database: not during a rebuild).  Saving
           writes into data/supplied; a page checked is proofread and enters
           at the next rebuild.  Never save while a rebuild runs.
    uv run python tools/desk.py add VOL:PAGE [...] --why "what is wrong with Wikisource's page"
        -> each page's reading of ours onto the desk (`add`): its figures
           Wikisource's own images or our Commons regions, the gate passed,
           held until proofread.  PAGE is the PRINTED page.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from eb1911.scans import _printed
from wikikit.scan import supplied
from wikikit.source_pages import SUPPLIED_DIR, fetched_text, prefer

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
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
        # a level-2 page (text missing: refused or unread) is shown for the
        # proofreader to supply what is missing: a save keeps the page's text
        # as they leave it, never rebuilt from the readings
        if (lv == 1 and held) or lv == 2 or (done and lv >= 3):
            keys.append((v, p))
    return keys


def add(vol: int, ws: int, why: str) -> str:
    """Put our reading of a page on the desk: into data/supplied, where the
    door holds it until it is proofread.  The reading: the table re-reading
    where one exists, else the judged reading (data/readings).  Its figures:
    Wikisource's own images where its page has them (`carry_images`), else
    the Commons regions set for them (data/readings/figure_regions.json); one
    the print sets with type beside it floats there (`measure_insets`).  A
    Wikisource page proofread there (level 2 or more) is replaced only because
    we say why (`replaces`); every page records why it was staged.  Refused:
    a page already supplied, a page with no reading of ours, a page the gate
    fails, a page that would enter unproofread."""
    import copy
    import datetime
    import urllib.request
    sys.path.insert(0, str(Path(__file__).parent / "patches"))
    sys.path.insert(0, str(Path(__file__).parent / "diagnostics"))
    from paths import READINGS, reading, table_reading
    from supplied_gate import LIVE_PRINTED, checks
    from wikikit.scan.transcribe import apply_type
    from wikikit.source_pages import page_level

    stem = f"vol{vol:02d}-page{ws:04d}"
    if supplied.path_for(vol, ws).exists():
        raise SystemExit(f"{label(vol, ws)}: already on the desk (data/supplied)")
    src = next((f for f in (table_reading(stem), reading(stem)) if f.exists()), None)
    if src is None:
        raise SystemExit(f"{label(vol, ws)}: no reading of ours — it needs a vision read first")
    d = json.loads(src.read_text(encoding="utf-8"))
    p = d["provenance"]
    fetched = fetched_text(vol, ws)
    # sizes measured into the readings (the reading is the only truth of them)
    for name, sizes in (p.pop("type", None) or {}).items():
        p["readings"][name] = apply_type(p["readings"][name], sizes)
    supplied.carry_images(d, fetched=fetched)
    regions = json.loads((READINGS / "figure_regions.json").read_text(encoding="utf-8")).get(stem, {})
    own = set(p.get("images") or {})
    figs = {i["name"] for i in p["items"] if i["kind"] == "figure"}
    p["regions"] = {i: r["css"] for i, r in regions.items() if i in figs and i not in own}
    level = page_level(fetched or "")
    if level is not None and level >= 2:
        p["replaces"] = why
    p["staged"] = {"why": why, "from": src.as_posix(),
                   "at": datetime.date.today().isoformat()}
    if figs:
        # a figure the print sets with type beside it floats there, in its text
        from wikikit.corpora import current_corpus
        from wikikit.scan import cut
        supplied.measure_insets(d, cut.deskew(current_corpus().page_scan(vol, ws), p["angle"]))
    supplied.reassemble(d, fetched=fetched)
    live = json.loads(urllib.request.urlopen(urllib.request.Request(
        LIVE_PRINTED, headers={"User-Agent": "desk add"}), timeout=60).read())
    faults = list(checks(copy.deepcopy(d), fetched, live))
    if faults:
        raise SystemExit(f"{label(vol, ws)}: not staged, the gate fails it — "
                         + "; ".join(f"{k}: {m}" for k, m in faults))
    if prefer({"raw_text": fetched} if fetched is not None else None, d) is d:
        raise SystemExit(f"{label(vol, ws)}: not staged, it would enter unproofread")
    supplied.write(d)
    left = sorted(figs - own - set(p["regions"]))
    return (f"{label(vol, ws)}: on the desk, from {src.as_posix()}; "
            f"{len(own)} figure(s) Wikisource's, {sum(1 for c in p['regions'].values() if c)} "
            f"Commons region(s)" + (f"; OUR CROP still stands for {', '.join(left)}" if left else ""))


def main() -> int:
    if len(sys.argv) in (2, 3) and sys.argv[1] == "serve":
        import subprocess
        from wikikit.scan import desk_serve
        who = subprocess.run(["git", "config", "user.name"], capture_output=True, text=True).stdout.strip()
        desk_serve.serve_desk(lambda: queue(done=True), label, int(sys.argv[2]) if len(sys.argv) == 3 else 8020, who or "proofreader")
    elif len(sys.argv) >= 3 and sys.argv[1] == "add":
        args = sys.argv[2:]
        if "--why" not in args or args.index("--why") == len(args) - 1:
            print(__doc__)
            return 2
        k = args.index("--why")
        why, pages = args[k + 1], args[:k] + args[k + 2:]
        for a in pages:
            v, pg = (int(x) for x in a.split(":"))
            print(add(v, ws_for(v, pg), why))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
