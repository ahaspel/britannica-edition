#!/usr/bin/env python3
"""Homonym-family link audit — rebuild the frame from the corpus, print adjudication cards.

    python tools/diagnostics/homonym_family_audit.py frame
    python tools/diagnostics/homonym_family_audit.py cards --n 30 --seed 7
    python tools/diagnostics/homonym_family_audit.py qualifiers

A FAMILY is a set of >=2 plain articles sharing one title (COLOPHON the Ionian city
and COLOPHON the printer's device).  A FAMILY LINK is any resolved xref whose target
lands in a family — i.e. a link the resolver had to *choose*, so a wrong choice sends
the reader to a different subject under the same name.

THIS TOOL CONVERTS NOTHING.  It reads only what the pipeline already produced:
  * the `«LN»` node's own fields, read off the node (target text | display text);
  * `body_start` from index.json — the export's identifying-clause field;
  * `rendered_html` — the production render — shown VERBATIM around the anchor.
No marker→text sweep of any kind lives here.  An audit that flattens is an audit
that silently drops (footnotes, tables, math) and then reports the gap as evidence;
two such drops corrupted this tool's first draft.  [[feedback_never_read_flat]]
[[feedback_flatteners_drop_content]] [[feedback_audit_code_discipline]]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.stdout.reconfigure(encoding="utf-8")
from britannica.markers import _LINK_RE  # the ONE link-node pattern  # noqa: E402

ART = ROOT / "data" / "derived" / "articles"
FRAME = ROOT / "data" / "derived" / "quality_reports" / "homonym_frame.json"
SURVEY = ROOT / "family_disagreements_survey.json"
WINDOW = 300


def _stem(filename: str) -> str:
    """Xref targets are stored as `{stable_id}.json`; the stem IS the URL id."""
    return filename[:-5] if filename.endswith(".json") else filename


def _link_fields(inner: str) -> tuple[str, str]:
    """A baked link node's payload is `target.json|target text|display text`
    (the display collapses to the target text when the source gave only one).
    Read the node's own slots — never re-derive them from the article text."""
    parts = inner.split("|")
    if len(parts) >= 3:
        return parts[1], parts[-1]
    if len(parts) == 2:
        return parts[1], parts[1]
    return "", ""


def build_frame() -> dict:
    index = {r["stable_id"]: r for r in
             json.loads((ART / "index.json").read_text(encoding="utf-8"))}
    files = [f for f in glob.glob(str(ART / "*.json"))
             if os.path.basename(f) not in ("index.json", "contributors.json")]
    arts: dict[str, dict] = {}
    links: list[dict] = []
    for f in files:
        d = json.loads(Path(f).read_text(encoding="utf-8"))
        stem = d["stable_id"]
        idx = index.get(stem, {})
        arts[stem] = {
            "title": d.get("title") or "",
            "type": d.get("article_type") or "",
            "vol": d.get("volume"),
            "page": idx.get("page_start", d.get("page_start")),
            "words": d.get("word_count") or 0,
            "lead": idx.get("body_start", ""),          # produced field, not a flatten
        }
        # The BAKED body is the authority on what actually links where: xrefs carries
        # the pre-bake surface, which does not occur in the body at all.
        for m in _LINK_RE.finditer(d.get("body") or ""):
            inner = m.group(1)
            head = inner.split("|", 1)[0]
            if not head.endswith(".json"):
                continue                                 # unresolved — no target
            target, display = _link_fields(inner)
            links.append({"src": stem, "dst": _stem(head),
                          "target_text": target, "display": display})

    by_title: dict[str, list[str]] = defaultdict(list)
    for stem, a in arts.items():
        if a["type"] == "article" and a["title"]:
            by_title[a["title"]].append(stem)
    families = {t: sorted(ss) for t, ss in by_title.items() if len(ss) > 1}
    in_family = {s: t for t, ss in families.items() for s in ss}

    fam_links = [ln for ln in links if ln["dst"] in in_family]
    for ln in fam_links:
        ln["family"] = in_family[ln["dst"]]
    return {"articles": arts, "families": families, "family_links": fam_links,
            "counts": {"articles": len(arts), "baked_links": len(links),
                       "families": len(families), "family_members": len(in_family),
                       "family_links": len(fam_links)}}


def load_frame() -> dict:
    if not FRAME.exists():
        sys.exit(f"no frame at {FRAME} — run `frame` first")
    return json.loads(FRAME.read_text(encoding="utf-8"))


def _rendered_window(stem: str, dst: str) -> str:
    """The PRODUCTION render around the anchor, verbatim — tags and all.  Showing
    what the reader is served costs some noise and removes nothing; stripping the
    tags to 'clean it up' would be the same flatten this tool refuses to do."""
    html = json.loads((ART / f"{stem}.json").read_text(encoding="utf-8")).get("rendered_html", "")
    i = html.find(f'href="/article/{dst}"')
    if i < 0:
        return "!! ANCHOR NOT FOUND IN rendered_html !!"
    a = html.rfind("<a ", 0, i)
    start, end = max(0, (a if a >= 0 else i) - WINDOW), i + WINDOW
    return ("…" if start else "") + html[start:end] + "…"


