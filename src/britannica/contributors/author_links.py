"""Harvest each article's contributors from its author-links — the authoritative
attribution for the great majority of binds.

EB1911 signs an article three ways, and the first two carry the NAME and
INITIALS together, in the article's own raw wikitext (``ArticleSegment.segment_text``):

  1. ``{{EB1911 footer initials|Full Name|Initials}}`` — the footer template.
  2. ``[[Author:Full Name|Initials]]``                — the signature wikilink,
     usually inside a trailing ``{{right|(…)}}`` (VESUVIUS, THUCYDIDES, …).
  3. ``{{EB1911 TAs}}``                               — a bare shortcut sign-off,
     initials only (no name).

Binding resolves by the (name, initials) COMBINATION through ``ContributorIndex``
— name-first, initials only confirming — so the source's occasional transcription
slips (a dropped ``*``, an OCR i-for-t) cannot misclassify: the name anchors the
identity ([[feedback_accrete_first_canonicalize_last]]).

A literal ``(A. C. G.)`` parenthetical with NO ``[[Author:…]]`` link (SHARK) is a
bare parenthetical — carries no name, so it is NOT harvested here; it is reserved
for step-4 disambiguation, never link harvest.  For the same reason an
``[[Author:…]]`` counts as a signature only when its display normalises to a
KNOWN contributor-initials key — otherwise it is a bibliographic reference to an
author, and the render (``_wrap_author_link``) treats it the same way.
"""
from __future__ import annotations

import re
from collections import defaultdict

from britannica.db.models import Contributor, ContributorInitials, ArticleSegment
from britannica.contributors.resolver import _fold, _name_core_tokens
from britannica.pipeline.stages.elements._contributor import (
    _SHORTCUT_RE, _expand_initials_shortcut)
from britannica.pipeline.stages.extract_contributors import (
    _iter_footers, _normalize_initials, _parse_contributors)

_AUTHOR_LINK_RE = re.compile(r"\[\[Author:([^\]|]+)\|([^\]]+)\]\]", re.IGNORECASE)


def raw_wikitext_by_article(session) -> dict[int, str]:
    """Each article's own raw wikitext: its segments concatenated in order."""
    parts: dict[int, list[str]] = defaultdict(list)
    for aid, _seq, text in (
        session.query(ArticleSegment.article_id,
                      ArticleSegment.sequence_in_article,
                      ArticleSegment.segment_text)
        .order_by(ArticleSegment.article_id,
                  ArticleSegment.sequence_in_article)
    ):
        parts[aid].append(text or "")
    return {aid: "\n".join(chunks) for aid, chunks in parts.items()}


def harvest_author_links(session, cidx, article_ids=None):
    """Resolve every author-link signature to its contributor.

    Returns ``(binds, unresolved, votes)``:
      - ``binds``: list of ``(article_id, contributor_id, sequence)``, per-article
        reading order preserved, de-duplicated within an article.
      - ``unresolved``: list of ``(article_id, name, initials)`` whose (name,
        initials) landed on no contributor — a roster gap (an author with an
        article-link but no name/initial bucket yet), a degenerate footer whose
        name field is bare initials, or an anonymous ``X.``.
      - ``votes``: ``{contributor_id -> [(name, initials), …]}`` — every RESOLVED
        signature occurrence (before the per-article dedup), so the canonical
        step-5 name/initials can be the MODE of what the source actually wrote,
        not a single index line ([[feedback_accrete_first_canonicalize_last]]).
    """
    known_initials = {ci.initials
                      for ci in session.query(ContributorInitials).all()}
    raws = raw_wikitext_by_article(session)
    binds: list[tuple[int, int, int]] = []
    unresolved: list[tuple[int, str, str]] = []
    votes: dict[int, list[tuple[str | None, str]]] = defaultdict(list)
    for aid, raw in raws.items():
        if article_ids is not None and aid not in article_ids:
            continue
        cands: list[tuple[str | None, str]] = [
            (c["full_name"], c["initials"])
            for content in _iter_footers(raw)
            for c in _parse_contributors(content)]
        for m in _AUTHOR_LINK_RE.finditer(raw):
            init = _normalize_initials(m.group(2).strip("() "))
            # A signature, not a bibliographic reference — the display's initials
            # are a KNOWN contributor's.  This roster lookup is the authoritative
            # discriminator; a pattern ("does it look like initials?") both drops
            # real signatures (A. Mü., St G., T. de L., W. MacD.) and waves
            # through references (Hus, Poe, Eus.) that would pollute the roster.
            if init in known_initials:
                cands.append((m.group(1).strip(), init))
        cands += [(None, _expand_initials_shortcut(tok))
                  for tok in _SHORTCUT_RE.findall(raw)]

        seq = 0
        seen: set[int] = set()
        for name, initials in cands:
            if not initials:
                continue
            cid = cidx.resolve(name=name, initials=initials)
            if cid is None:
                unresolved.append((aid, name or "", initials))
                continue
            votes[cid].append((name, initials))   # every resolved occurrence votes
            if cid in seen:
                continue
            seen.add(cid)
            seq += 1
            binds.append((aid, cid, seq))
    return binds, unresolved, votes


def accrete_author_link_contributors(session, cidx) -> int:
    """Add a Contributor + ContributorInitials for every author-link SIGNER who
    resolves to nobody — the roster accreting from its authoritative source.

    A footer / ``[[Author:…]]`` / shortcut signature IS a contributor identity
    (name + initials), so every signer belongs in the roster BY CONSTRUCTION — no
    per-name seeding (Woolhouse, McLachlan, and anyone else fall out for free; the
    Mc/M' fold in `_fold` already merges a signer's footer spelling with the front
    matter's).  Nameless/anonymous signatures (a bare-initials 'name', ``X.``, a
    shortcut with no name) are skipped.  New signers are clustered among
    themselves (folded surname + first initial) so one person's several footers
    become one contributor.  Returns the number of contributors added.
    ([[project_roster_from_author_links]])
    """
    _binds, unresolved, _votes = harvest_author_links(session, cidx)
    clusters: dict = defaultdict(lambda: {"names": [], "inits": set()})
    for _aid, name, init in unresolved:
        name = (name or "").strip()
        if not (name and name.lower() != "unknown"
                and re.search(r"[A-Za-z]{4,}", name)):
            continue
        tok = _name_core_tokens(name)
        key = (_fold(tok[-1]) if tok else name.lower(),
               tok[0][:1].lower() if tok else "")
        clusters[key]["names"].append(name)
        clusters[key]["inits"].add(_normalize_initials(init))
    added = 0
    for c in clusters.values():
        contrib = Contributor(full_name=max(c["names"], key=len))
        session.add(contrib)
        session.flush()
        for ini in sorted(c["inits"]):
            if ini:
                session.add(ContributorInitials(
                    contributor_id=contrib.id, initials=ini))
        added += 1
    session.commit()
    return added
