"""Emit the kind index: ``filename -> [kinds]`` — the general form of the person
set ([[project_resolver_consolidation]] step B).

Each article's kind is read from TWO sources and reconciled:

  - the TOPIC buckets it resolves into — a Towns bucket confers ``town``, a
    Lakes bucket ``lake``, a Biographies bucket ``person`` (a field-specific
    Biographies bucket also ``chemist`` / ``mathematician`` / …), a Races/Tribes
    bucket ``ethnic``, a Birds/Mammals bucket ``nature``;
  - the article's OWN ``lead_kind`` (the first is-a noun in its opening).

``lead`` ARBITRATES a cross-category disagreement: a town wrongly filed under a
Biographies bucket (ABERDEEN — a mis-resolved index entry) keeps only ``town``,
scrubbing the pollution.  But where ``lead`` is silent (``None``) the topic
supplies the kind — the atypical-lead critic filed under a Literature bucket
keeps ``person``.  So the two are complementary: topic covers unparseable leads,
lead scrubs mis-resolutions.

Trustworthy only after the A1/A2 topic-resolver fixes.  Consumed by the xref
collision-picker (step C).  Sole writer of ``kind_index.json``.
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, "src")
from britannica.xrefs.disambiguation import PERSON_KINDS, body_opening, lead_kind

ART = Path("data/derived/articles")
TOC = Path("data/derived/classified_toc.json")
OUT = Path("data/derived/kind_index.json")

# leaf-name -> place kind; category-word -> person field (matching the resolver's
# wanted_kinds vocabulary).
_GEO = {"divisions": "division", "division": "division", "cantons": "division",
        "states": "division", "provinces": "division", "departments": "division",
        "counties": "division", "governments": "division",
        "towns": "town", "town": "town", "cities": "town",
        "lakes": "lake", "rivers": "river", "mountains": "mountain",
        "islands": "island"}
_CAT_FIELD = {"chemistry": "chemist", "mathematics": "mathematician",
              "music": "musician", "physics": "physicist", "astronomy": "astronomer",
              "geology": "geologist", "philosophy": "philosopher",
              "painting": "painter", "sculpture": "sculptor", "medical": "physician",
              "stage": "actor", "dancing": "actor"}
_ETHNIC = re.compile(r"\b(races?|tribes?|peoples?)\b", re.I)
_NATURE = re.compile(r"\b(birds?|mammals?|fishes?|insects?|plants?|reptiles?|"
                     r"molluscs?|batrachians?|trees?|flowers?)\b", re.I)

# kind -> broad category, for lead arbitration.
_CATEGORY: dict[str, str] = {"nature": "nature", "ethnic": "ethnic"}
for _k in PERSON_KINDS | {"person"}:
    _CATEGORY[_k] = "person"
for _k in ("division", "town", "city", "lake", "river", "mountain", "island"):
    _CATEGORY[_k] = "place"


def _bucket_kinds(path: list[str], comma_frac: float) -> set[str]:
    """The kind(s) a bucket confers on its articles."""
    leaf = path[-1].lower() if path else ""
    joined = " ".join(path).lower()
    kinds: set[str] = set()
    if _ETHNIC.search(leaf):
        kinds.add("ethnic")
    if _NATURE.search(leaf):
        kinds.add("nature")
    for w, k in _GEO.items():
        if re.search(r"\b" + w + r"\b", leaf):
            kinds.add(k)
    # A person bucket: named 'Biographies' (path-wide, catches nested mononym
    # bios) OR overwhelmingly comma-filed (country-literature) -- the same
    # two-signal test as the person set.
    if "biograph" in joined or comma_frac >= 0.70:
        for w, f in _CAT_FIELD.items():
            if re.search(r"\b" + w + r"\b", joined):
                kinds.add(f)
        kinds.add("person")
    return kinds


def main() -> None:
    idx = [e for e in json.loads((ART / "index.json").read_text(encoding="utf-8"))
           if e.get("article_type") == "article"]
    title_by_fn = {e["filename"]: e.get("title", "") for e in idx}
    lead_of = {e["filename"]: lead_kind(body_opening(e.get("body_start", "")))
               for e in idx}
    toc = json.loads(TOC.read_text(encoding="utf-8"))

    topic_kinds: dict[str, set[str]] = defaultdict(set)

    def walk(node, path):
        cur = path + [node.get("name", "")]
        fns = [a["filename"] for a in node.get("articles", []) if a.get("filename")]
        if fns:
            cf = sum(1 for fn in fns if "," in title_by_fn.get(fn, "")) / len(fns)
            bk = _bucket_kinds(cur, cf)
            for fn in fns:
                topic_kinds[fn] |= bk
        for ch in node.get("children", []):
            walk(ch, cur)

    for cat in toc["categories"]:
        walk({"name": cat["name"], "articles": cat.get("articles", []),
              "children": cat.get("subsections", [])}, [])

    kind_index: dict[str, list[str]] = {}
    for e in idx:
        fn = e["filename"]
        lead = lead_of.get(fn)
        kinds = set(topic_kinds.get(fn, ()))
        if lead:
            lcat = _CATEGORY.get(lead)
            if lcat:                    # lead arbitrates: drop cross-category topic kinds
                kinds = {k for k in kinds if _CATEGORY.get(k) in (None, lcat)}
            kinds.add(lead)
        if kinds:
            kind_index[fn] = sorted(kinds)

    OUT.write_text(json.dumps(kind_index, ensure_ascii=False), encoding="utf-8")
    by_cat: dict[str, int] = defaultdict(int)
    for ks in kind_index.values():
        for c in {_CATEGORY.get(k, "specific") for k in ks}:
            by_cat[c] += 1
    print(f"Wrote {OUT}")
    print(f"  {len(kind_index)} / {len(idx)} articles carry a kind "
          f"({100 * len(kind_index) // len(idx)}%)")
    print(f"  by category: {dict(sorted(by_cat.items(), key=lambda x: -x[1]))}")


if __name__ == "__main__":
    main()
