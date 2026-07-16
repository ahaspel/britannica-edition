"""Parse vol 29's master Index of Contributors from the
vision-OCR transcription.

Pages 956-982 of vol 29 carry "CONTRIBUTORS TO THE ENCYCLOPAEDIA
BRITANNICA (11th EDITION) AND THE PRINCIPAL ARTICLES SIGNED BY
THEM" — a single canonical alphabetical list.

Source: ``data/derived/vol29_contributors_ocr.json``, produced by
``tools/vol29/vision_ocr_contributors.py`` (Claude vision
transcription).  The transcription enforces a regular per-entry
shape so this parser is straightforward:

  SURNAME, FIRSTNAMES, CREDS. (Initials)
  : Article 1; Article 2; ...
  : (continuation of article list, optional)

Asterisks in initials are CRITICAL — they distinguish two
contributors who share base initials (e.g. ``(E. B.)`` Breck vs
``(E. B.*)`` Babelon).  The parser preserves them verbatim.

Read-only.  Produces a list of `Vol29Entry` dataclass instances; a
caller (intended: a future revision of `build_contributor_table.py`)
uses the list as the authoritative source for `(initials → person)`
mappings, overriding per-volume table assignments where they
disagree.
"""

from __future__ import annotations

import io
import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

OCR_FILE = Path("data/derived/vol29_contributors_ocr.json")
VISION_TAG = "<!-- vision-ocr -->"

# Header line: SURNAME, FIRSTNAMES, CREDENTIALS (Initials)
# The name portion runs from the start to the FINAL paren-group (the
# initials).  The name may itself contain parenthetical credentials —
# "(Mrs. Edward Wilde)", "F.R.S.(Edin.)" — so it allows balanced parens, not
# just non-paren chars; otherwise such a header fails the match and the whole
# entry is swallowed into the PREVIOUS entry's article list, mis-attributing
# the swallowed articles.  The initials group's closing `)` is optional for
# the same reason: when OCR drops it ("...ANTOON. (H. A. L." for Lorentz) the
# header must still match, or Lorentz's articles bleed into the prior entry.
# Name/credential split is done by `_split_name_creds` after the match.
_HEADER_RE = re.compile(
    r"^([A-Z](?:[^()]|\([^)]*\))*?)\s*\(([^)]{1,30})\)?\s*\.?\s*$"
)

# Article-list line: starts with `:` (vision prompt enforces this).
_ARTICLES_RE = re.compile(r"^\s*:\s*(.*)$")

# Pages that aren't part of the alphabetical index proper — page
# headers, intro blurbs.  The vision prompt usually skips these but
# we filter defensively.
_NOT_AN_ENTRY = re.compile(
    r"^(?:CONTRIBUTORS TO|THE ENCYCLOPAEDIA|\(11(?:TH|th)\b|"
    r"AND THE PRINCIPAL|The Initials in)",
)


@dataclass
class Vol29Entry:
    """One row of the master Index of Contributors."""

    display: str            # Bold display: SURNAME, FIRSTNAMES (no creds)
    full_name: str          # Canonical First Middle Last form
    credentials: str        # Comma-separated credentials, no trailing dot
    initials: str           # Signature initials, asterisks preserved
    articles: list[str]     # Principal articles (cleaned)
    page: int               # Source ws page number


def _proper_case(s: str) -> str:
    """Title-case a name, preserving common multi-cap forms (McX, MacX,
    O'X, hyphens, all-caps abbreviations like II/III).  Vol 29 prints
    everything in caps; we want canonical mixed-case for storage."""
    parts = re.split(r"(\s+|-)", s)
    out = []
    for p in parts:
        if not p or p.isspace() or p == "-":
            out.append(p)
            continue
        if re.fullmatch(r"[IVX]+\.?", p, flags=re.IGNORECASE):
            out.append(p.upper())
            continue
        # Mc / Mac prefix — re-apply title case to the suffix
        m = re.match(r"^(Mc|Mac|O')(.+)$", p, flags=re.IGNORECASE)
        if m:
            out.append(m.group(1).capitalize() + m.group(2).capitalize())
            continue
        out.append(p.capitalize())
    return "".join(out)


