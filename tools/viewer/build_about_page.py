"""Build about.html from docs/about.txt.

Markup conventions:
  - ALL CAPS WORDS -> linked to article
  - {{Name}} -> linked to contributor/article entry
  - ---Shoulder Header--- -> shoulder heading (margin note)
  - *italic* -> <em>
  - [link, transcribe] -> link to ancillary page
"""
import io
import json
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                              errors="replace")

SRC = Path("docs/about.txt")
OUT = Path("tools/viewer/about.html")
ARTICLES_INDEX = Path("data/derived/articles/index.json")

SKIP_CAPS = {
    "THE", "AND", "OR", "IN", "OF", "IT", "AN", "AS", "BY", "AT",
    "TO", "ON", "IS", "IF", "SO", "MR", "CO", "VS", "VOL", "OCR",
    "GPT", "AARON HASPEL",
}

# Explicit link targets for bare surnames that would otherwise
# match the wrong person in the index.
ARTICLE_OVERRIDES = {
    "FIELDING": "FIELDING, HENRY",
    "RICHARDSON": "RICHARDSON, SAMUEL",
    "CHESTERFIELD": "CHESTERFIELD, PHILIP DORMER STANHOPE",
    "JOHNSON": "JOHNSON, SAMUEL",
    "ORCHID": "ORCHIDS",
}

# Explicit link targets for {{display}} contributor references
# where the display text doesn't contain the surname.
CONTRIBUTOR_OVERRIDES = {
    "Sir Leslie": "STEPHEN, SIR LESLIE",
    "Lyman Abbott": "ABBOTT, LYMAN",
}


def _build_article_lookup():
    """Map UPPER TITLE -> (filename, title). Also build a reverse
    name index: FIRSTNAME LASTNAME -> LASTNAME, FIRSTNAME entry."""
    if not ARTICLES_INDEX.exists():
        return {}, {}
    articles = json.loads(ARTICLES_INDEX.read_text(encoding="utf-8"))
    lookup = {}
    reverse = {}  # "EDWARD GIBBON" -> "GIBBON, EDWARD"
    for a in articles:
        if a.get("article_type") != "article":
            continue
        upper = a["title"].strip().upper()
        if upper not in lookup:
            lookup[upper] = (a["filename"], a["title"])
        # Build reverse: "GIBBON, EDWARD" -> also findable as "EDWARD GIBBON"
        if ", " in upper:
            parts = upper.split(", ", 1)
            reversed_name = f"{parts[1]} {parts[0]}"
            if reversed_name not in reverse:
                reverse[reversed_name] = upper
    return lookup, reverse


def _article_url(filename):
    base = filename.replace(".json", "")
    # Stable-ID filename: "NN-NNNN-section-TITLE". Section slug is
    # lowercase+digits+hyphens; title starts at the first Unicode
    # uppercase character after the prefix.
    prefix_m = re.match(r"^(\d{2}-\d{4}-)", base)
    if prefix_m:
        for i in range(prefix_m.end(), len(base)):
            c = base[i]
            if c.isupper() and i > 0 and base[i - 1] == "-":
                stable = base[:i - 1]
                title = base[i:]
                return f"/article/{stable}/{title.lower()}"
    # Legacy fallback for numeric-only IDs.
    idx = base.index("-")
    page = base[:idx].lstrip("0") or "0"
    slug = base[idx + 1:].lower()
    return f"/article/{page}/{slug}"


def _make_link(title, lookup, reverse):
    """Try to resolve an ALL CAPS title to an article link."""
    clean = title.rstrip(".,;:!?")
    suffix = title[len(clean):]
    # Explicit override.
    if clean in ARTICLE_OVERRIDES:
        target = ARTICLE_OVERRIDES[clean]
        if target in lookup:
            fn, _ = lookup[target]
            return f'<a href="{_article_url(fn)}">{clean}</a>{suffix}'
    # Direct lookup.
    if clean in lookup:
        fn, _ = lookup[clean]
        return f'<a href="{_article_url(fn)}">{clean}</a>{suffix}'
    # Reverse name: EDWARD GIBBON -> GIBBON, EDWARD
    if clean in reverse:
        fn, _ = lookup[reverse[clean]]
        return f'<a href="{_article_url(fn)}">{clean}</a>{suffix}'
    # Single word: try "WORD," prefix match (FIELDING -> FIELDING, HENRY)
    if " " not in clean:
        for key, (fn, _) in lookup.items():
            if key.startswith(clean + ","):
                return f'<a href="{_article_url(fn)}">{clean}</a>{suffix}'
    return None


