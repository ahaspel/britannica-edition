"""Build the ancillary transcription HTML pages.

Produces:
  tools/viewer/ancillary-prefatory-note.html   (from vol 1 ws6-9 wikitext)
  tools/viewer/ancillary-index-preface.html    (from vol29_ancillary.json)
  tools/viewer/ancillary-abbreviations.html    (from vol29_ancillary.json)
"""
import io
import json
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                              errors="replace")

VIEWER_DIR = Path("tools/viewer")
VOL1_DIR = Path("data/raw/wikisource/vol_01")
ANCILLARY_JSON = Path("data/derived/vol29_ancillary.json")


def _wiki_to_html(text: str) -> str:
    """Convert wikitext to simple HTML paragraphs."""
    # Strip noinclude, running headers, section tags
    text = re.sub(r"<noinclude>.*?</noinclude>", "", text,
                  flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"\{\{rh\|[^}]*\}\}", "", text)
    text = re.sub(r"<section[^>]*>", "", text, flags=re.IGNORECASE)
    # Drop initial caps template
    text = re.sub(r"\{\{dropinitial\|(\w)\|[^}]*\}\}", r"\1", text)
    text = re.sub(r"\{\{dropinitial\|(\w)\}\}", r"\1", text)
    # No-indent template
    text = re.sub(r"\{\{nodent\|", "", text)
    # Strip {{c|...}} centering
    text = re.sub(r"\{\{c\|([^}]*)\}\}", r"\1", text)
    # Strip {{x-larger|...}} etc.
    text = re.sub(r"\{\{(?:x-larger|xx-larger|xxx-larger|larger|smaller)\|([^}]*)\}\}",
                  r"\1", text)
    # {{sc|...}} small caps
    text = re.sub(r"\{\{sc\|([^}]*)\}\}", r'<span style="font-variant:small-caps">\1</span>', text)
    # {{asc|...}} all small caps
    text = re.sub(r"\{\{asc\|([^}]*)\}\}", r'<span style="font-variant:small-caps">\1</span>', text)
    # Wikilinks: [[w:Name|Display]] or [[Name|Display]] or [[Name]]
    text = re.sub(r"\[\[w:[^|]*\|([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[\[[^|\]]*\|([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    # Bold/italic
    text = re.sub(r"'''([^']+)'''", r"<b>\1</b>", text)
    text = re.sub(r"''([^']+)''", r"<em>\1</em>", text)
    # Remaining templates: strip
    for _ in range(3):
        text = re.sub(r"\{\{[^{}|]*\|([^{}]*)\}\}", r"\1", text)
    text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    # Stray closing braces
    text = text.replace("}}", "").replace("{{", "")
    # HTML cleanup
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    # Paragraphs
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    return "\n".join(f"<p>{p}</p>" for p in paras)


def _vision_to_html(text: str) -> str:
    """Convert vision-OCR transcription to HTML."""
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
        # Shoulder notes (>> prefix)
        if stripped.startswith(">> "):
            result.append(f'<div class="shoulder">{stripped[3:]}</div>')
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
            output.append(f"<p>{block}</p>")
    return "\n".join(output)


def _page_template(title: str, back_label: str, back_href: str,
                   scan_href: str, body_html: str) -> str:
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
      font-family: Georgia, "Times New Roman", serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.7;
    }}
    .page {{ max-width: 720px; margin: 0 auto; padding: 24px; }}
    .card {{ background: var(--panel); border: 1px solid var(--border);
      border-radius: 2px; padding: 24px 32px; margin-bottom: 20px; }}
    h1 {{ margin-top: 0; font-size: 1.6rem; font-variant: small-caps;
      letter-spacing: 0.06em; text-align: center; }}
    .nav-link {{ color: var(--link); text-decoration: none; font-size: 0.95rem; }}
    .nav-link:hover {{ text-decoration: underline; }}
    .nav-row {{ display: flex; justify-content: space-between; margin-bottom: 16px;
      font-size: 0.9rem; }}
    .body p {{ margin: 0 0 12px; text-indent: 1.5em; }}
    .body p:first-child {{ text-indent: 0; }}
    .body p:first-child::first-letter {{ font-size: 2em; float: left;
      line-height: 0.9; padding: 3px 6px 0 0; font-weight: bold; }}
    .shoulder {{ color: var(--muted); font-style: italic; font-size: 0.85rem;
      text-align: right; margin: 4px 0; }}
    .abbrev-table {{ width: 100%; border-collapse: collapse; margin: 12px 0; }}
    .abbrev-table td {{ padding: 2px 12px 2px 0; vertical-align: top;
      border-bottom: 1px solid var(--border); font-size: 0.9rem; }}
    .abbrev-table .abbr {{ font-weight: bold; white-space: nowrap; width: 1%; }}
    .footer {{ color: var(--muted); font-size: 0.85rem; margin-top: 20px;
      text-align: center; }}
  </style>
</head>
<body>
<div class="page">
  <div class="card">
    <div class="nav-row">
      <a class="nav-link" href="{back_href}">&larr; {back_label}</a>
      <a class="nav-link" href="{scan_href}">View source scans &rarr;</a>
    </div>
    <h1>{title}</h1>
    <div class="body">
{body_html}
    </div>
  </div>
  <div class="footer">
    Transcribed from the original 1911 text.
  </div>
</div>
</body>
</html>"""


def build_prefatory_note():
    text = ""
    for ws in range(6, 10):
        p = VOL1_DIR / f"vol01-page{ws:04d}.json"
        if p.exists():
            d = json.loads(p.read_text(encoding="utf-8"))
            text += d.get("raw_text", "") + "\n\n"
    html = _wiki_to_html(text)
    page = _page_template(
        title="Prefatory Note",
        back_label="Ancillary",
        back_href="ancillary.html",
        scan_href="scans.html?vol=1&start=6&end=9&prefix=page&label=Prefatory+Note&back=ancillary.html",
        body_html=html,
    )
    out = VIEWER_DIR / "ancillary-prefatory-note.html"
    out.write_text(page, encoding="utf-8")
    print(f"  {out}")


def build_editorial_introduction():
    text = ""
    for ws in range(10, 24):
        p = VOL1_DIR / f"vol01-page{ws:04d}.json"
        if p.exists():
            d = json.loads(p.read_text(encoding="utf-8"))
            text += d.get("raw_text", "") + "\n\n"
    html = _wiki_to_html(text)
    page = _page_template(
        title="Editorial Introduction",
        back_label="Ancillary",
        back_href="ancillary.html",
        scan_href="scans.html?vol=1&start=10&end=23&prefix=page&label=Editorial+Introduction&back=ancillary.html",
        body_html=html,
    )
    out = VIEWER_DIR / "ancillary-editorial-introduction.html"
    out.write_text(page, encoding="utf-8")
    print(f"  {out}")


def build_index_preface():
    data = json.loads(ANCILLARY_JSON.read_text(encoding="utf-8"))
    html = _vision_to_html(data["index_preface"])
    page = _page_template(
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
    html = _vision_to_html(data["rules_and_abbreviations"])
    page = _page_template(
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
