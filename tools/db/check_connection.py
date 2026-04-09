"""Check database connection. Exits with code 1 if unreachable."""
import sys
sys.path.insert(0, "src")
from sqlalchemy import text
from britannica.db.session import SessionLocal

try:
    session = SessionLocal()
    session.execute(text("SELECT 1"))
    session.close()
    print("Database connection OK.")
except Exception as e:
    print(f"ERROR: Cannot connect to database: {e}")
    sys.exit(1)
