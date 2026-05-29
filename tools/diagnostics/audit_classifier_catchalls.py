"""Audit the classifier-side catch-all labels — LAYOUT_WRAPPER and
DATA_TABLE — to measure the damage:

  1. LAYOUT_WRAPPER occupants — characterize each by structural
     features (verse / single-figure / data-leak / un-pairable multi-
     image figure) to find the misclassifications.
  2. `_process_table` exit paths — instrument each return point to
     count how many DATA_TABLE elements take a non-table return
     (image+caption bundle, plate-image-layout, structural formula,
     tiny inline emit, empty fall-through).  Each non-table return is
     a classifier under-inclusion.

Both are the classifier-side equivalent of the `_strip_templates`
producer-side audit: count the leaks, group by name/shape, surface
the upstream gap each leak names.
"""
from __future__ import annotations

import io
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                              errors="replace")

from sqlalchemy import or_  # noqa: E402
from britannica.db.session import SessionLocal  # noqa: E402
from britannica.db.models import Article, ArticleSegment  # noqa: E402
from britannica.pipeline.stages.elements._classifier import (  # noqa: E402
    classify_article,
)
from britannica.pipeline.stages.elements._tables import (  # noqa: E402
    _chem_row_is_reaction,
    _table_grid,
)
from britannica.pipeline.stages.elements import _tables as _tables_mod  # noqa: E402


# ── Layer A: LAYOUT_WRAPPER occupant characterisation ──────────────────

def walk(t):
    for ce in t.values():
        yield ce
        if ce.inner_registry:
            yield from walk(ce.inner_registry)


def child_counts(ce):
    c = Counter()
    if ce.inner_registry:
        for x in ce.inner_registry.values():
            c[x.label] += 1
    return c


def layout_wrapper_shape(ce):
    """Characterise a LAYOUT_WRAPPER occupant by structural features.

    The PRINCIPLED role per [[project_layout_wrapper_definition]] is
    un-pairable multi-image figures — when image↔caption mapping is
    not 1:1.  Anything else is a misclassification.
    """
    cc = child_counts(ce)
    n_images = cc.get("IMAGE", 0)
    n_poems = cc.get("POEM", 0)
    n_math = cc.get("MATH", 0)
    n_figs = sum(v for k, v in cc.items() if "FIGURE" in k or "PLATE" in k)
    inner = ce.inner_text or ""

    # Verse leak — poem child or <poem> tag in source.
    if n_poems >= 1 or "<poem>" in inner.lower():
        return "verse-leak (POEM child)"
    # Single figure — exactly one image child, principled role calls
    # for >= 2 images.
    if n_images == 1:
        return "single-figure-leak (1 IMAGE)"
    # Data leak — no images, has data-table signals.
    if n_images == 0 and n_figs == 0:
        grid = _table_grid(inner)
        if any(_chem_row_is_reaction(" ".join(r)) for r in grid):
            return "chem-leak (reaction)"
        if n_math >= 2 or "<math" in inner.lower():
            return "math-leak"
        if grid and all(len([c for c in r if c.strip()]) <= 1
                        for r in grid):
            return "single-column-leak"
        return "data-leak (no images)"
    # Multi-image — principled role.
    if n_images >= 2:
        return f"PRINCIPLED (>=2 IMAGES: {n_images})"
    # Figure-group case
    if n_figs >= 2:
        return f"PRINCIPLED (>=2 FIGURE children: {n_figs})"
    return "uncategorised"


# ── Layer B: _process_table exit-path tracking ─────────────────────────

_exit_paths: Counter[str] = Counter()
_exit_examples: dict[str, list[tuple[int, int, str]]] = defaultdict(list)
_current_article: tuple[int, int, str] | None = None


