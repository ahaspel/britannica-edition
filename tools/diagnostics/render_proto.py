"""Prototype of the recursive producer — `render(raw) -> output`.

THE diagnostic subject for Phase 0 (leak-scan + render-diff). It is the
walk→translate model in one place: `decompose` recognises block structure by
source token (the future walker's job at every depth), `render` recurses it and
carries style; leaves are image / prose / the compile-notations (`<math>`,
`<hiero>`, `<score>`) which ride through verbatim for the viewer to compile.

NOT wired into the pipeline. Importable, no side effects, no DB, no stdout
reconfig. Promoted from `tools/_scratch/{faithful_html,hostile}.py`. As Phase 1
proceeds this is where each newly-transcribed attribute lands first (producer
side), measured by `leak_scan.py` and `render_diff.py`, before it migrates into
the real producer at cutover.
"""
from __future__ import annotations

import re

from britannica.pipeline.stages.transform_articles.body_text import _apply_markup as TT
from britannica.pipeline.stages.elements._table_decompose import extract_wiki_rows
from britannica.pipeline.stages.elements._figure_decompose import (
    _peel_table, _normalize_attrs)
from britannica.pipeline.stages.elements._tables import _html_table_grid
from britannica.pipeline.stages.elements._layout import _process_image
from britannica.pipeline.stages.transform_articles.body_text import _convert_shoulder_headings
from britannica.export.sections import _dehyphenate_shoulder


# --- inline markers → HTML (viewer's mechanical layer) ---------------------
def render_inline(t: str) -> str:
    t = re.sub(r"«CTR»([\s\S]*?)«/CTR»", r'<div class="centered">\1</div>', t)
    t = re.sub(r"«I»([\s\S]*?)«/I»", r"<i>\1</i>", t)
    t = re.sub(r"«SC»([\s\S]*?)«/SC»", r'<span class="small-caps">\1</span>', t)
    t = re.sub(r"«B»([\s\S]*?)«/B»", r"<b>\1</b>", t)
    t = re.sub(r"«LN:[^|»]*\|([^»]*)«/LN»", r"\1", t)
    t = re.sub(r"«DHR\[[^\]]*\]»|«DHR»", "<hr>", t)
    # No generic "keep-inner" strip: it was a sweeper that dropped a marker's
    # styling silently AND would have mangled the carried compile-terminals
    # («MATH»/«HIERO»/«SCORE», which must ride through verbatim). Handled markers
    # convert above; terminals carry; everything else leaks honestly for leak_scan.
    # NB: no final strip of unhandled «MARKERS» — a silently-stripped marker is a
    # dropped style, i.e. a hidden gap. Leaving them lets leak_scan catch them.
    return t.strip()


# --- balanced-span helpers --------------------------------------------------
def _match(s: str, st: int, opn: str, cls: str) -> int:
    d = 0
    j = st
    while j < len(s):
        if s[j:j + len(opn)] == opn:
            d += 1
            j += len(opn)
        elif s[j:j + len(cls)] == cls:
            d -= 1
            j += len(cls)
            if d == 0:
                return j
        else:
            j += 1
    return len(s)


def _match_html(s: str, st: int) -> int:
    d = 0
    for m in re.finditer(r"<(/?)table\b[^>]*>", s[st:], re.I):
        d += -1 if m.group(1) else 1
        if d == 0:
            return st + m.end()
    return len(s)


_CENTER = re.compile(r"\{\{\s*(?:block center|center block|center|c)\s*\|", re.I)
# csc = centred small-caps; it can WRAP block structure (a figure: image + caption),
# so decompose must treat it as a wrapper and recurse its inner — otherwise it pulls
# the [[File:]] out from inside and shatters the balanced {{csc|…}}, leaking «{{csc|».
_CSC = re.compile(r"\{\{\s*csc\s*\|", re.I)


