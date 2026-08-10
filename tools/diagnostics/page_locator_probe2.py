"""Probe v2: locate page-marker positions per article, deriving the signature
from the PIPELINE ITSELF rather than approximating what will render.

v1 approximated `visible_approx()` by hand and got it wrong twice, in opposite
directions:

  * unwrap every template to its last positional arg -> `{{Ts|ma}}` injected
    "ma", `{{Ts|ac|sm92}}` injected "sm92".  41% exact, 55% not found.
  * drop every template whole -> `{{EB1911 Fine Print|<the whole page>}}` and
    `{{Fine block|…}}` deleted the page's entire prose, and `{{asc|B.C.}}` /
    `{{DNB lkpl|…}}` punched holes mid-sentence.  95.5% exact, 2.4% not found.

Deciding which templates emit their content IS the classifier's job.  So this
version runs `process_elements` on a PREFIX of the segment and takes the letters
of its actual output — no guessing, and the answer is by construction the same
answer the real render will give.

Both sides are compared in the MARKER-STREAM representation and cleaned by the
same `_clean()`.  That is deliberate: any imperfection in marker-stripping then
appears identically on both sides and cancels, instead of causing a miss.  (v1
compared a hand-stripped signature against rendered HTML, where `&amp;` put the
letters "amp" into the body and broke otherwise-good matches.)

Oracle: the pre-change snapshot bodies, which still carry `\x01PAGE:N\x01` at
its true position.
"""
from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, "src")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from britannica.db.session import SessionLocal                      # noqa: E402
from britannica.db.models import Article, ArticleSegment            # noqa: E402
from britannica.pipeline.stages.elements import process_elements    # noqa: E402
from britannica.pipeline.stages.elements._context import ElementContext  # noqa: E402

SNAP = Path("data/derived/_flip_snap/post-rebuild-20260809/b")
PAGE_TOK = re.compile(r"\x01PAGE:\d+\x01")
MARKER = re.compile(r"«[^«»]*»")
PLACEHOLDER = re.compile(r"\x03ELEM:\d+\x03")
SIG_LEN = 24
PREFIX = 600
PREFIX_MAX = 3000


def _clean(t: str) -> str:
    """Marker stream -> comparable letters.  Applied to BOTH sides."""
    t = PAGE_TOK.sub(" ", t)
    t = PLACEHOLDER.sub(" ", t)
    for _ in range(3):
        t2 = MARKER.sub(" ", t)
        if t2 == t:
            break
        t = t2
    # Alphabet is [a-z].  Adding digits was TRIED for the numeric-table pages
    # (HYDRAULICS / MICROSCOPE / FUNCTION) on the theory that a letters-only key
    # skips past their opening numbers: it moved exact placement 98.22% -> 98.24%
    # and made the 200+ band slightly WORSE (191 -> 196), because digits are far
    # less distinctive.  Not the cause; reverted.
    return re.sub(r"[^a-z]", "", t.lower())


_OPENERS = {"{{": "}}", "[[": "]]", "{|": "|}"}
_CLOSERS = {"}}", "]]", "|}"}


_TRUTH_TAG = "qzqzpagebreakhereqzqz"       # survives _clean (letters only), never in EB1911


def truth_offsets(raw: str) -> tuple[str, list[int]]:
    """`(cleaned_body, [cleaned offset of each page marker])`, cleaned in ONE pass.

    Computing these piecewise — summing `len(_clean(raw[a:b]))` between markers —
    is WRONG, because `_clean` is not additive: it strips `«…»` structurally, so a
    marker spanning a split survives in the fragment and vanishes in the whole.
    TACHEOMETRY made that visible — piecewise offsets ran to 12,976 in a 5,694
    letter body, and non-monotonically — which manufactured "off by 200+"
    failures out of correctly located pages.  Substituting a letters-only tag and
    cleaning the whole string once keeps every offset in the same coordinate
    system as the body being searched.
    """
    tagged = PAGE_TOK.sub(_TRUTH_TAG, raw)
    cleaned = _clean(tagged)
    offs: list[int] = []
    out: list[str] = []
    i = 0
    while True:
        j = cleaned.find(_TRUTH_TAG, i)
        if j < 0:
            out.append(cleaned[i:])
            break
        out.append(cleaned[i:j])
        offs.append(sum(len(x) for x in out))
        i = j + len(_TRUTH_TAG)
    return "".join(out), offs


