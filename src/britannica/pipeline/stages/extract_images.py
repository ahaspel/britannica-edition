import json
import re
import hashlib
from pathlib import Path
from urllib.parse import quote

from britannica.db.models import Article, ArticleImage, ArticleSegment, SourcePage
from britannica.db.session import SessionLocal


_IMAGE_PATTERN = re.compile(
    r"\[\[(?:File|Image):([^\]]+)\]\]",
    re.IGNORECASE,
)

_RAW_DIRS = [
    Path("data/raw/wikisource"),
]


def _commons_url(filename: str) -> str:
    """Build the Wikimedia Commons file URL from a filename."""
    # Commons uses MD5-based directory structure
    name = filename.replace(" ", "_")
    md5 = hashlib.md5(name.encode()).hexdigest()
    encoded = quote(name)
    return (
        f"https://upload.wikimedia.org/wikipedia/commons/{md5[0]}/{md5[:2]}/{encoded}"
    )


def _parse_image_ref(ref: str) -> dict:
    """Parse a [[File:...]] reference into filename, caption, etc."""
    parts = [p.strip() for p in ref.split("|")]
    filename = parts[0]

    # Last part is caption if it's not a size/position keyword
    caption = None
    keywords = {"center", "left", "right", "thumb", "thumbnail", "frameless",
                "frame", "border", "upright"}
    for part in reversed(parts[1:]):
        lower = part.lower()
        if lower in keywords:
            continue
        if re.match(r"^\d+px$", lower):
            continue
        if re.match(r"^upright=", lower):
            continue
        if part:
            caption = part
            break

    return {
        "filename": filename,
        "caption": caption,
        "commons_url": _commons_url(filename),
    }


def _load_raw_wikitext(volume: int, page_number: int) -> str | None:
    """Load the original wikitext from the cached JSON file on disk."""
    padded = f"vol{volume:02d}-page{page_number:04d}.json"
    for raw_dir in _RAW_DIRS:
        for subdir in sorted(raw_dir.iterdir()) if raw_dir.exists() else []:
            if not subdir.is_dir():
                continue
            path = subdir / padded
            if path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))
                return data.get("raw_text", "")
    return None


def extract_images_for_volume(volume: int) -> int:
    session = SessionLocal()

    try:
        pages = (
            session.query(SourcePage)
            .filter(SourcePage.volume == volume)
            .order_by(SourcePage.page_number)
            .all()
        )

        # Build a map: source_page_id -> article_id
        page_articles: dict[int, int] = {}
        segments = (
            session.query(ArticleSegment)
            .join(Article, ArticleSegment.article_id == Article.id)
            .filter(Article.volume == volume)
            .order_by(ArticleSegment.source_page_id, ArticleSegment.sequence_in_article)
            .all()
        )
        for seg in segments:
            page_articles[seg.source_page_id] = seg.article_id

        created = 0

        for page in pages:
            article_id = page_articles.get(page.id)
            if article_id is None:
                continue

            raw = _load_raw_wikitext(volume, page.page_number)
            if not raw:
                continue

            matches = list(_IMAGE_PATTERN.finditer(raw))

            for i, match in enumerate(matches):
                parsed = _parse_image_ref(match.group(1))

                existing = (
                    session.query(ArticleImage)
                    .filter(
                        ArticleImage.article_id == article_id,
                        ArticleImage.source_page_id == page.id,
                        ArticleImage.filename == parsed["filename"],
                    )
                    .first()
                )

                if existing:
                    continue

                session.add(
                    ArticleImage(
                        article_id=article_id,
                        source_page_id=page.id,
                        sequence_in_article=i + 1,
                        filename=parsed["filename"],
                        caption=parsed["caption"],
                        commons_url=parsed["commons_url"],
                    )
                )
                created += 1

        session.commit()
        return created

    finally:
        session.close()
