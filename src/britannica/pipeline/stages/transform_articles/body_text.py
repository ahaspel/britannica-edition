"""Body-text transformation pipeline.

The 12-step ordered sequence that turns raw wikitext (with embedded
markers from cleaning) into the canonical marker form the viewer
renders.  Each function is a pure ``text → text`` transformation;
``_transform_body_text`` composes them.

Order matters — see ``_transform_body_text`` for the canonical sequence.
"""

from __future__ import annotations

import re

from britannica.cleaners.unicode import (
    normalize_unicode,
    replace_print_artifacts,
)
from britannica.markers import RENDERED_MARKER_OPENS


# Negative-lookahead alternation built from the shared marker list in
# `markers.py`.  The strip regex matches any `{{…}}` template-style
# block UNLESS it opens with one of the rendered-marker prefixes (IMG,
# TABLE, TABLEH, LEGEND, VERSE), in which case it's left alone for the
# viewer.  Strip `{{` from each entry — the regex already anchors there.
#
# TABLE/TABLEH/VERSE markers may also carry an optional ``[style:…]``
# slot between the tag and ``:`` (whole-table styling from the source
# ``{|<attrs>`` opener — see :func:`_table_opener_styles`).  Accept
# either form in the lookahead so a ``{{TABLE[style:…]:…}}``-bearing
# marker isn't mistaken for a stray template.
def _marker_lookahead(name: str) -> str:
    # `name` includes its trailing `:` (e.g. `TABLE:`).  Allow either
    # ``TABLE:`` or ``TABLE[``; the marker body always closes with
    # ``}TABLE}`` / ``}VERSE}`` / ``}LEGEND}`` rather than ``}}``, so
    # the strip regex can't end inside it regardless.
    tag = name.rstrip(":")
    return rf"{re.escape(tag)}[:\[]"

_MARKER_OPEN_NAMES = "|".join(
    _marker_lookahead(o[2:]) for o in RENDERED_MARKER_OPENS
)
_STRIP_TEMPLATES_RE = re.compile(
    rf"\{{\{{(?!{_MARKER_OPEN_NAMES})[^{{}}]*\}}\}}"
)


# Internal control-character markers used to protect already-converted
# spans during subsequent transforms.  Each is a 1-byte sentinel.
_FMT = "\x05"   # formatting (bold/italic/small-caps)
_LNK = "\x06"   # link markers
_SH  = "\x07"   # shoulder headings

_FMT = "\x05"   # formatting (bold/italic/small-caps)
_LNK = "\x06"   # link markers
_SH  = "\x07"   # shoulder headings

def _convert_hieroglyphs(text: str) -> str:
    """{{hieroglyph|code}} → [hieroglyph: code]"""
    return re.sub(
        r"\{\{hieroglyph\|([^{}]*)\}\}",
        r"[hieroglyph: \1]", text, flags=re.IGNORECASE,
    )


def _convert_foreign_script(text: str) -> str:
    """Foreign-script wrapper templates whose arg is the already-Unicode
    content the audience should see.

    Each template name in source declares the script of the wrapped
    glyphs; we just unwrap.  Previously falling to `_strip_templates`,
    which silently deleted Greek / Hebrew / Arabic / etc. characters
    (real data loss — articles like SEMITIC LANGUAGES, BIBLE, hundreds
    of etymology footnotes rendered empty where source had non-Latin
    script).

    Variants handled:

      * ``{{Polytonic|content}}`` — Greek with polytonic diacritics.
        The corpus also has OCR'd unicode-suffix variants
        ``{{Polytoⁿⁱc|…}}`` (superscript, 46 hits) and
        ``{{Pₒₗyₜₒₙᵢc|…}}`` (subscript, 45 hits) that fell through
        the ascii-name match.
      * ``{{Greek|content}}`` — Greek without diacritics.
      * ``{{arabic|content}}`` / ``{{Arabic|content}}`` — Arabic.
      * ``{{latin|content}}`` — Latin (typographic emphasis, not
        translation).
      * ``{{coptic|content}}`` — Coptic.
      * ``{{grc|content}}`` — ISO 639 ancient-Greek tag.
      * ``{{lang|code|content}}`` — generic language wrapper; code
        is metadata, content is what renders.
      * ``{{he|letter[|transliteration]}}`` — Hebrew letter, optional
        romanization; emit ``letter (transliteration)`` when both
        present, just letter otherwise.  ``small=y`` and other named
        args are template-formatting flags, dropped.
    """
    # Single-arg unwrap: content rendered verbatim.
    text = re.sub(
        r"\{\{\s*(?:Polytonic|Polytoⁿⁱc|Pₒₗyₜₒₙᵢc|polytonic"
        r"|Greek|arabic|latin|coptic|grc)\s*\|([^{}]*)\}\}",
        lambda m: m.group(1),
        text, flags=re.IGNORECASE,
    )
    # {{lang|code|content}} — two-arg, emit content (positional[1]).
    def _lang(m):
        positional = [p for p in m.group(1).split("|") if "=" not in p]
        if len(positional) >= 2:
            return positional[1]
        if positional:
            return positional[0]
        return ""
    text = re.sub(
        r"\{\{\s*lang\s*\|([^{}]+)\}\}",
        _lang, text, flags=re.IGNORECASE,
    )
    # {{he|letter[|transliteration]}} — Hebrew with optional
    # romanization.  Render both when present so readers without
    # Hebrew get the transliteration in parens.
    def _he(m):
        positional = [
            p.strip() for p in m.group(1).split("|") if "=" not in p
        ]
        if len(positional) >= 2:
            return f"{positional[0]} ({positional[1]})"
        if positional:
            return positional[0]
        return ""
    text = re.sub(
        r"\{\{\s*he\s*\|([^{}]+)\}\}",
        _he, text, flags=re.IGNORECASE,
    )
    return text


def _convert_lb_dash(text: str) -> str:
    """``{{lb-|N}}`` → ``N lb.`` (N pounds, non-breaking).

    EB1911 unit-quantity template: ``{{lb-|N}}`` renders a pound-weight
    figure with a non-breaking space so the number and unit don't wrap
    across a line.  Examples: ``rails weighing from 50 to {{lb-|70}}
    per yard`` (RAILWAYS), ``it weighs {{Lb-|120,000}}`` (PEKING).
    446 corpus instances previously dropped by ``_strip_templates``,
    losing the unit and the number both.

    Bare form ``{{lb-}}`` (no arg) is the unit symbol alone, attached
    to a preceding number on the text-side: ``quarters of 480
    {{lb-}}`` (IRON AND STEEL) → ``quarters of 480 lb``; ``112
    {{lb-}}<br>(546.852 kg.)`` (fire-resistance tables) → ``112 lb<br>
    (546.852 kg.)``.  54 additional corpus instances.
    """
    text = re.sub(
        r"\{\{\s*lb-\s*\|\s*([^{}|]+?)\s*\}\}",
        lambda m: f"{m.group(1).strip()} lb",
        text, flags=re.IGNORECASE,
    )
    text = re.sub(r"\{\{\s*lb-\s*\}\}", "lb", text, flags=re.IGNORECASE)
    return text


def _convert_overline(text: str) -> str:
    """``{{overline|X}}`` -> X with a combining overline U+0305 after
    each character.  EB1911 crystallography uses this for Miller-index
    negative-axis notation: ``(11{{overline|1}})`` -> the (1 1 -1)
    plane, written with a bar over the digit.  290 corpus instances.
    Combining-overline is inline (no marker needed); modern fonts
    render a bar above each character glyph.
    """
    def _repl(m):
        s = m.group(1)
        return "".join(c + "̅" for c in s)
    return re.sub(
        r"\{\{\s*overline\s*\|([^{}|]+)\}\}",
        _repl, text, flags=re.IGNORECASE,
    )


def _convert_spaces(text: str) -> str:
    """``{{spaces|N}}`` -> N non-breaking spaces.  EB1911 layout
    primitive for explicit padding (typically HTML-table cell padding,
    e.g. ``{{spaces|2}}Year{{spaces|2}}``).  289 corpus instances."""
    def _repl(m):
        try:
            n = int(m.group(1).strip())
        except ValueError:
            return ""
        return " " * max(0, min(n, 20))  # cap defensively
    return re.sub(
        r"\{\{\s*spaces\s*\|([^{}|]+)\}\}",
        _repl, text, flags=re.IGNORECASE,
    )


def _convert_zero_pad(text: str) -> str:
    """``{{0}}`` / ``{{0|TEXT}}`` -> empty.  EB1911 invisible-padding
    template: MediaWiki renders the digit ``0`` (or TEXT, when arg
    supplied) at zero width — a glyph that occupies a numeric-figure's
    width in print typography for column alignment, but is visually
    absent.  Bare form is used as right-pad in numeric table columns
    (``||{{0}}3,410,756||`` aligns under ``||1,768,781||``); arg form
    pads with custom text (``{{0|IIV}}I.``).  In HTML with proportional
    fonts the alignment function is meaningless either way; emit
    nothing.  247 arg-form + 106 bare-form corpus instances."""
    text = re.sub(r"\{\{\s*0\s*\|[^{}|]*\}\}", "", text)
    text = re.sub(r"\{\{\s*0\s*\}\}", "", text)
    return text


def _convert_dotted_toc(text: str) -> str:
    """``{{Dotted TOC line|N|LABEL|VALUE|…}}`` and
    ``{{Dotted TOC page listing|...|entrytext=X|pagetext=Y}}`` →
    space-separated text from the content args.

    Despite the template name these are NOT used for tables of contents
    in EB1911 articles (articles don't have TOCs) — they're a
    typographic primitive for dotted-leader enumeration rows.  COUNCIL
    (vol 7) uses them for a list of ecumenical councils with dates,
    FISHERIES (vol 10) for a country/fleet-count table, SUGAR (vol 26)
    for production figures.  Print rendering connects label and value
    with dot leaders (``1. Nicaea I. ........ 325``); we drop the
    leader styling and emit the label/value content space-joined so
    the figures survive in prose form.  47 + 5 corpus instances
    previously dropped whole by ``_strip_templates``.
    """
    def _line(m: re.Match) -> str:
        parts = [p.strip() for p in m.group(1).split("|")
                 if "=" not in p]
        return " ".join(p for p in parts if p)
    text = re.sub(
        r"\{\{\s*Dotted\s+TOC\s+line\s*\|([^{}]*)\}\}",
        _line, text, flags=re.IGNORECASE,
    )
    # `Dotted TOC page listing` uses named args (`entrytext=`,
    # `pagetext=`) for label/value.  Extract those by name.
    def _listing(m: re.Match) -> str:
        body = m.group(1)
        entry = re.search(r"entrytext\s*=\s*([^|}]*)", body, re.IGNORECASE)
        page = re.search(r"pagetext\s*=\s*([^|}]*)", body, re.IGNORECASE)
        parts = []
        if entry and entry.group(1).strip():
            parts.append(entry.group(1).strip())
        if page and page.group(1).strip():
            parts.append(page.group(1).strip())
        return " ".join(parts)
    text = re.sub(
        r"\{\{\s*Dotted\s+TOC\s+page\s+listing\s*\|([^{}]*)\}\}",
        _listing, text, flags=re.IGNORECASE,
    )
    return text


def _convert_anchor_plus(text: str) -> str:
    """``{{anchor+|Name}}`` -> empty.  EB1911 anchor template — sets
    a cross-reference target with no visible output.  73 corpus
    instances; explicit named no-op."""
    return re.sub(
        r"\{\{\s*anchor\+\s*\|[^{}]*\}\}",
        "", text, flags=re.IGNORECASE,
    )


def _convert_sp(text: str) -> str:
    """``{{sp|word}}`` -> word.  EB1911 letter-spaced-typography
    template (used for emphasis in language entries like
    ``{{sp|amare}}``).  72 corpus instances; emit the bare word
    since marker-form letter-spacing isn't supported by the viewer."""
    return re.sub(
        r"\{\{\s*sp\s*\|([^{}|]+)\}\}",
        lambda m: m.group(1).strip(),
        text, flags=re.IGNORECASE,
    )


