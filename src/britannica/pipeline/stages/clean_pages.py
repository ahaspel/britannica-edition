from britannica.cleaners.headers_footers import strip_headers
from britannica.cleaners.hyphenation import fix_hyphenation
from britannica.cleaners.reflow import reflow_paragraphs
from britannica.cleaners.unicode import normalize_unicode
from britannica.cleaners.whitespace import normalize_whitespace
from britannica.db.models.source_page import SourcePage
from britannica.db.session import SessionLocal


def clean_pages(volume: int) -> int:
    session = SessionLocal()
    try:
        pages = session.query(SourcePage).filter(SourcePage.volume == volume).all()

        for page in pages:
            text = page.raw_text
            text = normalize_unicode(text)
            text, _removed_headers = strip_headers(text)
            text, _hyphen_changes = fix_hyphenation(text)
            text = reflow_paragraphs(text)
            text = normalize_whitespace(text)
            page.cleaned_text = text

        session.commit()
        return len(pages)
    finally:
        session.close()