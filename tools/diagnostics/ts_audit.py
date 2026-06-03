"""Fast, focused {{Ts}}-leak audit.

The cost is the producer (~0.2s/article), not the DB — so we (a) run it in
PARALLEL across cores and (b) iterate only on the articles that actually LEAK.

  uv run python tools/diagnostics/ts_audit.py scan     # parallel pass over all
        Ts-bearing articles → per-context + per-article leak table; SAVES the
        leaking article-ids to tools/_scratch/ts_leakers.json
  uv run python tools/diagnostics/ts_audit.py ids       # re-run ONLY the saved
        leakers (a few seconds) — the dev loop while fixing the table producer

`scan --refresh` rebuilds the raw-text cache from the DB.
"""
from __future__ import annotations
import io, json, re, sys, time
from collections import Counter
from multiprocessing import Pool, cpu_count
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))   # _corpus_cache
sys.path.insert(0, str(ROOT / "src"))
from _corpus_cache import load_corpus, CACHE
LEAKERS = ROOT / "tools" / "_scratch" / "ts_leakers.json"

_TS = re.compile(r"\{\{\s*ts\b", re.IGNORECASE)


def _classify(pre: str) -> str:
    if re.search(r"<t[dh]\b[^>]*$", pre): return "<td/<th cell"
    if re.search(r"<tr\b[^>]*$", pre): return "<tr row"
    if re.search(r"<table\b[^>]*$", pre): return "<table opener"
    if re.search(r"\{\|[^\n]*$", pre): return "{| wiki-opener"
    if re.search(r"(?:^|\n)[!|][^\n]*$", pre): return "wiki !/| cell"
    if re.search(r"colspan|rowspan|scope=|align=|valign=", pre): return "bare cell-attr"
    if re.search(r"<p\b[^>]*$", pre): return "<p paragraph"
    if re.search(r"<div\b[^>]*$", pre): return "<div"
    if re.search(r"<span\b[^>]*$", pre): return "<span"
    if re.search(r"/FS\b|/SC\b", pre): return "after caption/FS"
    return "OTHER"


# Per-worker state (set in _init); the spy appends (context, sample) per leak.
_HITS: list[tuple[str, str]] = []


def _init():
    global _tx
    from britannica.pipeline.stages.transform_articles import body_text as BT
    from britannica.pipeline.stages.transform_articles import _transform_text_v2 as _tx2
    _strip_re = BT._STRIP_TEMPLATES_RE
    _orig = BT._strip_templates

    def _spy(text: str) -> str:
        prev, t = None, text
        while prev != t:
            prev = t
            for m in re.finditer(_strip_re, t):
                tok = m.group(0)
                nm = re.match(r"\{\{\s*([^|}\n]*)", tok)
                if nm and nm.group(1).strip().lower() == "ts":
                    pre = t[max(0, m.start() - 60):m.start()]
                    _HITS.append((_classify(pre), pre[-30:] + "⟦" + tok + "⟧"))
            t = re.sub(_strip_re, "", t)
        return _orig(text)
    BT._strip_templates = _spy
    globals()["_tx"] = _tx2


def _work(item):
    aid, vol, pg0, raw = item
    _HITS.clear()
    try:
        _tx(raw, vol, pg0)
    except Exception:
        pass
    return aid, list(_HITS)


def _titles(aids):
    from britannica.db.session import SessionLocal
    from britannica.db.models import Article
    s = SessionLocal()
    out = {a.id: a.title for a in s.query(Article.id, Article.title).filter(Article.id.in_(aids))}
    s.close()
    return out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "scan"
    refresh = "--refresh" in sys.argv
    t0 = time.time()
    if mode == "ids":
        if not LEAKERS.exists():
            print("no saved leakers — run `scan` first"); return
        ids = set(json.loads(LEAKERS.read_text()))
        corpus = [r for r in load_corpus() if r[0] in ids]
    else:
        corpus = list(load_corpus(contains="{{ts", refresh=refresh))
    with Pool(max(1, cpu_count() - 1), initializer=_init) as pool:
        results = pool.map(_work, corpus, chunksize=8)
    ctx = Counter(); samp = {}; per_art = {}
    for aid, hits in results:
        if hits:
            per_art[aid] = len(hits)
            for k, sample in hits:
                ctx[k] += 1; samp.setdefault(k, sample)
    tot = sum(ctx.values())
    print(f"=== Ts-LEAK AUDIT ({mode}): {len(corpus)} articles scanned, "
          f"{tot} Ts leaks in {len(per_art)} articles, {time.time()-t0:.1f}s ===\n")
    for k, n in ctx.most_common():
        print(f"  {n:5d}  {k:16s}  e.g. {samp[k]!r}")
    titles = _titles(list(per_art))
    print("\n  leaking articles (count — title):")
    for aid, n in sorted(per_art.items(), key=lambda kv: -kv[1]):
        print(f"    {n:4d}  {titles.get(aid, '?')}  [id={aid}]")
    if mode == "scan":
        LEAKERS.write_text(json.dumps(sorted(per_art)))
        print(f"\n  saved {len(per_art)} leaker ids → {LEAKERS.name} (use `ids` to re-run just these)")


if __name__ == "__main__":
    main()
