"""Build the ancillary transcription HTML pages.

Produces:
  tools/viewer/ancillary-prefatory-note.html   (from vol 1 ws6-9 wikitext)
  tools/viewer/ancillary-index-preface.html    (from vol29_ancillary.json)
  tools/viewer/ancillary-abbreviations.html    (from vol29_ancillary.json)

The WIKITEXT page (Prefatory Note) renders through
`ancillary_render.render_pages` — the same preprocess → walker → renderer
the corpus goes through (it used to own a private regex chain with a
catch-all `{{…}}` strip and a bare `.replace("}}","")`; sweeper-campaign
item K1).  The two vol-29 pages are VISION-OCR transcriptions — a different
input language with no wikitext and no markers — and keep their own small
`_vision_to_html`.
"""
import io
import json
import re
import sys
from pathlib import Path

# IDEMPOTENT.  Both this module and build_ancillary_pages force UTF-8 here,
# and build_ancillary_pages imports build_toc_html from this one — so the
# second rewrap wrapped an already-wrapped stdout and closed the first,
# turning every later print into "I/O operation on closed file".  Wrap only
# if the stream is not already UTF-8.
if (sys.stdout.encoding or "").lower().replace("-", "") != "utf8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")

from ancillary_render import footnotes_html, render_pages
from build_preface import build_toc_html
from britannica.util.strings import section_slug
from britannica.source_pages import load_pages

VIEWER_DIR = Path("tools/viewer")
ANCILLARY_JSON = Path("data/derived/vol29_ancillary.json")


_ALLCAPS_LINE = re.compile(r"[A-Z][A-Z .ÆŒ'’-]{2,40}")


def _strip_running_heads(text: str) -> str:
    """Remove the printed page's RUNNING HEADS, rejoining the prose they split.

    The transcription records the page exactly as it reads, so the header at the
    top of each printed page lands in the middle of whatever sentence spans the
    page break: "To help the reader to find / PREFACE / what he wants in the
    quickest and easiest way".  Three of them in the Index preface, one more in
    the abbreviations — every one cutting a sentence in half.

    THE DISCRIMINATOR IS REPETITION, not a list of words.  A standalone all-caps
    line that has already appeared is the page furniture; its first appearance is
    the real heading.  That keeps `INDEX` / `VOLUME XXIX` / `PREFACE` at the top,
    keeps `LIST OF ABBREVIATIONS` where it is first used as a heading, and — the
    case a word list would have got wrong — keeps the signatures
    `JANET E. HOGARTH.` and `J. MALCOLM MITCHELL.`, which are all-caps, stand
    alone, and are content.

    Removing the line is not enough: it sits between two blank lines, so deleting
    it alone leaves the sentence split across two paragraphs.  The surrounding
    break is closed as well, which is what rejoins the prose.
    """
    lines = text.split("\n")
    seen: set[str] = set()
    drop: set[int] = set()
    for i, raw in enumerate(lines):
        s = raw.strip()
        if not s or not _ALLCAPS_LINE.fullmatch(s):
            continue
        if s in seen:
            drop.add(i)
        else:
            seen.add(s)
    if not drop:
        return text
    out: list[str] = []
    i = 0
    while i < len(lines):
        if i in drop:
            # swallow the blank line before and after, so the prose closes up
            while out and not out[-1].strip():
                out.pop()
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if out and j < len(lines):
                out[-1] = out[-1].rstrip() + " " + lines[j].lstrip()
                i = j + 1
                continue
            i = j
            continue
        out.append(lines[i])
        i += 1
    return "\n".join(out)


