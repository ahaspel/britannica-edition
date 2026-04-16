"""Link unlinked contributors to articles using front matter subject lists.

Fallback for contributors whose footer initials didn't match.
Reads subject1/lnksubject1 fields from front matter entries and
creates article-contributor links.

Run AFTER extract-contributors (footer matching) has completed for all volumes.
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, "src")

from britannica.db.models import Article, ArticleContributor, Contributor, ContributorInitials
from britannica.db.session import SessionLocal

_ENTRY_PATTERN = re.compile(
    r"\{\{EB1911 contributor table/entry(.*?)\}\}",
    flags=re.DOTALL,
)


def _parse_field(content, field_name):
    m = re.search(
        rf"\|\s*{field_name}\s*=\s*(.*?)(?=\n\s*\||\Z)", content, re.DOTALL
    )
    return m.group(1).strip() if m else ""


def link_from_frontmatter():
    session = SessionLocal()
    try:
        # Find contributors with no article links
        linked_ids = {
            ac.contributor_id
            for ac in session.query(ArticleContributor).all()
        }
        all_contributors = session.query(Contributor).all()
        unlinked = [c for c in all_contributors if c.id not in linked_ids]
        print(f"Unlinked contributors: {len(unlinked)}")

        if not unlinked:
            print("Nothing to do.")
            return

        # Build initials -> contributor_id lookup
        initials_to_contrib = {}
        for ci in session.query(ContributorInitials).all():
            initials_to_contrib[ci.initials] = ci.contributor_id

        # Build article title -> article_id lookup
        title_map = {}
        for a in session.query(Article).all():
            title_map[a.title.upper()] = a.id

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

                    contrib_id = initials_to_contrib.get(initials)
                    if contrib_id is None or contrib_id in linked_ids:
                        continue  # already linked or unknown

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
                article_id = title_map.get(subject)
                if not article_id:
                    # Try prefix match
                    article_id = next(
                        (aid for t, aid in title_map.items() if t.startswith(subject)),
                        None,
                    )
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

        session.commit()
        print(f"Created {created} article-contributor links for {len(matched_contribs)} contributors.")

        # Report remaining unlinked
        still_unlinked = len(unlinked) - len(matched_contribs)
        print(f"Still unlinked: {still_unlinked}")

    finally:
        session.close()


if __name__ == "__main__":
    link_from_frontmatter()
