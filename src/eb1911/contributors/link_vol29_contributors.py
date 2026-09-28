"""Run the vol 29 linker against the current DB state.

Usage:
  uv run python -m eb1911.contributors.link_vol29_contributors            # dry-run
  uv run python -m eb1911.contributors.link_vol29_contributors --apply    # mutate DB

Dry-run prints the classified action plan without touching the DB.
`--apply` commits INSERT and ADD_INITIALS actions; NEEDS_REVIEW items
are still printed but never auto-applied.

Run by `resolve_contributors_post.bind_contributors` (roster step 0), after
`build_contributor_table` and before the bios backfill.  Running on a stale
(post-bind) DB is supported but the
NEEDS_REVIEW caveats apply more strongly — reviewer should confirm
no `ArticleContributor` rows would be orphaned by an INSERT/ADD.
"""
from __future__ import annotations

import sys


from eb1911.contributors.vol29_index import parse_vol29_index
from eb1911.contributors.vol29_linker import (
    INSERT, ADD_INITIALS, RE_KEY_INITIALS, NEEDS_REVIEW,
    apply_action, bucket, build_plan, format_plan, snapshot_db,
)
from wikikit.db.session import SessionLocal


def main() -> int:
    apply_mode = "--apply" in sys.argv

    session = SessionLocal()
    try:
        entries = parse_vol29_index()
        db = snapshot_db(session)
        actions = build_plan(entries, db)
        buckets = bucket(actions)

        report = format_plan(buckets)
        sys.stdout.reconfigure(encoding="utf-8")
        print(report)

        if not apply_mode:
            print("(dry-run; pass --apply to mutate)")
            return 0

        # Auto-apply order: RE_KEY first (frees up an initials key for
        # a subsequent INSERT in a paired Group-Y resolution), then
        # ADD_INITIALS, then INSERT.
        applied = {INSERT: 0, ADD_INITIALS: 0, RE_KEY_INITIALS: 0}
        for kind in (RE_KEY_INITIALS, ADD_INITIALS, INSERT):
            for a in buckets.get(kind, []):
                apply_action(session, a)
                applied[kind] += 1
        session.commit()

        print(f"Applied: "
              f"{applied[RE_KEY_INITIALS]} RE_KEY, "
              f"{applied[ADD_INITIALS]} ADD_INITIALS, "
              f"{applied[INSERT]} INSERT.")
        skipped = len(buckets.get(NEEDS_REVIEW, []))
        if skipped:
            print(f"Skipped (NEEDS_REVIEW): {skipped} — see above for details.")
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
