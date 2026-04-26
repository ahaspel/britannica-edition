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
from britannica.cleaners.unicode import normalize_unicode, replace_print_artifacts
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
    # Numbered equations: {{ne||equation|(N)}} → equation  (N)
    text = re.sub(r"\{\{ne\|\|([^{}|]*(?:\{\{[^{}]*\}\}[^{}|]*)*)\|([^{}]*)\}\}",
                  r"\1\t\2", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{ne\|\|([^{}]*(?:\{\{[^{}]*\}\}[^{}]*)*)\}\}",
                  r"\1", text, flags=re.IGNORECASE)
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
    # Normalize malformed quote runs in math/notation contexts:
    # `'''x''` (3 open, 2 close) and `''x'''` (2 open, 3 close) are
    # typos common in EB1911 math sections (SHIPBUILDING p993's
    # `moderate amount '''w'' tons`) — the author meant italic on a
    # single-letter variable but the run count got unbalanced. Without
    # normalization the extra `'` cascades into the next italic pair,
    # inverting open/close markers through the rest of the article.
    #
    # The pattern: a 3-quote run bordering a short (≤5 char) token and
    # matched on the other side by a 2-quote run — almost certainly
    # italic intent. We normalize both sides to `''`.
    text = re.sub(
        r"(?<!')'{3}([^'\s]{1,5})'{2}(?!')",
        r"''\1''",
        text,
    )
    text = re.sub(
        r"(?<!')'{2}([^'\s]{1,5})'{3}(?!')",
        r"''\1''",
        text,
    )

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
    # Strip MediaWiki indent / definition-list prefix `:` and `;` at
    # the start of a line.  Used throughout EB1911 as visual indent
    # for numbered equations (e.g. BALLISTICS `:(43) <math>…</math>`).
    # We don't render these as indented blocks — stripping the sigil
    # keeps the content flush without a stray colon leaking through.
    # Bullet `*` and ordered `#` lists are left alone.
    text = re.sub(r"^[:;]+\s*", "", text, flags=re.MULTILINE)
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


_LEGEND_CELL_RE = re.compile(
    r"^\s*([A-Za-z0-9](?:[A-Za-z0-9.,\- ]{0,20}?))"
    r"[,.]\s+(.+\S)\s*$")

# Plain-ASCII label shape after italic markers have been stripped.
# Caps label at 4 chars so the regex doesn't greedily eat real words
# (HEXAPODA Fig. 58 `H, Air compressing cylinder` → label `H`, not
# `H, Air`).  Multi-label chains (`K, L. Round-nose tools.`) require
# a period terminator to distinguish them from single-label + comma
# + prose.
#
# Two variants: PERMISSIVE allows a single-label with NO separator
# (used inside VERSE/TABLE/POEM container content where `A text.` is
# legitimate — TOOL Fig. 65).  STRICT requires `,` or `.` after
# single-label (used for body paragraphs where `a drilling…` is an
# English article, not a label — TOOL Fig. 47).
_PARA_LEGEND_LABEL_ONE = r"[A-Za-z0-9][A-Za-z0-9.\-]{0,3}"

def _build_legend_line_re(strict: bool) -> re.Pattern:
    # Single-label separator: `[,.]` required in strict, `[,.]?` in
    # permissive mode.
    single_sep = r"[,.]" if strict else r"[,.]?"
    # Text group uses `[\s\S]+?` so legend entries with internal
    # newlines (source `<br>` → space/newline) still match.
    return re.compile(
        r"^\s*(?:"
        r"(" + _PARA_LEGEND_LABEL_ONE +
        r"(?:\s*,\s*" + _PARA_LEGEND_LABEL_ONE + r")+)\."
        r"|"
        r"(" + _PARA_LEGEND_LABEL_ONE + r")" + single_sep +
        r")\s+([\s\S]+?)\s*$",
        re.DOTALL,
    )


_PARA_LEGEND_PLAIN_RE = _build_legend_line_re(strict=False)
_PARA_LEGEND_STRICT_RE = _build_legend_line_re(strict=True)


def _strip_inline_italic(text: str) -> str:
    """Remove `«I»…«/I»`, `«B»…«/B»`, `«SC»…«/SC»` open/close markers
    so a line can be matched against a plain-ASCII legend-label regex.

    Enumerate the exact formatting markers rather than using a
    permissive ``«/?[A-Z]+»`` pattern: ``«/FN»`` / ``«/SEC»`` / etc.
    would match that pattern too, but their OPENERS use a trailing
    colon (``«FN:``, ``«SEC:``) that the regex misses — stripping
    just the closer turned every footnote into an unclosed marker.
    Observed corpus-wide: 9 articles had unbalanced FN markers
    traceable to this (CONVEYORS, GAS, RING, PROBABILITY, …).
    """
    return re.sub(r"\u00ab/?(?:I|B|SC)\u00bb", "", text)


# EB1911 inline section-heading pattern: ``LABEL. ''italic title.''—prose``
# (HARMONY vol 13: ``III. ''Modern Harmony and Tonality.''—In the harmonic
# system of Palestrina…``).  Label + italic-wrapped title + em-dash is
# the distinguishing shape — legend captions with Roman-numeral labels
# (CENTIPEDE "I. Mandibles", HYDRAULICS "VI. STEADY FLOW…") do NOT
# italicize their text or use em-dashes, so this regex misses them.
_INLINE_SECTION_HEADING_RE = re.compile(
    r"^\s*[A-Za-z0-9IVXLCDM]+\.?\s+"
    r"\u00abI\u00bb[^\u00ab]+\u00ab/I\u00bb"
    r"\s*[.\u2014\u2013\-]"
)


