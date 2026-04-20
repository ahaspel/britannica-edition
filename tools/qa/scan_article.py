"""Scan the rendered HTML of an article for leak patterns that should
never appear in what a reader sees.

Each invariant is a pattern the viewer SHOULD have eliminated.
Anything that survives to rendered HTML is a bug — template that
didn't get processed, formatting marker that didn't become an HTML
tag, control character that didn't get stripped, wikitable syntax
that leaked into prose, and so on.

Usage:
    # One article, human-readable
    uv run python tools/qa/scan_article.py 20-0196-s4-ORCHIDS

    # Multiple, batched (single browser, much faster)
    uv run python tools/qa/scan_article.py 27-0028-s3-TOOL 24-0984-s2-SHIPBUILDING

    # From a fixture file (one filename per line, # comments allowed)
    uv run python tools/qa/scan_article.py --from-file tools/qa/fixtures/default.txt

    # JSON output (for baseline snapshots + diffs)
    uv run python tools/qa/scan_article.py --json --from-file …

    # Inspect the rule catalog
    uv run python tools/qa/scan_article.py --list-rules

Exit 0 if every article is clean; exit 1 if any violation found,
exit 2 on render failure (article not found, viewer timeout, etc.).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Ensure ``render_article`` is importable regardless of cwd.
sys.path.insert(0, str(Path(__file__).parent))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

from render_article import Renderer, DEFAULT_ARTICLE_PATH  # type: ignore  # noqa: E402


# ---------------------------------------------------------------------------
# Invariant catalog
# ---------------------------------------------------------------------------
# Each rule is a named pattern. Anything the scanner matches is a failure.
# Keep rules crisp: one leak class per rule so the violation message points
# at a specific bug class, not a generic "something is wrong."

RULES: list[tuple[str, str, re.Pattern]] = [
    (
        "template_opener_leak",
        "Wikitext ``{{name|…}}`` opener survived to rendered HTML. "
        "The viewer should have converted recognized templates to HTML; "
        "any surviving opener means the pipeline has a gap.",
        re.compile(r"\{\{[A-Za-z][A-Za-z0-9_]*\|"),
    ),
    (
        "template_arg_leak",
        "A template size/style argument (``3em|``, ``200px|``, ``width:…|``)"
        " slipped out of its enclosing template into visible text. Common "
        "cause: ``{{hi|3em|text}}``-style templates whose handler consumed"
        " only the last arg.",
        re.compile(
            r"(?<![0-9A-Za-z/])"
            r"(?:\d+(?:\.\d+)?(?:em|px|pt|%)|\d+(?:em|px)?:\d+(?:em|px)?)"
            r"\|"
        ),
    ),
    (
        "internal_marker_leak",
        "Internal element marker (``«MATH:``, ``«FN:``, ``«SEC:``, "
        "``«PRE:``, ``«LN:``, ``«HTMLTABLE:``, ``«SH»``) survived to "
        "rendered HTML. These are pipeline-internal and the viewer "
        "should render every one.",
        re.compile(r"\u00ab(?:MATH|FN|SEC|PRE|LN|HTMLTABLE|/HTMLTABLE|SH|/SH):?"),
    ),
    (
        "format_marker_leak",
        "Formatting marker (``«I»``, ``«B»``, ``«SC»``) survived to "
        "rendered HTML instead of becoming ``<i>``/``<b>``/"
        "``<span class='small-caps'>``.",
        re.compile(r"\u00ab/?(?:I|B|SC)\u00bb"),
    ),
    (
        "element_closer_leak",
        "Internal element closer (``}TABLE}``, ``}VERSE}``, ``}LEGEND}``, "
        "``«/MATH»``) survived to rendered HTML.",
        re.compile(r"\}(?:TABLE[A-Z]?|VERSE|LEGEND)\}|\u00ab/(?:MATH|FN|SEC|PRE|LN)\u00bb"),
    ),
    (
        "wikitable_syntax_leak",
        "Wikitable markup (``|-``, ``{|``, ``|}``, ``|+``) leaked into "
        "visible text. Note: bare ``||`` is ambiguous with math "
        "(``parallel lines``) and is not flagged here.",
        re.compile(r"(?:^|[\s>])\|[-}{+]|\{\|"),
    ),
    (
        "bold_italic_wikitext",
        "2- or 3-apostrophe bold/italic run survived as literal "
        "apostrophes instead of becoming ``<i>``/``<b>``.",
        re.compile(r"(?<!')''[A-Za-z0-9]"),
    ),
    (
        "control_char_leak",
        "Pipeline-internal control character (\\x01–\\x07) visible in "
        "rendered HTML. These should be stripped or converted to "
        "``<span class='page-marker'>``-style HTML.",
        re.compile(r"[\x01\x02\x03\x04\x05\x06\x07]"),
    ),
    (
        "double_entity_encoding",
        "HTML entity double-encoded (``&amp;amp;``, ``&amp;#39;``). "
        "Commonly leaks when the pipeline runs escapeHtml on text "
        "that already contained a literal HTML entity. Note: "
        "URL-encoded entities inside ``href=\"…\"`` attributes "
        "(e.g. ``%26%2339%3B`` for ``&#39;`` in a search query) are "
        "legitimate and NOT flagged.",
        re.compile(r"&amp;(?:amp|#\d+|[a-z]+);"),
    ),
    (
        "raw_image_marker_leak",
        "``{{raw image|…}}`` or ``{{IMG:…}}`` marker survived to "
        "rendered HTML. These should be ``<figure><img></figure>``.",
        re.compile(r"\{\{(?:raw\s+image|IMG):"),
    ),
    (
        "dangling_pipe_start",
        "A line begins with ``|``-whitespace, the signature of a "
        "wikitable cell that didn't unwrap. Often appears in prose when "
        "an outer-layout table fails to fully parse.",
        re.compile(r"(?:^|<br\s*/?>|</p>|\n)\s*\|\s+[^|\s]", re.MULTILINE),
    ),
]


def _ctx(html: str, start: int, end: int, width: int = 60) -> str:
    """Return the match with ``width`` chars of context on either side,
    HTML tag chunks collapsed so the snippet stays readable."""
    s = max(0, start - width)
    e = min(len(html), end + width)
    snippet = html[s:e]
    snippet = re.sub(r"<[^>]+>", " ", snippet)
    snippet = re.sub(r"\s+", " ", snippet).strip()
    return snippet


def scan_html(html: str) -> list[dict]:
    """Return list of violation dicts for a single article's HTML."""
    hits: list[dict] = []
    for name, _desc, pattern in RULES:
        for m in pattern.finditer(html):
            hits.append({
                "rule": name,
                "offset": m.start(),
                "context": _ctx(html, m.start(), m.end()),
            })
    return hits


