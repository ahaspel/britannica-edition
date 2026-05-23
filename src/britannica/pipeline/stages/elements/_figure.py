"""Structural figure-span recognition for the walker.

A figure in EB1911 source is an image followed by *structurally delimited*
caption material — never bare prose (see [[loose-legend-no-bare]]).
``figure_tail_end`` reports how far that caption material runs so the walker can
break the figure (image + caption) as one unit, stopping at the first unmarked
prose block.

The signal is the source's template vocabulary, recognized in RAW wikitext (the
walker runs pre-production, so emphasis is already `«I»`/`«B»` but ``{{sc}}`` /
``{{center}}`` / ``{{EB1911 Fine Print}}`` are still raw).  Nothing here
classifies prose — body text matches no opener and ends the run.

Scope note: gated against the over-absorption the corpus span audit found —
the paired ``{{EB1911 fine print/s}}…/e}}`` wrapper is small-type BODY, not a
legend, and ``{|`` / ``<table>`` legend tables are left as sibling elements for
now (grouping them with the image is a later step).
"""
from __future__ import annotations

import re

# Templates that MAY wrap figure caption material — absorbed only when they
# contain a caption signal inside.  `{{EB1911 Fine Print|…}}` and `{{fine
# block|…}}` are used for small-type BODY too (SUNSHINE "Adjustments.—…",
# DUNBAR source notes), and `{{center|«I»Stratigraphy«/I»}}` is a heading — so
# the same caption-signal gate applies to every template, fine-print included.
_TMPL = re.compile(
    r"\{\{\s*(?:center|block\s*center|c|EB1911\s+Fine\s+Print|Fine\s*block|"
    r"Fs|fs\d*|sm|smaller|em|gap|dhr|Hi)\b",
    re.IGNORECASE)
# Caption signal: an `{{sc|Fig}}`/`{{sc|Plate}}` marker or a `(From …`/
# `(After …` source citation.  Deliberately NOT a bare "fig" (body says "in
# fig. 31") and NOT an image — in TAIL context an image opens a *new* figure,
# not caption material (that's the wrapper entry's job).
_CAP_SIGNAL = re.compile(
    r"\{\{\s*(?:c?sc|small-caps)\s*\|\s*(?:Figs?|Plate)"
    r"|<poem\b"
    r"|\(\s*(?:From|After)\b",
    re.IGNORECASE)
# The figure-number → em-dash tail that distinguishes a caption (`Fig. 6.—…`)
# from a body paragraph that merely *starts* with a label (`Fig. 6. The
# simplest instance…`).  The em/en-dash must follow the number(s) directly
# (allowing ranges/lists `1, 2`, `6 and 7`, `1–6`), with only `.`/space
# between — never arbitrary prose.
_CAP_HEAD_TAIL = (
    r"[.\s]*[\dIVXLC]+(?:\s*(?:,|&|and|to|–|-)\s*[\dIVXLC]+)*[.\s]*[—–]")
# A caption LINE led by a small-caps Fig/Plate template — the template wraps
# only `Fig.`; the number + em-dash trails it (`{{sc|Fig}}. 11.—Crystals…`).
_LINE_CAP = re.compile(
    r"\{\{\s*(?:c?sc|small-caps)\s*\|\s*(?:Figs?|Plate)[^\n}]*\}\}"
    + _CAP_HEAD_TAIL, re.IGNORECASE)
# A bare caption line: `Fig. 3.—…`, `Figs. 1–6.—…`.
_BARE_FIG = re.compile(
    r"(?:Figs?|Plate)s?\b" + _CAP_HEAD_TAIL, re.IGNORECASE)
# A parenthesized attribution citation — case-SENSITIVE `(From`/`(After`: the
# lowercase `(from Greek …)` etymology form (ANOMALY) is body, not attribution.
_ATTRIB = re.compile(
    r"\(\s*(?:From|After|Photo|Copyright|Redrawn|Reproduced|Drawn|"
    r"By\s+permission)\b")
# An italic-label legend paragraph: a SHORT typographic label then a COMMA then
# text (`«I»a«/I», External aspect`, `«I»st.c«/I», Cavity…`).  The comma is the
# legend form; a body lettered item uses a period (`«I»d«/I». «I»Opus sectile«/I»,
# a species of marqueterie…` — MOSAIC), so requiring the comma keeps body out.
# A bare `21. Method…` has no italic marker (body); a shoulder heading is
# `«I»Climate«/I».—…` (long label + period/em-dash) — both excluded.
_ITALIC_LABEL = re.compile(
    r"«I»\s*[A-Za-z0-9][A-Za-z0-9.,&\- ]{0,6}«/I»\s*,\s+\S")
# A verse legend (`<poem>…</poem>`) after the image.
_POEM = re.compile(r"<poem\b", re.IGNORECASE)
_POEM_END = re.compile(r"</poem\s*>", re.IGNORECASE)
_PAGE = re.compile(r"[\x01-\x08]PAGE:\d+[\x01-\x08]")
_SEP = re.compile(r"(?:<br\s*/?>|[ \t\r\n])*")


