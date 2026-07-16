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

_ENTRY_PATTERN = re.compile(
    r"\{\{EB1911 contributor table/entry(.*?)\}\}",
    flags=re.DOTALL,
)


def _parse_field(content, field_name):
    m = re.search(
        rf"\|\s*{field_name}\s*=\s*(.*?)(?=\n\s*\||\Z)", content, re.DOTALL
    )
    return m.group(1).strip() if m else ""


def link_from_frontmatter(apply_mode: bool = False):
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
                for m in _ENTRY_PATTERN.finditer(raw):
                    content = m.group(1)
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

        # Match subjects to articles and create links
        created = 0
        matched_contribs = set()
        for contrib_id, subjects in contrib_subjects.items():
            for subject in subjects:
                # Unique normalized-exact only; abstain on an ambiguous collision
                # (binding to either candidate would be a 50%-wrong credit).
                cands = by_norm.get(normalize_xref_target(subject))
                article_id = cands[0] if cands and len(cands) == 1 else None
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
