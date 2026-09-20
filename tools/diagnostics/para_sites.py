"""Every place prose resumes after a display block, addressed for the scan.

    uv run python tools/diagnostics/para_sites.py --out data/derived/para_sites.json
    uv run python tools/diagnostics/para_sites.py --out sample.json --sample 40 --seed 1911

A companion to `para_indent.py`, which measures ONE site against the scan.  This
one enumerates them, and its whole job is to produce an address the scan tool can
actually find: a volume, a Wikisource page, and a PROSE anchor.

WHY A PROSE ANCHOR, AND NOT THE MARKUP.  The resumption is the only stable part
of the site.  Its block is usually a formula or a table, whose transcription is
volatile -- and an address keyed to that text would rot on the next Wikisource
edit (21.7% of pages were edited in five months).  A run of plain words from the
resumption survives that, and it is also the one thing OCR can match.

WHAT THE SITE RECORDS.  `rendered` is what WE currently do, taken from the
markup: `indent` where a `<p>` opens (our pipeline saw a blank line) and `flush`
where the text rides on inside the open paragraph.  That is the claim the scan
adjudicates, so it belongs in the record beside the verdict, not inferred later.

The `ws_page` is carried, never re-derived from a leaf offset: the payload gives
`page_start`/`ws_page_start` for the article, and pages run in lockstep inside
one article (volume breaks fall at article boundaries), so the page marker's
printed number fixes the Wikisource page by its distance from the article's own
first page.
"""
from __future__ import annotations

import argparse
import html
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from britannica.export.corpus import load_corpus          # noqa: E402
from britannica.util.strings import strip_html_tags       # noqa: E402

EV = re.compile(r"<(/?)(div|table)\b([^>]*)>", re.I)
PAGE = re.compile(r'data-page="(\d+)" data-vol="(\d+)"')
NONPROSE = re.compile(r'^\s*<(td|th|tr|table|div|span class="small-caps)', re.I)
WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")
# The kind vocabulary lives here because this module MAKES the kinds;
# `para_indent` imports it rather than re-spelling the strings.
BARE_DIV = "div(bare)"
LIST_KINDS = ("div[indent]", "div[hanging]")
STYLE_ATTR = re.compile(r'style="([^"]*)"')
# Mathematics reaches the payload as TeX, so the words in it are COMMAND NAMES:
# an anchor taken raw from `\text{K}\! may also be expressed` leads with "text",
# which is nowhere on the printed page.  That is not a random miss -- it fails
# exactly the math-heavy kinds, which would quietly bias any rate measured from
# the sites that survive (6 of 6 `math-system-rows` and 5 of 6 `div.centered`
# went unlocated before this).  Strip the commands and the grouping, then anchor
# on real words only.
LATEX = re.compile(r"\\[A-Za-z]+|\\[^A-Za-z]|[{}$^_&]")
ANCHOR_MIN_LEN = 3
# The anchor must name the resumption's FIRST line -- measuring a later line
# would answer about the wrong paragraph -- so it is drawn from the head of the
# resumption only, not from wherever prose first appears.
ANCHOR_HEAD_WORDS = 14
# An anchor word tesseract can be trusted on: letters only, long enough not to
# match everywhere.  Italic and small-caps runs are avoided by taking the words
# after tag-stripping, which keeps only what was set as plain prose.
ANCHOR_MIN_WORDS = 3
ANCHOR_MAX_WORDS = 6

# Is the interrupting block MATHEMATICS?  The kinds do not answer this: the two
# largest, `table` and `div.centered`, each carry both displayed equations and
# ordinary matter (a verse quotation in FIELDING, a tariff table in CLARINET),
# while `div.math-system*` is only a fifth of the population.  Judge the block's
# own content instead.
_TEX = re.compile(r"\\(frac|sqrt|mbox|text|mathrm|partial|int|sum|left|right|"
                  r"alpha|beta|gamma|delta|theta|lambda|sigma|omega|pi|cdot|"
                  r"times|infin|ldots|dfrac|tfrac|overline|hat|vec)\b")
_MATH_CHR = re.compile(r"[∫∑∏√≤≥≠≡∞±×÷∂∇⁄⅓½¼′″]|＝")


def is_math(text: str) -> bool:
    """Strict: the block states mathematics, not merely numbers."""
    if _TEX.search(text) or _MATH_CHR.search(text):
        return True
    if "=" not in text:
        return False
    # An equation is mostly symbols; a sentence containing "=" is mostly letters.
    letters = sum(c.isalpha() for c in text)
    return bool(text) and letters / max(1, len(text)) < 0.45


def kindof(attrs: str) -> str:
    m = re.search(r'class="([^"]*)"', attrs)
    if m:
        cls = m.group(1).split()
        return "div." + cls[0] if cls else BARE_DIV
    m = STYLE_ATTR.search(attrs)
    if m:
        s = m.group(1)
        indent_kind, hanging_kind = LIST_KINDS
        for p, n in (("font-size:83%", "fine-print"), ("margin", "div[margin]"),
                     ("padding-left", indent_kind), ("text-indent", hanging_kind)):
            if p in s:
                return n
        return "div[style]"
    return BARE_DIV


