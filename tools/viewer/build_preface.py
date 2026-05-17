"""Build the static Editorial Preface page from raw Wikisource wikitext.

Run manually when the Editorial Preface ever needs regeneration:

    uv run python tools/viewer/build_preface.py

Reads `data/raw/wikisource/vol_01/vol01-page{0010..0023}.json`,
processes the raw_text (not the half-processed cleaned_preview that
the old dynamic preface.html used), and emits a fully static
`tools/viewer/preface.html` — same shell as ancillary-prefatory-note.html,
with the body, TOC, and footnotes pre-rendered.

Why this script exists at all (rather than `prepare_wikitext` →
`export_front_matter.py`):

  * The Editorial Preface is ancillary content, not article content.
    Per the principle "ancillary handling separate from article
    pipeline", this builder is standalone — it doesn't go through the
    DB or any article-pipeline stage.
  * The old dynamic path read the `cleaned_preview` field, which had
    already dropped most `<ref>` tags before our processing began.  The
    raw_text field has the actual source; rendering from there
    preserves both footnotes.
  * Editorial Preface content is frozen (1910).  Build once, commit.
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                              errors="replace")

# Reuse the article-pipeline's quote-run converter — same logic
# detect_boundaries / transform_articles already rely on.
from britannica.corrections import apply_corrections
from britannica.pipeline.stages.prepare_wikitext import _convert_quote_runs

VOL = 1
# Per-page (key is `vol:page`) corrections.json patches need apply
# at the SAME granularity as the article pipeline does, i.e. per
# source page BEFORE concatenation.  Editorial Preface uses leaves
# 10-23; only leaf 10 currently has a patch.  See data/corrections.json
# entry "1:10".
PAGES = range(10, 24)  # Editorial Preface only; pp.6-9 are Prefatory Note
RAW_DIR = Path("data/raw/wikisource/vol_01")
OUTPUT = Path("tools/viewer/preface.html")


# ── Stage 1: load + concatenate raw_text (per-page corrections applied) ─

def load_concatenated() -> str:
    parts: list[str] = []
    for p in PAGES:
        path = RAW_DIR / f"vol01-page{p:04d}.json"
        raw = json.loads(path.read_text(encoding="utf-8"))["raw_text"]
        # Apply corrections.json patches keyed by `vol:page` — same
        # source-of-truth typo file the article pipeline uses.
        raw = apply_corrections(raw, VOL)
        parts.append(raw)
    # Insert a single newline between pages.  The page-end of one
    # transcribed page often runs straight into the page-start of the
    # next (e.g. p10 ends `</ref>. To<noinclude>…</noinclude>` and p11
    # starts `<noinclude>…</noinclude>preserve`) with no whitespace
    # between the words — joining bare would render "Topreserve".  The
    # newline survives noinclude-stripping; within-paragraph whitespace
    # is collapsed to a single space at paragraph-wrap time.  Paragraph
    # boundaries that fall on page boundaries are unaffected because
    # the splitter expects `\n\s*\n` (a blank line), which a lone `\n`
    # doesn't produce.
    return "\n".join(parts)


# ── Stage 2: strip <noinclude>…</noinclude> ──────────────────────────
#
# <noinclude> wraps content that appears on the Wikisource page-edit
# view but is NOT transcluded into the main display: running headers
# ({{rh|…}}), pagequality markers, page-number footers, <references/>
# blocks that render the footnotes inline per-page.  All of these are
# noise for our consolidated rendering.

_NOINCLUDE_RE = re.compile(r"<noinclude>.*?</noinclude>", re.DOTALL)


def strip_noinclude(text: str) -> str:
    return _NOINCLUDE_RE.sub("", text)


# ── Stage 3: page-spanning hyphenated words ──────────────────────────
#
# `{{hws|stem|full-word}}` at end of one page pairs with `{{hwe|tail|
# full-word}}` at start of next page.  In our consolidated text both
# templates appear adjacent (with just a newline between).  Replace
# the pair with the full word (the 2nd parameter of either template
# is the joined form).

_HWS_RE = re.compile(r"\{\{hws\|([^|}]*)\|([^|}]*)\}\}\s*\{\{hwe\|([^|}]*)\|([^|}]*)\}\}")
# Also handle stranded ones (page ordering may produce orphans).
_HWS_LONE_RE = re.compile(r"\{\{hws\|[^|}]*\|([^|}]*)\}\}")
_HWE_LONE_RE = re.compile(r"\{\{hwe\|[^|}]*\|([^|}]*)\}\}")


def fix_hyphenated_words(text: str) -> str:
    text = _HWS_RE.sub(lambda m: m.group(2), text)  # paired
    text = _HWS_LONE_RE.sub(lambda m: m.group(1), text)
    text = _HWE_LONE_RE.sub(lambda m: m.group(1), text)
    return text


# ── Stage 4: convert wiki templates to internal markers / plain text ─

# `{{EB1911 Shoulder Heading|TEXT|align=…}}` → `«SH»TEXT«/SH»` with
# the align param discarded (we always render shoulder headings to the
# right margin in CSS).
_SH_RE = re.compile(
    r"\{\{\s*EB1911 Shoulder Heading\s*\|([^|}]*)(?:\|[^}]*)?\}\}",
    re.IGNORECASE,
)

# Drop-cap: `{{dropinitial|LETTER|SIZE}}` — emit as a span we can
# style.  Always followed immediately by `{{larger|REST}}` which
# completes the first word (e.g. drop-E + LSEWHERE = ELSEWHERE,
# drop-T + HE = THE).  Combine the two so the rendered first word
# is correct.
_DROP_PLUS_LARGER_RE = re.compile(
    r"\{\{\s*dropinitial\s*\|([^|}]*)\s*(?:\|[^}]*)?\}\}\s*"
    r"\{\{\s*larger\s*\|([^|}]*)\}\}"
)

# `{{nodent|X}}` — paragraph with no indent.  The opening-paragraph
# device.  Unwrap; we handle paragraph indent via CSS.
_NODENT_RE = re.compile(r"\{\{\s*nodent\s*\|", re.IGNORECASE)

# `{{center|X}}` / `{{c|X}}` — centred line.  Used for section
# subtitles within the Editorial Preface like "The Eleventh Edition
# and its Predecessors".  Wrap in a marker we can style.
_CENTER_RE = re.compile(r"\{\{\s*(?:center|c)\s*\|", re.IGNORECASE)

# `{{x-larger|X}}` / `{{xxx-larger|X}}` / `{{larger|X}}` — size hints
# we render via spans.  Unwrap to plain text inside a styled span.
_SIZE_RE = re.compile(
    r"\{\{\s*(x-larger|xxx-larger|larger)\s*\|", re.IGNORECASE)

# `{{sc|X}}` → `«SC»X«/SC»` small-caps (same marker article body uses).
_SC_RE = re.compile(r"\{\{\s*sc\s*\|([^|}]*)\}\}", re.IGNORECASE)

# `{{em}}` / `{{em|N}}` — em-space padding for table-like layouts.
# Render as a single em-space.
_EM_RE = re.compile(r"\{\{\s*em\s*(?:\|[^}]*)?\}\}", re.IGNORECASE)

# `{{smallrefs}}` / `{{references}}` — placeholders rendering the
# footnote list inline per-page.  We consolidate footnotes at the
# end, so drop these.
_SMALLREFS_RE = re.compile(r"\{\{\s*smallrefs\s*\}\}", re.IGNORECASE)

# `{{EB1911 article link|TARGET|DISPLAY}}` — internal cross-reference.
# Render as a link to /article/... or fall back to a search-style URL.
# The preface's two uses are non-critical; emit as plain text for now
# (the source articles aren't necessarily in vol 1).
_ARTICLE_LINK_RE = re.compile(
    r"\{\{\s*EB1911 article link\s*\|[^|}]*\|([^|}]*)\}\}",
    re.IGNORECASE,
)

# Generic balanced-brace stripper for any template whose body is
# already in marker/text form after the specific handlers above.
_BRACE_STRIP_RE = re.compile(
    r"\{\{(?:[^{}]|\{\{[^{}]*\}\})*\}\}"
)

# `<small>X</small>` is the EB1911 convention for emphasising a
# small-caps word inline (e.g. E<small>NCYCLOPÆDIA</small> meaning
# "ENCYCLOPÆDIA" rendered small-caps with a large initial).  Render
# as a small-caps span over the whole.
_SMALL_TAG_RE = re.compile(r"<small>(.*?)</small>", re.DOTALL)


def _unwrap_balanced(text: str, opener_re: re.Pattern[str],
                     prefix: str = "", suffix: str = "") -> str:
    """Replace each balanced-brace template match starting at
    `opener_re` with `prefix + inner + suffix`, where `inner` is the
    template's first-parameter content (with quote-run markers and
    nested templates preserved)."""
    out = []
    pos = 0
    for m in opener_re.finditer(text):
        start = m.end()
        depth = 1
        i = start
        while i < len(text) and depth > 0:
            if text[i:i + 2] == "{{":
                depth += 1
                i += 2
            elif text[i:i + 2] == "}}":
                depth -= 1
                i += 2
            else:
                i += 1
        if depth != 0:
            continue
        inner = text[start:i - 2]
        # First parameter only (handle nested pipes from sub-templates).
        # For our templates the first parameter is the whole body.
        out.append(text[pos:m.start()])
        out.append(prefix + inner + suffix)
        pos = i
    out.append(text[pos:])
    return "".join(out)


def convert_templates(text: str) -> str:
    # Drop `{{center|{{xxx-larger|TITLE}}}}` — the document-level
    # title ("EDITORIAL INTRODUCTION" in print).  Redundant with the
    # static page header that already shows "Editorial Preface".
    # Identified by the `xxx-larger` size template; the four section
    # subtitles use `x-larger` and are preserved below.
    text = re.sub(
        r"\{\{\s*center\s*\|\s*\{\{\s*xxx-larger\s*\|[^{}]*\}\}\s*\}\}",
        "", text, flags=re.IGNORECASE,
    )
    # Wrap SH with `\n\n` on both sides so the shoulder heading lands
    # in its own paragraph break (same as the fetch pipeline's
    # `_shoulder_to_heading`).  Without these, body text BEFORE and
    # AFTER the inline SH template ("Mitchell's{{SH}}assistance") is
    # glued together when the SH span is pulled out of flow by its
    # CSS `position: absolute` — visible as "subjects.assistance"
    # with no space.
    text = _SH_RE.sub(
        lambda m: f"\n\n«SH»{m.group(1).strip()}«/SH»\n\n", text)
    # Drop-cap + larger pair: emit drop-cap span + remainder as plain text.
    text = _DROP_PLUS_LARGER_RE.sub(
        lambda m: f'<span class="drop-cap">{m.group(1)}</span>{m.group(2)}',
        text,
    )
    # Strip remaining stray `{{dropinitial|...}}` if any (none expected
    # without a paired larger).
    text = re.sub(r"\{\{\s*dropinitial\s*\|[^}]*\}\}", "", text,
                  flags=re.IGNORECASE)
    text = _SC_RE.sub(lambda m: f"«SC»{m.group(1)}«/SC»", text)
    text = _EM_RE.sub(" ", text)  # em-space
    text = _SMALLREFS_RE.sub("", text)
    text = re.sub(r"\{\{\s*references\s*/?\s*\}\}", "", text,
                  flags=re.IGNORECASE)
    text = _ARTICLE_LINK_RE.sub(lambda m: m.group(1), text)
    # Balanced-brace unwrappers for nodent / center / size templates.
    # Centered subtitles ARE in the print source ("The Eleventh Edition
    # and its Predecessors", "Questions of Formal Arrangement", etc.) —
    # production drops them only because the fetch pipeline silently
    # strips `{{center|…}}` from cleaned_preview, which is a bug.  We
    # preserve them via a `«CENTER»…«/CENTER»` marker rendered as a
    # `<div class="centered">…</div>` block.
    text = _unwrap_balanced(text, _NODENT_RE)
    text = _unwrap_balanced(text, _CENTER_RE,
                            prefix='«CENTER»', suffix='«/CENTER»')
    text = _unwrap_balanced(text, _SIZE_RE)
    # Final pass: any remaining balanced-brace template (e.g.
    # `{{EB1911 fine print/s}}` / `…/e}}`) → drop.
    text = _BRACE_STRIP_RE.sub("", text)
    return text


# ── Stage 5: convert <ref>…</ref> → «FN:…«/FN» ───────────────────────

_REF_RE = re.compile(r"<ref(?:\s[^>]*)?>(.*?)</ref>", re.DOTALL)
_REFERENCES_INLINE_RE = re.compile(r"<references\s*/?>", re.IGNORECASE)


def convert_refs(text: str) -> str:
    text = _REF_RE.sub(lambda m: f"«FN:{m.group(1).strip()}«/FN»", text)
    text = _REFERENCES_INLINE_RE.sub("", text)
    return text


# ── Stage 5b: render wikilinks as clickable HTML anchors ────────────
#
# The Editorial Preface uses `[[w:Person|Display]]` for Wikipedia
# entries and `[[Author:Wikisource-Name|Display]]` for contributor
# references.  The fetch pipeline's cleaned_preview stripped these to
# plain text, so production never showed them as links — but they
# carry useful navigation that we now restore.
#
#   `[[w:Foo Bar|Display]]`       → en.wikipedia.org/wiki/Foo_Bar
#   `[[Author:Foo Bar|Display]]`  → /contributors.html?q=Display
#   `[[Bare target]]`             → plain text (no in-site article
#                                   link, since the preface refers
#                                   to topics by description rather
#                                   than to specific EB1911 articles)

_WIKILINK_RE = re.compile(r"\[\[([^\[\]|]+)(?:\|([^\[\]]+))?\]\]")


def render_wikilinks(text: str) -> str:
    def _replace(m: re.Match) -> str:
        target = m.group(1).strip()
        display = (m.group(2) if m.group(2) is not None else target).strip()
        if target.lower().startswith("w:"):
            page = target[2:].strip().replace(" ", "_")
            return f'<a href="https://en.wikipedia.org/wiki/{quote(page)}">{display}</a>'
        if target.lower().startswith("author:"):
            return f'<a href="/contributors.html?q={quote(display)}">{display}</a>'
        return display
    return _WIKILINK_RE.sub(_replace, text)


# ── Stage 6: simple HTML tag handling ────────────────────────────────

def convert_html_tags(text: str) -> str:
    # <small>X</small> → small-caps span
    text = _SMALL_TAG_RE.sub(
        lambda m: f'<span class="small-caps">{m.group(1)}</span>', text)
    return text


# ── Stage 7: marker → HTML rendering ─────────────────────────────────
#
# Mirrors the JS logic from the old dynamic preface.html, ported to
# Python so we produce static output.


def slugify(s: str) -> str:
    s = re.sub(r"&[a-z]+;|&#x[0-9a-f]+;", " ", s, flags=re.IGNORECASE)
    s = re.sub(r"<[^>]+>", "", s)
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


_HTML_SPACE_RE = re.compile(
    r"&(?:emsp|ensp|nbsp|thinsp);|[    ]"
)


def clean_sh_text(s: str) -> str:
    # Shoulder-heading source often has `<br>` line breaks (some
    # mid-word like `com-<br>mon`), `«B»`/`«I»` markers, em-space
    # entities (`&emsp;` for indented continuation lines), and a
    # trailing `.` we want to drop for the TOC slug + label.
    #   • HTML space entities (`&emsp;`/`&ensp;`/`&nbsp;`) and their
    #     Unicode equivalents → regular space.  Mirrors the JS's
    #     `.replace(/ /g, " ")`.
    #   • `<br>` → space, then `- ` (hyphen+space) removal joins
    #     soft-hyphenated words split across the print line break
    #     (e.g. `com-<br>mon` → `com- mon` → `common`).  Mirrors the
    #     JS's `.replace(/- /g, "")`.
    #   • Markers must be stripped BEFORE rstrip(".") since the
    #     period is typically inside the bold span
    #     (e.g. `«B»A new departure.«/B»`), which rstrip wouldn't
    #     see — the visible char would still be `»`.
    s = _HTML_SPACE_RE.sub(" ", s)
    s = re.sub(r"<br\s*/?>", " ", s, flags=re.IGNORECASE)
    s = re.sub(r"«/?[BI]»", "", s)
    s = s.replace("- ", "")
    s = re.sub(r"\s{2,}", " ", s).strip()
    return s.rstrip(".")


def render_markers(text: str) -> tuple[str, list[tuple[str, str]],
                                       list[str]]:
    """Convert internal markers to final HTML.  Returns
    (body_html, toc_entries, footnote_bodies)."""
    toc: list[tuple[str, str]] = []
    used_ids: set[str] = set()

    def _reserve_id(slug: str, fallback: str) -> str:
        candidate = f"section-{slug}" if slug else fallback
        if candidate not in used_ids:
            used_ids.add(candidate)
            return candidate
        for n in range(2, 100):
            c = f"{candidate}-{n}"
            if c not in used_ids:
                used_ids.add(c)
                return c
        return candidate

    sh_counter = [0]
    def _sh(m: re.Match) -> str:
        raw_text = m.group(1)
        clean = clean_sh_text(raw_text)
        # Strip wikitext bold/italic markers from inside the SH for the
        # visible label (the user-visible shoulder margin is plain).
        visible = re.sub(r"«/?[BI]»", "", clean)
        slug = slugify(visible)
        sh_counter[0] += 1
        sid = _reserve_id(slug, f"sh-{sh_counter[0]}")
        toc.append((sid, visible))
        # Mirror the fetch pipeline's `_shoulder_to_heading` behavior:
        # strip bold (`'''` / `«B»` markers — print shoulders are
        # italic-only via CSS, not bold-italic), collapse `<br>` to
        # spaces, normalize HTML space entities (`&emsp;` etc. that
        # appear inside multi-line shoulders to align continuation),
        # and join soft-hyphenated words split across the print line
        # break (`com-<br>mon` → `com- mon` → `common`, matching the
        # JS `.replace(/- /g, "")`).  The trailing period in the
        # source is preserved in the body span.
        sh_html = _HTML_SPACE_RE.sub(" ", raw_text)
        sh_html = re.sub(r"<br\s*/?>", " ", sh_html, flags=re.IGNORECASE)
        sh_html = re.sub(r"«/?B»", "", sh_html)
        sh_html = sh_html.replace("- ", "")
        sh_html = re.sub(r"«I»(.*?)«/I»", r"<i>\1</i>", sh_html)
        sh_html = re.sub(r"\s+", " ", sh_html).strip()
        return f'<span class="shoulder-heading" id="{sid}">{sh_html}</span>'

    text = re.sub(r"«SH»(.*?)«/SH»", _sh, text, flags=re.DOTALL)

    fn_counter = [0]
    footnotes: list[str] = []
    def _fn(m: re.Match) -> str:
        fn_counter[0] += 1
        n = fn_counter[0]
        footnotes.append(m.group(1).strip())
        # Mark the anchor so the back-link from the bottom-of-page
        # note list can scroll the reader back to where they were
        # reading — same pattern viewer.html uses (`id="fnref-N"`).
        return (f'<sup class="footnote-ref" id="fnref-{n}">'
                f'<a href="#fn-{n}">{n}</a></sup>')

    text = re.sub(r"«FN:(.*?)«/FN»", _fn, text, flags=re.DOTALL)
    text = re.sub(r"«B»(.*?)«/B»", r"<b>\1</b>", text, flags=re.DOTALL)
    text = re.sub(r"«I»(.*?)«/I»", r"<i>\1</i>", text, flags=re.DOTALL)
    text = re.sub(r"«SC»(.*?)«/SC»", r'<span class="small-caps">\1</span>',
                  text, flags=re.DOTALL)
    text = re.sub(r"«CENTER»(.*?)«/CENTER»",
                  r'<div class="centered">\1</div>', text, flags=re.DOTALL)
    # Any leftover marker → strip silently.
    text = re.sub(r"«/?[A-Z]+»", "", text)
    return text, toc, footnotes


# ── Stage 8: paragraph wrapping + assembly ───────────────────────────

def render_body(markered: str) -> tuple[str, list[tuple[str, str]],
                                        list[str]]:
    """Wrap text in `<p>`, merging shoulder-heading paragraphs into
    their surrounding body paragraph, then produce TOC + footnotes.

    Mirror's the production JS paragraph-merge logic: a paragraph
    that contains `«SH»…«/SH»` is appended to the previous
    paragraph AND the next paragraph is also appended to the same
    merged unit.  Net effect: prev + SH + next all live in one
    `<p>`, so the shoulder span (absolutely positioned via CSS) lays
    in the right margin alongside the merged prose rather than
    breaking it across blocks.
    """
    # Stage 1: split on blank lines, then merge SH paragraphs.
    raw_paras = [p for p in re.split(r"\n\s*\n", markered) if p.strip()]
    merged: list[str] = []
    i = 0
    while i < len(raw_paras):
        p = raw_paras[i]
        if "«SH»" in p:
            if merged:
                merged[-1] = merged[-1] + " " + p
            else:
                merged.append(p)
            # Consume the next paragraph too (unless it's also SH-only).
            if (i + 1 < len(raw_paras)
                    and "«SH»" not in raw_paras[i + 1]):
                merged[-1] = merged[-1] + " " + raw_paras[i + 1]
                i += 1
        else:
            merged.append(p)
        i += 1

    # Stage 2: render markers on the merged text.
    full = "\n\n".join(merged)
    rendered, toc, footnotes = render_markers(full)

    # Stage 3: paragraph-wrap.  Centered subtitles get their own
    # block (already `<div class="centered">…</div>`).
    body_parts = []
    for p in re.split(r"\n\s*\n", rendered):
        p = p.strip()
        if not p:
            continue
        if p.startswith('<div class="centered">'):
            body_parts.append(p)
        else:
            p = re.sub(r"\s+", " ", p)
            body_parts.append(f"<p>{p}</p>")
    return "".join(body_parts), toc, footnotes


# ── Stage 9: full-page assembly ──────────────────────────────────────

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Editorial Preface &mdash; Encyclop&aelig;dia Britannica, 11th Edition</title>
  <style>
    :root {{
      --bg: #f5f1eb; --panel: #fdfcf9; --text: #2c2416;
      --muted: #6b5e4f; --border: #d4cab8; --link: #7b3f00;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", "Cambria Math", "Segoe UI Symbol", "Noto Sans Symbols 2", serif;
      background: var(--bg); color: var(--text); line-height: 1.7;
    }}
    .page {{ max-width: 960px; margin: 0 auto; padding: 24px; }}
    .card {{ background: var(--panel); border: 1px solid var(--border);
      border-radius: 2px; padding: 20px 24px; margin-bottom: 20px; }}
    h1 {{ margin-top: 0; font-size: 1.8rem; font-variant: small-caps;
      letter-spacing: 0.06em; color: #2c2416; }}
    a {{ color: var(--link); text-decoration: none; }}
    a:hover {{ text-decoration: underline; background: rgba(139, 115, 85, 0.08); border-radius: 2px; }}
    .meta {{ color: var(--muted); font-size: 0.95rem; font-style: italic; margin-bottom: 16px; }}
    .preface-body {{ margin-right: 160px; position: relative; font-size: 1.08rem; }}
    .preface-body p {{ text-indent: 1.5em; margin: 0 0 0.5em 0; position: relative; }}
    .preface-body p:first-child {{ text-indent: 0; }}
    .preface-body .centered {{ text-align: center; font-style: italic;
      margin: 1.2em 0 0.5em; text-indent: 0; }}
    .shoulder-heading {{
      position: absolute; right: -170px; width: 150px;
      font-family: Georgia, "Times New Roman", "Cambria Math", "Segoe UI Symbol", "Noto Sans Symbols 2", serif;
      font-size: 0.65rem; font-style: italic; color: #8b7355;
      padding-right: 0.6em; text-align: left; text-indent: 0;
    }}
    @media (max-width: 900px) {{
      .preface-body {{ margin-right: 0; }}
      .shoulder-heading {{
        position: static; display: block; width: auto;
        margin: 0.5em 0 0.2em; font-weight: 600; color: var(--text);
      }}
    }}
    .drop-cap {{
      font-size: 3.2em; float: left; line-height: 0.8;
      margin: 0.05em 2px 0 0; color: #5c4a32; font-weight: normal;
    }}
    .small-caps {{ font-variant: small-caps; }}
    .footnote-ref a {{ color: #7b3f00; text-decoration: none;
      font-size: 1em; font-weight: 700; padding: 0 2px; cursor: pointer; }}
    .footnotes {{ border-top: 1px solid #8b7355; margin-top: 32px;
      padding-top: 16px; font-size: 0.88rem; color: var(--muted); line-height: 1.5; }}
    .footnotes h3 {{ font-size: 0.85rem; font-variant: small-caps;
      letter-spacing: 0.05em; color: #8b7355; margin-bottom: 10px; }}
    .footnotes ol {{ padding-left: 24px; list-style: none; }}
    .footnotes li {{ margin-bottom: 6px; text-indent: -1.5em; padding-left: 1.5em; }}
    .footnotes li a {{ color: #8b7355; text-decoration: none;
      font-weight: 600; margin-right: 2px; }}
    .toc {{ background: var(--bg); border: 1px solid var(--border);
      border-radius: 8px; padding: 12px 16px; margin-bottom: 20px; font-size: 0.9rem; }}
    .toc h3 {{ margin: 0 0 8px 0; font-size: 0.95rem; color: var(--muted); }}
    .toc ol {{ margin: 0; padding-left: 20px; columns: 2; column-gap: 24px; }}
    .toc li {{ margin-bottom: 3px; }}
    .toc a {{ color: var(--text); font-size: 0.88rem; }}
    .header-divider {{ text-align: center; color: #8b7355; font-size: 1.6rem;
      margin: -6px 0 14px; letter-spacing: 0.3em; user-select: none; }}
  </style>
  <script>
    (function() {{
      var isLocal = location.hostname === "localhost" || location.hostname === "127.0.0.1";
      var base = isLocal ? "/tools/viewer/" : "/";
      document.write('<link rel="icon" type="image/svg+xml" href="' + base + 'favicon.svg">');
    }})();
  </script>
</head>
<body>
  <div class="page">
    <div class="card">
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
        <h1 style="margin: 0; font-size: 1.15rem; color: #5c4a32;"><a href="/home.html" style="color: inherit; text-decoration: none;"><svg viewBox="0 0 32 32" width="28" height="28" style="vertical-align: middle; margin-right: 10px;" aria-hidden="true"><rect x="1" y="1" width="30" height="30" fill="none" stroke="currentColor" stroke-width="1"/><rect x="3.5" y="3.5" width="25" height="25" fill="none" stroke="currentColor" stroke-width="0.6"/><text x="16" y="22" text-anchor="middle" font-family="Georgia, serif" font-size="16" fill="currentColor" style="letter-spacing:-0.3px">EB</text></svg><span style="font-variant: small-caps; letter-spacing: 0.04em;">Editorial Preface</span> <span style="font-variant: normal; font-style: italic; letter-spacing: 0.01em;">&mdash; 11th Edition</span></a></h1>
        <div style="font-size: 0.9rem;">
          <a href="/index.html">Articles</a>
          &nbsp;&middot;&nbsp;
          <a href="/contributors.html">Contributors</a>
          &nbsp;&middot;&nbsp;
          <a href="/topics.html">Topics</a>
          &nbsp;&middot;&nbsp;
          <a href="/ancillary.html">Ancillary</a>
        </div>
      </div>
      <div class="meta">By <a href="/contributors.html?q=Hugh+Chisholm" style="color: var(--muted);">Hugh Chisholm</a> &middot; London, December 10, 1910 &middot; <a href="scans.html?vol=1&start=17&end=30&label=Editorial+Preface&back=ancillary.html" style="color: var(--muted);">View source scans &rarr;</a></div>
    </div>
    <div class="header-divider">&#x223C;&#x25C6;&#x223C;</div>
    <div class="card">
      <div class="preface-body">{TOC}{BODY}{FOOTNOTES}</div>
    </div>
  </div>
<script data-goatcounter="https://britannica11.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
</body>
</html>
"""


