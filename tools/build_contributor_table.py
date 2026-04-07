"""Build the master contributor table from front matter entries.

Parses all {{EB1911 contributor table/entry}} templates across all volumes,
deduplicates by initials then by canonical name, and populates the
contributors and contributor_initials tables.

Run AFTER truncate (clean DB) and BEFORE extract-contributors (which
links initials to articles via the contributor_initials table).
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, "src")

from britannica.db.models import Contributor, ContributorInitials
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


def _clean_name(raw_name):
    """Extract clean name from wiki markup, separating credentials."""
    # Strip author links: [[Author:X|Display]] → Display
    name = re.sub(r"\[\[Author:[^|]*\|([^\]]+)\]\]", r"\1", raw_name)
    name = re.sub(r"\[\[([^\]]+)\]\]", r"\1", name)
    # Strip bold/italic
    name = name.replace("'''", "").replace("''", "")
    # Strip templates
    prev = None
    while name != prev:
        prev = name
        name = re.sub(r"\{\{[^{}]*\}\}", "", name)
    # Strip HTML
    name = re.sub(r"<[^>]+>", "", name)
    # Decode entities
    name = name.replace("&thinsp;", "").replace("&nbsp;", " ")
    # Split name from credentials at first comma
    parts = name.split(",", 1)
    base_name = parts[0].strip().rstrip(".")
    credentials = parts[1].strip().rstrip(".") if len(parts) > 1 else ""
    # Validate: credentials should look like abbreviations
    if credentials and not re.search(r"[A-Z]\.", credentials):
        base_name = name.strip().rstrip(".")
        credentials = ""
    return base_name, credentials


def _clean_description(raw_desc):
    """Clean description text."""
    import html as html_mod
    desc = raw_desc
    desc = re.sub(r"\{\{EB1911 article link\|([^}|]+)(?:\|[^}]*)?\}\}", r"\1", desc)
    prev = None
    while desc != prev:
        prev = desc
        desc = re.sub(r"\{\{[^{}]*\}\}", "", desc)
    desc = re.sub(r"\[\[[^\]|]+\|([^\]]+)\]\]", r"\1", desc)
    desc = re.sub(r"\[\[([^\]]+)\]\]", r"\1", desc)
    desc = desc.replace("'''", "").replace("''", "")
    desc = re.sub(r"<[^>]+>", "", desc)
    desc = html_mod.unescape(desc)
    desc = desc.replace("\xa0", " ")
    desc = " ".join(desc.split()).strip().rstrip(".")
    return desc


def build_contributor_table():
    raw_dir = Path("data/raw/wikisource")

    # Step 1: Parse all (initials, name, credentials, description) entries
    entries = []  # (raw_initials, raw_name, description_text)
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
                if not initials or len(initials) > 20:
                    continue
                raw_name = _parse_field(content, "name")
                raw_desc = _parse_field(content, "description")
                entries.append((initials, raw_name, raw_desc))

    print(f"Parsed {len(entries)} front matter entries.")

    # Step 2: Deduplicate to unique (initials, name) pairs
    pairs = set()
    for initials, raw_name, raw_desc in entries:
        pairs.add((initials, raw_name))
    print(f"Unique (initials, name) pairs: {len(pairs)}")

    # Step 3: Group by initials → each group is one person with name variants
    by_initials = defaultdict(list)  # initials -> [(raw_name, raw_desc)]
    for initials, raw_name, raw_desc in entries:
        by_initials[initials].append((raw_name, raw_desc))

    # For each initials group, pick canonical name (longest cleaned name)
    # and best credentials/description
    initials_groups = {}  # initials -> {name, credentials, description}
    for initials, name_desc_list in by_initials.items():
        names_and_creds = [_clean_name(nd[0]) for nd in name_desc_list]
        descs = [_clean_description(nd[1]) for nd in name_desc_list if nd[1]]

        best_name = max((nc[0] for nc in names_and_creds), key=len)
        best_creds = max((nc[1] for nc in names_and_creds), key=len) if any(nc[1] for nc in names_and_creds) else ""
        best_desc = max(descs, key=len) if descs else ""

        initials_groups[initials] = {
            "name": best_name,
            "credentials": best_creds,
            "description": best_desc,
        }

    print(f"Initials groups: {len(initials_groups)}")

    # Step 4: Merge across initials by canonical name
    # Group initials that share the same canonical name → same person
    by_name = defaultdict(list)  # canonical_name -> [initials]
    for initials, data in initials_groups.items():
        by_name[data["name"]].append(initials)

    # Each name group is one contributor with potentially multiple initials
    contributors = []  # {name, credentials, description, initials: [list]}
    for name, initials_list in by_name.items():
        # Merge credentials and descriptions across all initials variants
        all_creds = [initials_groups[i]["credentials"] for i in initials_list]
        all_descs = [initials_groups[i]["description"] for i in initials_list]

        best_creds = max(all_creds, key=len) if any(all_creds) else ""
        best_desc = max(all_descs, key=len) if any(all_descs) else ""

        contributors.append({
            "name": name,
            "credentials": best_creds,
            "description": best_desc,
            "initials": initials_list,
        })

    merges = sum(1 for c in contributors if len(c["initials"]) > 1)
    print(f"Final contributors: {len(contributors)} ({merges} merged from multiple initials)")

    # Step 5: Write to DB
    session = SessionLocal()
    try:
        for c in contributors:
            contributor = Contributor(
                full_name=c["name"],
                credentials=c["credentials"] or None,
                description=c["description"] or None,
            )
            session.add(contributor)
            session.flush()

            for initials in c["initials"]:
                session.add(ContributorInitials(
                    contributor_id=contributor.id,
                    initials=initials,
                ))

        session.commit()

        # Stats
        total = session.query(Contributor).count()
        total_initials = session.query(ContributorInitials).count()
        with_creds = session.query(Contributor).filter(
            Contributor.credentials != None, Contributor.credentials != ""
        ).count()
        with_desc = session.query(Contributor).filter(
            Contributor.description != None, Contributor.description != ""
        ).count()
        print(f"\nCreated {total} contributors with {total_initials} initials entries.")
        print(f"  With credentials: {with_creds}")
        print(f"  With descriptions: {with_desc}")

    finally:
        session.close()


if __name__ == "__main__":
    build_contributor_table()
