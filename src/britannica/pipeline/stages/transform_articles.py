"""Transform raw wikitext article bodies into internal marker format.

This stage runs after boundary detection.  Each article's body contains
raw Wikisource wikitext at this point.  We convert it to the internal
marker format (``«B»``, ``«FN:``, ``{{IMG:``, etc.) by running the same
26 fetch stages and clean_pages transformations — but per-article instead
of per-page, and skipping stage 3 (section-tag conversion) since
boundaries have already been determined.

Articles are processed one at a time and committed individually so that
only one article body is in memory at any point.
"""
from __future__ import annotations

import re

from britannica.db.models import Article, ArticleSegment, SourcePage
from britannica.db.session import SessionLocal

from britannica.cleaners.reflow import reflow_paragraphs
from britannica.cleaners.unicode import normalize_unicode
from britannica.pipeline.stages.clean_pages import _replace_score_tags


# ── Body text processing stages ──────────────────────────────────────
#
# Each function handles one kind of wiki markup.  They run on body text
# AFTER embedded elements have been extracted, so they never see tables,
# images, footnotes, poems, math, or scores.

# Control characters for intermediate markers.
# \x03 is used by elements.py for placeholders, so we avoid it.
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
        r"\{\{(?:1911link|11link)\|([^{}]+)\}\}",
        _link11, text, flags=re.IGNORECASE,
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
        display = display.replace("'''", "").replace("''", "")
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
_FRAKTUR_MAP.update({"C": "\u212D", "H": "\u210C", "I": "\u2111",
                      "R": "\u211C", "Z": "\u2128"})


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
    # Standalone image crop templates (not inside a table — those are handled
    # as DJVU_CROP elements in elements.py)
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
    # Numbered equations: {{ne||equation|(N)}} → equation  (N)
    text = re.sub(r"\{\{ne\|\|([^{}|]*(?:\{\{[^{}]*\}\}[^{}|]*)*)\|([^{}]*)\}\}",
                  r"\1\t\2", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{ne\|\|([^{}]*(?:\{\{[^{}]*\}\}[^{}]*)*)\}\}",
                  r"\1", text, flags=re.IGNORECASE)
    # Hanging indent → unwrap to content
    text = re.sub(r"\{\{hanging indent\|([^{}]*(?:\{\{[^{}]*\}\}[^{}]*)*)\}\}",
                  r"\1", text, flags=re.IGNORECASE)
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
                    heading_text = heading_text.replace("'''", "").replace("''", "")
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


def _unwrap_layout_templates(text: str) -> str:
    """Unwrap {{center|...}}, {{c|...}}, {{fine block|...}} to content.
    {{csc|...}} → «SC»...«/SC»."""
    for name in ["center", "c", "fine block", "EB1911 Fine Print"]:
        text = re.sub(
            r"\{\{" + re.escape(name) + r"\|((?:[^{}]|\{\{[^{}]*\}\})*)\}\}",
            r"\1", text, flags=re.IGNORECASE,
        )
    # {{csc|...}} = centered small caps — always a section heading,
    # so ensure paragraph breaks around it
    text = re.sub(
        r"\{\{csc\|((?:[^{}]|\{\{[^{}]*\}\})*)\}\}",
        f"\n\n{_FMT}SC\\1{_FMT}/SC\n\n", text, flags=re.IGNORECASE,
    )
    return text