def _prefix(seg: str) -> str:
    """First `PREFIX` chars, with any construct the cut left OPEN closed off.

    Extending until things balance (the previous approach) fails whenever the
    real closer is past the cap — a page that opens a wide table whose `|}` is
    thousands of chars away.  The walker then never recognizes the table, so its
    ATTRIBUTES (`border="1" style="border-collapse: collapse"`) fall through as
    body text and poison the signature: BRITISH COLUMBIA scored
    'borderstylebordercollaps', CEPHALOPODA 'tabletrtdcolspanimgebcep'.

    Synthesizing the closers instead gives the walker a well-formed — if
    truncated — construct, so it bounds it and yields the first CELL's text,
    which is exactly the visible content the signature wants.  Closed
    innermost-first from a real scan, not by counting, so nesting is respected.
    """
    head = seg[:PREFIX]
    stack: list[str] = []
    i, n = 0, len(head)
    while i < n:
        two = head[i:i + 2]
        if two in _OPENERS:
            stack.append(_OPENERS[two])
            i += 2
            continue
        if two in _CLOSERS:
            if stack and stack[-1] == two:
                stack.pop()
            i += 2
            continue
        i += 1
    return head + "".join(reversed(stack))


def signature(seg: str, vol: int) -> str:
    try:
        out = process_elements(_prefix(seg), ElementContext(volume=vol))
    except Exception:
        return ""
    return _clean(out)[:SIG_LEN]


MAX_OCC = 32


def locate(body: str, sigs: list[str], expected: list[int],
           gap_penalty: float) -> list[int | None]:
    """Choose a MONOTONIC assignment of pages to occurrences, minimizing total
    deviation from the expected offsets.

    The previous version walked greedily with a `cur` floor, which let ONE bad
    match destroy every page after it: in SEA-POWER a signature matched a later
    recurrence of its own text at 58,249 when it belonged near 40,000, the floor
    jumped, and pages 7-12 all reported "not found" despite being present.  That
    cascade was most of the 332 not-founds.

    Global assignment removes the cascade — a mismatched page costs only itself.
    The expectation is a strong prior, not a hint: pages are near-uniform in
    length (HUNGARY's 37 sit ~7,000 letters apart), so deviation is meaningful.
    A page with no acceptable occurrence takes a GAP (None) at `gap_penalty`,
    so a genuinely unlocatable page does not force a wrong choice on its
    neighbours.
    """
    n = len(sigs)
    cand: list[list[int]] = []
    for sig in sigs:
        occ: list[int] = []
        if sig and len(sig) >= 8:
            st = 0
            while len(occ) < MAX_OCC:
                j = body.find(sig, st)
                if j < 0:
                    break
                occ.append(j)
                st = j + 1
        cand.append(occ)

    # states: last real position -> (cost, chosen path)
    states: dict[int, float] = {-1: 0.0}
    paths: dict[int, list[int | None]] = {-1: []}
    for i in range(n):
        new: dict[int, float] = {}
        newp: dict[int, list[int | None]] = {}

        def offer(key: int, cost: float, path: list[int | None]) -> None:
            if key not in new or cost < new[key]:
                new[key] = cost
                newp[key] = path

        for last, cost in states.items():
            offer(last, cost + gap_penalty, paths[last] + [None])
            for pos in cand[i]:
                if pos < last:
                    continue
                offer(pos, cost + abs(pos - expected[i]), paths[last] + [pos])
        if not new:
            new, newp = {k: v + gap_penalty for k, v in states.items()}, \
                        {k: paths[k] + [None] for k in states}
        if len(new) > 48:                      # prune, keeping the cheapest
            keep = sorted(new, key=lambda k: new[k])[:48]
            new = {k: new[k] for k in keep}
            newp = {k: newp[k] for k in keep}
        states, paths = new, newp

    best = min(states, key=lambda k: states[k])
    return paths[best]


