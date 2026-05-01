"""Verify every static asset referenced by deployed HTML is reachable on britannica11.org.

Scans tools/viewer/*.html for asset references — `<script src=...>`,
`<link href=...>`, document.write-injected scripts, `IS_LOCAL ? : `
ternaries, and `${BASE}/file.json` template literals — then HEAD-checks
each one against the live site. Catches the "shipped HTML that
references a file we forgot to upload" bug class (the article-urls.js
near-miss on 2026-04-22).

References are split into two classes:
  - HARD  — <script>, <link>, <img>, document.write injections.
            A missing one of these breaks page rendering. Failure
            here exits non-zero so rebuild_all.sh's `set -e` suppresses
            the success banner.
  - SOFT  — fetch() literals and ternary data paths. Production code
            wraps these in `.catch(() => …)` so the page still loads
            when missing. Failures here print as warnings only.
"""

from __future__ import annotations

import re
import sys
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VIEWER_DIR = ROOT / "tools" / "viewer"
SITE = "https://britannica11.org"
TIMEOUT_SECS = 15
MAX_WORKERS = 16

_STATIC_EXT = (".json", ".js", ".svg", ".css", ".jpg", ".jpeg",
               ".png", ".gif", ".ico", ".html", ".txt", ".pdf")

_TAG_RE = re.compile(
    r"""<(?:script|link|img)\s[^>]*?(?:src|href)\s*=\s*["']([^"']+)["']""",
    re.IGNORECASE,
)
_DOCWRITE_BASE_RE = re.compile(
    r"""['"]\s*\+\s*base\s*\+\s*['"]([^'"]+)['"]""",
)
_DATA_LITERAL_RE = re.compile(
    r"""["'](/data/[^"'\s]+?)["']""",
)
_TERNARY_PROD_RE = re.compile(
    r"""IS_LOCAL\w*\s*\?\s*(?:"[^"]*"|'[^']*'|`[^`]*`)\s*:\s*(?:"([^"]+)"|'([^']+)'|`([^`]+)`)""",
)
_VAR_DECL_RE = re.compile(
    r"""(?:const|let|var)\s+(\w+)\s*=\s*IS_LOCAL\w*\s*\?\s*(?:"[^"]*"|'[^']*'|`[^`]*`)\s*:\s*(?:"([^"]+)"|'([^']+)'|`([^`]+)`)""",
)
_TEMPLATE_REF_RE = re.compile(
    r"""`\$\{(\w+)\}([^`$]+)`""",
)

_LOCAL_TO_PROD = [
    ("/data/derived/articles/", "/data/articles/"),
    ("/data/derived/", "/data/"),
]


def is_external(url: str) -> bool:
    return url.startswith(("http://", "https://", "//", "mailto:", "tel:", "data:"))


def has_dynamic(url: str) -> bool:
    return "${" in url or "{{" in url


def to_prod(url: str) -> str:
    for src, dst in _LOCAL_TO_PROD:
        if url.startswith(src):
            return dst + url[len(src):]
    return url


def has_static_ext(url: str) -> bool:
    base = url.split("?", 1)[0].split("#", 1)[0].lower()
    return base.endswith(_STATIC_EXT)


def normalize(url: str) -> str:
    url = url.split("?", 1)[0].split("#", 1)[0]
    url = to_prod(url)
    if not url.startswith("/"):
        url = "/" + url
    return re.sub(r"/+", "/", url)