def _render(text, lookup, reverse):
    lines = text.strip().split("\n")
    if lines and lines[0].strip() == "About this Edition":
        lines = lines[1:]

    html_parts = []
    paragraphs = []
    toc_entries = []  # (slug, text) for each shoulder heading
    is_first_para = True

    def flush_para():
        nonlocal is_first_para
        if not paragraphs:
            return
        raw = " ".join(paragraphs)
        paragraphs.clear()

        # Shoulder headers: ---text--- -> margin note
        def replace_shoulder(m):
            heading_text = m.group(1).strip()
            slug = re.sub(r"[^a-z0-9]+", "-", heading_text.lower()).strip("-")
            toc_entries.append((slug, heading_text))
            return (f'<span class="shoulder-heading" id="{slug}">'
                    f'{heading_text}</span>')
        raw = re.sub(r"-{3}(.+?)-{3}", replace_shoulder, raw)

        # {{contributor}} links
        def replace_contributor(m):
            name = m.group(1).strip()
            # Explicit override
            if name in CONTRIBUTOR_OVERRIDES:
                target = CONTRIBUTOR_OVERRIDES[name]
                if target in lookup:
                    fn, _ = lookup[target]
                    return f'<a href="{_article_url(fn)}">{name}</a>'
            words = name.split()
            # Try exact
            upper = name.upper()
            if upper in lookup:
                fn, _ = lookup[upper]
                return f'<a href="{_article_url(fn)}">{name}</a>'
            # Try surname match
            surname = words[-1].upper() if words else ""
            for key, (fn, _) in lookup.items():
                if key.startswith(surname + ",") or key == surname:
                    return f'<a href="{_article_url(fn)}">{name}</a>'
            return name
        raw = re.sub(r"\{\{([^}]+)\}\}", replace_contributor, raw)

        # ALL CAPS article links. Match sequences of uppercase + spaces +
        # periods + hyphens + apostrophes, but split on commas to avoid
        # grabbing "FIELDING, RICHARDSON" as one match.
        def replace_article(m):
            title = m.group(0).strip()
            if title in SKIP_CAPS:
                return title
            link = _make_link(title, lookup, reverse)
            return link if link else title
        # Match ALL CAPS words/phrases (possibly hyphenated, with
        # apostrophes or spaces). Period excluded to avoid grabbing
        # across sentences.
        raw = re.sub(r"\b[A-Z][A-Z'-]*(?:\s[A-Z][A-Z'.-]*)*\b",
                     replace_article, raw)

        # *italic*
        raw = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", raw)

        # "prefatory remarks [link, transcribe]" -> direct link
        raw = raw.replace(
            "prefatory remarks [link, transcribe]",
            '<a href="ancillary-prefatory-note.html">prefatory remarks</a>'
        )
        # "prefatory note" -> direct link to the Prefatory Note ancillary page
        raw = re.sub(
            r"\bprefatory note\b",
            '<a href="ancillary-prefatory-note.html">prefatory note</a>',
            raw,
        )
        # Fallback in case wording changes
        raw = raw.replace(
            "[link, transcribe]",
            '(<a href="ancillary.html">transcribed here</a>)'
        )
        # Internal page links
        raw = raw.replace(
            "contributor index",
            '<a href="contributors.html">contributor index</a>'
        )
        raw = raw.replace(
            "Topic Index",
            '<a href="topics.html">Topic Index</a>'
        )
        raw = raw.replace(
            "Reader's Guide",
            '<a href="readers-guide.html">Reader\'s Guide</a>'
        )

        # Signature formatting
        raw = re.sub(r"^::", "&emsp;&emsp;", raw)
        raw = re.sub(r"^:", "&emsp;", raw)

        # Drop cap on first paragraph
        if is_first_para:
            raw = re.sub(
                r"^(\w)",
                r'<span class="drop-cap">\1</span>',
                raw.strip(),
            )
            is_first_para = False

        html_parts.append(f"<p>{raw.strip()}</p>")

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush_para()
        else:
            paragraphs.append(stripped)
    flush_para()

    _render.toc_entries = toc_entries
    return "\n".join(html_parts)

_render.toc_entries = []