def _match_legend_line(line: str, *, strict: bool = False) -> tuple[str, str] | None:
    """Try to parse `line` as a legend entry.  Returns (label, text)
    or None.  Handles all the variants we've seen:

    * `A, text.`                       (comma separator)
    * `A. text.`                       (period separator)
    * `A text`                         (no separator — TOOL Fig. 65;
                                        only accepted in permissive mode)
    * `«I»A«/I», text.`                (italic label, outside punct)
    * `«I»A,«/I» text.`                (italic label, inside punct;
                                        TOOL Fig. 58 `A,` inside)
    * `A, B, text.`                    (multiple labels)
    * `«I»A«/I», «I»B«/I», text.`      (multiple italic labels)

    `strict=True` rejects single-label entries without a `,` or `.`
    separator, used for body-paragraph context where `a drilling…`
    (English article "a") should NOT be mistaken for a label.
    """
    # EB1911 inline section-heading pattern: ``LABEL. ''italic
    # title.''—prose``.  Check this BEFORE stripping italic markers,
    # since ``_strip_inline_italic`` would erase the signature.
    if _INLINE_SECTION_HEADING_RE.match(line):
        return None
    plain = _strip_inline_italic(line).strip()
    pat = _PARA_LEGEND_STRICT_RE if strict else _PARA_LEGEND_PLAIN_RE
    m = pat.match(plain)
    if not m:
        return None
    label = (m.group(1) or m.group(2) or "").strip().rstrip(".,")
    text = m.group(3).strip().rstrip(".")
    if not label or not text:
        return None
    return label, text


def _promote_paragraph_legends(text: str) -> str:
    """Convert `{{IMG:…}}` followed by legend-shaped prose into
    `{{IMG:…}}\\n\\n{{LEGEND:…}LEGEND}`.

    The legend content can appear in several layouts:
      * Multiple paragraphs, each one entry (TOOL Figs 2-3)
      * A single paragraph with multiple entries glued together
        separated by sentence boundaries (TOOL Figs 9-10)
      * Multiple lines in one paragraph, each one entry (TOOL Fig. 13)

    Everything from the IMG's closing `}}` up to the next blank-line
    paragraph break (or page-break marker) is handed to
    `_parse_legend_lines`, which already knows how to handle all
    three layouts.  Separator between IMG and the first legend line
    may be a single newline OR a blank line.
    """
    img_re = re.compile(r"\{\{IMG:[^}]+\}\}")
    block_end_re = re.compile(r"\n\n+|\x01PAGE:\d+\x01")
    out_parts: list[str] = []
    pos = 0
    for m in img_re.finditer(text):
        out_parts.append(text[pos:m.end()])
        pos = m.end()
        tail = text[pos:]
        # Skip past any whitespace (single `\n`, `\n\n`, spaces).
        ws_m = re.match(r"[ \t]*\n+", tail)
        if not ws_m:
            continue
        after_ws = pos + ws_m.end()
        # Find the end of the legend block: next blank-line break
        # or page marker.  Everything up to there is candidate
        # legend content.
        end_m = block_end_re.search(text, after_ws)
        block_end = end_m.start() if end_m else len(text)
        candidate = text[after_ws:block_end]
        # Don't try to absorb overly long chunks as a single legend —
        # real legends per figure are bounded (≤ 2000 chars is a
        # generous cap).
        if not candidate.strip() or len(candidate) > 2000:
            continue
        # Handle the "multi-entry on one line" shape by pre-splitting
        # the candidate on sentence-boundary-before-label.
        lines_to_parse: list[str] = []
        for line in candidate.split("\n"):
            line = line.strip()
            if not line:
                continue
            chunks = _split_multi_entry_line(line)
            if len(chunks) >= 2:
                lines_to_parse.extend(chunks)
            else:
                lines_to_parse.append(line)
        entries = _parse_legend_lines(lines_to_parse)
        if entries is None:
            continue
        legend = "\n".join(f"{lbl}. {t}." for lbl, t in entries)
        out_parts.append(f"\n\n{{{{LEGEND:{legend}}}LEGEND}}\n\n")
        pos = block_end
    out_parts.append(text[pos:])
    return "".join(out_parts)


def _split_multi_entry_line(line: str) -> list[str]:
    """Split a line like `A, first text. B, second text. C, third.`
    into per-entry chunks using the sentence boundary immediately
    preceding the next label shape.  Labels may be wrapped in
    italic markers (`«I»A«/I», text`) — TOOL Figs 9-10.  Single-entry
    lines return the line unchanged."""
    split_re = re.compile(
        r"(?<=\.)\s+(?=(?:\u00abI\u00bb)?"
        + _PARA_LEGEND_LABEL_ONE +
        r"(?:\u00ab/I\u00bb)?[,.]\s+)")
    parts = split_re.split(line)
    return [p.strip() for p in parts if p.strip()]