def _balanced_brace_end(text: str, start: int) -> int | None:
    """End position just past the ``}}`` matching the ``{{`` at ``start``."""
    if text[start:start + 2] != "{{":
        return None
    depth = 0
    i = start
    n = len(text)
    while i < n - 1:
        two = text[i:i + 2]
        if two == "{{":
            depth += 1
            i += 2
        elif two == "}}":
            depth -= 1
            i += 2
            if depth == 0:
                return i
        else:
            i += 1
    return None


def _paren_end(text: str, start: int) -> int | None:
    """End just past the ``)`` matching the ``(`` at ``start``; None if
    unbalanced or it would cross a paragraph break.  Keeps an attribution
    citation `(From …, by permission.)` to its own parentheses instead of
    running to the paragraph end and swallowing following body."""
    depth = 0
    i = start
    n = len(text)
    while i < n:
        c = text[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i + 1
        elif c == "\n" and i + 1 < n and text[i + 1] == "\n":
            return None
        i += 1
    return None


def _match_material(text: str, pos: int) -> tuple[int | None, bool]:
    """If a figure-material unit starts at ``pos``, return ``(end, is_caption)``;
    else ``(None, False)``.  ``is_caption`` is False for a bare attribution
    citation — an attribution alone (no caption) does not make a figure.

    A unit is a balanced caption template, a layout template that *contains* a
    caption signal, a single `Fig. N.—…` caption line, or a parenthesized
    attribution.  Prose (no opener match) returns None — the run stops there.

    Deliberately NOT figure material: the paired ``{{EB1911 fine print/s}}…/e}}``
    wrapper (small-type BODY sections, not legends) and bare ``{|`` / ``<table>``
    legend tables (left as sibling elements for now) — both caused large body
    over-absorption in the corpus span audit.
    """
    rest = text[pos:]
    # Any caption-bearing template — absorbed only when a caption signal sits
    # inside the balanced block (else it's a body note / section heading).
    if _TMPL.match(rest):
        e = _balanced_brace_end(text, pos)
        if e is not None and _CAP_SIGNAL.search(text, pos, e):
            return e, True
        return None, False
    # A caption (`{{sc|Fig}} N.—…` / bare `Fig. N.—…`): absorb the whole caption
    # PARAGRAPH (to the blank-line break), so a caption wrapped across source
    # lines (`…System for␤Ventilating Tunnels.`) stays whole.
    if _LINE_CAP.match(rest) or _BARE_FIG.match(rest):
        pp = text.find("\n\n", pos)
        return (pp if pp >= 0 else len(text)), True
    # An italic-label legend paragraph (`«I»a«/I», text`): absorb the paragraph.
    if _ITALIC_LABEL.match(rest):
        pp = text.find("\n\n", pos)
        return (pp if pp >= 0 else len(text)), True
    # A verse legend (`<poem>…</poem>`): absorb the balanced block.
    if _POEM.match(rest):
        c = _POEM_END.search(text, pos)
        if c is not None:
            return c.end(), True
        return None, False
    # A parenthesized attribution citation: absorb only its own `(...)`, not the
    # rest of the paragraph (a following body sentence must not come along).
    if _ATTRIB.match(rest):
        return _paren_end(text, pos), False
    return None, False


# A wrapper template that, when it encloses an image, IS the figure unit.
_WRAP_OPEN = re.compile(r"\{\{\s*(?:center|block\s*center)\s*\|", re.IGNORECASE)
# An image opener (bracket or float template) — used to confirm a wrapper
# actually encloses a figure.
_IMG_IN = re.compile(
    r"\[\[(?:File|Image):|\{\{\s*(?:img\s*float|figure|FI)\b", re.IGNORECASE)


def figure_wrapper_end(text: str, pos: int) -> int | None:
    """If a ``{{center|…}}`` / ``{{block center|…}}`` wrapper at ``pos``
    encloses an image, return the end of the figure unit (the balanced wrapper
    plus any trailing caption/legend run); else None.

    This is the entry point for figures whose image sits INSIDE the wrapper
    (CALCITE, many BRIDGES) — recognizing the wrapper as the unit keeps the
    caption that lives inside it intact and never spills past its ``}}``.
    """
    if not _WRAP_OPEN.match(text, pos):
        return None
    end = _balanced_brace_end(text, pos)
    if end is None:
        return None
    if _IMG_IN.search(text, pos, end) is None:
        return None
    return figure_tail_end(text, end)


def figure_tail_end(text: str, img_end: int) -> int:
    """Given an image whose own extract ends at ``img_end``, return the end of
    the figure unit after absorbing the trailing structural caption/legend run.

    Returns ``img_end`` unchanged when nothing structural follows (a plain
    image — the body that follows is left alone), OR when the run is attribution
    ONLY with no actual caption (an image whose tail is just `(After X.)` is left
    for the post-pass, matching baseline, rather than splitting the attribution
    off a caption the recognizer can't see).  Stops at the first unmarked prose
    block, a page-break sentinel, or a following image.
    """
    pos = img_end
    end = img_end
    saw_caption = False
    n = len(text)
    while pos < n:
        sep = _SEP.match(text, pos)
        sep_text = text[pos:sep.end()]
        if _PAGE.search(sep_text):
            break  # never cross a page boundary into column-interleaved body
        scan = sep.end()
        unit, is_caption = _match_material(text, scan)
        if unit is None or unit <= scan:
            break
        end = unit
        if is_caption:
            saw_caption = True
        pos = unit
    return end if saw_caption else img_end
