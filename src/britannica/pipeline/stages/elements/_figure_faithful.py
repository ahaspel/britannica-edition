"""The faithful recursive figure producer — promoted from the proven
`tools/diagnostics/render_proto.py` prototype (the plate playbook applied to
in-article figures).

The model (walk → translate, no role classification): `decompose` recognizes a
chunk's BLOCK structure by source token at every depth (table / html / center /
csc / poem / image / prose), `render_markers` recurses it and translates each
block into the viewer's EXISTING marker vocabulary IN SOURCE ORDER:

  image  → ``{{IMG:…}}`` (width/align carried; caption only when the source
           bundled one in the image cell)
  table  → ``«HTMLTABLE:<table class="figtable">…»`` (borderless figure lane;
           per-cell width/valign carried as ``<td style>``; the viewer renders
           it natively) — or ``data-table`` when the source marks a real grid
  center → ``«CTR»…«/CTR»``;  csc → ``«CTR»«SC»…«/SC»«/CTR»``
  poem   → ``{{VERSE:…}VERSE}``
  prose  → body-text (`text_transform`)

No caption/legend/attribution ROLES, no ``{{LEGEND}}`` aside — the source states
its own rendering (``{{Hi}}`` indent, ``{{csc}}`` small-caps, ``||`` columns) and
we render that faithfully. The `|+` table caption (which `extract_wiki_rows`
surfaces but the grid drops) is recursed back in, not discarded — it can carry
the figure's caption OR its image (ALGAE).

Content-total by construction (`decompose` partitions every byte; nothing is
classified-and-dropped). Verified corpus-wide 2026-06-02; see
[[project_figure_collapse]].
"""
from __future__ import annotations

import re

from britannica.pipeline.stages.transform_articles.body_text import (
    _apply_markup as TT, _convert_shoulder_headings)
from britannica.export.sections import _dehyphenate_shoulder
from britannica.pipeline.stages.elements._table_decompose import extract_wiki_rows
from britannica.pipeline.stages.elements._figure_decompose import (
    _peel_table, _normalize_attrs)
from britannica.pipeline.stages.elements._tables import _html_table_grid


# ── balanced-span helpers ──────────────────────────────────────────────
def _match(s: str, st: int, opn: str, cls: str) -> int:
    d, j = 0, st
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
# csc = centred small-caps; it can WRAP block structure (image + caption), so
# decompose treats it as a recursing wrapper, not a leaf — else it pulls the
# [[File:]] out and shatters the balanced {{csc|…}}.
_CSC = re.compile(r"\{\{\s*csc\s*\|", re.I)


def decompose(c: str) -> list[tuple[str, str]]:
    """Recognize the block structure of `c` by source token, in order — the one
    recognizer used at every depth."""
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


# ── shoulder-heading + fine-print transcription (per-attribute, from proto) ──
_SH_BR = re.compile(r"-\s*<br\s*/?>\s*", re.I)


def _shoulder(c: str) -> str:
    c = _convert_shoulder_headings(c)
    return re.sub(
        r"«SH»(.*?)«/SH»",
        lambda m: "«SH»" + _dehyphenate_shoulder(_SH_BR.sub("", m.group(1))).strip() + "«/SH»",
        c, flags=re.S)


def _unwrap_ci(text: str, name: str) -> str:
    """Case-insensitive balanced unwrap of `{{name…|X}}` → X."""
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


# ── leaves → markers ────────────────────────────────────────────────────
_GW = re.compile(r"wikitable|border\s*=\s*[\"']?[1-9]|rules\s*=", re.I)
_GH = re.compile(r"border\s*=\s*[\"']?[1-9]|rules\s*=|wikitable|\bb[abc]\b|border\s*:", re.I)
_IMG_ATTR = re.compile(
    r"^(?:\d+\s*x?\s*\d*\s*px|thumb\w*|frame\w*|frameless|border|center|right|"
    r"left|none|top|middle|bottom|baseline|text-top|text-bottom|"
    r"upright(?:=[\d.]+)?|link=.*|alt=.*|page=\d+|lang=.*)$", re.I)


def _tt_br(s: str) -> str:
    """Apply body markup, then regularize the inline HTML the viewer can't
    render raw inside an escaped marker into canonical markers: `<br>`→«BR»
    (figure prose treats it as a line break — the BODY producer renders it as a
    space, different rule), and `<small>`→«SM» (the HTML twin of `{{smaller}}`,
    which TT already maps to «SM»; the source mixes both forms — AEGEAN PLATE II
    Figs 6-7). The single place that knows figure inline-HTML → marker."""
    s = TT(s)
    s = re.sub(r"<br\s*/?>", "«BR»", s, flags=re.I)
    s = re.sub(r"<small>", "«SM»", s, flags=re.I)
    s = re.sub(r"</small>", "«/SM»", s, flags=re.I)
    return s


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
    cap = _tt_br(caps[-1]).strip() if caps else ""
    meta = (f"|align={align}" if align else "") + (f"|width={width}" if width else "")
    body = f"IMG:{fn}{meta}"
    return f"{{{{{body}|{cap}}}}}" if cap else f"{{{{{body}}}}}"


