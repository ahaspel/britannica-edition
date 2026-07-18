"""Credit contributors with articles from the per-volume front-matter tables.

Each volume's `{{EB1911 contributor table/entry}}` lists a contributor's
subjects (subject1/lnksubject1…); this binds every one that resolves to an
article.  Like the vol 29 master index
([[project_vol29_contributor_attributions]]) this is an authoritative
per-volume record, so we credit a contributor with ALL their resolved
subjects — not only contributors who are otherwise orphaned; the per-link
dedup below prevents any double-bind.

Run AFTER extract-contributors (footer matching).
"""
import json
import re
from collections import defaultdict
from pathlib import Path

from britannica.contributors.resolver import ContributorIndex
from britannica.db.models import Article, ArticleContributor, Contributor, ContributorInitials
from britannica.db.session import SessionLocal
from britannica.xrefs.normalizer import normalize_xref_target
from britannica.xrefs.resolver import build_core_maps

_ENTRY_MARKER = "{{EB1911 contributor table/entry"


def _iter_entries(raw):
    """Yield the brace-balanced inner content of each contributor-table entry.

    Entries embed inner templates ({{brace2}}, {{fwn}}, {{EB1911 Article Link}}),
    so a non-greedy ``(.*?)}}`` stops at the FIRST inner ``}}`` and drops every
    subject after it — which silently truncated ~2/3 of all entries and
    suppressed thousands of front-matter binds.  Count braces and stop at the
    entry's OWN closing ``}}`` instead.
    """
    i = 0
    while True:
        j = raw.find(_ENTRY_MARKER, i)
        if j < 0:
            return
        depth, k, n = 0, j, len(raw)
        while k < n:
            if raw[k:k + 2] == "{{":
                depth += 1
                k += 2
            elif raw[k:k + 2] == "}}":
                depth -= 1
                k += 2
                if depth == 0:
                    break
            else:
                k += 1
        yield raw[j + len(_ENTRY_MARKER):k - 2]
        i = k


def _clean_subject(v):
    """Strip wiki/template/italic markup from a front-matter subject value."""
    v = re.sub(r"\[\[[^\]|]*\|([^\]]+)\]\]", r"\1", v)
    v = re.sub(r"\[\[([^\]]+)\]\]", r"\1", v)
    v = re.sub(r"\{\{[^{}|]*\|?", "", v)
    v = v.replace("}}", "").replace("''", "")
    v = re.sub(r"<[^>]+>", "", v)
    return v.strip()


def _subject_variants(subject):
    """Fallback forms so a disambiguated or section-qualified subject still
    resolves: 'PHILO (PHILOSOPHER)' -> 'PHILO', 'UNITED STATES, THE/GEOLOGY' ->
    'UNITED STATES, THE'.  Each still goes through the unique-exact matcher, so
    an ambiguous fallback simply abstains (never a wrong credit)."""
    yield subject
    base = re.sub(r"\s*\([^)]*\)\s*$", "", subject).strip()
    if base and base != subject:
        yield base
    head = re.split(r"[/:]", subject, 1)[0].strip()
    if head and head != subject:
        yield head


def _word_count(body):
    return len(re.sub(r"«[^»]*»", " ", body or "").split())


def _disambiguate_by_footprint(session, contrib_id, cand_ids, kind_of):
    """Pick among homonymous article candidates from what we already know about
    the contributor: co-authorship proximity (same volume, nearest page to their
    OTHER resolved articles — Conder co-authored GALILEE, SEA OF, next to the
    region GALILEE not the architectural galilee), matching kind, and substance
    (the longer article — Philo the philosopher, not the 84-word poet).  Returns
    the single best candidate id, or None when nothing separates them by a clear
    margin.  Length is a RELATIVE tiebreak only — it decides among homonyms but
    never filters a unique match (EB1911 signs bios as short as ~70 words)."""
    cand_set = set(cand_ids)
    bound = [ac.article_id for ac in session.query(ArticleContributor)
             .filter(ArticleContributor.contributor_id == contrib_id).all()
             if ac.article_id not in cand_set]
    known = (session.query(Article).filter(Article.id.in_(bound)).all()
             if bound else [])
    cands = session.query(Article).filter(Article.id.in_(cand_ids)).all()
    profile = set()
    if kind_of:
        for b in bound:
            profile |= kind_of(b)

    def score(ca):
        s = 0.0
        for ka in known:
            if ka.volume == ca.volume:
                s += 1.0
                if ka.page_start is not None and ca.page_start is not None:
                    s += max(0.0, 5.0 - abs(ka.page_start - ca.page_start))
        if kind_of and (kind_of(ca.id) & profile):
            s += 3.0
        s += min(_word_count(ca.body), 3000) / 1000.0
        return s

    ranked = sorted(cands, key=score, reverse=True)
    if len(ranked) >= 2 and score(ranked[0]) - score(ranked[1]) >= 0.5:
        return ranked[0].id
    return None


def _parse_field(content, field_name):
    m = re.search(
        rf"\|\s*{field_name}\s*=\s*(.*?)(?=\n\s*\||\Z)", content, re.DOTALL
    )
    return m.group(1).strip() if m else ""


