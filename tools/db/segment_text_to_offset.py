"""Schema move: `article_segments.segment_text` -> `article_segments.offset`.

The table stops holding the article's text cut into per-page pieces and starts
holding page KEYS — where each source page BEGINS inside `Article.body`.  The
body itself is one slice of the clean volume stream, stored whole and never
edited ([[project_page_position_out_of_band]]).

There is no Alembic in this project (schema is `Base.metadata.create_all`), so a
live schema change is an explicit ALTER — same pattern as
`tools/_scratch/alter_title_columns.py`.

Existing rows keep their (article, page, sequence) relation, which is still
correct, and get `offset = 0`, which is NOT — the real offsets only exist once
detection re-runs.  Every article body in the database is likewise stale: it
holds the old space-or-newline reassembly, not the slice.  So this migration
must be followed by a rebuild; it makes the schema right, not the data.

    uv run python tools/db/segment_text_to_offset.py [--check]
"""
from __future__ import annotations

import sys

from sqlalchemy import inspect, text

from britannica.db.session import engine


def columns() -> set[str]:
    return {c["name"] for c in inspect(engine).get_columns("article_segments")}


def main() -> int:
    check_only = "--check" in sys.argv
    cols = columns()
    print(f"article_segments columns now: {sorted(cols)}")

    todo: list[str] = []
    if "offset" not in cols:
        # `offset` is a reserved word in SQL — always quoted.
        todo.append('ALTER TABLE article_segments ADD COLUMN "offset" INTEGER '
                    'NOT NULL DEFAULT 0')
    if "segment_text" in cols:
        todo.append("ALTER TABLE article_segments DROP COLUMN segment_text")

    if not todo:
        print("nothing to do — schema already migrated")
        return 0
    print("\nstatements:")
    for stmt in todo:
        print(f"   {stmt}")
    if check_only:
        print("\n--check given; nothing executed")
        return 0

    with engine.begin() as conn:
        for stmt in todo:
            conn.execute(text(stmt))
    after = columns()
    print(f"\narticle_segments columns after: {sorted(after)}")
    ok = "offset" in after and "segment_text" not in after
    print("OK" if ok else "MIGRATION DID NOT TAKE")
    if ok:
        print("\nNOTE: every existing row now has offset=0, and every Article.body "
              "still holds the OLD reassembly.  Re-run detection/rebuild before "
              "trusting any of it.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