def _parse_legend_lines(
    lines: list[str], *, strict: bool = False,
) -> list[tuple[str, str]] | None:
    """Parse a list of lines as legend entries.  A line may contain
    multiple legend entries separated by sentence boundaries (TOOL
    Figs 4-5, HEXAPODA Fig. 3 Saw-Fly); those are split on `. LABEL,`
    boundaries and each chunk parsed independently.  A line that
    doesn't match gets appended as continuation to the PREVIOUS
    entry (multi-line anatomy descriptions in TOOL Figs 35/43/44).
    Returns None if no entry parses at all.

    `strict=True` enforces strict label matching (`,` or `.`
    separator required) — used when parsing body paragraphs where
    `a drilling…` shouldn't be mistaken for a label.
    """
    entries: list[tuple[str, str]] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parsed = _match_legend_line(line, strict=strict)
        if parsed:
            entries.append(parsed)
            continue
        chunks = _split_multi_entry_line(line)
        if len(chunks) >= 2:
            chunk_parsed = [_match_legend_line(c, strict=strict)
                            for c in chunks]
            if all(chunk_parsed):
                entries.extend(cp for cp in chunk_parsed if cp)
                continue
        if entries:
            label, text = entries[-1]
            entries[-1] = (label, f"{text} {line.rstrip('.')}".strip())
            continue
        return None
    return entries if len(entries) >= 2 else None


def _promote_legend_verses(text: str) -> str:
    """Convert `{{IMG:…}} {{VERSE:…}VERSE}` sequences into
    `{{IMG:…}} {{LEGEND:…}LEGEND}` when the VERSE content parses as
    legend entries.  Biological-taxonomy articles (HYDROMEDUSAE,
    HEXAPODA) and engineering articles (TOOL) both use `<poem>`
    blocks for figure legends, which earlier stages convert to
    VERSE; this retroactively relabels them so the viewer renders
    them in figure-legend style."""
    def _try_convert(m: re.Match) -> str:
        img_block = m.group(1)
        verse_content = m.group(2)
        entries = _parse_legend_lines(verse_content.split("\n"))
        if not entries:
            return m.group(0)
        legend = "\n".join(f"{lbl}. {t}." for lbl, t in entries)
        return f"{img_block}\n\n{{{{LEGEND:{legend}}}LEGEND}}"

    return re.sub(
        r"(\{\{IMG:[^}]+\}\})\s*\{\{VERSE:([\s\S]*?)\}VERSE\}",
        _try_convert_verse_simple, text)


def _try_convert_verse_simple(m: re.Match) -> str:
    img_block = m.group(1)
    verse_content = m.group(2)
    entries = _parse_legend_lines(verse_content.split("\n"))
    if not entries:
        return m.group(0)
    legend = "\n".join(f"{lbl}. {t}." for lbl, t in entries)
    return f"{img_block}\n\n{{{{LEGEND:{legend}}}LEGEND}}"


def _fold_image_attribution(text: str) -> str:
    """Fold an attribution line immediately following an `{{IMG:…}}`
    marker into the IMG's caption in parens.  An attribution is a
    short line that starts with `(`, `From `, `After `, `Modified `,
    `Photo`, or `Copyright` — so regular body prose doesn't get
    eaten.  Covers the TOOL Fig. 58 `{{IMG:…}}\\n(W. & J. Player,
    Birmingham.)\\n\\n{{VERSE:…` layout."""
    attr_re = re.compile(
        r"(\{\{IMG:[^}]+\}\})\n"
        r"(\([^\n{}]{3,200}\)"
        r"|(?:From|After|Modified|Photo|Copyright)[^\n{}]{1,200})"
        r"[ \t]*"           # tolerate trailing whitespace on attr line
        r"(?=\n)",
        re.IGNORECASE,
    )
    def _apply(m: re.Match) -> str:
        img_block = m.group(1)
        attribution = m.group(2).strip()
        return _append_attr_to_img(img_block, attribution)
    return attr_re.sub(_apply, text)


# ── Figure walker (unified IMG+attribution+legend handler) ────────────
#
# For each `{{IMG:…}}` marker, walk forward paragraph-by-paragraph
# collecting "figure material" (attribution, legend-shaped content in
# any wrapper) until we hit a figure boundary, then emit a cleanly
# formatted IMG + optional LEGEND.  This replaces the earlier zoo of
# container-specific promoters (`_promote_legend_tables/verses/
# paragraphs`) with one pipeline: (1) classify pattern, (2) locate
# boundary, (3) format content.

_ATTRIBUTION_START_RE = re.compile(
    # Parenthetical attribution OR attribution-word immediately
    # followed by a capital-letter proper noun (or an initial).
    # Real source credits always have a name (After Haeckel, From
    # A. M. Paterson, Modified after Linko).  "After body." or
    # "After the war" would fail this check and stay as body prose.
    r"^(?:\("
    r"|(?:From|After|Modified|Photo|Copyright)"
    r"(?:\s+after)?\s+[A-Z])",
)
_FIGURE_BOUNDARY_MARKERS = (
    "{{IMG:", "\u00abSEC:", "\u00abSH", "\u00abHTMLTABLE:",
    "\x01PAGE:",
)


_BLOCK_MARKER_RE = re.compile(
    # A block-level marker that begins a fresh paragraph even when
    # preceded by just a single newline.  VERSE / TABLE / HTMLTABLE
    # are complete self-terminating units; \x01PAGE:N\x01 is a
    # page-break sentinel.  `«SEC:` / `«SH»` are heading markers.
    r"\{\{(?:VERSE|TABLE[A-Z]?|IMG|LEGEND):"
    r"|\u00abHTMLTABLE:"
    r"|\u00abSEC:"
    r"|\u00abSH\u00bb"
    r"|\x01PAGE:\d+\x01"
)