def _lkpl_to_marker(args: str) -> str:
    """`{{EB1911/DNB lkpl|target|display|…}}` arg string → hard link marker.
    target = arg 0; display = first non-empty arg after it, else the target."""
    parts = args.split("|")
    target = parts[0].strip()
    display = next((p.strip() for p in parts[1:] if p.strip()), target)
    return f"{_LNK}{target}|{display}{_LNK}"


def _convert_links(text: str) -> str:
    """Convert link templates and wikilinks to link markers."""

    # {{EB1911 article link|...}} — multiple parameter forms
    def _eb1911_link(m):
        inner = m.group(1)
        # Unwrap nested {{sc|...}}
        inner = re.sub(r"\{\{sc\|([^{}]*)\}\}", r"\1", inner, flags=re.IGNORECASE)
        parts = [p.strip() for p in inner.split("|")]
        positional = [p for p in parts if "=" not in p and p]
        if len(positional) >= 2:
            display, target = positional[0], positional[1]
        elif len(positional) == 1:
            display = target = positional[0]
        else:
            return ""
        # Subpage targets → plain text for section labels, link for articles
        if "/" in target:
            if re.match(r"^[IVXLC]+\.", display):
                return display
            return f"{_LNK}{display}|{display}{_LNK}"
        return f"{_LNK}{target}|{display}{_LNK}"

    # Unwrap nested {{sc|}} before matching EB1911 article link.
    # `\s+` tolerates the double-space typo variant
    # `{{EB1911 article  link|…}}` (3 corpus hits).
    text = re.sub(
        r"(\{\{EB1911\s+article\s+link\|[^}]*)(\{\{sc\|)([^}]*)(\}\})",
        lambda m: m.group(1) + m.group(3), text, flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\{\{\s*EB1911\s+article\s+link\s*\|([^{}]*)\}\}",
        _eb1911_link, text, flags=re.IGNORECASE,
    )

    # {{1911link|Target}} or {{1911link|Target|Display}} (and 11link,
    # `1911 article link`).  Positional args named like `nosc=yes` are
    # template options that can sit BEFORE the target slot — drop all
    # `name=value` parts first, then take the first remaining positional
    # as target and the second as display.
    def _link11(m):
        positional = [
            p.strip() for p in m.group(1).split("|")
            if p.strip() and "=" not in p
        ]
        if not positional:
            return ""
        target = positional[0]
        display = positional[1] if len(positional) > 1 else target
        return f"{_LNK}{target}|{display}{_LNK}"
    text = re.sub(
        r"\{\{(?:1911link|11link|EB1911\s+link)\|([^{}]+)\}\}",
        _link11, text, flags=re.IGNORECASE,
    )

    # 9th-edition + Catholic-Encyclopedia references.  Many subjects
    # have an 11th-edition counterpart (Atom, Diffusion, Ether…); some
    # don't (Attraction).  Emit a soft-link marker that export resolves
    # to a real link when an 11th-edition article exists, falling back
    # to plain display text otherwise — never a search-link, since we
    # know the source template points at a different work.
    #
    # Three argument conventions are in use:
    #   {{EB9link|Target[|Display]}}                — target first
    #   {{EB9 Intra-Article Link|Target[|section]}} — target first; arg2 is a
    #                                                 section name, not display
    #   {{EB9 article link|Display|Target}}         — display first, target second
    #                                                 (parallel to {{EB1911 article link}})
    #   {{CE article link|Display|Target}}          — same as EB9 article link
    # Section qualifiers like "(2.)" are stripped from the target for
    # matching ({{EB9link|Ether (2.)|Ether}} → target "Ether").
    def _soft_link(target: str, display: str) -> str:
        target = re.sub(r"\s*\([^)]*\)\s*$", "", target).strip() or target
        return f"«EB9:{target}|{display}«/EB9»"

    def _eb9link(m):  # target-first
        positional = [p.strip() for p in m.group(1).split("|")
                      if p.strip() and "=" not in p]
        if not positional:
            return ""
        target = positional[0]
        display = positional[1] if len(positional) > 1 else target
        return _soft_link(target, display)
    text = re.sub(
        r"\{\{EB9link\|([^{}]+)\}\}",
        _eb9link, text, flags=re.IGNORECASE,
    )

    def _eb9_intra(m):  # target-first; arg2 is a section, not display
        positional = [p.strip() for p in m.group(1).split("|")
                      if p.strip() and "=" not in p]
        if not positional:
            return ""
        target = positional[0]
        return _soft_link(target, target)
    text = re.sub(
        r"\{\{EB9\s+intra[- ]article\s+link\|([^{}]+)\}\}",
        _eb9_intra, text, flags=re.IGNORECASE,
    )

    def _article_link_soft(m):  # display-first, target-second
        positional = [p.strip() for p in m.group(1).split("|")
                      if p.strip() and "=" not in p]
        if not positional:
            return ""
        if len(positional) >= 2:
            display, target = positional[0], positional[1]
        else:
            display = target = positional[0]
        return _soft_link(target, display)
    text = re.sub(
        r"\{\{(?:EB9|CE)\s+article\s+link\|([^{}]+)\}\}",
        _article_link_soft, text, flags=re.IGNORECASE,
    )

    # {{EB1911 intra-article link|Target[|Display]}} — Wikisource template
    # that links to ANOTHER EB1911 article (despite the misleading "intra-
    # article" name).  Target is first arg; display defaults to target.
    # Same hard-link marker shape as `EB1911 article link` — xref resolver
    # (stage 3a) picks them up cross-volume.  Distinct from `EB9 intra-
    # article link` (which is 9th-edition target-first with arg2 as
    # section name, soft-linked).
    def _eb1911_intra(m):
        positional = [p.strip() for p in m.group(1).split("|")
                      if p.strip() and "=" not in p]
        if not positional:
            return ""
        target = positional[0]
        display = positional[1] if len(positional) > 1 else target
        return f"{_LNK}{target}|{display}{_LNK}"
    text = re.sub(
        r"\{\{\s*EB1911\s+intra[- ]article\s+link\s*\|([^{}]+)\}\}",
        _eb1911_intra, text, flags=re.IGNORECASE,
    )

    # {{1911 article link|[nosc=N|]Target[|Display]}} — sibling of
    # `{{1911link|…}}` / `{{11link|…}}` with a longer name.  Same
    # target-first / display-second convention; `nosc=…` is a template-
    # option flag (drop, not display).
    text = re.sub(
        r"\{\{\s*1911\s+article\s+link\s*\|([^{}]+)\}\}",
        _link11, text, flags=re.IGNORECASE,
    )

    # {{9link|Target}} — Wikisource short-form 9th-edition link, target-
    # only.  Same soft-link semantics as `{{EB9link|…}}` — emit
    # `«EB9:Target|Target«/EB9»`, xref export resolves to a real link
    # when a corpus counterpart exists, falls back to plain display
    # otherwise.
    def _9link(m):
        positional = [p.strip() for p in m.group(1).split("|")
                      if p.strip() and "=" not in p]
        if not positional:
            return ""
        target = positional[0]
        display = positional[1] if len(positional) > 1 else target
        return _soft_link(target, display)
    text = re.sub(
        r"\{\{\s*9link\s*\|([^{}]+)\}\}",
        _9link, text, flags=re.IGNORECASE,
    )

    # {{CE lkpl|Target[|Display][|text=Display]}} — Catholic Encyclopedia
    # link.  Target-first like `{{EB1911 lkpl|…}}` but the work being
    # cited is external (CE has no per-article EB1911 counterpart most
    # of the time), so emit a soft link via `_soft_link` rather than a
    # hard `«LN:` marker.  Supports both positional `|Display` and the
    # named `|text=Display` form the corpus uses interchangeably.
    def _ce_lkpl(m):
        parts = m.group(1).split("|")
        target = parts[0].strip()
        # Look for `text=` named arg first, then fall back to first
        # non-empty positional after the target.
        display = None
        for p in parts[1:]:
            if p.strip().lower().startswith("text="):
                display = p.split("=", 1)[1].strip()
                break
        if display is None:
            display = next(
                (p.strip() for p in parts[1:] if p.strip() and "=" not in p),
                target,
            )
        return _soft_link(target, display)
    text = re.sub(
        r"\{\{\s*CE\s+lkpl\s*\|([^{}]+)\}\}",
        _ce_lkpl, text, flags=re.IGNORECASE,
    )

    # {{cite|Work title[|Subtitle]}} — Wikisource bibliography cite.  The
    # work being cited is external (rarely an EB1911 article), so we
    # don't emit any link marker — just unwrap to the inner content,
    # preserving any nested `[[wikilink]]` to a Wikisource source page.
    # Replaces silent deletion via `_strip_templates` (~29 corpus hits,
    # all content-loss).
    def _cite(m):
        # The whole content joined back — cite is structurally just
        # typographic emphasis on a work title; inner wikilinks /
        # italics survive downstream handlers.
        return m.group(1).strip()
    text = re.sub(
        r"\{\{\s*cite\s*\|((?:[^{}]|\{\{[^{}]*\}\}|\[\[[^\]]*\]\])+)\}\}",
        _cite, text, flags=re.IGNORECASE,
    )

    # {{EB1911 lkpl|...}}, {{DNB lkpl|...}}, {{EB9 lkpl|...}} — Wikisource
    # link-with-display-text-and-target templates.  `EB1911`/`DNB` get a
    # hard `«LN:` marker (xref resolver looks for cross-volume EB1911
    # articles); `EB9` falls through to a soft `«EB9:` marker because
    # the 9th edition is a different work without a per-article counterpart
    # in our corpus.  Outer `\s*` + name-internal `\s+` tolerate the
    # double-space typo `{{EB1911  lkpl|…}}` (2 corpus hits).
    text = re.sub(
        r"\{\{\s*(?:EB1911|DNB)\s+lkpl\s*\|([^{}]+)\}\}",
        lambda m: _lkpl_to_marker(m.group(1)), text, flags=re.IGNORECASE,
    )

    def _eb9_lkpl(m):
        parts = m.group(1).split("|")
        target = parts[0].strip()
        display = next((p.strip() for p in parts[1:] if p.strip()), target)
        return _soft_link(target, display)
    text = re.sub(
        r"\{\{\s*EB9\s+lkpl\s*\|([^{}]+)\}\}",
        _eb9_lkpl, text, flags=re.IGNORECASE,
    )

    # [[wikilinks]] — handle nested brackets
    def _wikilink(m):
        content = m.group(1)
        # Skip File/Image/Category
        if re.match(r"(?i)^(File|Image|Category):", content):
            return ""
        # Protect {{...}} from pipe-splitting
        protected = re.sub(r"\{\{[^{}]*\}\}", lambda m2: m2.group(0).replace("|", "\x04"), content)
        parts = protected.split("|")
        parts = [p.replace("\x04", "|") for p in parts]
        target = parts[0].strip()
        display = parts[1].strip() if len(parts) > 1 else target
        # Unwrap templates in display text
        display = re.sub(r"\{\{sc\|([^{}]*)\}\}", r"\1", display, flags=re.IGNORECASE)
        display = re.sub(r"\{\{[^{}|]*\|([^{}]*)\}\}", r"\1", display)
        display = (display
                   .replace("«B»", "").replace("«/B»", "")
                   .replace("«I»", "").replace("«/I»", ""))
        # Interwiki/Author/Portal → display text only
        if re.match(r"(?i)^(Author|wikt|wiktionary|s|w|d|wikipedia|Portal|Page|File|1911):", target):
            return display
        return f"{_LNK}{target}|{display}{_LNK}"

    text = re.sub(r"\[\[(.*?)\]\]", _wikilink, text, flags=re.DOTALL)

    return text


_FRAKTUR_MAP = {}
for _i, _c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    _FRAKTUR_MAP[_c] = chr(0x1D504 + _i)
for _i, _c in enumerate("abcdefghijklmnopqrstuvwxyz"):
    _FRAKTUR_MAP[_c] = chr(0x1D51E + _i)
# Unicode assigns different codepoints for some Fraktur capitals
_FRAKTUR_MAP.update({"C": "ℭ", "H": "ℌ", "I": "ℑ",
                      "R": "ℜ", "Z": "ℨ"})


def _to_fraktur(text: str) -> str:
    """Convert plain text to Unicode Mathematical Fraktur characters."""
    return "".join(_FRAKTUR_MAP.get(c, c) for c in text)


