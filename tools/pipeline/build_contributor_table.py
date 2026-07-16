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

from britannica.contributors.aliases import canonical_name
from britannica.corrections import apply_corrections
from britannica.db.models import Contributor, ContributorInitials
from britannica.db.session import SessionLocal
from britannica.pipeline.stages.extract_contributors import _normalize_initials

_ENTRY_START_PATTERN = re.compile(
    r"\{\{EB1911 contributor table/entry",
)


def _iter_entries(text: str):
    """Yield the inner content of each `{{EB1911 contributor table/entry
    …}}` template, counting braces so that nested templates (like
    `brace = {{brace2|…}}`) don't prematurely terminate the match.

    The old non-greedy regex stopped at the first `}}` inside a nested
    template, dropping every entry that used one — about 93 entries,
    including Gertrude Bell, Hilda Murray, and others whose signatures
    we later found in article footers but couldn't resolve.
    """
    for m in _ENTRY_START_PATTERN.finditer(text):
        start = m.end()
        depth = 1  # we've entered the outer {{
        i = start
        while i < len(text) - 1:
            pair = text[i : i + 2]
            if pair == "{{":
                depth += 1
                i += 2
            elif pair == "}}":
                depth -= 1
                if depth == 0:
                    yield text[start:i]
                    break
                i += 2
            else:
                i += 1


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
    # Unwrap templates (keep content), then strip remaining
    prev = None
    while name != prev:
        prev = name
        name = re.sub(r"\{\{[^{}|]*\|([^{}]*)\}\}", r"\1", name)
    prev = None
    while name != prev:
        prev = name
        name = re.sub(r"\{\{[^{}]*\}\}", "", name)
    # Strip unclosed templates (keep their content after the last |)
    name = re.sub(r"\{\{[^{}|]*\|", "", name)
    # Strip HTML
    name = re.sub(r"<[^>]+>", "", name)
    # Decode entities
    name = name.replace("&thinsp;", "").replace("&nbsp;", " ")
    # Strip death date and status annotations: (d. 1907), (d.), (late), (late R.A.)
    name = re.sub(r"\s*\(d\.?\s*\d*\)\.?", "", name)
    name = re.sub(r"\s*\(late[^)]*\)\.?", "", name, flags=re.IGNORECASE)
    # Also handle unclosed variants: trailing "(d." or "(late" without closing paren
    name = re.sub(r"\s*\(d\.?\s*$", "", name)
    name = re.sub(r",?\s*\(late\s*$", "", name, flags=re.IGNORECASE)
    # Split name from credentials at first comma
    parts = name.split(",", 1)
    base_name = parts[0].strip().rstrip(".")
    credentials = parts[1].strip().rstrip(".") if len(parts) > 1 else ""
    # Validate: credentials should look like abbreviations
    if credentials and not re.search(r"[A-Z]\.", credentials):
        base_name = name.strip().rstrip(".")
        credentials = ""
    # Canonicalize: applies Unicode normalization (curly→straight quotes,
    # NFKC) AND data/contributor_aliases.json variant→canonical lookup.
    # Without this, multi-source name variants (vol 29 Index vs per-volume
    # front matter) become separate Contributor rows for the same person.
    base_name = canonical_name(base_name)
    return base_name, credentials