_BLOCK_END_RE = re.compile(
    r"\}VERSE\}"
    r"|\}TABLE\}"
    r"|\}LEGEND\}"
    r"|\u00ab/HTMLTABLE\u00bb"
)


def _paragraphs_starting_at(text: str, start: int):
    """Yield `(para_start, para_end, para_text)` for each paragraph
    from `start` onward.  Paragraphs are separated by blank lines OR
    by block-level markers (VERSE, TABLE, IMG, LEGEND, HTMLTABLE,
    PAGE sentinel, section headings), so a `{{VERSE:…}VERSE}\\n<body
    prose>` sequence yields the VERSE and the body prose as two
    paragraphs instead of one glued chunk.  `para_text` is the
    paragraph content with leading/trailing whitespace stripped."""
    pos = start
    ws = re.match(r"\s+", text[pos:])
    if ws:
        pos += ws.end()
    while pos < len(text):
        # Does the current position start with a self-terminating
        # block marker? If so, the paragraph is just that block.
        if text[pos:].startswith(("{{VERSE:", "{{TABLE:", "{{TABLEH:",
                                   "{{LEGEND:")):
            # Find the matching close.
            end_m = _BLOCK_END_RE.search(text, pos)
            if end_m:
                end = end_m.end()
            else:
                end = len(text)
        elif text[pos:].startswith("\u00abHTMLTABLE:"):
            end_i = text.find("\u00ab/HTMLTABLE\u00bb", pos)
            end = end_i + len("\u00ab/HTMLTABLE\u00bb") if end_i > 0 else len(text)
        elif text[pos:].startswith("{{IMG:"):
            close = text.find("}}", pos)
            end = close + 2 if close > 0 else len(text)
        elif text[pos:].startswith("\x01PAGE:"):
            close = text.find("\x01", pos + 1)
            end = close + 1 if close > 0 else len(text)
        elif text[pos:].startswith("\u00abSEC:"):
            close = text.find("\u00bb", pos)
            end = close + 1 if close > 0 else len(text)
        else:
            # Plain-text paragraph — up to next blank line OR the
            # next block-marker opening.
            blank = text.find("\n\n", pos)
            if blank < 0:
                blank = len(text)
            block = _BLOCK_MARKER_RE.search(text, pos)
            block_pos = block.start() if block and block.start() > pos else blank
            end = min(blank, block_pos)
        para = text[pos:end].strip()
        if para:
            yield pos, end, para
        pos = end
        ws = re.match(r"\s+", text[pos:])
        if ws:
            pos += ws.end()


def _is_attribution_paragraph(para: str) -> bool:
    """An attribution is a short paragraph that opens with a known
    attribution marker — `(…)`, `From …`, `After …`, `Modified …`,
    `Photo…`, `Copyright…`."""
    if len(para) > 200:
        return False
    return bool(_ATTRIBUTION_START_RE.match(para))


def _legend_entries_from_paragraph(
    para: str,
) -> list[tuple[str, str]] | None:
    """Parse a body paragraph as a legend — either a single-entry
    paragraph, a multi-line paragraph with one entry per line, or a
    single line packing multiple entries separated by sentence
    boundaries.  Uses STRICT label-matching so body prose that
    starts with an English article (`a drilling machine…`) doesn't
    get mistaken for a label + text.  Returns None if the paragraph
    doesn't parse as a legend."""
    # First try: a single entry (strict mode).
    if len(para) <= 400:
        single = _match_legend_line(para, strict=True)
        if single:
            return [single]
    # Multi-line: split into lines, optionally re-split each for
    # packed multi-entry lines.  Still strict.
    lines_to_parse: list[str] = []
    for line in para.split("\n"):
        line = line.strip()
        if not line:
            continue
        chunks = _split_multi_entry_line(line)
        if len(chunks) >= 2:
            lines_to_parse.extend(chunks)
        else:
            lines_to_parse.append(line)
    return _parse_legend_lines(lines_to_parse, strict=True)


# Bare label cell (label without text in same cell): `a,` / `At,` /
# `br.s,` / `br f,` / `g.s.`.  Up to ~12 chars; may contain dots,
# hyphens, and a single internal space (TUNICATA Fig. 25 uses `br f,`
# `i l,` for biological abbreviations).  Uses \w (Unicode-aware) so
# Latin ligatures (œ, æ) and accented letters survive.  Requires a
# trailing `,` or `.` so the label is unambiguously a legend label
# and not just a short word in a data table cell.
_LEGEND_LABEL_ALONE_RE = re.compile(
    r"^\s*(\w[\w.\- ]{0,12}?)\s*[,.]\s*$")


