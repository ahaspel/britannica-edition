"""Build download.html from docs/download.txt (rebuilt in Phase 6d).

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
<script data-goatcounter="https://britannica11.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
</body>
</html>
"""


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _render(source: str) -> tuple[str, str]:
    lines = source.strip().split("\n")
    title = lines[0].strip() if lines else "Download"
    parts: list[str] = []
    para: list[str] = []
    first = True

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
        raw = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', raw)
        raw = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", raw)
        if first:
            raw = re.sub(r"^(\w)", r'<span class="drop-cap">\1</span>', raw.strip())
            first = False
        parts.append(f"<p>{raw.strip()}</p>")

    for line in lines[1:]:
        if line.strip():
            para.append(line.strip())
        else:
            flush()
    flush()
    return title, "\n".join(parts)


def main() -> None:
    title, body = _render(SRC.read_text(encoding="utf-8"))
    OUT.write_text(SHELL.replace("%%TITLE%%", title).replace("%%BODY%%", body),
                   encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
