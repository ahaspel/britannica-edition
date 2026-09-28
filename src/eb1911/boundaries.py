"""EB1911's articles begin at a TITLE BLOCK — its own typographic rule.

An article starts at a heading the classifier calls a title, sitting at a
block start (section open, blank line, table close or page break), past any
lead illustration.  Three shapes:
  * `«B»TITLE«/B»` opening a section (most articles, incl. figure-led)
  * `«B»TITLE«/B»` after a blank line / table close inside a section that holds
    several articles (sections are NOT 1:1 with articles)
  * `{{dropinitial|L}}` + prose, no bold heading (the single-letter articles)
Continuations (section re-emits with no opening heading) and subsection
headings (title-ish but not at a block start, or rejected by the classifier)
are not cuts.

The Britannica's rule, not the engine's: moved out of pipeline/stages/
super_walker.py (wikikit step 5).  The engine asks every book where its
articles start (``Corpus.article_starts``); the DNB answers from its explicit
`<section>` runs instead.
"""
from __future__ import annotations

import re

from wikikit.pipeline.stages.elements._title import _letter_from_dropcap
from wikikit.util.strings import HTML_TAG_RE, until_stable
from wikikit.wikitext import COMMENT_RE, TEMPLATE_OPEN, template_end

# An article heading: «B»…«/B», optionally wrapped in an [[Author:…|…]] link.
# Inner italic spans are tolerated; the closer is «/B».  `\s*` after the link
# pipe: the «B» can sit on the NEXT line (`[[Author:…|\n«B»STAWELL…«/B»]]`).
_HEADING = re.compile(r"(?:\[\[[^\]|]*\|\s*)?«B»((?:[^«]|«/?I»)*?)«/B»")
# Block starts inside a section, after the open: a blank line, or a closed
# wikitable / HTML table (the previous article's trailing figure).
#
# A PAGE BREAK is also a block start — an article heading often sits at the top
# of a page with no blank line before it, and the seam is a single `\n`, so
# without it those articles are never detected at all.  It used to be the third
# alternative here (`\x01PAGE:\d+\x01`); the token is gone from the stream, so
# `article_starts` folds the page-key offsets into `starts` instead.  Same
# boundaries, taken from data rather than from a marker sitting in the text.
_BLOCK_BOUNDARY = re.compile(r"\n\n|(?:\|\}|</table>)[ \t]*\n")
# Leading whitespace / table-remnant pipes / nbsp to skip.
_WS = re.compile(r"(?:\s|&nbsp;|\xa0|\|)+")
# Lead layout that may sit before a heading — the article's own opening
# illustration / fine-print frame / drop-cap / column comment, or page-level
# transclusion chrome (`<noinclude>` header/footer, `<section …>` tags) — all
# skipped to REACH the heading on RAW source.  Recognized-and-skipped, never
# stripped: what comes in goes out (their producers consume them downstream).
_LEAD = [
    re.compile(r"<noinclude>.*?</noinclude>", re.DOTALL | re.I),  # page chrome
    re.compile(r"<section\s+(?:begin|end)\b[^>]*?/?>", re.I),     # transclusion tag
    COMMENT_RE,                                                 # HTML comment
    re.compile(r"<br\s*/?>", re.I),                            # line break
    re.compile(r"\{\|.*?\n\s*\|\}", re.DOTALL),                 # wikitable
    re.compile(r"\{\|.*?\|\}", re.DOTALL),                      # wikitable (inline close)
    re.compile(r"<table[^>]*>.*?</table>", re.DOTALL | re.I),   # HTML table
    re.compile(r"\[\[(?:File|Image):(?:[^\[\]]|\[\[[^\]]*\]\])*\]\]",
               re.I),                                          # image
]

# A TEMPLATE is skipped by walking its braces, not by a pattern that spells the
# nesting out.  What stood here matched three levels and carried the cap in its
# own comment (`# template (≤3 deep)`); 106 templates in the raw corpus nest
# deeper, and they are overwhelmingly figure legends —
# `{{center|{{lh|88%|{{smaller|{{sc|Fig.}} 1.}}}}}}` is four — because that is
# where EB1911 stacks templates hardest.  Unskipped lead layout is not a cosmetic
# miss here: this walk exists to REACH the heading, so a template it cannot step
# over hides the heading behind it ([[feedback_walker_on_raw_source]]).
#
# `template_end` returns None for a template that never closes, and returning
# None here means "not lead layout" — the walk stops rather than guessing a close
# and swallowing the rest of the page ([[feedback_honesty_surface_failures]]).
def _skip_template(body: str, pos: int) -> "int | None":
    if not body.startswith(TEMPLATE_OPEN, pos):
        return None
    return template_end(body, pos)


