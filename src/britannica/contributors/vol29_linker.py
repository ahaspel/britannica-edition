"""Reconcile the master DB contributor table with vol 29's master Index
of Contributors.

Designed to run as a step inside `tools/db/rebuild_contributors.py`,
between `build_contributor_table.py` (which populates contributors
from per-volume front matter) and `extract_contributors` (which binds
body-footer signatures to ContributorInitials rows).  In that fresh-
rebuild context, no `ArticleContributor` rows exist yet — so the
linker's job is purely to ensure the DB has the right Contributor
records and the right ContributorInitials keys before the body-footer
extractor runs.

Conservative-by-default: the linker auto-applies INSERT, ADD_INITIALS,
and RE_KEY_INITIALS only.  Anything that would require deciding
*between* two existing contributors with no clear vol-29 disambiguator
is flagged NEEDS_REVIEW and listed in the dry-run report.

Two upgrade passes turn most NEEDS_REVIEW cases into auto-applicable
actions:

- **Group X** — vol 29 duplicate-initials false positive.  When vol
  29's Vision OCR has two entries sharing the same canonical initials
  key (the classic OCR-lost-asterisk pattern, e.g. `L. Be.` for both
  Bell and Bénédite, `V. C.` for both Caillard and Chirol), and the
  DB already has those contributors distinguished under their own
  initials, classify NO_OP — the DB is correct, the linker just
  couldn't tell from one vol 29 entry alone.

- **Group Y** — paired re-key.  When a vol 29 entry wants initials K
  which DB currently routes to a different contributor X, AND vol 29
  has another entry for X assigning them a different initials K' which
  is currently free in DB, emit a pair: RE_KEY (X: K → K') + INSERT
  (new contributor at K).  Babelon/Breck textbook.
"""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field

from britannica.contributors.vol29_index import Vol29Entry
from britannica.db.models import ArticleContributor, Contributor, ContributorInitials
from britannica.pipeline.stages.extract_contributors import _normalize_initials


# --- Action types -----------------------------------------------------------

INSERT = "INSERT"                 # auto-apply: new Contributor + new initials
ADD_INITIALS = "ADD_INITIALS"     # auto-apply: existing person, new initials
RE_KEY_INITIALS = "RE_KEY_INITIALS"  # auto-apply: existing initials row's value changes
NEEDS_REVIEW = "NEEDS_REVIEW"     # never auto-applied
NO_OP = "NO_OP"                   # already correct


@dataclass
class Action:
    """One linker decision for one vol 29 entry."""

    kind: str
    entry: Vol29Entry
    reason: str
    contributor_id: int | None = None
    target_initials: str | None = None
    old_initials: str | None = None  # only used for RE_KEY_INITIALS
    extra: dict = field(default_factory=dict)


# --- Name-folding helpers ---------------------------------------------------

# Honorifics, ranks, and other non-name tokens to strip when comparing
# names across vol 29 / per-volume tables / DB records.  Mirrors the
# logic used in tmp_compare_vol29.py.
_HONORIFIC = re.compile(
    r"\b(?:sir|rev\.?|dr\.?|hon\.?|right\s+hon\.?|most\s+rev\.?|"
    r"very\s+rev\.?|the\s+hon\.?|prof\.?|professor|lord|lady|"
    r"dame|major|captain|colonel|lieut\.?-?colonel|lieut\.?-?col\.?|"
    r"lt\.?|lieut\.?|admiral|mrs\.?|miss|baron|count|cardinal|"
    r"bishop|archbishop|major-general|general|brig\.?-?general|"
    r"st|ven\.?|rt\.?\s*rev\.?|rt\.?\s*hon\.?|the\s+earl\s+of)\b\.?\s*",
    re.IGNORECASE,
)


