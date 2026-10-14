"""Step 1 of evaluation: every place our page and Wikisource's say different
things, after removing only differences that are provably the same text:

  - tokens split at letter/digit boundaries (H2SiO3 = "H 2 SiO 3"; a
    footnote mark glued to its word, huggins7 = "huggins 7")
  - a formula is one token (MATH)
  - a word split or joined at a hyphen or line end ("water chamber" =
    "waterchamber"): a site whose two sides join to the same letters is equal
  - footnotes: ours as the transcriber now assembles them (<ref> at the mark,
    `supplied.name_sections`), so both sides carry them inline

Every remaining site is a DISPUTE for the judge — no frequency list decides
anything.  Each records both sides' words, 6 words of agreed context either
side, and the item (column/strip) of ours it falls in, found by its context.

Pages: --set FILE (one stem per line) or stems.  Writes disputes.json; with
--add, the pages join those already there."""
import copy
import difflib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, "tools/diagnostics")
sys.stdout.reconfigure(encoding="utf-8")
import supplied_gate as g
from wikikit.markers import markers_to_text
from wikikit.scan import supplied
from wikikit.source_pages import fetched_text
sys.path.insert(0, str(Path(__file__).parent))
from paths import DISPUTES, reading
from patterns import TOKEN

MATH = re.compile(r"«MATH(?:\[[^\]]*\])?:[\s\S]*?«/MATH»")
SPLIT = TOKEN
CTX = 6


def latex_of(marker: str) -> str:
    """The TeX a walked formula marker («MATH…:TeX«/MATH») holds."""
    return marker.split(":", 1)[1].rsplit("«/MATH»", 1)[0]


def running_text(body: str) -> str:
    """A walked page's running text, as both sides are compared:
      - footnotes apart: Wikisource keeps a note's text at the page's foot
        (<ref follow=…>), ours at its mark — the running text is compared
        without them (their placement: footnote_check.py, 142 of 146 at the
        mark)
      - a paragraph or line break separates words (markers_to_text closes
        it up)
      - a table's cells are text: markers_to_text drops the table whole, and
        no table had been compared on either side (vol 26 p735's recipes);
        and verse's lines likewise
      - a shoulder heading is printed in the margin, not in the running text:
        compared apart (the markup judge checks it against the margin)"""
    body = re.sub(r"«FN:[\s\S]*?«/FN»", " ", body)
    body = body.replace("«P»", " «P» ").replace("«BR»", " «BR» ")
    body = re.sub(r"«/?(?:TABLE|TR|TD|TH|CAPTION)(?:\[[^\]]*\])?»", " ", body)
    body = body.replace("{{VERSE:", " ").replace("}VERSE}", " ")
    return re.sub(r"«SH:[^»]*»[\s\S]*?«/SH»", " ", body)


GREEK = {n: chr(c) for n, c in (
    ("alpha", 945), ("beta", 946), ("gamma", 947), ("delta", 948), ("epsilon", 949), ("varepsilon", 949),
    ("zeta", 950), ("eta", 951), ("theta", 952), ("vartheta", 977), ("iota", 953), ("kappa", 954),
    ("lambda", 955), ("mu", 956), ("nu", 957), ("xi", 958), ("pi", 960), ("varpi", 982), ("rho", 961),
    ("sigma", 963), ("varsigma", 962), ("tau", 964), ("upsilon", 965), ("phi", 966), ("varphi", 966),
    ("chi", 967), ("psi", 968), ("omega", 969), ("Gamma", 915), ("Delta", 916), ("Theta", 920),
    ("Lambda", 923), ("Xi", 926), ("Pi", 928), ("Sigma", 931), ("Phi", 934), ("Psi", 936), ("Omega", 937), ("sum", 931), ("prod", 928))}
CMD = re.compile(r"\\([A-Za-z]+)")
#: Commands that PRINT a word: the operator names (\tan prints "tan").
OPERATORS = {"sin", "cos", "tan", "cot", "sec", "csc", "cosec", "sinh", "cosh", "tanh", "coth", "arcsin",
             "arccos", "arctan", "log", "ln", "exp", "lim", "max", "min", "sup", "inf", "det", "deg",
             "arg", "dim", "ker", "gcd", "mod", "bmod", "pmod", "hom", "lg"}


def math_letters(latex: str) -> str:
    """A formula as its letters and digits: Greek names as their letters,
    operator names as the words they print (\\tan -> tan), every other command
    (\\frac, \\text, \\sqrt, …) dropped, braces and operators gone.  Both sides
    go through this, so a symbol written as a formula equals the same symbol
    written as a letter."""
    def one(m):
        c = m.group(1)
        return f" {GREEK[c]} " if c in GREEK else f" {LETTERLIKE[c]} " if c in LETTERLIKE else \
            f" {c} " if c in OPERATORS else " "
    s = ENV.sub(" ", latex)              # \begin{vmatrix}: the name prints nothing
    s = CMD.sub(one, s)
    return " ".join(SPLIT.findall(s))


