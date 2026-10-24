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
           Beside it, the PATCH SCREEN at /desk/patches: every patch the chain
           made (data/staging/patches/kept.json, so after build.sh) on the
           judged pages, beside the scan, Wikisource's markup before and after,
           flagged pages first; a ruling, keep, drop or edit (your own text
           in the patch's place), goes into data/readings/patch_rulings.json
           and install.py honours it over every check.
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


def _patch_paths():
    sys.path.insert(0, str(Path(__file__).parent / "patches"))
    import paths
    return paths


def validator_faults(problems: list[str]) -> list[tuple[str, str]]:
    """validate.json's "removes word(s) [...]: 'old'" problems of one page:
    (the old text it quotes, the problem) — as drop_faulted.py reads them."""
    import ast
    import re
    out = []
    for pr in problems:
        m = re.match(r"removes word\(s\) \[[^\]]*\]: (.*)$", pr, re.S)
        if m:
            out.append((ast.literal_eval(m.group(1)), pr.split(":", 1)[0]))
    return out


def _quoted(x: dict, old: str) -> bool:
    """The patch a check quotes by its old text (whole, or its first 60+)."""
    return x["old"] == old or (len(old) >= 60 and x["old"].startswith(old))


class Patches:
    """The patch screen's patches (`wikikit.scan.desk_serve.PatchSource`):
    the chain's kept patches on the judged pages, less the pages our own
    whole page replaces, each with what the checks say of it — the leak
    check (leaks.json, less leaks_reviewed.json), the validator
    (validate.json), drop.json — and a person's ruling."""

    def __init__(self):
        P = _patch_paths()
        self.P = P
        load = lambda f, empty: json.loads(f.read_text(encoding="utf-8")) if f.exists() else empty
        self.kept = load(P.WORK / "kept.json", {})
        self.leaks = load(P.WORK / "leaks.json", {})
        self.faults = {s: validator_faults(ps) for s, ps in load(P.WORK / "validate.json", {}).items()}
        self.drop = [tuple(x) for x in load(P.DROP, [])]
        judged = P.PAGES.read_text().split()
        pages = []
        for stem in judged:
            if not self.kept.get(stem):
                continue
            v, p = int(stem[3:5]), int(stem[-4:])
            if supplied.path_for(v, p).exists():
                ws = fetched_text(v, p)
                d = supplied.read(v, p)
                if prefer({"raw_text": ws} if ws is not None else None, d) is d:
                    continue                    # ours enters whole: no patches laid
            pages.append((v, p))
        flagged = {k for k in pages if any(x["flags"] for x in self.patches(*k))}
        self.pages = sorted(pages, key=lambda k: (k not in flagged, k))

    @staticmethod
    def stem(v: int, p: int) -> str:
        return f"vol{v:02d}-page{p:04d}"

    def _rulings(self) -> list[dict]:
        f = self.P.PATCH_RULINGS
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else []

    def queue(self) -> list[tuple[int, int]]:
        return self.pages

    def patches(self, v: int, p: int) -> list[dict]:
        stem = self.stem(v, p)
        rulings = {(r["old"], r["new"]): r for r in self._rulings() if r["stem"] == stem}
        together = [l["why"] for l in self.leaks.get(stem, []) if l["old"].startswith("(all the page")]
        out = []
        for x in self.kept.get(stem, []):
            flags = [f"leak: {l['why']}" for l in self.leaks.get(stem, [])
                     if l["old"] == x["old"][:200] and l["new"] == x["new"][:200]]
            flags += [f"validator: {why}" for old, why in self.faults.get(stem, []) if _quoted(x, old)]
            flags += [f"the page's patches together: {w}" for w in together]
            dropped = any(s == stem and _quoted(x, old) for s, old in self.drop)
            r = rulings.get((x["old"], x["new"]))
            out.append({**{k: x[k] for k in ("kind", "start", "end", "old", "new")}, "flags": flags,
                        "chain": "drop" if dropped else "install",
                        "ruling": {k: r.get(k) for k in ("ruling", "note", "by", "at", "edit")} if r else None})
        return out

    def reading(self, v: int, p: int) -> dict:
        return json.loads(self.P.reading(self.stem(v, p)).read_text(encoding="utf-8"))

    def rule(self, v: int, p: int, old: str, new: str, ruling: str | None, note: str, by: str,
             edit: dict | None = None) -> str:
        import datetime
        from wikikit.scan.patches import check
        stem = self.stem(v, p)
        x = next((x for x in self.kept.get(stem, []) if x["old"] == old and x["new"] == new), None)
        if x is None:
            raise LookupError(f"{label(v, p)}: no such patch in kept.json — rebuild the chain and reload")
        rows = [r for r in self._rulings() if not (r["stem"] == stem and r["old"] == old and r["new"] == new)]
        mine = None
        if ruling == "edit":
            # the person's text over a span of the fetched page — the patch's
            # own, or wider when they changed the words either side — held to
            # the check install holds every patch to: Wikisource's structure kept
            raw = fetched_text(v, p) or ""
            s, t = edit["start"], edit["end"]
            if not (0 <= s <= x["start"] and x["end"] <= t <= len(raw)):
                raise ValueError(f"{label(v, p)}: the edit's span {s}:{t} does not hold the patch's own")
            if raw[s:t] != edit.get("was"):
                # the screen says what it showed under the span: else an edit
                # could take or leave text the person never saw
                raise ValueError(f"{label(v, p)}: the page under the edit is not what the box showed — "
                                 "nothing saved; reload the page")
            dropped = {(r["old"], r["new"]) for r in rows if r["stem"] == stem and r["ruling"] == "drop"}
            other = next((y for y in self.kept.get(stem, []) if y is not x and (y["old"], y["new"]) not in dropped
                          and y["start"] < t and s < y["end"]), None)
            if other:
                raise ValueError(f"{label(v, p)}: the edit reaches into the patch {other['old'][:30]!r} → "
                                 f"{other['new'][:30]!r} — drop that one first, nothing saved")
            mine = {"start": s, "end": t, "old": raw[s:t], "new": edit["text"]}
            bad = check(raw, [{**mine, "kind": x["kind"]}])
            if bad:
                raise ValueError(f"{label(v, p)}: the edit is refused, nothing saved — {bad[0]}")
        if ruling:
            rows.append({"stem": stem, "old": old, "new": new, "ruling": ruling, "note": note, "by": by,
                         "at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                         **({"edit": mine} if mine else {})})
        rows.sort(key=lambda r: (r["stem"], r["old"]))
        self.P.PATCH_RULINGS.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        a, b = (mine["old"], mine["new"]) if mine else (old, new)
        return f"{label(v, p)}: {ruling or 'ruling withdrawn'} — {a[:40]!r} → {b[:40]!r}"


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
        desk_serve.serve_desk(lambda: queue(done=True), label, int(sys.argv[2]) if len(sys.argv) == 3 else 8020,
                              who or "proofreader", patches=Patches())
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
