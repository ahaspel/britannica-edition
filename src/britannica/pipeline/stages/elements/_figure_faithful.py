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
from britannica.pipeline.stages.elements._figure_decompose import _peel_table
from britannica.pipeline.stages.elements._tables import _html_table_grid
from britannica.pipeline.stages.elements._walker import _construct_end


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
# Image LEAF in TEMPLATE spelling — `{{img float|…}}` / `{{figure|…}}` /
# `{{FI|…}}` (named params file/cap/width/align) and `{{raw image|…}}` (DjVu
# page-ref → local full-page render, optional trailing `{{c|cap}}`).  decompose
# treats these as image atoms exactly like `[[File:…]]`; the marker reuses the
# shared parsers + `build_img_marker`, so the `_process_image_float` /
# `_process_raw_image` PRODUCERS are no longer needed (the bracket form and the
# template forms are now all one leaf in faithful).
_IMG_TEMPLATE = re.compile(
    r"\{\{\s*(?:img\s*float|figure|FI|raw\s+image)\s*\|", re.I)


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
        it = _IMG_TEMPLATE.search(c, i)
        if it:
            cand.append((it.start(), "imgt"))
        dv = re.search(r"<div\b", c[i:], re.I)
        if dv and _construct_end(c, i + dv.start()) is not None:
            # only a BALANCED div is a block node; an unbalanced one falls to
            # prose (fail-closed — never bound-to-EOF / swallow).
            cand.append((i + dv.start(), "div"))
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
        elif kind == "imgt":
            en = _match(c, st, "{{", "}}")
            out.append(("imgt", c[st:en]))
        elif kind == "div":
            en = _construct_end(c, st)        # depth-aware, shared matcher
            out.append(("div", c[st:en]))
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
    """Apply body markup, then regularize `<br>` to the canonical «BR» line
    break: figure prose treats `<br>` as a break (the BODY producer renders it as
    a space — different producer, different rule). `<small>`/`<big>` are carried
    by TT itself now (→ «SM»/«LG»). The single place that knows figure `<br>` =
    line break."""
    return re.sub(r"<br\s*/?>", "«BR»", TT(s), flags=re.I)


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
    # The image is a LEAF: filename + display params, nothing else.  The
    # bracket's trailing text on a sized/centred image is `alt`, NOT a caption —
    # MediaWiki never renders it, and there are no "honest captions" living
    # inside an image marker.  We don't render it either; if that leaves a figure
    # captionless, that's the source author's intent.  Every VISIBLE caption is a
    # separate sibling block, recursed on its own (e.g. SUNDEW's {{center|…}}
    # that follows the image — which was being DOUBLED by the old caps-fold here).
    meta = (f"|align={align}" if align else "") + (f"|width={width}" if width else "")
    return f"{{{{IMG:{fn}{meta}}}}}"


def _template_image_marker(raw: str) -> str:
    """Image leaf in TEMPLATE spelling → `{{IMG:…}}`.  `{{raw image|…}}` carries
    a DjVu page-ref (→ local full-page render) or a plain filename plus an
    optional trailing `{{c|cap}}`; `{{img float|…}}` / `{{figure|…}}` / `{{FI|…}}`
    carry named params (file/cap/width/align).  Unlike the bare `[[File:…]]`
    leaf, these templates carry an AUTHOR-DECLARED caption (`cap=` / the `{{c}}`
    block) the EB1911 template renders — a real caption, not alt — so it is
    kept.  Reuses the shared parsers + `build_img_marker` (the leaves that
    survive); the old `_process_image_float`/`_process_raw_image` producers do
    not."""
    from britannica.parsers import img_float as _imgf
    from britannica.pipeline.stages.elements._image import (
        build_img_marker, _RAW_IMAGE_ARG_RE, _RAW_DJVU_REF_RE, _RAW_CAPTION_RE)
    s = raw.strip()
    if re.match(r"\{\{\s*raw\s+image", s, re.I):
        m = _RAW_IMAGE_ARG_RE.match(s)
        if not m:
            return ""
        arg = m.group(1).strip()
        dref = _RAW_DJVU_REF_RE.match(arg)
        filename = (f"djvu_vol{int(dref.group(1)):02d}_page{int(dref.group(2)):04d}.jpg"
                    if dref else arg)
        cap_m = _RAW_CAPTION_RE.search(s, m.end())
        caption = TT(cap_m.group(1).strip()) if cap_m else ""
        return build_img_marker(filename, caption or None)
    inner = s[2:-2] if s.startswith("{{") and s.endswith("}}") else s
    parsed = _imgf.parse(inner)
    if parsed is None:
        return ""
    caption = TT(parsed.caption) if parsed.caption else None
    return build_img_marker(parsed.filename, caption or None,
                            align=parsed.align, width=parsed.width)


