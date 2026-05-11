"""Plate-parser data classes shared across the four stages."""

from __future__ import annotations

from dataclasses import dataclass, field

@dataclass
class ImageRef:
    """One image reference found in the source.

    ``inline_caption`` is the caption that lived INSIDE the image
    template (``{{img float|file=X|cap=Y}}`` carries Y on its own); if
    set, this image is already paired and stage 4 won't try to attach
    a separate caption to it.
    """
    filename: str
    pos: int                      # start byte position in the source
    end_pos: int                  # one past last byte
    inline_caption: str | None = None
    raw: str = ""                 # the matched markup, for debugging
    number: int | None = None     # number embedded in filename if any


@dataclass
class CaptionFrag:
    """One caption-shaped text fragment found in the source."""
    text: str                     # cleaned caption text
    pos: int
    end_pos: int
    number: int | None = None     # explicit prefix number if any
    is_credit: bool = False       # italic credit line, no figure number
    is_shared: bool = False       # colspan row → applies to multiple imgs
    raw: str = ""


@dataclass
class PlateBlock:
    header: str = ""
    pairs: list[tuple[str, str]] = field(default_factory=list)  # (filename, caption)
    shared_legends: list[str] = field(default_factory=list)
    footer: str = ""


