#!/usr/bin/env python
"""Find the diagnostic that already answers your question — search before writing.

There are 60 scripts here and each docstring states the question it answers, so
the index exists; what was missing is a cheap way to consult it.  Writing a new
analysis script takes minutes and searching took composing a bash incantation,
so writing usually won.  Every one of those reinventions was WORSE than the tool
it duplicated: an alias audit that reported pairs "broken" which the real gate
accepts, leaf arithmetic that raised a production alarm with no instance behind
it, a wikitext stripper that ate 73% of a page.

    uv run python tools/diagnostics/what_answers.py dedup contributor
    uv run python tools/diagnostics/what_answers.py leaf scan page
    uv run python tools/diagnostics/what_answers.py --all

Searches each module's docstring AND the public helpers in `src/britannica`, so
"who maps a page to a leaf" finds `extract_scan.py` and `leaf_for_ws` alike.
"""
import argparse
import ast
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
DIAG = ROOT / "tools" / "diagnostics"
SRC = ROOT / "src" / "britannica"


def docstring_of(path):
    try:
        return ast.get_docstring(ast.parse(path.read_text(encoding="utf-8"))) or ""
    except (SyntaxError, UnicodeDecodeError, OSError):
        return ""


def public_functions(path):
    """`(name, first docstring line)` for each public top-level def."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError, OSError):
        return []
    out = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("__"):
                continue
            doc = (ast.get_docstring(node) or "").strip()
            out.append((node.name, doc.splitlines()[0] if doc else "", doc))
    return out


def score(text, terms):
    t = text.lower()
    return sum(t.count(w.lower()) for w in terms)


def row(hits, left, right, width=38):
    """One result line.  ONE owner for the shape — writing it twice is exactly
    the duplication `dup_constants.py` ratchets against, and it caught this file
    doing it."""
    return f"    [{hits:>2}] {left:<{width}} {right}"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("terms", nargs="*", help="words describing your question")
    ap.add_argument("--all", action="store_true", help="list every diagnostic")
    a = ap.parse_args()
    if not a.terms and not a.all:
        ap.print_help()
        return 1

    diags = []
    for p in sorted(DIAG.glob("*.py")):
        if p.name == pathlib.Path(__file__).name:
            continue
        doc = docstring_of(p)
        first = doc.strip().splitlines()[0] if doc.strip() else "(no docstring)"
        diags.append((p.name, first, doc))

    if a.all:
        for name, first, _ in diags:
            print(f"  {name:40s} {first[:80]}")
        return 0

    hits = sorted(((score(d + n, a.terms), n, f) for n, f, d in diags),
                  reverse=True)
    hits = [h for h in hits if h[0] > 0][:8]
    print(f"  DIAGNOSTICS matching {a.terms}:")
    if hits:
        for s, name, first in hits:
            print(row(s, name, first[:72]))
    else:
        print("    (none — check src/ below, then write one)")

    print(f"\n  PUBLIC FUNCTIONS in src/britannica matching {a.terms}:")
    fns = []
    for p in SRC.rglob("*.py"):
        for name, first, doc in public_functions(p):
            s = score(name + " " + doc, a.terms)
            if s:
                rel = p.relative_to(ROOT).as_posix()
                fns.append((s, f"{rel}:{name}", first))
    for s, where, first in sorted(fns, reverse=True)[:8]:
        print(row(s, where, first[:60], width=56))
    if not fns:
        print("    (none)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