def _vision_to_html(text: str) -> tuple[str, list]:
    """Convert vision-OCR transcription to (html, toc).

    The toc is `(section_id, label)` per shoulder heading, the same shape
    `build_preface.build_toc_html` consumes — one contents-list builder for
    both prefaces rather than a second one here."""
    toc: list = []
    text = _strip_running_heads(text)
    # Bold markers **text**
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    # Italic markers *text*
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    # Section headings (ALL CAPS lines)
    lines = text.split("\n")
    result = []
    in_abbrev_list = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            result.append("")
            continue
        # Detect abbreviation list entries (tab-separated)
        if "\t" in stripped and not in_abbrev_list:
            # Start of abbreviation table
            result.append('<table class="abbrev-table">')
            in_abbrev_list = True
        if in_abbrev_list:
            if "\t" in stripped:
                parts = stripped.split("\t", 1)
                result.append(f'<tr><td class="abbr">{parts[0]}</td>'
                              f'<td>{parts[1]}</td></tr>')
                continue
            else:
                result.append("</table>")
                in_abbrev_list = False
        # SHOULDER NOTES, on the Editorial Preface's model: a positioned SPAN
        # inside the paragraph, not a block pulled out of it.  In print the note
        # stands in the margin beside the sentence it annotates; an absolutely
        # positioned span sits exactly there and interrupts nothing, which is
        # both more faithful and simpler than lifting it out.  (Emitting a <div>
        # inside a <p> was the original bug — invalid, and it split sentences
        # across three lines.)  Anchored by slug so the contents list can link
        # to it, exactly as `build_preface` does.
        if stripped.startswith(">> "):
            label = re.sub(r"<[^>]+>", "", stripped[3:]).strip().rstrip(".")
            sid = f"section-{section_slug(label)}"
            toc.append((sid, label))
            result.append(
                f'<span class="shoulder-heading" id="{sid}">{stripped[3:]}</span>')
            continue
        result.append(stripped)
    if in_abbrev_list:
        result.append("</table>")

    # Join and make paragraphs from consecutive non-tag lines
    html = "\n".join(result)
    # Split on blank lines for paragraphs
    blocks = re.split(r"\n\n+", html)
    output = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if block.startswith("<table") or block.startswith("<tr") or block.startswith("<div"):
            output.append(block)
        elif block.startswith("<h"):
            output.append(block)
        else:
            # The shoulder span stays IN the paragraph — the CSS lifts it into
            # the margin, and it must be inside for `position: absolute` to
            # anchor against `p { position: relative }`.  But it is hoisted to
            # the FRONT of the paragraph, which is where the Editorial Preface
            # always has it: that source marks the note at a paragraph boundary,
            # while this OCR transcription records it wherever the eye met it in
            # the margin — sometimes mid-sentence ("a title such as the /
            # Concordance ideal avoided. / earldom of Derby").  Leading the
            # paragraph puts the note beside the passage it labels, exactly as
            # in print, AND leaves the prose unbroken for reading aloud, copying
            # and search, which an interleaved span does not.
            notes = re.findall(r'<span class="shoulder-heading".*?</span>', block, re.S)
            for n in notes:
                block = block.replace(n, " ", 1)
            block = re.sub(r"\s+", " ", block).strip()
            if block or notes:
                output.append(f"<p>{''.join(notes)}{block}</p>")
    return "\n".join(output), toc