def _skip_pattern(pat: "re.Pattern"):
    """Adapt a lead PATTERN to the same (body, pos) -> end | None contract."""
    def skip(body: str, pos: int) -> "int | None":
        m = pat.match(body, pos)
        return m.end() if m else None
    return skip


_LEAD_SKIPS = [_skip_pattern(p) for p in _LEAD] + [_skip_template]

# Strict Roman numeral, so real words made of Roman letters (CIVIL, DILL, VILL)
# aren't mistaken for section numbers; only well-formed numerals (II, IV) match.
_STRICT_ROMAN = re.compile(
    r"M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\.?$")
# Numbered structural headings (ORDER I, PART II …) — not article titles.
_NUMBERED = re.compile(
    r"^(?:ORDER|PART|SECTION|CLASS|BOOK|CHAPTER|DIVISION|GROUP|SERIES|PERIOD"
    r"|GRADE|LEGION|BRIGADE|FAMILY|TRIBE|GENUS|SUBORDER|SUBFAMILY)"
    r"\s+[IVXLCDM]+\b")
# A Title-case word (Cap then lowercase): the signature of a taxonomy subsection
# heading ("A. Rhachitomi", "Sub-class. TRILOBITA"), never an all-caps headword.
_TITLECASE_WORD = re.compile(r"^[A-ZÀ-Þ][a-zà-ÿ][a-zà-ÿ-]*$")


def _first_word_caps(t: str) -> bool:
    """True if the title's first word is uppercase-dominant — the headword
    signature.  Counting upper ≥ lower (rather than all-upper) keeps the
    lowercase-prefixed surnames (McPHERSON, MacVEAGH) and single-letter words
    (X RAYS, I.O.U.), and transliteration capitals (Ī, Ū, Ṣ) via
    ``str.isupper``; it still rejects title-case openers like 'Sub-class …'."""
    t = t.lstrip("ʿʼ'\"([{ \t.-")
    first = re.split(r"[\s,]", t, 1)[0]
    up = sum(c.isupper() for c in first)
    lo = sum(c.islower() for c in first)
    return up >= 1 and up >= lo


def _has_titlecase_word(t: str) -> bool:
    """True if any word is Title-case (Cap then lowercase) — taxonomy subsection
    headings ('A. Rhachitomi', 'Sub-class. TRILOBITA').  Mc/Mac surnames don't
    match (uppercase resumes after the prefix); all-caps headwords don't."""
    for w in re.split(r"[\s,]+", t):
        w = re.sub(r"^[^0-9A-Za-zÀ-ÿ]+|[^0-9A-Za-zÀ-ÿ]+$", "", w)
        if _TITLECASE_WORD.match(w):
            return True
    return False


# Read a block-opening heading down to its plain headword text — the classifier's
# eyes, recognition only.  «I» italics, a footnote, a link, a styler template, a
# disambiguator paren all come off; `uc`/`sc` content is folded to the CAPITALS it
# renders as, so the caps test reads true case.  NOT title production — produce_title
# owns that, downstream; here we only look enough to classify.
_HI = re.compile(r"«/?I»")
_HREF = re.compile(r"<ref[^>]*>.*?</ref>|<ref[^/]*/\s*>", re.DOTALL)
_HLINK = re.compile(r"\[\[(?:[^\]|]*\|)?([^\]]+)\]\]")
_HABBR = re.compile(r"\{\{\s*abbr\s*\|([^{}|]*)\|[^{}]*\}\}", re.I)
_HCAPS = re.compile(r"\{\{\s*(?:uc|sc|asc|small[\s-]?caps?)\s*\|([^{}|]*)\}\}", re.I)
_HTMPL3 = re.compile(r"\{\{[^{}|]+\|[^{}]*\|([^{}|]*)\}\}")
_HTMPL2 = re.compile(r"\{\{[^{}|]+\|([^{}|]*)\}\}")
_HTMPL0 = re.compile(r"\{\{[^{}]*\}\}")
_HTAG = HTML_TAG_RE
_HPAREN = re.compile(r"\s*\([^)]*\)")


