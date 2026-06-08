"""Corpus-wide ``_transform_text_v2`` snapshot + diff net.

The regression instrument for the walker flip: capture the IMMEDIATE
output of ``_transform_text_v2`` (the marker-string body, BEFORE the
downstream xref / page-translation phases — same surface as
``capture_transform_snapshots.py``, but for the WHOLE corpus, not the
20 curated seeds) under a named tag, then diff two tags to find every
article whose output changed.

Every flip move is a TAGGED DIFF against a baseline tag, never a
wholesale rebaseline ([[no_wholesale_rebaseline]]).  Most moves should
be byte-identical except at the precise cases the old layer couldn't
handle — the diff makes that provable.

Snapshots live under ``data/derived/_flip_snap/<tag>/`` (gitignored):
    manifest.tsv          id \\t sha \\t bytes \\t vol \\t title
    b/<vol>/<id>.txt      the captured body (for per-article inspection)

Usage::
    uv run python tools/diagnostics/snapshot_corpus.py capture <tag> [all|<vol>]
    uv run python tools/diagnostics/snapshot_corpus.py diff <tagA> <tagB>
    uv run python tools/diagnostics/snapshot_corpus.py show <tagA> <tagB> <id>
"""
from __future__ import annotations

import hashlib
import io
import re
import sys
from collections import defaultdict
from difflib import unified_diff
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                              errors="replace")

from britannica.db.models import Article, ArticleSegment, SourcePage  # noqa: E402
from britannica.db.session import SessionLocal  # noqa: E402
from britannica.pipeline.stages.transform_articles import (  # noqa: E402
    _transform_text_v2,
)
from britannica.util.strings import section_slug  # noqa: E402

ROOT = Path("data/derived/_flip_snap")


def _build_joined_raw(segs: list[tuple[str, int]]) -> str:
    """Mirror transform_articles' faithful segment re-join: concatenate the
    segments with NO separator, reproducing the article's slice of the clean
    stream exactly.  Each segment already carries its «PAGE» marker (stamped at
    detection) and the seam was healed upstream — dry-run-must-mirror-prod."""
    return "".join(txt or "" for txt, pg in segs)


def _load_segments_by_article(s) -> dict[int, list[tuple[str, int]]]:
    """One bulk query → {article_id: [(segment_text, page_number), ...]}
    in sequence order.  Avoids 36k per-article round-trips."""
    rows = (
        s.query(
            ArticleSegment.article_id,
            ArticleSegment.sequence_in_article,
            ArticleSegment.segment_text,
            SourcePage.page_number,
        )
        .join(SourcePage, ArticleSegment.source_page_id == SourcePage.id)
        .order_by(ArticleSegment.article_id,
                  ArticleSegment.sequence_in_article)
        .all()
    )
    by_art: dict[int, list[tuple[str, int]]] = defaultdict(list)
    for art_id, _seq, text, page in rows:
        by_art[art_id].append((text, page))
    return by_art


def capture(tag: str, vol_filter: str) -> int:
    tag_dir = ROOT / tag
    body_dir = tag_dir / "b"
    body_dir.mkdir(parents=True, exist_ok=True)
    manifest = tag_dir / "manifest.tsv"

    s = SessionLocal()
    try:
        q = s.query(Article.id, Article.volume, Article.title,
                    Article.page_start, Article.section_name).filter(
            Article.article_type != "plate")
        if vol_filter != "all":
            q = q.filter(Article.volume == int(vol_filter))
        arts = q.order_by(Article.volume, Article.page_start).all()
        print(f"capturing {len(arts)} articles → {tag_dir}", flush=True)
        segs_by_art = _load_segments_by_article(s)

        out = manifest.open("w", encoding="utf-8")
        done = err = 0
        for art_id, vol, title, page_start, section_name in arts:
            segs = segs_by_art.get(art_id)
            if not segs:
                continue
            # Key on the DURABLE stable_id (vol+page_start+section_slug), NOT the
            # autoincrement PK — the PK is reassigned on every re-detect, which
            # would break any cross-rebuild diff (the whole point of the net).
            slug = section_slug(section_name) if section_name else ""
            if not slug:
                slug = section_slug(title)
            sid = f"{vol:02d}-{page_start:04d}-{slug}"
            joined = _build_joined_raw(segs)
            try:
                body = _transform_text_v2(joined, vol, segs[0][1])
            except Exception as exc:  # noqa: BLE001 — record, don't abort the net
                body = f"\x00TRANSFORM-ERROR\x00{type(exc).__name__}: {exc}"
                err += 1
            sha = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
            vdir = body_dir / str(vol)
            vdir.mkdir(exist_ok=True)
            (vdir / f"{sid}.txt").write_text(body, encoding="utf-8")
            safe_title = (title or "").replace("\t", " ").replace("\n", " ")
            out.write(f"{sid}\t{sha}\t{len(body)}\t{vol}\t{safe_title}\n")
            done += 1
            if done % 1000 == 0:
                out.flush()
                print(f"  {done}/{len(arts)} (errors={err})", flush=True)
        out.close()
        print(f"DONE: {done} captured, {err} transform-errors → {manifest}",
              flush=True)
        return 0
    finally:
        s.close()