# --- decompose: block children of a chunk, in source order ------------------
def decompose(c: str) -> list[tuple[str, str]]:
    """Recognise the block structure of `c` by source token, in order. Returns
    [(kind, payload), …] with kind ∈ tbl/html/ctr/poem/img/prose. This is the
    one recogniser, used at every depth (walker = this at top level; render =
    this recursing)."""
    out: list[tuple[str, str]] = []
    i = 0
    while i < len(c):
        cand = []
        t = c.find("{|", i)
        if t >= 0:
            cand.append((t, "tbl"))
        m = _CENTER.search(c, i)
        if m:
            cand.append((m.start(), "ctr"))
        cm = _CSC.search(c, i)
        if cm:
            cand.append((cm.start(), "csc"))
        p = re.search(r"<poem>", c[i:], re.I)
        if p:
            cand.append((i + p.start(), "poem"))
        h = re.search(r"<table\b", c[i:], re.I)
        if h:
            cand.append((i + h.start(), "html"))
        im = re.search(r"\[\[(?:File|Image):", c[i:], re.I)
        if im:
            cand.append((i + im.start(), "img"))
        if not cand:
            if c[i:].strip():
                out.append(("prose", c[i:]))
            break
        st, kind = min(cand)
        if st > i and c[i:st].strip():
            out.append(("prose", c[i:st]))
        if kind == "tbl":
            en = _match(c, st, "{|", "|}")
            out.append(("tbl", c[st:en]))
        elif kind == "html":
            en = _match_html(c, st)
            out.append(("html", c[st:en]))
        elif kind == "ctr":
            en = _match(c, st, "{{", "}}")
            mm = _CENTER.match(c, st)
            out.append(("ctr", c[st + (mm.end() - st):en - 2]))
        elif kind == "csc":
            en = _match(c, st, "{{", "}}")
            mm = _CSC.match(c, st)
            out.append(("csc", c[st + (mm.end() - st):en - 2]))
        elif kind == "poem":
            mc = re.search(r"</poem>", c[st:], re.I)
            en = st + (mc.end() if mc else len(c) - st)
            out.append(("poem", re.sub(r"^<poem>|</poem>$", "", c[st:en], flags=re.I)))
        else:  # img
            en = c.find("]]", st) + 2
            out.append(("img", c[st:en]))
        i = en
    return out


def _lines(t: str) -> list[str]:
    t = re.sub(r"<br\s*/?>", "\n", t, flags=re.I)
    return [render_inline(TT(ln)) for ln in t.split("\n") if ln.strip()]


def _img(raw: str) -> str:
    inner = re.sub(r"\]\]\s*$", "", re.sub(r"^\s*\[\[(?:File|Image):", "", raw, flags=re.I))
    parts = inner.split("|")
    fn = parts[0].strip()
    w = None
    al = None
    for p in parts[1:]:
        p = p.strip()
        mm = re.match(r"(\d+)\s*px", p)
        if mm:
            w = int(mm.group(1))
        if p in ("center", "right", "left"):
            al = p
    if w and w <= 40 and not al:
        return f'<img alt="{fn}" style="width:{w}px;height:auto;vertical-align:middle">'
    st = f"max-width:{w}px;" if w else "max-width:100%;"
    if al == "center":
        return f'<figure style="text-align:center"><img alt="{fn}" style="{st}"></figure>'
    return f'<img alt="{fn}" style="{st}">'


_GW = re.compile(r"wikitable|border\s*=\s*[\"']?[1-9]|rules\s*=", re.I)
_GH = re.compile(r"border\s*=\s*[\"']?[1-9]|rules\s*=|wikitable|\bb[abc]\b|border\s*:", re.I)


def _cell(sep: str, attr: str, content: str) -> str:
    na = _normalize_attrs(attr)
    stl = "vertical-align:top;"
    if na.get("align"):
        stl += f"text-align:{na['align']};"
    if na.get("width"):
        stl += f"width:{na['width']};"
    tag = "th" if sep == "!" else "td"
    return f'<{tag} style="{stl}">{render(content)}</{tag}>'


def _wrap(cls: str, rows) -> str:
    body = ["<tr>" + "".join(_cell(s, a, co) for s, a, co in cells) + "</tr>"
            for _r, cells in rows if cells]
    return f'<table class="{cls}">{"".join(body)}</table>'


def _wiki_table(t: str) -> str:
    m = re.match(r"\{\|([^\n]*)", t)
    ta = m.group(1) if m else ""
    cls = "data-table" if _GW.search(ta) else "figtable"
    _cap, rows = extract_wiki_rows(_peel_table(t))
    return _wrap(cls, rows)


