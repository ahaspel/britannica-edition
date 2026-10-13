"""The patterns the patch chain shares — one owner each."""
import re

#: a <math> block in wikitext
RAW_MATH = re.compile(r"<math[^>]*>[\s\S]*?</math>")
_RAW_MATH_PARTS = re.compile(r"(<math[^>]*>)([\s\S]*?)(</math>)")
#: a letter run; a letter or digit run (the judge's tokens); real-word lengths
WORD = re.compile(r"[^\W\d_]+")
TOKEN = re.compile(r"[^\W\d_]+|\d+")
WORD2 = re.compile(r"[^\W\d_]{2,}")
WORD3 = re.compile(r"[^\W\d_]{3,}")
#: a template's name, at its opening
TEMPLATE_NAME = re.compile(r"\{\{\s*([^|{}]*?)\s*(?:\||\}\})")


def blank_math(text: str) -> str:
    """`text`, the same length, with every formula's TeX blanked: braces are
    counted on it — TeX's `}}` (`\\frac{a}{b}}`) closes no template."""
    return _RAW_MATH_PARTS.sub(lambda m: m.group(1) + " " * len(m.group(2)) + m.group(3), text)
