"""Divide the vol-29 'Classified List of Articles' into its 24 major categories.

ONE job, nothing else.  Read the assembled per-page OCR stream and cut it into
exactly 24 category chunks.  The 24 categories print in a fixed, KNOWN order,
each opened by a full-width banner -- so a wall is pinned by SEQUENCE: a banner
only ever opens the NEXT category.  An out-of-order or substring-coincidence
match (Zoology's "Natural History" -> History, a clipped "Phy" -> Geography) is
not the next category in line, so it can never cut a wall.  A wall is absolute;
category-mixing is unexpressible.

Self-contained by design: imports nothing from the rest of the pipeline.  Input
is the assembled OCR text (data/derived/vol29_ocr.json); output is the 24 chunks
(data/derived/toc_category_chunks.json), each a category name + all its bytes.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

OCR = Path("data/derived/vol29_ocr.json")
OUT = Path("data/derived/toc_category_chunks.json")
WS_START, WS_END = 891, 955

# The 24 major categories, in printed order.
CATEGORIES = [
    "Anthropology and Ethnology", "Archaeology and Antiquities", "Art",
    "Astronomy", "Biology", "Chemistry", "Economics and Social Science",
    "Education", "Engineering", "Geography", "Geology", "History",
    "Industries, Manufactures and Occupations", "Language and Writing",
    "Law and Political Science", "Literature", "Mathematics",
    "Medical Science", "Military and Naval", "Philosophy and Psychology",
    "Physics", "Religion and Theology", "Sports and Pastimes", "Miscellaneous",
]

# Art prints no full-width banner of its own -- it is a group of sub-arts -- so
# it opens on the first of THESE sub-art section banners instead of on a name.
ART_OPENERS = ["Architecture", "Music", "Painting and Engraving",
               "Sculpture", "Minor Arts", "Stage and Dancing"]


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def _banner_token(line: str) -> str:
    """A `## ` banner line -> its category-name part, normalized.  Drop any
    `: Subjects` / `*...*` section tail the model appended to the banner."""
    return _norm(re.sub(r"[*:].*$", "", line.strip()[3:]))


def assemble_sequence() -> list[tuple[int, int, str]]:
    """The per-page reads concatenated in page order -> [(ws, idx, line)].  A
    category runs start-to-finish before the next begins, so page order is the
    only sequencing the boundaries need.  No reordering, no tampering."""
    ocr = json.loads(OCR.read_text(encoding="utf-8"))
    seq: list[tuple[int, int, str]] = []
    for ws in range(WS_START, WS_END + 1):
        text = ocr.get(str(ws))
        if not text:
            continue
        for idx, line in enumerate(text.split("\n")):
            seq.append((ws, idx, line))
    return seq


def category_openers() -> list[tuple[str, list[str]]]:
    """In printed order, each category and the banner tokens that open it: its
    own name, except Art, which opens on its sub-art section banners."""
    openers: list[tuple[str, list[str]]] = []
    for c in CATEGORIES:
        toks = ART_OPENERS if c == "Art" else [c]
        openers.append((c, [_norm(t) for t in toks]))
    return openers


def _opens(banner: str, tokens: list[str]) -> bool:
    """A banner opens a category if its (possibly gutter-clipped) name token is a
    prefix/suffix of one of the category's opener tokens, or vice versa.  A clip
    shorter than 3 chars is too ambiguous to seat a wall."""
    for t in tokens:
        if not t or len(banner) < 3:
            continue
        if (t == banner or t.startswith(banner) or t.endswith(banner)
                or banner.startswith(t) or banner.endswith(t)):
            return True
    return False


def build_category_chunks(seq, openers):
    """Slice the stream into (category, lines) chunks: every line from a
    category's wall up to the next category's wall.  Advance to the next category
    ONLY when a banner opens it; everything else (repeats, sub-banners,
    coincidental matches) stays in the current chunk.  Each line belongs to
    exactly one category, so the chunks partition the stream -- nothing dropped,
    nothing shared.  `preamble` holds anything before the first wall."""
    preamble: list[tuple[int, int, str]] = []
    chunks: list[list] = []
    cur = -1
    for ws, idx, line in seq:
        s = line.strip()
        if s.startswith("## ") and cur + 1 < len(openers):
            bt = _banner_token(line)
            # Open the next category ONLY if the banner names the next and NOT
            # the current.  "Geo" is a prefix of both Geography and Geology, so a
            # clipped Geography banner ("Geo") is a repeat, never the Geology
            # wall; the real Geology banner clips to "Geol"/"ogy", which name
            # Geology alone.  This is the only sound way to seat a clipped wall.
            if (_opens(bt, openers[cur + 1][1])
                    and not (cur >= 0 and _opens(bt, openers[cur][1]))):
                cur += 1
                chunks.append([openers[cur][0], []])
        (chunks[cur][1] if cur >= 0 else preamble).append((ws, idx, line))
    return preamble, chunks


def main() -> None:
    seq = assemble_sequence()
    preamble, chunks = build_category_chunks(seq, category_openers())

    def asc(x: str) -> str:
        return x.encode("ascii", "backslashreplace").decode()

    def nbytes(lines) -> int:
        return sum(len(l) for _, _, l in lines)

    print(f"assembled {len(seq):,} lines / {nbytes(seq):,} bytes "
          f"from pages {WS_START}-{WS_END}\n")
    print(f"{len(chunks)} category chunks  (name + every byte inside):")
    for i, (cat, lines) in enumerate(chunks, 1):
        ws0, idx0, _ = lines[0]
        print(f"  {i:2d}. {asc(cat):34s} ws{ws0}:{idx0:<3d}  "
              f"{len(lines):5,d} lines  {nbytes(lines):7,d} bytes")

    total, accounted = nbytes(seq), nbytes(preamble) + sum(
        nbytes(l) for _, l in chunks)
    print(f"\npreamble before first wall: {nbytes(preamble)} bytes")
    print(f"bytes conserved: {accounted:,} / {total:,}  "
          f"({'all accounted for' if accounted == total else 'LOSS'})")
    print(f"all 24, in printed order: {[c for c, _ in chunks] == CATEGORIES}")

    OUT.write_text(json.dumps(
        [{"name": c, "text": "\n".join(l for _, _, l in ls)} for c, ls in chunks],
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
