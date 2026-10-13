"""Formula patches to Wikisource's pages, placed by the PROSE the two pages
share — never by the formula's own letters, which on an OCR page are salad.

  1. Both pages' anchors: tokens of running text (`raw_tokens.tokens`, raw
     positions) that are real words — 3+ letters, 5+ times in the corpus —
     and the structure both pages set (`_ANCHOR`: footnotes, images, margin
     headings, sections, tables).  OCR salad makes almost no real word, so
     the two streams align cleanly.
  2. Each formula of ours (a <math> block) lies between two aligned anchors.
     Formulas sharing the same two are one patch.
  3. The patch: Wikisource's raw text between those two words -> ours between
     them (our formulas, our display wrapper, and any words beside them,
     which ours reads better — the judge's sites there all ruled ours).

Refused — Wikisource's text stays — when:
  - Wikisource's span holds structure: a footnote, link, image, table,
    heading, section, or any template not part of a formula or a wrapper
  - our span holds any markup but <math>, sub/sup, italics, and the display
    wrappers
  - Wikisource's span holds a real word ours there does not (a word lost)
  - a site the judge did NOT rule ours stands in Wikisource's span
  - either span runs long (Wikisource's > 4x ours + 200 chars; ours > PROSE_MAX
    prose words beside its formulas)

Writes formulas.json; prints the tally.
Usage: build_formulas.py [--why]  (book root)"""
import copy
import json
import re
import sys
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from paths import DISPUTES, RULINGS, VOCAB, WORK, reading
from patterns import RAW_MATH, TEMPLATE_NAME, WORD3, blank_math
from raw_tokens import tokens
from build_words import find, locate

from wikikit.scan import supplied
from wikikit.scan.carry import markup_balance
from wikikit.scan.patches import balanced
from wikikit.source_pages import fetched_text

VOCAB_FILE = VOCAB
WHY = []
#: rulings against our reading at a site: a patch over it is refused.  The
#: judge's other labels set a site aside without a verdict on our text —
#: "moved" (an assembly order), "caption", "margin" (a margin heading's words
#: in Wikisource's lines)
AGAINST = {"ws", "neither", "unsure"}
#: our real words a formula patch may carry beside its formulas — our reading
#: of the OCR prose about them; the filter refuses any patch that makes a
#: disagreement with our reading, the guard against a span run wild
PROSE_MAX = 40
#: templates that are part of a formula, or present one: replaceable
FORMULA_T = {"polytonic", "greek", "eb1911 tfrac", "sfrac", "tfrac", "frac", "sub", "sup", "overline", "em",
             "gap", "ne", "uc", "brace2", "=", "...", "spaces", "nop", "hi", "fs", "lb-", "asc", "csc",
             "subsup", "su", "sqrt", "radic", "math", "mvar", "var", "ell", "prime", "√", "abs", "e",
             "center", "c", "centre", "block center", "nowrap", "larger", "smaller", "x-larger", "dual line",
             "ditto", "sm", "nowrap begin", "nowrap end", "underline", "ts", "brace", "rbrace", "lbrace",
             "bigg", "big", "huge", "constrained", "xx-larger", "x-smaller", "sfrac nobar"}


def vocabulary():
    if VOCAB_FILE.exists():
        return set(json.loads(VOCAB_FILE.read_text(encoding="utf-8")))
    from wikikit.export.corpus import load_corpus
    corpus, _ = load_corpus()
    c = Counter()
    for a in corpus.values():
        c.update(w.lower() for w in WORD3.findall(a.get("body", "")))
    v = sorted(w for w, n in c.items() if n >= 5)
    VOCAB_FILE.write_text(json.dumps(v), encoding="utf-8")
    return set(v)


#: html elements that are structure (an OCR "<j>" is not one)
STRUCTURE_TAGS = {"ref", "section", "noinclude", "includeonly", "poem", "div", "p", "table", "tr", "td", "th",
                  "ul", "ol", "li", "dl", "dd", "dt", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "img", "references",
                  "gallery", "pre", "blockquote", "score", "chem", "ce", "timeline", "imagemap"}
_TABLE = re.compile(r"\{\|[\s\S]*?\n\|\}|<table[\s\S]*?</table>", re.I)


