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
