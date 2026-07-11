"""Tree-emitter render — HTML directly off the ClassifiedElement tree.

This is ``produce_tree``'s twin (pipeline/stages/elements/_classifier.py): the same
recursive walk, dispatching each node on its label, where ``produce_tree``'s emitter
writes a *marker* and this one writes *HTML*.  A node's children render first and fold
into the parent; nothing re-parses a flattened string.

The flat-body render (``render_paragraph`` + ``decode_inline``) re-derived structure the
walker already knew — a block-scan to re-find blocks, span-match regexes to re-pair
`«FN»`/`«MATH»`/… opens with closes, and per-construct "protect this span" band-aids.
Here there is no flat body: a footnote is a ``REF`` node, a table is ``TABLE``→``ROW``→``TD``,
a footnote inside a cell is a ``REF`` node under a ``TD`` node — walked, never torn.

Ported labels live in ``_RENDER_DISPATCH``; every other label falls back to the current
per-node handling so the port is byte-identical at each step and the span-match regexes
come out one construct at a time (each provably dead once its label is a node).
"""
from __future__ import annotations

import re

from britannica.render.article import (
    RenderContext,  # noqa: F401  (re-exported for callers)
    render_paragraph,
    render_page_markers,
    _render_sh,
    _render_math_markers,
    _TABLE_COLS_RE,
)
from britannica.render.inline import decode_inline, escape_html, render_fn_marker

# Labels that break a paragraph — the tree analog of ``BLOCK_MARKER_SCAN_RE``.  A run of
# consecutive INLINE nodes is one paragraph; a BLOCK node stands alone.  This is a label
# set, not a regex over the stream: the walker already told us what each node is.
_BLOCK_LABELS = {
    "TABLE", "OUTLINE", "PLATE_OUTLINE", "EQN", "TITLE", "VERSE", "LEGEND",
    "CENTER", "HTML_STYLE", "CHART2", "SCORE", "CHEMISTRY_LAYOUT",
}


def _inline_decode(markers: str, ctx) -> str:
    """One inline node's contribution to a paragraph — the current prose path *minus* the
    ``<p>`` wrap.  Position-invariant (escape / token substitution / math), so decoding a
    node's marker in isolation equals decoding it inside the whole run.  This is the
    fallback for inline labels not yet ported."""
    h = escape_html(markers)
    h = render_page_markers(h, ctx)
    h = _render_sh(h)
    h = decode_inline(h, skip_math=True, ctx=ctx)
    h = _render_math_markers(h, ctx)
    return h


def _render_content(ce, ctx) -> str:
    """Render a node's inner content: substitute each child's rendered HTML into the
    node's ``inner_text`` placeholders (recurse the structure).  With BODY-wrap on, the
    text runs are themselves BODY children, so their escaping happens in the child."""
    text = ce.inner_text or ""
    for ph, child in ce.inner_registry.items():
        if ph in text:
            text = text.replace(ph, render_node(child, ctx))
    return text


_FN_NAME_RE = re.compile(r"«FN(?:\[([^\]]+)\])?:")


def _emit_ref(ce, ctx) -> str:
    """A footnote node → its numbered superscript + popup, with the footnote's content
    rendered from its *children* (recurse), not from a `«FN»` span-match.  The numbering /
    collection stays in ``render_fn_marker`` (the one owner); it re-decodes the content,
    which is idempotent on already-rendered HTML.

    A NAMED ref's body is resolved article-wide into ``ref_bodies`` and baked into the
    marker rather than hung on the tree as a child, so when there are no children we take
    the content from the marker's own `«FN»` inner.  (Threading named-ref bodies onto the
    tree as real children is the follow-up that makes even this path pure structure.)"""
    m = _FN_NAME_RE.match(ce.marker or "")
    name = m.group(1) if m else None
    content = _render_content(ce, ctx)
    if not content:
        inner = _FN_NAME_RE.sub("", ce.marker or "", count=1)
        content = re.sub(r"«/FN»\s*$", "", inner)
    return render_fn_marker(name, content, ctx)


