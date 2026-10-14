"""Pages where our tables might replace what Wikisource has — no reads, the
fetched pages only.  Two kinds:

  flat     a table the OCR flattened into lines of figures: a run of MIN_RUN+
           consecutive lines dense with figures (MIN_FIGS+ digit runs, a
           MIN_SHARE+ share of the line's tokens), outside any table the page
           sets, on a page not proofread (quality 0 or 1)
  missing  a `{{missing table}}`: the page's own mark that a table belongs there

Pages whose tables are already patched (data/readings/tables/) are left out,
and vol 29 (the index: its entries are lines of figures by nature).  For each
page: the printed page, its articles, its quality, whether we have a reading
and whether the judge saw it, each block's size and first lines.

Writes data/staging/patches/table_candidates.json; prints the list.
Usage: table_candidates.py  (book root)"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))
from paths import PAGES, TABLE_READINGS, WORK, reading

from eb1911.scans import _printed
from wikikit.export.corpus import load_corpus
from wikikit.scan.patches import MISSING_TABLE

MIN_FIGS, MIN_SHARE, MIN_RUN = 2, 0.3, 3
LEVEL = re.compile(r'pagequality level="(\d)"')
TABLES = re.compile(r"(?s)^\s*\{\|.*?^\s*\|\}|<table.*?</table>", re.M | re.I)
TOK = re.compile(r"\d+(?:[·.,]\d+)*|[^\W\d_]+")


def tabular(line: str) -> bool:
    toks = TOK.findall(line)
    figs = [t for t in toks if t[0].isdigit()]
    return len(figs) >= MIN_FIGS and len(figs) >= MIN_SHARE * len(toks)


def flat_blocks(raw: str) -> list[dict]:
    """Runs of tabular lines outside the page's own tables."""
    lines = TABLES.sub(lambda x: "\n" * x.group(0).count("\n"), raw).split("\n")
    out, run, start = [], 0, 0
    for i, line in enumerate(lines + [""]):
        if not line.strip() and run:
            continue
        if tabular(line):
            start = i if not run else start
            run += 1
        else:
            if run >= MIN_RUN:
                out.append({"kind": "flat", "lines": run,
                            "sample": [l.strip() for l in lines[start:start + 12] if l.strip()][:6]})
            run = 0
    return out


def main():
    pp = _printed("printed_pages.json")
    judged = set(PAGES.read_text().split())
    done = {f.stem for f in TABLE_READINGS.glob("vol_*/*.json")}
    corpus, _ = load_corpus()
    arts = {}
    for a in corpus.values():
        p0 = a.get("ws_page_start")
        for q in range(p0, (a.get("ws_page_end") or p0) + 1) if p0 is not None else ():
            arts.setdefault((a["volume"], q), []).append(a["title"])
    out = {}
    for f in sorted(Path("data/raw/wikisource").glob("vol_*/vol*-page*.json")):
        if f.parent.name == "vol_29" or f.stem in done:
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        raw = d.get("raw_text") or ""
        m = LEVEL.search(raw)
        level = m.group(1) if m else "?"
        blocks = flat_blocks(raw) if level in ("0", "1") else []
        for mt in MISSING_TABLE.finditer(raw):
            after = [l.strip() for l in raw[mt.end():mt.end() + 600].split("\n") if l.strip()][:4]
            blocks.append({"kind": "missing", "lines": 0, "sample": after})
        if not blocks:
            continue
        v, p = d["volume"], d["page_number"]
        out[f.stem] = {"volume": v, "ws": p, "printed": pp.get(str(v), {}).get(str(p)),
                       "articles": arts.get((v, p), [])[:4], "level": level,
                       "read": reading(f.stem).exists(), "judged": f.stem in judged, "blocks": blocks}
    (WORK / "table_candidates.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    kinds = {k: sum(any(b["kind"] == k for b in c["blocks"]) for c in out.values()) for k in ("flat", "missing")}
    print(f"{len(out)} pages: {kinds}; read {sum(c['read'] for c in out.values())}, "
          f"judged {sum(c['judged'] for c in out.values())}")
    for stem, c in out.items():
        print(f"\n{stem} vol {c['volume']} p. {c['printed']} [q{c['level']}{' read' if c['read'] else ''}"
              f"{' judged' if c['judged'] else ''}] {', '.join(c['articles'])}")
        for b in c["blocks"]:
            print(f"   {b['kind']} {b['lines'] or ''}: " + " / ".join(b["sample"])[:240])


if __name__ == "__main__":
    main()
