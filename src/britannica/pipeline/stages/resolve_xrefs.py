import json
from collections import defaultdict
from pathlib import Path

from britannica.db.models import Article, CrossReference
from britannica.db.session import SessionLocal
from britannica.export.article_json import stable_id
from britannica.xrefs.alias_table import (
    build_alias_map,
    build_section_alias_map,
    build_vol29_index_aliases,
)
from britannica.xrefs.normalizer import normalize_xref_target
from britannica.xrefs.resolver import (
    disambiguate_among, resolve_xref_exact, resolve_xref_fuzzy,
)


_DISAMBIG_CACHE_FILE = Path("data/derived/xref_disambiguation_cache.json")
_PERSON_VARIANT_THRESHOLD = 3

# ``BIBLE (KING JAMES)/EXODUS: 4:27`` style scripture references.
# The target carries the structural form
# ``BIBLE...../<BOOK_NAME>[#chapter:verse | : chapter:verse]``;
# the right article is the EB1911 entry for that book.  Most books
# follow predictable title shapes (``EXODUS, BOOK OF`` / ``EXODUS,
# THE`` / ``DEUTERONOMY``) so this is a pure rule, no LLM needed.
import re as _re
_BIBLE_REF_RE = _re.compile(
    r"^BIBLE\b.*?/([A-Z][A-Z\s]+?)(?:\s*[:#]|$)",
    _re.IGNORECASE,
)


def _try_bible_handler(
    target: str, title_to_articles: dict[str, list[Article]]
) -> int | None:
    """Resolve ``BIBLE (KING JAMES)/EXODUS: 4:27`` form to the article
    about that book, by trying common title variants in order.

    Returns the resolved article id, or None if the book name doesn't
    correspond to any title variant we recognise.
    """
    m = _BIBLE_REF_RE.match(target)
    if not m:
        return None
    book = m.group(1).strip().upper()
    for variant in (book, f"{book}, BOOK OF", f"{book}, THE"):
        candidates = title_to_articles.get(variant)
        if candidates:
            return candidates[0].id
    return None


def _build_ambiguity_state(all_articles: list[Article]) -> tuple[
    set[str], dict[str, int], dict
]:
    """Return ``(ambiguous_titles, stable_id_to_article_id, cache)``.

    Ambiguous title := exists as standalone article AND has 3+
    ``TITLE, FirstName`` person-variant articles.  References to bare
    ``SMITH`` then go through the LLM disambiguation cache rather than
    auto-linking to the generic surname article.

    The cache file (``data/derived/xref_disambiguation_cache.json``)
    is populated by ``tools/xrefs/disambiguate_xrefs.py``.  When it
    exists, ambiguous candidates resolve to the cached choice;
    otherwise they're marked ``status='ambiguous'`` and the
    disambiguator picks them up on the next run.
    """
    person_variants: dict[str, int] = defaultdict(int)
    standalone_titles: set[str] = set()
    for a in all_articles:
        if a.article_type != "article" or not a.title:
            continue
        n = normalize_xref_target(a.title)
        if not n:
            continue
        if "," in n:
            surname = n.partition(",")[0].strip()
            if surname:
                person_variants[surname] += 1
        else:
            standalone_titles.add(n)

    ambiguous_titles = {
        surname for surname, count in person_variants.items()
        if surname in standalone_titles
        and count >= _PERSON_VARIANT_THRESHOLD
    }

    stable_id_to_article_id: dict[str, int] = {}
    for a in all_articles:
        if a.article_type != "article":
            continue
        try:
            stable_id_to_article_id[stable_id(a)] = a.id
        except Exception:
            continue

    cache: dict = {}
    if _DISAMBIG_CACHE_FILE.exists():
        try:
            cache = json.loads(
                _DISAMBIG_CACHE_FILE.read_text(encoding="utf-8")
            )
        except Exception:
            cache = {}

    return ambiguous_titles, stable_id_to_article_id, cache


