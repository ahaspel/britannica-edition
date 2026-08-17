"""Identity of the measured table-width cache.

The build-time tool ``tools/diagnostics/measure_table_widths.py`` renders every
unique «TABLE» span through the REAL ``decode_inline`` inside a 590px
`.body-text` host and records whether the browser could fit it in the column.
``tools/pipeline/annotate_table_markers.py`` then stamps `«TABLE[cols:N|wide|`
from that cache, and the render wraps exactly the tables that measured wide.

Writer and reader must address a span IDENTICALLY: the cache keys on the span's
BYTES, so a key or a path that differs by a character between the two sides is
not an error, it is a total cache miss — every table silently loses its Expand
hint.  That is a channel this file exists to close, and it is not theoretical:
the 2026-08-16 rebuild re-hyphenated table interiors, the spans hashed
differently than when measured, and 194 of them dropped their hints unnoticed.

So the span-addressing lives HERE, in the library both sides already depend on,
rather than in either tool — the pipeline used to reach into a diagnostics
script through a CWD-relative ``sys.path`` hack to borrow it.  The measuring,
the annotating, and the render each keep their own business; only the identity
is shared.  Companion of :mod:`britannica.math_widths`, same arrangement.

What a table span IS — where it ends, what its params mean — is the lexicon's
(:mod:`britannica.markers`); this module only says how one is ADDRESSED.
"""
from __future__ import annotations

from pathlib import Path

from britannica.markers import strip_table_wide
from britannica.util.strings import content_digest

CACHE_PATH = Path("data/derived/table_widths.json")


def span_key(span: str) -> str:
    """Cache identity of a table span: its unannotated bytes, addressed.

    The FULL digest, not the 16-char default — the on-disk cache has always
    been keyed this way and its 10,984 measured entries depend on it.
    """
    return content_digest(strip_table_wide(span), n=None)


# Where a table starts costing the reader something.  Measured in the real
# viewer (viewport 1280, `/article/…`), NOT in a reconstruction of it:
#
#     .body-text content box .................. 590px
#     room before the card clips anything ..... 751px
#     what else occupies that right margin .... nothing
#
# `.body-text` carries `margin-right: 160px` of furniture space for the marginal
# page numbers, and nothing clips it (`flow-root` contains floats; it does not
# hide overflow).  A table wider than the 590px column therefore loses NOTHING
# until it reaches the card's content edge at 751px — it simply spills into empty
# margin and stays whole and readable.
#
# Measuring against 590 gave 471 of 920 measured-wide spans (51%) an Expand
# button for an overflow that cost the reader nothing — and made them WORSE:
# PURIN's four chem tables (743/650/633/588px) render complete and readable
# unwrapped, while the treatment puts three into 588px scroll boxes and squeezes
# the fourth to fit.  Expand is a LAST RESORT (user, 2026-08-17); it is for a
# table the page genuinely cannot show.
WIDE_LIMIT = 751


def is_wide(entry: "dict | None") -> bool:
    """Does this measured span actually overflow what the page can show?

    THE policy, and it lives apart from the measurement on purpose: the cache
    stores `w`, a FACT about a span, so re-tuning this line never means
    re-rendering 10,984 tables in a browser — the same reason the width and the
    hint are separate in the math path.
    """
    return bool(entry) and (entry.get("w") or 0) > WIDE_LIMIT
