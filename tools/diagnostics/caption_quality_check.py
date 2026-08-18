"""Audit exported article IMG captions for markup artifacts.

Flags captions that contain patterns indicating incomplete sanitization:
- HTML table-cell attributes (align=, width=, style=, colspan=, ...)
- Unwrapped `{{template|...}}` or `{{template}}` fragments
- Wikilink syntax `[[...]]`
- Suspicious `))` sequences (our }} sanitizer artifact)
- Stray `|` or double braces
- Stray HTML tags

Usage:
    python tools/caption_quality_check.py
"""
import io
import json

from britannica.export.corpus import load_corpus
import os
import re
import sys
from britannica.util.strings import HTML_TAG_RE

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                              errors="replace")

ART_DIR = "data/derived/articles"

SUSPECT_PATTERNS = {
    "html_attr": re.compile(r'\b(?:align|width|style|colspan|rowspan|valign|class|scope)\s*='),
    "template_frag": re.compile(r"\{\{[^}]+|[^{]+\}\}"),
    "wikilink": re.compile(r"\[\[|\]\]"),
    "double_close_artifact": re.compile(r"\)\)"),
    "stray_pipe": re.compile(r" \| "),
    "html_tag": HTML_TAG_RE,
    "ref_tag": re.compile(r"&(?:amp|nbsp|lt|gt);"),
}


def audit() -> None:
    totals: dict[str, int] = {k: 0 for k in SUSPECT_PATTERNS}
    samples: dict[str, list[tuple[str, str]]] = {k: [] for k in SUSPECT_PATTERNS}
    articles_with_imgs = 0
    total_img_markers = 0
    total_with_caption = 0

    # Through the one reader: it owns the exclusion list (hand-spelled here) and
    # raises on a payload it cannot read.
    for _p, d in sorted(load_corpus()[0].items()):
        path = str(_p)
        body = d.get("body") or ""
        if "{{IMG:" not in body:
            continue
        articles_with_imgs += 1
        for m in re.finditer(r"\{\{IMG:([^|}]+)(?:\|([^{}]*))?\}\}", body):
            total_img_markers += 1
            cap = m.group(2)
            if not cap:
                continue
            total_with_caption += 1
            for name, pat in SUSPECT_PATTERNS.items():
                if pat.search(cap):
                    totals[name] += 1
                    if len(samples[name]) < 5:
                        samples[name].append((d["title"], cap))

    print(f"Articles with IMG markers:     {articles_with_imgs}")
    print(f"Total IMG markers:             {total_img_markers}")
    print(f"IMG markers with captions:     {total_with_caption}")
    print()
    print("=== Caption-quality issues ===")
    for name in SUSPECT_PATTERNS:
        pct = (totals[name] * 100 / total_with_caption) if total_with_caption else 0
        print(f"  {name:24s} {totals[name]:5d}  ({pct:.2f}%)")
        for title, cap in samples[name]:
            print(f"    {title!r}: {cap[:120]!r}")


if __name__ == "__main__":
    audit()