def main() -> int:
    s = SessionLocal()
    man = SNAP.parent / "manifest.tsv"
    meta: dict[str, tuple[int, str]] = {}
    for line in man.read_text(encoding="utf-8").splitlines():
        p = line.split("\t")
        if len(p) >= 5:
            meta[p[0]] = (int(p[3]), p[4])

    arts = (s.query(Article.id, Article.volume, Article.title,
                    Article.page_start, Article.section_name)
            .filter(Article.article_type != "plate").all())
    rows = (s.query(ArticleSegment.article_id,
                    ArticleSegment.sequence_in_article,
                    ArticleSegment.segment_text)
            .order_by(ArticleSegment.article_id, ArticleSegment.sequence_in_article).all())
    segs: dict[int, list[str]] = defaultdict(list)
    for aid, _q, t in rows:
        segs[aid].append(t or "")

    # stable_id -> body path, via the manifest (same key the snapshot used)
    files = {p.stem: p for vd in SNAP.iterdir() if vd.is_dir() for p in vd.glob("*.txt")}
    # article_id -> snapshot stable_id.  Two false starts here, both worth
    # recording: (volume, title) COLLIDES for same-title articles in a volume,
    # and the export index's `stable_id` is a DIFFERENT key (`01-0032-86f7e4`,
    # hash-formed) from the snapshot's (`01-0032-a`, slug-formed).  The only
    # correct source is the snapshot's own derivation, reused verbatim.
    from britannica.util.strings import section_slug

    d = Counter()
    nf = Counter()
    nfex = defaultdict(list)
    worst: list[tuple[str, int, int]] = []
    done = desync = embedded = 0
    for aid, vol, title, _ps, _sn in arts:
        if aid not in segs:
            continue
        slug = section_slug(_sn) if _sn else ""
        if not slug:
            slug = section_slug(title)
        sid = f"{vol:02d}-{_ps:04d}-{slug}"
        if sid not in files:
            continue
        body_raw = files[sid].read_text(encoding="utf-8")
        truth_tokens = list(PAGE_TOK.finditer(body_raw))
        seglist = segs[aid]
        if len(truth_tokens) != len(seglist):
            desync += 1
            continue
        body, truth = truth_offsets(body_raw)
        if len(truth) != len(seglist):
            # The tag was consumed by `_clean` — the page marker sits INSIDE a
            # `«…»` construct, so it is not at a text position at all.  The old
            # piecewise arithmetic hid this by producing a plausible-looking
            # number; surface it instead of scoring against a fiction.
            embedded += 1
            continue
        sigs = [signature(x, vol) for x in seglist]
        expected, run = [], 0
        for x in seglist:
            expected.append(run)
            run += len(_clean(x))
        if run:
            k = len(body) / run
            expected = [int(v * k) for v in expected]

        # A gap is a LAST RESORT, not a competitor to a real match.  Pricing it
        # at half a mean page (the first attempt) made it cheaper than the
        # deviation of a perfectly good match whenever the expected offset was
        # a little off, so the assignment declined 1,092 findable pages —
        # 94.5% exact, worse than the greedy version it replaced.
        #
        # The cheap gap was only needed when a bad match CASCADED through the
        # `cur` floor.  Global assignment already removes the cascade: a
        # mispicked page now costs only itself.  So price the gap above any
        # possible deviation and let it win only when no monotonic candidate
        # exists.  Deviation still ranks the candidates that do exist.
        got = locate(body, sigs, expected, gap_penalty=float(len(body) + 1))
        for i, g in enumerate(got):
            if i == 0:
                d["segment 0 (structural)"] += 1
                continue
            if g is None:
                d["not found"] += 1
                sig = sigs[i]
                if not sig:
                    nf["empty signature (prefix produced no letters)"] += 1
                    k2 = "empty signature (prefix produced no letters)"
                elif len(sig) < 8:
                    nf[f"short signature ({len(sig)} letters)"] += 1
                    k2 = f"short signature ({len(sig)} letters)"
                else:
                    # present but absent from the body: how much of it matches?
                    lead = 0
                    while lead < len(sig) and body.find(sig[:lead + 1]) >= 0:
                        lead += 1
                    k2 = (f"absent, only first {lead} letters occur"
                          if lead else "absent, not even 1 letter matches")
                    nf[k2] += 1
                if len(nfex[k2]) < 4:
                    nfex[k2].append((title, vol, repr(sig), repr(seglist[i][:88])))
                continue
            delta = abs(g - truth[i])
            d["exact (0)" if delta == 0 else "1-5" if delta <= 5 else
              "6-40" if delta <= 40 else "41-200" if delta <= 200 else "200+"] += 1
            if delta > 200 and len(worst) < 12:
                worst.append((title, vol, delta))
        done += 1
        if done % 2000 == 0:
            print(f"  {done} articles…", flush=True)

    searched = sum(v for k, v in d.items() if k != "segment 0 (structural)")
    print(f"\narticles scored          : {done}")
    print(f"skipped (count desync)   : {desync}")
    print(f"skipped (marker INSIDE a «…» construct): {embedded}")
    print(f"segment-0 (structural)   : {d['segment 0 (structural)']}")
    print(f"INTERIOR boundaries searched: {searched}\n")
    for k in ["exact (0)", "1-5", "6-40", "41-200", "200+", "not found"]:
        if d[k]:
            print(f"   {k:12} {d[k]:>7}  ({100*d[k]/searched:.2f}%)")
    if worst:
        print("\nworst misses:")
        for t, v, dd in worst:
            print(f"   v{v:<3} {t[:40]:42} off by {dd}")
    if nf:
        total_nf = sum(nf.values())
        print("\n=== NOT-FOUND breakdown ===")
        for k, v in nf.most_common():
            print(f"   {k:46} {v:>5}  ({100*v/total_nf:.1f}%)")
        for k, rows_ in nfex.items():
            print(f"\n--- {k} ---")
            for t, v, sg, sr in rows_:
                print(f"   v{v:<3} {t[:24]:26} sig={sg[:34]}")
                print(f"        seg={sr[:120]}")
    s.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
