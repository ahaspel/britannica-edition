"""Kind-validated article matching for vol-29 contributor credits.

The vol-29 master index credits a contributor with a list of article titles.
The old matcher stripped every disambiguator ("Adams, C. F." -> ADAMS, "Rhea
(Mythology)" -> RHEA), then bound the biggest same-named article — crediting
historians with townships and classicists with birds (~96 false binds).

This matcher instead asks the question the reviewer asked: *is this the right
KIND of thing?*  Every candidate carries a kind (from the post-export kind
index); the credit implies a kind (a "SURNAME, Given" form -> person, a
"(Mythology)"/"(king)" disambiguator -> its kind); and the contributor implies a
kind (the FOOTPRINT — the kinds of the articles we are already certain they
wrote).  A candidate is bound only when its kind is consistent with the credit
and/or the footprint; otherwise we ABSTAIN.  A miss beats a false link.

Pure functions over plain data (title -> [candidate ids], id -> kinds, id ->
title, footprint counter); the phase wiring lives elsewhere.
"""
from __future__ import annotations

import re
from collections import Counter

from britannica.xrefs.disambiguation import PERSON_KINDS

# Editorial parentheticals — NOT disambiguators.  "(in part)" / "(in
# collaboration with X)" / "(continued)" mean the contributor wrote part of the
# NAMED article; strip them and keep the name.  Everything else in parens
# disambiguates (which homonym) and must steer the match.
_EDITORIAL_PAREN = re.compile(
    r"\((?:in part|in collaboration[^)]*|continued|concluded|part [ivx]+|"
    r"[ivx]+\.?(?:\s*,\s*[ivx]+\.?)*(?:\s+and\s+[ivx]+\.?)?)\)", re.I)
_PAREN = re.compile(r"\(([^)]*)\)")

# A disambiguator word -> the kind it implies (same vocabulary as the kind index
# / lead_kind).  Built from the person roles + a few index/mythology terms.
_DISAMBIG_KIND: dict[str, str] = {
    "king": "king", "kings": "king", "emperor": "emperor", "emperors": "emperor",
    "pope": "pope", "popes": "pope", "saint": "saint", "st": "saint",
    "general": "general", "statesman": "statesman", "poet": "poet",
    "painter": "painter", "sculptor": "sculptor", "composer": "musician",
    "musician": "musician", "physician": "physician", "bishop": "bishop",
    "family": "family", "tribe": "ethnic", "people": "ethnic",
}
_PERSONISH = PERSON_KINDS | {"person"}


def credit_expected_kinds(credit_title: str) -> set[str]:
    """Kinds the credit's own form/disambiguator implies (∅ if it says nothing).

    - A trailing "SURNAME, <forename or rank>" (not a section word) -> person.
    - A parenthetical disambiguator maps through ``_DISAMBIG_KIND`` (king, pope,
      tribe->ethnic, family, mythology->person, …).
    """
    kinds: set[str] = set()
    for m in _PAREN.finditer(credit_title):
        if _EDITORIAL_PAREN.fullmatch(m.group(0)):
            continue
        for w in re.findall(r"[a-z]+", m.group(1).lower()):
            if w in ("mythology", "mythological", "god", "goddess", "deity"):
                kinds |= _PERSONISH            # a myth subject is a person-ish entry
            elif w in _DISAMBIG_KIND:
                kinds.add(_DISAMBIG_KIND[w])
    tail = _tail_after_comma(credit_title)
    if tail and _looks_like_forename_or_rank(tail):
        kinds |= _PERSONISH
    return kinds


def _tail_after_comma(title: str) -> str:
    t = re.sub(r"\s*\([^)]*\)", "", title)
    return t.split(",", 1)[1].strip() if "," in t else ""


# Section words that make "PLACE, X" a section reference, not a personal name.
_SECTION_WORDS = {
    "history", "geography", "geology", "statistics", "literature", "language",
    "the", "book", "council", "modern", "ancient", "electric", "lake",
    "province", "kingdom", "battle", "treaty", "synod", "diet", "religion",
    "art", "architecture", "music", "law", "constitution", "climate", "fauna",
    "flora", "economics", "administration", "population",
}


_RANKS = {"lord", "earl", "duke", "baron", "sir", "st", "saint", "king",
          "count", "marquis", "viscount", "1st", "2nd", "3rd", "4th"}


def _looks_like_forename_or_rank(tail: str) -> bool:
    """True when a post-comma tail names a PERSON (forename/initials/rank), not a
    section — "C. F.", "Ulysses S", "Grover", "Léon", "Lord", "1st Earl of" ->
    person; "History", "Book of", "United States" -> not.  Unicode-safe (accents
    are letters: "Léon" is a forename)."""
    toks = tail.split()
    if not toks:
        return False
    if toks[0].lower().strip(".,") in _SECTION_WORDS:
        return False
    if any(t.lower().strip(".,") in _RANKS for t in toks):
        return True
    # all-initials tail ("C. F.", "J. B.")
    if all(len(t.strip(".")) == 1 and t.strip(".").isalpha() for t in toks):
        return True
    # a leading Title-case forename token (isalpha keeps accented letters)
    t0 = toks[0].strip(".,")
    return bool(t0) and t0[:1].isupper() and t0.isalpha()


