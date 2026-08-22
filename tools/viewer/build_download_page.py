"""Build download.html from docs/download.txt (rebuilt in Phase 6.2).

Markup, deliberately minimal:
  first line          the page title (shown in the header)
  blank line          paragraph break
  ---Shoulder.---     margin heading (shoulder-heading), auto-anchored by slug
  *italic*            <em>
  [text](url)         a link — explicit, since this page's links aren't articles
  first letter        drop-cap on paragraph one

No article auto-linking or contributor resolution (cf. build_about_page.py) — the
download page's links (the archive, Hugging Face, the source note) are all explicit.
"""
from __future__ import annotations

import re

from britannica.util.strings import section_slug
from pathlib import Path

SRC = Path("docs/download.txt")
OUT = Path("tools/viewer/download.html")

SHELL = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Encyclop&aelig;dia Britannica, 11th Edition &mdash; %%TITLE%%</title>
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
    /* The download list.  There are now six things to download, in three
       licenses and four formats; as running prose the reader had to parse a
       paragraph to find out whether the thing they wanted existed. */
    .dl-list { list-style: none; margin: 0.6em 0 0.2em; padding: 0; }
    .dl-list li {
      padding: 0.75em 0 0.75em 0;
      border-top: 1px solid var(--border);
      text-indent: 0;
    }
    .dl-list li:last-child { border-bottom: 1px solid var(--border); }
    .dl-list .dl-name { font-size: 1.06rem; }
    .dl-list .dl-meta {
      display: block;
      font-size: 0.8rem;
      font-style: italic;
      color: var(--muted);
      margin: 0.1em 0 0.35em;
    }
    .dl-list .dl-desc { display: block; font-size: 0.97rem; }
    .header-divider {
      text-align: center;
      color: #8b7355;
      font-size: 1.6rem;
      margin: -6px 0 14px;
      letter-spacing: 0.3em;
      user-select: none;
    }
  </style>
  <link rel="icon" type="image/svg+xml" href="/favicon.svg">
</head>
<body>
<div class="page">
  <div class="card">
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
      <h1 style="margin: 0; font-size: 1.15rem; color: #5c4a32;"><a href="/home.html" style="color: inherit; text-decoration: none;"><svg viewBox="0 0 32 32" width="28" height="28" style="vertical-align: middle; margin-right: 10px;" aria-hidden="true"><rect x="1" y="1" width="30" height="30" fill="none" stroke="currentColor" stroke-width="1"/><rect x="3.5" y="3.5" width="25" height="25" fill="none" stroke="currentColor" stroke-width="0.6"/><text x="16" y="22" text-anchor="middle" font-family="Georgia, serif" font-size="16" fill="currentColor" style="letter-spacing:-0.3px">EB</text></svg><span style="font-variant: small-caps; letter-spacing: 0.04em;">%%TITLE%%</span> <span style="font-variant: normal; font-style: italic; letter-spacing: 0.01em;">&mdash; 11th Edition</span></a></h1>
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
    <div class="body">
%%BODY%%
    </div>
  </div>
</div>
<script src="/gc-gate.js"></script>
<script data-goatcounter="https://britannica11.goatcounter.com/count" async src="//gc.zgo.at/count.js" onload="if(window.__gcReady)__gcReady()"></script>
</body>
</html>
"""


def _slug(text: str) -> str:
    return section_slug(text)


def _render(source: str) -> tuple[str, str]:
    lines = source.strip().split("\n")
    title = lines[0].strip() if lines else "Download"
    parts: list[str] = []
    para: list[str] = []
    first = True

    def inline(raw: str) -> str:
        """Links and italics — the rules shared by paragraphs and list items.
        One owner, because a second copy is how the two drift apart."""
        raw = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', raw)
        return re.sub(r"\*([^*]+)\*", r"<em>\1</em>", raw)

    def flush() -> None:
        nonlocal first
        if not para:
            return
        raw = " ".join(para)
        para.clear()
        raw = re.sub(r"-{3}(.+?)-{3}",
                     lambda m: (f'<span class="shoulder-heading" '
                                f'id="{_slug(m.group(1).strip())}">'
                                f'{m.group(1).strip()}</span>'), raw)
        raw = inline(raw)
        if first:
            raw = re.sub(r"^(\w)", r'<span class="drop-cap">\1</span>', raw.strip())
            first = False
        parts.append(f"<p>{raw.strip()}</p>")

    # A run of `* ` lines is a DOWNLOAD LIST, not a paragraph.  Each item is
    #     * [Name](url) :: format, size, license :: what it is
    # — the three fields a reader actually scans for.  Any of the last two may be
    # omitted.  Inline rules (links, italics) apply inside each field.
    items: list[str] = []

    def flush_items() -> None:
        if not items:
            return
        lis = []
        for raw in items:
            fields = [f.strip() for f in raw.split("::")]
            name = inline(fields[0])
            meta = f'<span class="dl-meta">{inline(fields[1])}</span>' if len(fields) > 1 else ""
            desc = f'<span class="dl-desc">{inline(fields[2])}</span>' if len(fields) > 2 else ""
            lis.append(f'<li><span class="dl-name">{name}</span>{meta}{desc}</li>')
        items.clear()
        parts.append(f'<ul class="dl-list">{"".join(lis)}</ul>')

    for line in lines[1:]:
        stripped = line.strip()
        if stripped.startswith("* "):
            flush()
            items.append(stripped[2:].strip())
        elif stripped:
            flush_items()
            para.append(stripped)
        else:
            # A blank line separates items for readability in the SOURCE; it does
            # not end the list.  Only prose does.  (Six one-item lists is what
            # happens otherwise, and the rules between entries disappear.)
            flush()
    flush()
    flush_items()
    return title, "\n".join(parts)


def main() -> None:
    title, body = _render(SRC.read_text(encoding="utf-8"))
    OUT.write_text(SHELL.replace("%%TITLE%%", title).replace("%%BODY%%", body),
                   encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
