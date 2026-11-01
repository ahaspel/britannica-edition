"""What Wikisource's wikitext writes, as the book's tools count and strip it —
the patch chain, the censuses, the printed-page builder.  One owner each."""
import re

#: the HTML tags wikitext renders; anything else after `<` is OCR's text
TAGS = ("ref|references|math|chem|ce|table|tr|td|th|caption|sub|sup|span|div|br|hr|poem|i|b|u|s|"
        "small|big|center|font|p|blockquote|ol|ul|li|dl|dt|dd|pre|code|nowiki|score|section|abbr|"
        "includeonly|onlyinclude|noinclude|gallery|imagemap|timeline|hiero|syntaxhighlight|tt|var|del|ins|q")
#: a tag as written: bare, or with attributes `name=…` — OCR's "<s- s>",
#: "<s-a>", "<p, z = cr cos 0 … >" (formula salad, vol 25 p. 659) are text
TAG = re.compile(rf"<\s*/?\s*({TAGS})(?:\s+[a-z-]+\s*=\s*[^<>]*)?\s*/?\s*>", re.I)
#: a template's name, at its opening, on one line
TEMPLATE = re.compile(r"\{\{\s*([^|{}\n]+?)\s*(?=[|}])")

#: bold and italic runs: exactly three, two — OCR reads a garbled exponent as
#: "''''" (vol 28 p. 429)
BOLD = re.compile(r"(?<!')'''(?!')")
ITALIC = re.compile(r"(?<!')''(?!')")
#: a table's opening line; a file link's opening
TABLE_OPEN = re.compile(r"(?m)^\s*\{\|")
FILE_LINK = re.compile(r"\[\[(?:File|Image):", re.I)
#: a page's noinclude header or footer
NOINCLUDE = re.compile(r"<noinclude>[\s\S]*?</noinclude>")
#: an HTML entity, named or numeric (`&nbsp;`, `&#8212;`)
ENTITY = re.compile(r"&[a-z]+;|&#\d+;", re.I)