def footprint_kind_ok(cand_kinds: set[str], footprint: Counter) -> bool:
    """Consistent with the contributor's footprint: the candidate shares a kind
    the contributor demonstrably writes, and does NOT belong to a broad category
    they never touch.  Empty/near-empty footprints answer False (no signal)."""
    if sum(footprint.values()) < _MIN_FOOTPRINT:
        return False
    return bool(cand_kinds & set(footprint))


_MIN_FOOTPRINT = 5   # below this a footprint is too thin / circular to trust


def _fold(s: str) -> str:
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFKD", s.upper())
                   if not unicodedata.combining(c))


def _tok_compat(c: str, a: str) -> bool:
    """A credit given-token vs an article given-token: an initial matches a
    first letter; full names match (accent-folded)."""
    c, a = c.upper().strip("."), a.upper().strip(".")
    if not c or not a:
        return False
    if len(c) == 1:
        return a[0] == c
    if len(a) == 1:
        return c[0] == a
    return _fold(c) == _fold(a)


def given_compatible(credit_given: str, article_given: str) -> bool:
    """The credit's forename(s) are an order-preserving, per-token match of the
    article's forenames — "C. F." ~ "Charles Francis", "Léon" ~ "[Jean Baptiste]
    Léon" (brackets ignored), "Ulysses S" ~ "Ulysses Simpson"."""
    ctoks = [t for t in re.split(r"[\s.]+", credit_given) if t]
    atoks = [t for t in re.split(r"[\s.]+", re.sub(r"[\[\]]", " ", article_given)) if t]
    if not ctoks or not atoks:
        return False
    ai = 0
    for ct in ctoks:
        for j in range(ai, len(atoks)):
            if _tok_compat(ct, atoks[j]):
                ai = j + 1
                break
        else:
            return False
    return True


def split_surname_given(credit_title: str):
    """('ADAMS', 'C. F.') from 'Adams, C. F.'; ('', '') when there's no comma."""
    t = re.sub(r"\s*\([^)]*\)", "", credit_title).strip().rstrip(",.;")
    if "," not in t:
        return "", ""
    head, _, tail = t.partition(",")
    return head.strip().upper(), tail.strip()


def given_exact(credit_given: str, article_given: str) -> bool:
    """Every forename accounted for, none left over — "Jean Baptiste" == "Jean
    Baptiste" but NOT "[Jean Baptiste] Léon" (Léon left over).  So a "Say, Jean
    Baptiste" credit prefers J.-B. Say over his grandson Léon."""
    ct = [t for t in re.split(r"[\s.]+", credit_given) if t]
    at = [t for t in re.split(r"[\s.]+", re.sub(r"[\[\]]", " ", article_given)) if t]
    return len(ct) == len(at) and len(ct) > 0 and all(
        _tok_compat(c, a) for c, a in zip(ct, at))


def candidate_ids(credit_title, title_map, comma_index, given_of):
    """The article ids a credit could denote: exact normalised title, plus — for a
    "SURNAME, forename" credit — the comma-form persons whose forenames match
    (preferring an EXACT forename match over a mere subsequence), plus the
    section-head fallback (kept, but the caller kind-gates it so a township can't
    win a person credit)."""
    from britannica.contributors.link_vol29_articles import _normalize_vol29_title
    key = _normalize_vol29_title(credit_title)
    ids = list(title_map.get(key, []))
    surname, given = split_surname_given(credit_title)
    if given and _looks_like_forename_or_rank(given):
        exact = [aid for aid in comma_index.get(surname, [])
                 if given_exact(given, given_of(aid))]
        compat = [aid for aid in comma_index.get(surname, [])
                  if given_compatible(given, given_of(aid))]
        ids.extend(exact if exact else compat)    # a unique exact wins its grandson
    if not ids and "," in key:                    # section head ("Bolivia, History")
        ids = list(title_map.get(key.split(",", 1)[0].strip(), []))
    seen, out = set(), []
    for i in ids:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


def pick_article(cands, kinds_of, expected, footprint):
    """Pick the article a credit denotes, or abstain (None).

    ``cands``: candidate article ids.  ``kinds_of(id)`` -> kinds.  ``expected``:
    the credit's implied kinds (∅ if it says nothing).  ``footprint``: Counter.

    - EXPECTED kinds are a REQUIREMENT: a "SURNAME, forename" / "(king)" credit
      must land on a matching kind — unique match binds, many narrow by footprint,
      zero abstains (never bind a kind-mismatched homonym).
    - With NO expected kind, a LONE candidate binds (the credit points at it, no
      conflict); the footprint only breaks a MULTI-candidate tie (Buffalo -> the
      animal).  The footprint never vetoes a lone match — that would drop every
      valid section/bare credit whose author isn't a specialist in that kind."""
    if not cands:
        return None
    if expected:
        matches = [c for c in cands if kinds_of(c) & expected]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            narrowed = [c for c in matches if footprint_kind_ok(kinds_of(c), footprint)]
            return narrowed[0] if len(narrowed) == 1 else None
        return None
    if len(cands) == 1:
        return cands[0]
    narrowed = [c for c in cands if footprint_kind_ok(kinds_of(c), footprint)]
    return narrowed[0] if len(narrowed) == 1 else None
