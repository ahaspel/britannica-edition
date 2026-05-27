"""How many IMG markers does `_patch_img` ACTUALLY mutate?

Models the real production sweeper: an IMG marker without an inline
caption AND whose filename has a stored caption in ``article_images``
AND the stored caption survives `_sanitize_caption` (which already
filters MediaWiki `x?\\d+px` size params to empty) AND `clean_caption`
(which strips wrapper templates / entities / stray markup, leaving an
empty string when the cleaned result is empty).  Only a NON-EMPTY
sanitized result causes the sweeper to mutate the body — those are the
patches we'd actually lose by deleting `_patch_img`.

A workload of 0 means `_patch_img` is dead and can be deleted.

    uv run python tools/diagnostics/audit_patch_img.py [--limit N]
"""
from __future__ import annotations

import argparse
import re
import sys
import time

from britannica.captions import clean_caption
from britannica.db.models import (
    Article, ArticleImage, ArticleSegment, SourcePage)
from britannica.db.session import SessionLocal
from britannica.markers import IMG_PARTS_RE
from britannica.pipeline.stages.transform_articles import _transform_text_v2


def _sanitize_caption(cap: str) -> str:
    """Mirror of the production ``_sanitize_caption`` in
    ``export/article_json.py``.  Kept in lockstep with prod so this
    audit measures what prod actually does, not what the marker grammar
    might allow."""
    if re.fullmatch(r"\s*x?\d+px\s*", cap, re.IGNORECASE):
        return ""
    return clean_caption(cap)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--show", type=int, default=15,
                    help="Show first N patches with article + filename")
    args = ap.parse_args()

    session = SessionLocal()
    try:
        q = (session.query(Article)
             .filter(Article.article_type != "plate")
             .order_by(Article.id))
        if args.limit:
            q = q.limit(args.limit)
        arts = q.all()
        sys.stdout.buffer.write(
            f"Auditing {len(arts)} articles...\n".encode("utf-8"))

        total_imgs = 0
        no_caption_imgs = 0
        # Two distinct workloads (per [[audit-code-discipline]] —
        # "what would the sweeper try" vs "what does it actually do"):
        # `would_attempt` = sweeper finds a DB caption candidate, calls
        #    `_sanitize_caption` on it
        # `would_mutate`  = `_sanitize_caption` returned non-empty, so
        #    the IMG marker actually gets the caption written in
        # Only `would_mutate` is what's lost if `_patch_img` is deleted.
        would_attempt: list[tuple[str, str, str, str]] = []  # +sanitized
        would_mutate: list[tuple[str, str, str, str]] = []
        t0 = time.time()
        for i, art in enumerate(arts):
            if i % 2000 == 0 and i > 0:
                sys.stdout.buffer.write(
                    f"  ...{i}/{len(arts)} ({time.time()-t0:.0f}s, "
                    f"mutate={len(would_mutate)}, "
                    f"attempt={len(would_attempt)})\n".encode("utf-8"))
                sys.stdout.flush()

            segs = (session.query(ArticleSegment, SourcePage.page_number)
                    .join(SourcePage,
                          ArticleSegment.source_page_id == SourcePage.id)
                    .filter(ArticleSegment.article_id == art.id)
                    .order_by(ArticleSegment.sequence_in_article).all())
            if not segs:
                continue
            raw = "\n".join(
                f"\x01PAGE:{pn}\x01{(seg.segment_text or '')}"
                for seg, pn in segs)
            raw = re.sub(
                r"(\w)-\n(\x01PAGE:\d+\x01)(\w)", r"\1\2\3", raw)
            try:
                body = _transform_text_v2(raw, art.volume, segs[0][1])
            except Exception:
                continue

            # Gather IMG markers + their captions in this body.
            imgs_in_body = []
            for m in IMG_PARTS_RE.finditer(body):
                fn = m.group(1).strip()
                cap = m.group(3)
                total_imgs += 1
                if not cap:
                    no_caption_imgs += 1
                    imgs_in_body.append(fn)

            if not imgs_in_body:
                continue

            # Lookup DB captions; `_patch_img` would fire iff IMG has no
            # cap AND DB has a caption.
            db_caps = {
                img.filename: img.caption
                for img in session.query(ArticleImage).filter(
                    ArticleImage.article_id == art.id).all()
                if img.caption
            }
            for fn in imgs_in_body:
                if fn in db_caps:
                    raw_cap = db_caps[fn]
                    sanitized = _sanitize_caption(raw_cap)
                    would_attempt.append((art.title, fn, raw_cap, sanitized))
                    if sanitized:
                        would_mutate.append(
                            (art.title, fn, raw_cap, sanitized))

        sys.stdout.buffer.write(
            f"\nDone ({time.time()-t0:.0f}s).\n".encode("utf-8"))
        sys.stdout.buffer.write(
            f"\nTotal IMG markers:         {total_imgs:>6d}\n"
            f"No inline caption:         {no_caption_imgs:>6d}\n"
            f"Would-attempt (DB hit):    {len(would_attempt):>6d}\n"
            f"Would-MUTATE (real load):  {len(would_mutate):>6d}\n"
            .encode("utf-8"))
        sys.stdout.buffer.write(
            f"\nFirst {args.show} mutating patches "
            "(real captions the sweeper actually writes):\n"
            .encode("utf-8"))
        for title, fn, raw_cap, sanitized in would_mutate[:args.show]:
            sys.stdout.buffer.write(
                f"  [{title}] {fn[:50]}\n"
                f"    raw : {raw_cap[:80]!r}\n"
                f"    sani: {sanitized[:80]!r}\n"
                .encode("utf-8"))
        sys.stdout.flush()
        return 0 if not would_mutate else 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