def _mask_nested(s: str, store: list) -> str:
    res = []
    i = 0
    pat = re.compile(r"<table\b", re.I)
    while True:
        m = pat.search(s, i)
        if not m:
            res.append(s[i:])
            break
        res.append(s[i:m.start()])
        en = _match_html(s, m.start())
        store.append(s[m.start():en])
        res.append(f"\x00{len(store) - 1}\x00")
        i = en
    return "".join(res)


def _html_table(block: str) -> str:
    tg = re.match(r"<table\b([^>]*)>", block, re.I)
    ta = tg.group(1) if tg else ""
    cls = "data-table" if _GH.search(ta) else "figtable"
    inner = block[tg.end():] if tg else block
    inner = re.sub(r"</table>\s*$", "", inner, flags=re.I)
    store: list = []
    masked = _mask_nested(inner, store)
    body = []
    for row in _html_table_grid(masked):
        body.append("<tr>" + "".join(
            _cell(s, a, re.sub(r"\x00(\d+)\x00", lambda mm: store[int(mm.group(1))], co))
            for s, a, co in row) + "</tr>")
    return f'<table class="{cls}">{"".join(body)}</table>'


# Phase-1 (per-attribute lockstep). Shoulder heading: TRANSCRIBE — a style marker
# «SH» (viewer styles it; NOT a compile-terminal), via the existing producer, plus
# soft-hyphen mend. Fine-print family: STRIP at top — drop wrapper, keep inner (a
# small-font print artifact we don't reproduce).
_SH_BR = re.compile(r"-\s*<br\s*/?>\s*", re.I)


def _shoulder(c: str) -> str:
    c = _convert_shoulder_headings(c)
    return re.sub(
        r"«SH»(.*?)«/SH»",
        lambda m: "«SH»" + _dehyphenate_shoulder(_SH_BR.sub("", m.group(1))).strip() + "«/SH»",
        c, flags=re.S)


def _unwrap_ci(text: str, name: str) -> str:
    """Case-insensitive balanced unwrap of `{{name…|X}}` → X (paired /s,/e → '')."""
    low = ("{{" + name).lower()
    out, pos = [], 0
    while True:
        i = text.lower().find(low, pos)
        if i < 0:
            out.append(text[pos:])
            return "".join(out)
        en = _match(text, i, "{{", "}}")
        seg = text[i:en]
        bar = seg.find("|")
        out.append(text[pos:i])
        out.append(seg[bar + 1:-2] if bar >= 0 else "")
        pos = en


def _strip_fineprint(c: str) -> str:
    return _unwrap_ci(_unwrap_ci(c, "EB1911 fine print"), "fine block")


def render(c: str) -> str:
    """Recurse `c`: structure → recurse, prose/image → carry, (compile-leaves
    ride through inline via TT for the viewer)."""
    if "shoulder heading" in c.lower():
        c = _shoulder(c)
    if re.search(r"\{\{\s*(?:fine block|eb1911 fine print)", c, re.I):
        c = _strip_fineprint(c)
    out = []
    for kind, pay in decompose(c):
        if kind == "tbl":
            out.append(_wiki_table(pay))
        elif kind == "html":
            out.append(_html_table(pay))
        elif kind == "ctr":
            out.append(f'<div class="centered">{render(pay)}</div>')
        elif kind == "csc":
            out.append(f'<div class="centered"><span class="small-caps">{render(pay)}</span></div>')
        elif kind == "poem":
            out.append("<br>".join(_lines(pay)))
        elif kind == "img":
            out.append(_img(pay))
        else:
            out.append(" ".join(_lines(pay)))
    return "".join(out)


# === producer-contract variant: render_markers() ===========================
# `render()` above emits HTML (it fuses producer+viewer for visual checks).
# `render_markers()` emits the PRODUCER marker contract — the same vocabulary
# (`{{IMG:}}`/`{{LEGEND:}}`/`«CTR»`/`«SC»`/`«HTMLTABLE:»`/`{{VERSE:}}`) every
# article body carries and the viewer (proven total) renders.  Same `decompose`
# skeleton; only the block leaves change emit-form.  Tables emit as `«HTMLTABLE:`
# so they inherit the viewer's wide-table Expand machinery (≥10 cols → modal).
_IMG_ATTR = re.compile(
    r"^(?:\d+\s*x?\s*\d*\s*px|thumb\w*|frame\w*|frameless|border|center|right|"
    r"left|none|top|middle|bottom|baseline|text-top|text-bottom|"
    r"upright(?:=[\d.]+)?|link=.*|alt=.*|page=\d+|lang=.*)$", re.I)


