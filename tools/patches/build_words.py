"""Word patches to Wikisource's pages from the judge's rulings.

Our side is read exactly as the judge read it (`judge_tokens.flat_tokens`,
token-for-token the judge's sequence, with places); Wikisource's side is its
raw wikitext (`raw_tokens.tokens`, markup a barrier no patch may hold).
Each judged site is found where its Wikisource words stand among the agreed
words the judge saw either side (`locate`), or not patched.

  word     a site ruled "ours" outside our formulas: Wikisource's raw span ->
           our words as printed on our page (case and punctuation between
           them); both plain text — no formatting, no markup, no line break
  formula  (superseded by build_formulas.py: `merge` keeps only the word
           patches; the formula runs are still made here because overlaps
           are settled against them — the first stands — and removing them
           would change which word patches the shipped patches.json holds)

Writes words.json; prints the tally.
Usage: build_words.py --loose [--why] [--fwhy]  (book root)"""
import copy
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from paths import DISPUTES, RULINGS, WORK, reading
from patterns import RAW_MATH, WORD2
from judge_tokens import flat_tokens
from raw_tokens import FORMAT, regions, tokens

from wikikit.scan import supplied
from wikikit.source_pages import fetched_text

CTX = 6
#: --loose: OCR-tolerant anchors, plain spans across lines, short garbles inside salad
LOOSE = "--loose" in sys.argv
#: how near (share of the page) a repeated anchor must stand to where ours does
WINDOW = 0.05
DEBUG = "--debug" in sys.argv
DEBUG_OUT = []
FWHY = []
#: ordinary words: never in a formula's letter salad
COMMON = set("""a an and are as at be been but by can for from had has have he his if in into is it its
may no not of on or so such than that the their then there these they this to was we were when where
which while who will with would""".split())
MATH_RAW = RAW_MATH


def _near(a, b):
    """OCR-tolerant word match (--loose): equal, or both 4+ letters and
    nearly the same ("whieh" / "which")."""
    if a == b:
        return True
    if len(a) < 4 or len(b) < 4 or abs(len(a) - len(b)) > 2:
        return False
    from difflib import SequenceMatcher
    return SequenceMatcher(None, a, b).ratio() >= 0.8


def find(toks, pat, fuzzy=False):
    """Where the token texts `pat` stand in a row; with `fuzzy` (only when
    the exact search finds nothing), OCR-garbled words match too."""
    n, out = len(pat), []
    if not n:
        return out
    for i in range(len(toks) - n + 1):
        if toks[i][0] == pat[0] and all(toks[i + k][0] == pat[k] for k in range(1, n)):
            out.append(i)
    if out or not (fuzzy and LOOSE):
        return out
    for i in range(len(toks) - n + 1):
        if all(_near(toks[i + k][0], pat[k]) for k in range(n)):
            out.append(i)
    return out


def anchored(toks, before, mid, after):
    """The one place where `mid` stands with the most context either side
    that is still found exactly once: 6 tokens a side down to 2."""
    for n in (6, 5, 4, 3, 2):
        b, a = before[-n:], after[:n]
        if len(b) < min(n, len(before)) or len(a) < min(n, len(after)):
            continue
        hits = find(toks, b + mid + a, fuzzy=True)
        if len(hits) == 1:
            return hits[0] + len(b)
        if not hits:
            continue
        if len(hits) > 1:
            return None
    return None


def span_between(toks, pre, post, limit, near=None):
    """The one (end of `pre`, start of `post`) pair with `post` following
    `pre` within `limit` tokens.  Several: `near` (where on the page, as a
    share of its tokens, ours stands) picks the one within WINDOW of it, if
    exactly one is."""
    pairs = []
    for i in find(toks, pre, fuzzy=True):
        j0 = i + len(pre)
        for j in find(toks[j0:j0 + limit], post, fuzzy=True):
            pairs.append((j0 - 1, j0 + j))
            break
    if len(pairs) == 1:
        return pairs[0]
    if near is not None and pairs:
        close = [x for x in pairs if abs(x[0] / max(1, len(toks)) - near) < WINDOW]
        if len(close) == 1:
            return close[0]
    return None


def align(O, W):
    """Our token index -> Wikisource's, for tokens in a matching run of 2+:
    the whole page aligned once, as the disputes themselves were found."""
    from difflib import SequenceMatcher
    sm = SequenceMatcher(None, [t[0] for t in O], [t[0] for t in W], autojunk=False)
    m = {}
    for b in sm.get_matching_blocks():
        if b.size >= 2:
            for q in range(b.size):
                m[b.a + q] = b.b + q
    return m