def _formula_table(t: str) -> bool:
    """A table laying out a formula (FUNCTION sets its equations so): no
    rules or border, no class, no image, no footnote — under the formula
    exception (2026-10-12) it gives way to our <math>."""
    head = t.split("\n", 1)[0] if t.startswith("{|") else re.match(r"<table[^>]*>", t, re.I).group(0)
    return not re.search(r"border|rules|class", head, re.I) \
        and not re.search(r"\[\[\s*(?:File|Image)|Css image crop|raw image|<ref", t, re.I)


def structure(span: str) -> str | None:
    """What structure a span holds, or None: anything but formula pieces."""
    tables = _TABLE.findall(span)
    if any(not _formula_table(t) for t in tables):
        return "structure table"
    span = _TABLE.sub(" ", span)
    if re.search(r"<ref|<section|<noinclude|\[\[|\{\||\|\}|^==|<poem|<div", span, re.M | re.I):
        return "structure"
    for m in TEMPLATE_NAME.finditer(span):
        if m.group(1).strip().lower() not in FORMULA_T:
            return "template " + m.group(1).strip()[:30]
    for m in re.finditer(r"</?([a-zA-Z][a-zA-Z0-9]*)[\s/>]", span):
        if m.group(1).lower() in STRUCTURE_TAGS:
            return "tag " + m.group(1)
    return None


_OPENER = re.compile(r"\{\{\s*[^|{}\n]*\|")


def edges(text: str, a: int, b: int) -> tuple[int, int]:
    """a..b less, at either edge, what belongs to the paragraph around it:
    whitespace, the punctuation before, a `}}` closing what opened before
    it, a `{{name|` opening what closes after it (`.}}\\n\\n{{smaller block|`
    between a formula and the next paragraph's first word).  Braces are
    counted with formulas blanked: TeX's `}}` closes no template."""
    text = blank_math(text)
    while True:
        a0, b0 = a, b
        while a < b and (text[a].isspace() or text[a] in ";,.:—"):
            a += 1
        if text.startswith("}}", a) and a + 2 <= b:
            a += 2
        m = _OPENER.match(text, a, b)
        if m and balanced(text, a, "{{", "}}") > b:
            a = m.end()
        while b > a and text[b - 1].isspace():
            b -= 1
        if text[a:b].endswith("}}") and text[a:b].count("{{") < text[a:b].count("}}"):
            b -= 2
        m = re.search(r"\{\{\s*[^|{}\n]*\|\s*\Z", text[a:b])
        if m:
            b = a + m.start()
        if (a, b) == (a0, b0):
            return a, b


#: Structure both pages set at the same place, an anchor as good as a word:
#: a formula's span ends at it instead of running through it (a figure, a
#: margin heading or a footnote between a formula and the next shared word
#: had refused the patch: 2026-10-13, 410 formulas)
_ANCHOR = [(re.compile(r"<ref\b", re.I), "‹ref›"),
           (re.compile(r"\[\[\s*(?:File|Image)\s*:|\{\{\s*(?:Css image crop|raw image)\b", re.I), "‹img›"),
           (re.compile(r"\{\{\s*(?:EB1911 Shoulder Heading|EB9 Margin Note)", re.I), "‹sh›"),
           (re.compile(r"<section\b", re.I), "‹sec›"),
           (re.compile(r"\{\||<table\b", re.I), "‹table›")]


def anchor_key(text: str, tok, vocab: set) -> str | None:
    """A token's key for the alignment: a real word, or a piece of structure
    (`_ANCHOR`); None for anything else (salad, other markup)."""
    if tok[3] == "word":
        return tok[0] if len(tok[0]) >= 3 and tok[0] in vocab else None
    if tok[3] == "barrier":
        piece = text[tok[1]:tok[2]]
        return next((k for rx, k in _ANCHOR if rx.match(piece)), None)
    return None


_DISPLAY = re.compile(r"\{\{\s*(?:block center|c|center|centre)\s*\|")


def displays(text: str) -> list[tuple[int, int]]:
    """Our displayed formulas' lines: a centring wrapper holding a <math>.
    Their words ("(n even)", "from equation (2)") are no anchors — an edge
    there would cut the line's wrapper in two (2026-10-13: 453 formulas)."""
    blank = blank_math(text)
    out = []
    for m in _DISPLAY.finditer(blank):
        end = balanced(blank, m.start(), "{{", "}}")
        if "<math" in blank[m.start():end]:
            out.append((m.start(), end))
    return out