def _instrument_process_table():
    """Replace `_process_table` with an instrumented wrapper that
    records which of its return points fired for each invocation."""
    orig = _tables_mod._process_table

    def _wrapped(raw, inner, text_transform, inner_registry=None):
        # Pre-checks before the canonical path — capture which one
        # fires by re-implementing the gate logic in inspection mode.
        import re as _re

        # 1. Tiny inline table unwrap.
        _BLOCK_TYPES = {"POEM", "TABLE", "HTML_TABLE"}
        has_block_child = inner_registry and any(
            ct in _BLOCK_TYPES for ct, _ in inner_registry.elements.values())
        if "|-" not in inner and not has_block_child:
            from britannica.pipeline.stages.elements._tables import (
                _extract_table_cells,
            )
            all_cells = _extract_table_cells(inner, text_transform)
            content_cells = [c for c in all_cells if c.strip()]
            if (len(content_cells) <= 4
                    and sum(len(c) for c in all_cells) < 120):
                _record("1-tiny-inline-emit")
                return orig(raw, inner, text_transform, inner_registry)

        # 2. Image + caption bundle.
        if "|-" in inner and inner_registry is not None:
            from britannica.pipeline.stages.elements._registry import (
                _PH,
            )
            from britannica.pipeline.stages.elements._tables import (
                IMAGE_LABELS, _extract_table_cells,
            )
            ph_re = _re.compile(_re.escape(_PH) + r"ELEM:\d+"
                                + _re.escape(_PH))
            rows_filtered = [r for r in _re.split(r"\|-[^\n]*", inner)
                             if r.strip()]
            if len(rows_filtered) >= 2:
                row1_cells = _extract_table_cells(rows_filtered[0],
                                                  text_transform)
                if (len(row1_cells) == 1
                        and ph_re.fullmatch(row1_cells[0].strip())):
                    ph_id = row1_cells[0].strip()
                    if inner_registry.labels.get(ph_id) in IMAGE_LABELS:
                        eraw = inner_registry.elements[ph_id][1]
                        fname_m = _re.match(
                            r"\[\[(?:File|Image):([^\]|]+)",
                            eraw, _re.IGNORECASE)
                        if fname_m:
                            row2_cells = _extract_table_cells(
                                rows_filtered[1], text_transform)
                            caption = " ".join(
                                c.strip() for c in row2_cells
                                if c.strip())
                            if caption or True:
                                _record("2-image-caption-bundle")
                                return orig(raw, inner, text_transform,
                                            inner_registry)

        # 3. Plate-image-layout.
        from britannica.pipeline.stages.elements._registry import _PH
        if _PH in inner:
            placeholders = _re.findall(
                _re.escape(_PH) + r"[^" + _re.escape(_PH) + r"]+"
                + _re.escape(_PH), inner)
            non_ph = _re.sub(_re.escape(_PH) + r"[^"
                             + _re.escape(_PH) + r"]+"
                             + _re.escape(_PH), "", inner)
            non_ph = _re.sub(r"[-|{}\n]", " ", non_ph)
            non_ph = _re.sub(
                r"\b(?:align|valign|colspan|rowspan|style|width|"
                r"cellpadding|cellspacing|center|right|left|top|"
                r"bottom)\b", "", non_ph, flags=_re.IGNORECASE)
            non_ph = _re.sub(r'[="]+', "", non_ph)
            non_ph = _re.sub(r"\s+", " ", non_ph).strip()
            if (len(placeholders) >= 2
                    and len(non_ph) < len(placeholders) * 20):
                _record("3-plate-image-layout")
                return orig(raw, inner, text_transform, inner_registry)

        # 4. Structural formula.
        from britannica.pipeline.stages.elements._tables import (
            _is_structural_formula,
        )
        if _is_structural_formula(inner):
            _record("4-structural-formula")
            return orig(raw, inner, text_transform, inner_registry)

        # 5. Main path — genuine table.
        _record("5-canonical-table")
        return orig(raw, inner, text_transform, inner_registry)

    _tables_mod._process_table = _wrapped


def _record(path: str) -> None:
    _exit_paths[path] += 1
    if _current_article is not None and len(_exit_examples[path]) < 6:
        _exit_examples[path].append(_current_article)


# ── Driver ─────────────────────────────────────────────────────────────

def main() -> int:
    global _current_article
    _instrument_process_table()
    s = SessionLocal()
    arts = (s.query(Article)
            .join(ArticleSegment, ArticleSegment.article_id == Article.id)
            .filter(or_(
                ArticleSegment.segment_text.like("%{|%"),
                ArticleSegment.segment_text.like("%<table%")))
            .distinct().order_by(Article.volume, Article.page_start).all())
    lw_shapes: Counter[str] = Counter()
    lw_examples: dict[str, list[tuple[int, int, str]]] = defaultdict(list)
    cur = None
    for a in arts:
        if a.article_type == "plate":
            continue
        if a.volume != cur:
            cur = a.volume
            print(f"  vol {cur}", file=sys.stderr, flush=True)
        _current_article = (a.volume, a.page_start, a.title[:30])
        segs = (s.query(ArticleSegment).filter_by(article_id=a.id)
                .order_by(ArticleSegment.sequence_in_article).all())
        body = "\n\n".join(x.segment_text or "" for x in segs)
        try:
            _ph, tree = classify_article(body)
        except Exception:
            continue
        for ce in walk(tree):
            if ce.label == "LAYOUT_WRAPPER":
                sh = layout_wrapper_shape(ce)
                lw_shapes[sh] += 1
                if len(lw_examples[sh]) < 6:
                    lw_examples[sh].append(_current_article)
    s.close()

    print()
    print("═" * 70)
    print("LAYER A: LAYOUT_WRAPPER occupant characterisation")
    print("═" * 70)
    total_lw = sum(lw_shapes.values())
    principled = sum(v for k, v in lw_shapes.items()
                     if k.startswith("PRINCIPLED"))
    print(f"\nTotal LAYOUT_WRAPPER elements: {total_lw}")
    print(f"Principled (un-pairable multi-image): {principled} "
          f"({100 * principled // max(1, total_lw)}%)")
    print(f"Misclassifications:                   "
          f"{total_lw - principled} "
          f"({100 * (total_lw - principled) // max(1, total_lw)}%)\n")
    for sh, n in sorted(lw_shapes.items(), key=lambda x: -x[1]):
        tag = "" if sh.startswith("PRINCIPLED") else "  <-- MISCLASS"
        print(f"  {n:5}  {sh}{tag}")
        for v, p, t in lw_examples[sh][:3]:
            print(f"         {v:02d}-{p:04d} {t}")

    print()
    print("═" * 70)
    print("LAYER B: _process_table exit-path tracking")
    print("═" * 70)
    total_pt = sum(_exit_paths.values())
    canonical = _exit_paths.get("5-canonical-table", 0)
    print(f"\nTotal _process_table invocations: {total_pt}")
    print(f"Canonical table return:           {canonical} "
          f"({100 * canonical // max(1, total_pt)}%)")
    print(f"Fallback (non-table) returns:     "
          f"{total_pt - canonical} "
          f"({100 * (total_pt - canonical) // max(1, total_pt)}%)\n")
    for path, n in sorted(_exit_paths.items()):
        tag = "" if path == "5-canonical-table" else "  <-- LEAK"
        print(f"  {n:5}  {path}{tag}")
        for v, p, t in _exit_examples[path][:3]:
            print(f"         {v:02d}-{p:04d} {t}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
