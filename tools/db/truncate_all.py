"""Truncate all tables in the database. Used by rebuild_all.sh.

`--keep-source-pages` spares `source_pages` — the immutable raw wikileaf layer
imported by `import_wikisource_pages.py`.  rebuild_all.sh's `--skip-import` uses
it: the raw never changes, so re-importing it is ~30 min wasted.  Keep the pages
and re-derive everything else (segments, articles, contributors) from them via
detect-boundaries + extract-contributors.  FK-safe: the derived tables are the
CHILDREN (`article_segments.source_page_id → source_pages`), so truncating them
while keeping `source_pages` leaves no dangling reference, and detect-boundaries
re-creates the children against the kept pages."""
import argparse
import sys
sys.path.insert(0, "src")
from britannica.db.session import SessionLocal
from sqlalchemy import text

ap = argparse.ArgumentParser()
ap.add_argument(
    "--keep-source-pages", action="store_true",
    help="spare source_pages (the imported raw layer); truncate only derived tables")
args = ap.parse_args()

# Derived tables (regenerated every rebuild) first; `source_pages` (the immutable
# imported raw) LAST so --keep-source-pages can drop it from the list.
tables = [
    "article_contributors",
    "cross_references",
    "article_segments",
    "articles",
    "contributor_initials",
    "contributors",
    "source_pages",
]
if args.keep_source_pages:
    tables = [t for t in tables if t != "source_pages"]

session = SessionLocal()
for table in tables:
    session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
session.commit()
session.close()
print(f"Truncated {len(tables)} tables"
      + (" (kept source_pages)." if args.keep_source_pages else "."))