def _try_disambig_cache(
    xref: CrossReference,
    source_article: Article,
    cache: dict,
    stable_id_to_article_id: dict[str, int],
) -> int | None:
    """Look up an ambiguous xref in the disambiguation cache.

    Returns the chosen ``target_article_id`` if the cache has an
    entry with a non-null ``chosen`` whose stable_id maps to a
    current article.  Returns ``None`` for cache miss OR for cached
    null (LLM said no candidate fits).  The caller distinguishes
    those cases via the cache key membership check.
    """
    sid = stable_id(source_article)
    key = f"{sid}::{xref.surface_text}::{xref.normalized_target}"
    entry = cache.get(key)
    if not entry:
        return None
    chosen = entry.get("chosen")
    if not chosen:
        return None
    return stable_id_to_article_id.get(chosen)


def resolve_xrefs_for_volume(volume: int) -> int:
    session = SessionLocal()

    try:
        articles = session.query(Article).filter(Article.volume == volume).all()
        xrefs = (
            session.query(CrossReference)
            .join(Article, CrossReference.article_id == Article.id)
            .filter(Article.volume == volume)
            .all()
        )

        resolved = 0

        for xref in xrefs:
            if xref.target_article_id is not None and xref.status == "resolved":
                continue

            target_article_id = resolve_xref_exact(xref, articles)

            if target_article_id is not None:
                xref.target_article_id = target_article_id
                xref.status = "resolved"
                resolved += 1
            else:
                xref.target_article_id = None
                xref.status = "unresolved"

        session.commit()
        return resolved

    finally:
        session.close()