def _parse_table_as_legend(
    table_content: str,
) -> list[tuple[str, str]] | None:
    """Try to parse a `{{TABLE:…}TABLE}` body as a 2+-column legend
    grid.  Returns entries or None.

    Two layouts are recognised:
      1. `label, text | label, text` — each cell holds one entry.
      2. `label, | text | spacer? | label, | text` — labels and
         text live in alternating cells, separated by empty or
         whitespace-only spacer cells (TUNICATA Fig. 24)."""
    rows = [r for r in table_content.strip().split("\n") if r.strip()]
    if not rows:
        return None

    def _strip_italic(s: str) -> str:
        return re.sub(r"\u00ab/?[A-Z]+\u00bb", "", s).strip()

    # Layout 1: each cell is `label, text`.
    entries: list[tuple[str, str]] = []
    layout1_ok = True
    for row in rows:
        cells = [c.strip() for c in row.split(" | ")]
        if len(cells) < 2:
            layout1_ok = False
            break
        for cell in cells:
            clean = _strip_italic(cell)
            cm = _LEGEND_CELL_RE.match(clean)
            if not cm:
                layout1_ok = False
                break
            label = cm.group(1).strip().rstrip(".,")
            txt = cm.group(2).strip().rstrip(".")
            if label and txt:
                entries.append((label, txt))
        if not layout1_ok:
            break
    if layout1_ok and len(entries) >= 2:
        return entries

    # Layout 2: alternating label-cell + text-cell, possibly
    # separated by empty/whitespace-only spacer cells (em-/en-spaces).
    entries = []
    for row in rows:
        cells = [c.strip() for c in row.split(" | ")]
        meaningful = []
        for c in cells:
            stripped = _strip_italic(c)
            # Treat em-space (\u2003), en-space (\u2002), nbsp
            # (\u00a0) and regular whitespace as spacer-only.
            collapsed = re.sub(
                r"[\s\u2002\u2003\u00a0]+", "", stripped)
            if collapsed:
                meaningful.append(c)
        if len(meaningful) < 2 or len(meaningful) % 2 != 0:
            return None
        for i in range(0, len(meaningful), 2):
            label_clean = _strip_italic(meaningful[i])
            text_clean = _strip_italic(meaningful[i + 1])
            lm = _LEGEND_LABEL_ALONE_RE.match(label_clean)
            if not lm:
                return None
            label = lm.group(1).strip().rstrip(".,")
            txt = text_clean.strip().rstrip(".")
            if not label or not txt:
                return None
            entries.append((label, txt))
    return entries if len(entries) >= 2 else None


def _parse_verse_as_legend(
    verse_content: str,
) -> list[tuple[str, str]] | None:
    """Try to parse a `{{VERSE:…}VERSE}` body as legend lines."""
    return _parse_legend_lines(verse_content.split("\n"))


def _classify_figure_paragraph(
    para: str,
) -> tuple[str, object]:
    """Classify one paragraph of post-IMG content.  Returns a tuple:

        ("boundary",   None)             — stop here, don't consume
        ("attribution", attribution_text) — append to caption
        ("legend",     [(label, text)…])  — emit as LEGEND entries
        ("skip",       None)             — empty / continuation

    Also returns `"boundary"` for block markers that don't belong to
    the figure (next IMG, section heading, HTMLTABLE, …).
    """
    if not para:
        return "skip", None

    # Boundary markers
    for marker in _FIGURE_BOUNDARY_MARKERS:
        if para.startswith(marker):
            return "boundary", None

    # VERSE block: legend-shaped?
    verse_m = re.match(r"\{\{VERSE:([\s\S]*)\}VERSE\}\s*$", para)
    if verse_m:
        entries = _parse_verse_as_legend(verse_m.group(1))
        if entries:
            return "legend", entries
        return "boundary", None  # unrelated verse → stop

    # TABLE block: legend-shaped?
    table_m = re.match(r"\{\{TABLE[A-Z]?:([\s\S]*)\}TABLE\}\s*$", para)
    if table_m:
        entries = _parse_table_as_legend(table_m.group(1))
        if entries:
            return "legend", entries
        return "boundary", None

    # Attribution line
    if _is_attribution_paragraph(para):
        return "attribution", para.strip(" .")

    # Legend-shape paragraph
    entries = _legend_entries_from_paragraph(para)
    if entries:
        # Reject caption-repeat paragraphs. A lone ``Fig. 21.`` after
        # an IMG parses as legend entry ("Fig", "21") — but real legend
        # labels are short symbols (A, B, i, ii, α), never the word
        # "Fig". This pattern appears in source wikitext that writes
        # the caption both in the File link and as a separate
        # ``{{csc|Fig. N.}}`` line (SHIPBUILDING Figs 21–22).
        if len(entries) == 1:
            lbl, txt = entries[0]
            if lbl.lower() == "fig" and re.fullmatch(r"\d+", txt.strip()):
                return "skip", None
        return "legend", entries

    # Anything else is body prose — figure boundary.
    return "boundary", None