# ── TABLE family — pure structure.  The producer already decomposed every table to
# TABLE→ROW→TD→body-text; the render just peels each tag and recurses the children into
# the ONE leaf render.  Attrs ride on each node's own opener («TD[colspan:2|style:…]»),
# the same quote-free payload `_table_open` decodes; `cols` is wide-table metadata, dropped.
_COLS_META_RE = re.compile(r"«COLS:\d+»")
_TAG_OPEN_RE = re.compile(r"^«(?:TABLE|TR|TD|TH)(?:\[([^\]]*)\])?»")


def _tag_attrs(payload: str | None) -> str:
    """`colspan:2|style:text-align:right` → ` colspan="2" style="text-align:right"` (the
    same split `_table_open` does: on `|`, each field on its FIRST `:`; `cols` dropped)."""
    if not payload:
        return ""
    out = ""
    for field in payload.split("|"):
        k, _, v = field.partition(":")
        if k == "cols":
            continue
        out += f' {k}="{v}"'
    return out


def _wrap(ce, tag: str, ctx) -> str:
    m = _TAG_OPEN_RE.match(ce.marker or "")
    return f"<{tag}{_tag_attrs(m.group(1) if m else None)}>{_render_content(ce, ctx)}</{tag}>"


def _emit_row(ce, ctx) -> str:
    return _wrap(ce, "tr", ctx)


def _emit_cell(ce, ctx) -> str:
    return _wrap(ce, "th" if ce.label == "TH" else "td", ctx)


def _emit_caption(ce, ctx) -> str:
    return f"<caption>{_render_content(ce, ctx)}</caption>"


def _emit_table(ce, ctx) -> str:
    # The CAPTION child rides the registry, NOT an inner_text placeholder (the producer
    # prepends it), so render it explicitly first — a <caption> is the table's first child.
    caption = "".join(render_node(c, ctx) for c in ce.inner_registry.values()
                      if c.label == "CAPTION")
    content = _COLS_META_RE.sub("", _render_content(ce, ctx))
    m = _TAG_OPEN_RE.match(ce.marker or "")
    html = f"<table{_tag_attrs(m.group(1) if m else None)}>{caption}{content}</table>"
    cm = _TABLE_COLS_RE.match(ce.marker or "")
    cols = int(cm.group(1)) if cm else 0
    if cols >= 10:
        ctx.wide_table_counter += 1
        html = (f'<figure class="wide-table-wrap"><button class="expand-table-btn" '
                f'data-wt="wt-{ctx.wide_table_counter}" title="Open full-width view">'
                f'⤢ Expand ({cols} columns)</button>'
                f'<div class="wide-table-inline">{html}</div></figure>')
    return html


_RENDER_DISPATCH = {
    "REF": _emit_ref,
    "REF_SELF": _emit_ref,
    "TABLE": _emit_table,
    "ROW": _emit_row,
    "TD": _emit_cell,
    "TH": _emit_cell,
    "CAPTION": _emit_caption,
}


def render_node(ce, ctx) -> str:
    """Render one node: dispatch on label to its emitter (which recurses its children), or
    fall back to the current per-node handling for a label not yet ported."""
    emitter = _RENDER_DISPATCH.get(ce.label)
    if emitter is not None:
        return emitter(ce, ctx)
    if ce.label in _BLOCK_LABELS:
        return render_paragraph(ce.marker, None, ctx)     # current block case, one block
    return _inline_decode(ce.marker, ctx)                 # current inline case, one node


def render_tree(tree, ctx) -> str:
    """Walk the top-level nodes in source order; group consecutive inline nodes into a
    paragraph (``<p>`` — the block-scan's job, done by label instead of by regex) and emit
    block nodes standalone."""
    out: list[str] = []
    para: list[str] = []

    def flush():
        if para:
            joined = "".join(para)
            if joined.strip():
                out.append(f"<p>{joined}</p>")
            para.clear()

    for ph, ce in tree.items():
        if ce.label in _BLOCK_LABELS:
            flush()
            out.append(render_node(ce, ctx))
        else:
            para.append(render_node(ce, ctx))
    flush()
    return "".join(out)
