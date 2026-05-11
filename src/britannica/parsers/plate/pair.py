"""Stage 4: pair images with captions and render.

``pair_images_with_captions`` walks the collected lists by source
position, with explicit-number overrides and shared-caption (colspan)
detection.  ``_try_render_as_outline_plate`` handles the special case
of a GEMS-style outline-numbered plate, where the captions arrive as a
nested ``::`` outline rather than a flat list.
"""

from __future__ import annotations

import re

from britannica.parsers.plate.captions import _strip_caption_markup
from britannica.parsers.plate.images import _filename_number
from britannica.parsers.plate.models import CaptionFrag, ImageRef

def pair_images_with_captions(
    images: list[ImageRef],
    captions: list[CaptionFrag],
) -> tuple[list[tuple[str, str]], list[str]]:
    """Return ``(pairs, shared_legends)``.

    Algorithm:
      1. Inline captions (from ``{{img float|cap=…}}``) attach immediately.
      2. Explicit-number override: when both filename and caption carry
         the same trailing number, pair them regardless of position.
      3. Remaining images take the nearest unclaimed caption by source
         position (preferring the one immediately following the image).
      4. Captions left over after every image is paired become shared
         legends if they're long enough to read as collective; short
         leftovers are ignored.
    """
    pairs: list[tuple[str, str]] = []
    used_caption_ids: set[int] = set()

    # 1. Inline captions take precedence.
    for img in images:
        if img.inline_caption:
            cleaned = _strip_caption_markup(img.inline_caption)
            pairs.append((img.filename, cleaned))
            img.inline_caption = "__USED__"  # mark consumed

    # 2. Explicit-number override.
    cap_by_number: dict[int, list[CaptionFrag]] = {}
    for c in captions:
        if c.number is not None:
            cap_by_number.setdefault(c.number, []).append(c)
    for img in images:
        if img.inline_caption == "__USED__":
            continue
        if img.number is None:
            continue
        candidates = cap_by_number.get(img.number, [])
        candidates = [c for c in candidates if id(c) not in used_caption_ids]
        if candidates:
            # Prefer the closest by position.
            best = min(candidates, key=lambda c: abs(c.pos - img.pos))
            pairs.append((img.filename, best.text))
            used_caption_ids.add(id(best))
            img.inline_caption = "__USED__"

    # 3. Position-based pairing for the rest.  Two passes:
    #    - First pass uses NON-CREDIT captions only — descriptive
    #      captions ("JACOPO DELLA QUERCIA—Tomb…") claim the primary
    #      slot.
    #    - Images that didn't find a non-credit fall back to credits
    #      in a second pass.
    # SCULPTURE PLATE I has photo-credit rows BETWEEN image rows and
    # descriptive-caption rows; without this two-pass logic the
    # nearest-by-position rule pairs every image with its photo
    # credit ("(Photo, Brogi.)") and the descriptive captions dangle
    # as legends at the bottom.
    remaining_imgs = [r for r in images if r.inline_caption != "__USED__"]
    remaining_caps = [c for c in captions if id(c) not in used_caption_ids]

    def _pick_best(img: ImageRef, pool: list[CaptionFrag]) -> CaptionFrag | None:
        after = [c for c in pool if c.pos > img.pos]
        if after:
            return min(after, key=lambda c: c.pos - img.pos)
        before = [c for c in pool if c.pos < img.pos]
        if before:
            return max(before, key=lambda c: c.pos)
        return None

    img_to_cap: dict[str, str] = {}
    for img in remaining_imgs:
        # ``is_shared`` cells (colspan>1) are plate-wide titles, not
        # per-image captions — exclude from primary pool so they
        # become LEGENDs at step 5.  Without this, DOG PLATE IV's
        # ``TYPICAL TOY DOGS`` (colspan=4 footer) gets pulled into the
        # primary slot and cascades the per-image pairing off by one.
        non_credits = [c for c in remaining_caps
                       if not c.is_credit and not c.is_shared
                       and id(c) not in used_caption_ids]
        best = _pick_best(img, non_credits)
        if best is not None:
            img_to_cap[img.filename] = best.text
            used_caption_ids.add(id(best))
        else:
            img_to_cap[img.filename] = ""
    # Second pass: images without a non-credit caption fall back to
    # credits.
    for img in remaining_imgs:
        if img_to_cap.get(img.filename):
            continue
        credits = [c for c in remaining_caps
                   if c.is_credit and id(c) not in used_caption_ids]
        best = _pick_best(img, credits)
        if best is not None:
            img_to_cap[img.filename] = best.text
            used_caption_ids.add(id(best))

    # Build pair list in source-image order.
    pairs_by_pos: list[tuple[str, str]] = []
    seen: set[str] = set()
    for img in images:
        if img.filename in seen:
            continue
        seen.add(img.filename)
        # Inline / explicit-number / position pass — find this image's
        # caption from any of the three lists.
        cap_text = ""
        for fn, cap in pairs:
            if fn == img.filename:
                cap_text = cap
                break
        else:
            cap_text = img_to_cap.get(img.filename, "")
        pairs_by_pos.append((img.filename, cap_text))

    # 4. Append credits to their column-aligned image caption.  When
    # a plate has a credit row of the same width as the image row,
    # the credit at column k belongs to the image at column k — both
    # are at the same x-coordinate in the rendered table.  Approximate
    # this with source-order pairing: if the count of unclaimed
    # credits exactly equals the image count, credit[i] attaches to
    # image[i] in source order.  When counts mismatch the structural
    # rule doesn't apply (credit row only covers some images, or
    # there's a per-figure credit interleaving); skip the attach
    # rather than risk duplicate pile-ups.
    unpaired_credits = sorted(
        (c for c in remaining_caps
         if c.is_credit and id(c) not in used_caption_ids),
        key=lambda c: c.pos,
    )
    images_in_order = sorted(images, key=lambda i: i.pos)
    if unpaired_credits and len(unpaired_credits) == len(images_in_order):
        for img, credit in zip(images_in_order, unpaired_credits):
            for j, (fn, cap) in enumerate(pairs_by_pos):
                if fn == img.filename:
                    credit_clean = credit.text.strip("() ")
                    if cap:
                        pairs_by_pos[j] = (fn, f"{cap} ({credit_clean})")
                    else:
                        pairs_by_pos[j] = (fn, f"({credit_clean})")
                    used_caption_ids.add(id(credit))
                    break

    # 5. Leftover non-credit, non-shared captions become shared
    # legends if long enough.  ``is_shared`` captions are handled
    # separately by ``parse_plate`` — they get routed to header or
    # footer based on source position so the viewer can render them
    # with title styling rather than caption styling.
    shared = []
    for c in remaining_caps:
        if id(c) in used_caption_ids:
            continue
        if c.is_credit or c.is_shared:
            continue
        if len(c.text) > 20:
            shared.append(c.text)
    return pairs_by_pos, shared