def _process_figures(text: str) -> str:
    """Walk each `{{IMG:…}}` marker and absorb the figure material
    that follows it (attribution, legend) up to the figure boundary.
    Emits a clean `{{IMG:…|caption}}` optionally followed by a single
    `{{LEGEND:…}LEGEND}`."""
    img_re = re.compile(r"\{\{IMG:[^}]+\}\}")
    # Skip IMG markers that live inside a table-like container — those
    # are inline icons (e.g. ABBREVIATION's per-symbol/pound glyphs in a
    # data-table cell), not standalone figures. Walking paragraphs after
    # them would scoop up subsequent table rows and emit a runaway
    # LEGEND that engulfs the rest of the table.
    skip_spans: list[tuple[int, int]] = []
    for sm in re.finditer(
        r"«HTMLTABLE:.*?«/HTMLTABLE»", text, re.DOTALL,
    ):
        skip_spans.append((sm.start(), sm.end()))
    for sm in re.finditer(
        r"\{\{TABLE[A-Z]?:.*?\}TABLE\}", text, re.DOTALL,
    ):
        skip_spans.append((sm.start(), sm.end()))

    def _in_skip(p: int) -> bool:
        return any(s <= p < e for s, e in skip_spans)

    out_parts: list[str] = []
    pos = 0
    for m in img_re.finditer(text):
        if m.start() < pos:
            # Overlap: we already consumed this IMG as part of a
            # prior figure (shouldn't happen since IMG markers are
            # atomic, but guard anyway).
            continue
        if _in_skip(m.start()):
            # Inline IMG inside a table/htmltable cell — leave as-is.
            out_parts.append(text[pos:m.end()])
            pos = m.end()
            continue
        out_parts.append(text[pos:m.start()])
        img_marker = m.group()
        scan = m.end()
        attributions: list[str] = []
        entries: list[tuple[str, str]] = []
        boundary = scan
        for p_start, p_end, para in _paragraphs_starting_at(text, scan):
            cls, payload = _classify_figure_paragraph(para)
            if cls == "boundary":
                boundary = p_start
                break
            if cls == "attribution":
                attributions.append(payload)  # type: ignore[arg-type]
            elif cls == "legend":
                entries.extend(payload)  # type: ignore[arg-type]
            boundary = p_end
        # Build the updated IMG marker with any attribution folded in
        updated_img = img_marker
        for attr in attributions:
            updated_img = _append_attr_to_img(updated_img, attr)
        out_parts.append(updated_img)
        if entries:
            legend = "\n".join(f"{lbl}. {t}." for lbl, t in entries)
            out_parts.append(f"\n\n{{{{LEGEND:{legend}}}LEGEND}}")
        # Preserve the blank-line separator after our figure so the
        # paragraph break between figure and body text survives.
        out_parts.append("\n\n")
        pos = boundary
    out_parts.append(text[pos:])
    return "".join(out_parts)


def _try_convert_with_attr(m: re.Match) -> str:
    """Convert IMG + optional attribution line + VERSE into IMG +
    LEGEND, folding the attribution into the IMG caption.  Shared
    helper so the same logic applies to TABLE and paragraph
    promoters."""
    img_block = m.group(1)
    attribution = (m.group(2) or "").strip(" .")
    verse_content = m.group(3)
    entries = _parse_legend_lines(verse_content.split("\n"))
    if not entries:
        return m.group(0)
    # Append attribution to caption if present.
    if attribution:
        img_block = _append_attr_to_img(img_block, attribution)
    legend = "\n".join(f"{lbl}. {t}." for lbl, t in entries)
    return f"{img_block}\n\n{{{{LEGEND:{legend}}}LEGEND}}"


def _append_attr_to_img(img_block: str, attribution: str) -> str:
    """Append attribution text to an IMG marker's caption in parens."""
    m = re.match(r"\{\{IMG:([^|}]+)(?:\|([^}]*))?\}\}", img_block)
    if not m:
        return img_block
    filename = m.group(1)
    caption = m.group(2) or ""
    if attribution in caption:
        return img_block
    if attribution.startswith("(") and attribution.endswith(")"):
        new_caption = (f"{caption.rstrip()} {attribution}"
                       if caption else attribution)
    else:
        new_caption = (f"{caption.rstrip()} ({attribution}.)"
                       if caption else f"({attribution}.)")
    return f"{{{{IMG:{filename}|{new_caption}}}}}"


def _promote_legend_tables(text: str) -> str:
    """Convert `{{IMG:…}} {{TABLE:…}TABLE}` sequences into
    `{{IMG:…}} {{LEGEND:…}LEGEND}` when the table is a 2+-column
    grid of `label, text` pairs (WEAVING Fig. 26)."""
    def _try_convert(m: re.Match) -> str:
        img_block = m.group(1)
        table_content = m.group(2)
        rows_text = [r for r in table_content.strip().split("\n")
                     if r.strip()]
        if not rows_text:
            return m.group(0)
        entries: list[tuple[str, str]] = []
        for row in rows_text:
            cells = [c.strip() for c in row.split(" | ")]
            if len(cells) < 2:
                return m.group(0)
            for cell in cells:
                # Strip italic markers before parsing so `«I»a«/I», x`
                # matches the label regex.
                clean = re.sub(
                    r"\u00ab/?[A-Z]+\u00bb", "", cell).strip()
                cm = _LEGEND_CELL_RE.match(clean)
                if not cm:
                    return m.group(0)
                label = cm.group(1).strip().rstrip(".,")
                txt = cm.group(2).strip().rstrip(".")
                if label and txt:
                    entries.append((label, txt))
        if len(entries) < 2:
            return m.group(0)
        legend = "\n".join(f"{lbl}. {t}." for lbl, t in entries)
        return f"{img_block}\n\n{{{{LEGEND:{legend}}}LEGEND}}"

    return re.sub(
        r"(\{\{IMG:[^}]+\}\})\s*\{\{TABLE:([\s\S]*?)\}TABLE\}",
        _try_convert, text)


_DJVU_PAGE_REF_RE = re.compile(
    # "EB1911 - Volume 24.djvu/1037"  (canonical wikisource page ref)
    # "EB1911 - Volume 20.djvu-694.png"  (typo variant)
    r"EB1911\s+-\s+Volume\s+(\d+)\.djvu[/\-](\d+)(?:\.png)?",
    re.IGNORECASE,
)


