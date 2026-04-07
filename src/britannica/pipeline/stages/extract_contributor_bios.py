"""Extract contributor biographical data from front matter tables.

Parses {{EB1911 contributor table/entry}} templates from raw wikitext
to populate credentials and descriptions for Contributor records.
"""

import json
import re
import glob
from pathlib import Path

from britannica.db.models import Contributor
from britannica.db.session import SessionLocal


_RAW_DIRS = [Path("data/raw/wikisource")]

_ENTRY_PATTERN = re.compile(
    r"\{\{EB1911 contributor table/entry(.*?)\}\}",
    flags=re.DOTALL,
)


def _parse_entry(content: str) -> dict[str, str]:
    """Parse a contributor table entry into fields."""
    fields = {}
    for m in re.finditer(r"\|\s*(\w+)\s*=\s*(.*?)(?=\n\s*\||\Z)", content, re.DOTALL):
        key = m.group(1).strip()
        value = m.group(2).strip()
        # Clean wiki markup
        value = re.sub(r"\[\[[^\]|]+\|([^\]]+)\]\]", r"\1", value)
        value = re.sub(r"\[\[([^\]]+)\]\]", r"\1", value)
        value = value.replace("'''", "").replace("''", "")
        # Iteratively strip templates (handles nesting)
        prev = None
        while value != prev:
            prev = value
            value = re.sub(r"\{\{[^{}]*\}\}", "", value)
        # Strip unclosed templates
        value = re.sub(r"\{\{[^{}]*$", "", value)
        # Decode HTML entities
        import html as html_mod
        value = html_mod.unescape(value)
        # Strip any remaining HTML tags
        value = re.sub(r"<[^>]+>", "", value)
        value = value.replace("\xa0", " ")  # non-breaking space
        value = " ".join(value.split()).strip().rstrip(".")
        if value:
            fields[key] = value
    return fields


def extract_contributor_bios() -> int:
    """Update Contributor records with biographical data from front matter."""
    session = SessionLocal()

    try:
        updated = 0

        for raw_dir in _RAW_DIRS:
            if not raw_dir.exists():
                continue
            for subdir in sorted(raw_dir.iterdir()):
                if not subdir.is_dir():
                    continue
                for path in sorted(subdir.glob("*.json")):
                    with open(path, encoding="utf-8") as f:
                        data = json.load(f)
                    raw = data.get("raw_text", "")

                    for m in _ENTRY_PATTERN.finditer(raw):
                        fields = _parse_entry(m.group(1))
                        initials = fields.get("initials", "").strip()
                        if not initials or len(initials) > 20 or "<" in initials or "{" in initials:
                            continue

                        # Find existing contributor — never create new ones
                        # (only contributors linked to articles matter)
                        contributor = (
                            session.query(Contributor)
                            .filter(Contributor.initials == initials)
                            .first()
                        )
                        if not contributor:
                            continue

                        # Update with biographical data
                        name = fields.get("name")
                        description = fields.get("description")

                        if name:
                            # Extract credentials (after the name)
                            # e.g. "Alfred Barton Rendle, F.R.S., F.L.S., D.Sc"
                            parts = name.split(",", 1)
                            if len(parts) > 1:
                                base_name = parts[0].strip()
                                creds = parts[1].strip()
                                if not contributor.credentials:
                                    contributor.credentials = creds
                                # Always use the base name without credentials
                                contributor.full_name = base_name

                        if description:
                            if not contributor.description or len(description) > len(contributor.description):
                                contributor.description = description
                                updated += 1

        session.commit()
        return updated

    finally:
        session.close()
