"""WIKI RENDER-ZERO harness for producer refactors (Phase 2 step 2).

Step-2 converts the figure/legend producers to read cells via `_table_grid` so
they handle `<table>` too.  On the `{|` wiki path the conversion must be
render-IDENTICAL.  This captures the rendered body of every wiki-table-bearing
article (the only population a table-producer edit can touch) and diffs two
captures, so a wiki regression shows up as a non-empty diff.

  capture <tag>   -> render all `{|` articles, write tools/_scratch/rz.<tag>.json
  diff <a> <b>    -> report every article whose rendered body differs

Reusing `verify_refactor._shadow_transform` so the render path is identical to
production.  Non-plate.  Flushed."""
import io
import json
import re
import sys
import difflib
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "tools/diagnostics")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from britannica.db.session import SessionLocal
from britannica.db.models import Article, ArticleSegment
from verify_refactor import _shadow_transform


def _out(tag):
    return Path(f"tools/_scratch/rz.{tag}.json")


_POP_LIKE = {"wiki": "%{|%", "html": "%<table%"}


def capture(tag, pop="wiki"):
    """pop: 'wiki' ({|), 'html' (<table>), or 'both'."""
    from sqlalchemy import or_
    s = SessionLocal()
    if pop == "both":
        filt = or_(ArticleSegment.segment_text.like("%{|%"),
                   ArticleSegment.segment_text.like("%<table%"))
    else:
        filt = ArticleSegment.segment_text.like(_POP_LIKE[pop])
    arts = (s.query(Article)
            .join(ArticleSegment, ArticleSegment.article_id == Article.id)
            .filter(filt)
            .distinct().order_by(Article.volume, Article.page_start).all())
    out = {}
    cur = None
    for a in arts:
        if a.article_type == "plate":
            continue
        if a.volume != cur:
            cur = a.volume
            print(f"  vol {cur}", flush=True)
        try:
            out[str(a.id)] = _shadow_transform(s, a)
        except Exception as e:  # noqa: BLE001
            out[str(a.id)] = f"<<ERROR:{type(e).__name__}:{e}>>"
    _out(tag).write_text(json.dumps(out), encoding="utf-8")
    print(f"wrote {len(out)} rendered bodies -> {_out(tag)}", flush=True)


def diff(a, b):
    da = json.loads(_out(a).read_text(encoding="utf-8"))
    db = json.loads(_out(b).read_text(encoding="utf-8"))
    s = SessionLocal()
    keys = set(da) | set(db)
    changed = 0
    for k in sorted(keys, key=int):
        x, y = da.get(k, ""), db.get(k, "")
        if x == y:
            continue
        changed += 1
        art = s.query(Article).filter_by(id=int(k)).first()
        title = f"{art.volume:02d}-{art.page_start:04d} {art.title[:28]}" if art else k
        print(f"\n### CHANGED [{title}] (id {k})")
        for line in list(difflib.unified_diff(
                x.splitlines(), y.splitlines(),
                lineterm="", n=1))[:24]:
            print(line)
    print(f"\n=== {changed} articles changed (of {len(keys)}) ===")


# Marker keyword tokens to ignore when comparing prose word-multisets — they
# are structural (counts shift when a shape's marker syntax changes), not
# content.  Lost CONTENT = lost words minus these.
_MARKER_WORDS = frozenset("""img legend htmltable chem math verse pre outline
page fn ln sh sc br td tr th table vert nbsp emsp ensp imginline span div
center small caps polytonic frac sfrac brace ts hi fs
width height align valign colspan rowspan left right top bottom middle
style class border cellpadding cellspacing bgcolor color scope nowrap px
text font size""".split())
_WORD_RE = re.compile(r"[A-Za-zÀ-ÿ]{2,}")
_PAGE_RE = re.compile(r"\x01[^\x01]*\x01")
_IMG_RE = re.compile(r"\{\{IMG[^:]*:([^|}]+)")


def _words(body):
    from collections import Counter
    c = Counter(w for w in _WORD_RE.findall(_PAGE_RE.sub(" ", body).lower())
                if w not in _MARKER_WORDS)
    return c


def losscheck(a, b):
    """For each changed article report image-marker delta + any REAL prose words
    present in OLD (a) but missing in NEW (b) — the content-loss regression
    signal for the flip."""
    import json
    da = json.loads(_out(a).read_text(encoding="utf-8"))
    db = json.loads(_out(b).read_text(encoding="utf-8"))
    s = SessionLocal()
    n_changed = n_img_gain = n_img_loss = n_wordloss = 0
    losers = []
    for k in da:
        x, y = da[k], db.get(k, "")
        if x == y:
            continue
        n_changed += 1
        oi, ni = set(_IMG_RE.findall(x)), set(_IMG_RE.findall(y))
        if ni - oi:
            n_img_gain += 1
        if oi - ni:
            n_img_loss += 1
        lost = _words(x) - _words(y)
        if lost:
            n_wordloss += 1
            art = s.query(Article).filter_by(id=int(k)).first()
            losers.append((sum(lost.values()),
                           f"{art.volume:02d}-{art.page_start:04d} {art.title[:26]}" if art else k,
                           oi - ni, dict(lost.most_common(8))))
    print(f"changed={n_changed}  img-gained={n_img_gain}  "
          f"img-lost-marker={n_img_loss}  word-loss={n_wordloss}")
    print("\n=== articles with REAL word loss (review) ===")
    for cnt, title, imgmiss, lost in sorted(losers, reverse=True)[:30]:
        print(f"\n[{title}]  lost {cnt} word-instances; missing-imgs={sorted(imgmiss)}")
        print(f"   {lost}")


def main():
    if sys.argv[1] == "capture":
        capture(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "wiki")
    elif sys.argv[1] == "diff":
        diff(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "losscheck":
        losscheck(sys.argv[2], sys.argv[3])


if __name__ == "__main__":
    main()
