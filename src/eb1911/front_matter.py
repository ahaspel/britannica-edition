"""EB1911's pages beyond its articles — its ``Corpus.ancillary`` hook.

The Introduction group, in book order after the title page (the user's TOC
spec):

  * ``introduction.xhtml`` — the editor's own introduction, "To This Edition",
    from ``docs/introduction.txt`` (plain-text notation; omitted while empty).
  * ``preface.xhtml`` — the 1910 Editorial Preface, extracted from the static site
    page ``tools/viewer/preface.html`` (built once from raw Wikisource by
    ``tools/viewer/build_preface.py``; frozen content).
  * ``historical-preface.xhtml`` — the Prefatory Note, the 1910 history of the
    Britannica's editions, from ``tools/viewer/ancillary-prefatory-note.html``.

The vol-29 Preface to the Index is OUT (user: the book's own indices supersede
it).  Then the guide: the Reader's Guide (``readers_guide``).

Moved out of the engine's epub/front_matter.py (wikikit step 5); the extraction
itself stays there.
"""
import os
from pathlib import Path

from eb1911 import readers_guide
from wikikit.epub.front_matter import ROOT, Ancillary, _extract, text_page_html

_VIEWER = os.path.join(ROOT, "tools", "viewer")
_INTRODUCTION = os.path.join(ROOT, "docs", "introduction.txt")
_PREFACE = os.path.join(_VIEWER, "preface.html")
_PREFATORY_NOTE = os.path.join(_VIEWER, "ancillary-prefatory-note.html")


def introduction_html():
    """The editor's own introduction, or None while it is not yet written."""
    return text_page_html(_INTRODUCTION, "To This Edition")


def preface_html():
    body = _extract(_PREFACE, "preface-body")
    return ("<h1>Editorial Preface</h1>"
            '<p class="fm-meta"><i>By Hugh Chisholm · London, December 10, 1910</i></p>'
            + body)


def historical_preface_html():
    """The Prefatory Note — the 1910 history of the Britannica's editions."""
    body = _extract(_PREFATORY_NOTE, "body")
    return "<h1>Historical Preface</h1>" + body


def pages():
    """[(fname, nav title, body HTML)] — the Introduction group's children, in
    book order; the editor's own piece only when written."""
    out = []
    intro = introduction_html()
    if intro:
        out.append(("introduction.xhtml", "To This Edition", intro))
    out.append(("preface.xhtml", "Editorial Preface", preface_html()))
    out.append(("historical-preface.xhtml", "Historical Preface",
                historical_preface_html()))
    return out


def ancillary() -> Ancillary:
    front = pages()
    guide, images = readers_guide.pages()
    sources = ([Path(_INTRODUCTION)]
               + sorted(Path(_VIEWER).glob("readers-guide*.html"))
               + [Path(_PREFACE), Path(_PREFATORY_NOTE)])
    return Ancillary(front=front, guide=guide, images=images, sources=sources)
