import json
import re
import hashlib
from pathlib import Path
from urllib.parse import quote

from britannica.db.models import Article, ArticleImage, ArticleSegment, SourcePage
from britannica.db.session import SessionLocal
from britannica.parsers import img_float as _img_float_parser


_IMAGE_PATTERN = re.compile(
    # Standard [[File:name|opts]] form
    r"\[\[(?:File|Image):([^\]]+)\]\]"
    # OR {{raw image|filename}} — alternate EB1911 image syntax; the
    # filename is captured bare (no caption/options).
    r"|\{\{\s*raw\s+image\s*\|([^{}|]+)\s*\}\}"
    # OR {{img float|file=...|cap=...}} / {{figure|...}} / {{FI|...}}
    # — inline float templates.  Supports up to 4 levels of nested
    # `{{…}}` (CASTLE Fig. 9 `cap={{Fs85|…}}{{center|{{EB1911 Fine
    # Print|{{sc|Fig.}}…}}}}` is 4 levels deep).
    r"|\{\{\s*(?:img\s+float|figure|FI)\s*\|"
    r"((?:[^{}]|\{\{(?:[^{}]|\{\{(?:[^{}]|\{\{[^{}]*\}\})*\}\})*\}\})*)\}\}",
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
    parsed = _img_float_parser.parse(body)
    if parsed is None:
        return None
    return {
        "filename": parsed.filename,
        "caption": parsed.caption or None,
        "commons_url": _commons_url(parsed.filename),
    }


def _clean_caption_markup(text: str) -> str:
    """Strip wiki/HTML noise from an extracted caption string.

    Handles the caption-wrapper templates and tags that appear around
    WEIGHING MACHINES / SEWING MACHINES figures: {{sc|…}}, {{smaller|…}},
    {{c|…}}, <br/>, alignment attributes like `align="center"|`.
    """
    # Drop leading wikitable cell attributes: `align="..." width="..." |`.
    # Both quoted (`align="center"`) and unquoted (`rowspan=4`) values
    # are accepted.  Also handles a nested-table opener ``{|...attrs...``
    # — when the post-image line is actually the header of an inner
    # layout table, we want to strip the attrs and leave the (likely
    # empty) remainder for the attribute-fragment guard below.
    text = re.sub(
        r'^\{?\|?(?:(?:align|style|width|valign|class|colspan|rowspan|'
        r'id|scope|cellpadding|cellspacing|bgcolor|border|nowrap|height)'
        r'\s*=\s*(?:"[^"]*"|\S+)\s*)+\|?\s*',
        "", text,
    )
    # Reject captions that, after stripping, contain only attribute
    # fragments (`width="80%" cellpadding="0" ...` from a nested-table
    # header).  These are leakage, not real caption text — return empty
    # so the caller can fall through to a more accurate caption source.
    attr_only_check = re.sub(
        r'(?:[a-z]+\s*=\s*(?:"[^"]*"|\S+)\s*)+',
        '', text, flags=re.IGNORECASE,
    ).strip(' .|{}|"\'')
    if not attr_only_check:
        return ""
    # Strip common wrapper templates, keeping inner text. `Fs` has a
    # `|percent|text` signature — keep only the text.
    for _ in range(5):
        text = re.sub(r"\{\{\s*(?:sc|smaller|c|center|small|big|bold|italic|nowrap)\s*\|([^{}]*)\}\}",
                      r"\1", text, flags=re.IGNORECASE)
        # ``{{uc|TEXT}}`` uppercases TEXT in Wikisource rendering —
        # preserve that when unwrapping (REGALIA plate captions use
        # it extensively).
        text = re.sub(r"\{\{\s*uc\s*\|([^{}]*)\}\}",
                      lambda m: m.group(1).upper(),
                      text, flags=re.IGNORECASE)
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
    # Skip whitespace, <br/>, closing tags, EB1911 fine print close,
    # and inner-wikitable closers.  Plate pages routinely wrap each
    # image in a 1-cell inner table (``{|…|[[Image:…]]|}``) whose
    # closer sits between the image reference and the caption text.
    tail = re.sub(
        r"^(?:\s|<br\s*/?>|</(?:span|div)\s*>"
        r"|\{\{EB1911 fine print/e\}\}|\|\})+",
        "", tail, flags=re.IGNORECASE,
    )
    # Peel outer-wikitable row separators + cell-attribute prefixes.
    # REGALIA Plate III layout puts the caption in the NEXT row of the
    # outer table after the image's inner ``|}``:
    #   {| ...inner image table...
    #   |[[Image:...]]
    #   |}
    #   |-                        ← outer-table row separator
    #   | {{ts|ac}} | N.—CAPTION  ← caption in the next outer cell
    # Loop because plate pages sometimes have a blank-spacer row
    # (``|-\n| &nbsp;``) between the image and the caption.
    while True:
        new_tail = tail
        # Row separator: ``|-`` with any attributes, newline.
        new_tail = re.sub(
            r"^\|-[^\n]*\n\s*", "", new_tail)
        # Cell opener with attrs+content-separator: ``| {{ts|…}} |``
        # or ``| style="…" |``.  Consumes up through the attr-content
        # pipe.  ``(?!-)`` prevents matching ``|-`` row separators as
        # cell openers.  The alternation ``\{\{[^}]*\}\}|[^|\n]`` lets
        # the attrs contain ``{{ts|ac}}``-style templates with internal
        # pipes — matching the template as an atomic unit rather than
        # stopping at the first ``|``.
        new_tail = re.sub(
            r"^\|(?!-)(?:\{\{[^}]*\}\}|[^|\n])*?\|\s*", "", new_tail)
        # Blank spacer cells: ``| &nbsp;`` or ``|`` followed by nothing
        # meaningful.  Treat them as skippable padding.
        m = re.match(r"^\|(?!-)\s*&(?:nbsp|emsp|ensp|thinsp);?\s*\n",
                     new_tail)
        if m:
            new_tail = new_tail[m.end():]
        if new_tail == tail:
            break
        tail = new_tail
        # Strip any whitespace/closer noise we may have uncovered.
        tail = re.sub(
            r"^(?:\s|<br\s*/?>|</(?:span|div)\s*>"
            r"|\{\{EB1911 fine print/e\}\}|\|\})+",
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

    # 4b. Bare numbered plate caption: ``N.—CAPTION TEXT`` or
    # ``N.-CAPTION``.  Common in plate pages where each image is in a
    # nested wikitable and the caption sits immediately after the inner
    # ``|}``.  REGALIA Plates I-IV use this exclusively.  Extended
    # numbered forms (``1(a).``) and letter-indexed (``A.—``) too.
    # ``[^\n]`` (not ``[^\n}]``) so captions with embedded templates
    # like ``{{uc|TITLE}}`` aren't truncated at the first ``}`` in
    # ``}}`` — ``_clean_caption_markup`` unwraps templates below.
    m = re.match(
        r"((?:\d+(?:\([a-z]\))?|[A-Z])\.?\s*"
        r"[\u2014\u2013\-]\s*[^\n]*)",
        tail,
    )
    if m and re.search(r"[A-Za-z]{3,}", m.group(1)):
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