_APPARATUS = ('<div class="footnotes"', "<h3>Notes</h3>", "<h2>Notes</h2>",
              "<h2>Cross-references</h2>", "<h3>Cross-references</h3>",
              "<h2>Contributor</h2>", "<h3>Contributor</h3>")


def body_end(h: str, start: int) -> int:
    """Where the article body stops and the appended apparatus begins.

    Every heading level, and the footnotes DIV, because they do not agree: the
    cross-references card uses `<h2>` but footnotes use
    `<div class="footnotes"><h3>Notes</h3>`.  Cutting on `<h2>` alone leaves the
    footnote list inside the body, where the last small-type block appears to be
    followed by prose -- strip the tags and a footnote reads as a resumption
    beginning "Notes 1. ...".  Three of nine sampled fine-print sites were that,
    not body text at all.
    """
    ends = [x for x in (h.find(t, start) for t in _APPARATUS) if x > 0]
    end = min(ends) if ends else len(h)
    back = h.rfind('<div class="card">', start, end)
    return back if back > 0 else end


def sites_in(payload: dict) -> list[dict]:
    h = payload.get("rendered_html") or ""
    i = h.find('class="body-text"')
    if i < 0:
        return []
    h = h[:body_end(h, i)]
    page0, ws0 = payload.get("page_start"), payload.get("ws_page_start")
    out, stack = [], []
    for m in EV.finditer(h, i):
        closing, tag, attrs = m.group(1), m.group(2), m.group(3)
        if not closing:
            stack.append((m.end(), "table" if tag.lower() == "table" else kindof(attrs)))
            continue
        if not stack:
            continue
        cstart, kind = stack.pop()
        rest = h[m.end():m.end() + 400]
        lead = rest.lstrip()
        indented = lead.startswith("<p>")
        body = lead[3:] if indented else lead
        if NONPROSE.match(body):
            continue
        # Drop a tag the window cut in half: `rest` is a fixed slice, so a
        # `<td style="...">` beginning near its end survives as `<td style="bo`
        # with no closing bracket, which TAG cannot match -- and the attribute
        # text then reads as prose ("and thus given style border-top").
        dangling = body.rfind("<")
        if dangling > body.rfind(">"):
            body = body[:dangling]
        # Entities AFTER tag-stripping, never before, or `&lt;p&gt;` would turn
        # into a tag and be stripped as one.
        after = html.unescape(re.sub(r"\s+", " ", strip_html_tags(body, " "))).strip()
        head = WORD.findall(LATEX.sub(" ", after))[:ANCHOR_HEAD_WORDS]
        words = [w for w in head if len(w) >= ANCHOR_MIN_LEN]
        if len(words) < ANCHOR_MIN_WORDS:
            continue
        pm = None
        for x in PAGE.finditer(h, 0, cstart):
            pm = x
        if not pm or page0 is None or ws0 is None:
            continue
        printed = int(pm.group(1))
        inner = re.sub(r"\s+", " ", strip_html_tags(h[cstart:m.start()], " ")).strip()
        out.append({
            "article": payload.get("title", "?"),
            "id": payload.get("id"),
            "vol": int(pm.group(2)),
            "printed_page": printed,
            "ws_page": int(ws0) + (printed - int(page0)),
            "kind": kind,
            "rendered": "indent" if indented else "flush",
            "math": is_math(inner),
            "anchor": " ".join(words[:ANCHOR_MAX_WORDS]),
            "after": after[:90],
            "block_tail": inner[-46:],
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--sample", type=int, help="take a random sample of this size")
    ap.add_argument("--seed", type=int, default=1911)
    ap.add_argument("--kind", help="only this interrupter kind")
    ap.add_argument("--rendered", choices=("indent", "flush"))
    args = ap.parse_args()

    payloads, failures = load_corpus(strict=False)
    rows: list[dict] = []
    for p in payloads.values():
        rows.extend(sites_in(p))
    if args.kind:
        rows = [r for r in rows if r["kind"] == args.kind]
    if args.rendered:
        rows = [r for r in rows if r["rendered"] == args.rendered]
    rows.sort(key=lambda r: (r["vol"], r["ws_page"], r["anchor"]))
    if args.sample:
        random.seed(args.seed)
        # Stratify by interrupter kind so the rare ones are actually represented.
        by_kind: dict[str, list[dict]] = {}
        for r in rows:
            by_kind.setdefault(r["kind"], []).append(r)
        per = max(1, args.sample // max(1, len(by_kind)))
        picked: list[dict] = []
        for k in sorted(by_kind):
            picked.extend(random.sample(by_kind[k], min(per, len(by_kind[k]))))
        rows = picked[:args.sample]
    Path(args.out).write_text(json.dumps(rows, ensure_ascii=False, indent=1),
                              encoding="utf-8")
    kinds: dict[str, int] = {}
    for r in rows:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    print("payload failures: %d" % len(failures))
    print("sites written   : %d -> %s" % (len(rows), args.out))
    for k in sorted(kinds, key=lambda k: -kinds[k]):
        print("   %-18s %6d" % (k, kinds[k]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
