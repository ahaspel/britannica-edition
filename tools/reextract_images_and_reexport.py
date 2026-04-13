"""Clear ArticleImage, re-run extract_images per volume, re-export articles.

Used when the image-extraction logic changes (e.g. segment-based
assignment, caption extraction from wikitable/span wrappers) without
needing a full boundary-detection rebuild.

Usage:
    python tools/reextract_images_and_reexport.py
"""
import sys
import time

from britannica.db.models import ArticleImage
from britannica.db.session import SessionLocal
from britannica.pipeline.stages.extract_images import extract_images_for_volume
from britannica.export.article_json import export_articles_to_json


def clear_all_images() -> int:
    session = SessionLocal()
    try:
        n = session.query(ArticleImage).delete()
        session.commit()
        return n
    finally:
        session.close()


def main() -> None:
    t0 = time.time()
    cleared = clear_all_images()
    print(f"Cleared {cleared} ArticleImage rows. [{time.time() - t0:.1f}s]")

    total_images = 0
    for vol in range(1, 29):
        n = extract_images_for_volume(vol)
        total_images += n
        print(f"  vol {vol}: extracted {n} images. "
              f"total {total_images} [{time.time() - t0:.1f}s]")

    print()
    print("Re-exporting all volumes...")
    for vol in range(1, 29):
        n = export_articles_to_json(vol, "data/derived/articles")
        print(f"  vol {vol}: exported {n} articles. [{time.time() - t0:.1f}s]")

    print(f"\nDone. Total elapsed: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
