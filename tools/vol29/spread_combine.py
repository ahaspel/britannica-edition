"""Band-from-spread / walk-from-halves combine for the vol-29 classified TOC.

The OCR can read a spread two incompatible ways: the WHOLE spread (banners
intact, columns scrambled) or the two HALVES (columns in order, banners sliced).
Neither alone suffices -- you need both, because the gutter forces the trade-off.
So we read each spread three ways (`spread`, `left`, `right`) and combine them:

  * BAND from `spread` -- the only view where a full-width banner is whole, so it
    is the authority for which bands exist and their order.
  * WALK from `left`/`right` -- the only view where the columns are in reading
    order, so it is the authority for content sequence.

The combine parses `spread` into bands, walks each half into per-band segments by
matching its sliver banners to the whole band names (no reconstruction -- the
band name is READ, not rebuilt), and merges left-then-right per band.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_toc as B

_STOP = {"and", "the", "of", "with", "for", "etc", "see", "also"}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def _toks(s: str) -> list[str]:
    s = re.sub(r"\(.*?cont.*?\)", "", s, flags=re.I)
    s = re.sub(r"[#*()\[\]:,.\-—?]", " ", s)
    return [w for w in (_norm(x) for x in s.split()) if len(w) >= 3 and w not in _STOP]


def _fz(x: str, y: str) -> bool:
    return x == y or (len(x) >= 3 and len(y) >= 3
                      and (x.startswith(y) or y.startswith(x)))


def _overlap(a: list[str], b: list[str]) -> bool:
    return any(_fz(x, y) for x in a for y in b)


_CATS = [_norm(c) for c in B.CATEGORIES]
# Only REAL continents (those with section children) -- a childless subcat
# ("Physical features and Oceanography") must not pose as a continent.
_CONT = {cont: _toks(cont)
         for _, subs in B._cat_continents().items()
         for cont, secs in subs if secs}


def _is_cat(label: str) -> bool:
    n = _norm(label)
    return any(n == c or (len(n) >= 5 and (c.startswith(n) or n.startswith(c)))
               for c in _CATS)


def _cont_only(label: str) -> bool:
    lt = _toks(label)
    return bool(lt) and any(
        ct and all(any(_fz(w, cw) for cw in ct) for w in lt)
        for ct in _CONT.values())


def _is_band(s: str) -> bool:
    # A full-width banner: `## ` (two hashes) or an all-caps `**...**`.  A `### `
    # header or a mixed-case `**Name**` is a within-column header, i.e. content.
    return s.startswith("## ") or (s.startswith("**") and B._is_caps_banner(s))


def _resolve_cont(text: str) -> str | None:
    """A continent fragment -> the full index continent name, so the canonical
    banner carries the whole name (which `_resolve_banner` needs) not a clip."""
    tt = _toks(text)
    if not tt:
        return None
    for cont, ct in _CONT.items():
        if ct and all(any(_fz(w, cw) for cw in ct) for w in tt):
            return cont
    for cont, ct in _CONT.items():
        if ct and _fz(tt[0], ct[0]):
            return cont
    return None


def parse_bands(spread: str) -> list[dict]:
    """`spread` text -> ordered bands, each emitting the CANONICAL banner the
    nester expects: "## Category", "## Continent", or the one-line
    "## Continent — Section".  A continent line is fused with the section that
    follows it (the banner wrapped two lines); a combined "Continent?Section"
    line is split; a bare section carries the continent in scope.  The one-line
    form matters: a bare "## Physical Features" mis-resolves to the childless
    subcat "Physical features and Oceanography"."""
    L = [l.strip() for l in spread.split("\n") if l.strip().startswith("## ")]
    bands: list[dict] = []
    cur_cont: str | None = None
    i = 0
    while i < len(L):
        lab = L[i][3:].strip().strip("*").strip()
        parts = [p.strip() for p in re.split(r"\s*[—–?]\s*", lab) if p.strip()]
        if _is_cat(lab):
            cur_cont = None
            bands.append({"emit": ["## " + lab], "toks": _toks(lab),
                          "norm": _norm(lab)})
            i += 1
        elif len(parts) >= 2 and _resolve_cont(parts[0]):
            cont, sec = _resolve_cont(parts[0]), " ".join(parts[1:])
            cur_cont = cont
            bands.append({"emit": [f"## {cont} — {sec}"], "toks": _toks(lab),
                          "norm": _norm(cont + sec)})
            i += 1
        elif _cont_only(lab):
            cont = _resolve_cont(lab) or lab
            cur_cont = cont
            if i + 1 < len(L):
                nx = L[i + 1][3:].strip().strip("*").strip()
                if not _is_cat(nx) and not _cont_only(nx):
                    bands.append({"emit": [f"## {cont} — {nx}"],
                                  "toks": _toks(lab) + _toks(nx),
                                  "norm": _norm(cont + nx)})
                    i += 2
                    continue
            bands.append({"emit": [f"## {cont}"], "toks": _toks(lab),
                          "norm": _norm(cont)})
            i += 1
        else:
            emit = f"## {cur_cont} — {lab}" if cur_cont else "## " + lab
            bands.append({"emit": [emit], "toks": _toks(lab),
                          "norm": _norm((cur_cont or "") + lab)})
            i += 1
    return bands


def combine(spread: str, left: str, right: str, incoming: int = -1) -> list[str]:
    bands = parse_bands(spread)

    def match(banner: str, cur: int) -> int | None:
        b = _norm(re.sub(r"[#*]", "", banner))
        bt = _toks(banner)

        def hit(j: int) -> bool:
            n = bands[j]["norm"]
            return ((len(b) >= 2 and (n.startswith(b) or b.startswith(n)
                                      or n.endswith(b) or b.endswith(n)))
                    or _overlap(bt, bands[j]["toks"]))

        for j in range(cur + 1, len(bands)):
            if hit(j):
                return j
        for j in range(cur, -1, -1):
            if hit(j):
                return j
        return None

    def walk(text: str, cur: int) -> dict[int, list[str]]:
        segs: dict[int, list[str]] = {}
        first = None
        for l in text.split("\n"):
            s = l.strip()
            if _is_band(s):
                j = match(s, cur)
                if j is not None:
                    if first is None:
                        first = j
                    if j > cur:
                        cur = j
                continue
            if not s:
                continue
            n = _norm(s.lstrip("# "))
            if len(n) >= 5 and n in "classifiedlistofarticles":
                continue                              # running page header furniture
            if (s.startswith("<!--") or B._CONT_RE.search(s)
                    or B._is_clip_header(s)):
                continue                              # comment / (cont.) repeat / clip
            m = re.fullmatch(r"\*([^*]+)\*", s)        # eponymous principal: a band
            if m:                                      # whose banner clip THIS half
                x = _norm(m.group(1))                  # lost, named by its lead article
                for j in range(cur + 1, len(bands)):   # (e.g. left-half Art, headed
                    if x and bands[j]["norm"] == x:    # by `*Art*`, no `## Art`)
                        old = segs.get(cur, [])
                        moved = ([old.pop()] if old
                                 and old[-1].strip().startswith("### ") else [])
                        cur = j
                        if first is None:
                            first = j
                        segs.setdefault(cur, []).extend(moved)
                        break
            segs.setdefault(cur, []).append(l)
        # A half that continues a band established on the OTHER half carries that
        # band's content before its own first banner -> seat the lead one band
        # back.  Only when that band is strictly past the incoming one (else the
        # lead already sits in the right place; popping it would just drop it).
        if first is not None and first - 1 > incoming and incoming in segs:
            lead = segs.pop(incoming)
            segs.setdefault(first - 1, []).extend(lead)
        return segs

    sL = walk(left, incoming)
    sR = walk(right, incoming)
    out: list[str] = []
    for j in sorted(set(sL) | set(sR)):
        if 0 <= j < len(bands) and j > incoming:
            out += bands[j]["emit"]
        out += sL.get(j, []) + sR.get(j, [])
    return out