def _img_marker(raw: str) -> str:
    inner = re.sub(r"\]\]\s*$", "", re.sub(r"^\s*\[\[(?:File|Image):", "", raw, flags=re.I))
    parts = [p.strip() for p in inner.split("|")]
    fn = parts[0]
    width = align = None
    for p in parts[1:]:
        mw = re.match(r"(\d+)\s*px$", p)
        if mw:
            width = int(mw.group(1))
        elif p.lower() in ("center", "right", "left"):
            align = p.lower()
    caps = [p for p in parts[1:] if p and not _IMG_ATTR.match(p)]
    cap = TT(caps[-1]).strip() if caps else ""
    meta = (f"|align={align}" if align else "") + (f"|width={width}" if width else "")
    body = f"IMG:{fn}{meta}"
    return f"{{{{{body}|{cap}}}}}" if cap else f"{{{{{body}}}}}"


def _cell_marker(sep: str, attr: str, content: str) -> str:
    tag = "th" if sep == "!" else "td"
    na = _normalize_attrs(attr)
    extra = ""
    if na.get("colspan"):
        extra += f' colspan="{na["colspan"]}"'
    if na.get("rowspan"):
        extra += f' rowspan="{na["rowspan"]}"'
    return f"<{tag}{extra}>{render_markers(content).strip()}</{tag}>"


def _rows_to_htmltable(rows, cls: str = "data-table") -> str:
    trs = "".join(
        "<tr>" + "".join(_cell_marker(s, a, co) for s, a, co in cells) + "</tr>"
        for _r, cells in rows if cells)
    return f'«HTMLTABLE:<table class="{cls}">{trs}</table>«/HTMLTABLE»'


def _wiki_table_marker(t: str) -> str:
    m = re.match(r"\{\|([^\n]*)", t)
    ta = m.group(1) if m else ""
    cls = "data-table" if _GW.search(ta) else "figtable"
    _cap, rows = extract_wiki_rows(_peel_table(t))
    return _rows_to_htmltable(rows, cls)


def _html_table_marker(block: str) -> str:
    tg = re.match(r"<table\b([^>]*)>", block, re.I)
    ta = tg.group(1) if tg else ""
    cls = "data-table" if _GH.search(ta) else "figtable"
    inner = block[tg.end():] if tg else block
    inner = re.sub(r"</table>\s*$", "", inner, flags=re.I)
    store: list = []
    masked = _mask_nested(inner, store)
    rows = list(_html_table_grid(masked))
    # Restore nested tables (recursively rendered) inside their cells.
    restored = []
    for row in rows:
        cells = [(s, a, re.sub(r"\x00(\d+)\x00",
                               lambda mm: store[int(mm.group(1))], co))
                 for s, a, co in row]
        restored.append((None, cells))
    return _rows_to_htmltable(restored)


def render_markers(c: str) -> str:
    """Producer-contract sibling of `render()`: raw → MARKER text (not HTML)."""
    if "shoulder heading" in c.lower():
        c = _shoulder(c)
    if re.search(r"\{\{\s*(?:fine block|eb1911 fine print)", c, re.I):
        c = _strip_fineprint(c)
    out = []
    for kind, pay in decompose(c):
        if kind == "tbl":
            out.append(_wiki_table_marker(pay))
        elif kind == "html":
            out.append(_html_table_marker(pay))
        elif kind == "ctr":
            out.append(f"«CTR»{render_markers(pay)}«/CTR»")
        elif kind == "csc":
            out.append(f"«CTR»«SC»{render_markers(pay)}«/SC»«/CTR»")
        elif kind == "poem":
            lines = [TT(ln).strip() for ln in re.sub(r"<br\s*/?>", "\n", pay, flags=re.I).split("\n") if ln.strip()]
            out.append("{{VERSE:" + "\n".join(lines) + "}VERSE}")
        elif kind == "img":
            out.append(_img_marker(pay))
        else:
            out.append(TT(pay).strip())
    return "\n\n".join(x for x in out if x)
