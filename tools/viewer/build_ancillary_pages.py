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
input language with no wikitext and no markers — read by `vision_text`, which
the Topics page also uses for the Classified Table of Contents introduction.
"""
import io
import json
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
from vision_text import _vision_to_html
from build_preface import build_toc_html
from britannica.source_pages import load_pages

VIEWER_DIR = Path("tools/viewer")
ANCILLARY_JSON = Path("data/derived/vol29_ancillary.json")


def _page_template(title: str, scan_href: str, body_html: str,
                   toc_html: str = "", byline: str = "") -> str:
    """The Editorial Preface's shell, for the transcription pages.

    The `&larr; Ancillary` back-link is gone deliberately: the model page has no
    such affordance, carrying `Ancillary` in the nav row instead, and these
    pages are meant to be indistinguishable from it.
    """
    meta_html = f"{byline} &middot; " if byline else ""
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
      border-radius: 2px; padding: 20px 24px; margin-bottom: 20px; }}
    h1 {{ margin-top: 0; font-size: 1.8rem; font-variant: small-caps;
      letter-spacing: 0.06em; color: #2c2416; }}
    /* The Editorial Preface's rules verbatim.  Links were underlined here for
       one reason: that page sets `a {{ text-decoration: none }}` globally and
       this template never did, so every contents entry got the browser default.
       Matching the model page fixes the contents list and the nav together
       instead of patching `.toc a` and leaving the next link to repeat it. */
    a {{ color: var(--link); text-decoration: none; }}
    a:hover {{ text-decoration: underline; background: rgba(139, 115, 85, 0.08);
      border-radius: 2px; }}
    .meta {{ color: var(--muted); font-size: 0.95rem; font-style: italic;
      margin-bottom: 16px; }}
    .header-divider {{ text-align: center; color: #8b7355; font-size: 1.6rem;
      margin: -6px 0 14px; letter-spacing: 0.3em; user-select: none; }}
    /* Margin headings, on the Editorial Preface's model: the body is inset and
       the note is lifted into the gap, beside the sentence it annotates.  Both
       prefaces carry shoulder headings, so both should read the same way. */
    .body {{ margin-right: 160px; position: relative; font-size: 1.08rem; }}
    .body p {{ text-indent: 1.5em; margin: 0 0 0.5em 0; position: relative; }}
    .body p:first-of-type {{ text-indent: 0; }}
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
      /* The note is IN FLOW at this width, and on this page it leads the first
         paragraph — so ::first-letter enlarges the NOTE's first letter, not the
         prose's.  Measured as a 20.8px cap on "Need for an Index." where the
         desktop view correctly showed 34.56px on "IT may".  There is nothing to
         drop-cap onto once a heading leads the paragraph, so switch it off
         rather than decorate the heading. */
      .body p:first-of-type:has(.shoulder-heading)::first-letter {{
        font-size: inherit; float: none; margin: 0; color: inherit;
      }}
    }}
    .toc {{ background: var(--bg); border: 1px solid var(--border);
      border-radius: 8px; padding: 12px 16px; margin-bottom: 20px; font-size: 0.9rem; }}
    .toc h3 {{ margin: 0 0 8px 0; font-size: 0.95rem; color: var(--muted); }}
    .toc ol {{ margin: 0; padding-left: 20px; columns: 2; column-gap: 24px; }}
    .toc li {{ margin-bottom: 3px; }}
    .toc a {{ color: var(--text); font-size: 0.88rem; }}
    /* The print's drop initial, the Editorial Preface's rule verbatim. */
    .body p:first-of-type::first-letter {{
      font-size: 3.2em; float: left; line-height: 0.8;
      margin: 0.05em 2px 0 0; color: #5c4a32;
    }}
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
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
      <h1 style="margin: 0; font-size: 1.15rem; color: #5c4a32;"><a href="/home.html" style="color: inherit; text-decoration: none;"><svg viewBox="0 0 32 32" width="28" height="28" style="vertical-align: middle; margin-right: 10px;" aria-hidden="true"><rect x="1" y="1" width="30" height="30" fill="none" stroke="currentColor" stroke-width="1"/><rect x="3.5" y="3.5" width="25" height="25" fill="none" stroke="currentColor" stroke-width="0.6"/><text x="16" y="22" text-anchor="middle" font-family="Georgia, serif" font-size="16" fill="currentColor" style="letter-spacing:-0.3px">EB</text></svg><span style="font-variant: small-caps; letter-spacing: 0.04em;">{title}</span> <span style="font-variant: normal; font-style: italic; letter-spacing: 0.01em;">&mdash; 11th Edition</span></a></h1>
      <div style="font-size: 0.9rem;">
        <a href="/index.html">Articles</a>
        &nbsp;&middot;&nbsp;
        <a href="/contributors.html">Contributors</a>
        &nbsp;&middot;&nbsp;
        <a href="/topics.html">Topics</a>
        &nbsp;&middot;&nbsp;
        <a href="/ancillary.html">Ancillary</a>
        &nbsp;&middot;&nbsp;
        <a href="/download.html">Download</a>
      </div>
    </div>
    <div class="meta">{meta_html}<a href="{scan_href}" style="color: var(--muted);">View source scans &rarr;</a></div>
  </div>
  <div class="header-divider">&#x223C;&#x25C6;&#x223C;</div>
  <div class="card">
    <div class="body">
{toc_html}
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
        scan_href="scans.html?vol=1&start=7&end=10&prefix=page&label=Prefatory+Note&back=ancillary.html",
        body_html=html,
    )
    out = VIEWER_DIR / "ancillary-prefatory-note.html"
    out.write_text(page, encoding="utf-8")
    print(f"  {out}")


def build_index_preface():
    data = json.loads(ANCILLARY_JSON.read_text(encoding="utf-8"))
    html, toc = _vision_to_html(data["index_preface"],
                                drop_leading_title=True)
    page = _page_template(
        toc_html=build_toc_html(toc),
        title="Preface to the Index",
        byline='By <a href="/contributors.html?q=Janet+Hogarth" '
               'style="color: var(--muted);">Janet E. Hogarth</a> and '
               '<a href="/contributors.html?q=Malcolm+Mitchell" '
               'style="color: var(--muted);">J. Malcolm Mitchell</a>',
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