_DIV_OPEN_RE = re.compile(r"<div\b([^>]*)>", re.IGNORECASE)


def _div_block_marker(raw: str) -> str:
    """A styled `<div …>` block → carry its FULL style as
    ``«DIV[style:CSS]»…«/DIV»`` (the viewer renders ``<div style="CSS">…</div>``)
    and recurse the content.  The `{{Ts}}` shorthand + inline `style=` + `align=`
    are translated ONCE by the shared `_table_opener_styles` (same parser the
    table opener uses), so every block style — float, centring, text-indent,
    padding, width, font-size, line-height — rides through with no per-property
    mapping and no loss; the `{{Ts}}` is consumed, not swept.  The inner recurses
    to the ground (image → leaf, nested table → table branch, etc.).  Mirrors
    `«HTMLTABLE»` carrying `<table style>`; the viewer is a pure decoder."""
    from britannica.pipeline.stages.elements._tables import _table_opener_styles
    m = _DIV_OPEN_RE.match(raw)
    attrs = m.group(1) if m else ""
    inner = re.sub(r"</div\s*>\s*$", "", raw[m.end():] if m else raw, flags=re.I)
    body = render_markers(inner).strip()
    if not body:
        return ""
    css = ";".join(_table_opener_styles("{|" + attrs))
    return f"«DIV[style:{css}]»{body}«/DIV»" if css else body


def _cell_marker(sep: str, attr: str, content: str) -> str:
    # Carry the cell's FULL source styling via the canonical `produce_cell`
    # (= `_cell_styles` + body-text) — not the four-property `_normalize_attrs`
    # lift, which dropped the `{{Ts|ba}}` → `border:1px` (so bordered figure
    # tables rendered border-less cells) along with padding and the rest.  The
    # cell body recurses to the ground via `render_markers` (images / nested
    # tables / poems become their own markers in source order).
    from britannica.pipeline.stages.elements._table_decompose import produce_cell
    from britannica.pipeline.stages.elements._tables import emit_html_cell
    tag = "th" if sep == "!" else "td"
    styles, body = produce_cell(attr, content, render_markers)
    rs = re.search(r'rowspan\s*=\s*"?(\d+)', attr, re.I)
    cs = re.search(r'colspan\s*=\s*"?(\d+)', attr, re.I)
    return emit_html_cell(
        tag, body, styles=styles,
        rowspan=int(rs.group(1)) if rs else 1,
        colspan=int(cs.group(1)) if cs else 1)


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
        elif kind == "imgt":
            out.append(_template_image_marker(pay))
        elif kind == "div":
            out.append(_div_block_marker(pay))
        else:
            out.append(_tt_br(pay).strip())
    return "\n\n".join(x for x in out if x)


def produce_faithful_figure(raw: str) -> str:
    """Producer entry point: a figure's RAW bytes → marker output. Wired into
    the dispatch as ``lambda raw, inner, tt, ctx, reg: produce_faithful_figure(raw)``."""
    return render_markers(raw)