def aligned_span(amap, O, lo, hi, plain_only=True):
    """Wikisource's tokens for our O[lo:hi]: the matched tokens of ours either
    side (outside our formulas, with `plain_only`) -> (W index of the one
    before, W index of the one after); None when a side has none."""
    p = lo - 1
    while p >= 0 and (p not in amap or (plain_only and O[p][3] is not None)):
        p -= 1
    n = hi
    while n < len(O) and (n not in amap or (plain_only and O[n][3] is not None)):
        n += 1
    if p < 0 or n >= len(O) or amap[n] <= amap[p]:
        return None
    return p, n, amap[p], amap[n]


NEAR = 12


def locate(W, ws, before, after):
    """Where the site's Wikisource words stand: each place `ws` occurs (an
    insertion: each place before's last word meets after's first), scored by
    how many of the agreed words before and after it stand within NEAR
    tokens on their own side.  The best place, if it has 2+ each side and
    beats every other place; else None."""
    n = len(ws)
    if n:
        cands = find(W, ws)
    else:
        if not before or not after:
            return None
        cands = [i for i in range(1, len(W)) if W[i - 1][0] == before[-1] and W[i][0] == after[0]]

    def side(window, words):
        have = Counter(t[0] for t in window)
        return sum((Counter(words) & have).values())

    scored = []
    for i in cands:
        left = side(W[max(0, i - NEAR):i], before)
        right = side(W[i + n:i + n + NEAR], after)
        scored.append((min(left, right), left + right, i))
    scored.sort(reverse=True)
    if not scored or scored[0][0] < 2:
        return None
    if len(scored) > 1 and scored[1][:2] == scored[0][:2]:
        return None
    return scored[0][2]


def barrier(text):
    return any(k == "barrier" for _, _, k in regions(text))


