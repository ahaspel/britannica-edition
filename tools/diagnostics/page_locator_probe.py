"""Probe: can page-marker positions be LOCATED at render time, per article,
from facts we already hold — with nothing carried through the pipeline?

The dissolution being tested ([[feedback_dissolve_dont_fix]]): if page position
never enters the content stream, no recognizer can trip over it.  The cost is
that the marker's place in the OUTPUT must be found at the end.  This measures
how well that works, using the baked corpus as an oracle: every article already
carries its markers in their true positions, so `located` can be scored against
`truth` exactly.

Inputs per article — both already available at export time, nothing stored:
  * the rendered body                (transformed text)
  * its ArticleSegments, in order    (each page's raw contribution)

`segment_text` is ALREADY post-preprocess (make_stream -> preprocess ->
super_detect -> segments), so the signature only has to survive the ELEMENT
pipeline, not preprocessing.

Scoring is in LETTERS (a-z), which is the coordinate the transform preserves:
markup changes, letters and their order do not.
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, "src")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from britannica.db.session import SessionLocal          # noqa: E402
from britannica.db.models import Article, ArticleSegment  # noqa: E402

TAG = re.compile(r"<[^>]+>")
PAGE_TOK = re.compile(r"\x01PAGE:\d+\x01")
# A rendered page marker: an <a> (or <span>, for EPUB) with no text content.
MARK = re.compile(r'<a class="page-marker[^"]*"[^>]*?data-page="(\d+)"[^>]*></a>')

SIG_LEN = 24


def letters(t: str) -> str:
    return re.sub(r"[^a-z]", "", t.lower())


def visible_approx(t: str) -> str:
    """Approximate what the ELEMENT pipeline will leave as visible text.

    Not exact — that would require running the pipeline — but every construct
    dropped here is one that contributes no letters to the render, and every
    construct unwrapped here keeps the letters that do.
    """
    t = PAGE_TOK.sub(" ", t)
    t = re.sub(r"<ref[^>]*>.*?</ref>", " ", t, flags=re.S | re.I)   # → footnote, moves away
    t = re.sub(r"<ref[^>]*/>", " ", t, flags=re.I)
    t = re.sub(r"<!--.*?-->", " ", t, flags=re.S)
    t = re.sub(r"\[\[File:[^\]]*\]\]", " ", t, flags=re.I)          # image, no prose
    # Templates are DROPPED WHOLE, never unwrapped.  Unwrapping to the last
    # positional arg looks smarter and is much worse: `{{sc|Foo}}` → "Foo" is
    # right, but `{{Ts|ma}}` → "ma" and `{{Ts|ac|sm92}}` → "sm92" inject STYLE
    # arguments that never render.  For a signature a missing letter is
    # survivable (the window slides past it); an INVENTED letter is fatal (the
    # signature matches nothing).  Measured: unwrapping dropped corpus accuracy
    # from ~98% exact to 41%, with 55% not found.  Conservative wins.
    for _ in range(4):
        t = re.sub(r"\{\{[^{}]*\}\}", " ", t)
    t = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", t)         # wikilink → display
    t = re.sub(r"«[^»]*»", " ", t)                                  # preprocess quote markers
    t = re.sub(r"<[^>]+>", " ", t)
    # Table syntax lines go WHOLE for the same reason: the cell text is worth
    # less than the attribute letters (`style`, `colspan`, `align`) are harmful.
    t = re.sub(r"^\s*[|!{].*$", " ", t, flags=re.M)
    return t


def signature(seg: str) -> str:
    return letters(visible_approx(seg))[:SIG_LEN]


def locate(body_letters: str, sigs: list[str], expected: list[int]) -> list[int | None]:
    """Monotonic, expectation-guided search.  For each page in order, take the
    occurrence of its signature nearest the expected offset among those at or
    after the previous anchor.  None when the signature cannot be found."""
    out: list[int | None] = []
    cur = 0
    for i, sig in enumerate(sigs):
        if not sig or len(sig) < 8:
            out.append(None)
            continue
        best, j = None, body_letters.find(sig, cur)
        while j >= 0:
            if best is None or abs(j - expected[i]) < abs(best - expected[i]):
                best = j
            nxt = body_letters.find(sig, j + 1)
            # stop scanning once we are moving away from the expectation
            if nxt < 0 or (best is not None and nxt - expected[i] > abs(best - expected[i])):
                break
            j = nxt
        out.append(best)
        if best is not None:
            cur = best + 1
    return out


def main() -> int:
    s = SessionLocal()
    idx = json.load(open("data/derived/articles/index.json", encoding="utf-8"))
    entries = idx if isinstance(idx, list) else (idx.get("articles") or list(idx.values())[0])
    byid = {e["id"]: e for e in entries if "id" in e}

    rows = (s.query(ArticleSegment.article_id,
                    ArticleSegment.sequence_in_article,
                    ArticleSegment.segment_text)
            .order_by(ArticleSegment.article_id, ArticleSegment.sequence_in_article).all())
    segs: dict[int, list[str]] = defaultdict(list)
    for aid, _seq, txt in rows:
        segs[aid].append(txt or "")

    arts = (s.query(Article.id, Article.volume, Article.title)
            .filter(Article.article_type != "plate").all())

    d = Counter()
    worst: list[tuple[str, int, int]] = []
    desync = 0
    done = 0
    for aid, vol, title in arts:
        e = byid.get(aid)
        if not e or aid not in segs:
            continue
        path = f"data/derived/articles/{e['filename']}"
        if not os.path.exists(path):
            continue
        html = json.load(open(path, encoding="utf-8")).get("rendered_html", "")
        if "page-marker" not in html:
            continue

        # TRUTH: letter-offset of each real marker
        truth, pos, last = [], 0, 0
        for m in MARK.finditer(html):
            pos += len(letters(TAG.sub(" ", html[last:m.start()])))
            truth.append(pos)
            last = m.end()
        seglist = segs[aid]
        if len(truth) != len(seglist):
            desync += 1
            continue

        body_letters = letters(TAG.sub(" ", html))
        sigs = [signature(x) for x in seglist]
        # expectation: cumulative visible letters of preceding segments
        expected, run = [], 0
        for x in seglist:
            expected.append(run)
            run += len(letters(visible_approx(x)))
        # scale expectation into the actual body length (transform shrinks text)
        if run:
            k = len(body_letters) / run
            expected = [int(v * k) for v in expected]

        got = locate(body_letters, sigs, expected)
        for i, g in enumerate(got):
            if i == 0:
                # Segment 0 is NOT a search problem.  Its marker sits at the start
                # of the body by definition, which is a structural position.  Its
                # raw also opens with the article TITLE, which `produce_title` cuts
                # out of the body — so a signature built from it can never match,
                # and scoring it as a miss measures nothing.
                d["segment 0 (structural, not searched)"] += 1
                continue
            if g is None:
                d["not found (fallback used)"] += 1
                continue
            delta = abs(g - truth[i])
            d["exact (0)" if delta == 0 else "1-5" if delta <= 5 else
              "6-40" if delta <= 40 else "41-200" if delta <= 200 else "200+"] += 1
            if delta > 200 and len(worst) < 12:
                worst.append((title, vol, delta))
        done += 1
        if done % 4000 == 0:
            print(f"  {done} articles…", flush=True)

    tot = sum(d.values())
    print(f"\narticles scored                    : {done}")
    print(f"articles skipped (marker/segment desync): {desync}")
    print(f"page markers scored                : {tot}\n")
    for k in ["exact (0)", "1-5", "6-40", "41-200", "200+", "not found (fallback used)"]:
        if d[k]:
            print(f"   {k:28} {d[k]:>7}  ({100*d[k]/tot:.2f}%)")
    if worst:
        print("\nworst misses:")
        for t, v, dd in worst:
            print(f"   v{v:<3} {t[:40]:42} off by {dd}")
    s.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
