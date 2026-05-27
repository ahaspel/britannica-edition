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
legend.  ``{|`` wikitables directly under an image (no ``\n\n`` separator)
ARE absorbed as legend tables: a corpus check found 25 such instances,
uniformly legend-shaped (short labels + descriptions, caption-style ``Ts``
classes).  HTML ``<table>`` legends remain sibling elements (no current
corpus evidence demands inclusion).
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
# RELAXED caption signals — used ONLY in the tight-after-image position
# (image directly followed by `<br>`, single `\n`, or whitespace — anything
# WITHOUT a blank-line break).  Body small-type uses `\n\n` to separate
# itself from any preceding content, so the absence of `\n\n` between an
# image and the next unit IS the caption-position signal — and that lets
# us accept caption-bearing content that the strict signal would reject:
# the bare numbered captions (`{{Fs|92%|Fig. 10.}}`, `{{sc|Fig. 13.}}`,
# `Fig. 4. Fig. 5. Fig. 6`), AND the bare fine-print or italicized name
# (RORQUAL: `{{c|{{EB1911 fine print|Common Rorqual («I»Balaenoptera
# musculus«/I»).}}}}`).  NEVER applied in mid-run position, so a body
# sentence opening `Fig. 6. The simplest…` or a SUNSHINE-style
# `{{EB1911 Fine Print|Adjustments.—…}}` body annotation (always
# `\n\n`-separated from its surroundings) is untouched.
_CAP_SIGNAL_RELAXED = re.compile(
    r"\{\{\s*(?:c?sc|small-caps)\s*\|\s*(?:Figs?|Plate)"
    r"|<poem\b"
    r"|\(\s*(?:From|After)\b"
    r"|\b(?:Figs?|Plate)s?\.?\s*\d"
    r"|\{\{\s*(?:EB1911\s+fine\s+print|fine\s*block)\s*\|",
    re.IGNORECASE)
# A small-caps caption template carrying the number INSIDE it
# (`{{sc|Fig. 13.}}`) — `sc` is not a layout template (not in `_TMPL`) and the
# number sits inside, so neither the `_TMPL` nor the `_LINE_CAP` path sees it.
_SC_FIG = re.compile(
    r"\{\{\s*(?:c?sc|small-caps)\s*\|[^{}]*(?:Figs?|Plate)s?\.?\s*\d",
    re.IGNORECASE)
# A bare numbered caption with no em-dash (`Fig. 13.`, `Plate II.`).
_BARE_FIG_RELAXED = re.compile(
    r"(?:Figs?|Plate)s?\.?\s*[\dIVXLC]", re.IGNORECASE)
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
# Separator between an image and its caption material: `<br>`, ordinary or
# Unicode whitespace (`\s` is Unicode-aware), and HTML space entities.  The
# Unicode/entity coverage matters because a `{{center|…}}` wrapper unwrapped
# upstream can leave a bare ` `/`&emsp;`/`&nbsp;` sitting between the
# image and its caption — without consuming it the caption is unreachable and
# the figure decays to a bare image (ACCUMULATOR Figs 8, 9).
# Pure spacer templates ({{em|N}}, {{gap}}, {{dhr}}) are separators too — a
# {{em|3}} between the <br> and the caption is layout spacing, not a caption
# wrapper (left in _TMPL an empty one halts the run and orphans the caption,
# ACCUMULATOR Fig 3).  Content-bearing forms still route via _TMPL.
_SEP = re.compile(
    r"(?:<br\s*/?>"
    r"|&(?:nbsp|ensp|emsp|thinsp);"
    r"|&#(?:160|8194|8195|8201|8202);"
    r"|\{\{\s*(?:em(?:\s*\|\s*\d+)?|gap(?:\s*\|[^{}]*)?|dhr)\s*\}\}"
    r"|\s)*",
    re.IGNORECASE)


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


# A `{|…|}` wikitable directly under an image is uniformly a legend table
# in the corpus (25/25 instances examined: LEMON, MILLIPEDE, MYRTLE, NIAGARA,
# PARASITIC DISEASES, OIL ENGINE, PANSY, PLANKTON, PRIMULACEAE×2, PROBOSCIDEA,
# RIVER ENGINEERING, SAGO, SCROPHULARIACEAE, SHIP×2, THEATRE, TRUFFLE, ALGAE×4,
# ANDES, MODERN, PLATE_VOL12).  All carry caption-style `Ts` classes
# (`ma`/`mc`/`sm92`/`lh…`) and short-label content.  A sibling DATA table
# always has a `\n\n` paragraph break separating it from preceding content,
# so gating on the tight-after-image position excludes them structurally.
_WIKITABLE_OPEN = re.compile(r"\{\|")


def _wikitable_end(text: str, start: int) -> int | None:
    """End just past the ``|}`` matching the ``{|`` at ``start``; None if
    unbalanced.  Tracks ``{|`` nesting so a wikitable containing another
    wikitable (rare but legal) closes at the outer ``|}``."""
    if text[start:start + 2] != "{|":
        return None
    depth = 1
    i = start + 2
    n = len(text)
    while i < n - 1:
        two = text[i:i + 2]
        if two == "{|":
            depth += 1
            i += 2
        elif two == "|}":
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


def _caption_paragraph_end(text: str, pos: int) -> int:
    """End of a caption/legend paragraph starting at ``pos``: the next blank
    line, but never crossing a ``PAGE`` marker.  A caption is sometimes only
    a single ``\\n`` from the following body (the blank-line break sits a
    paragraph too far), and when a page/column boundary falls in that gap the
    naive ``\\n\\n`` scan swallows the body into the caption (STEAM_ENGINE
    Fig 60).  Capping at the PAGE marker mirrors the run-level rule that a
    figure never crosses a page boundary into column-interleaved body."""
    pp = text.find("\n\n", pos)
    end = pp if pp >= 0 else len(text)
    pg = _PAGE.search(text, pos)
    if pg is not None and pg.start() < end:
        end = pg.start()
    return end


def _match_material(
    text: str, pos: int, tail_after_br: bool = False,
) -> tuple[int | None, bool]:
    """If a figure-material unit starts at ``pos``, return ``(end, is_caption)``;
    else ``(None, False)``.  ``is_caption`` is False for a bare attribution
    citation — an attribution alone (no caption) does not make a figure.

    A unit is a balanced caption template, a layout template that *contains* a
    caption signal, a single `Fig. N.—…` caption line, or a parenthesized
    attribution.  Prose (no opener match) returns None — the run stops there.

    ``tail_after_br`` is True for the FIRST unit when the image is directly
    followed by ``<br>`` (the caption-below-image position).  There a caption
    needs no `{{sc|Fig}}` marker and no em-dash — the `<br>` under the image is
    itself the signal — so bare numbered captions are accepted.  Never set
    mid-run, so a body sentence opening `Fig. 6. The simplest…` stays body.

    Deliberately NOT figure material: the paired ``{{EB1911 fine print/s}}…/e}}``
    wrapper (small-type BODY sections, not legends).  Bare ``{|…|}`` wikitables
    in the tight-after-image position ARE absorbed (legend tables — see the
    ``_WIKITABLE_OPEN`` note); HTML ``<table>`` legends remain sibling.
    """
    rest = text[pos:]
    # Any caption-bearing template — absorbed only when a caption signal sits
    # inside the balanced block (else it's a body note / section heading).
    # A template that itself ENCLOSES an image is a self-contained sibling
    # figure (e.g. ``{{center|[[File:Fig 31]]<br>{{sc|Fig}}. 31.…}}`` directly
    # after ``{{center|[[File:Fig 30]]<br>{{sc|Fig}}. 30.…}}`` in STEAM_ENGINE);
    # leave it for the walker's next match, NOT as our caption tail material.
    if _TMPL.match(rest):
        e = _balanced_brace_end(text, pos)
        if e is None:
            return None, False
        if _IMG_IN.search(text, pos, e):
            return None, False
        if _CAP_SIGNAL.search(text, pos, e):
            return e, True
        if tail_after_br and _CAP_SIGNAL_RELAXED.search(text, pos, e):
            return e, True
        return None, False
    # A caption (`{{sc|Fig}} N.—…` / bare `Fig. N.—…`): absorb the whole caption
    # PARAGRAPH (to the blank-line break), so a caption wrapped across source
    # lines (`…System for␤Ventilating Tunnels.`) stays whole.
    if _LINE_CAP.match(rest) or _BARE_FIG.match(rest):
        return _caption_paragraph_end(text, pos), True
    # Bare numbered caption directly beneath the image (`{{sc|Fig. 13.}}`,
    # `{{Fs|…Fig. 10.}}` handled above, plain `Fig. 4. Fig. 5. Fig. 6`).
    if tail_after_br and (_SC_FIG.match(rest) or _BARE_FIG_RELAXED.match(rest)):
        return _caption_paragraph_end(text, pos), True
    # An italic-label legend paragraph (`«I»a«/I», text`): absorb the paragraph.
    if _ITALIC_LABEL.match(rest):
        return _caption_paragraph_end(text, pos), True
    # A `{|…|}` wikitable directly under the image: legend table.  Gated to
    # the tight-after-image position — a wikitable separated by ``\n\n`` is a
    # sibling data table.  Corpus-verified uniform legend shape (see
    # ``_WIKITABLE_OPEN`` note above).
    if tail_after_br and _WIKITABLE_OPEN.match(rest):
        e = _wikitable_end(text, pos)
        if e is not None:
            return e, True
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
# A wrapper template that, when it encloses an image, IS the figure unit.
# Includes small-caps wrappers (`{{csc|[[File:…]]<br>Fig. N.}}` — ACCUMULATOR
# Fig 20): around a whole figure the small-caps is just caption styling, so the
# wrapper is the figure unit (gated on `_IMG_IN` — must contain an image).
_WRAP_OPEN = re.compile(
    r"\{\{\s*(?:center|block\s*center|c?sc|small-caps)\s*\|", re.IGNORECASE)
# An image opener (bracket or float template) — used to confirm a wrapper
# actually encloses a figure.  `{{raw image|…}}` deliberately NOT included
# here: ``_process_prose_figure``'s ``_PROSE_FIG_IMG_RE`` only matches
# bracket syntax, so a wrapper whose only image is ``{{raw image|…}}``
# (WELDING-style ``<div style="float:left">{{raw image|…}}…</div>``)
# recognises as a figure but produces empty output.  Raw image lives on
# the separate DOUBLE_BRACE walker path (``_RAW_IMAGE_RE``) for now.
_IMG_IN = re.compile(
    r"\[\[(?:File|Image):|\{\{\s*(?:img\s*float|figure|FI)\b", re.IGNORECASE)
# HTML float-wrapper opener: ``<span/div style="...float: left|right..."``
# enclosing an image + caption.  EB1911's standard floating-figure markup
# (WATERBUCK, VOLTMETER, YAM, SUMACH, WELDING, …; ~150 corpus instances).
# Parallel to ``_WRAP_OPEN`` but for HTML wrappers — the closed wrapper
# bounds caption absorption, so bare-prose captions ("Waterbuck.") under
# ``<br>`` are safe to fold in.
_HTML_WRAP_OPEN = re.compile(
    r"<(?P<tag>span|div)\b[^>]*\bfloat\s*:[^>]*>", re.IGNORECASE)


def figure_wrapper_end(text: str, pos: int) -> int | None:
    """If a ``{{center|…}}`` / ``{{block center|…}}`` / ``{{csc|…}}``
    wrapper at ``pos`` encloses BOTH an image AND a structural caption
    signal (``{{sc|Fig|Plate}}`` / ``Fig. N.—`` / ``(From|After)`` /
    ``<poem>``), return the end of the figure unit (the balanced wrapper
    plus any trailing caption/legend run); else None.

    The dual gate is what keeps generic centering wrappers OFF the figure
    path: ``{{center|«I»Symbols of Ogam Alphabet.«/I»<br>[[File:…]]}}``
    (ALPHABET) has an image but no structural caption signal — it's a
    layout-positioning wrapper, not a figure; let the body-text layout-
    unwrap handle it.  ``{{center|[[File:Fig22]] [[File:Fig23]]<br>
    {{sc|Fig.}} 22.{{sc|Fig.}} 23.}}`` (ACCUMULATOR Figs 22-23) has BOTH
    — image and ``{{sc|Fig.}}`` caption marker — and IS a figure.
    """
    if not _WRAP_OPEN.match(text, pos):
        return None
    end = _balanced_brace_end(text, pos)
    if end is None:
        return None
    if _IMG_IN.search(text, pos, end) is None:
        return None
    if _CAP_SIGNAL_RELAXED.search(text, pos, end) is None:
        return None
    return figure_tail_end(text, end, post_wrapper=True)


def html_float_figure_end(text: str, pos: int) -> int | None:
    """If a ``<span/div style="...float: left|right...">…</…>`` HTML
    wrapper at ``pos`` encloses an image, return the end of the closing
    tag; else None.

    Unlike ``figure_wrapper_end``, NO caption-signal gate: the wrapper
    boundary itself is closed (HTML tags pair structurally), so bare-prose
    captions under ``<br>`` are safe to fold in — the close tag bounds the
    absorption.  WATERBUCK ``<span style="float: right">[[Image:…]]<br />
    Waterbuck.</span>`` is the canonical case; the wrapper IS the figure
    signal (you don't write ``style="float: right"`` around prose).
    """
    m = _HTML_WRAP_OPEN.match(text, pos)
    if m is None:
        return None
    tag = m.group("tag").lower()
    # Match the FIRST closing tag — corpus float wrappers are non-nested.
    close = re.search(rf"</{tag}\s*>", text[m.end():], re.IGNORECASE)
    if close is None:
        return None
    inner_start = m.end()
    inner_end = inner_start + close.start()
    if _IMG_IN.search(text, inner_start, inner_end) is None:
        return None
    return inner_start + close.end()


def figure_tail_end(text: str, img_end: int, post_wrapper: bool = False) -> int:
    """Given an image whose own extract ends at ``img_end``, return the end of
    the figure unit after absorbing the trailing structural caption/legend run.

    Returns ``img_end`` unchanged when nothing structural follows (a plain
    image — the body that follows is left alone), OR when the run is attribution
    ONLY with no actual caption (an image whose tail is just `(After X.)` is left
    for the post-pass, matching baseline, rather than splitting the attribution
    off a caption the recognizer can't see).  Stops at the first unmarked prose
    block, a page-break sentinel, or a following image.

    ``post_wrapper`` is True when called from ``figure_wrapper_end`` — the
    wrapper already absorbed the caption(s), so anything that follows is
    post-figure content.  We still scan for strict signals (a trailing
    ``<poem>`` legend or ``(From …)`` attribution that the wrapper didn't
    enclose), but RELAXED signals stay off — otherwise a body paragraph
    starting "Figs. 62 and 63 are sections…" after a ``{{center|…}}``
    wrapper figure gets pulled in as caption material.
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
        # The FIRST unit, when the image is in the caption-below-image
        # position — directly followed by `<br>` OR by only single-line
        # whitespace (no blank-line break) — relaxes the caption signal
        # requirements: a body-text small-type block uses `\n\n` to
        # separate itself, so the absence of `\n\n` between image and
        # the next unit IS the caption-position signal.  Suppressed when
        # called post-wrapper (the wrapper already absorbed its captions).
        tight_after_image = (not saw_caption
                              and not post_wrapper
                              and "\n\n" not in sep_text)
        unit, is_caption = _match_material(text, scan, tight_after_image)
        if unit is None or unit <= scan:
            break
        end = unit
        if is_caption:
            saw_caption = True
        pos = unit
    return end if saw_caption else img_end