def main():
    dis = json.loads((DISPUTES).read_text(encoding="utf-8"))
    rul = json.loads((RULINGS).read_text(encoding="utf-8"))
    patches, tally = {}, Counter()
    for stem, rec in dis.items():
        d = json.loads((reading(stem)).read_text(encoding="utf-8"))
        v, p = d["volume"], d["page_number"]
        ours_text = supplied.name_sections(copy.deepcopy(d))["raw_text"]
        plain, O, formulas = flat_tokens(v, p, ours_text)
        raw_math = MATH_RAW.findall(ours_text)
        if len(raw_math) != len(formulas):
            raw_math = None
        ws_raw = fetched_text(v, p) or ""
        W = [t for t in tokens(ws_raw) if t[3] != "barrier"]
        amap = align(O, W)
        rulings = rul.get(stem, {})
        page, by_formula = [], defaultdict(list)
        for i, s in enumerate(rec["sites"]):
            verdict = rulings.get(str(i))
            before, after = s["before"].split(), s["after"].split()
            ws, ours = s["ws"].split(), s["ours"].split()
            hits = find(O, before + ours + after)
            if len(hits) != 1:
                tally["context not found once (ours)"] += 1
                continue
            k = hits[0] + len(before)
            near = O[k:k + len(ours)] if ours else O[max(0, k - 1):k + 1]
            fs = {t[3] for t in near if t[3] is not None}
            if fs:
                for f in fs:
                    by_formula[f].append(verdict)
                continue
            if verdict != "ours":
                continue
            # Wikisource's place: where its words for the site stand among
            # the agreed words the judge saw either side (`locate`)
            wb = [t[0] for t in O[max(0, k - CTX):k] if t[3] is None]
            wa = [t[0] for t in O[k + len(ours):k + len(ours) + CTX] if t[3] is None]
            j = locate(W, ws, before, after)
            if j is None:
                if ws and not find(W, ws):
                    # Wikisource's page no longer has the words the judge saw
                    # there (edited since, or never in its wikitext): nothing to patch
                    tally["word: Wikisource's words not on its page now"] += 1
                    continue
                tally["word: Wikisource's place not found"] += 1
                if "--why" in sys.argv and len(DEBUG_OUT) < 25:
                    DEBUG_OUT.append((stem, f"ws={ws} ours={ours}", before, after, len(find(W, ws))))
                continue
            if not ws:
                # a word Wikisource dropped: ours set in before the next
                # agreed word, with a space; never where markup stands between
                if j == 0 or j >= len(W) or not wb or not wa or len(ours) > 3:
                    tally["word: insertion without both anchors"] += 1
                    continue
                gap = ws_raw[W[j - 1][2]:W[j][1]]
                new = plain[O[k][1]:O[k + len(ours) - 1][2]]
                if barrier(gap) or FORMAT.search(gap) or "\n" in gap or "«" in new or "\n" in new \
                        or not gap.strip(" ") == "":
                    tally["word: insertion not between plain words"] += 1
                    continue
                at = W[j][1]
                page.append({"kind": "word", "start": at, "end": at, "old": "", "new": new + " "})
                continue
            if not ours:
                # a stray of Wikisource's OCR: removed with the space before it
                start, end = W[j][1], W[j + len(ws) - 1][2]
                old = ws_raw[start:end]
                pre_gap = ws_raw[W[j - 1][2]:start] if j else ""
                if barrier(old) or FORMAT.search(old) or "{{" in old or "\n" in old or any(t in COMMON for t in ws) \
                        or pre_gap != " " or not re.match(r"[\s,.;:)]", ws_raw[end:end + 1] or " "):
                    tally["word: deletion not plain"] += 1
                    continue
                page.append({"kind": "word", "start": start - 1, "end": end, "old": " " + old, "new": ""})
                continue
            start, end = W[j][1], W[j + len(ws) - 1][2]
            old = ws_raw[start:end]
            new = plain[O[k][1]:O[k + len(ours) - 1][2]]
            if barrier(old) or FORMAT.search(old) or "{{" in old or "}}" in old or "\n" in old or "\n" in new \
                    or "«" in new:
                tally["word: markup in span (not patched)"] += 1
                continue
            page.append({"kind": "word", "start": start, "end": end, "old": old, "new": new})
        # formulas standing in a run (nothing but formulas between them) are
        # one unit: Wikisource's span for the run -> our run, raw
        spans = [m.span() for m in MATH_RAW.finditer(ours_text)]
        runs, cur, prev_f = [], [], None
        for t in O:
            if t[3] is None:
                if cur:
                    runs.append(cur)
                cur, prev_f = [], None
            elif t[3] != prev_f:
                cur.append(t[3])
                prev_f = t[3]
        if cur:
            runs.append(cur)
        for run in runs:
            verdicts = [x for f in run for x in by_formula.get(f, [])]
            if not verdicts:
                continue
            if raw_math is None or len(spans) != len(formulas):
                tally["formula: page's formulas not matched"] += 1
                continue
            if any(x != "ours" for x in verdicts):
                tally["formula run: a site not ruled ours"] += 1
                continue
            idx = [n for n, t in enumerate(O) if t[3] in run]
            ja, jb = idx[0], idx[-1] + 1
            pre, q = [], ja - 1
            while q >= 0 and O[q][3] is None and len(pre) < 3:
                pre.insert(0, O[q][0])
                q -= 1
            post, q = [], jb
            while q < len(O) and O[q][3] is None and len(post) < 3:
                post.append(O[q][0])
                q += 1
            if not pre or not post or len(pre) + len(post) < 4:
                tally["formula run: no plain words either side"] += 1
                if DEBUG and len(DEBUG_OUT) < 12:
                    ra0, rb0 = spans[min(run)][0], spans[max(run)][1]
                    DEBUG_OUT.append((stem, pre, post, ours_text[max(0, ra0 - 120):rb0 + 120]))
                continue
            # Wikisource's span, placed two ways — the context searched for
            # (`span_between`), and the page's alignment (`aligned_span`): the
            # first that passes every check below stands
            limit = 4 * (jb - ja) + 12
            al = aligned_span(amap, O, ja, jb)
            hits = [span_between(W, pre, post, limit, near=ja / max(1, len(O))),
                    None if al is None or al[3] - al[2] > limit else (al[2], al[3])]
            hits = [h for n, h in enumerate(hits) if h is not None and h not in hits[:n]]
            if not hits:
                tally["formula run: context not found once (Wikisource)"] += 1
                continue

            def ws_side(hit):
                """(start, end, old) of Wikisource's span at `hit`, or why not."""
                inner = W[hit[0] + 1:hit[1]]
                if not inner:
                    return "no Wikisource text to replace"
                # letter salad holds no ordinary word: one there means the span's
                # edges are wrong ("= o, p is" took "is": vol 1 p. 675)
                # --loose: a one- or two-letter "word" INSIDE the salad (a mangled
                # sign) does not stop it; at either edge, where a real word would
                # be lost, it still does — and the anchors must be 2+ words a side
                # a one-letter "word" is a formula's letter ("cos a cos b": vol
                # 27 p. 275) anywhere in it, when the anchors are 2+ words a side
                common = [n for n, t in enumerate(inner) if t[0] in COMMON]
                if common and not (LOOSE and len(pre) >= 2 and len(post) >= 2
                                   and all(len(inner[n][0]) == 1 or (len(inner[n][0]) <= 2 and 0 < n < len(inner) - 1)
                                           for n in common)):
                    return "Wikisource span holds an ordinary word"
                # the WHOLE gap between the agreed words, both sides: Wikisource's
                # salad includes signs that are not tokens ("m-\\-\\," left "-\\-\\,"
                # behind: vol 25 p. 680); each gap keeps its own spacing at the
                # edges, and ours its own punctuation
                g0, g1 = W[hit[0]][2], W[hit[1]][1]
                gap = ws_raw[g0:g1]
                start = g0 + (len(gap) - len(gap.lstrip()))
                end = g1 - (len(gap) - len(gap.rstrip()))
                if end <= start:
                    return "no Wikisource text to replace"
                # a line's own markup stays: an indent (":") or list mark
                while start < end and ws_raw[start] in ":*#;" and (start == 0 or ws_raw[start - 1] == "\n"):
                    start += 1
                while start < end and ws_raw[start] == " ":
                    start += 1
                old = ws_raw[start:end]
                # --loose: OCR breaks salad over lines — allowed when every line is
                # plain (no line-start markup: indent, list, table row) and no
                # paragraph break
                # a displayed formula, OCR'd, is paragraphs of salad: allowed
                # across paragraph breaks too — the span holding no word (above)
                over_lines = "\n" in old and not (
                    LOOSE and not re.search(r"\n\s*[:*#;|!{]", old))
                if over_lines or old.count("{{") != old.count("}}"):
                    return "Wikisource span runs over lines or splits a template"
                if barrier(old) or len(old.strip()) > 4 * len(ours_text[spans[min(run)][0]:spans[max(run)][1]]) + 120:
                    return "Wikisource span holds markup or runs long"
                return start, end, old

            tried = [ws_side(h) for h in hits]
            ok = [x for x in tried if isinstance(x, tuple)]
            if not ok:
                tally["formula run: " + tried[0]] += 1
                if "--fwhy" in sys.argv:
                    h = hits[0]
                    FWHY.append({"stem": stem, "why": tried[0], "pre": pre, "post": post,
                                 "ws": ws_raw[W[h[0]][1]:W[h[1]][2]][:300],
                                 "ours": ours_text[spans[min(run)][0]:spans[max(run)][1]][:300]})
                continue
            start, end, old = ok[0]
            ra, rb = spans[min(run)][0], spans[max(run)][1]
            # our gap: the run with the punctuation either side of it, up to
            # our agreed words — never past markup
            stop = "<>{}[]|'\n"
            while ra > 0 and not ours_text[ra - 1].isalnum() and ours_text[ra - 1] not in stop:
                ra -= 1
            while rb < len(ours_text) and not ours_text[rb].isalnum() and ours_text[rb] not in stop:
                rb += 1
            ours_run = ours_text[ra:rb].strip()
            between = MATH_RAW.sub(" ", ours_run)
            if barrier(between) or WORD2.search(between):
                tally["formula run: words between our formulas"] += 1
                continue
            # outside our formulas: spaces and ordinary punctuation only —
            # never a piece of our own markup ("|<math>…</math>}}" from
            # our {{block center|…}}: vol 27 p. 944)
            if not re.fullmatch(r"[\s,.;:()\-–—=+/!?·0-9…]*", between):
                tally["formula run: markup around our formulas"] += 1
                continue
            if barrier(old) or ("\n\n" in old.strip() and not LOOSE) or len(old.strip()) > 4 * len(ours_run) + 120:
                tally["formula run: Wikisource span holds markup or runs long"] += 1
                continue
            page.append({"kind": "formula", "start": start, "end": end, "old": old,
                         "new": ours_run, "formulas": len(run)})
        page.sort(key=lambda x: (x["start"], x["end"]))
        clean, last = [], -1
        for x in page:
            if x["start"] < last:
                tally["overlap (not patched)"] += 1
                continue
            clean.append(x)
            last = x["end"]
        for x in clean:
            tally[f"{x['kind']} patches"] += 1
        if clean:
            patches[stem] = clean
    if FWHY:
        (WORK / "words_why.json").write_text(json.dumps(FWHY, indent=1, ensure_ascii=False), encoding="utf-8")
    (WORK / "words.json").write_text(json.dumps(patches, indent=1, ensure_ascii=False), encoding="utf-8")
    for x in DEBUG_OUT:
        print("DEBUG", x[0], x[1], x[2], repr(x[3]))
    print(len(patches), "pages patched")
    for k2, n in sorted(tally.items()):
        print(f"  {k2}: {n}")


if __name__ == "__main__":
    main()