def _convert_sub_sup(text: str) -> str:
    """<sub>x</sub> → Unicode subscript, <sup>x</sup> → Unicode superscript."""
    _SUB = str.maketrans("0123456789+-=()", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎")
    _SUP = str.maketrans("0123456789+-=()", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾")

    def _strip_wiki_format(s):
        """Strip '''/'' wiki formatting from sub/sup content."""
        return s.replace("'''", "").replace("''", "")

    def _sub_repl(m):
        return _strip_wiki_format(m.group(1)).translate(_SUB)

    def _sup_repl(m):
        return _strip_wiki_format(m.group(1)).translate(_SUP)

    text = re.sub(r"<sub>([^<]*)</sub>", _sub_repl, text, flags=re.IGNORECASE)
    text = re.sub(r"<sup>([^<]*)</sup>", _sup_repl, text, flags=re.IGNORECASE)
    return text


def _convert_bold_italic(text: str) -> str:
    """'''bold''' → «B»bold«/B», ''italic'' → «I»italic«/I»."""
    # Bold-italic (5 quotes) first
    text = re.sub(r"'''''(.*?)'''''",
                  lambda m: f"{_FMT}B{_FMT}I{m.group(1)}{_FMT}/I{_FMT}/B",
                  text, flags=re.DOTALL)
    # Normalize 4 quotes to 3
    text = text.replace("''''", "'''")
    # Bold (3 quotes)
    text = re.sub(r"'''(.*?)'''", f"{_FMT}B\\1{_FMT}/B", text, flags=re.DOTALL)
    # Italic (2 quotes)
    text = re.sub(r"''(.*?)''", f"{_FMT}I\\1{_FMT}/I", text, flags=re.DOTALL)
    # Strip any residual '' markers
    text = text.replace("''", "")
    return text


def _strip_templates(text: str) -> str:
    """Strip all remaining {{...}} wiki templates and orphaned markup."""
    # Iterative stripping handles nesting — preserve our own markers
    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"\{\{(?!IMG:|TABLE|VERSE:)[^{}]*\}\}", "", text)
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


def _strip_html(text: str) -> str:
    """Strip remaining HTML tags (safe on body text — elements already extracted).

    `<br>` is replaced with a space FIRST so line breaks separating
    words (e.g. `{{sc|Fig. 4.}}<br />St Mary's Abbey`) survive as word
    boundaries instead of collapsing to `Fig. 4.St Mary's Abbey`.
    """
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"</?[a-zA-Z][^>]*>", "", text)
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
    return text


