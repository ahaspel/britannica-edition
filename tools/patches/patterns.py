"""The patterns the patch chain shares — one owner each."""
import re

#: a <math> block in wikitext (a tag's name is any case: vol 10 p. 755's `<Math>`)
RAW_MATH = re.compile(r"<math[^>]*>[\s\S]*?</math>", re.I)
_RAW_MATH_PARTS = re.compile(r"(<math[^>]*>)([\s\S]*?)(</math>)", re.I)
#: a <math> block, its TeX the group
MATH_TEX = re.compile(r"<math[^>]*>([\s\S]*?)</math>", re.I)
#: a letter run; a letter or digit run (the judge's tokens); real-word lengths
WORD = re.compile(r"[^\W\d_]+")
TOKEN = re.compile(r"[^\W\d_]+|\d+")
WORD2 = re.compile(r"[^\W\d_]{2,}")
WORD3 = re.compile(r"[^\W\d_]{3,}")
#: a template's name, at its opening
TEMPLATE_NAME = re.compile(r"\{\{\s*([^|{}]*?)\s*(?:\||\}\})")

#: check_leaks' "old" for a leak no single patch makes: the page's patches together
LEAK_TOGETHER = "(all the page's patches together)"
#: validate_patches' problem for a patch that loses words — the patch's old text the group
REMOVES_WORDS = re.compile(r"removes word\(s\) \[[^\]]*\]: (.*)$", re.S)


def blank_math(text: str) -> str:
    """`text`, the same length, with every formula's TeX blanked: braces are
    counted on it — TeX's `}}` (`\\frac{a}{b}}`) closes no template."""
    return _RAW_MATH_PARTS.sub(lambda m: m.group(1) + " " * len(m.group(2)) + m.group(3), text)