def _clean_description(raw_desc):
    """Clean description text."""
    import html as html_mod
    desc = raw_desc
    # Preserve article-link templates as `«BIOLINK:target|display«/BIOLINK»`
    # markers (unique sentinel so the wikilink + template strippers below
    # don't touch them).  `_resolve_bio_articles` at export time parses
    # the marker to resolve peerage-style cases (St. Cyres → Iddesleigh)
    # where simple surname-inversion can't find the biographical article.
    # The viewer hides the description's "See the biographical article…"
    # sentence entirely and renders a real link from `bio_article_filename`.
    desc = re.sub(
        r"\{\{EB1911 (?:article link|lkpl)\|([^}|]+)\|([^}]+)\}\}",
        r"«BIOLINK:\1|\2«/BIOLINK»", desc, flags=re.IGNORECASE,
    )
    desc = re.sub(
        r"\{\{EB1911 (?:article link|lkpl)\|([^}|]+)\}\}",
        r"«BIOLINK:\1|\1«/BIOLINK»", desc, flags=re.IGNORECASE,
    )
    # Unclosed variants — best-effort target capture.
    desc = re.sub(
        r"\{\{EB1911 (?:article link|lkpl)\|([^}|]+)(?:\|[^}|]*)*$",
        r"«BIOLINK:\1|\1«/BIOLINK»", desc, flags=re.IGNORECASE,
    )
    # Strip wiki links (including long 1911 Encyclopædia paths, closed and unclosed)
    desc = re.sub(r"\[\[[^\]|]+\|([^\]]+)\]\]", r"\1", desc)
    desc = re.sub(r"\[\[([^\]]+)\]\]", r"\1", desc)
    desc = re.sub(r"\[\[[^\]]*$", "", desc)
    # Unwrap formatting templates (sc, asc, font-variant, etc.)
    prev = None
    while desc != prev:
        prev = desc
        desc = re.sub(r"\{\{[^{}|]*\|([^{}]*)\}\}", r"\1", desc)
    # Strip remaining closed templates
    prev = None
    while desc != prev:
        prev = desc
        desc = re.sub(r"\{\{[^{}]*\}\}", "", desc)
    # Strip unclosed templates and fragments
    desc = re.sub(r"\{\{[^{}]*$", "", desc)
    desc = re.sub(r"^\s*\|[^|]*$", "", desc, flags=re.MULTILINE)
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
        try:
            volume = int(vol_dir.name.split("_", 1)[1])
        except (IndexError, ValueError):
            continue
        for path in sorted(vol_dir.glob("*.json")):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            raw = apply_corrections(data.get("raw_text", ""), volume)
            for content in _iter_entries(raw):
                # Normalize before the length filter — entries whose
                # raw initials field uses HTML-entity spacing (e.g.
                # vol 6's `J.&thinsp;D.&thinsp;v.&thinsp;d.&thinsp;W.`
                # for Van Der Waals) blow well past 20 chars in raw
                # form, but normalize cleanly to short canonical
                # signatures.  The same normalizer used at lookup
                # time is applied here so storage and lookup share
                # one canonical form.
                initials = _normalize_initials(_parse_field(content, "initials"))
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


def backfill_bios(apply_mode: bool = True):
    """Attach per-volume contributor bios that build_contributor_table()'s
    initials-grouping lost to a shared-initials collision — Muir's
    'Demonstrator of Pathological…' got bucketed with Muther under `R. Mr.`,
    so his separate `R. Mr.*` record shipped bio-less.

    Runs AFTER the identities are final (post vol29_linker): re-resolves each
    front-matter entry's (name, initials) through the shared ContributorIndex,
    which splits Muir from Muther by SURNAME, and fills the description /
    credentials of any contributor still missing them.  Only fills blanks —
    never overwrites.  See [[project_contributor_resolver_consolidation]]."""
    from britannica.contributors.resolver import ContributorIndex

    session = SessionLocal()
    try:
        inits = defaultdict(list)
        for ci in session.query(ContributorInitials).all():
            inits[ci.contributor_id].append(ci.initials)
        contribs = {c.id: c for c in session.query(Contributor).all()}
        idx = ContributorIndex(
            (c.id, c.full_name, inits.get(c.id, [])) for c in contribs.values())

        best: dict[int, tuple[str, str]] = {}  # cid -> (credentials, description)
        for vol_dir in sorted(Path("data/raw/wikisource").iterdir()):
            if not vol_dir.is_dir():
                continue
            try:
                volume = int(vol_dir.name.split("_", 1)[1])
            except (IndexError, ValueError):
                continue
            for path in sorted(vol_dir.glob("*.json")):
                with open(path, encoding="utf-8") as f:
                    raw = apply_corrections(json.load(f).get("raw_text", ""), volume)
                for content in _iter_entries(raw):
                    name, creds = _clean_name(_parse_field(content, "name"))
                    desc = _clean_description(_parse_field(content, "description"))
                    if not (desc or creds):
                        continue
                    cid = idx.resolve(
                        name=name,
                        initials=_normalize_initials(_parse_field(content, "initials")))
                    if cid is None:
                        continue
                    cur_creds, cur_desc = best.get(cid, ("", ""))
                    best[cid] = (
                        creds if len(creds) > len(cur_creds) else cur_creds,
                        desc if len(desc) > len(cur_desc) else cur_desc,
                    )

        filled = 0
        for cid, (creds, desc) in best.items():
            c = contribs[cid]
            changed = False
            if desc and not c.description:
                c.description = desc
                changed = True
            if creds and not c.credentials:
                c.credentials = creds
                changed = True
            if changed:
                filled += 1
        if apply_mode:
            session.commit()
        else:
            session.rollback()
        verb = "Backfilled" if apply_mode else "Would backfill"
        print(f"{verb} bio for {filled} contributors that lost it to an "
              f"initials collision." + ("" if apply_mode else "  (dry-run)"))
    finally:
        session.close()


if __name__ == "__main__":
    if "--backfill-bios" in sys.argv:
        backfill_bios()
    else:
        build_contributor_table()
