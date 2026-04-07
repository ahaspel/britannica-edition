"""Verify database is empty. Exits with code 1 if not."""
import sys
sys.path.insert(0, "src")
from britannica.db.session import SessionLocal
from britannica.db.models import Article

session = SessionLocal()
count = session.query(Article).count()
session.close()

if count != 0:
    print(f"ERROR: Database not empty ({count} articles). Aborting.")
    sys.exit(1)
print("Verified: database empty.")