# ── Inline fraction typography ────────────────────────────────────────
#
# Variants share one rendering contract (num/den as plain text, vulgar
# Unicode where available): {{sfrac|n|d}}, {{sfrac nobar|n|d}}, {{frac|n|d}},
# {{mfrac|i|n|d}} (mixed), {{over|n|d}}, {{sfracN|n|d}}, {{EB1911 sfrac|…}},
# {{EB1911 tfrac|…}}, and the unicode-name EB¹⁹¹¹ / EB₁₉₁₁ variants.  Three
# positional-arg shapes: 3 → integer + num/den (mixed), 2 → num/den, 1 → 1/n.
# Named-param styling args (font-size=…, color=…) are dropped.
_VULGAR_FRACTIONS = {
    ("1", "2"): "½", ("1", "4"): "¼", ("3", "4"): "¾",
    ("1", "3"): "⅓", ("2", "3"): "⅔",
    ("1", "5"): "⅕", ("2", "5"): "⅖",
    ("3", "5"): "⅗", ("4", "5"): "⅘",
    ("1", "6"): "⅙", ("5", "6"): "⅚",
    ("1", "8"): "⅛", ("3", "8"): "⅜",
    ("5", "8"): "⅝", ("7", "8"): "⅞",
}

_FRAC_NAMES = (
    r"sfrac\s+nobar"
    r"|sfracN"
    r"|sfrac"
    r"|mfrac"
    r"|frac"
    r"|over"
    r"|EB1911\s+sfrac"
    r"|EB1911\s+tfrac"
    r"|EB¹⁹¹¹\s+sfrac"
    r"|EB¹⁹¹¹\s+tfrac"
    r"|EB₁₉₁₁\s+ₜfᵣₐc"
)
_FRAC_TOKEN_RE = re.compile(
    r"\{\{\s*(?:" + _FRAC_NAMES + r")\b", re.IGNORECASE)


def _frac(num: str, den: str) -> str:
    return _VULGAR_FRACTIONS.get((num.strip(), den.strip()),
                                 f"{num.strip()}/{den.strip()}")


def _split_top_pipes(s: str) -> list[str]:
    """Split ``s`` on ``|`` at brace/bracket depth 0, so nested ``{{…}}`` /
    ``[[…]]`` arguments aren't bisected."""
    parts: list[str] = []
    buf: list[str] = []
    depth = 0
    i, n = 0, len(s)
    while i < n:
        two = s[i:i + 2]
        if two in ("{{", "[["):
            depth += 1
            buf.append(two)
            i += 2
        elif two in ("}}", "]]"):
            depth = max(0, depth - 1)
            buf.append(two)
            i += 2
        elif s[i] == "|" and depth == 0:
            parts.append("".join(buf))
            buf = []
            i += 1
        else:
            buf.append(s[i])
            i += 1
    parts.append("".join(buf))
    return parts


def _render_fraction(args: str) -> str:
    """Render one fraction's already-expanded ``|``-joined arg string (which
    begins with the leading ``|``).  Drops ``name=value`` styling args; the
    positional-arg count selects mixed / num-den / 1-n."""
    parts = _split_top_pipes(args)
    if parts and parts[0] == "":          # empty slot before the first `|`
        parts = parts[1:]
    pos = [p for p in parts if not re.match(r"^[a-zA-Z_-]+=", p)]
    if len(pos) >= 3:
        return f"{pos[0].strip()}{_frac(pos[1], pos[2])}"
    if len(pos) == 2:
        return _frac(pos[0], pos[1])
    if len(pos) == 1:
        return _frac("1", pos[0])
    return ""


def _expand_fractions(text: str) -> str:
    """Render every inline fraction template via balanced-brace recursion.

    Replaces the former nested 8-pass fixpoint loop (a loop inside
    ``_unwrap_content_templates``, itself re-run by the body unwrap pass —
    doubly fake recursion).  Each ``{{frac…|…}}`` is located, brace-counted
    to its matching ``}}`` (spanning nested braces the old ``[^{}|]`` slots
    could not), its inner recursively expanded FIRST so a nested fraction arg
    is plain text before the args are split, then the positional args drive
    ``_frac``.  Children-resolved-first is structural — no iteration, no
    ordering, and pipe-bearing / >8-deep nestings now resolve instead of
    leaking to ``_strip_templates``."""
    m = _FRAC_TOKEN_RE.search(text)
    if m is None:
        return text
    open_idx = m.start()
    depth, j, n, close = 0, open_idx, len(text), None
    while j < n - 1:
        pair = text[j:j + 2]
        if pair == "{{":
            depth += 1
            j += 2
        elif pair == "}}":
            depth -= 1
            if depth == 0:
                close = j
                break
            j += 2
        else:
            j += 1
    if close is None:
        # Unbalanced opener — advance past the name token (never stall) and
        # recurse on the remainder; the bare opener is left as it is today.
        return text[:m.end()] + _expand_fractions(text[m.end():])
    inner = text[m.end():close]
    if not inner.startswith("|"):
        # Name not immediately followed by `|` (the old `names\|` adjacency
        # requirement) — not a positional fraction call; leave it, recurse on.
        return text[:m.end()] + _expand_fractions(text[m.end():])
    rendered = _render_fraction(_expand_fractions(inner))
    return text[:open_idx] + rendered + _expand_fractions(text[close + 2:])


# ── General recursive inline-template expander ────────────────────────
#
# Registry-driven balanced-brace recursion — the general form of
# `_expand_fractions`.  Finds each balanced `{{name|args}}`; if `name` is
# registered, recursively expands its inner FIRST (children-resolved-first
# by construction), then dispatches the handler; unregistered templates are
# scanned INTO (not skipped over), so a registered template nested inside an
# unregistered one still resolves.  This dissolves the fake-recursion loop
# for the registered families: nesting and pipe-bearing inners that the flat
# `[^{}]` regexes leaked now resolve in one pass, no ordering, no iteration.
#
# Families migrate into the registry one batch at a time; each batch first
# runs ALONGSIDE the legacy flat handlers (the expander resolves the hard
# nested cases up-front, the flat passes then no-op on what's left), then the
# now-redundant flat regexes are removed in a separate byte-identical step.


def _next_template(text: str, start: int = 0):
    """Find the next balanced ``{{…}}`` at/after ``start``.  Returns
    ``(open_idx, full_inner, close_idx)`` (``full_inner`` = name+args between
    the braces) or ``None``.  An unbalanced ``{{`` is skipped, not fatal — the
    scan resumes past it so later well-formed templates still resolve."""
    pos = start
    n = len(text)
    while True:
        idx = text.find("{{", pos)
        if idx < 0:
            return None
        depth, j = 0, idx
        while j < n - 1:
            pair = text[j:j + 2]
            if pair == "{{":
                depth += 1
                j += 2
            elif pair == "}}":
                depth -= 1
                if depth == 0:
                    return (idx, text[idx + 2:j], j)
                j += 2
            else:
                j += 1
        pos = idx + 2  # unbalanced opener — skip it, keep scanning


def _inline_unwrap(args: list[str]) -> str:
    """Wrapper → its content: everything after the first pipe, verbatim
    (matches the legacy `[^{}]*` capture, which kept inner pipes)."""
    return "|".join(args)


def _inline_lang(args: list[str]) -> str:
    """`{{lang|code|text}}` → text (drop the language code)."""
    return "|".join(args[1:])


def _inline_small_caps(args: list[str]) -> str:
    return f"{_FMT}SC" + "|".join(args) + f"{_FMT}/SC"


def _inline_fs(args: list[str]) -> str:
    """`{{Fs|size|content}}` → value-bearing `«FS[size]»content«/FS»` marker
    (the recursive companion to the flat handler in `_unwrap_content_templates`
    — content may itself hold nested `{{sc|…}}`/etc., resolved children-first)."""
    if len(args) < 2:
        return "|".join(args)
    return f"{_FMT}FS[{args[0].strip()}]" + "|".join(args[1:]) + f"{_FMT}/FS"


_INLINE_REGISTRY = {
    # script/language + alignment wrappers → content
    "greek": _inline_unwrap, "polytonic": _inline_unwrap,
    "hebrew": _inline_unwrap, "uc": _inline_unwrap,
    "nowrap": _inline_unwrap, "right": _inline_unwrap, "left": _inline_unwrap,
    "lang": _inline_lang,
    # Typographic OVERRIDE wrappers — meaningful only in a context whose default
    # they cancel (`nobold` = non-bold inside a bold table header; `font-variant
    # normal` = cancel small-caps).  In default body context the override equals
    # the default, so unwrapping to the inner content is faithful and recovers
    # text the catch-all was deleting whole (BEER's analysis-table headers).
    "nobold": _inline_unwrap, "font-variant normal": _inline_unwrap,
    # small-caps family → «SC» marker
    "sc": _inline_small_caps, "asc": _inline_small_caps,
    "smallcaps": _inline_small_caps, "small caps": _inline_small_caps,
    # value-bearing font-size wrapper → «FS[size]» marker
    "fs": _inline_fs,
}


def _expand_inline_templates(text: str) -> str:
    out: list[str] = []
    pos = 0
    while True:
        nt = _next_template(text, pos)
        if nt is None:
            out.append(text[pos:])
            return "".join(out)
        open_idx, full_inner, close_idx = nt
        name = _split_top_pipes(full_inner)[0].strip().lower()
        handler = _INLINE_REGISTRY.get(name)
        if handler is None:
            # not ours — keep the opener, scan inward for nested registered ones
            out.append(text[pos:open_idx + 2])
            pos = open_idx + 2
            continue
        out.append(text[pos:open_idx])
        # children-resolved-first: expand the inner, then re-split + dispatch
        parts = _split_top_pipes(_expand_inline_templates(full_inner))
        out.append(handler(parts[1:]))
        pos = close_idx + 2