def build_toc_html(toc: list[tuple[str, str]]) -> str:
    if not toc:
        return ""
    items = "".join(
        f'<li><a href="#{sid}">{label}.</a></li>'
        for sid, label in toc
    )
    return f'<div class="toc"><h3>Contents</h3><ol>{items}</ol></div>'


def build_footnotes_html(fns: list[str]) -> str:
    if not fns:
        return ""
    # Match viewer.html's footnote-back-navigation pattern: clicking
    # the back-link scrolls the reader to the original `<sup
    # id="fnref-N">` rather than jumping to top-of-page (the default
    # `href="#"` behavior).
    items = "".join(
        f'<li id="fn-{i+1}" value="{i+1}">'
        f'<a onclick="var el=document.getElementById(\'fnref-{i+1}\');'
        f'if(el)el.scrollIntoView({{behavior:\'instant\',block:\'start\'}});'
        f'return false;" href="#">{i+1}.</a> {body}</li>'
        for i, body in enumerate(fns)
    )
    return f'<div class="footnotes"><h3>Notes</h3><ol>{items}</ol></div>'


def main() -> int:
    text = load_concatenated()
    text = strip_noinclude(text)
    text = fix_hyphenated_words(text)
    text = _convert_quote_runs(text)
    text = convert_refs(text)
    text = convert_html_tags(text)
    text = render_wikilinks(text)
    text = convert_templates(text)
    body_html, toc, footnotes = render_body(text)

    page = PAGE_TEMPLATE.format(
        TOC=build_toc_html(toc),
        BODY=body_html,
        FOOTNOTES=build_footnotes_html(footnotes),
    )
    OUTPUT.write_text(page, encoding="utf-8")
    print(f"Wrote {OUTPUT}: {len(page):,} chars; "
          f"{len(toc)} shoulder headings; {len(footnotes)} footnotes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