PAGE_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Encyclop&aelig;dia Britannica, 11th Edition &mdash; About</title>
  <style>
    :root {
      --bg: #f5f1eb;
      --panel: #fdfcf9;
      --text: #2c2416;
      --muted: #6b5e4f;
      --border: #d4cab8;
      --link: #7b3f00;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Georgia, "Times New Roman", "Cambria Math", "Segoe UI Symbol", "Noto Sans Symbols 2", serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.7;
    }
    .page { max-width: 960px; margin: 0 auto; padding: 24px; }
    .card { background: var(--panel); border: 1px solid var(--border);
      border-radius: 2px; padding: 20px 24px; margin-bottom: 20px; }
    a { color: var(--link); text-decoration: none; }
    a:hover { text-decoration: underline; }
    .body {
      margin-right: 160px;
      position: relative;
      font-size: 1.08rem;
    }
    .body p {
      text-indent: 1.5em;
      margin: 0 0 0.5em 0;
      position: relative;
    }
    .body p:first-child { text-indent: 0; }
    .drop-cap {
      font-size: 3.2em;
      float: left;
      line-height: 0.8;
      margin: 0.05em 2px 0 0;
      color: #5c4a32;
      font-weight: normal;
    }
    .shoulder-heading {
      position: absolute;
      right: -170px;
      width: 150px;
      font-family: Georgia, "Times New Roman", "Cambria Math", "Segoe UI Symbol", "Noto Sans Symbols 2", serif;
      font-size: 0.65rem;
      font-style: italic;
      color: #8b7355;
      padding-right: 0.6em;
      text-align: left;
      text-indent: 0;
    }
    @media (max-width: 900px) {
      .body { margin-right: 0; }
      .shoulder-heading {
        position: static;
        display: block;
        width: auto;
        margin: 0.5em 0 0.2em;
        font-weight: 600;
        color: var(--text);
      }
    }
    .toc {
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px 16px;
      margin-bottom: 20px;
      font-size: 0.9rem;
    }
    .toc h3 {
      margin: 0 0 8px 0;
      font-size: 0.95rem;
      color: var(--muted);
    }
    .toc ol {
      margin: 0;
      padding-left: 20px;
      columns: 2;
      column-gap: 24px;
    }
    .toc li { margin-bottom: 3px; }
    .toc a { color: var(--text); font-size: 0.88rem; }
    .header-divider {
      text-align: center;
      color: #8b7355;
      font-size: 1.6rem;
      margin: -6px 0 14px;
      letter-spacing: 0.3em;
      user-select: none;
    }
  </style>
  <script>
    (function() {
      var isLocal = location.hostname === "localhost" || location.hostname === "127.0.0.1";
      var base = isLocal ? "/tools/viewer/" : "/";
      document.write('<link rel="icon" type="image/svg+xml" href="' + base + 'favicon.svg">');
    })();
  </script>
</head>
<body>
<div class="page">
  <div class="card">
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
      <h1 style="margin: 0; font-size: 1.15rem; color: #5c4a32;"><a href="/home.html" style="color: inherit; text-decoration: none;"><svg viewBox="0 0 32 32" width="28" height="28" style="vertical-align: middle; margin-right: 10px;" aria-hidden="true"><rect x="1" y="1" width="30" height="30" fill="none" stroke="currentColor" stroke-width="1"/><rect x="3.5" y="3.5" width="25" height="25" fill="none" stroke="currentColor" stroke-width="0.6"/><text x="16" y="22" text-anchor="middle" font-family="Georgia, serif" font-size="16" fill="currentColor" style="letter-spacing:-0.3px">EB</text></svg><span style="font-variant: small-caps; letter-spacing: 0.04em;">About</span> <span style="font-variant: normal; font-style: italic; letter-spacing: 0.01em;">&mdash; 11th Edition</span></a></h1>
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
  </div>
  <div class="header-divider">&#x223C;&#x25C6;&#x223C;</div>
  <div class="card">
%%TOC%%
    <div class="body">
%%BODY%%
    </div>
  </div>
</div>
</body>
</html>"""


def main():
    text = SRC.read_text(encoding="utf-8")
    lookup, reverse = _build_article_lookup()
    print(f"Article lookup: {len(lookup)} entries, {len(reverse)} reverse names")

    body_html = _render(text, lookup, reverse)

    # Build TOC from collected shoulder headings
    if _render.toc_entries:
        toc_items = "\n".join(
            f'      <li><a href="#{slug}">{heading}</a></li>'
            for slug, heading in _render.toc_entries
        )
        toc_html = (
            f'    <div class="toc">\n'
            f'      <h3>Sections</h3>\n'
            f'      <ol>\n{toc_items}\n      </ol>\n'
            f'    </div>'
        )
    else:
        toc_html = ""

    page = PAGE_TEMPLATE.replace("%%BODY%%", body_html)
    page = page.replace("%%TOC%%", toc_html)

    OUT.write_text(page, encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
