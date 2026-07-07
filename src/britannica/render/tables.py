"""Table rendering: «HTMLTABLE:<table>…»/«CHEM:…» → decoded HTML.

The producer carries a table as literal HTML with markers in the cells (the "quasi-recursive"
wire format).  We parse it ONCE with html5lib and recurse the outer table's rows→cells,
decoding each cell's markers through the shared inline decoder — cleaner than the viewer's
DOMParser-mutate-serialize, same output.  Nested tables' cells decode too (a cell's whole
inner HTML goes through decode_inline, which leaves the <table>/<td> structure and resolves
the markers inside it).  Page markers in cells hoist to the row's first cell; column count
drives the wide-table wrap.

This is the seam that makes html5lib a RUNTIME dependency of the renderer.  Decomposing the
producer into recursive «TABLE»/«TR»/«TD» markers (a later arc) would remove the need to
parse HTML here and return html5lib to dev-only.
"""
import re

import html5lib
from html5lib.serializer import HTMLSerializer
from html5lib.treewalkers import getTreeWalker

from britannica.render.inline import decode_inline

_WALKER = getTreeWalker("etree")
_PAGE_RE = re.compile("\x01PAGE:(\\d+)\x01")
_CAPTION_RE = re.compile(r"<caption>([\s\S]*?)</caption>")

HTMLTABLE_OPEN, HTMLTABLE_CLOSE = "«HTMLTABLE:", "«/HTMLTABLE»"
CHEM_OPEN, CHEM_CLOSE = "«CHEM:", "«/CHEM»"


def _ser(tokens):
    return HTMLSerializer(quote_attr_values="always", omit_optional_tags=False).render(tokens)


def _serialize(elem):
    return _ser(_WALKER(elem))


def _inner_html(elem):
    """Serialize an element's children (its inner HTML)."""
    toks = list(_WALKER(elem))
    if toks and toks[0]["type"] in ("StartTag", "EmptyTag"):
        toks = toks[1:]
    if toks and toks[-1]["type"] == "EndTag":
        toks = toks[:-1]
    return _ser(iter(toks))


def _parse(html_str):
    return html5lib.parseFragment(html_str, treebuilder="etree", namespaceHTMLElements=False)


def _set_inner_html(elem, html_str):
    frag = _parse(html_str)
    for c in list(elem):
        elem.remove(c)
    elem.text = frag.text
    for c in list(frag):
        elem.append(c)


def _prepend_inner_html(elem, html_str):
    frag = _parse(html_str)
    spans = list(frag)
    if not spans:
        return
    old_children = list(elem)
    old_text = elem.text or ""
    for c in old_children:
        elem.remove(c)
    elem.text = frag.text or ""
    for c in spans:
        elem.append(c)
    spans[-1].tail = (spans[-1].tail or "") + old_text
    for c in old_children:
        elem.append(c)


def _strip_nested_markers(s):
    for m in (HTMLTABLE_OPEN, HTMLTABLE_CLOSE, CHEM_OPEN, CHEM_CLOSE):
        s = s.replace(m, "")
    return s


def _merge_table_class(html, cls):
    """Add `cls` to the FIRST <table>'s class, preserving any class already carried."""
    def repl(m):
        attrs = m.group(1)
        cm = re.search(r'\sclass="([^"]*)"', attrs)
        if cm:
            if cls in cm.group(1).split():
                return m.group(0)
            return "<table" + attrs.replace(cm.group(0), ' class="' + cm.group(1) + " " + cls + '"') + ">"
        return '<table class="' + cls + '"' + attrs + ">"
    return re.sub(r"<table\b([^>]*)>", repl, html, count=1)


def _find_outer_table(frag, outer_class):
    first = None
    for elem in frag.iter("table"):
        if first is None:
            first = elem
        if outer_class in (elem.get("class") or "").split():
            return elem
    return first


def _table_rows(table):
    """The table's own <tr> in document order, excluding rows of nested tables."""
    rows = []

    def walk(elem, nested):
        for child in elem:
            if child.tag == "table":
                walk(child, True)
            elif child.tag == "tr":
                if not nested:
                    rows.append(child)
                walk(child, nested)
            else:
                walk(child, nested)

    walk(table, False)
    return rows


def _make_page_span(pg, ctx):
    unproofed = pg in ctx.unproofed_pages
    cls = "page-marker unproofed" if unproofed else "page-marker"
    title = (f"Volume {ctx.volume}, page {pg} (unproofed source) — click to view scan"
             if unproofed else f"Volume {ctx.volume}, page {pg} — click to view scan")
    return (f'<a class="{cls}" data-page="{pg}" title="{title}" '
            f'href="{ctx.scan_url}&pinit={pg}">{ctx.volume}:{pg}</a>')


def render_table(inner, is_chem, ctx):
    """Render a table's inner HTML (markers decoded) → (html, max_cols)."""
    outer_class = "chem-grid" if is_chem else "data-table"
    inner = _strip_nested_markers(inner)          # nested tables → bare <table>
    if is_chem:
        inner = _merge_table_class(inner, "chem-grid")
    # Captions decode with escape (their content is raw text, unlike cell HTML).
    inner = _CAPTION_RE.sub(
        lambda m: "<caption>" + decode_inline(m.group(1), escape=True, dhr_inline=True, ctx=ctx) + "</caption>",
        inner)

    frag = _parse(inner)
    outer = _find_outer_table(frag, outer_class)
    if outer is None:
        return inner, 0

    max_cols = 0
    for tr in _table_rows(outer):
        page_markers = []
        cells = [c for c in tr if c.tag in ("td", "th")]
        row_cols = 0
        for cell in cells:
            cs = cell.get("colspan")
            row_cols += int(cs) if (cs and cs.isdigit()) else 1
            ci = _inner_html(cell)
            page_markers.extend(_PAGE_RE.findall(ci))
            ci = _PAGE_RE.sub("", ci)
            _set_inner_html(cell, decode_inline(ci, dhr_inline=True, ctx=ctx))
        if row_cols > max_cols:
            max_cols = row_cols
        if page_markers and cells:
            _prepend_inner_html(cells[0], "".join(_make_page_span(pg, ctx) for pg in page_markers))

    return _serialize(outer), max_cols