def _heading_text(raw_heading: str) -> str:
    """The plain headword text of a raw «B» heading, for classification only."""
    t = _HI.sub("", raw_heading)
    t = _HREF.sub("", t)
    t = _HLINK.sub(r"\1", t)
    t = _HABBR.sub(r"\1", t)
    t = _HCAPS.sub(lambda m: m.group(1).upper(), t)
    t = until_stable(
        t, lambda s: _HTMPL0.sub("", _HTMPL2.sub(r"\1", _HTMPL3.sub(r"\1", s))))
    t = _HTAG.sub("", t)
    t = _HPAREN.sub("", t)
    return re.sub(r"\s+", " ", t).strip(" ,.;:")


def _is_title(raw_heading: str) -> bool:
    """The one classification: is this block-opening heading an article title?
    One question in two parts — is the headword caps-set PROSE (the EB1911 title
    convention), and NOT a numeral or formula (which wear the same bold at the
    same block starts)?  Everything else fell out of those two."""
    t = _heading_text(raw_heading)
    if len(t) < 2:                                   # empty / lone char (dropcap)
        return False
    if (t[0].isdigit() or "·" in t or "→" in t       # not prose: a numeral /
            or re.search(r"[A-Za-z]\d|\d[A-Za-z]", t)  #   formula (CH3, C6H5) /
            or _STRICT_ROMAN.match(t)                #   roman (II, IV) /
            or _NUMBERED.match(t)):                  #   section marker (ORDER I)
        return False
    if _has_titlecase_word(t):                       # Title-case = subsection
        return False                                 #   (A. Rhachitomi, Sub-class.)
    return len(t) == 2 or _first_word_caps(t)        # caps-prose headword


def _heading_at(body: str, pos: int):
    """Skip lead layout from ``pos``; return the `«B»` heading match there
    (positions in ``body``), or None if the next content isn't a heading."""
    prev = -1
    while pos != prev:
        prev = pos
        m = _WS.match(body, pos)
        if m:
            pos = m.end()
        for skip in _LEAD_SKIPS:
            end = skip(body, pos)
            if end is not None:
                pos = end
                break
    return _HEADING.match(body, pos)


def article_starts(stream: str, page_keys: list, section_keys: list) -> list[int]:
    """Where EB1911's articles START: one offset per title block.

    The engine's boundaries hook (``Corpus.article_starts``).  The engine
    builds the volume stream and its keys ONCE and passes them here — this
    was ``super_walk(volume)``, which rebuilt the stream itself.  The engine
    orders and de-duplicates the offsets and does everything after.

    For each `<section begin>` section: scan every block start (section open,
    each blank line, each table close) for a title heading; each is an article.
    Plus the single-letter drop-cap case.  Continuations (no opening heading)
    and subsection headings (rejected by `_is_title`) fall out for free."""
    out: list[int] = []
    for i, (sec_off, _name) in enumerate(section_keys):
        # The tag itself is no longer in the stream — its position IS the key, so
        # the section runs from this key to the next.
        seg_start = sec_off
        seg_end = section_keys[i + 1][0] if i + 1 < len(section_keys) else len(stream)
        body = stream[seg_start:seg_end]

        seen: set[int] = set()
        # Single-letter article: a drop-cap opener (any of the source's six
        # template shapes), not a bold heading — the title producer's own
        # structural detector (sole owner of drop-cap letter extraction).
        letter = _letter_from_dropcap(body.lstrip())
        if letter:
            seen.add(0)
            out.append(seg_start)

        # Block starts: the section open, each blank line / table close, AND each
        # page break inside this section (see `_BLOCK_BOUNDARY`).
        starts = sorted({0}
                        | {m.end() for m in _BLOCK_BOUNDARY.finditer(body)}
                        | {off - seg_start for off, _pg in page_keys
                           if seg_start <= off < seg_end})
        for pos in starts:
            m = _heading_at(body, pos)
            if m is None or m.start() in seen or not _is_title(m.group(1)):
                continue
            seen.add(m.start())
            gpos = seg_start + m.start()
            out.append(gpos)

    return out