def paragraph_end(ours: str, n0: int, n1: int, ws: str, w0: int, w1: int) -> tuple[int, int]:
    """Both spans ended at the paragraph break before the next paragraph,
    when ours runs on into a paragraph it opens and does not close
    (`…</math>.\\n\\n{{smaller block|It`: the next shared word, "It", too short
    to anchor) — and Wikisource's span has a paragraph break to end at.
    Else unchanged (the balance check then refuses)."""
    span = ours[n0:n1]
    m = None
    for m in re.finditer(r"\n\s*\n\s*\{\{\s*[^|{}\n]*\|", span):
        pass
    if not m or balanced(blank_math(ours), n0 + m.end() - len(m.group(0).lstrip()), "{{", "}}") <= n1:
        return n1, w1
    k = ws.rfind("\n\n", w0, w1)
    if k < 0:
        return n1, w1
    return n0 + len(span[:m.start()].rstrip()), len(ws[:k].rstrip())


def prose(toks, vocab, text, inside=()):
    """The anchor tokens of a page: (index, key), words and structure — none
    inside the spans `inside`."""
    keyed = ((n, anchor_key(text, t, vocab)) for n, t in enumerate(toks)
             if not any(a <= t[1] < b for a, b in inside))
    return [(n, k) for n, k in keyed if k]


def words_of(span, vocab, ours=False):
    """The real words a span prints: markup's own names and settings are
    not (`{{Polytonic|`, `<span style=…>`, `font-size=100%`).  Our formulas
    count every letter run in them (\\sin, \\text{N}, ABC) — what they may
    stand for in Wikisource's salad; Wikisource's own <math> prints none."""
    maths = re.findall(r"<math[^>]*>([\s\S]*?)</math>", span)
    text = RAW_MATH.sub(" ", span)
    text = re.sub(r"<[^<>]*>", " ", text)                       # tags with their attributes
    # a named parameter's whole value, to the next | or brace: a style runs
    # on past spaces ("style=text-align: left;font-size: 80%")
    text = re.sub(r"\|\s*[\w-]+\s*=[^|{}]*", " ", text)
    text = re.sub(r"\{\{\s*[^|{}]*\|", " ", text)               # a template's name
    text = re.sub(r"[\w-]+\s*=\s*[^|{}\s]*", " ", text)         # name=value settings left
    text = re.sub(r"&\w+;", " ", text)
    if ours:                                    # added after the settings are gone: "a = \cos b"
        text += " " + " ".join(re.sub(r"[\\{}_^]", " ", m) for m in maths)
        text += " " + re.sub(r"[^A-Za-z]", "", " ".join(maths))
    return Counter(w.lower() for w in WORD3.findall(text) if w.lower() in vocab)


def lost_words(old: str, new: str, vocab, given: Counter) -> Counter:
    """Wikisource's real words in `old` that ours in `new` does not print —
    less those the judge gave us, and the pieces of a word Wikisource's OCR
    split or hyphenated ("in volutes" for "involutes", "prin- cipal")."""
    lost = words_of(old, vocab) - words_of(new, vocab, ours=True) - given
    joined = RAW_MATH.sub(" ", new).lower()
    return Counter({w: n for w, n in lost.items()
                    if not re.search(rf"[^\W\d_]{w}|{w}[^\W\d_]", joined)})