def fold_name(s: str) -> str:
    """Normalise a contributor name for comparison: drop credentials,
    parenthetical qualifiers, accents, honorifics, punctuation, and
    case.  Result is a whitespace-separated lowercase token sequence
    suitable for set-equality and subset comparisons."""
    if not s:
        return ""
    s = re.sub(r"\s*\([^)]*\)", " ", s)
    s = s.split(",", 1)[0]
    s = "".join(
        c for c in unicodedata.normalize("NFKD", s)
        if not unicodedata.combining(c)
    )
    while True:
        s2 = _HONORIFIC.sub("", s)
        if s2 == s:
            break
        s = s2
    s = re.sub(r"[.,]+", "", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def name_tokens(s: str) -> frozenset[str]:
    """Token-set form of a folded name; tokens shorter than 2 chars
    (typically initials and middle-initial letters) are dropped to
    avoid spurious overlaps."""
    return frozenset(w for w in fold_name(s).split() if len(w) >= 2)


# --- DB snapshot ------------------------------------------------------------


@dataclass
class DBSnapshot:
    """In-memory cache of contributor tables for fast linker lookups.

    Built once at the start of a linker run; eliminates per-entry DB
    queries during classification.
    """

    contributors_by_id: dict[int, Contributor]
    initials_to_contributor: dict[str, Contributor]  # normalised → owner
    contributors_by_token_set: dict[frozenset[str], list[Contributor]]


def snapshot_db(session) -> DBSnapshot:
    """Snapshot the current Contributor / ContributorInitials state."""
    by_id: dict[int, Contributor] = {}
    by_tokens: dict[frozenset[str], list[Contributor]] = {}
    for c in session.query(Contributor).all():
        by_id[c.id] = c
        toks = name_tokens(c.full_name)
        if toks:
            by_tokens.setdefault(toks, []).append(c)

    initials_to_contributor: dict[str, Contributor] = {}
    for ci in session.query(ContributorInitials).all():
        norm = _normalize_initials(ci.initials)
        c = by_id.get(ci.contributor_id)
        if c:
            # First wins on duplicates (which shouldn't exist post-
            # corrections.json, but defensively).
            initials_to_contributor.setdefault(norm, c)

    return DBSnapshot(
        contributors_by_id=by_id,
        initials_to_contributor=initials_to_contributor,
        contributors_by_token_set=by_tokens,
    )


# --- Classification ---------------------------------------------------------


def is_unreadable(entry: Vol29Entry) -> bool:
    """A `[?]` marker (Vision-OCR's unreadable sentinel) anywhere in
    the name or initials means we can't trust the entry."""
    return "[?]" in entry.full_name or "[?]" in entry.initials


def find_by_name(db: DBSnapshot, entry: Vol29Entry) -> list[Contributor]:
    """DB contributors matching the vol 29 entry's folded name.

    Tiebreak rule: if any DB record has the EXACT same token set as
    the vol 29 entry, return only those — even if other DB records'
    token sets would also subset-overlap.  This prevents a vol 29
    entry like "Edward Armstrong" from spuriously matching DB record
    "Henry Edward Armstrong" via the subset rule when the simpler
    "Edward Armstrong" record is right there.  Subset matching is
    used only when no exact-match candidate exists (i.e. the vol 29
    name has a middle name the DB doesn't, or vice versa).
    """
    et = name_tokens(entry.full_name)
    if not et:
        return []
    # Prefer exact token-set match.
    exact = db.contributors_by_token_set.get(et)
    if exact:
        return list(exact)
    # Fall back to subset match.
    matches: list[Contributor] = []
    seen: set[int] = set()
    for tokens, contribs in db.contributors_by_token_set.items():
        if not (et & tokens):
            continue
        if et.issubset(tokens) or tokens.issubset(et):
            for c in contribs:
                if c.id not in seen:
                    matches.append(c)
                    seen.add(c.id)
    return matches


def classify(entry: Vol29Entry, db: DBSnapshot) -> Action:
    """Decide what to do with one vol 29 entry."""
    if is_unreadable(entry):
        return Action(
            NEEDS_REVIEW, entry,
            "Vision OCR marked an unreadable token ([?]) in name or initials",
        )

    target = _normalize_initials(entry.initials)
    if not target:
        return Action(
            NEEDS_REVIEW, entry,
            "initials parsed empty after normalisation",
        )

    init_owner = db.initials_to_contributor.get(target)
    name_matches = find_by_name(db, entry)
    name_match_ids = {c.id for c in name_matches}

    # Case A: ideal match — the DB initials owner is among the name matches.
    if init_owner is not None and init_owner.id in name_match_ids:
        return Action(
            NO_OP, entry,
            f"already correct: id={init_owner.id} {init_owner.full_name!r} owns {target!r}",
        )

    # Case B: nothing in DB at all — clean INSERT.
    if init_owner is None and not name_matches:
        return Action(
            INSERT, entry,
            f"new contributor (no DB match for name or initials)",
            target_initials=target,
        )

    # Case C: person is in DB by name; the canonical initials key is free.
    if init_owner is None and len(name_matches) == 1:
        c = name_matches[0]
        return Action(
            ADD_INITIALS, entry,
            f"add {target!r} to existing id={c.id} {c.full_name!r}",
            contributor_id=c.id,
            target_initials=target,
        )

    # Case D: name-fold matches multiple DB contributors → ambiguous.
    if init_owner is None and len(name_matches) > 1:
        return Action(
            NEEDS_REVIEW, entry,
            "name-fold matches multiple DB contributors: "
            + ", ".join(f"id={c.id} {c.full_name!r}" for c in name_matches),
            extra={"candidate_ids": sorted(name_match_ids)},
        )

    # Case E: initials owned but no name match in DB.
    # Could be a name-fold miss (vol 29 spells differently from DB) or a
    # genuine collision where vol 29 reassigns the initials.  Conservative:
    # if there's any token overlap between the init owner's name and the
    # vol 29 name, treat as the same person (NO_OP).  Otherwise NEEDS_REVIEW.
    if init_owner is not None and not name_matches:
        if name_tokens(init_owner.full_name) & name_tokens(entry.full_name):
            return Action(
                NO_OP, entry,
                f"init owner id={init_owner.id} {init_owner.full_name!r} "
                f"likely matches vol 29 {entry.full_name!r} via partial token overlap",
            )
        return Action(
            NEEDS_REVIEW, entry,
            f"initials {target!r} currently owned by id={init_owner.id} "
            f"{init_owner.full_name!r}, but vol 29 says {entry.full_name!r} "
            f"(no name-fold overlap; possible collision case)",
            extra={"colliding_owner_id": init_owner.id},
        )

    # Case F: both exist, but they're different contributors.
    # Likely a re-key situation (the existing init owner has another vol 29
    # entry with different initials).  The linker doesn't auto-handle these;
    # human reviewer decides.
    return Action(
        NEEDS_REVIEW, entry,
        f"name match id={name_matches[0].id} {name_matches[0].full_name!r} "
        f"differs from initials owner id={init_owner.id} "
        f"{init_owner.full_name!r}; likely a paired re-key (e.g. Babelon/Breck)",
        extra={
            "name_match_id": name_matches[0].id,
            "init_owner_id": init_owner.id,
        },
    )


def build_plan(entries: list[Vol29Entry], db: DBSnapshot) -> list[Action]:
    """Classify each vol 29 entry, then post-process NEEDS_REVIEW items
    into auto-applicable actions where vol-29 cross-entry context allows.
    """
    actions = [classify(e, db) for e in entries]

    # Build vol-29 indices once
    vol29_by_initials: dict[str, list[Vol29Entry]] = defaultdict(list)
    vol29_by_name_tokens: dict[frozenset[str], list[Vol29Entry]] = defaultdict(list)
    for e in entries:
        if is_unreadable(e):
            continue
        target = _normalize_initials(e.initials)
        if target:
            vol29_by_initials[target].append(e)
        toks = name_tokens(e.full_name)
        if toks:
            vol29_by_name_tokens[toks].append(e)

    upgraded: list[Action] = []
    rekey_actions: list[Action] = []
    seen_rekeys: set[tuple[int, str]] = set()  # (contributor_id, from_initials)
    # (contributor_id, target_initials) of every RE_KEY destination —
    # used to suppress redundant ADD_INITIALS actions that would target
    # the same row and trip the unique constraint.
    rekey_destinations: set[tuple[int, str]] = set()

    for a in actions:
        if a.kind != NEEDS_REVIEW:
            upgraded.append(a)
            continue

        # Group X — vol 29 duplicate-initials false positive
        upgrade = _try_upgrade_group_x(a, db, vol29_by_initials)
        if upgrade is not None:
            upgraded.append(upgrade)
            continue

        # Group Y — paired re-key
        result = _try_upgrade_group_y(a, db, vol29_by_name_tokens)
        if result is not None:
            insert_action, rekey_action = result
            upgraded.append(insert_action)
            key = (rekey_action.contributor_id, rekey_action.old_initials)
            if key not in seen_rekeys:
                rekey_actions.append(rekey_action)
                seen_rekeys.add(key)
            rekey_destinations.add(
                (rekey_action.contributor_id, rekey_action.target_initials)
            )
            continue

        upgraded.append(a)

    # Coordination: an existing ADD_INITIALS that would target the same
    # (contributor_id, initials) as a RE_KEY destination would conflict
    # at apply time (unique constraint on initials).  The RE_KEY already
    # leaves the contributor owning the target key, so the ADD_INITIALS
    # is redundant.  Demote it to NO_OP.
    if rekey_destinations:
        for i, a in enumerate(upgraded):
            if a.kind != ADD_INITIALS:
                continue
            if (a.contributor_id, a.target_initials) in rekey_destinations:
                upgraded[i] = Action(
                    NO_OP, a.entry,
                    f"redundant with paired RE_KEY: target {a.target_initials!r} "
                    f"will be set on contributor id={a.contributor_id} via re-key, "
                    "no separate ADD_INITIALS needed",
                )

    return upgraded + rekey_actions


def _try_upgrade_group_x(
    action: Action,
    db: DBSnapshot,
    vol29_by_initials: dict[str, list[Vol29Entry]],
) -> Action | None:
    """Recognise the OCR-duplicate-initials false positive.

    Pattern: vol 29 has multiple entries at this canonical initials
    (asterisk dropped by OCR), the DB has the named contributor under
    SOME initials key already, and the DB's current owner of the
    target key is *also* one of the vol-29 duplicates.  Conclusion:
    DB is correct, vol 29 just can't disambiguate via OCR alone.
    """
    e = action.entry
    target = _normalize_initials(e.initials)
    duplicates = vol29_by_initials.get(target, [])
    if len(duplicates) < 2:
        return None

    init_owner = db.initials_to_contributor.get(target)
    name_matches = find_by_name(db, e)

    # Need both: e's contributor exists in DB (under some initials)
    # and the existing init owner exists too (and they're not the same).
    if init_owner is None or not name_matches:
        return None
    if init_owner.id in {c.id for c in name_matches}:
        return None

    # The DB's init_owner should match one of the OTHER vol-29 entries
    # at this same key (the OCR-equivalent asterisked counterpart).
    init_owner_tokens = name_tokens(init_owner.full_name)
    for other in duplicates:
        if other is e:
            continue
        other_tokens = name_tokens(other.full_name)
        if not (init_owner_tokens & other_tokens):
            continue
        if init_owner_tokens.issubset(other_tokens) or other_tokens.issubset(init_owner_tokens):
            # init_owner corresponds to another vol-29 entry at this same
            # key — confirms vol 29 OCR has duplicate entries for what's
            # really two distinct people, and DB has them right.
            return Action(
                NO_OP, e,
                f"vol 29 has duplicate entries at {target!r} (Vision-OCR "
                f"lost an asterisk); DB already distinguishes "
                f"{e.full_name!r} (id={name_matches[0].id}) from "
                f"{init_owner.full_name!r} (id={init_owner.id}) under "
                f"separate initials",
            )
    return None


def _try_upgrade_group_y(
    action: Action,
    db: DBSnapshot,
    vol29_by_name_tokens: dict[frozenset[str], list[Vol29Entry]],
) -> tuple[Action, Action] | None:
    """Recognise the paired re-key pattern (Babelon/Breck textbook).

    Pattern: vol 29 entry E1 wants initials K, DB currently routes K
    to a different contributor X, AND vol 29 has another entry for X
    assigning them a different initials K' which is currently free
    in DB.  Returns (INSERT for E1 at K, RE_KEY of X from K to K').
    Both actions are auto-applicable.
    """
    e = action.entry
    target = _normalize_initials(e.initials)
    init_owner = db.initials_to_contributor.get(target)
    if init_owner is None:
        return None
    # If the named person already exists in DB, this isn't a clean
    # pair re-key — leave NEEDS_REVIEW.
    if find_by_name(db, e):
        return None

    # Find a vol 29 entry for the init_owner that assigns them
    # different initials.
    init_owner_tokens = name_tokens(init_owner.full_name)
    candidate_v29: Vol29Entry | None = None
    for tokens, v29_entries in vol29_by_name_tokens.items():
        if not (init_owner_tokens & tokens):
            continue
        if not (init_owner_tokens.issubset(tokens) or tokens.issubset(init_owner_tokens)):
            continue
        for v29e in v29_entries:
            v29_target = _normalize_initials(v29e.initials)
            if v29_target == target:
                continue
            # That target must be currently free in DB
            if db.initials_to_contributor.get(v29_target) is not None:
                continue
            candidate_v29 = v29e
            break
        if candidate_v29 is not None:
            break

    if candidate_v29 is None:
        return None

    new_target = _normalize_initials(candidate_v29.initials)
    insert_action = Action(
        INSERT, e,
        f"new contributor (paired with re-key of id={init_owner.id} "
        f"{init_owner.full_name!r} from {target!r} to {new_target!r} "
        f"per vol 29)",
        target_initials=target,
    )
    rekey_action = Action(
        RE_KEY_INITIALS, candidate_v29,
        f"re-key id={init_owner.id} {init_owner.full_name!r} from "
        f"{target!r} to {new_target!r} (vol 29 places them at "
        f"{new_target!r}, freeing {target!r} for {e.full_name!r})",
        contributor_id=init_owner.id,
        old_initials=target,
        target_initials=new_target,
    )
    return insert_action, rekey_action


# --- Apply ------------------------------------------------------------------


def apply_action(session, action: Action) -> None:
    """Mutate the DB to enact one action.  Caller commits.

    RE_KEY_INITIALS refuses to act if the affected contributor already
    has any ArticleContributor rows attributed via the old initials —
    such rows would be stranded (still pointing at the contributor by
    id, but the initials/signature link they came from is gone).  In
    a fresh-rebuild context (linker run between build_contributor_table
    and extract_contributors) this never trips because no
    ArticleContributor rows exist yet.
    """
    e = action.entry
    if action.kind == INSERT:
        c = Contributor(
            full_name=e.full_name,
            credentials=e.credentials or None,
            description=None,
        )
        session.add(c)
        session.flush()
        session.add(ContributorInitials(
            contributor_id=c.id,
            initials=action.target_initials,
        ))
        return

    if action.kind == ADD_INITIALS:
        session.add(ContributorInitials(
            contributor_id=action.contributor_id,
            initials=action.target_initials,
        ))
        return

    if action.kind == RE_KEY_INITIALS:
        # Safety: refuse if any article attributions already exist for
        # this contributor — RE_KEY would leave them dangling under a
        # name/signature mismatch.
        existing_attribs = (
            session.query(ArticleContributor)
            .filter_by(contributor_id=action.contributor_id)
            .count()
        )
        if existing_attribs:
            raise RuntimeError(
                f"RE_KEY_INITIALS refused: contributor id={action.contributor_id} "
                f"has {existing_attribs} existing ArticleContributor rows; "
                f"re-keying would orphan them.  Run linker before "
                f"extract_contributors (fresh-rebuild context)."
            )
        ci = (
            session.query(ContributorInitials)
            .filter_by(
                contributor_id=action.contributor_id,
                initials=action.old_initials,
            )
            .one()
        )
        ci.initials = action.target_initials
        return

    # NO_OP and NEEDS_REVIEW: no DB change.
    return


# --- Reporting --------------------------------------------------------------


def bucket(actions: list[Action]) -> dict[str, list[Action]]:
    """Group actions by kind, preserving order within each bucket."""
    buckets: dict[str, list[Action]] = {}
    for a in actions:
        buckets.setdefault(a.kind, []).append(a)
    return buckets


def format_plan(buckets: dict[str, list[Action]]) -> str:
    """Render the action plan as a markdown-friendly text report."""
    lines: list[str] = ["=== Vol 29 Linker Plan ===\n"]
    counts = {k: len(v) for k, v in buckets.items()}
    lines.append("Action distribution:")
    for k in (INSERT, ADD_INITIALS, RE_KEY_INITIALS, NEEDS_REVIEW, NO_OP):
        if k in counts:
            lines.append(f"  {k:18s}  {counts[k]}")
    lines.append("")

    for kind in (INSERT, ADD_INITIALS, RE_KEY_INITIALS):
        if kind not in buckets:
            continue
        lines.append(f"=== {kind} ({len(buckets[kind])}) ===")
        for a in buckets[kind]:
            lines.append(
                f"  {a.entry.initials!r:18s} {a.entry.full_name!r}"
            )
            lines.append(f"      {a.reason}")
        lines.append("")

    if NEEDS_REVIEW in buckets and buckets[NEEDS_REVIEW]:
        lines.append(f"=== NEEDS_REVIEW ({len(buckets[NEEDS_REVIEW])}) ===")
        lines.append(
            "These will NOT be auto-applied; human review required.\n"
        )
        for a in buckets[NEEDS_REVIEW]:
            lines.append(
                f"  {a.entry.initials!r:18s} {a.entry.full_name!r}  "
                f"(vol29 p.{a.entry.page})"
            )
            lines.append(f"      reason: {a.reason}")
            if a.entry.articles:
                head = ", ".join(a.entry.articles[:3])
                if len(a.entry.articles) > 3:
                    head += f" (+{len(a.entry.articles) - 3} more)"
                lines.append(f"      vol29 articles: {head}")
        lines.append("")

    return "\n".join(lines)
