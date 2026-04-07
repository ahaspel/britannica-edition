"""Truncate all tables in the database. Used by rebuild_all.sh."""
import sys
sys.path.insert(0, "src")
from britannica.db.session import SessionLocal
from sqlalchemy import text

session = SessionLocal()
for table in [
    "article_contributors",
    "article_images",
    "cross_references",
    "article_segments",
    "articles",
    "contributor_initials",
    "contributors",
    "source_pages",
]:
    session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
session.commit()
session.close()
print("All tables truncated.")