def main():
    vocab = vocabulary()
    dis = json.loads((DISPUTES).read_text(encoding="utf-8"))
    rul = json.loads((RULINGS).read_text(encoding="utf-8"))
    out, tally = {}, Counter()
    for stem in sorted(dis):
        d = json.loads((reading(stem)).read_text(encoding="utf-8"))
        v, p = d["volume"], d["page_number"]
        ours = supplied.name_sections(copy.deepcopy(d))["raw_text"]
        ws = fetched_text(v, p) or ""
        OT, WT = tokens(ours), tokens(ws)
        op, wp = prose(OT, vocab, ours, displays(ours)), prose(WT, vocab, ws)
        sm = SequenceMatcher(None, [k for _, k in op], [k for _, k in wp], autojunk=False)
        pairs = []                              # (our token, ws token) aligned: words and structure
        for b in sm.get_matching_blocks():
            if b.size >= 2:
                pairs += [(op[b.a + k][0], wp[b.b + k][0]) for k in range(b.size)]
        if not pairs:
            continue
        o_at = [OT[o][1] for o, _ in pairs]
        # sites the judge did not give us: where their Wikisource words stand
        W = [t for t in WT if t[3] != "barrier"]
        not_ours, ours_sites = [], []
        for i, s in enumerate(dis[stem]["sites"]):
            r = rul.get(stem, {}).get(str(i))
            if r and s["ws"].split():
                j = locate(W, s["ws"].split(), s["before"].split(), s["after"].split())
                if j is not None:
                    at = (W[j][1], W[j + len(s["ws"].split()) - 1][2])
                    if r == "ours":         # Wikisource's words the judge gave us
                        ours_sites.append((at, Counter(w for w in s["ws"].split() if len(w) >= 3)))
                    elif r in AGAINST:
                        not_ours.append((at, r))
        groups = defaultdict(list)
        for m in RAW_MATH.finditer(ours):
            import bisect
            k = bisect.bisect_left(o_at, m.start())
            if k == 0 or k >= len(pairs):
                tally["formula: no aligned prose on a side"] += 1
                continue
            groups[(k - 1, k)].append(m)
        page = []
        for (ka, kb), ms in groups.items():
            (oa, wa), (ob, wb) = pairs[ka], pairs[kb]
            # spans between the two aligned words: from the end of the one
            # before to the start of the one after
            o0, o1 = OT[oa][2], OT[ob][1]
            w0, w1 = WT[wa][2], WT[wb][1]
            if w1 <= w0:
                tally["refused: aligned words out of order"] += len(ms)
                continue
            # each side keeps its own spacing, punctuation before, and
            # paragraph markup at the edges: the patch is the formulas and
            # the words among them (`edges`)
            n0, n1 = edges(ours, o0, o1)
            w0, w1 = edges(ws, w0, w1)
            n1, w1 = paragraph_end(ours, n0, n1, ws, w0, w1)
            new_c, old_c = ours[n0:n1], ws[w0:w1]
            if old_c == new_c or "<math" not in new_c:
                continue
            why = None
            s = structure(old_c)
            if markup_balance(old_c) != markup_balance(new_c):
                why = "markup unbalanced at an edge"
            elif s:
                why = "Wikisource span holds " + s.split()[0]
            elif structure(new_c):
                why = "our span holds markup"
            elif len(old_c) > 4 * len(new_c) + 200:
                why = "Wikisource span runs long"
            elif sum(words_of(new_c, vocab).values()) > PROSE_MAX:
                why = "our span holds many words"
            elif lost_words(old_c, new_c, vocab,
                            sum((c for (a, b), c in ours_sites if w0 <= a and b <= w1), Counter())):
                why = "a word of Wikisource's would be lost"
            elif any(w0 <= a and b <= w1 for (a, b), _ in not_ours):
                why = "a site the judge did not give us"
            if why:
                tally["refused: " + why] += len(ms)
                if "--why" in sys.argv:
                    WHY.append({"stem": stem, "why": why, "n": len(ms), "real": sum(1 for (a, b), _ in ours_sites if w0 <= a and b <= w1), "old": old_c[:400], "new": new_c[:400], "bal": [markup_balance(old_c), markup_balance(new_c)], "oend": old_c[-150:], "nend": new_c[-150:],
                                "lost": sorted(lost_words(old_c, new_c, vocab, Counter()))[:10]})
                continue
            page.append({"kind": "formula", "start": w0, "end": w1, "old": old_c,
                         "new": new_c, "formulas": len(ms)})
            tally["formulas patched"] += len(ms)
        if page:
            out[stem] = sorted(page, key=lambda x: x["start"])
            tally["pages"] += 1
    if WHY:
        (WORK / "formulas_why.json").write_text(json.dumps(WHY, indent=1, ensure_ascii=False), encoding="utf-8")
        return
    (WORK / "formulas.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    for k, n in sorted(tally.items()):
        print(f"  {k}: {n}")


if __name__ == "__main__":
    main()