_CRED_TOKEN = re.compile(
    r"^(?:"
    r"[A-Z]\.?(?:[A-Z]\.?)*"            # initials sequences: M.A., LL.D., D.C.L.
    r"|Ph\.?D\.?|Litt\.?D\.?|Sc\.?D\.?|D\.?Sc\.?|"
    r"[A-Z]+\.[A-Z]+\.?(?:\([^)]+\))?"  # F.R.S.(Edin.) etc.
    r"|F\.[A-Z]+\.?[A-Z]?\.?"           # F.R.S., F.S.A., F.R.G.S.
    r"|K\.[A-Z]\.[A-Z]\.?"              # K.C.B., K.C.M.G., K.C.S.I.
    r"|Bart\.?|Esq\.?|Jr\.?|Sr\.?|"
    r"O\.S\.B\.?|D\.\s*è?s\.?\s*L\.?"
    r")$",
    re.IGNORECASE,
)


def _is_credential(tok: str) -> bool:
    """A token reads as credentials when it's short, dotted, and
    matches one of the EB1911 degree / honorific patterns.  Any
    purely-alphabetic token of more than ~3 lowercase letters is a
    name word, never a credential."""
    t = tok.strip().rstrip(".,")
    if not t:
        return True
    return bool(_CRED_TOKEN.match(t))


def _split_name_creds(raw_name: str) -> tuple[str, str, str]:
    """Split a vol 29 header name into (display, full_name, credentials).

    Vol 29 prints names as ``SURNAME, FIRSTNAMES, CREDENTIALS``.
    Splitting on the first comma gives SURNAME on the left and
    `FIRSTNAMES, CREDENTIALS` on the right.  In practice the
    second comma-separated chunk is always given names; subsequent
    chunks are credentials.  This works because EB1911 doesn't split
    a person's first/middle names with a comma — only the
    SURNAME/given boundary and the credential boundary use commas.
    """
    name = raw_name.strip().rstrip(".,")
    parts = [p.strip() for p in name.split(",") if p.strip()]
    if not parts:
        return "", "", ""
    surname = parts[0]
    if len(parts) == 1:
        # Just a surname (rare — usually a one-name entity).
        return surname, _proper_case(surname), ""
    given = parts[1]
    cred_tokens: list[str] = []
    for tok in parts[2:]:
        cred_tokens.append(tok)
    creds = ", ".join(cred_tokens).strip().rstrip(".")
    display = f"{surname}, {given}"
    full_name = f"{_proper_case(given)} {_proper_case(surname)}".strip()
    return display, full_name, creds


def _clean_initials(raw: str) -> str:
    """Tidy whitespace; preserve `.`, `*`, `-`, hyphens, and case
    distinctions (the subscript-letter `Ba.` / `Bo.` form).  Strip
    only stray brackets and HTML.  Vol 29's print convention treats
    `(E. B.)` and `(E. B.*)` as DIFFERENT signatures — never collapse
    them."""
    s = re.sub(r"<[^>]+>", "", raw).strip()
    s = re.sub(r"\s+", " ", s).strip()
    return s.rstrip(",")


def _clean_articles(joined: str) -> list[str]:
    """Split a ``:``-prefixed article list into individual titles.

    Vol 29 separates with semicolons.  Italic notes are wrapped in
    asterisks (``*in part*``, ``*Ancient*``); we strip the asterisks
    but keep the parenthetical qualifier inline because it's part of
    the article-title disambiguator (``Italy, *Geography and
    Statistics*`` vs ``Italy, *History*``).
    """
    s = re.sub(r"\*", "", joined)
    s = re.sub(r"\s+", " ", s).strip().rstrip(".")
    out: list[str] = []
    for chunk in re.split(r"\s*;\s*", s):
        chunk = chunk.strip().rstrip(".,")
        if not chunk:
            continue
        if chunk.lower() in {"&c", "&c.", "etc", "etc.", "and others",
                             "and other articles"}:
            continue
        if len(chunk) > 200:
            continue        # OCR run-on, drop
        out.append(chunk)
    return out


