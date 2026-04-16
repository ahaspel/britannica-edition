import json
import re
import hashlib
from pathlib import Path
from urllib.parse import quote

from britannica.db.models import Article, ArticleImage, ArticleSegment, SourcePage
from britannica.db.session import SessionLocal


_IMAGE_PATTERN = re.compile(
    # Standard [[File:name|opts]] form
    r"\[\[(?:File|Image):([^\]]+)\]\]"
    # OR {{raw image|filename}} — alternate EB1911 image syntax; the
    # filename is captured bare (no caption/options).
    r"|\{\{\s*raw\s+image\s*\|([^{}|]+)\s*\}\}"
    # OR {{img float|file=...|cap=...}} / {{figure|...}} / {{FI|...}}
    # — inline float templates. Captured as group 3 (full template
    # body after the opening keyword); file= and cap= are extracted
    # downstream by _parse_img_float().
    # Supports up to 2 levels of nested {{…}} (e.g. {{EB1911|{{sc|Fig.}} 15.}}).
    r"|\{\{\s*(?:img\s+float|figure|FI)\s*\|"
    r"((?:[^{}]|\{\{(?:[^{}]|\{\{[^{}]*\}\})*\}\})*)\}\}",
    re.IGNORECASE | re.DOTALL,
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


def _parse_img_float(body: str) -> dict | None:
    """Parse an {{img float|...}} template body into filename + caption."""
    file_m = re.search(r"\|file=([^|}\n]+)", "|" + body, re.IGNORECASE)
    if not file_m:
        return None
    filename = file_m.group(1).strip()
    # cap= value may contain nested templates up to 2 levels deep:
    # cap={{EB1911 Fine Print|{{sc|Fig.}} 15.—Flanged Girder.}}
    cap_m = re.search(
        r"\|cap=((?:[^|{}]|\{\{(?:[^{}]|\{\{[^{}]*\}\})*\}\})+)",
        "|" + body, re.IGNORECASE,
    )
    caption = cap_m.group(1).strip() if cap_m else None
    return {
        "filename": filename,
        "caption": caption,
        "commons_url": _commons_url(filename),
    }


def _clean_caption_markup(text: str) -> str:
    """Strip wiki/HTML noise from an extracted caption string.

    Handles the caption-wrapper templates and tags that appear around
    WEIGHING MACHINES / SEWING MACHINES figures: {{sc|…}}, {{smaller|…}},
    {{c|…}}, <br/>, alignment attributes like `align="center"|`.
    """
    # Drop leading wikitable cell attributes: `align="..." width="..." |`
    text = re.sub(
        r'^(?:(?:align|style|width|valign|class|colspan|rowspan|id|scope)'
        r'\s*=\s*"[^"]*"\s*)+\|\s*',
        "", text,
    )
    # Strip common wrapper templates, keeping inner text. `Fs` has a
    # `|percent|text` signature — keep only the text.
    for _ in range(5):
        text = re.sub(r"\{\{\s*(?:sc|smaller|c|center|small|big|bold|italic|nowrap)\s*\|([^{}]*)\}\}",
                      r"\1", text, flags=re.IGNORECASE)
        text = re.sub(r"\{\{\s*fs\s*\|[^{}|]*\|([^{}]*)\}\}",
                      r"\1", text, flags=re.IGNORECASE)
    # Unwrap any other pipe-separated template — keep the last arg
    # (usually the display text, e.g. `{{EB1911 article link|Foo}}` → Foo).
    for _ in range(3):
        text = re.sub(r"\{\{[^{}|]+\|([^{}]*)\}\}", r"\1",
                      text, flags=re.IGNORECASE)
    # Any remaining bare template (no pipe) — drop entirely.
    text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    # Strip <br/> and remaining inline HTML tags
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    # Strip wikilinks [[X|Y]] → Y, [[X]] → X
    text = re.sub(r"\[\[[^\]|]*\|([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    # Strip stray braces, pipes, and table-row markers
    text = re.sub(r"\{\{+|\}\}+|\|\}|\{\|", "", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Drop source-attribution prefixes like "From Airy, ..." preceding
    # the actual caption (usually separated from the caption by <br/>).
    # Heuristic: if the caption contains "Fig." after another sentence,
    # trim the prefix up through the last period before "Fig.".
    m = re.search(r"((?:Fig|Plate)\.?\s*[\dIVX]+)", text, re.IGNORECASE)
    if m and m.start() > 40:
        text = text[m.start():].strip()
    return text.strip(" .|")


# Image inside a 2-row wikitable:
#   {| ...
#   | [[Image:…]]   OR  | {{raw image|…}}
#   |-
#   | CAPTION
#   |}
_TABLE_IMAGE_RE = re.compile(
    r"\{\|[^\n]*\n"
    r"\s*\|\s*(?:\[\[(?:File|Image):([^\]|]+)[^\]]*\]\]"
    r"|\{\{\s*raw\s+image\s*\|([^{}|]+)\s*\}\})"
    r"[^\n]*\n"
    r"\s*\|-[^\n]*\n"
    r"\s*\|\s*([^\n]+)",
    re.IGNORECASE,
)

# Image inside a styled <span> or <div>:
#   <span …>            or   <div …>
#   [[Image:…]]<br/>            {{raw image|…}}
#   {{sc|Fig. N.}}              {{c|{{sc|Fig. N.}}}}
#   </span>                 </div>
# The <br/> between image and caption is optional.
_WRAPPER_IMAGE_RE = re.compile(
    r"<(span|div)\b[^>]*>\s*"
    r"(?:\[\[(?:File|Image):([^\]|]+)[^\]]*\]\]"
    r"|\{\{\s*raw\s+image\s*\|([^{}|]+)\s*\}\})"
    r"\s*(?:<br\s*/?>\s*)?"
    r"((?:\{\{[^{}]*(?:\{\{[^{}]*\}\}[^{}]*)*\}\}|[^<])+?)"
    r"\s*</\1>",
    re.IGNORECASE | re.DOTALL,
)


def _find_following_caption(after_text: str) -> str | None:
    """Look forward from an image's position to find a caption.

    Handles several layouts common in EB1911:
      • <br> followed by caption text/templates
      • {{EB1911 Fine Print|…}} wrapper
      • Loose {{c|…}} (or {{c|{{sc|Fig. N.}}}}) on the next line
      • Standalone {{sc|Fig. N.}}—caption line
      • Plain "Fig. N.—caption" text
      • Separate wikitable after the image
    """
    tail = after_text
    # Skip whitespace, <br/>, closing tags, and EB1911 fine print close.
    tail = re.sub(
        r"^(?:\s|<br\s*/?>|</(?:span|div)\s*>|\{\{EB1911 fine print/e\}\})+",
        "", tail, flags=re.IGNORECASE,
    )
    if not tail:
        return None

    # 1. {{EB1911 Fine Print|…}} wrapper (may contain {{sc|…}}).
    m = re.match(
        r"\{\{\s*EB1911\s+Fine\s+Print\s*\|"
        r"((?:[^{}]|\{\{[^{}]*\}\})*)\}\}",
        tail, re.IGNORECASE,
    )
    if m:
        return _clean_caption_markup(m.group(1))

    # 2. {{c|…}} template (may contain nested templates).
    m = re.match(
        r"\{\{\s*c\s*\|((?:\{\{[^{}]*(?:\{\{[^{}]*\}\}[^{}]*)*\}\}|[^{}])+)\}\}",
        tail, re.IGNORECASE,
    )
    if m:
        return _clean_caption_markup(m.group(1))

    # 3. {{sc|Fig. N.}}… (with optional text after: num + em-dash + caption)
    m = re.match(
        r"(\{\{\s*sc\s*\|[^{}]*\}\}\s*"
        r"(?:\d+\.?\s*)?(?:[\u2014\u2013\-][^}\n]*)?)",
        tail, re.IGNORECASE,
    )
    if m:
        return _clean_caption_markup(m.group(1))

    # 4. Plain "Fig. N." or "Fig. N.—caption" (no template wrapper).
    m = re.match(
        r"((?:Fig|Plate)\.?\s*\d+\.(?:\s*[\u2014\u2013\-][^\n}]*)?)",
        tail, re.IGNORECASE,
    )
    if m:
        return _clean_caption_markup(m.group(1))

    # 5. Wikitable: {|…|}. Extract last row-cell as caption.
    if tail.startswith("{|"):
        end = tail.find("|}")
        if end > 0:
            table = tail[:end]
            rows = re.split(r"\n\s*\|-[^\n]*\n", table)
            if len(rows) > 1:
                last_row = rows[-1].strip()
                if last_row.startswith("|"):
                    last_row = last_row[1:].strip()
                return _clean_caption_markup(last_row)

    return None


def _collect_wrapper_captions(text: str) -> dict[str, str]:
    """Extract (filename → caption) for every image reference in text.

    Runs the full pattern set for each image position:
      • Image inside styled <span>/<div> wrapper
      • Image inside wikitable (|-\n|caption)
      • Image followed by loose {{c|…}} / {{sc|Fig…}} / wikitable

    Used to fill in captions that aren't embedded in the
    [[File:name|caption]] syntax itself.
    """
    captions: dict[str, str] = {}

    # Wikitable form with image INSIDE the table (first row = image,
    # second row = caption)
    for m in _TABLE_IMAGE_RE.finditer(text):
        fname = (m.group(1) or m.group(2) or "").strip()
        caption = _clean_caption_markup(m.group(3) or "")
        if fname and caption and fname not in captions:
            captions[fname] = caption

    # Wrapper form (<span>/<div>)
    for m in _WRAPPER_IMAGE_RE.finditer(text):
        fname = (m.group(2) or m.group(3) or "").strip()
        caption = _clean_caption_markup(m.group(4) or "")
        if fname and caption and fname not in captions:
            captions[fname] = caption

    # Forward-looking fallback: for every image reference, search the
    # text immediately after it for a loose caption line or table.
    for m in _IMAGE_PATTERN.finditer(text):
        fname = ((m.group(1) or m.group(2)) or "").split("|")[0].strip()
        if fname in captions:
            continue
        tail = text[m.end():m.end() + 1000]
        cap = _find_following_caption(tail)
        if cap:
            captions[fname] = cap

    return captions


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
        # Iterate article segments rather than pages. A single page may
        # contain content from two articles (end of article A, start of
        # article B); images get assigned to the article that actually
        # owns the segment they sit in. This fixes the WEIGHING MACHINES
        # vs WEIGHTS AND MEASURES case on vol 28 p.495, where two raw
        # images at the top of the page (Automatic Coal, Automatic
        # Luggage) belong to WEIGHING MACHINES but were being attached
        # to WEIGHTS AND MEASURES under the old page-only mapping.
        segments = (
            session.query(ArticleSegment, Article.volume)
            .join(Article, ArticleSegment.article_id == Article.id)
            .filter(Article.volume == volume)
            .order_by(ArticleSegment.article_id, ArticleSegment.sequence_in_article)
            .all()
        )

        created = 0
        seq_by_article: dict[int, int] = {}

        for segment, _vol in segments:
            text = segment.segment_text or ""
            matches = list(_IMAGE_PATTERN.finditer(text))
            if not matches:
                continue

            # Harvest wrapper-based captions (wikitable rows, styled
            # <span>s) once per segment and fill them in below.
            wrapper_captions = _collect_wrapper_captions(text)

            for match in matches:
                # Group 1 = [[File:…]] content
                # Group 2 = {{raw image|…}} filename
                # Group 3 = {{img float|…}} body
                if match.group(3) is not None:
                    parsed = _parse_img_float(match.group(3))
                    if not parsed:
                        continue
                elif match.group(1) is not None:
                    parsed = _parse_image_ref(match.group(1))
                else:
                    parsed = _parse_image_ref(match.group(2))
                if not parsed.get("caption"):
                    parsed["caption"] = wrapper_captions.get(parsed["filename"])

                existing = (
                    session.query(ArticleImage)
                    .filter(
                        ArticleImage.article_id == segment.article_id,
                        ArticleImage.source_page_id == segment.source_page_id,
                        ArticleImage.filename == parsed["filename"],
                    )
                    .first()
                )

                if existing:
                    continue

                seq_by_article[segment.article_id] = seq_by_article.get(
                    segment.article_id, 0) + 1

                session.add(
                    ArticleImage(
                        article_id=segment.article_id,
                        source_page_id=segment.source_page_id,
                        sequence_in_article=seq_by_article[segment.article_id],
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