def _normalize_djvu_page_refs(text: str) -> str:
    """Rewrite wikisource-style DjVu page references to a canonical
    local filename `djvu_volNN_pagePPPP.jpg`.

    These references appear as `{{raw image|EB1911 - Volume 24.djvu/
    1037}}` (full-page plate, SHIPBUILDING) or `[[File:EB1911 -
    Volume 20.djvu-694.png]]` (typo variant — the `/` was replaced
    with `-` and `.png` appended so it parsed as a File link).
    Neither form is a valid Commons filename; the real content lives
    as a specific page of the volume's `.djvu` file.  The renamed
    filename matches the convention used by `download_djvu_crops.py`
    so a full-page render can be downloaded and served locally."""
    def _rewrite(m: re.Match) -> str:
        vol = int(m.group(1))
        page = int(m.group(2))
        return f"djvu_vol{vol:02d}_page{page:04d}.jpg"
    return _DJVU_PAGE_REF_RE.sub(_rewrite, text)


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
    from britannica.pipeline.stages.fold_unfold import unfold_folded_rows

    # Source-text corrections (transcription typos in wikisource) are
    # applied once during clean_pages, mutating `wikitext` so all
    # downstream stages — including this one — operate on already-
    # corrected text. No repeat application needed here.

    # Rewrite folded wikitable rows — single physical rows holding N
    # logical rows via <br>-stacking — as N real rows, so downstream
    # table processing sees a well-formed N-row table instead of one
    # giant row with concatenated values.
    raw_wikitext = unfold_folded_rows(raw_wikitext)

    # Convert STANDALONE {{Css image crop|Image=EB1911 - Volume N.djvu|
    # Page=P|…}} templates (not inside a wikitable) to File links.
    # Css image crops INSIDE wikitables are part of image-layout
    # tables and must be left for the table extractor to classify as
    # DJVU_CROP — converting them here would break ORCHIDS et al.
    #
    # Detection: scan {|…|} table bodies, mark their byte ranges, and
    # only apply the replacement to matches whose start is OUTSIDE any
    # such range. Nested-template-aware table boundary tracking (walk
    # {|/|} depth, skipping {{…}} content) mirrors the extractor in
    # elements.py so ``{{Ts|vmi|}}``-style pipes don't mistrigger.
    def _table_ranges(text: str) -> list[tuple[int, int]]:
        ranges: list[tuple[int, int]] = []
        i = 0
        n = len(text)
        while i < n - 1:
            if text[i:i+2] == "{|":
                start = i
                depth = 1
                j = i + 2
                while j < n - 1 and depth > 0:
                    if text[j:j+2] == "{{":
                        # skip balanced {{…}} block
                        td = 1; j += 2
                        while j < n - 1 and td > 0:
                            if text[j:j+2] == "{{": td += 1; j += 2
                            elif text[j:j+2] == "}}": td -= 1; j += 2
                            else: j += 1
                    elif text[j:j+2] == "{|": depth += 1; j += 2
                    elif text[j:j+2] == "|}": depth -= 1; j += 2
                    else: j += 1
                ranges.append((start, j))
                i = j
            else:
                i += 1
        return ranges

    _table_spans = _table_ranges(raw_wikitext)
    _crop_pat = re.compile(
        r"(\{\{\s*Css\s+image\s+crop\s*\|[^}]*\}\})"
        r"(?:\s*(?:\{\{\s*center\s*\|([^{}]*(?:\{\{[^{}]*\}\}[^{}]*)*)\}\}"
        r"|\{\{\s*csc\s*\|([^{}]*)\}\}))?",
        re.IGNORECASE,
    )

    # Pre-compute crop indices.  ``download_djvu_crops.py`` numbers
    # every ``{{Css image crop|Image=…djvu|Page=P|…}}`` on a page as
    # ``_crop0``, ``_crop1``, …  in wikitext order across BOTH
    # standalone and in-table occurrences.  We must mirror that
    # indexing so the ``{{IMG:djvu_volNN_pagePPPP_cropI.jpg}}`` marker
    # references the file that actually got produced.  (Previously
    # ``_css_crop_replace`` dropped standalone crops into the no-crop
    # ``djvu_volNN_pagePPPP.jpg`` full-page slot, so SHIPBUILDING
    # Figs 3, 6, 9, 10 et al pointed at the whole page instead of the
    # cropped figure.)
    _CSS_CROP_ALL_RE = re.compile(
        r"\{\{\s*Css\s+image\s+crop\s*\n?(.*?)\}\}",
        re.DOTALL | re.IGNORECASE,
    )
    _crop_index_at: dict[int, int] = {}   # match-start offset → crop index
    _page_counts: dict[tuple[int, int], int] = {}
    for _m in _CSS_CROP_ALL_RE.finditer(raw_wikitext):
        _body = _m.group(1)
        _img_m = re.search(
            r"Image\s*=\s*(EB1911\s+-\s+Volume\s+(\d+)\.djvu)",
            _body, re.IGNORECASE)
        _page_m = re.search(r"Page\s*=\s*(\d+)", _body, re.IGNORECASE)
        if not (_img_m and _page_m):
            continue
        _key = (int(_img_m.group(2)), int(_page_m.group(1)))
        _crop_index_at[_m.start()] = _page_counts.get(_key, 0)
        _page_counts[_key] = _page_counts.get(_key, 0) + 1

    def _css_crop_replace(m: re.Match) -> str:
        body = m.group(1)
        caption = ((m.group(2) if len(m.groups()) >= 2 else None) or
                   (m.group(3) if len(m.groups()) >= 3 else None) or "").strip()
        if caption:
            for _ in range(3):
                new = re.sub(r"\{\{[A-Za-z][A-Za-z0-9_]*\s*\|([^{}|]*)\}\}",
                             r"\1", caption)
                if new == caption:
                    break
                caption = new
            caption = caption.strip()
        img_m = re.search(
            r"Image\s*=\s*(EB1911\s+-\s+Volume\s+(\d+)\.djvu)",
            body, re.IGNORECASE)
        page_m = re.search(r"Page\s*=\s*(\d+)", body, re.IGNORECASE)
        if img_m and page_m:
            vol = int(img_m.group(2))
            page = int(page_m.group(1))
            idx = _crop_index_at.get(m.start(), 0)
            filename = f"djvu_vol{vol:02d}_page{page:04d}_crop{idx}.jpg"
            if caption:
                return f"[[File:{filename}|{caption}]]"
            return f"[[File:{filename}]]"
        return m.group(0)

    def _maybe_replace(m: re.Match) -> str:
        for s, e in _table_spans:
            if s <= m.start() < e:
                return m.group(0)  # inside a table — leave alone
        return _css_crop_replace(m)
    raw_wikitext = _crop_pat.sub(_maybe_replace, raw_wikitext)

    # Strip section tags — boundaries already determined
    text = re.sub(r'<section\s+(?:begin|end)="[^"]*"\s*/?>', "",
                  raw_wikitext, flags=re.IGNORECASE)

    # Strip <noinclude> blocks (page headers, quality tags), but preserve
    # any `{|` opener or `|}` closer lines inside them — EB1911 pages
    # often put the table wrapper `{|...` in the header noinclude and
    # `|}` in the footer noinclude so the page displays standalone.
    # Stripping the whole block leaves the rows orphaned and the
    # balanced-table extractor later pairs a `{|` on one page with a
    # `|}` many pages later, swallowing all intermediate prose (this
    # was silently eating Climate / Fauna / Population sections of
    # UNITED STATES, THE). detect_boundaries applies the same logic at
    # its own preprocess step; this is defence in depth.
    def _strip_noinclude(m: re.Match) -> str:
        block = m.group(0)
        kept: list[str] = []
        for om in re.finditer(r"(?:^|\n)\s*\{\|[^\n<]*", block):
            kept.append(om.group(0).strip())
        if re.search(r"(?:^|\n)\s*\|\}(?!\})", block):
            kept.append("|}")
        return ("\n" + "\n".join(kept) + "\n") if kept else ""
    text = re.sub(r"<noinclude>.*?</noinclude>", _strip_noinclude, text,
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

    # Normalize `EB1911 - Volume N.djvu/PPP` (and the typo variant
    # `…djvu-PPP.png`) to local filenames `djvu_volNN_pagePPPP.jpg`
    # BEFORE image extraction.  `download_djvu_crops.py` provisions
    # these files from the volume's DjVu renders — otherwise the
    # viewer would try (and fail) to resolve them on Commons.
    text = _normalize_djvu_page_refs(text)

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
    text = replace_print_artifacts(text)
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

    # Unwrap `{{center|[[File:…]]<br>caption}}` so the image and its
    # caption become a normal image+caption sequence the IMAGE
    # extractor already knows how to parse (WEAVING Fig. 1 & 2).
    # Caption may contain one level of nested `{{…}}` templates.
    text = re.sub(
        r"\{\{center\|(\[\[(?:File|Image):[^\]]+\]\])\s*<br\s*/?>\s*"
        r"((?:[^{}]|\{\{[^{}]*\}\})*)\}\}",
        r"\1\n\2",
        text, flags=re.IGNORECASE,
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
                        # Strip a leading MediaWiki positional-parameter
                        # name (e.g. "1="). Wikitext allows the explicit
                        # form {{center|1=payload}}; without this, the
                        # "1=" leaks into the rendered text.
                        content = re.sub(r"^\d+=", "", content)
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

    # Normalize {{center|{{sc|...}}}} (and {{center|1={{sc|...}}}}) to
    # {{csc|...}} so it gets paragraph breaks. The explicit 1= form
    # is MediaWiki's positional-parameter syntax and appears in some
    # hand-edited articles (e.g. JEWS, MALAYS, AMERICAN WAR OF
    # INDEPENDENCE).
    text = re.sub(
        r"\{\{center\|(?:1=)?\{\{sc\|([^{}]*)\}\}\}\}",
        r"{{csc|\1}}", text, flags=re.IGNORECASE,
    )

    # Note: ``hi`` intentionally NOT in this list. ``{{hi|Nem|content}}``
    # has a two-arg form with a size prefix that the generic balanced
    # unwrap would leak into visible text (``3em|content``). The
    # dedicated handlers in ``_unwrap_content_templates`` (called per
    # text-transform pass) handle both ``{{hi|content}}`` and
    # ``{{hi|Nem|content}}`` correctly.
    for tmpl in ["block center", "fine block", "center", "c", "larger", "smaller",
                  "EB1911 Fine Print", "nowrap", "Fine", "sm"]:
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

    # Single-pass figure walker: for each `{{IMG:…}}`, collect
    # attribution lines + legend-shaped content (in any wrapper —
    # VERSE, TABLE, paragraphs) up to the figure boundary, then emit
    # one clean `{{IMG:…|caption}}` + optional `{{LEGEND:…}LEGEND}`.
    # Replaces the previous zoo of container-specific promoters.
    text = _process_figures(text)

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