def _transform_body_text(text: str) -> str:
    """Transform plain wikitext body text to internal marker format.

    Each step is explicit.  No fetch stage dependencies.
    Embedded elements have already been extracted.
    """
    text = _convert_hieroglyphs(text)
    text = _convert_links(text)
    text = _unwrap_content_templates(text)
    text = _convert_small_caps(text)
    text = _convert_shoulder_headings(text)
    text = _unwrap_layout_templates(text)
    text = _convert_sub_sup(text)
    text = _convert_bold_italic(text)
    text = _strip_templates(text)
    text = _strip_html(text)
    text = _decode_entities(text)
    text = _finalize_markers(text)
    # Normalize whitespace
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" +([,.;:!?])", r"\1", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def _transform_plate(raw_wikitext: str) -> str:
    """Transform a plate page: extract images and numbered captions, pair them.

    Plate pages are image grids with captions — not regular article text.
    No table processing, no text transformation. Just images and captions.
    """
    # Strip noinclude, section tags, comments
    text = re.sub(r"<noinclude>.*?</noinclude>", "", raw_wikitext,
                  flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<section[^>]+>', "", text, flags=re.IGNORECASE)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    # Extract all images
    images = []
    for m in re.finditer(r"\[\[(?:File|Image):([^|\]]+)", text, re.IGNORECASE):
        images.append(m.group(1).strip())

    # Extract all numbered captions.
    # Formats: "N. ALL CAPS CAPTION" or "Fig. N.—Mixed case description"
    captions = {}
    # Strip [[File:...]] content before caption search — filenames often
    # contain "Fig. N.—..." embedded in them (EB1911 - Globe - Fig. 18.—
    # The Indian Ocean...jpg), which would otherwise match the caption
    # regex and produce garbage.
    caption_text = re.sub(r"\[\[(?:File|Image):[^\]]*\]\]", "",
                          text, flags=re.IGNORECASE)
    # Format 1: N. ALL CAPS
    for m in re.finditer(r"(?<!\w)(\d+)\.\s+([A-Z][A-Z\s,.:;()\-']+)", caption_text):
        num = int(m.group(1))
        cap = m.group(2).strip().rstrip(",.|;")
        if len(cap) >= 3 and num not in captions:
            captions[num] = cap
    # Format 2: {{sc|Fig.}} N.—description, {{sc|Fig. N.}}—description,
    # or plain Fig. N.—description. Captions may wrap across lines
    # (inside <td> blocks), so capture until </td>, next Fig heading,
    # or newline.
    for m in re.finditer(
        r"(?:\{\{(?:small-caps|sc)\|Fig\.\s*(\d+)\.?\s*\}\}"
        r"|(?:\{\{(?:small-caps|sc)\|Fig\.\}\}|Fig\.)\s*(\d+)\.?)"
        r"\s*[\u2014\u2013\-]\s*"
        r"(.+?)(?=</td>|\|-|\n|\{\{(?:small-caps|sc)\|Fig\.|Fig\.\s*\d+\.|$)",
        caption_text, re.DOTALL,
    ):
        # Number is in group 1 ({{sc|Fig. N.}}) or group 2 ({{sc|Fig.}} N).
        num = int(m.group(1) or m.group(2))
        cap = m.group(3).strip().rstrip(",.|;")
        # Clean wiki markup from caption — unwrap templates that wrap text
        cap = re.sub(r"\{\{(?:uc|sc|nowrap|lang\|[^{}]*)\|([^{}]*)\}\}", r"\1", cap, flags=re.IGNORECASE)
        cap = re.sub(r"\{\{[^{}]*\}\}", "", cap)
        cap = re.sub(r"'''|''", "", cap)
        cap = re.sub(r"&amp;", "&", cap)
        cap = re.sub(r"\|\}", "", cap)  # stray table close
        cap = re.sub(r"\}\}+", "", cap)  # stray closing braces
        cap = re.sub(r"\s+", " ", cap).strip()
        if len(cap) >= 3 and num not in captions:
            captions[num] = f"Fig. {num}. {cap}"

    # Extract title lines (plate title, e.g. "EARLY EGYPTIAN ART")
    # Skip lines inside table cells (<td>, |) and avoid duplicates
    title_seen = set()
    title_lines = []
    in_table = False
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("<table") or stripped.startswith("{|"):
            in_table = True
            continue
        if stripped.startswith("</table") or stripped.startswith("|}"):
            in_table = False
            continue
        if in_table:
            continue
        if stripped.startswith("[[") or stripped.startswith("{{"):
            continue
        if stripped.startswith("|") or stripped.startswith("<tr") or stripped.startswith("<td"):
            continue
        clean = re.sub(r"\{\{[^{}]*\}\}", "", stripped)
        clean = re.sub(r"'''|''", "", clean)
        clean = re.sub(r"<[^>]+>", "", clean)
        clean = clean.strip()
        if clean and len(clean) > 2 and not re.match(r"^\d+\.", clean):
            if (clean.isupper() or clean.startswith("Plate")) and clean not in title_seen:
                title_seen.add(clean)
                title_lines.append(clean)

    # Pair images with captions by keyword matching
    sorted_caps = sorted(captions.items())
    used_images = set()
    unmatched_caps = []
    paired = []

    def _img_words(filename):
        name = filename.rsplit("/", 1)[-1]
        name = re.sub(r"\.jpg$|\.png$", "", name, flags=re.IGNORECASE)
        if " - " in name:
            name = name.rsplit(" - ", 1)[-1]
        return set(re.findall(r"[A-Za-z]{3,}", name.upper()))

    for num, cap in sorted_caps:
        cap_words = set(re.findall(r"[A-Z]{3,}", cap))
        best_img = None
        best_score = 0
        for i, img in enumerate(images):
            if i in used_images:
                continue
            img_words = _img_words(img)
            score = len(cap_words & img_words)
            if score > best_score:
                best_score = score
                best_img = i
        if best_img is not None and best_score > 0:
            used_images.add(best_img)
            paired.append(f"{{{{IMG:{images[best_img]}|{cap}}}}}")
        else:
            unmatched_caps.append((num, cap))

    # Positional fallback: pair unmatched captions with unmatched images in order
    unmatched_imgs = [i for i in range(len(images)) if i not in used_images]
    for j, (num, cap) in enumerate(unmatched_caps):
        if j < len(unmatched_imgs):
            img_idx = unmatched_imgs[j]
            used_images.add(img_idx)
            paired.append(f"{{{{IMG:{images[img_idx]}|{cap}}}}}")
        else:
            paired.append(cap)

    # Add remaining unmatched images
    for i, img in enumerate(images):
        if i not in used_images:
            paired.append(f"{{{{IMG:{img}}}}}")

    # Assemble: title + paired images
    result_parts = []
    for t in title_lines:
        result_parts.append(t)
    result_parts.extend(paired)

    return "\n\n".join(result_parts)


def _clean_loose_caption(text: str) -> str:
    """Strip wiki/HTML markup from a loose caption block extracted
    from `{{c|…}}` or a wikitable row."""
    # Unwrap pipe-separated templates iteratively (innermost first).
    for _ in range(5):
        new = re.sub(
            r"\{\{\s*(?:sc|smaller|small|c|center|big|bold|italic|nowrap|fs)"
            r"\s*\|(?:[^{}|]*\|)?([^{}]*)\}\}",
            r"\1", text, flags=re.IGNORECASE,
        )
        if new == text:
            break
        text = new
    # Strip <br/>
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    # Strip stray HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Collapse whitespace and trim trailing punctuation
    text = re.sub(r"\s+", " ", text).strip()
    # Drop attribution-prefixed captions: when the text before "Fig. N."
    # ends in a sentence-ending punctuation, treat that as a separate
    # source-attribution line and trim it. Catches "From the Notice
    # issued by the Board. Fig. 13.—..." → "Fig. 13.—...".
    m = re.search(r"((?:Fig|Plate)\.?\s*\d+)", text, re.IGNORECASE)
    if m and m.start() > 0:
        prefix = text[:m.start()].rstrip()
        if prefix.endswith((".", ":")):
            text = text[m.start():]
    return text.strip(" .|")


def _bundle_raw_image_with_caption(text: str) -> str:
    """Bundle a bare image reference and its following caption block
    into a single `[[File:X|caption]]` so the caption renders inside
    the figure rather than as a separate paragraph beneath it.

    Handles three image source forms:
      • `{{raw image|X}}` — EB1911 alternate syntax
      • `[[File:X|size|align]]` — caption-less wikilink with only
        size/position params
      • `[[Image:X|size|align]]` — same, alternate prefix

    Followed by a caption block in either form:
      • `{{c|…}}` (potentially nested) — single-line caption
      • `{| … |}` wikitable — multi-row attribution + caption
    """
    out: list[str] = []
    pos = 0
    img_pat = re.compile(
        # raw image: {{raw image|filename}}
        r"\{\{\s*raw\s+image\s*\|([^{}|]+)\}\}"
        # OR caption-less wikilink: [[File:filename|size|align]]
        r"|\[\[(?:File|Image):([^\]|]+)((?:\|[^\]|]+)*)\]\]",
        re.IGNORECASE,
    )

    _IMG_KEYWORDS = {"center", "left", "right", "thumb", "thumbnail",
                     "frameless", "frame", "border", "upright", "none"}

    def _has_caption(params: str) -> bool:
        """Return True if any | param is a real caption (not size/align)."""
        for p in params.split("|"):
            p = p.strip()
            if not p:
                continue
            lp = p.lower()
            if lp in _IMG_KEYWORDS:
                continue
            if re.match(r"^\d+px$|^x\d+px$|^\d+x\d+px$", lp):
                continue
            if "=" in p:
                continue
            return True
        return False

    for m in img_pat.finditer(text):
        out.append(text[pos:m.start()])

        if m.group(1) is not None:
            # {{raw image|X}} form — never has inline caption
            filename = m.group(1).strip()
            already_captioned = False
        else:
            # [[File:X|...]] form — skip if it already has a real caption
            filename = (m.group(2) or "").strip()
            params = m.group(3) or ""
            already_captioned = _has_caption(params)

        if already_captioned:
            # Don't touch — let normal extraction handle it
            out.append(m.group(0))
            pos = m.end()
            continue

        # Skip whitespace/newlines after the image
        cur = m.end()
        ws = re.match(r"\s*", text[cur:])
        cur += ws.end() if ws else 0
        caption = ""
        consumed_to = m.end()

        # Try {{c|…}} (or {{C|…}}) — count braces to find the close
        if text[cur:cur + 4].lower().startswith("{{c|"):
            end = _find_matching_double_braces(text, cur)
            if end > 0:
                inner = text[cur + 2:end - 2]
                inner = inner.split("|", 1)[1] if "|" in inner else inner
                caption = _clean_loose_caption(inner)
                consumed_to = end
        # Try wikitable {| … |}
        elif text[cur:cur + 2] == "{|":
            end = text.find("|}", cur)
            if end > 0:
                table = text[cur + 2:end]
                rows = re.split(r"\n\s*\|-[^\n]*\n", table)
                last_row = rows[-1].strip() if rows else ""
                if last_row.startswith("|"):
                    last_row = last_row[1:].strip()
                last_row = re.sub(
                    r'^(?:(?:align|style|width|valign|class|colspan|rowspan)'
                    r'\s*=\s*"[^"]*"\s*)+\|\s*', "", last_row,
                )
                caption = _clean_loose_caption(last_row)
                consumed_to = end + 2

        if caption:
            out.append(f"[[File:{filename}|{caption}]]")
        else:
            out.append(m.group(0))  # leave as-is
        pos = consumed_to
    out.append(text[pos:])
    return "".join(out)


def _find_matching_double_braces(text: str, start: int) -> int:
    """Given text[start:start+2] == '{{', return index just past the
    matching '}}'. Returns -1 if not balanced within 5000 chars."""
    if text[start:start + 2] != "{{":
        return -1
    depth = 0
    i = start
    end_search = min(len(text), start + 5000)
    while i < end_search - 1:
        ch2 = text[i:i + 2]
        if ch2 == "{{":
            depth += 1
            i += 2
        elif ch2 == "}}":
            depth -= 1
            i += 2
            if depth == 0:
                return i
        else:
            i += 1
    return -1


_CORRECTIONS = None


def _load_corrections():
    """Load data/corrections.json once (literal source-text fixes)."""
    global _CORRECTIONS
    if _CORRECTIONS is not None:
        return _CORRECTIONS
    from pathlib import Path
    p = Path("data/corrections.json")
    if not p.exists():
        _CORRECTIONS = {}
        return _CORRECTIONS
    import json
    data = json.loads(p.read_text(encoding="utf-8"))
    _CORRECTIONS = {k: v for k, v in data.items() if not k.startswith("_")}
    return _CORRECTIONS


def _transform_text_v2(raw_wikitext: str, volume: int, page_number: int) -> str:
    """New architecture: extract-process-reassemble.

    1. Minimal preprocessing (strip section tags, noinclude, normalize)
    2. process_elements does everything:
       - Extracts embedded elements
       - Transforms body text (bold, italic, links, etc.)
       - Processes each element recursively
       - Reassembles
    3. Done.
    """
    from britannica.pipeline.stages.elements import process_elements

    # Apply per-page source-text corrections (transcription typos in
    # wikisource we don't want to edit upstream). Keys: "{vol}:{page}".
    corrections = _load_corrections().get(f"{volume}:{page_number}", [])
    for c in corrections:
        raw_wikitext = raw_wikitext.replace(c["from"], c["to"])

    # Strip section tags — boundaries already determined
    text = re.sub(r'<section\s+(?:begin|end)="[^"]*"\s*/?>', "",
                  raw_wikitext, flags=re.IGNORECASE)

    # Strip <noinclude> blocks (page headers, quality tags)
    text = re.sub(r"<noinclude>.*?</noinclude>", "", text,
                  flags=re.DOTALL | re.IGNORECASE)

    # Unclosed `{{nowrap|…` (malformed wikitext in sources like EGYPT
    # vol 9 p76) confuses cell parsing because its inner `|` leaks as
    # a cell separator. Scan for each `{{nowrap|` opener; if it has no
    # matching `}}`, strip just the opener. Balanced cases (including
    # nested templates) are left alone for _unwrap_balanced to handle.
    def _strip_unclosed_nowrap(text):
        out = []
        i = 0
        low = text.lower()
        while i < len(text):
            if low[i:i+9] == "{{nowrap|" or (
                    low[i:i+8] == "{{nowrap" and i+8 < len(text)
                    and low[i+8] in " \t" and "|" in text[i+8:i+30]):
                # Find matching }} by depth counting from this opener.
                depth = 1
                j = i + 2
                matched = False
                while j < len(text) - 1:
                    if text[j:j+2] == "{{":
                        depth += 1
                        j += 2
                    elif text[j:j+2] == "}}":
                        depth -= 1
                        j += 2
                        if depth == 0:
                            matched = True
                            break
                    else:
                        j += 1
                if matched:
                    # Balanced — leave untouched.
                    out.append(text[i:j])
                    i = j
                else:
                    # Unclosed — strip opener up through first `|`.
                    pipe_idx = text.find("|", i)
                    if pipe_idx >= 0:
                        i = pipe_idx + 1  # skip `{{nowrap|`
                    else:
                        i += 2  # just drop the `{{`
            else:
                out.append(text[i])
                i += 1
        return "".join(out)
    text = _strip_unclosed_nowrap(text)

    # Replace <score> tags (static lookup, must happen before extraction)
    text = _replace_score_tags(text, volume, page_number)

    # {{raw image|filename}} is an alternate EB1911 image syntax used
    # for figures whose caption sits on a following line as
    # `{{c|{{sc|Fig. 10.}}}}` or in a separate wikitable. Bundle the
    # image and its caption block into one `[[File:filename|caption]]`
    # so downstream extraction renders them as a single figure (avoids
    # the figure showing both a figcaption and a duplicate caption
    # paragraph below — see WEIGHING MACHINES / SEWING MACHINES).
    text = _bundle_raw_image_with_caption(text)

    # Unwrap center `{{c|…}}` templates — they only control alignment.
    # Done before element extraction so an image caption like
    # `{{c|{{sc|Fig. 10.}}}}` simplifies to `{{sc|Fig. 10.}}` and the
    # IMAGE extractor's caption-pairing regex can recognize it.
    for _ in range(3):
        new = re.sub(
            r"\{\{\s*c\s*\|((?:[^{}]|\{\{[^{}]*\}\})*)\}\}",
            r"\1", text, flags=re.IGNORECASE,
        )
        if new == text:
            break
        text = new

    # Strip {{missing table}} markers that precede chart2 blocks (the chart
    # image replaces the table; the marker is redundant)
    text = re.sub(
        r"\{\{missing table\}\}\s*(?:\x01PAGE:\d+\x01)?\s*(?=\{\{center\|.*?GENEALOGICAL|\{\{chart2/start)",
        "", text, flags=re.IGNORECASE | re.DOTALL,
    )

    # Normalize
    text = normalize_unicode(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Strip HTML comments (replace with space to avoid creating false paragraph breaks)
    text = re.sub(r"\n?<!--.*?-->\n?", " ", text, flags=re.DOTALL)

    # Unwrap poem wrappers: {{block center|<poem>...</poem>}} → <poem>...</poem>
    text = re.sub(
        r"\{\{block center\|(<poem>.*?</poem>)\}\}",
        r"\1", text, flags=re.DOTALL | re.IGNORECASE,
    )
    text = re.sub(
        r"\{\{center\|(<poem>.*?</poem>)\}\}",
        r"\1", text, flags=re.DOTALL | re.IGNORECASE,
    )

    # Unwrap fine print markers
    text = re.sub(
        r"\{\{EB1911 fine print/s\}\}(.*?)\{\{EB1911 fine print/e\}\}",
        r"\1", text, flags=re.DOTALL | re.IGNORECASE,
    )

    # Unwrap {{fine block|...}} with balanced brace matching
    def _unwrap_balanced(text, template_name):
        """Unwrap a template by finding the balanced closing }}.

        Skips over <math>...</math> regions so that LaTeX braces
        (e.g. \\Delta_{b}}) don't confuse the brace counter.
        """
        prefix = "{{" + template_name + "|"
        # Pre-compute math regions to skip
        math_spans = [(m.start(), m.end()) for m in
                      re.finditer(r"<math\b[^>]*>.*?</math>", text,
                                  re.DOTALL | re.IGNORECASE)]

        def _in_math(pos):
            for s, e in math_spans:
                if s <= pos < e:
                    return e  # return end position to skip to
            return 0

        while True:
            idx = text.lower().find(prefix.lower())
            if idx < 0:
                break
            # Find balanced close
            depth = 0
            i = idx
            while i < len(text) - 1:
                skip_to = _in_math(i)
                if skip_to:
                    i = skip_to
                    continue
                if text[i:i+2] == "{{":
                    depth += 1
                    i += 2
                elif text[i:i+2] == "}}":
                    depth -= 1
                    if depth == 0:
                        # Replace: strip outer {{ and }}
                        content = text[idx + len(prefix):i]
                        text = text[:idx] + content + text[i+2:]
                        # Recompute math spans since offsets shifted
                        math_spans = [(m.start(), m.end()) for m in
                                      re.finditer(r"<math\b[^>]*>.*?</math>",
                                                  text, re.DOTALL | re.IGNORECASE)]
                        break
                    i += 2
                else:
                    i += 1
            else:
                break  # unbalanced — give up
        return text

    # Normalize {{center|{{sc|...}}}} to {{csc|...}} so it gets paragraph breaks
    text = re.sub(
        r"\{\{center\|\{\{sc\|([^{}]*)\}\}\}\}",
        r"{{csc|\1}}", text, flags=re.IGNORECASE,
    )

    for tmpl in ["block center", "fine block", "center", "c", "larger", "smaller",
                  "EB1911 Fine Print", "nowrap"]:
        text = _unwrap_balanced(text, tmpl)
    # Note: {{ts|...}} templates are stripped inside table processors,
    # not globally — global stripping corrupts cell boundaries in complex tables.
    # Convert spacing templates to a space ({{gap}}, {{em|N}}, {{rule}})
    text = re.sub(r"\{\{gap(?:\|[^{}]*)?\}\}", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{em\s*\|[^{}]*\}\}", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{rule\}\}", "———", text, flags=re.IGNORECASE)

    # No need for orphan table wrapping — articles are joined before
    # transform, so all tables have their {| and |} in the same text.

    # Extract, process, reassemble — this does all the work
    context = {"volume": volume, "page_number": page_number}
    text = process_elements(text, _transform_body_text, context)

    # Inject chart images for pages where chart2 markup was lost during import
    from britannica.pipeline.stages.elements import _CHART2_IMAGES
    for (v, p), filename in _CHART2_IMAGES.items():
        if v == volume and f"IMG:{filename}" not in text:
            marker = f"\x01PAGE:{p}\x01"
            if marker in text:
                text = text.replace(marker, f"{marker}\n\n{{{{IMG:{filename}|Genealogical table}}}}\n\n", 1)

    # Reflow paragraphs — join lines that were hard-wrapped in the source
    text = reflow_paragraphs(text)


    # Strip leading comma/space left after title+descriptor stripping
    # (e.g. "'''BISMARCK,''' {{sc|Prince}}, duke..." → ", duke..." after transform)
    text = re.sub(r"^[\s,]+", "", text)

    # Defensive cleanup for orphan punctuation left when a template
    # gets stripped without its display text (e.g. a malformed
    # `{{1911link|X|Y}}` previously dropped, leaving `…, , Y…`):
    #   ", , , "  → ", "
    #   ", ;"     → ";"
    #   ", ."     → "."
    # Preserve `,,` adjacent (ditto marks in tables).
    text = re.sub(r",(\s+,)+", ",", text)
    text = re.sub(r",\s*([;.])", r"\1", text)

    return text




def _wrap_orphaned_table_rows(text: str) -> str:
    """Wrap orphaned wiki table rows (|- and | lines) that lack a {| opener.

    Multi-page wiki tables have {| in <noinclude> on continuation pages.
    After noinclude stripping, the rows are left bare.  Wrap them in
    {|...|} so the table converter can process them.

    Also detects runs of |lines without |- separators (two-column tables
    spanning page boundaries).
    """
    # Quick check: any lines starting with |?
    has_pipe_rows = any(
        line.strip().startswith("|") and len(line.strip()) > 3
        for line in text.split("\n")
    )
    if not has_pipe_rows:
        return text

    # Count opens and closes
    opens = len(re.findall(r"\{\|", text))
    closes = len(re.findall(r"\|\}", text))

    if "{|" in text:
        if opens > closes:
            # Unclosed table — add |} at end so balanced extractor can find it
            text = text + "\n|}"
        elif opens < closes:
            # Orphaned |} — wrap preceding rows in {|
            first_close = text.find("|}")
            prefix = text[:first_close]
            rest = text[first_close + 2:]
            text = "{|\n" + prefix + "\n|}" + rest
        # Also handle orphaned rows before the first {|
        first_table = text.find("{|")
        prefix = text[:first_table]
        rest = text[first_table:]
        if prefix.strip() and ("\n|-" in prefix or prefix.strip().startswith("|-")):
            wrapped_prefix = _wrap_orphaned_table_rows(prefix)
            return wrapped_prefix + rest
        return text

    # Find runs of |lines and wrap them
    lines = text.split("\n")
    first_row = None
    last_row = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        is_table_line = (
            (stripped.startswith("|-") or stripped.startswith("|"))
            and len(stripped) > 3
            and not stripped.startswith("|}")
        )
        if is_table_line:
            if first_row is None:
                first_row = i
            last_row = i

    if first_row is None:
        return text

    # Wrap the table rows
    before = "\n".join(lines[:first_row])
    table = "\n".join(lines[first_row:last_row + 1])
    after = "\n".join(lines[last_row + 1:])
    parts = []
    if before.strip():
        parts.append(before)
    parts.append("{|\n" + table + "\n|}")
    if after.strip():
        parts.append(after)
    return "\n".join(parts)




def transform_articles(volume: int) -> int:
    """Transform raw wikitext to internal marker format for all articles in a volume.

    Transforms each segment (page-sized) individually, then joins them
    into article.body with \\x01PAGE:N\\x01 markers at page boundaries.
    The markers are injected after transformation so they survive the
    control-character stripping in clean_pages.

    Processes one article at a time with per-article commits.
    """
    session = SessionLocal()
    try:
        article_ids = [
            aid for (aid,) in session.query(Article.id)
            .filter(Article.volume == volume)
            .all()
        ]

        for aid in article_ids:
            article = session.get(Article, aid)
            segments = (
                session.query(ArticleSegment)
                .join(SourcePage, ArticleSegment.source_page_id == SourcePage.id)
                .filter(ArticleSegment.article_id == aid)
                .order_by(ArticleSegment.sequence_in_article)
                .add_columns(SourcePage.page_number)
                .all()
            )

            is_plate = article.article_type == "plate"

            if is_plate:
                # Plates are single pages — process directly
                raw = segments[0][0].segment_text if segments else ""
                article.body = _transform_plate(raw) if raw else ""
            else:
                # Join raw segments with page markers, then transform once.
                raw_parts = []
                for seg, page_number in segments:
                    raw = seg.segment_text or ""
                    # Always emit the page marker, even for empty/untranscribed pages
                    raw_parts.append(f"\x01PAGE:{page_number}\x01{raw}")
                joined_raw = "\n".join(raw_parts)

                # Fix cross-page hyphenation: con-\n\x01PAGE:N\x01tinuation
                joined_raw = re.sub(
                    r"(\w)-\n(\x01PAGE:\d+\x01)(\w)",
                    r"\1\2\3", joined_raw,
                )
                article.body = _transform_text_v2(
                    joined_raw, volume,
                    segments[0][1] if segments else 0,
                ) if joined_raw else ""
                # Strip redundant title qualifier from body start.
                # e.g. title "YORK, HOUSE OF" → body starts "(House of),"
                if article.body and ", " in article.title:
                    qualifier = article.title.split(", ", 1)[1]
                    # Strip formatting markers for matching
                    body_clean = re.sub(
                        r"[\u00ab\u00bb](?:SC|/SC|I|/I|B|/B)[\u00ab\u00bb]",
                        "", article.body[:200],
                    )
                    paren_q = f"({qualifier})"
                    if body_clean.lstrip("\x01PAGE:0123456789").lstrip().lower().startswith(paren_q.lower()):
                        # Strip the parenthetical qualifier from actual body
                        article.body = re.sub(
                            r"^(\x01PAGE:\d+\x01)?\s*\([^)]*\)[,;\s]*",
                            r"\1", article.body,
                        )
            session.commit()
            session.expire_all()

        return len(article_ids)
    finally:
        session.close()