def _cell_marker(sep: str, attr: str, content: str) -> str:
    # Carry the cell's PAGE layout faithfully — align (the caption row's
    # `align="center"`), valign, width — so the viewer need not guess. The
    # viewer's figtable CSS no longer imposes text-align:center; it comes from
    # here, from the source.
    tag = "th" if sep == "!" else "td"
    na = _normalize_attrs(attr)
    extra = ""
    if na.get("colspan"):
        extra += f' colspan="{na["colspan"]}"'
    if na.get("rowspan"):
        extra += f' rowspan="{na["rowspan"]}"'
    style = ""
    if na.get("align"):
        style += f"text-align:{na['align']};"
    if na.get("valign"):
        style += f"vertical-align:{na['valign']};"
    if na.get("width"):
        style += f"width:{na['width']};"
    if style:
        extra += f' style="{style}"'
    return f"<{tag}{extra}>{render_markers(content).strip()}</{tag}>"


# Page-faithful figure-table layout from the `{|<attrs>` opener — carried
# whole onto the figtable so the VIEWER need not impose any of it. The canonical
# `_table_opener_styles` does the real work (inline `style="…"`, and the `{{Ts}}`
# codes — `ma`→margin:auto centring, `sm92`→font-size, with the alias + period
# fixes); we only correct its two figure-box blind spots: a table-level
# `align=right/left` is a FLOAT (the body wraps the figure — SEWING MACHINES
# Fig 1), not text-align, and a bare `width=NNN` it drops.
_OPENER_ALIGN_RE = re.compile(r'align\s*=\s*"?(right|left|center)\b', re.I)
_OPENER_WIDTH_RE = re.compile(r'width\s*=\s*"?(\d+)', re.I)


def _figtable_table_style(opener: str) -> str:
    from britannica.pipeline.stages.elements._tables import _table_opener_styles
    decls = []
    m = _OPENER_ALIGN_RE.search(opener)
    if m:
        a = m.group(1).lower()
        if a == "center":
            # table-level align=center centres the BOX (margin:auto), same as
            # `{{Ts|ma}}` — NOT a float, NOT text-align.
            decls += ["margin-right:auto", "margin-left:auto"]
        else:
            decls.append(f"float:{a}")
    w = _OPENER_WIDTH_RE.search(opener)
    if w:
        decls.append(f"width:{w.group(1)}px")
    # The rest (Ts centring/size, inline margins, valign) from the canonical
    # parser — minus its `text-align`, which is meaningless on a <table> box
    # (centring rides on `ma`→margin:auto; the float on `align`).
    for d in _table_opener_styles("{|" + opener):
        if d.lower().startswith("text-align"):
            continue
        decls.append(d)
    return ";".join(decls)


def _rows_to_htmltable(rows, cls: str = "data-table", table_style: str = "") -> str:
    trs = "".join(
        "<tr>" + "".join(_cell_marker(s, a, co) for s, a, co in cells) + "</tr>"
        for _r, cells in rows if cells)
    sty = f' style="{table_style}"' if table_style else ""
    return f'«HTMLTABLE:<table class="{cls}"{sty}>{trs}</table>«/HTMLTABLE»'


def _wiki_table_marker(t: str) -> str:
    m = re.match(r"\{\|([^\n]*)", t)
    ta = m.group(1) if m else ""
    cls = "data-table" if _GW.search(ta) else "figtable"
    cap, rows = extract_wiki_rows(_peel_table(t))
    tbl = _rows_to_htmltable(
        rows, cls, _figtable_table_style(ta) if cls == "figtable" else "") if rows else ""
    if cap.strip():
        # `|+` carries the figure's caption — or its image (ALGAE). Recurse it
        # (don't drop), in source position before the rows.
        cap_md = render_markers(cap).strip()
        if cap_md:
            return (cap_md + "\n\n" + tbl) if tbl else cap_md
    return tbl


def _mask_nested(s: str, store: list) -> str:
    res, i = [], 0
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


def _html_table_marker(block: str) -> str:
    tg = re.match(r"<table\b([^>]*)>", block, re.I)
    ta = tg.group(1) if tg else ""
    cls = "data-table" if _GH.search(ta) else "figtable"
    inner = block[tg.end():] if tg else block
    inner = re.sub(r"</table>\s*$", "", inner, flags=re.I)
    store: list = []
    masked = _mask_nested(inner, store)
    rows = list(_html_table_grid(masked))
    restored = []
    for row in rows:
        cells = [(s, a, re.sub(r"\x00(\d+)\x00",
                               lambda mm: store[int(mm.group(1))], co))
                 for s, a, co in row]
        restored.append((None, cells))
    return _rows_to_htmltable(restored)


def render_markers(c: str) -> str:
    """Raw figure bytes → producer MARKER text, recursively, in source order."""
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
            lines = [TT(ln).strip() for ln in
                     re.sub(r"<br\s*/?>", "\n", pay, flags=re.I).split("\n")
                     if ln.strip()]
            out.append("{{VERSE:" + "\n".join(lines) + "}VERSE}")
        elif kind == "img":
            out.append(_img_marker(pay))
        else:
            out.append(_tt_br(pay).strip())
    return "\n\n".join(x for x in out if x)


def produce_faithful_figure(raw: str) -> str:
    """Producer entry point: a figure's RAW bytes → marker output. Wired into
    the dispatch as ``lambda raw, inner, tt, ctx, reg: produce_faithful_figure(raw)``."""
    return render_markers(raw)