def print_card(n: int, ln: dict, frame: dict, oracle: str | None) -> None:
    arts, fams = frame["articles"], frame["families"]
    src = arts.get(ln["src"], {})
    fam = fams.get(ln["family"], [])
    print(f"\n{'='*100}\n#{n}  FAMILY: {ln['family']}   ({len(fam)} members)")
    print(f"SOURCE   {ln['src']}  {src.get('title','?')}  "
          f"[vol {src.get('vol')} p.{src.get('page')}, {src.get('words')} words]")
    print(f"REFERENCE  target={ln['target_text']!r}   display={ln['display']!r}")
    print(f"RENDERED   {_rendered_window(ln['src'], ln['dst'])}")
    print("CANDIDATES")
    for s in fam:
        a = arts.get(s, {})
        mark = [m for m, c in (("BAKED", s == ln["dst"]), ("ORACLE", oracle and s == oracle),
                               ("=SOURCE", s == ln["src"])) if c]
        tag = ("  <<< " + "/".join(mark)) if mark else ""
        print(f"  {s}  {a.get('title','')}  vol {a.get('vol')} p.{a.get('page')}  "
              f"{a.get('words')}w{tag}")
        print(f"      {a.get('lead','')}")


_PAREN = re.compile(r"\(([^)]*)\)\s*$")


def qualifiers(frame: dict) -> None:
    """How many family links carry a parenthetical qualifier the SOURCE supplied —
    `Down (hill)`, `Durham (city)` — and how often the bind ignores it?  A qualifier
    that names a candidate is a stated source attribute, not a judgment call."""
    arts, fams = frame["articles"], frame["families"]
    tally = Counter()
    ignored = []
    for ln in frame["family_links"]:
        m = _PAREN.search(ln["target_text"])
        if not m:
            tally["no qualifier"] += 1
            continue
        tally["qualified"] += 1
        qual = m.group(1).strip().lower()
        if not qual:
            continue
        hits = [s for s in fams[ln["family"]]
                if qual in (arts[s].get("lead", "") + " " + arts[s].get("title", "")).lower()]
        if not hits:
            tally["qualifier matched nothing"] += 1
        elif ln["dst"] in hits:
            tally["qualifier agrees with bind"] += 1
        else:
            tally["QUALIFIER CONTRADICTS BIND"] += 1
            ignored.append((ln["family"], ln["target_text"], ln["src"], ln["dst"], hits))
    for k, v in tally.most_common():
        print(f"{v:6d}  {k}")
    print(f"\nfirst 25 contradictions ({len(ignored)} total):")
    for fam_t, tgt, src, dst, hits in ignored[:25]:
        print(f"  {fam_t:22s} {tgt!r:34s} in {src} -> {dst}   qualifier points at {hits}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["frame", "cards", "qualifiers"])
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--disagreements", action="store_true")
    ap.add_argument("--exclude-self", action="store_true")
    ap.add_argument("--stems", default="")
    args = ap.parse_args()

    if args.cmd == "frame":
        fr = build_frame()
        FRAME.parent.mkdir(parents=True, exist_ok=True)
        FRAME.write_text(json.dumps(fr), encoding="utf-8")
        print(json.dumps(fr["counts"], indent=2))
        return

    frame = load_frame()
    if args.cmd == "qualifiers":
        qualifiers(frame)
        return

    rows = frame["family_links"]
    oracle: dict[tuple[str, str], str] = {}
    if SURVEY.exists():
        for _margin, s, baked, pick, _t in json.loads(SURVEY.read_text(encoding="utf-8")):
            oracle[(s, baked)] = pick

    if args.stems:
        want = set(args.stems.split(","))
        sel = [ln for ln in rows if ln["src"] in want]
    else:
        pool = rows
        if args.disagreements:
            pool = [ln for ln in rows if (ln["src"], ln["dst"]) in oracle]
        if args.exclude_self:
            pool = [ln for ln in pool if oracle.get((ln["src"], ln["dst"])) != ln["src"]]
        pool.sort(key=lambda ln: (ln["src"], ln["dst"], ln["display"]))
        sel = random.Random(args.seed).sample(pool, min(args.n, len(pool)))
        sel.sort(key=lambda ln: (ln["family"], ln["src"]))
        print(f"pool={len(pool)}  sampled={len(sel)}  seed={args.seed}")

    for i, ln in enumerate(sel, 1):
        print_card(i, ln, frame, oracle.get((ln["src"], ln["dst"])))


if __name__ == "__main__":
    main()