def _unwrap_content_templates(text: str) -> str:
    """Unwrap content templates to their text content."""
    # greek/polytonic/hebrew/lang/uc/nowrap → owned by the recursive
    # `_expand_inline_templates` engine (run first in the unwrap loop); the
    # flat negated-class passes here were superseded and removed (step 1b).
    # smaller/larger now carry graduated size markers (see the «SM»/«LG»
    # block below) instead of flattening — kept symmetric with «XL»/«XXL».
    # `{{Fs|size|content}}` → «FS[size]» — owned by the recursive engine
    # (`_inline_fs`), which resolves nested-brace content (fractions/sub/sup/
    # sc) correctly where the flat negated-class handler mis-scoped «FS».
    # Drop initial (decorative large first letter) → just the letter
    text = re.sub(r"\{\{[Dd]rop ?initial\|([^{}|]*)[^{}]*\}\}", r"\1", text)
    # Abbreviation/tooltip → first arg (display text). The first arg
    # can contain a link marker \x06…\x06 which itself holds a pipe;
    # treat the marker as atomic so the pipe split doesn't bisect it.
    _ABBR_ARG1 = r"(?:" + re.escape(_LNK) + r"[^" + re.escape(_LNK) + r"]*" + re.escape(_LNK) + r"|[^{}|])*"
    text = re.sub(
        r"\{\{abbr\|(" + _ABBR_ARG1 + r")\|[^{}]*\}\}",
        r"\1", text, flags=re.IGNORECASE)
    text = re.sub(
        r"\{\{tooltip\|(" + _ABBR_ARG1 + r")\|[^{}]*\}\}",
        r"\1", text, flags=re.IGNORECASE)
    # Alignment wrappers → content (`sm` now carries «SM» — see size block).
    # right/left → content: owned by the recursive engine (step 1b).
    # Rotation wrapper: {{rotate|angle|content}} → content. Rotation
    # is purely visual styling (used for rotated column labels in
    # geology/stratigraphy tables); preserve the text.
    text = re.sub(
        r"\{\{rotate\s*\|[^{}|]*\|([^{}]*)\}\}",
        r"\1", text, flags=re.IGNORECASE)
    # {{fqm|X}} (floating quotation mark — hanging typographical quote
    # at the start of a verse/quotation block) → just X.  Without this
    # the opener quote gets eaten by the ``_strip_templates`` whitelist
    # pass, leaving verse quotations with only a closing quote.
    # Bare ``{{fqm}}`` defaults to a curly opening double-quote.
    text = re.sub(r"\{\{fqm\|([^{}]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{fqm\}\}", "\u201c", text, flags=re.IGNORECASE)
    # Inline fractions are rendered by the recursive expander
    # `_expand_fractions` (module-level): one balanced-brace pass, nested
    # fractions resolved bottom-up by construction — no loop, no ordering.
    text = _expand_fractions(text)
    # Any remaining Css image crop templates (non-DjVu sources, or
    # those that survived the pre-pass in _transform_text_v2).
    text = re.sub(r"\{\{Css image crop[^}]*\}\}", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{Css image crop[^}]*$", "", text, flags=re.IGNORECASE | re.MULTILINE)
    # Ellipsis (three dots, not Unicode ellipsis, so it's searchable)
    text = re.sub(r"\{\{\.\.\.\}\}", "...", text)
    # Ditto marks
    text = re.sub(r"\{\{ditto\|([^{}]*)\}\}", "″", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{ditto\}\}", "″", text, flags=re.IGNORECASE)
    # Blackletter → Unicode Mathematical Fraktur
    text = re.sub(r"\{\{[Bb]lackletter\|([^{}]*)\}\}",
                  lambda m: _to_fraktur(m.group(1)), text)
    # Numbered equations `{{ne|...}}` and labeled-equation templates
    # (`{{equation|...}}`, `{{MathForm1|...}}`) are now lifted at the
    # walker as MATH_NE / MATH_EQUATION / MATH_FORMULA_LABELED elements
    # and rendered by the math producers — `«EQN:LABEL»content«/EQN»`
    # markers come back substituted into body prose with `\n\n` margins
    # the producer applies.
    # {{sans-serif|content}} — metalinguistic letter typography: the
    # source visually distinguishes letters being discussed as letters
    # (the letter "A" qua letter) from running prose by wrapping them
    # in a sans-serif font, usually combined with bold.  ALPHABET uses
    # this 117 times to mark up the individual letters under discussion.
    # Emit as `«SS»content«/SS»`; the viewer applies the sans-serif font.
    # Brace-counted so an inner template (e.g. `{{EB1911 lkpl|X}}`)
    # doesn't break the regex.
    text = _unwrap_balanced(text, "sans-serif",
                            lambda inner: f"{_FMT}SS{inner}{_FMT}/SS")
    # {{Serif|X}} — opposite of sans-serif: explicit serif font for a
    # single letter discussed AS A LETTER.  Mirror of the sans-serif
    # marker.  Less common than sans-serif (ALPHABET uses it twice).
    text = _unwrap_balanced(text, "Serif",
                            lambda inner: f"{_FMT}SR{inner}{_FMT}/SR")
    # {{small-caps|X}} — long-form alias for {{sc|X}}; reuse the
    # existing «SC» marker so the viewer renders identically.
    text = _unwrap_balanced(text, "small-caps",
                            lambda inner: f"{_FMT}SC{inner}{_FMT}/SC")
    # {{=}} — Wikisource convention for a literal `=` inside template
    # args (escapes the named-parameter separator).  Just emit `=`.
    text = re.sub(r"\{\{\s*=\s*\}\}", "=", text)
    # {{–}} — literal en-dash, used in source where `–` would be
    # ambiguous (e.g. inside template args).
    text = re.sub(r"\{\{\s*–\s*\}\}", "–", text)
    # {{shy}} — soft hyphen (U+00AD): invisible, marks an acceptable
    # hyphenation point.  Preserve as the actual soft-hyphen char.
    text = re.sub(r"\{\{\s*shy\s*\}\}", "­", text, flags=re.IGNORECASE)
    # Single-char escapes — Wikisource uses `{{X}}` to embed literal
    # characters that would otherwise be parsed as template / wikitable
    # syntax.  Each renders to its literal char; previously falling to
    # `_strip_templates` and losing the char entirely.  Corpus counts
    # (post-prior-cleanups audit): `(` 24, `)` 24, `'` 22, `!` 15,
    # `*` 3 — and the spaced-dots `***` 4, `…` 7, `. . .` 2.
    text = re.sub(r"\{\{\s*\(\s*\}\}", "(", text)
    text = re.sub(r"\{\{\s*\)\s*\}\}", ")", text)
    text = re.sub(r"\{\{\s*'\s*\}\}", "'", text)
    text = re.sub(r"\{\{\s*!\s*\}\}", "|", text)
    text = re.sub(r"\{\{\s*\*\s*\}\}", "*", text)
    text = re.sub(r"\{\{\s*…\s*\}\}", "…", text)
    text = re.sub(r"\{\{\s*\.\s*\.\s*\.\s*\}\}", "...", text)
    # `{{***|N}}` — typographic ornamental break (3+ asterisks centered).
    # The `|N` arg controls width; we emit a literal `***` separator.
    text = re.sub(r"\{\{\s*\*\*\*\s*(?:\|[^{}]*)?\}\}", "***", text)
    # {{...|N}} — ellipsis with optional spacing arg; render as plain
    # `...` regardless of arg.  (Different from {{...}} bare, which is
    # already handled in _unwrap_content_templates' fixed-point loop.)
    text = re.sub(r"\{\{\s*\.\.\.\s*\|[^{}]*\}\}", "...", text)
    # {{hws|short|full}} / {{hwe|short|full}} — hyphenated-word page-
    # split markers: at a page boundary, `hws` is the last syllable on
    # the previous page and `hwe` is the first syllable on the next.
    # The pair's second arg is the FULL word.  In our linear rendering
    # (no page boundaries), hws emits the full word once; hwe drops
    # (the full word was already emitted by its hws partner).
    #
    # Long-form names `{{hyphenated word start|…}}` and `{{hyphenated
    # word end|…}}` are aliases — same arg convention.  Previously
    # falling to `_strip_templates`, losing both the word fragment
    # AND the word join (~35 audit hits across the corpus).
    text = re.sub(
        r"\{\{\s*(?:hws|hyphenated\s+word\s+start)\s*\|[^{}|]*\|([^{}]*)\}\}",
        r"\1", text, flags=re.IGNORECASE)
    text = re.sub(
        r"\{\{\s*(?:hwe|hyphenated\s+word\s+end)\s*\|[^{}|]*\|[^{}]*\}\}",
        "", text, flags=re.IGNORECASE)
    # {{SIC|wrong|right}} — source-error annotation.  Render the
    # wrong-as-printed text followed by `[sic]` so the reader sees
    # both the source's actual content and a typographic notice.
    text = re.sub(r"\{\{\s*sic\s*\|([^{}|]*)\|[^{}]*\}\}",
                  r"\1 [sic]", text, flags=re.IGNORECASE)
    # Center-family templates → `«CTR»content«/CTR»` marker.  All six
    # variants (inline {{center|}}, {{c|}}, {{block center|}}; paired
    # {{c/s}}…{{c/e}}, {{block center/s}}…{{/e}}, {{center block/s}}…
    # {{/e}}) collapse to one marker — the centering signal is what
    # matters; the inline-vs-block distinction in MediaWiki's templates
    # is mostly cosmetic margin and can be revisited per-context in the
    # viewer if needed.  Paired forms are atomic during body-split (see
    # walker's _PAIRED_WRAPPER_NAMES) so a placeholder inside doesn't
    # fragment them.
    # Emit one `«CTR»para«/CTR»` per source paragraph (split on `\n\n`).
    # Pure placeholder paragraphs stay unwrapped (they substitute back to
    # block markers which are semantically centred-as-blocks by their
    # own rendering, not by CTR-around-block).  No outer `\n\n` borders:
    # paragraph separation between this CTR and surrounding content is
    # the renderer's problem; the producer only emits the marker itself.
    _CTR_PURE_PH_RE = re.compile(r"^\s*\x03ELEM:\d+\x03\s*$")
    def _wrap_ctr(inner: str) -> str:
        content = inner.strip()
        if not content:
            return ""
        out = []
        for p in re.split(r"\n\n+", content):
            p = p.strip()
            if not p:
                continue
            if _CTR_PURE_PH_RE.match(p):
                out.append(p)
            else:
                out.append(f"«CTR»{p}«/CTR»")
        return "\n\n".join(out)
    for _name in _CENTER_INLINE_TEMPLATES:
        text = _unwrap_balanced(text, _name, _wrap_ctr)
    # Paired `{{NAME/s}}…{{NAME/e}}` wrappers (center family → «CTR»;
    # fine-print family → strip-keep-content) are now recognized at the WALKER
    # as the CENTER element — a balanced node whose inner is recursively
    # classified (step 2).  The former `.*?` overlays here couldn't span a
    # `/s`-`/e` pair the walker had split between, so orphaned halves leaked.
    # {{section|TITLE}} — Wikisource transclusion anchor.  The transcriber
    # places this BEFORE the visible inline italic-em-dash section
    # heading (e.g. `{{section|Literature of Alchemy}}''Literature of
    # Alchemy''.—`).  The template itself produces no visible output —
    # it's a `{{#section:Page|Name}}` partial-transclusion anchor — and
    # the visible heading is the italic-em-dash text that follows,
    # which the body's section-detector already renders correctly.
    # Drop explicitly so the deletion is a named no-op, not catch-all-
    # swept.  759 corpus instances; cross-reference audit confirmed
    # only 6/6328 unresolved xrefs target sections (0.1%), so the
    # preservation upside is negligible for now.
    text = re.sub(r"\{\{\s*section\s*\|[^{}]*\}\}", "", text,
                  flags=re.IGNORECASE)
    # `<p {{Ts|...ac...}}>content</p>` — paragraph centering, appears
    # in body prose AND inside refs/footnotes/captions.  Convert to the
    # universal `«CTR»` marker BEFORE the catch-all sees the `{{Ts|}}`.
    # ~173 corpus instances; 95% include `ac` (center-align), the rest
    # have margin/sizing styling we drop.  Handled here in
    # `_unwrap_content_templates` (not in `_transform_body_text`) so it
    # runs in every text-transform context — bodies, refs, captions,
    # cells.  Without this, refs that wrap a centered equation lose
    # the centering (MOLECULE's footnotes contain centered formulas).
    def _ts_block(codes_str: str, content: str,
                  force_center: bool = False) -> str:
        # Carry the FULL `{{Ts}}` styling (carry-by-default), not just center.
        # Pure-center stays the canonical «CTR» (byte-identical to before);
        # anything more becomes a styled block «DIV[style:CSS]» (the viewer
        # renders it, incl. block props like text-indent an inline span can't
        # hold); empty → unwrap.  `_parse_ts_codes` is the cell/row parser.
        from britannica.pipeline.stages.elements._tables import _parse_ts_codes
        css = _parse_ts_codes(codes_str)
        if force_center and "text-align:center" not in css:
            css = ["text-align:center", *css]
        if not css:
            return content
        if css == ["text-align:center"]:
            return f"«CTR»{content}«/CTR»"
        return f"«DIV[style:{';'.join(css)}]»{content}«/DIV»"
    def _p_ts(m: re.Match) -> str:
        return _ts_block(m.group(1), m.group(2).strip())
    text = re.sub(
        r"<p\s+\{\{[Tt]s\|([^}]*)\}\}[^>]*>(.*?)</p>",
        _p_ts, text, flags=re.DOTALL)
    # `<div {{Ts|…}}>content</div>` — sibling of the `<p {{Ts|…}}>`
    # handler above for the `<div>` variant of the same shape: an HTML
    # block wrapper around flowing prose whose attributes are packed in
    # the `Ts` template (text-indent, sm92, lh12, ac, …).  Same logic:
    # `ac` → «CTR» marker, else unwrap-only (presentation lost in
    # flowing HTML).  167 corpus instances of pure-prose `<div>`
    # wrappers (taxonomic enumerations like SUBORDER lists, dairy
    # cleanliness rules under MILK, scholarly small-type asides).
    # The 6 image-bearing variants reach this stage as walker FIGURE
    # extracts (via `html_ts_figure_end`) and never appear here.
    # The `(?P<attrs>[^>{}]*?)` slot between `<div\s+` and `{{Ts|…}}`
    # tolerates other HTML attributes — ~108 corpus instances of
    # CRYSTALLOGRAPHY-style `<div align=center {{Ts|pt1|lg}}>…</div>`
    # (centred boldface system-name headings between sections) carry
    # `align=center` before the `Ts` block.  `[^>{}]` keeps the match
    # inside the opener tag (no crossing `>`) and outside any nested
    # template (no crossing `{`).  Center-signal is read from either
    # an `ac` code OR an `align=center`/`text-align:center` attr in
    # the prefix slot.
    def _div_ts(m: re.Match) -> str:
        force_center = bool(re.search(
            r"""align\s*=\s*['"]?center|text-align\s*:\s*center""",
            m.group("attrs"), re.IGNORECASE))
        return _ts_block(m.group("codes"), m.group("content").strip(),
                         force_center)
    text = re.sub(
        r"<div\s+(?P<attrs>[^>{}]*?)\{\{[Tt]s\|(?P<codes>[^}]*)\}\}"
        r"[^>]*>(?P<content>.*?)</div>",
        _div_ts, text, flags=re.DOTALL,
    )
    # `<span ...{{Ts|codes}}...>` — inline styling.  Unlike the <p>/<div>
    # prose wrappers above (where only the center signal survives), a span's
    # styling is STRUCTURAL: the math limit-notation spans
    # (`{{Ts|display:inline-block;|ac|vbm|lh11|fs120}}`) stack the limit via
    # inline-block + vertical-align, the over-bar spans (`{{ts|bt}}`) draw a
    # rule.  So carry the FULL `{{Ts}}` → `style="…"` (`_parse_ts_codes`, the
    # same parser cells/rows use) rather than reducing to «CTR».  Rewrites the
    # opening tag only; content + `</span>` are untouched, so nested spans
    # fold independently.  Drains the 23 `<span {{Ts}}>` Ts-leaks.
    def _span_ts(m: re.Match) -> str:
        from britannica.pipeline.stages.elements._tables import _parse_ts_codes
        pre, post = m.group("pre").strip(), m.group("post").strip()
        css = _parse_ts_codes(m.group("codes"))
        out = "<span"
        if pre:
            out += " " + pre
        if css:
            out += f' style="{";".join(css)}"'
        if post:
            out += " " + post
        return out + ">"
    text = re.sub(
        r"<span\s+(?P<pre>[^>{}]*?)\{\{[Tt]s\|(?P<codes>[^}]*)\}\}"
        r"(?P<post>[^>]*)>",
        _span_ts, text)
    # {{brace2|N|side}} — vertical or horizontal grouping brace.  Two
    # distinct uses (corpus-audited 2026-05-26, task #31):
    #   * Multi-row (N≥2) inside wikitables: row-grouping brace.  May
    #     be data-table annotation OR outline-in-disguise (the user's
    #     hypothesis under #31, verify-before-acting).
    #   * Single-row (N=1) in body math: inline grouping bracket
    #     (proper math notation, e.g. ALGEBRA's polynomial expansions).
    # Sides: `l`/`r` (vertical, 99% of cases), `u`/`d` (horizontal
    # column-grouping, rare).  Some source spans the side with italic
    # markup (``''r''``) — strip the italic markers when normalising.
    # Preserve as `«BRACE2[N|side]»` marker; viewer renders per side.
    text = re.sub(
        r"\{\{\s*brace2\s*\|\s*(\d+)\s*\|\s*(?:'')?([lrud])(?:'')?\s*\}\}",
        lambda m: f"«BRACE2[{m.group(1)}|{m.group(2).lower()}]»",
        text, flags=re.IGNORECASE)
    # {{xx-larger|X}} / {{x-larger|X}} — math grouping characters scaled
    # up for tall equations: `(`, `)`, `√`, `[`, `]`.  Source uses 200%
    # / 150% size respectively.  STEAM_ENGINE / ORDNANCE: 22 occurrences;
    # losing them silently broke equation grouping (the bare `(` would
    # vanish, leaving the equation mis-grouped).  Emit per-size markers
    # so the viewer scales appropriately.  Brace-counted unwrap so a
    # literal `{` inside content (math square-root opener `{{xx-larger|√ {}}`)
    # doesn't break the pairing.
    text = _unwrap_balanced(text, "xx-larger",
                            lambda inner: f"{_FMT}XXL{inner}{_FMT}/XXL")
    text = _unwrap_balanced(text, "x-larger",
                            lambda inner: f"{_FMT}XL{inner}{_FMT}/XL")
    # Complete the size scale SYMMETRICALLY (down-steps + plain `larger`).
    # Previously these flattened to bare text in `_unwrap_content_templates`
    # / `_unwrap_layout_templates`, dropping the size signal on ~12k corpus
    # instances (the smaller half was the missing mirror of «XL»/«XXL»).
    # Now each carries a graduated marker; the viewer renders the scale
    # (.size-lg/.size-sm/.size-xs/.size-xxs).  Longest names first so the
    # balanced matcher resolves `xx-smaller` before `x-smaller`/`smaller`.
    text = _unwrap_balanced(text, "larger",
                            lambda inner: f"{_FMT}LG{inner}{_FMT}/LG")
    text = _unwrap_balanced(text, "xx-smaller",
                            lambda inner: f"{_FMT}XXS{inner}{_FMT}/XXS")
    text = _unwrap_balanced(text, "x-smaller",
                            lambda inner: f"{_FMT}XS{inner}{_FMT}/XS")
    text = _unwrap_balanced(text, "smaller",
                            lambda inner: f"{_FMT}SM{inner}{_FMT}/SM")
    text = _unwrap_balanced(text, "sm",
                            lambda inner: f"{_FMT}SM{inner}{_FMT}/SM")
    # `{{lh|<line-height>|content}}` — line-height wrapper (tightens
    # multi-line captions so label/description/citation read as one unit,
    # e.g. AEGEAN plate figure legends).  Previously the inner templates
    # resolved to markers, then `{{lh|88%|«SC»…}}` (now brace-free) was
    # eaten WHOLE by `_strip_templates` — silent caption loss, invisible
    # to leak_scan.  CARRY the line-height (it spaces the lines — dropping
    # it spreads caption and citation apart); viewer renders it.
    def _lh_carry(inner: str) -> str:
        head, sep, tail = inner.partition("|")
        if sep and re.fullmatch(r"\s*[\d.]+\s*(?:%|px|em)?\s*", head):
            return f"«LH[{head.strip()}]»{tail}«/LH»"
        return inner
    text = _unwrap_balanced(text, "lh", _lh_carry)
    # `{{float right|X}}` / `{{zfloat right|X}}` / `{{float left|X}}` — content
    # floated to the margin: contributor-initial signatures (`(A. P. C.)`,
    # `(E. H. Palmer's translation.)`) and right-floated marginal annotations
    # (`† «I»in carcere«/I»`, `«I»resignat.«/I»` — status notes in chronological
    # tables).  Previously DELETED whole by `_strip_templates` (the float-scan
    # worklist's biggest content loss).  Carry «FR»/«FL»; viewer renders the
    # float.  `float center` → the existing «CTR».
    text = _unwrap_balanced(text, "float right", lambda inner: f"«FR»{inner}«/FR»")
    text = _unwrap_balanced(text, "zfloat right", lambda inner: f"«FR»{inner}«/FR»")
    text = _unwrap_balanced(text, "float left", lambda inner: f"«FL»{inner}«/FL»")
    text = _unwrap_balanced(text, "float center", lambda inner: f"«CTR»{inner}«/CTR»")
    # `{{11co|D|M|S|dir}}` / `{{EB1911 Coordinates|…}}` — geographic
    # coordinates (D°M′S″ + N/S/E/W).  Deterministic formatting (args →
    # text), like fractions — format in place; no marker, no viewer work.
    # Args vary (D|dir, D|M, D|M|dir, D|M|S|dir): numeric parts take °/′/″ by
    # position, the letter is the hemisphere.  Previously DELETED whole by
    # `_strip_templates` (the coordinates leaked as nothing — silent loss).
    def _coord_fmt(inner: str) -> str:
        parts = [p.strip() for p in inner.split("|") if p.strip()]
        sym = ["°", "′", "″"]
        nums = [p for p in parts if p.isdigit()]
        dirs = [p.upper() for p in parts if re.fullmatch(r"[NSEWnsew]", p)]
        deg = " ".join(n + (sym[i] if i < 3 else "") for i, n in enumerate(nums))
        return (deg + (" " + dirs[0] if dirs else "")).strip()
    text = _unwrap_balanced(text, "11co", _coord_fmt)
    text = _unwrap_balanced(text, "EB1911 Coordinates", _coord_fmt)
    # Underline family ({{underline}}, {{double underline}}, {{u}}) → «U»;
    # {{strikethrough}} → «STK».  Both were DELETED whole by _strip_templates.
    text = _unwrap_balanced(text, "double underline", lambda inner: f"«U»{inner}«/U»")
    text = _unwrap_balanced(text, "underline", lambda inner: f"«U»{inner}«/U»")
    text = _unwrap_balanced(text, "u", lambda inner: f"«U»{inner}«/U»")
    text = _unwrap_balanced(text, "strikethrough", lambda inner: f"«STK»{inner}«/STK»")
    # Size-extras — all reuse the existing «FS[n%]» marker (no new viewer
    # work).  {{fsNN|X}} carries the % in the name (fs70/fs85/fs90); the
    # named {{font-size|N%|X}} / {{font size|N%|X}} match {{fs|N%|X}};
    # {{xxx-larger}}/{{xxxx-larger}} extend the larger scale (250/300%).
    text = re.sub(r"\{\{fs(\d{1,3})\|([^{}]*)\}\}",
                  lambda m: f"«FS[{m.group(1)}%]»{m.group(2)}«/FS»",
                  text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{font[- ]size\|([^{}|]+)\|([^{}]*)\}\}",
                  lambda m: f"«FS[{m.group(1).strip()}]»{m.group(2)}«/FS»",
                  text, flags=re.IGNORECASE)
    text = _unwrap_balanced(text, "xxxx-larger", lambda inner: f"«FS[300%]»{inner}«/FS»")
    text = _unwrap_balanced(text, "xxx-larger", lambda inner: f"«FS[250%]»{inner}«/FS»")
    # Inline typography wrappers — content carriers previously falling
    # to `_strip_templates`, so the catch-all deleted both wrapper and
    # content. Corpus-audit counts (2026-05-28): bold 2 (with nested
    # {{Greek|…}}), bl 30, smb 31, nw 24, di 16, x-smaller 40,
    # word-spacing 36.
    #
    # `bold`, `bl`, `smb` — bold variants. `bl|X` is a bold single
    # letter (math/table label), `smb|X` small bold; both reduce to
    # «B»…«/B» (the small-bold size distinction is lost — present
    # `«B»` is the only bold marker we carry).
    text = _unwrap_balanced(text, "bold",
                            lambda inner: f"{_FMT}B{inner}{_FMT}/B")
    text = re.sub(r"\{\{\s*(?:bl|smb)\s*\|([^{}]*)\}\}",
                  lambda m: f"{_FMT}B{m.group(1)}{_FMT}/B",
                  text, flags=re.IGNORECASE)
    # `nw|TEXT` (no-wrap: typographic hint that TEXT shouldn't break
    # across a line) and `di|X` (drop-initial: decorative large
    # opening letter at section start) — both content-pass-through
    # with presentation lost in flowing HTML.  Unwrap to content.
    text = re.sub(r"\{\{\s*(?:nw|di)\s*\|([^{}]*)\}\}",
                  r"\1", text, flags=re.IGNORECASE)
    # Layout/spacing scatter (leak-tail) — all previously DELETED whole by
    # `_strip_templates`.  None are nesting issues (those are the fake-recursion
    # class); these are flat: unwrap-to-content / space / strip-contentless.
    #   * Styling wrappers we don't reproduce → unwrap to content (text survives,
    #     like nw/di): {{lsp|[v|]X}} / {{letter-spacing|v|X}} / {{font-stretch|[v|]X}}
    #     (letter/word-spacing, stretch) and {{pad thin|X}} (thin padding).
    text = re.sub(
        r"\{\{\s*(?:lsp|letter-spacing|font-stretch)\s*\|(?:[^{}|]*\|)?([^{}]*)\}\}",
        r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{\s*pad thin\s*\|([^{}]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    #   * Spacing/break: {{fsp}} → figure space (U+2007); {{parabr}} → paragraph break.
    text = re.sub(r"\{\{\s*fsp\s*\}\}", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{\s*parabr\s*\}\}", "\n\n", text, flags=re.IGNORECASE)
    #   * Contentless column/clear layout markers → strip; the content between
    #     flows normally (single-column in our reflowing layout).
    text = re.sub(r"\{\{\s*multicol(?:-break|-end)?(?:\s*\|[^{}]*)?\s*\}\}", "",
                  text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{\s*(?:clear|nopt)\s*\}\}", "", text, flags=re.IGNORECASE)
    #   * Brace glyphs the existing «BRACE2[N|side]» handler misses: no-side
    #     {{brace2|N}} (default left) and side-first {{brace|side|…}}.
    text = re.sub(r"\{\{\s*brace2\s*\|\s*(\d+)\s*\}\}",
                  lambda m: f"«BRACE2[{m.group(1)}|l]»", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{\s*brace\s*\|\s*([lrud])\b[^{}]*\}\}",
                  lambda m: f"«BRACE2[1|{m.group(1).lower()}]»", text, flags=re.IGNORECASE)
    # `x-smaller|TEXT` — small typography (smaller-than-small; used
    # for parenthetical inline labels like `{{x-smaller|[HISTORY}}`
    # in HISTORY-tagged article headers).  Whitespace-padded residual
    # not caught by the balanced «XS» pass above — carry «XS» here too
    # (don't flatten; keep the size signal).
    text = re.sub(r"\{\{\s*x-smaller\s*\|([^{}]*)\}\}",
                  lambda m: f"{_FMT}XS{m.group(1)}{_FMT}/XS",
                  text, flags=re.IGNORECASE)
    # `word-spacing|Npx|TEXT` — extra inter-word spacing (typography).
    # Lost in flowing HTML; unwrap second arg.
    text = re.sub(r"\{\{\s*word-spacing\s*\|[^{}|]*\|([^{}]*)\}\}",
                  r"\1", text, flags=re.IGNORECASE)
    # `rule|...` — same N-em rule as {{bar|N}}, alternate template.
    # Two arg forms in corpus: `{{rule|4em}}` (em-suffix) and
    # `{{rule|width=12em}}` (named arg).  Strip non-digit suffix to
    # reuse the BAR[N] marker the viewer already renders.
    def _rule_to_bar(m: re.Match) -> str:
        arg = m.group(1)
        digits = re.search(r"(\d+)", arg)
        return f"{_FMT}RULE[{digits.group(1)}]" if digits else ""
    text = re.sub(r"\{\{\s*rule\s*\|([^{}]*)\}\}",
                  _rule_to_bar, text, flags=re.IGNORECASE)
    # {{bar|N}} — N-em horizontal rule, used for column-sum underlines
    # in tables (AFRICA / GREAT BRITAIN territorial summaries) and a few
    # other inline-rule contexts.  Single numeric arg, no content;
    # emit as a labeled marker so the viewer can render the rule width.
    # Sentinel uses `RULE` (not `BAR`) because `\x05B` is the bold-open
    # sentinel — `\x05BAR` would collide with it in _finalize_markers.
    text = re.sub(r"\{\{bar\|(\d+)\}\}",
                  lambda m: f"{_FMT}RULE[{m.group(1)}]",
                  text, flags=re.IGNORECASE)
    # Body-context running-header rows: {{rh|LEFT|MIDDLE|RIGHT}} —
    # 3-column layout used to label equation rows in math articles
    # (MOLECULE p.688: ``{{rh|(ii)|<eq chain>|}}``). Same template name
    # as the page-heading rh consumed in detect_boundaries; body-
    # context occurrences fall through to here. Tab-join non-empty
    # slots, matching the {{ne}} convention. Without this, the row's
    # entire middle arg (the equation chain) is eaten by the catch-all
    # template stripper because the outer ``{{rh|...|...|...}}`` has
    # too many pipes to satisfy ``[^{}|]*``-arg patterns.
    def _rh_body(m: re.Match) -> str:
        slots = [m.group(1).strip(), m.group(2).strip(), m.group(3).strip()]
        return "\t".join(s for s in slots if s)
    text = re.sub(
        r"\{\{(?:rh|RunningHeader)\|([^{}|]*)\|([^{}|]*(?:\{\{[^{}]*\}\}[^{}|]*)*)\|([^{}]*)\}\}",
        _rh_body, text, flags=re.IGNORECASE,
    )
    # Hanging indent → unwrap to content
    text = re.sub(r"\{\{hanging indent\|([^{}]*(?:\{\{[^{}]*\}\}[^{}]*)*)\}\}",
                  r"\1", text, flags=re.IGNORECASE)
    # ``{{hi|…}}`` — hanging-indent shorthand. Two argument forms:
    #   ``{{hi|content}}``           — indented content, no size spec
    #   ``{{hi|N(em|px)|content}}``  — explicit indent amount + content
    # The indent arg is presentation-only (we don't render it in
    # plain HTML), so drop any size prefix and keep the content.
    # ORCHIDS Fig. 2 legend uses ``{{hi|3em|…}}`` per entry; the
    # generic ``_unwrap_balanced`` at the end of ``_transform_text_v2``
    # would strip only the ``{{hi|`` and ``}}`` delimiters, leaving
    # ``3em|`` visible in the caption — hence these dedicated handlers.
    text = re.sub(
        r"\{\{hi\|[^{}|]*\|([^{}]*(?:\{\{[^{}]*\}\}[^{}]*)*)\}\}",
        r"\1", text, flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\{\{hi\|([^{}]*(?:\{\{[^{}]*\}\}[^{}]*)*)\}\}",
        r"\1", text, flags=re.IGNORECASE,
    )
    # Binomial coefficient: {{binom|n|r}} → KaTeX-rendered binom
    def _binom_to_math(m: re.Match) -> str:
        top = m.group(1).replace("''", "")
        bot = m.group(2).replace("''", "")
        return f"\u00abMATH:\\binom{{{top}}}{{{bot}}}\u00ab/MATH\u00bb"
    text = re.sub(r"\{\{binom\|([^{}|]*)\|([^{}|]*)\}\}",
                  _binom_to_math, text, flags=re.IGNORECASE)
    # Missing content markers → visible editorial notes
    text = re.sub(r"\{\{missing table\}\}", "[Table missing from source]", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{missing image\}\}", "[Image missing from source]", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{formula missing\}\}", "[Formula missing from source]", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{missing math\}\}", "[Formula missing from source]", text, flags=re.IGNORECASE)
    # Structural spacers (no visible output)
    text = re.sub(r"\{\{nop\}\}", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{clear\}\}", "", text, flags=re.IGNORECASE)
    # Special markers
    text = re.sub(r"\{\{sic\}\}", "[sic]", text, flags=re.IGNORECASE)
    # {{sic|word}} — preserve the marked word (SIC tag means the
    # original spelling is intentional, not a typo).
    text = re.sub(
        r"\{\{sic\|([^{}|]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    # Strip anchor templates (no visible output)
    text = re.sub(r"\{\{anchor\|[^{}]*\}\}", "", text, flags=re.IGNORECASE)
    return text


def _convert_shoulder_headings(text: str) -> str:
    """{{EB1911 Shoulder Heading|text}} → «SH»text«/SH»

    ``{{EB9 Margin Note|text}}`` is the 9th-edition synonym — the same
    construct, a marginal topic label for the following paragraph (VARIATIONS,
    CALCULUS OF: "Euler", "Lagrange", "Formulation of the First Problem.") —
    so it converts to the same «SH» marker (margin furniture; the viewer inlines
    it on narrow screens).  Previously deleted whole by ``_strip_templates``.

    Handles nested templates (e.g. {{Fs|108%|...}}) inside the heading.
    Consumes surrounding newlines to prevent false paragraph breaks.
    """
    prefixes = ("{{eb1911 shoulder heading", "{{eb9 margin note")
    while True:
        low = text.lower()
        cands = [(low.find(p), p) for p in prefixes]
        cands = [(pos, p) for pos, p in cands if pos >= 0]
        if not cands:
            break
        idx, prefix = min(cands)
        # Find balanced closing }}
        depth = 0
        i = idx
        while i < len(text) - 1:
            if text[i:i+2] == "{{":
                depth += 1
                i += 2
            elif text[i:i+2] == "}}":
                depth -= 1
                if depth == 0:
                    # Extract content: everything after the last | at depth 1
                    inner = text[idx+len(prefix):i]
                    # Find the last top-level | to get the actual heading
                    # text. Treat \x06…\x06 link markers and [[…]] as
                    # atomic — their internal pipes are not delimiters.
                    def _top_level_pipes(s):
                        d = 0
                        in_link = False
                        in_bracket = 0
                        pipes = []
                        k = 0
                        while k < len(s):
                            ch = s[k]
                            if ch == _LNK:
                                in_link = not in_link
                            elif not in_link:
                                if s[k:k+2] == "[[":
                                    in_bracket += 1
                                    k += 2
                                    continue
                                if s[k:k+2] == "]]":
                                    in_bracket -= 1
                                    k += 2
                                    continue
                                if ch == "{":
                                    d += 1
                                elif ch == "}":
                                    d -= 1
                                elif ch == "|" and d == 0 and in_bracket == 0:
                                    pipes.append(k)
                            k += 1
                        return pipes
                    pipes = _top_level_pipes(inner)
                    last_pipe = pipes[-1] if pipes else -1
                    heading_text = inner[last_pipe+1:] if last_pipe >= 0 else inner
                    # If we got an attribute instead of heading text, walk back
                    # through pipes until we find actual text
                    _ATTR_RE = re.compile(r"\s*(?:align|width|style)\s*=", re.IGNORECASE)
                    pipe_idx = len(pipes) - 1
                    while _ATTR_RE.match(heading_text) and pipe_idx > 0:
                        pipe_idx -= 1
                        prev_pipe = pipes[pipe_idx]
                        heading_text = inner[prev_pipe+1:last_pipe]
                        last_pipe = prev_pipe
                    # Strip inner templates, bold/italic, and line breaks
                    heading_text = re.sub(r"<br\s*/?>", " ", heading_text, flags=re.IGNORECASE)
                    heading_text = re.sub(r"\{\{[^{}]*\|([^{}]*)\}\}", r"\1", heading_text)
                    heading_text = (heading_text
                                    .replace("«B»", "").replace("«/B»", "")
                                    .replace("«I»", "").replace("«/I»", ""))
                    # Rejoin hyphenated words split across lines
                    heading_text = re.sub(r"(\w)- (\w)", r"\1\2", heading_text)
                    # Collapse em-spaces and extra whitespace
                    heading_text = heading_text.replace("\u2003", " ")
                    heading_text = re.sub(r"\s{2,}", " ", heading_text).strip()
                    marker = f"{_SH}SH{heading_text}{_SH}/SH"
                    # Consume surrounding newlines to keep text flowing
                    start = idx
                    end = i + 2
                    if start > 0 and text[start-1] == "\n":
                        start -= 1
                    if end < len(text) and text[end] == "\n":
                        end += 1
                    text = text[:start] + " " + marker + " " + text[end:]
                    break
                i += 2
            else:
                i += 1
        else:
            break  # unbalanced
    return text


def _find_balanced_template(
    text: str, name: str, start: int = 0,
) -> tuple[int, int, int] | None:
    """Find the next ``{{name|…}}`` opener at or after ``start``, matching
    via balanced ``{{`` / ``}}`` depth counting (so the inner content may
    carry literal single braces — e.g. ``{{xx-larger|√ {}}`` from
    STEAM_ENGINE's Q=V equation, where ``{`` is a math square-root
    opener, not a template open).

    Returns ``(open_idx, content_start, close_idx)`` where
    ``text[open_idx : close_idx + 2]`` is the full ``{{…}}`` span and
    ``text[content_start : close_idx]`` is the inner content (after the
    template name and the pipe).  Returns ``None`` if no balanced match
    is found.  Case-insensitive on the template name, and tolerant of
    whitespace around it — MediaWiki ignores it, and source carries
    ``{{ Fine block|…}}`` / ``{{fine block |…}}`` variants that a literal
    ``{{name|`` match dropped to ``_strip_templates`` (content lost)."""
    opener = re.compile(r"\{\{\s*" + re.escape(name) + r"\s*\|", re.IGNORECASE)
    om = opener.search(text, start)
    if om is None:
        return None
    idx = om.start()
    content_start = om.end()
    depth = 1
    j = content_start
    n = len(text)
    while j < n - 1:
        if text[j:j + 2] == "{{":
            depth += 1
            j += 2
        elif text[j:j + 2] == "}}":
            depth -= 1
            if depth == 0:
                return (idx, content_start, j)
            j += 2
        else:
            j += 1
    return None


def _unwrap_balanced(text: str, name: str, substitute) -> str:
    """Unwrap every balanced ``{{name|…}}`` via ``substitute(inner)``.

    ``substitute`` takes the inner content (with any leading MediaWiki
    positional-parameter name like ``1=`` already stripped) and returns
    the replacement bytes.  Unbalanced openers (no matching ``}}``) are
    left intact and skipped — the scanner advances past them."""
    out: list[str] = []
    pos = 0
    while True:
        m = _find_balanced_template(text, name, pos)
        if m is None:
            out.append(text[pos:])
            return "".join(out)
        idx, content_start, close_idx = m
        out.append(text[pos:idx])
        inner = text[content_start:close_idx]
        # Strip leading MediaWiki positional-parameter name (``1=``).
        # MediaWiki accepts ``{{center|1=payload}}`` for templates that
        # might otherwise mis-parse a content-leading ``=`` as a named
        # arg; we don't want ``1=`` leaking through into the unwrapped
        # output.
        inner = re.sub(r"^\d+=", "", inner)
        out.append(substitute(inner))
        pos = close_idx + 2


_LAYOUT_TEMPLATES = (
    "fine block", "smaller block",
    "EB1911 Fine Print", "larger", "smaller", "nowrap",
    "Fine", "sm",
)
# Center-family templates — DEDICATED handling (emit `«CTR»` marker
# instead of unwrap-to-content), so the centering signal survives end-
# to-end.  All variants (center / c / block center / paired begin-end
# forms) collapse to one marker; viewer renders with text-align:center.
_CENTER_INLINE_TEMPLATES = ("center", "c", "block center", "center block")


def _unwrap_layout_templates(text: str) -> str:
    """Unwrap layout-only templates to their content (the text producer owns
    this — formerly duplicated by Layer-A's ``balanced_unwrap``/``c_unwrap``/
    ``poem_unwrap``/``fine_print_se``).  ``{{csc|…}}`` → ``«SC»…«/SC»``
    with surrounding paragraph breaks.  The fixed-point loop in
    ``_transform_body_text`` resolves nesting one level per pass (e.g.
    ``{{fine block|{{block center|…}}}}``).

    Uses brace-counted matching so templates whose inner content carries
    literal single braces (the math square-root ``{`` in STEAM_ENGINE's
    Q=V equation, the math grouping braces in ALPHABET's Carian alphabet
    inscriptions, etc.) unwrap correctly — a regex-only
    ``\\{\\{[^{}]*\\}\\}`` inner-template pattern leaks the outer wrapper
    as visible markup when an inner template contains an unbalanced
    single ``{`` or ``}``."""
    for name in _LAYOUT_TEMPLATES:
        text = _unwrap_balanced(text, name, lambda inner: inner)
    text = _unwrap_balanced(
        text, "csc",
        lambda inner: f"\n\n«CTR»{_FMT}SC{inner}{_FMT}/SC«/CTR»\n\n")
    return text


def _convert_sub_sup(text: str) -> str:
    """`<sub>x</sub>`/`<sup>x</sup>` AND the `{{sub|x}}`/`{{sup|x}}`
    template forms → Unicode subscript / superscript.

    Sub/sup are typography (chem subscripts, math exponents, French
    ordinals, footnote markers) — NOT math.  This function owns both
    syntactic forms: it first rewrites the template form to the HTML
    form, then translates the HTML span.  Lifting templates here
    instead of at the walker keeps the volume of small inline elements
    out of the classifier/producer dispatch.

    Element placeholders (``\\x03ELEM:N\\x03``) inside the matched
    HTML span are preserved verbatim — their digit IDs would otherwise
    be translated to Unicode superscripts and break the marker
    substitution.  STEAM_ENGINE's nozzle equation has
    ``D<sup>{{sfrac|1|n}}</sup>`` — the inner sfrac is a walker
    element placeholder; only the surrounding chars get translated.
    """
    text = re.sub(r"\{\{\s*sub\s*\|([^{}]*)\}\}", r"<sub>\1</sub>",
                  text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{\s*sup\s*\|([^{}]*)\}\}", r"<sup>\1</sup>",
                  text, flags=re.IGNORECASE)
    _SUB = str.maketrans("0123456789+-=()", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎")
    _SUP = str.maketrans("0123456789+-=()", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾")
    _PLACEHOLDER_SPAN = re.compile(r"\x03[^\x03]*\x03")

    def _strip_wiki_format(s):
        """Strip bold/italic markers from sub/sup content."""
        return (s.replace("«B»", "").replace("«/B»", "")
                 .replace("«I»", "").replace("«/I»", ""))

    def _translate_around_placeholders(s: str, table) -> str:
        """Apply ``str.translate(table)`` to every non-placeholder span,
        leaving ``\\x03ELEM:N\\x03`` placeholders verbatim so their
        digit IDs survive for the marker-substitution pass."""
        parts = []
        last = 0
        for m in _PLACEHOLDER_SPAN.finditer(s):
            parts.append(s[last:m.start()].translate(table))
            parts.append(m.group(0))
            last = m.end()
        parts.append(s[last:].translate(table))
        return "".join(parts)

    def _sub_repl(m):
        return _translate_around_placeholders(
            _strip_wiki_format(m.group(1)), _SUB)

    def _sup_repl(m):
        return _translate_around_placeholders(
            _strip_wiki_format(m.group(1)), _SUP)

    text = re.sub(r"<sub>([^<]*)</sub>", _sub_repl, text, flags=re.IGNORECASE)
    text = re.sub(r"<sup>([^<]*)</sup>", _sup_repl, text, flags=re.IGNORECASE)
    return text




def _strip_templates(text: str) -> str:
    """Strip all remaining {{...}} wiki templates and orphaned markup.

    DRAIN-AND-DELETE CAMPAIGN (2026-05-31): this is a disguised sweeper —
    it silently deletes every unhandled {{template}} (content and all),
    invisible to leak_scan.  Worklist = `strip_scan.py` (real-pipeline
    mirror).  Draining each family upstream until this records zero, then
    deleting the function.  Measure with strip_scan, NOT leak_scan (whose
    render_proto engine over-reports page-furniture consumed upstream)."""
    # Iterative stripping handles nesting — preserve our own markers
    prev = None
    while prev != text:
        prev = text
        text = _STRIP_TEMPLATES_RE.sub("", text)
    # Note: unclosed-opener stripping is handled targeted per-template
    # (see `_strip_unclosed_nowrap` in _transform_text_v2). A blanket
    # `{{name|` strip here is unsafe — it drops openers of balanced
    # templates whose content confuses the `[^{}]*` pattern (e.g.
    # templates with literal `{`/`}` in text), leaving orphan `}}`.
    # Orphaned closing braces (standalone lines)
    text = re.sub(r"^\s*\}\}+\s*$", "", text, flags=re.MULTILINE)
    # Trailing orphaned }} at end of lines (from unclosed fine block/print
    # templates). Only strip when the line has more `}}` than `{{` — valid
    # markers like {{IMG:...}} balance out and must not have their `}}` eaten.
    def _strip_excess_closers(m):
        line = m.group(0)
        opens = len(re.findall(r"\{\{", line))
        closes = len(re.findall(r"\}\}", line))
        if closes > opens:
            # Strip excess closers from the end
            excess = closes - opens
            return re.sub(r"(\}\})" * excess + r"\s*$", "", line)
        return line
    text = re.sub(r"^.*$", _strip_excess_closers, text, flags=re.MULTILINE)
    # Orphaned wiki table markup
    text = re.sub(r"^\s*\|\}+\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\{\|\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\|-\s*$", "", text, flags=re.MULTILINE)
    return text


def _decode_entities(text: str) -> str:
    """Decode HTML entities to characters."""
    import html as html_mod
    return html_mod.unescape(text)


def _finalize_markers(text: str) -> str:
    """Convert control-character markers to readable «» format."""
    text = text.replace(f"{_FMT}B", "\u00abB\u00bb")
    text = text.replace(f"{_FMT}/B", "\u00ab/B\u00bb")
    text = text.replace(f"{_FMT}I", "\u00abI\u00bb")
    text = text.replace(f"{_FMT}/I", "\u00ab/I\u00bb")
    text = text.replace(f"{_FMT}SC", "\u00abSC\u00bb")
    text = text.replace(f"{_FMT}/SC", "\u00ab/SC\u00bb")
    text = text.replace(f"{_FMT}SS", "\u00abSS\u00bb")
    text = text.replace(f"{_FMT}/SS", "\u00ab/SS\u00bb")
    text = text.replace(f"{_FMT}SR", "\u00abSR\u00bb")
    text = text.replace(f"{_FMT}/SR", "\u00ab/SR\u00bb")
    text = text.replace(f"{_FMT}XXL", "\u00abXXL\u00bb")
    text = text.replace(f"{_FMT}/XXL", "\u00ab/XXL\u00bb")
    text = text.replace(f"{_FMT}XL", "\u00abXL\u00bb")
    text = text.replace(f"{_FMT}/XL", "\u00ab/XL\u00bb")
    # Down-steps + plain `larger` \u2014 symmetric with \u00abXL\u00bb/\u00abXXL\u00bb.  Longest
    # tokens first so \u00abXXS\u00bb isn't bitten by the \u00abXS\u00bb replace.
    text = text.replace(f"{_FMT}XXS", "\u00abXXS\u00bb")
    text = text.replace(f"{_FMT}/XXS", "\u00ab/XXS\u00bb")
    text = text.replace(f"{_FMT}XS", "\u00abXS\u00bb")
    text = text.replace(f"{_FMT}/XS", "\u00ab/XS\u00bb")
    text = text.replace(f"{_FMT}SM", "\u00abSM\u00bb")
    text = text.replace(f"{_FMT}/SM", "\u00ab/SM\u00bb")
    text = text.replace(f"{_FMT}LG", "\u00abLG\u00bb")
    text = text.replace(f"{_FMT}/LG", "\u00ab/LG\u00bb")
    # `{{fs|<size>|X}}` \u2192 value-bearing \u00abFS[size]\u00bbX\u00ab/FS\u00bb (parameterized).
    text = re.sub(re.escape(_FMT) + r"FS\[([^\]]*)\]",
                  lambda m: f"\u00abFS[{m.group(1)}]\u00bb", text)
    text = text.replace(f"{_FMT}/FS", "\u00ab/FS\u00bb")
    # BAR is a no-content marker (`\u00abBAR[N]\u00bb` with width).  Sentinel
    # uses RULE prefix internally to avoid the `\x05B` bold-open
    # collision; finalised marker keeps the BAR name for the viewer.
    text = re.sub(re.escape(_FMT) + r"RULE\[(\d+)\]",
                  lambda m: f"\u00abBAR[{m.group(1)}]\u00bb",
                  text)
    text = text.replace(f"{_SH}SH", "\u00abSH\u00bb")
    text = text.replace(f"{_SH}/SH", "\u00ab/SH\u00bb")
    # Link markers
    text = re.sub(
        re.escape(_LNK) + r"([^|" + re.escape(_LNK) + r"]+)\|([^" + re.escape(_LNK) + r"]+)" + re.escape(_LNK),
        lambda m: f"\u00abLN:{m.group(1)}|{m.group(2)}\u00ab/LN\u00bb",
        text,
    )
    # Strip any orphan _LNK (\x06) placeholders that didn't pair up.
    # Quality-report sweep 2026-05-08 found these in MENSURATION
    # vol 18 and ZOOLOGY vol 28 \u2014 single unclosed `\x06` chars that
    # leaked from malformed link markup in the source.  Stripping
    # late so the regex above gets first crack at any well-formed
    # marker.
    text = text.replace(_LNK, "")
    return text


def _apply_markup(text: str) -> str:
    """Shared text-transform utility: convert EB1911 source markup
    (templates, entities, sub/sup, small-caps, italic/bold, hieroglyphs,
    links) to the internal marker format.  Called by every producer that
    handles wikitext content (cell producers, caption producers, figure
    producers, footnotes, etc.) — anyone with a fragment of source that
    needs its markup canonicalised.

    Does NOT do body-prose finishing (whitespace collapse, ``\\xa0`` →
    ASCII space, paragraph-break collapse).  Those normalisations belong
    to the BODY producer's own finishing pass and should NOT be applied
    to fragments handled by other producers (cells with ``&nbsp;``
    padding, captions, etc. — body normalisations would lose information
    those producers must preserve).
    """
    # Strip HTML comments — non-rendering; the bypassed Layer-A `html_comments`
    # pass re-homed here (else they leak into output: AFRICA's
    # `<!-- Greenland is actually the largest -->`).  The walker already masks
    # comments for table-scanning, so this is purely a rendering concern.
    #
    # NEWLINE-PRESERVING: a comment surrounded by soft-wrap newlines on
    # both sides — ``\n<!-- col. 2 -->\n`` (the wikisource column-break
    # hint between physically-adjacent text lines) — must NOT collapse
    # to a paragraph break (``\n\n``); it must collapse to ONE newline so
    # the surrounding prose remains a single paragraph.  Keep the LONGER
    # adjacent run so `\n\n<!--…-->\n\n` (genuine paragraph break) stays
    # `\n\n`, and `\n<!--…-->\n` (soft-wrap interpolation) stays `\n`.
    # Without this, ORDNANCE / HYDROMEDUSAE had mid-sentence blank-line
    # breaks (FINE_WRAP_BREAK regression, ≥6 corpus hits).
    def _strip_comment(m: re.Match) -> str:
        pre, post = m.group(1) or "", m.group(2) or ""
        if not pre and not post:
            return ""
        return pre if len(pre) >= len(post) else post
    text = re.sub(r"(\n*)<!--.*?-->(\n*)", _strip_comment,
                  text, flags=re.DOTALL)
    # Unicode normalization (NFC, subscript-preserving) + audited lossless print-
    # artifact substitutions for font-portability/searchability — the bypassed
    # Layer-A `unicode`/`print_artifacts` passes re-homed in the text producer.
    text = normalize_unicode(text)
    text = replace_print_artifacts(text)
    text = _convert_hieroglyphs(text)
    text = _convert_foreign_script(text)
    # Order: content-BEARING template handlers (dual_line, overline,
    # lb-, sp) run AFTER `_convert_sub_sup` and the iterative-unwrap
    # loop below, so their content is brace-free when matched.
    # Counter-example: `{{dual line|C{{sub|6}}H{{sub|5}}|CH{{sub|3}}}}`
    # — the regex's `[^{}]*` rightly refuses nested braces, so the
    # handler must run when the inner `{{sub|...}}` is already resolved.
    # Empty-content handlers (spaces, 0, anchor+) don't care about
    # nesting and can run here.
    text = _convert_spaces(text)
    text = _convert_zero_pad(text)
    text = _convert_dotted_toc(text)
    text = _convert_anchor_plus(text)
    # `_convert_sfrac` deliberately NOT called: the single-arg form
    # `{{sfrac|n}}` was emerging from the catch-all in a way that
    # produced `¹/n` in some baselines (likely the catch-all output
    # interacting with sup/sub context).  Math-grade rendering for
    # this template needs the math pipeline, not body-text.
    text = _convert_links(text)
    # Template unwrap is a fixed-point loop: nested patterns like
    # `{{nowrap|1{{EB1911 tfrac|2}} m.}}` need the inner template
    # resolved before the outer regex (which excludes nested braces)
    # can match.  Without iteration the outer survives to the catch-all
    # stripper, which deletes the whole template including its content.
    # Bound is generous; real-world EB1911 wikitext rarely nests >2 deep.
    for _ in range(8):
        before = text
        # General recursive expander first — resolves the registered families
        # (greek/sc/lang/… ) incl. nested/pipe-bearing inners the flat passes
        # below leak; those passes then no-op on what it already handled.
        text = _expand_inline_templates(text)
        text = _unwrap_content_templates(text)
        text = _convert_shoulder_headings(text)
        text = _unwrap_layout_templates(text)
        if text == before:
            break
    # Residual `{{EB1911/DNB lkpl|…}}` whose DISPLAY held a nested {{sc}}/
    # {{small-caps}}: the early `_convert_links` pass couldn't span the braces,
    # but the unwrap loop above has now resolved them to «SC» (brace- AND
    # inner-pipe-free), so the link converts here instead of being deleted by
    # `_strip_templates` (~71 corpus instances — the lkpl leak-tail item).
    text = re.sub(r"\{\{\s*(?:EB1911|DNB)\s+lkpl\s*\|([^{}]+)\}\}",
                  lambda m: _lkpl_to_marker(m.group(1)), text, flags=re.IGNORECASE)
    text = _convert_sub_sup(text)
    # Content-bearing handlers, deferred from before the unwrap loop so
    # any inner `{{sub|N}}` / `{{sup|N}}` / unwrap-templates inside their
    # arguments are already resolved — their regexes use `[^{}]*` and
    # would otherwise reject nested templates.  (`{{dual line|…}}` was
    # also in this group; promoted to a walker-level DUAL_LINE element,
    # so body-text no longer sees the raw template here.)
    text = _convert_overline(text)
    text = _convert_lb_dash(text)
    text = _convert_sp(text)
    # Spacer templates render as the space/rule they ARE — not stripped to "" by
    # the catch-all below (that joins legend entries: BRACHIOPODA Fig 27
    # "Peduncle.{{em|2}}z" → "Peduncle.z").  The last Layer-A rendering pass
    # (`spacing`) re-homed here, in the text producer.
    #
    # Each rule allows the arg-bearing AND bare forms — previously the
    # bare forms (`{{em}}`, `{{rule|N|...}}`) fell through to the catch-
    # all and got deleted with their contents.
    text = re.sub(r"\{\{\s*em(?:\s*\|[^{}]*)?\s*\}\}", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{\s*gap(?:\s*\|[^{}]*)?\s*\}\}", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{\s*rule\s*\}\}", "———", text, flags=re.IGNORECASE)
    # {{rule|Nem|...}} — width-bearing horizontal rule (same shape as
    # `{{bar|N}}` but with optional alignment).  Reuse the `«BAR[N]»`
    # marker via the shared RULE sentinel.
    text = re.sub(r"\{\{\s*rule\s*\|\s*(\d+)\s*em\b[^{}]*\}\}",
                  lambda m: f"{_FMT}RULE[{m.group(1)}]",
                  text, flags=re.IGNORECASE)
    # {{dhr}} / {{dhr|N%}} — Display Horizontal Rule, a vertical spacer.
    # CONVERSION is universal (source → marker); the marker is data
    # the viewer renders contextually.  Specific producers that want a
    # different concrete rendering (legend's compact-inline collapse,
    # e.g. `_clean_legend_text`) handle the marker form as their own
    # override after `_apply_markup` returns.  Emit the final marker
    # directly (no `_FMT` sentinel) so the catch-all doesn't see a
    # template to delete; `«…»` form passes through `_strip_templates`.
    text = re.sub(r"\{\{\s*dhr(?:\s*\|([^{}]*))?\s*\}\}",
                  lambda m: (f"«DHR[{(m.group(1) or '').strip()}]»"
                             if (m.group(1) or '').strip()
                             else "«DHR»"),
                  text, flags=re.IGNORECASE)
    # Bold/italic markers already present from prepare_wikitext's
    # `_convert_quote_runs` (the canonical MediaWiki-aware conversion).
    # No quote-run conversion is needed here.
    # <small>/<big> HTML tags → size markers.  We now CARRY size (the viewer
    # renders «SM»/«LG»), so these are the HTML twins of {{smaller}}→«SM» /
    # {{larger}}→«LG» — not presentational wrappers to flatten.  Tag-only
    # conversion (open/close separately, so nested/cross-line content is handled
    # by the other passes); finalize turns the «…» sentinels into real markers.
    text = re.sub(r"<small\b[^>]*>", f"{_FMT}SM", text, flags=re.IGNORECASE)
    text = re.sub(r"</small\s*>", f"{_FMT}/SM", text, flags=re.IGNORECASE)
    text = re.sub(r"<big\b[^>]*>", f"{_FMT}LG", text, flags=re.IGNORECASE)
    text = re.sub(r"</big\s*>", f"{_FMT}/LG", text, flags=re.IGNORECASE)
    text = _strip_templates(text)
    text = _decode_entities(text)
    text = _finalize_markers(text)
    return text


_KNOWN_WRAPPER_TAGS: tuple[str, ...] = (
    # NB: `small`/`big` are NOT here — `_apply_markup` now carries them as
    # «SM»/«LG» size markers (we support size), rather than flattening to plain.
    "span", "div", "p", "ins",
)


def strip_known_wrapper_tags(text: str) -> str:
    """Strip an enumerated set of HTML wrapper tags, keeping each tag's
    inner content.  Each tag is listed EXPLICITLY — if a new wrapper tag
    appears in EB1911 source, it surfaces as a literal tag in output
    rather than being silently swept like the old ``_strip_html`` catch-
    all did.  This is a toolkit utility: producers that emit prose
    content (body, cell, caption, …) call it on the content they own;
    it does NOT run as part of the shared markup transform.

    Order ≠ priority — each tag is independent, and the same span never
    qualifies for two strips."""
    for tag in _KNOWN_WRAPPER_TAGS:
        text = re.sub(
            rf"<{tag}\b[^>]*>(.*?)</{tag}>", r"\1",
            text, flags=re.IGNORECASE | re.DOTALL)
    return text


def _transform_body_text(text: str) -> str:
    """Body-text producer: apply the shared markup transform, then the
    body-only finishing normalisations that prose-flow output needs.

    Called EXACTLY ONCE per article — by ``process_elements`` on the
    article body's placeholderized text.  Element producers (cells,
    captions, figures) do NOT call this — they call ``_apply_markup``
    directly via the ``text_transform`` parameter ``process_elements``
    hands them.
    """
    # Body-prose line-leading equation indent: a BALLISTICS-style
    # `:(43) <math>…</math>` line uses `:` as a typographic indent
    # sigil, not as content.  Strip the colon when it's IMMEDIATELY
    # followed by `(N)` — the only line-leading `:` shape that's a
    # bare indent rather than content (outline-depth `:` lines are
    # extracted by the walker as OUTLINE elements BEFORE this body
    # producer ever runs; this strip only sees residual prose lines).
    #
    # Narrow lookahead is the load-bearing constraint: a generic
    # `^[:;]+\s*` strip swallows mid-sentence `;`/`:` punctuation when
    # the walker has carved an element span and left a BODY fragment
    # starting with the trailing punctuation (the MATH_SEAM /
    # FN_SEAM regression — `<math>X</math>; the theorem` left
    # fragment ``; the theorem`` whose ``;`` got eaten).  Requiring
    # `(\d+)` afterwards excludes those cases without losing the
    # equation-indent use.
    text = re.sub(r"^:+\s*(?=\(\d+\))", "", text, flags=re.MULTILINE)
    text = _apply_markup(text)
    # Body-only `<br>` regularization: in flowing prose, a `<br>` is a
    # soft line break that should render as a word boundary, NOT a
    # paragraph break and not a literal tag.  This is the body
    # producer's owned rule — figure / caption / cell producers handle
    # `<br>` on their own terms (segment boundary, paragraph, etc.)
    # via their own producers, NOT by calling this function.
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    # Body-only wrapper-strip HTML rules: shared toolkit utility, called
    # explicitly here rather than absorbed into the markup transform
    # because each producer owns whether to strip wrappers (body and
    # cells yes; producer markers like {{IMG:…}} no, the rendering tags
    # IN them are deliberate).
    text = strip_known_wrapper_tags(text)
    # Body-only whitespace finishing.  These article-wide sweeps are
    # "guilty until proven innocent" per the architecture; we keep them
    # for now because the existing snapshots assume them and removing
    # them is a corpus-wide rebaseline (separate decision).  Crucially,
    # they run on the BODY's placeholderized text — placeholders are
    # opaque control chars, producer-emitted markers haven't been
    # substituted yet — so these sweeps shape the body's own prose, not
    # producer output.  Cell / caption / etc. producers call
    # ``_apply_markup`` directly (no body finishing).
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" +([,.;:!?])", r"\1", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


