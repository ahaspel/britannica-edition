"""Resolved-link census: how many links actually LAND, local corpus vs production.

A marker diff cannot see this.  TARAFA's marker changed in a way that read as
correct in isolation, and the link then failed to resolve and died — resolution
is the one thing that decides whether a link works.  The 2026-08-14 regression
(~370 links lost to a display-slot grammar fork in the extractor) was invisible
to every marker-level measurement and obvious to this one.

Production is the "before".  The comparison is NET: it includes intended gains
(cross-references that never resolved, targets recovered by the typography
fold) as well as losses — so the gate is "resolved links must not go DOWN",
not "nothing may change".

    uv run python tools/diagnostics/link_census.py 250          # report
    uv run python tools/diagnostics/link_census.py 250 --gate   # exit 1 on net loss

`--gate` runs beside the Phase 7.3 mangled-marker gate: mangled markers must be
zero AND resolved links must not go down.  It needs production reachable; a
sample where most fetches fail is a FAILED gate, not a passed one.
"""
import io
import json
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ART = Path("data/derived/articles")
LIVE = "https://britannica11.org/data/articles/{}.json"
# RESOLVED links only — an `/article/…` href is a reference that bound to a
# corpus article.  `class="article-link"` alone also matches the renderer's
# `/search.html?q=` fallback for an UNRESOLVED «LN» that survived into a baked
# body: production's corpus carries those (its bake left unresolved markers in
# place), while the current bake never does (Wikisource link or plain text).
# Counting them scored a deliberate fallback-policy difference as "lost links"
# (2026-08-15: the -4 that failed the first gate run were three citations that
# became BETTER links — Wikisource, the cited book itself — and one honest
# strip).  Resolution is the thing this census exists to measure.
ANCHOR = re.compile(r'<a href="/article/[^"]*" class="article-link"')


def local_count(stem):
    try:
        d = json.loads((ART / f"{stem}.json").read_text(encoding="utf-8"))
    except Exception:
        return None
    return len(ANCHOR.findall(d.get("rendered_html") or ""))


def live_count(stem):
    try:
        req = urllib.request.Request(
            LIVE.format(stem), headers={"User-Agent": "britannica11-census/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read().decode("utf-8"))
        return len(ANCHOR.findall(d.get("rendered_html") or ""))
    except Exception:
        return None


def main():
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding="utf-8", errors="replace")
    args = [a for a in sys.argv[1:] if a != "--gate"]
    gate = "--gate" in sys.argv[1:]
    n = int(args[0]) if args else 250
    stems = sorted(p.stem for p in ART.glob("*.json")
                   if p.stem[:2].isdigit())
    print(f"  local articles: {len(stems)}")

    # Every k-th, so the sample spans all volumes and is reproducible.
    step = max(1, len(stems) // n)
    sample = stems[::step][:n]

    with ThreadPoolExecutor(max_workers=12) as ex:
        live = list(ex.map(live_count, sample))
    local = [local_count(s) for s in sample]

    pairs = [(s, o, w) for s, o, w in zip(sample, live, local)
             if o is not None and w is not None]
    lost = [(s, o, w) for s, o, w in pairs if w < o]
    gained = [(s, o, w) for s, o, w in pairs if w > o]
    to = sum(o for _s, o, _w in pairs)
    tn = sum(w for _s, _o, w in pairs)
    print(f"  sampled: {len(pairs)} articles  (fetch failures "
          f"{len(sample) - len(pairs)})")
    print(f"  resolved links  PRODUCTION: {to}")
    print(f"  resolved links  LOCAL     : {tn}   ({tn - to:+d}, "
          f"{100.0 * (tn - to) / max(1, to):+.1f}%)")
    print(f"  articles LOSING links : {len(lost)}  "
          f"({100.0 * len(lost) / max(1, len(pairs)):.1f}% of sample)")
    print(f"  articles GAINING links: {len(gained)}")
    print(f"  net links lost in the losers: "
          f"{sum(o - w for _s, o, w in lost)}\n")
    for s, o, w in sorted(lost, key=lambda r: r[1] - r[2], reverse=True)[:15]:
        try:
            t = json.loads((ART / f"{s}.json").read_text(encoding="utf-8")).get("title")
        except Exception:
            t = "?"
        print(f"    -{o - w:<3} {o:>3} -> {w:<3}  {t}  [{s}]")

    if gate:
        if len(pairs) < max(50, len(sample) // 2):
            print("\n  GATE FAILED: too few comparable articles "
                  f"({len(pairs)}/{len(sample)}) — production unreachable?")
            sys.exit(1)
        if tn < to:
            print(f"\n  GATE FAILED: the corpus resolves FEWER links than "
                  f"production ({tn} < {to}).  A link that stops resolving "
                  f"died silently — find the reader that went blind.")
            sys.exit(1)
        print(f"\n  GATE PASSED: resolved links {to} -> {tn} (net {tn - to:+d}).")


if __name__ == "__main__":
    main()
