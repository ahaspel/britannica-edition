"""Survey the alignment + size source forms on every image in the corpus.

Grounds the align/size metadata task: where align/size actually live (image
params vs wrappers), in what syntax, how often — so the {{IMG:…}} marker format
and the viewer parser match reality.  Scans RAW segment_text across ALL articles
(not just {{IMG:}} ones) so inline-glyph articles (ALPHABET, letter-articles)
are included too.

Read-only; per-volume flushed.
"""
import argparse
import io
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, "src")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from britannica.db.session import SessionLocal
from britannica.db.models import Article, ArticleSegment

_BRACKET = re.compile(r"\[\[(?:File|Image):([^\]]+)\]\]", re.IGNORECASE)
_TMPL = re.compile(
    r"\{\{\s*(img\s*float|figure|FI|raw\s*image)\s*\|([^{}]*(?:\{\{[^{}]*\}\}[^{}]*)*)\}\}",
    re.IGNORECASE)
_SIZE_PX = re.compile(r"^\d+px$", re.IGNORECASE)
_SIZE_WH = re.compile(r"^\d+x\d+px$", re.IGNORECASE)
_SIZE_X = re.compile(r"^x\d+px$", re.IGNORECASE)
_ALIGN_KW = frozenset({"right", "left", "center", "centre", "none"})
_DISPLAY_KW = frozenset({"thumb", "thumbnail", "frame", "framed", "frameless", "border"})
_WRAP = re.compile(
    r"\{\{\s*(center|block\s*center|c|float\s*right|float\s*left|fr|fl)\s*\||"
    r"<div\b[^>]*float\s*:\s*(right|left)|<center\b", re.IGNORECASE)


def _raw(s, aid):
    return "\n".join(seg.segment_text or "" for seg in
                     s.query(ArticleSegment).filter(ArticleSegment.article_id == aid)
                     .order_by(ArticleSegment.sequence_in_article))


def _classify_bracket_params(inner):
    parts = [p.strip() for p in inner.split("|")[1:]]
    size = align = display = "none"
    caption = False
    for p in parts:
        low = p.lower()
        if not p:
            continue
        if low in _ALIGN_KW:
            align = low if align == "none" else align
        elif low in _DISPLAY_KW:
            display = low if display == "none" else display
        elif _SIZE_PX.match(low):
            size = "Npx"
        elif _SIZE_WH.match(low):
            size = "WxHpx"
        elif _SIZE_X.match(low):
            size = "xNpx"
        elif low == "upright" or low.startswith("upright="):
            size = "upright"
        elif "=" in p:  # link= alt= …
            pass
        else:
            caption = True
    return size, align, display, caption


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--volumes", default="all")
    args = ap.parse_args()
    s = SessionLocal()
    if args.volumes == "all":
        vols = [v for (v,) in s.query(Article.volume).distinct()
                .order_by(Article.volume) if v and v < 29]
    else:
        vols = [int(x) for x in args.volumes.split(",")]

    syntax = Counter()
    b_size = Counter(); b_align = Counter(); b_display = Counter()
    b_align_source = Counter()   # where align comes from: param / wrapper / none
    tmpl_keys = Counter()
    wrappers = Counter()
    samples = defaultdict(list)
    n_imgs = 0
    print(f"{'vol':>3} {'imgs':>6}", flush=True)
    for v in vols:
        aids = [a for (a,) in s.query(Article.id)
                .filter(Article.volume == v, Article.article_type == "article").all()]
        vi = 0
        for aid in aids:
            src = _raw(s, aid)
            for m in _BRACKET.finditer(src):
                n_imgs += 1; vi += 1
                syntax["bracket [[File:]]"] += 1
                size, align, display, caption = _classify_bracket_params(m.group(1))
                b_size[size] += 1
                b_display[display] += 1
                # wrapper around the image (look back in same block)
                blk = src[max(0, m.start() - 120):m.start()]
                w = None
                wm = list(_WRAP.finditer(blk))
                if wm:
                    w = wm[-1].group(0).lower().rstrip("|").strip()
                    w = re.sub(r"\s+", " ", w)
                    wrappers[w] += 1
                if align != "none":
                    b_align[align] += 1
                    b_align_source["param keyword"] += 1
                elif w:
                    b_align_source["wrapper"] += 1
                    if len(samples["wrapper-align"]) < 8:
                        samples["wrapper-align"].append(src[m.start()-60:m.end()][:120])
                else:
                    b_align_source["none (default)"] += 1
            for m in _TMPL.finditer(src):
                n_imgs += 1; vi += 1
                kind = re.sub(r"\s+", " ", m.group(1).lower())
                syntax[f"template {{{{{kind}}}}}"] += 1
                for kv in m.group(2).split("|"):
                    k = kv.split("=")[0].strip().lower()
                    if k:
                        tmpl_keys[k] += 1
        print(f"{v:>3} {vi:>6}", flush=True)

    print(f"\n=== images scanned: {n_imgs} ===")
    print("\n-- image syntax --");      [print(f"  {k:24}{v}") for k, v in syntax.most_common()]
    print("\n-- bracket size param --"); [print(f"  {k:12}{v}") for k, v in b_size.most_common()]
    print("\n-- bracket display kw --");  [print(f"  {k:12}{v}") for k, v in b_display.most_common()]
    print("\n-- bracket align: SOURCE --");[print(f"  {k:18}{v}") for k, v in b_align_source.most_common()]
    print("\n-- bracket align keyword (when in param) --");[print(f"  {k:10}{v}") for k, v in b_align.most_common()]
    print("\n-- wrappers around bracket images --");[print(f"  {k:20}{v}") for k, v in wrappers.most_common()]
    print("\n-- template ({{img float}}/{{figure}}) param keys --");[print(f"  {k:14}{v}") for k, v in tmpl_keys.most_common()]
    print("\n-- wrapper-align samples --")
    for sn in samples["wrapper-align"]:
        print(f"  {sn!r}")


if __name__ == "__main__":
    main()