def _strip_vision_tag(text: str) -> str:
    """Drop the `<!-- vision-ocr -->` sentinel and any leading blank lines."""
    if text.startswith(VISION_TAG):
        text = text[len(VISION_TAG):]
    return text.lstrip("\n")


def parse_vol29_index(
    ocr_path: Path | str = OCR_FILE,
) -> list[Vol29Entry]:
    """Parse the Claude-vision transcription into typed entries."""
    path = Path(ocr_path)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} missing — run "
            "`tools/vol29/vision_ocr_contributors.py` first."
        )
    pages = json.loads(path.read_text(encoding="utf-8"))

    entries: list[Vol29Entry] = []
    for ws_str, page_text in sorted(pages.items(), key=lambda kv: int(kv[0])):
        ws = int(ws_str)
        text = _strip_vision_tag(page_text)
        lines = text.split("\n")

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line or _NOT_AN_ENTRY.match(line):
                i += 1
                continue
            m = _HEADER_RE.match(line)
            if not m:
                i += 1
                continue
            raw_name, raw_init = m.group(1), m.group(2)
            # Lift any parenthetical credentials out of the name ("(Mrs. Edward
            # Wilde)") so the comma-split sees a clean SURNAME, FIRSTNAMES form;
            # fold them into the credentials.
            paren_creds = re.findall(r"\(([^)]*)\)", raw_name)
            raw_name = re.sub(r"\s*\([^)]*\)\s*", " ", raw_name)
            display, full_name, creds = _split_name_creds(raw_name)
            if paren_creds:
                creds = ", ".join(c for c in [creds, *paren_creds] if c)
            initials = _clean_initials(raw_init)

            # Collect article-list lines until next header / blank /
            # end of page.
            article_lines: list[str] = []
            j = i + 1
            while j < len(lines):
                nxt = lines[j].strip()
                if not nxt:
                    j += 1
                    continue
                am = _ARTICLES_RE.match(nxt)
                if am:
                    article_lines.append(am.group(1))
                    j += 1
                    continue
                # Non-blank, non-`:` line — could be a header for the
                # next entry, or a continuation of the previous
                # article list (rare but seen when vision OCR drops
                # the `:`).
                if _HEADER_RE.match(nxt):
                    break
                article_lines.append(nxt)
                j += 1

            articles = _clean_articles(" ".join(article_lines))
            entries.append(Vol29Entry(
                display=display,
                full_name=full_name,
                credentials=creds,
                initials=initials,
                articles=articles,
                page=ws,
            ))
            i = j
    return entries


def main() -> None:
    """CLI: print a quick summary."""
    import sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    entries = parse_vol29_index()
    print(f"Parsed {len(entries)} entries.")
    distinct_init = {e.initials for e in entries}
    print(f"Distinct initials: {len(distinct_init)}")
    total_arts = sum(len(e.articles) for e in entries)
    print(f"Total article references: {total_arts}")
    print()
    print("Sample entries (first 6 + Babelon + Breck):")
    for e in entries[:6]:
        print(f"  init={e.initials!r:14s} {e.full_name!r}")
        if e.articles:
            print(f"    articles: {e.articles[:3]}")
    for keyword in ("Babelon", "Breck"):
        for e in entries:
            if keyword.lower() in e.full_name.lower():
                print(f"  init={e.initials!r:14s} {e.full_name!r} creds={e.credentials!r}")
                print(f"    articles: {e.articles}")


if __name__ == "__main__":
    main()