def _print_human(filename: str, hits: list[dict], html_len: int,
                  verbose: bool) -> None:
    if not hits:
        print(f"[OK] {filename}  ({html_len} chars, no violations)")
        return
    by_rule: dict[str, list[dict]] = {}
    for h in hits:
        by_rule.setdefault(h["rule"], []).append(h)
    print(f"[FAIL] {filename}  ({len(hits)} violations)")
    for rule_name in sorted(by_rule):
        entries = by_rule[rule_name]
        print(f"  {rule_name} ({len(entries)}):")
        show = entries if verbose else entries[:3]
        for e in show:
            print(f"    @{e['offset']}:  …{e['context']}…")
        if not verbose and len(entries) > 3:
            print(f"    (+{len(entries) - 3} more — use --verbose)")


def scan_articles(names: list[str], json_out: bool = False,
                   verbose: bool = False,
                   base_path: str = DEFAULT_ARTICLE_PATH) -> tuple[int, int]:
    """Render and scan every article. Return (violation_count,
    render_fail_count)."""
    results: dict[str, dict] = {}
    total_violations = 0
    render_fails = 0
    with Renderer(base_path=base_path) as r:
        for name in names:
            try:
                html = r.render(name)
            except RuntimeError as e:
                results[name] = {"error": str(e), "violations": []}
                render_fails += 1
                if not json_out:
                    print(f"[RENDER-FAIL] {name}")
                    for line in str(e).splitlines()[:3]:
                        print(f"  {line}")
                continue
            hits = scan_html(html)
            results[name] = {
                "html_len": len(html),
                "violations": hits,
            }
            total_violations += len(hits)
            if not json_out:
                _print_human(name, hits, len(html), verbose)

    if json_out:
        json.dump(results, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
    else:
        print()
        print(f"Scanned {len(names)} article(s): "
              f"{total_violations} violations, "
              f"{render_fails} render failures.")
    return total_violations, render_fails


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("articles", nargs="*",
                    help="Article filenames (with or without .json).")
    ap.add_argument("--from-file", type=Path,
                    help="Read article filenames from a file "
                         "(one per line, blank / # comment lines ignored).")
    ap.add_argument("--list-rules", action="store_true",
                    help="List the invariant catalog and exit.")
    ap.add_argument("--verbose", action="store_true",
                    help="Show all matches per rule instead of the first 3.")
    ap.add_argument("--json", action="store_true",
                    help="Emit JSON results on stdout instead of the "
                         "human-readable report. Suitable as input to "
                         "diff_baselines.py.")
    ap.add_argument("--base-path", default=DEFAULT_ARTICLE_PATH,
                    help="Article path the viewer loads from "
                         "(default: %(default)s). Use "
                         "/data/qa_baseline/articles to scan a "
                         "downloaded S3 baseline. "
                         "Note on Git Bash: leading single-slash paths "
                         "get auto-converted to Windows paths. Either "
                         "use a double slash (``//data/qa_baseline/…``), "
                         "prefix with ``MSYS2_ARG_CONV_EXCL=``*, or "
                         "invoke from CMD/PowerShell.")
    # Undo MSYS2-style path conversion: if the shell converted
    # ``/data/…`` into ``C:/…/data/…`` or similar, pull the trailing
    # absolute path back out. Cheap heuristic — looks for the segment
    # that starts with a known project-root-relative prefix.
    def _unmangle(p: str) -> str:
        for anchor in ("/data/qa_baseline/", "/data/derived/"):
            i = p.find(anchor)
            if i > 0:
                return p[i:]
        return p
    args = ap.parse_args()

    if args.list_rules:
        for name, desc, pat in RULES:
            print(f"{name}")
            print(f"  {desc}")
            print(f"  pattern: {pat.pattern!r}")
            print()
        return 0

    names: list[str] = list(args.articles)
    if args.from_file:
        for line in args.from_file.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            names.append(s)
    if not names:
        ap.error("supply article filenames or --from-file")

    total, fails = scan_articles(names, json_out=args.json,
                                   verbose=args.verbose,
                                   base_path=_unmangle(args.base_path))
    if total or fails:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