def link_from_frontmatter(apply_mode: bool = False, kind_of=None):
    session = SessionLocal()
    try:
        # The single contributor resolver
        # ([[project_contributor_resolver_consolidation]]): the entry's name AND
        # initials → id, surname-aware.  The front-matter table gives both, so
        # this replaces the old name-discarding last-wins initials map (which
        # mis-credited Muir's PATHOLOGY to Muther and Babelon to Breck).
        inits = defaultdict(list)
        for ci in session.query(ContributorInitials).all():
            inits[ci.contributor_id].append(ci.initials)
        idx = ContributorIndex((c.id, c.full_name, inits.get(c.id, []))
                               for c in session.query(Contributor).all())

        # Article resolution via the shared INDEX core ([[project_resolver_consolidation]]),
        # but NOT the fuzzy cascade: contributor linking is the zero-false-positive
        # context ([[feedback_contributor_zero_false_positives]]), and the cascade's
        # entity-altering strategies mis-bind distinct people/places (STEPHEN, ST →
        # SIR JAMES STEPHEN; WOLFF, CHRISTIAN → CASPAR WOLFF; ZÜRICH canton+town → one).
        by_norm, _ = build_core_maps(
            ((a.title, a.id) for a in session.query(Article).all()
             if a.article_type == "article"),
            value_of=lambda x: x,
        )

        # Parse front matter for subject lists
        raw_dir = Path("data/raw/wikisource")
        contrib_subjects = defaultdict(set)  # contributor_id -> set of article titles

        for vol_dir in sorted(raw_dir.iterdir()):
            if not vol_dir.is_dir():
                continue
            for path in sorted(vol_dir.glob("*.json")):
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                raw = data.get("raw_text", "")
                for content in _iter_entries(raw):
                    initials = _parse_field(content, "initials").strip()
                    if not initials:
                        continue
                    name = _parse_field(content, "name")
                    name = re.sub(r"\[\[[^\]|]*\|([^\]]+)\]\]", r"\1", name)
                    name = re.sub(r"\[\[([^\]]+)\]\]", r"\1", name)
                    name = re.sub(r"<[^>]+>", "", name).strip()

                    contrib_id = idx.resolve(name=name, initials=initials)
                    if contrib_id is None:
                        continue  # unresolved

                    # Collect all lnksubject fields
                    for n in range(1, 20):
                        lnk = _parse_field(content, f"lnksubject{n}")
                        if not lnk:
                            # Try plain subject
                            lnk = _parse_field(content, f"subject{n}")
                        if not lnk:
                            break
                        # Clean wiki markup
                        lnk = re.sub(r"\[\[[^\]|]*\|([^\]]+)\]\]", r"\1", lnk)
                        lnk = re.sub(r"\[\[([^\]]+)\]\]", r"\1", lnk)
                        lnk = re.sub(r"<[^>]+>", "", lnk)
                        lnk = lnk.strip()
                        if lnk:
                            contrib_subjects[contrib_id].add(lnk.upper())

        # Match subjects to articles and create links.  Try the subject in
        # progressively more forgiving forms (_subject_variants: exact →
        # disambiguator-stripped → section-head), binding the first that
        # resolves: a UNIQUE normalized match binds directly; a homonym collision
        # ("Philo" → two articles) goes to the footprint/kind disambiguator, which
        # abstains unless one candidate clearly wins — never a 50%-wrong guess.
        # Without this, Salisbury's "United States, The/Geology" and Schürer's
        # "Philo (philosopher)" resolve to nothing and their authors go uncredited.
        created = 0
        matched_contribs = set()
        for contrib_id, subjects in contrib_subjects.items():
            for subject in subjects:
                article_id = None
                for variant in _subject_variants(subject):
                    cands = by_norm.get(normalize_xref_target(variant)) or []
                    if len(cands) == 1:
                        article_id = cands[0]
                        break
                    if len(cands) > 1:
                        article_id = _disambiguate_by_footprint(
                            session, contrib_id, cands, kind_of)
                        if article_id:
                            break
                if article_id:
                    existing = (
                        session.query(ArticleContributor)
                        .filter(
                            ArticleContributor.article_id == article_id,
                            ArticleContributor.contributor_id == contrib_id,
                        )
                        .first()
                    )
                    if not existing:
                        session.add(ArticleContributor(
                            article_id=article_id,
                            contributor_id=contrib_id,
                            sequence=99,  # appended after footer-matched contributors
                        ))
                        created += 1
                        matched_contribs.add(contrib_id)

        if apply_mode:
            session.commit()
        else:
            session.rollback()
        verb = "Created" if apply_mode else "Would create"
        print(f"{verb} {created} article-contributor links "
              f"for {len(matched_contribs)} contributors.")
        if not apply_mode:
            print("(dry-run; pass --apply to commit)")

    finally:
        session.close()


if __name__ == "__main__":
    import sys
    link_from_frontmatter(apply_mode="--apply" in sys.argv)