def _load_manifest(tag: str) -> dict[str, tuple[str, int, int, str]]:
    """{stable_id: (sha, bytes, vol, title)}."""
    path = ROOT / tag / "manifest.tsv"
    if not path.exists():
        sys.exit(f"no manifest for tag {tag!r} at {path}")
    out: dict[str, tuple[str, int, int, str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        if len(parts) < 5:
            continue
        aid, sha, nbytes, vol, title = parts[0], parts[1], parts[2], parts[3], parts[4]
        out[aid] = (sha, int(nbytes), int(vol), title)
    return out


def diff(tag_a: str, tag_b: str) -> int:
    a = _load_manifest(tag_a)
    b = _load_manifest(tag_b)
    a_ids, b_ids = set(a), set(b)
    added = b_ids - a_ids
    removed = a_ids - b_ids
    changed = sorted(i for i in (a_ids & b_ids) if a[i][0] != b[i][0])

    print(f"=== diff {tag_a} → {tag_b} ===")
    print(f"  {tag_a}: {len(a)} articles   {tag_b}: {len(b)} articles")
    print(f"  changed: {len(changed)}   added: {len(added)}   "
          f"removed: {len(removed)}")
    by_vol: dict[int, int] = defaultdict(int)
    for i in changed:
        by_vol[b[i][2]] += 1
    if by_vol:
        print("  changed by volume: " +
              "  ".join(f"v{v}:{n}" for v, n in sorted(by_vol.items())))

    out_path = ROOT / f"diff_{tag_a}__{tag_b}.txt"
    with out_path.open("w", encoding="utf-8") as f:
        for i in changed:
            sha_a, ba, _v, title = a[i]
            sha_b, bb, _v2, _t = b[i]
            f.write(f"{i}\t{ba}->{bb}\tv{b[i][2]}\t{title}\n")
    print(f"  changed-id list → {out_path}")
    # Show the 25 biggest byte-swings as a quick triage view.
    if changed:
        swings = sorted(changed, key=lambda i: abs(b[i][1] - a[i][1]),
                        reverse=True)[:25]
        print("  largest byte-swings:")
        for i in swings:
            print(f"    {i:>7}  {a[i][1]:>7}->{b[i][1]:<7} "
                  f"({b[i][1]-a[i][1]:+d})  v{b[i][2]}  {b[i][3]}")
    return 0


def show(tag_a: str, tag_b: str, art_id: str) -> int:
    a = _load_manifest(tag_a)
    vol = (a.get(art_id) or _load_manifest(tag_b).get(art_id) or ("", 0, 0, ""))[2]
    pa = ROOT / tag_a / "b" / str(vol) / f"{art_id}.txt"
    pb = ROOT / tag_b / "b" / str(vol) / f"{art_id}.txt"
    if not pa.exists() or not pb.exists():
        sys.exit(f"missing body file(s): {pa} / {pb}")
    la = pa.read_text(encoding="utf-8").splitlines(keepends=True)
    lb = pb.read_text(encoding="utf-8").splitlines(keepends=True)
    sys.stdout.write("".join(unified_diff(
        la, lb, fromfile=f"{tag_a}/{art_id}", tofile=f"{tag_b}/{art_id}")))
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    if cmd == "capture":
        return capture(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "all")
    if cmd == "diff":
        return diff(sys.argv[2], sys.argv[3])
    if cmd == "show":
        return show(sys.argv[2], sys.argv[3], sys.argv[4])
    sys.exit(f"unknown command {cmd!r}")


if __name__ == "__main__":
    sys.exit(main())
