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
_MARKER_OPEN_NAMES = "|".join(
    re.escape(o[2:]) for o in RENDERED_MARKER_OPENS
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

    # Unwrap nested {{sc|}} before matching EB1911 article link
    text = re.sub(
        r"(\{\{EB1911 article link\|[^}]*)(\{\{sc\|)([^}]*)(\}\})",
        lambda m: m.group(1) + m.group(3), text, flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\{\{EB1911 article link\|([^{}]*)\}\}",
        _eb1911_link, text, flags=re.IGNORECASE,
    )

    # {{1911link|Target}} or {{1911link|Target|Display}} (and 11link).
    # Positional args named like `nosc=yes` are template options, not
    # display text — drop them.
    def _link11(m):
        parts = m.group(1).split("|")
        target = parts[0].strip()
        positional = [
            p.strip() for p in parts[1:]
            if p.strip() and "=" not in p
        ]
        display = positional[0] if positional else target
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

    # {{EB1911 lkpl|...}} and {{DNB lkpl|...}}
    def _lkpl(m):
        parts = m.group(1).split("|")
        target = parts[0].strip()
        # Display is the first non-empty parameter after the target;
        # fall back to the target when all others are empty
        # (e.g. `{{EB1911 lkpl|Grebe|grebes|}}` with trailing empty arg).
        display = next((p.strip() for p in parts[1:] if p.strip()), target)
        return f"{_LNK}{target}|{display}{_LNK}"
    text = re.sub(
        r"\{\{(?:EB1911|DNB)\s+lkpl\|([^{}]+)\}\}",
        _lkpl, text, flags=re.IGNORECASE,
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


def _convert_small_caps(text: str) -> str:
    """{{sc|text}}, {{asc|text}} → «SC»text«/SC»"""
    text = re.sub(
        r"\{\{sc\|([^{}]*)\}\}",
        f"{_FMT}SC\\1{_FMT}/SC", text, flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\{\{asc\|([^{}]*)\}\}",
        f"{_FMT}SC\\1{_FMT}/SC", text, flags=re.IGNORECASE,
    )
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


def _unwrap_content_templates(text: str) -> str:
    """Unwrap content templates to their text content."""
    # Language/script templates → plain text
    text = re.sub(r"\{\{Greek\|([^{}]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{polytonic\|([^{}]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{Hebrew\|([^{}]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{lang\|[^{}|]*\|([^{}]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    # Formatting wrappers → content
    text = re.sub(r"\{\{uc\|([^{}]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{nowrap\s*\|([^{}]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{smaller\|([^{}]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{larger\|([^{}]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    # `{{Fs|<size>|<content>}}` — Wikisource font-size template, used
    # to size individual math operators (∫, (, ), {, }, etc.) in
    # table cells (HYDROMECHANICS vol 14 p138/139).  Strip the
    # wrapper, keep content.  Content can be a literal `{` or `}`
    # (math grouping brace), so `[^}]*` rather than `[^{}]*` — the
    # regex still stops at the first `}}` because of the literal
    # `\}\}` close requirement.
    text = re.sub(
        r"\{\{Fs\|[^{}|]+\|([^}]*)\}\}",
        r"\1", text, flags=re.IGNORECASE,
    )
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
    # Size/alignment wrappers → content
    text = re.sub(r"\{\{sm\|([^{}]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{right\|([^{}]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{left\|([^{}]*)\}\}", r"\1", text, flags=re.IGNORECASE)
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
    # Fractions. {{sfrac|a|b}} = {{EB1911 tfrac|a|b}} = a/b.
    # Single-arg form {{sfrac|a}} = {{EB1911 tfrac|a}} = 1/a.
    # Render common ones as Unicode vulgar fractions; rest as "a/b".
    _VULGAR = {
        ("1", "2"): "\u00bd", ("1", "4"): "\u00bc", ("3", "4"): "\u00be",
        ("1", "3"): "\u2153", ("2", "3"): "\u2154",
        ("1", "5"): "\u2155", ("2", "5"): "\u2156",
        ("3", "5"): "\u2157", ("4", "5"): "\u2158",
        ("1", "6"): "\u2159", ("5", "6"): "\u215a",
        ("1", "8"): "\u215b", ("3", "8"): "\u215c",
        ("5", "8"): "\u215d", ("7", "8"): "\u215e",
    }
    def _frac(num, den):
        return _VULGAR.get((num.strip(), den.strip()),
                           f"{num.strip()}/{den.strip()}")
    # Strip named-param args (``|font-size=100%``, ``|color=red``, …)
    # from sfrac before positional-arg extraction. MediaWiki sfrac
    # accepts styling overrides as named args; without this they fall
    # into the integer/numerator slot and leak as literal text.
    def _strip_sfrac_named_args(m: re.Match) -> str:
        template = m.group(0)
        inner = template[2:-2]
        parts = inner.split("|")
        cleaned = [parts[0]] + [p for p in parts[1:]
                                 if not re.match(r"^[a-zA-Z_-]+=", p)]
        return "{{" + "|".join(cleaned) + "}}"

    # Loop sfrac resolution to fixed point — nested forms like
    # ``{{sfrac|font-size=100%|X {{EB1911 tfrac|2|3}}|Y}}`` need the
    # inner tfrac to resolve first, then the outer sfrac to re-match
    # once its braces are no longer nested. Without iteration the outer
    # survives my regexes and gets wiped by the catch-all template
    # stripper at line ~440, dropping the entire formula's LHS.
    _SFRAC_TOKEN_RE = re.compile(r"\{\{(?:sfrac|EB1911 tfrac)\b",
                                  re.IGNORECASE)
    for _ in range(8):
        if not _SFRAC_TOKEN_RE.search(text):
            break
        before = text
        text = re.sub(
            r"\{\{(?:sfrac|EB1911 tfrac)\|[^{}]*\}\}",
            _strip_sfrac_named_args,
            text, flags=re.IGNORECASE,
        )
        # Three-arg sfrac: {{sfrac|integer|num|den}} → "integer num/den"
        text = re.sub(
            r"\{\{(?:sfrac|EB1911 tfrac)\|([^{}|]*)\|([^{}|]*)\|([^{}|]*)\}\}",
            lambda m: f"{m.group(1).strip()}{_frac(m.group(2), m.group(3))}",
            text, flags=re.IGNORECASE,
        )
        # Two-arg: {{sfrac|num|den}} → num/den
        text = re.sub(
            r"\{\{(?:sfrac|EB1911 tfrac)\|([^{}|]*)\|([^{}|]*)\}\}",
            lambda m: _frac(m.group(1), m.group(2)),
            text, flags=re.IGNORECASE,
        )
        # One-arg: {{sfrac|N}} → 1/N
        text = re.sub(
            r"\{\{(?:sfrac|EB1911 tfrac)\|([^{}|]*)\}\}",
            lambda m: _frac("1", m.group(1)),
            text, flags=re.IGNORECASE,
        )
        if text == before:
            break
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
    # Numbered equations: {{ne||content|(N)}} → an «EQN»-marked
    # labeled display block.  The viewer renders the content (which
    # may be a `<math>` block OR italic-text like `''pv''=RT`) as a
    # centred display equation with the label `(N)` floated to the
    # right margin.  Wrap with `\n\n` so the equation always sits on
    # its own paragraph — `{{ne}}` typically appears on a single
    # source line between prose sentences (one `\n` either side),
    # which reflow_paragraphs would otherwise glue back into prose.
    def _ne_labeled(m: re.Match) -> str:
        content = m.group(1).strip()
        raw_label = m.group(2).strip()
        # Source convention is `(N)` — strip the parens so the label
        # marker holds just the content, mirroring the MATH_PARA_RE
        # capture style used for multi-row rowspan systems.  Trailing
        # spacing entities (`&ensp;`, `&nbsp;`) are dropped.
        paren = re.match(r"\(([^()]+)\)", raw_label)
        label = (paren.group(1) if paren else raw_label).strip()
        # Strip wikitext italic markers (``''``) from labels.  The label
        # is emitted as ``«EQN:LABEL»content«/EQN»``; if the italic
        # span survives to the later italic-conversion pass, ``''a''``
        # becomes ``«I»a«/I»`` and the EQN open-marker's trailing ``»``
        # collides with the italic ``»`` of the label.  Viewer parses
        # the label up to the first ``»``, splitting ``10«I»a«/I»`` into
        # label=``10«I`` and stranding ``a«/I»`` onto the content.
        # ORDNANCE p244 (10''a''): canonical form for equation labels
        # is plain text — italic styling on a label is decorative noise.
        label = label.replace("''", "")
        return f"\n\n«EQN:{label}»{content}«/EQN»\n\n"

    text = re.sub(r"\{\{ne\|\|([^{}|]*(?:\{\{[^{}]*\}\}[^{}|]*)*)\|([^{}]*)\}\}",
                  _ne_labeled, text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{ne\|\|([^{}]*(?:\{\{[^{}]*\}\}[^{}]*)*)\}\}",
                  r"\n\n\1\n\n", text, flags=re.IGNORECASE)
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
        r"\{\{rh\|([^{}|]*)\|([^{}|]*(?:\{\{[^{}]*\}\}[^{}|]*)*)\|([^{}]*)\}\}",
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

    Handles nested templates (e.g. {{Fs|108%|...}}) inside the heading.
    Consumes surrounding newlines to prevent false paragraph breaks.
    """
    prefix = "{{EB1911 Shoulder Heading"
    while True:
        idx = text.lower().find(prefix.lower())
        if idx < 0:
            break
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
    is found.  Case-insensitive on the template name."""
    prefix = "{{" + name + "|"
    pref_lower = prefix.lower()
    text_lower = text.lower()
    idx = text_lower.find(pref_lower, start)
    if idx < 0:
        return None
    content_start = idx + len(prefix)
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
    "block center", "center", "c", "fine block",
    "EB1911 Fine Print", "larger", "smaller", "nowrap",
    "Fine", "sm",
)


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
        lambda inner: f"\n\n{_FMT}SC{inner}{_FMT}/SC\n\n")
    return text


def _convert_sub_sup(text: str) -> str:
    """`<sub>x</sub>`/`<sup>x</sup>` AND the `{{sub|x}}`/`{{sup|x}}` template
    forms → Unicode subscript / superscript.

    The template forms were previously left for the catch-all `_strip_templates`
    pass, which deleted them outright — silently losing ~7000 sub/superscripts
    across 195 articles (chemistry formulae `C{{sub|4}}H{{sub|9}}O{{sub|4}}` →
    `CHO`; math variables/exponents `r{{sub|12}}` → `r`, `x{{sup|2}}` → `x`).
    Normalise them to the HTML form first so the existing conversion renders
    them.  (Surfaced by routing chemistry reactions to a focused producer — see
    [[current-output-not-oracle]].)
    """
    text = re.sub(r"\{\{\s*sub\s*\|([^{}]*)\}\}", r"<sub>\1</sub>",
                  text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{\s*sup\s*\|([^{}]*)\}\}", r"<sup>\1</sup>",
                  text, flags=re.IGNORECASE)
    _SUB = str.maketrans("0123456789+-=()", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎")
    _SUP = str.maketrans("0123456789+-=()", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾")

    def _strip_wiki_format(s):
        """Strip bold/italic markers from sub/sup content."""
        return (s.replace("«B»", "").replace("«/B»", "")
                 .replace("«I»", "").replace("«/I»", ""))

    def _sub_repl(m):
        return _strip_wiki_format(m.group(1)).translate(_SUB)

    def _sup_repl(m):
        return _strip_wiki_format(m.group(1)).translate(_SUP)

    text = re.sub(r"<sub>([^<]*)</sub>", _sub_repl, text, flags=re.IGNORECASE)
    text = re.sub(r"<sup>([^<]*)</sup>", _sup_repl, text, flags=re.IGNORECASE)
    return text




def _strip_templates(text: str) -> str:
    """Strip all remaining {{...}} wiki templates and orphaned markup."""
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
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    # Unicode normalization (NFC, subscript-preserving) + audited lossless print-
    # artifact substitutions for font-portability/searchability — the bypassed
    # Layer-A `unicode`/`print_artifacts` passes re-homed in the text producer.
    text = normalize_unicode(text)
    text = replace_print_artifacts(text)
    text = _convert_hieroglyphs(text)
    text = _convert_links(text)
    # Template unwrap is a fixed-point loop: nested patterns like
    # `{{nowrap|1{{EB1911 tfrac|2}} m.}}` need the inner template
    # resolved before the outer regex (which excludes nested braces)
    # can match.  Without iteration the outer survives to the catch-all
    # stripper, which deletes the whole template including its content.
    # Bound is generous; real-world EB1911 wikitext rarely nests >2 deep.
    for _ in range(8):
        before = text
        text = _unwrap_content_templates(text)
        text = _convert_small_caps(text)
        text = _convert_shoulder_headings(text)
        text = _unwrap_layout_templates(text)
        if text == before:
            break
    text = _convert_sub_sup(text)
    # Spacer templates render as the space/rule they ARE — not stripped to "" by
    # the catch-all below (that joins legend entries: BRACHIOPODA Fig 27
    # "Peduncle.{{em|2}}z" → "Peduncle.z").  The last Layer-A rendering pass
    # (`spacing`) re-homed here, in the text producer.
    text = re.sub(r"\{\{\s*em\s*\|[^{}]*\}\}", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{\s*gap(?:\s*\|[^{}]*)?\s*\}\}", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{\s*rule\s*\}\}", "———", text, flags=re.IGNORECASE)
    # Bold/italic markers already present from prepare_wikitext's
    # `_convert_quote_runs` (the canonical MediaWiki-aware conversion).
    # No quote-run conversion is needed here.
    text = _strip_templates(text)
    text = _decode_entities(text)
    text = _finalize_markers(text)
    return text


_KNOWN_WRAPPER_TAGS: tuple[str, ...] = (
    "span", "small", "big", "div", "p", "ins",
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
    # Body-prose line-leading indent markers (`:` / `;` definition-list
    # prefix used in EB1911 for numbered-equation indents like BALLISTICS
    # `:(43) <math>…</math>`).  We don't render these as indented blocks —
    # stripping the sigil keeps the content flush.  Body-only because
    # only the body has line-leading prose context.
    text = re.sub(r"^[:;]+\s*", "", text, flags=re.MULTILINE)
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


