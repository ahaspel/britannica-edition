"""What markup do Wikisource's transcribers use on this book's pages, and how
much of it can our transcription vocabulary say?

Every template, well-formed HTML tag and wikitext construct in every fetched
page's body (its noinclude header and footer aside), tallied by name: on how
many pages, how many uses, and whether the scan vocabulary covers it — the
shared constructs plus the book's own (`wikikit.scan.vocabulary.constructs`)
and the table forms (`{|`, `{{Ts}}`, `{{brace2}}`).  A construct the
transcribers use on hundreds of pages and the vocabulary lacks is one the
book's collection (`Corpus.scan_constructs`, the desk's
`scan_notation.json`) should consider.  Each row gives one example.

Read-only.  Usage: markup_census.py [N rows, default 100]   (book root)"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parents[1] / "patches"))
from whole_candidates import TAG, TEMPLATE

from wikikit.scan.vocabulary import constructs
from wikikit.source_pages import RAW_DIR

#: wikitext's own constructs, besides templates and tags
WIKI = {
    "'''": r"(?<!')'''(?!')",
    "''": r"(?<!')''(?!')",
    "[[link": r"\[\[(?!(?:File|Image):)",
    "[[File": r"\[\[(?:File|Image):",
    "{|": r"(?m)^\s*\{\|",
    "== heading": r"(?m)^=+[^=\n]+=+\s*$",
    ": indent": r"(?m)^:+",
    "* list": r"(?m)^[*#]+",
    "<!-- comment": r"<!--",
    "&entity;": r"&[a-z]+;|&#\d+;",
}


def norm(name: str) -> str:
    return re.sub(r"[\s_]+", " ", name.strip().lower()).removeprefix("template:")


def covered() -> set[str]:
    """The names the vocabulary can write, as this census names them."""
    out = {"{|", "{{ts", "{{brace2"}
    for c in constructs():
        o = c.open
        if o.startswith("{{"):
            out.add("{{" + norm(o[2:].rstrip("|")))
        elif o.startswith("<"):
            out.add("<" + o.strip("<>").split()[0].lower())
        else:
            out.add(o)
    return out


def main():
    rows = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    pages, uses, example = Counter(), Counter(), {}
    n = 0
    for f in sorted(Path(RAW_DIR).glob("vol_*/*.json")):
        t = json.loads(f.read_text(encoding="utf-8")).get("raw_text") or ""
        body = re.sub(r"<noinclude>[\s\S]*?</noinclude>", "", t)
        if not body.strip():
            continue
        n += 1
        found = Counter()
        for m in TEMPLATE.finditer(body):
            k = "{{" + norm(m.group(1))
            found[k] += 1
            example.setdefault(k, (f.stem, body[m.start():m.start() + 70]))
        for m in TAG.finditer(body):
            if m.group(0).startswith("</"):
                continue
            k = "<" + m.group(1).lower()
            found[k] += 1
            example.setdefault(k, (f.stem, body[m.start():m.start() + 70]))
        for k, pat in WIKI.items():
            for m in re.finditer(pat, body):
                found[k] += 1
                example.setdefault(k, (f.stem, body[max(0, m.start() - 10):m.start() + 60]))
        uses.update(found)
        pages.update(found.keys())
    have = covered()
    print(f"{n} fetched pages with text; {len(pages)} distinct constructs\n")
    print(f"{'construct':34} {'pages':>6} {'uses':>8}  vocab  example")
    for k, p in pages.most_common(rows):
        ex = example[k]
        print(f"{k[:34]:34} {p:6} {uses[k]:8}  {'yes' if k in have else ' - '}    "
              f"{ex[0]}: {ex[1]!r}"[:200])
    missing = [(k, p) for k, p in pages.most_common() if k not in have and p >= 20]
    print(f"\nnot in the vocabulary, on 20 pages or more: {len(missing)}")


if __name__ == "__main__":
    main()
