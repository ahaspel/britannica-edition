"""A page's raw wikitext cut into tokens, each with its character span in
the RAW text — what a patch is placed by:

  word     a letter run or digit run of running text (lowercased, NFKC)
  math     the letters of a <math> block (`disputes.math_letters`), every
           token spanning the whole block
  inner    a letter of a formula-making template (Wikisource's salad)
  barrier  any markup that is not inline formatting: a template, a link,
           a tag, a footnote, a table, the noinclude header — one token
           that matches nothing, so no patch can reach across it
  (italic / bold quote marks and <sub>/<sup> are not tokens; a word patch
   whose span holds any is refused)"""
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from disputes import SAME, math_letters
from patterns import TEMPLATE_NAME, TOKEN

SPLIT = TOKEN
FORMAT = re.compile(r"'{2,5}|</?su[bp]>")


#: Wikisource's formula-making templates: Greek letters, fractions, sub- and
#: superscripts, overlines, spacing — inside a formula's salad
INNER = {"polytonic", "greek", "eb1911 tfrac", "sfrac", "tfrac", "frac", "sub", "sup", "overline", "em",
         "gap", "ne", "uc", "brace2", "=", "...", "spaces", "nop", "hi", "fs", "lb-", "asc", "csc",
         "subsup", "su", "sqrt", "radic", "math", "mvar", "var", "ell", "prime", "√", "abs", "e"}
#: presentation wrappers: centring, size, small capitals, no-wrap
WRAP = {"center", "c", "centre", "block center", "nowrap", "sc", "smaller", "larger", "x-larger",
        "small", "x-smaller", "fine block", "smaller block"}


def _balanced(text, i, open_, close):
    depth, j = 0, i
    while j < len(text):
        if text.startswith(open_, j):
            depth += 1
            j += len(open_)
        elif text.startswith(close, j):
            depth -= 1
            j += len(close)
            if depth == 0:
                return j
        else:
            j += 1
    return len(text)


def regions(text):
    """(start, end, kind) for every math block and barrier, in order."""
    out, i = [], 0
    while i < len(text):
        if text.startswith("<math", i):
            j = text.find("</math>", i)
            j = len(text) if j < 0 else j + 7
            out.append((i, j, "math"))
            i = j
        elif text.startswith("<noinclude>", i):
            j = text.find("</noinclude>", i)
            j = len(text) if j < 0 else j + 12
            out.append((i, j, "barrier"))
            i = j
        elif text.startswith("<ref", i):
            j = text.find("</ref>", i)
            k = text.find("/>", i)
            j = (j + 6) if j >= 0 and (k < 0 or j < k or text[i:k].count(">") > 0) else (k + 2 if k >= 0 else len(text))
            out.append((i, j, "barrier"))
            i = j
        elif text.startswith("{{", i):
            j = _balanced(text, i, "{{", "}}")
            name = TEMPLATE_NAME.match(text[i:j])
            name = name.group(1).lower() if name else ""
            bar = text.find("|", i, j)
            if name in INNER:
                # part of Wikisource's attempt at a formula: a formula patch
                # may replace it with the salad around it
                out.append((i, j, "inner"))
            elif name in WRAP and 0 < bar < j - 2:
                # presentation only: its syntax is a wall, its contents text
                out.append((i, bar + 1, "barrier"))
                out.extend((a + bar + 1, b + bar + 1, k) for a, b, k in regions(text[bar + 1:j - 2]))
                out.append((j - 2, j, "barrier"))
            else:
                out.append((i, j, "barrier"))
            i = j
        elif text.startswith("[[", i):
            j = _balanced(text, i, "[[", "]]")
            out.append((i, j, "barrier"))
            i = j
        elif text.startswith("{|", i) and (i == 0 or text[i - 1] == "\n"):
            j = text.find("\n|}", i)
            j = len(text) if j < 0 else j + 3
            out.append((i, j, "barrier"))
            i = j
        elif text[i] == "<" and not FORMAT.match(text, i) and re.match(r"</?[a-zA-Z]", text[i:i + 3]):
            j = text.find(">", i)
            j = len(text) if j < 0 else j + 1
            out.append((i, j, "barrier"))
            i = j
        else:
            i += 1
    return out


def norm(s):
    s = unicodedata.normalize("NFKC", s)
    return "".join(SAME.get(c, c) for c in s).lower()


def tokens(text):
    """[(token, start, end, kind)] over the raw wikitext."""
    out, pos = [], 0
    for a, b, kind in regions(text) + [(len(text), len(text), "end")]:
        # normalised text mapped back char by char: NFKC and SAME change
        # lengths, and positions must be the RAW text's (mojibake "Â" had
        # shifted every span after it: "of f is equa", vol 1 p. 674)
        chars, back = [], []
        for i in range(pos, a):
            for c in norm(text[i]):
                chars.append(c)
                back.append(i)
        seg = "".join(chars)
        for m in SPLIT.finditer(seg):
            out.append((m.group(0), back[m.start()], back[m.end() - 1] + 1, "word"))
        if kind == "math":
            body = re.sub(r"^<math[^>]*>|</math>$", "", text[a:b])
            for t in math_letters(body).lower().split():
                out.append((t, a, b, "math"))
        elif kind == "barrier":
            out.append((f"§{a}", a, b, "barrier"))
        elif kind == "inner":
            # the letters it prints: its arguments, not its name or settings
            args = text[a + 2:b - 2].split("|")[1:]
            shown = " ".join(x for x in args if "=" not in x or x.strip() == "=")
            for t in SPLIT.findall(norm(re.sub(r"\{\{[^{}|]*\||\}\}", " ", shown))):
                out.append((t, a, b, "inner"))
        pos = b
    return out