def collect_refs(html_path: Path) -> tuple[set[str], set[str]]:
    """Return (hard_refs, soft_refs) for one HTML file."""
    text = html_path.read_text(encoding="utf-8", errors="replace")
    hard: set[str] = set()
    soft: set[str] = set()

    # HARD: <script src>, <link href>, <img src>
    for m in _TAG_RE.finditer(text):
        url = m.group(1).strip()
        if not url or is_external(url) or has_dynamic(url) or url.startswith("#"):
            continue
        hard.add(url)

    # HARD: document.write('...' + base + 'NAME...')
    for m in _DOCWRITE_BASE_RE.finditer(text):
        name = m.group(1).strip().lstrip('/"\\').rstrip('"\\')
        name = name.split('"', 1)[0].split("'", 1)[0]
        if name and not has_dynamic(name):
            hard.add("/" + name)

    # SOFT: collect all IS_LOCAL prod sides per declared name
    var_prods: dict[str, list[str]] = {}
    for m in _VAR_DECL_RE.finditer(text):
        name = m.group(1)
        prod = m.group(2) or m.group(3) or m.group(4) or ""
        if prod and not has_dynamic(prod):
            var_prods.setdefault(name, []).append(prod)

    # SOFT: inline ternary production side
    for m in _TERNARY_PROD_RE.finditer(text):
        prod = m.group(1) or m.group(2) or m.group(3) or ""
        if (prod and not has_dynamic(prod) and prod.startswith("/")
                and has_static_ext(prod)):
            soft.add(prod)

    # SOFT: template-literal fetches `${VAR}/file.json` against /data/-shaped
    # prefixes only. Other prefixes (e.g. base="index.html") are not
    # directories and would synthesize bogus paths.
    for m in _TEMPLATE_REF_RE.finditer(text):
        name, suffix = m.group(1), m.group(2)
        if not suffix:
            continue
        for prefix in var_prods.get(name, []):
            if not prefix.startswith("/data/"):
                continue
            joined = prefix.rstrip("/") + "/" + suffix.lstrip("/")
            if has_static_ext(joined):
                soft.add(joined)

    # SOFT: bare /data/... literals other than dev-only paths
    for m in _DATA_LITERAL_RE.finditer(text):
        url = m.group(1)
        if (has_dynamic(url) or not has_static_ext(url)
                or url.startswith("/data/derived/")):
            continue
        soft.add(url)

    return (
        {normalize(u) for u in hard if has_static_ext(normalize(u))},
        {normalize(u) for u in soft if has_static_ext(normalize(u))},
    )


def check_url(path: str) -> tuple[str, int | str]:
    url = SITE + path
    req = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECS) as resp:
            return path, resp.status
    except urllib.error.HTTPError as e:
        return path, e.code
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return path, f"ERR:{e.__class__.__name__}"


def report(label: str, refs: set[str], failures: dict[str, int | str],
           sources: dict[str, set[str]], stream) -> None:
    print(f"  {label}: {len(refs)} ref(s), {len(failures)} broken", file=stream)
    for path in sorted(failures):
        srcs = sorted(sources.get(path, ()))
        head = ", ".join(srcs[:3])
        if len(srcs) > 3:
            head += f" (+{len(srcs) - 3} more)"
        print(f"    [{failures[path]}] {path}  — {head}", file=stream)


def main() -> int:
    html_files = sorted(VIEWER_DIR.glob("*.html"))
    if not html_files:
        print(f"No HTML files found under {VIEWER_DIR}", file=sys.stderr)
        return 2

    hard_all: set[str] = set()
    soft_all: set[str] = set()
    sources: dict[str, set[str]] = {}
    for f in html_files:
        h, s = collect_refs(f)
        hard_all.update(h)
        soft_all.update(s)
        for p in h | s:
            sources.setdefault(p, set()).add(f.name)
    # If a path appears in both, treat it as hard (stronger constraint wins)
    soft_all -= hard_all

    every = hard_all | soft_all
    print(f"Scanning {len(html_files)} HTML files; "
          f"{len(hard_all)} hard + {len(soft_all)} soft = {len(every)} unique refs.")

    statuses: dict[str, int | str] = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(check_url, r): r for r in sorted(every)}
        for fut in as_completed(futures):
            path, status = fut.result()
            statuses[path] = status

    hard_fail = {p: s for p, s in statuses.items() if p in hard_all and s != 200}
    soft_fail = {p: s for p, s in statuses.items() if p in soft_all and s != 200}

    if soft_fail:
        print("Soft (fetch) references not reachable:")
        report("soft", soft_all, soft_fail, sources, sys.stdout)

    if hard_fail:
        print("FAIL: missing hard (script/link/img) references:", file=sys.stderr)
        report("hard", hard_all, hard_fail, sources, sys.stderr)
        return 1

    print(f"OK: all {len(hard_all)} hard references reachable"
          + (f" ({len(soft_fail)} soft warnings above)" if soft_fail else "")
          + ".")
    return 0


if __name__ == "__main__":
    sys.exit(main())
