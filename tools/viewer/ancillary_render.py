"""Ancillary wikitext → HTML through the ONE pipeline.

The preface / ancillary page builders each grew a private regex chain —
noinclude strip, template unwrappers, a catch-all `{{…}}` strip, a paired
`«B»(.*?)«/B»`-style marker decoder — a parallel mini-pipeline per page
(sweeper-campaign item K1).  This module replaces every one of those chains
with the same three calls the corpus itself goes through:

    stream_with_keys  →  process_elements  →  decode_inline

so ancillary pages get the walker's full recognition (templates, refs,
links, shoulder headings, hyphenation seams) and the renderer's one
grammar, and a construct the pipeline learns is learned here for free.

"Ancillary handling separate from the article pipeline" still holds: no DB,
no article rows — the pipeline pieces are functions, and this calls them.

Render target is "epub" — the no-JS render: footnote superscripts are plain
`<a href="#fn-N">` noterefs (the assembled Notes list is the popup-free
delivery), while links keep the site policy (`epub_bundled=None`).

«AL» author references are baked HERE (the page's own policy: a link into
the contributors index), through THE «AL» reader — after decode, so the
display's inner markers are already HTML and the bake only wraps.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import NamedTuple
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from britannica.markers import markers_to_text, sub_al_markers, sub_ln_markers
from britannica.pipeline.stages.elements import process_elements
from britannica.pipeline.stages.elements._context import ElementContext
from britannica.pipeline.stages.preprocess import stream_with_keys
from britannica.render.article import RenderContext
from britannica.render.inline import decode_inline, format_footnote_text

# The producer's shoulder-heading wire form, read for the TOC — a
# whole-document COLLECTION pass over the marker stream (the sections.py
# model).  THE regex is the render's own `_SH_RE` (one owner), so the TOC
# reads exactly the spans `_render_sh` will anchor as `id="section-{slug}"`.
from britannica.render.article import _SH_RE as _SH_TOC_RE

# A document-title block the page header already shows: a leading «CTR»
# whose text is set at xxx-larger (the print's own masthead line).
_LEADING_TITLE_RE = re.compile(r"^\s*«CTR».*?«/CTR»\s*", re.DOTALL)


class AncillaryDoc(NamedTuple):
    body_html: str
    toc: list                  # [(anchor id, label)]
    footnotes: list            # [(number, body html)]


def render_pages(raw_pages: list, volume: int,
                 drop_leading_title: bool = False) -> AncillaryDoc:
    """``[(page_number, corrected_raw_wikitext)]`` pairs → the rendered document.

    The caller owns page selection and corrections (they are per-page,
    applied before the seam-joining stream build) and the page shell; this
    owns everything between raw wikitext and body HTML.
    """
    pages = [SimpleNamespace(wikitext=raw, page_number=n)
             for n, raw in raw_pages]
    stream, _page_keys, _sec_keys = stream_with_keys(pages, volume=volume)
    marked = process_elements(stream, ElementContext(volume=volume))

    if drop_leading_title:
        marked = _LEADING_TITLE_RE.sub("", marked, count=1)

    # These pages skip the article bake (no corpus resolver), so an interwiki
    # `[[w:…]]` reference would fall through to the renderer's site-search
    # fallback — a search for "w:Herbert Spencer" answers nothing.  The bake
    # strips interwiki for articles; the page policy here is the link the
    # source meant: Wikipedia, as an «XL» the renderer decodes mechanically.
    src = marked

    def _interwiki(m):
        t = m.target.strip()
        if t.lower().startswith("w:"):
            page = quote(t[2:].strip().replace(" ", "_"))
            return (f"«XL:https://en.wikipedia.org/wiki/{page}"
                    f"|{m.display}«/XL»")
        return src[m.start:m.end]
    marked = sub_ln_markers(src, _interwiki)

    toc = [(f"section-{slug}", markers_to_text(content).strip().rstrip("."))
           for slug, content in _SH_TOC_RE.findall(marked)]

    ctx = RenderContext(volume=volume, scan_url=None, unproofed_pages=set(),
                        target="epub")
    html = decode_inline(marked, escape=True, body_blocks=True, ctx=ctx)

    def _author_link(m):
        # Page policy for an «AL» reference: link the person into the
        # contributors index by their full (target) name.  The display's
        # inner markers are already decoded — this only wraps.
        return (f'<a href="/contributors.html?q={quote(m.target.strip())}">'
                f'{m.display}</a>')
    html = sub_al_markers(html, _author_link)

    footnotes = [(fn["num"], format_footnote_text(fn["text"], ctx))
                 for fn in ctx.collected_footnotes]
    return AncillaryDoc(html, toc, footnotes)


def footnotes_html(footnotes: list) -> str:
    """The assembled Notes list — the delivery for the no-JS noteref sups
    the render emits (`<a href="#fn-N">`); each note's back-link returns to
    its `fnref-N` anchor.  ONE owner for the markup both page builders ship."""
    if not footnotes:
        return ""
    items = "".join(
        f'<li id="fn-{n}" value="{n}">'
        f'<a href="#fnref-{n}">{n}.</a> {body}</li>'
        for n, body in footnotes)
    return f'<div class="footnotes"><h3>Notes</h3><ol>{items}</ol></div>'