def resolve_xrefs_all() -> int:
    """Resolve all unresolved xrefs against articles from any volume.

    Uses a unified lookup: canonical titles + aliases + fuzzy matching.
    Colliding titles (e.g. ZÜRICH canton vs city) are routed through
    the collision-aware `disambiguate_among` in the resolver module —
    the same code path the intra-volume pass uses — so self-references
    get filtered and display-disambiguator hints get honored.
    """
    session = SessionLocal()

    try:
        all_articles = session.query(Article).all()

        # Collision-aware canonical map: title (UPPER) → list[Article].
        # 580 titles in the corpus are shared by 2+ articles (ABBAS I,
        # ABDERA, ABERDEEN, ZÜRICH, …); the legacy single-value dict
        # silently dropped all but one candidate.
        title_to_articles: dict[str, list[Article]] = defaultdict(list)
        for a in all_articles:
            if a.article_type == "plate":
                continue
            key = (a.title or "").strip().upper()
            if key:
                title_to_articles[key].append(a)

        # Aliases: same guard as before — don't overwrite canonical
        # titles.  When the canonical has collisions, the alias
        # inherits the full candidate list so disambiguation applies
        # uniformly.
        alias_map = build_alias_map()
        for alias, canonical in alias_map.items():
            if alias not in title_to_articles and canonical in title_to_articles:
                title_to_articles[alias] = title_to_articles[canonical]

        section_map = build_section_alias_map()
        section_lookup: dict[str, str] = {}
        for alias, canonical in section_map.items():
            if alias not in title_to_articles and canonical in title_to_articles:
                title_to_articles[alias] = title_to_articles[canonical]
                section_lookup[alias] = alias

        vol29_map = build_vol29_index_aliases()
        for alias, canonical in vol29_map.items():
            if alias not in title_to_articles and canonical in title_to_articles:
                title_to_articles[alias] = title_to_articles[canonical]

        # Fuzzy matching still needs a plain title→id map.  Include
        # all titles (picking the first candidate for collisions) so
        # fuzzy retains the coverage it had before collision-aware
        # lookup landed — fuzzy has no xref-side signal to disambiguate,
        # and the first-wins fallback matches what disambiguate_among
        # does when no rule fires.
        title_map: dict[str, int] = {
            k: v[0].id
            for k, v in title_to_articles.items()
        }

        # Ambiguity routing — bare-surname targets (SMITH, GRAY, …)
        # whose generic article exists alongside 3+ person-variants
        # ("SMITH, ADAM") consult the LLM disambiguation cache before
        # falling through to default resolution.
        #
        # Per-entry opt-in: cache HIT → use the chosen target.  Cache
        # MISS → fall through to normal title-match (same behaviour
        # as before the disambiguator existed).  This means a partial
        # cache only improves the entries it covers; uncached
        # ambiguous candidates aren't degraded to ``status='ambiguous'``,
        # they keep their pre-disambig resolution.  Coverage
        # improvements (new extractor patterns) ship independently of
        # disambiguator runs.
        ambiguous_titles, stable_id_to_article_id, disambig_cache = (
            _build_ambiguity_state(all_articles)
        )
        articles_by_id = {a.id: a for a in all_articles}

        unresolved = (
            session.query(CrossReference)
            .filter(CrossReference.status == "unresolved")
            .all()
        )
        # Currently-resolved xrefs targeting an ambiguous title need
        # re-evaluation when the cache has gained an entry that
        # would route them differently.  Only relevant if the cache
        # has any entries.
        if disambig_cache and ambiguous_titles:
            previously_resolved_ambiguous = (
                session.query(CrossReference)
                .filter(
                    CrossReference.status == "resolved",
                    CrossReference.normalized_target.in_(ambiguous_titles),
                )
                .all()
            )
        else:
            previously_resolved_ambiguous = []

        resolved = 0

        for xref in unresolved + previously_resolved_ambiguous:
            target = xref.normalized_target.strip().upper()
            target_article_id: int | None = None
            section: str | None = None

            # 0. Ambiguous-title routing.  If the target matches one
            # of the surname-with-variants titles AND the cache has
            # an entry, route to the cached choice.  Cache miss
            # falls through to normal resolution — preserves
            # pre-disambig behaviour for unprocessed entries so
            # partial cache deployments never degrade existing links.
            if target in ambiguous_titles:
                source = articles_by_id.get(xref.article_id)
                cached_target = (
                    _try_disambig_cache(
                        xref, source, disambig_cache,
                        stable_id_to_article_id,
                    )
                    if source is not None else None
                )
                if cached_target is not None:
                    xref.target_article_id = cached_target
                    xref.target_section = None
                    xref.status = "resolved"
                    resolved += 1
                    continue
                # else: cache miss → fall through to normal resolution.

            # 1. Exact title / alias / section-alias (collision-aware)
            candidates = title_to_articles.get(target)
            if candidates:
                target_article_id = disambiguate_among(xref, candidates)
                if target in section_lookup:
                    section = section_lookup[target]

            # 1b. Bible-reference handler: ``BIBLE (KING JAMES)/EXODUS:
            # 4:27`` → EXODUS, BOOK OF.  Deterministic, fast,
            # matches ~45 unresolved entries cleanly.  No LLM needed.
            if target_article_id is None:
                target_article_id = _try_bible_handler(
                    target, title_to_articles
                )

            # 2. Section-suffix form: "EUROPE: HISTORY" -> (EUROPE, HISTORY)
            if target_article_id is None and ": " in target:
                base, _, suffix = target.rpartition(": ")
                base = base.strip()
                suffix = suffix.strip()
                base_candidates = title_to_articles.get(base)
                if base_candidates and suffix:
                    target_article_id = disambiguate_among(
                        xref, base_candidates
                    )
                    section = suffix

            # 3. Fuzzy matching (plurals, name inversion, section-strip, etc.)
            if target_article_id is None:
                target_article_id = resolve_xref_fuzzy(xref, title_map)

            # 4. LLM-resolved unresolveds (last-resort fall-back).
            # When everything above has missed, check whether
            # ``tools/xrefs/resolve_unresolved.py`` has a cached
            # decision for this xref.  Same cache file as the
            # ambiguous-surname disambig path; same key shape; same
            # opt-in semantics (no cache → no behaviour change).
            if target_article_id is None and disambig_cache:
                source = articles_by_id.get(xref.article_id)
                if source is not None:
                    cached_target = _try_disambig_cache(
                        xref, source, disambig_cache,
                        stable_id_to_article_id,
                    )
                    if cached_target is not None:
                        target_article_id = cached_target

            if target_article_id is not None:
                xref.target_article_id = target_article_id
                xref.target_section = section
                xref.status = "resolved"
                resolved += 1

        session.commit()
        return resolved

    finally:
        session.close()