def _try_render_as_outline_plate(
    text: str, images: list[ImageRef],
) -> str | None:
    """Detect a single-composite-image plate whose post-image content
    is a hierarchical numbered caption block (GEMS PLATE I), and
    render it as ``{{IMG:fn}}`` followed by the OUTLINE marker.

    Returns ``None`` if the plate doesn't match this shape — the
    normal image+caption pairing path then runs.
    """
    if len(images) != 1:
        return None
    img = images[0]
    after = text[img.end_pos:]
    # Strip wrappers that interrupt the list-shape detection but
    # carry no list content of their own.
    after = re.sub(r"\{\{EB1911 fine print/[se]\}\}", "", after)
    after = re.sub(r"<div\b[^>]*>|</div>", "", after)
    # Flatten layout-only HTML tables (GEMS PLATE II uses a 2-column
    # `<table>` to split the numbered caption block into columns).
    # Strip the table / row / cell tags but keep their content; cells
    # are already in reading order (left-to-right then top-to-bottom).
    after = re.sub(
        r"</?(?:table|tbody|thead|tfoot|tr|td|th)\b[^>]*>",
        "", after, flags=re.IGNORECASE,
    )
    # `<br />` lines that survived as bare line-starts (GEM II's column
    # cells start with `\n<br />27–34.—…`); the line-start `<br />` is
    # a column-top spacer, not part of the list line — drop it so the
    # range header reads cleanly.
    after = re.sub(r"^\s*<br\s*/?>\s*", "", after, flags=re.MULTILINE | re.IGNORECASE)

    # Defer imports — these modules import this one.
    from britannica.pipeline.stages.elements import (
        ElementRegistry,
        _extract_outlines,
        _process_outline,
    )
    from britannica.pipeline.stages.transform_articles import (
        _transform_body_text,
    )

    registry = ElementRegistry()
    residual = _extract_outlines(after, registry, require_emphasis=False)
    outlines = [
        (k, raw) for k, (etype, raw) in registry.elements.items()
        if etype == "OUTLINE"
    ]
    if not outlines:
        return None

    parts = [f"{{{{IMG:{img.filename}}}}}"]
    for _, raw_block in outlines:
        rendered = _process_outline(raw_block, _transform_body_text)
        if rendered.strip():
            # Plate-caption outlines render in figure-caption styling
            # (smaller, italic, compressed) — re-tag the marker so
            # the viewer can route to a dedicated CSS class without
            # restyling every taxonomic OUTLINE corpus-wide.
            rendered = rendered.replace(
                "«OUTLINE:", "«PLATE_OUTLINE:", 1,
            ).replace(
                "«/OUTLINE»", "«/PLATE_OUTLINE»", 1,
            )
            parts.append(rendered.strip())

    # Preserve post-outline footer prose (credit line under the plate,
    # e.g. GEMS PLATE I's "All the above are in the British Museum.").
    # Strip OUTLINE placeholders from residual; what remains is plate
    # bookend matter.
    placeholder_keys = [k for k, _ in outlines]
    footer = residual
    for k in placeholder_keys:
        footer = footer.replace(k, "")
    footer = _transform_body_text(footer).strip()
    if footer:
        parts.append(f"«I»{footer}«/I»")

    return "\n\n".join(parts)