def _page_template(title: str, back_label: str, back_href: str,
                   scan_href: str, body_html: str, toc_html: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Encyclop&aelig;dia Britannica, 11th Edition &mdash; {title}</title>
  <style>
    :root {{
      --bg: #f5f1eb;
      --panel: #fdfcf9;
      --text: #2c2416;
      --muted: #6b5e4f;
      --border: #d4cab8;
      --link: #7b3f00;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", "Cambria Math", "Segoe UI Symbol", "Noto Sans Symbols 2", serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.7;
    }}
    .page {{ max-width: 960px; margin: 0 auto; padding: 24px; }}
    .card {{ background: var(--panel); border: 1px solid var(--border);
      border-radius: 2px; padding: 24px 32px; margin-bottom: 20px; }}
    h1 {{ margin-top: 0; font-size: 1.6rem; font-variant: small-caps;
      letter-spacing: 0.06em; text-align: center; }}
    .nav-link {{ color: var(--link); text-decoration: none; font-size: 0.95rem; }}
    .nav-link:hover {{ text-decoration: underline; }}
    .nav-row {{ display: flex; justify-content: space-between; margin-bottom: 16px;
      font-size: 0.9rem; }}
    /* Margin headings, on the Editorial Preface's model: the body is inset and
       the note is lifted into the gap, beside the sentence it annotates.  Both
       prefaces carry shoulder headings, so both should read the same way. */
    .body {{ margin-right: 160px; position: relative; }}
    .body p {{ margin: 0 0 12px; text-indent: 1.5em; position: relative; }}
    .body p:first-child {{ text-indent: 0; }}
    .shoulder-heading {{
      position: absolute; right: -170px; width: 150px;
      font-family: Georgia, "Times New Roman", "Cambria Math", "Segoe UI Symbol", "Noto Sans Symbols 2", serif;
      font-size: 0.65rem; font-style: italic; color: #8b7355;
      padding-right: 0.6em; text-align: left; text-indent: 0;
    }}
    @media (max-width: 900px) {{
      .body {{ margin-right: 0; }}
      .shoulder-heading {{
        position: static; display: block; width: auto;
        margin: 0.5em 0 0.2em; font-weight: 600; color: var(--text);
      }}
    }}
    .toc {{ background: var(--bg); border: 1px solid var(--border);
      border-radius: 8px; padding: 12px 16px; margin-bottom: 20px; font-size: 0.9rem; }}
    .toc h3 {{ margin: 0 0 8px 0; font-size: 0.95rem; color: var(--muted); }}
    .toc ol {{ margin: 0; padding-left: 20px; columns: 2; column-gap: 24px; }}
    .toc li {{ margin-bottom: 3px; }}
    .toc a {{ color: var(--text); font-size: 0.88rem; }}
    .body p:first-child::first-letter {{ font-size: 2em; float: left;
      line-height: 0.9; padding: 3px 6px 0 0; font-weight: bold; }}
    .shoulder {{ color: var(--muted); font-style: italic; font-size: 0.85rem;
      text-align: right; margin: 4px 0; }}
    .centered {{ text-align: center; font-style: italic;
      margin: 1.2em 0 0.5em; text-indent: 0; }}
    .small-caps {{ font-variant: small-caps; }}
    .footnote-ref a {{ color: var(--link); text-decoration: none;
      font-weight: 700; padding: 0 2px; }}
    .footnotes {{ border-top: 1px solid var(--border); margin-top: 24px;
      padding-top: 12px; font-size: 0.88rem; color: var(--muted); }}
    .footnotes ol {{ padding-left: 24px; list-style: none; }}
    .abbrev-table {{ width: 100%; border-collapse: collapse; margin: 12px 0; }}
    .abbrev-table td {{ padding: 2px 12px 2px 0; vertical-align: top;
      border-bottom: 1px solid var(--border); font-size: 0.9rem; }}
    .abbrev-table .abbr {{ font-weight: bold; white-space: nowrap; width: 1%; }}
    .footer {{ color: var(--muted); font-size: 0.85rem; margin-top: 20px;
      text-align: center; }}
  </style>
  <link rel="icon" type="image/svg+xml" href="/favicon.svg">
</head>
<body>
<div class="page">
  <div class="card">
    <div class="nav-row">
      <a class="nav-link" href="{back_href}">&larr; {back_label}</a>
      <a class="nav-link" href="{scan_href}">View source scans &rarr;</a>
    </div>
    <h1>{title}</h1>
{toc_html}
    <div class="body">
{body_html}
    </div>
  </div>
  <div class="footer">
    Transcribed from the original 1911 text.
  </div>
</div>
<script src="/gc-gate.js"></script>
<script data-goatcounter="https://britannica11.goatcounter.com/count" async src="//gc.zgo.at/count.js" onload="if(window.__gcReady)__gcReady()"></script>
</body>
</html>"""


def build_prefatory_note():
    # The one raw reader: it applies corrections and RAISES on a page of this
    # named range that is missing, rather than quietly emitting a short note.
    raw_pages = [(p.page, p.text) for p in load_pages(1, pages=range(6, 10))[0]]
    doc = render_pages(raw_pages, volume=1, drop_leading_title=True)
    html = doc.body_html + footnotes_html(doc.footnotes)
    page = _page_template(
        title="Prefatory Note",
        back_label="Ancillary",
        back_href="ancillary.html",
        scan_href="scans.html?vol=1&start=7&end=10&prefix=page&label=Prefatory+Note&back=ancillary.html",
        body_html=html,
    )
    out = VIEWER_DIR / "ancillary-prefatory-note.html"
    out.write_text(page, encoding="utf-8")
    print(f"  {out}")


def build_index_preface():
    data = json.loads(ANCILLARY_JSON.read_text(encoding="utf-8"))
    html, toc = _vision_to_html(data["index_preface"])
    page = _page_template(
        toc_html=build_toc_html(toc),
        title="Preface to the Index",
        back_label="Ancillary",
        back_href="ancillary.html",
        scan_href="scans.html?vol=29&start=11&end=14&prefix=leaf&label=Preface+to+the+Index&back=ancillary.html",
        body_html=html,
    )
    out = VIEWER_DIR / "ancillary-index-preface.html"
    out.write_text(page, encoding="utf-8")
    print(f"  {out}")


def build_abbreviations():
    data = json.loads(ANCILLARY_JSON.read_text(encoding="utf-8"))
    # No shoulder headings on this one, so no contents list — build_toc_html
    # returns "" for an empty toc, which is the right answer rather than an
    # empty box.
    html, toc = _vision_to_html(data["rules_and_abbreviations"])
    page = _page_template(
        toc_html=build_toc_html(toc),
        title="Rules and Abbreviations",
        back_label="Ancillary",
        back_href="ancillary.html",
        scan_href="scans.html?vol=29&start=15&end=16&prefix=leaf&label=Rules+and+Abbreviations&back=ancillary.html",
        body_html=html,
    )
    out = VIEWER_DIR / "ancillary-abbreviations.html"
    out.write_text(page, encoding="utf-8")
    print(f"  {out}")


def main():
    print("Building ancillary transcription pages:")
    build_prefatory_note()
    build_index_preface()
    build_abbreviations()
    print("Done.")


if __name__ == "__main__":
    main()