#: Commands that print a letter-like sign
LETTERLIKE = {"Re": "ℜ", "Im": "ℑ", "aleph": "ℵ", "ell": "ℓ", "wp": "℘", "hbar": "ℏ"}
ENV = re.compile(r"\\(?:begin|end)\{[^}]*\}")
#: The same print in another code point, beyond Unicode's compatibility forms
SAME = {"ƒ": "f", "℔": "lb", "Σ": "σ", "∑": "σ", "∏": "π"}


#: A centred caption line: "{{c|{{sc|Fig. 1.—…}}}}", "{{center|Fig. 2. …}}"
CAPTION_LINE = re.compile(r"(?m)^[ \t]*\{\{(?:c|center)\|(?:\{\{sc\||''+)*\s*Fig\.[^\n]*$")


def tokens(v, p, text):
    """Every printed letter-run and digit-run, any script — Greek included
    (`countable_word_list` counts Latin words only, and the disputes it gave
    lost every μ and λ: the judge, given "we have 2 2" for "we have μ + λ₂ <
    2", looked in the wrong place)."""
    import unicodedata
    # a figure's caption is printed under its figure, not in the running
    # text: compared apart (Wikisource seldom carries one; ours sets it by its
    # figure, and "Fig. 3, Composite joint" was judged a word we added)
    text = CAPTION_LINE.sub("", text)
    body = MATH.sub(lambda m: " " + math_letters(latex_of(m.group(0))) + " ", g.walked(v, p, text))
    flat = unicodedata.normalize("NFKC", markers_to_text(running_text(body)))
    flat = "".join(SAME.get(ch, ch) for ch in flat)
    return [t.lower() for t in SPLIT.findall(flat)]


def item_of(ctx_words, readings_tokens):
    """The item whose reading holds these context words in a row, or None."""
    k = len(ctx_words)
    for name, toks in readings_tokens.items():
        for i in range(len(toks) - k + 1):
            if toks[i:i + k] == ctx_words:
                return name
    return None


def page(stem, src_dir=None):
    v = int(stem[3:5])
    src = Path(src_dir) / f"{stem}.json" if src_dir else reading(stem)
    d = json.loads(src.read_text(encoding="utf-8"))
    p = d["page_number"]
    ours_text = supplied.name_sections(copy.deepcopy(d))["raw_text"]
    t, o = tokens(v, p, fetched_text(v, p) or ""), tokens(v, p, ours_text)
    rt = {}
    for name, r in d["provenance"]["readings"].items():
        r = re.sub(r"⟦\d+⟧[ \t]*", "", r)          # recorded positions are not text
        try:
            rt[name] = tokens(v, p, r)
        except Exception:
            rt[name] = []
    sites = []
    sm = difflib.SequenceMatcher(None, t, o, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            continue
        a, b = t[i1:i2], o[j1:j2]
        if "".join(a) == "".join(b):
            continue                                   # split/joined: the same letters
        before = o[max(0, j1 - CTX):j1]
        after = o[j2:j2 + CTX]
        where = item_of(before[-4:], rt) if len(before) >= 4 else None
        where = where or (item_of(after[:4], rt) if len(after) >= 4 else None)
        sites.append({"ws": " ".join(a), "ours": " ".join(b), "before": " ".join(before),
                      "after": " ".join(after), "item": where})
    agree = sum(i2 - i1 for op, i1, i2, _, _ in sm.get_opcodes() if op == "equal")
    # agreed words to plant calibration errors in: a word of 4+ letters inside
    # an agreed run, with agreed context both sides
    agreed = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op != "equal" or i2 - i1 < 2 * CTX + 1:
            continue
        for j in range(j1 + CTX, j2 - CTX, 3):
            w = o[j]
            kind = "word" if len(w) >= 4 and w.isalpha() else "symbol" if len(w) <= 2 else None
            if kind == "word" and j % 9:
                continue                     # words are plenty: every third candidate
            if kind:
                before, after = o[j - CTX:j], o[j + 1:j + 1 + CTX]
                agreed.append({"word": w, "kind": kind, "before": " ".join(before), "after": " ".join(after),
                               "item": item_of(before[-4:], rt)})
    return {"page": stem, "ws_tokens": len(t), "our_tokens": len(o), "agree": agree, "sites": sites,
            "agreed": agreed}


def main():
    args = sys.argv[1:]
    src_dir = None
    if "--src" in args:
        src_dir = args[args.index("--src") + 1]
    if "--set" in args:
        stems = Path(args[args.index("--set") + 1]).read_text(encoding="utf-8").split()
    else:
        stems = [a for a in args if a.startswith("vol")]
    # --add: these pages join the disputes already made (pages newly read);
    # a page already there is never remade — its sites are what the judge's
    # answers are keyed by
    out = json.loads(DISPUTES.read_text(encoding="utf-8")) if "--add" in args else {}
    if "--add" in args and (again := sorted(set(stems) & set(out))):
        raise SystemExit(f"--add: already disputed, left as they are: {again}")
    for s in stems:
        out[s] = page(s, src_dir)
        r = out[s]
        print(f"{s}: agree {r['agree']}/{r['ws_tokens']}  disputes {len(r['sites'])}"
              f"  unplaced {sum(1 for x in r['sites'] if not x['item'])}", flush=True)
    DISPUTES.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("pages", len(out), "disputes", sum(len(r["sites"]) for r in out.values()))


if __name__ == "__main__":
    main()
