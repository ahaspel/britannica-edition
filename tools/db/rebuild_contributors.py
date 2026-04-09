"""Rebuild just the contributor tables without touching articles.

Truncates contributors and contributor_initials, rebuilds from front
matter, re-links article footers, and re-exports all volumes.

Usage: uv run python tools/db/rebuild_contributors.py
"""
import sys
sys.path.insert(0, "src")

from sqlalchemy import text
from britannica.db.session import SessionLocal


def main():
    # Step 1: Truncate only contributor tables
    print("Truncating contributor tables...")
    session = SessionLocal()
    session.execute(text("TRUNCATE TABLE article_contributors CASCADE"))
    session.execute(text("TRUNCATE TABLE contributor_initials CASCADE"))
    session.execute(text("TRUNCATE TABLE contributors CASCADE"))
    session.commit()
    session.close()
    print("Done.")

    # Step 2: Build contributor table from front matter
    print("\nBuilding contributor table from front matter...")
    import subprocess
    subprocess.run(
        ["uv", "run", "python", "tools/build_contributor_table.py"],
        check=True,
    )

    # Step 3: Re-link article footers
    print("\nRe-linking article footers...")
    import subprocess
    for vol in range(1, 29):
        result = subprocess.run(
            ["uv", "run", "britannica", "extract-contributors", str(vol)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        lines = result.stdout.strip().splitlines()
        if lines:
            print(f"  Vol {vol}: {lines[-1]}")

    # Step 4: Re-export all volumes (to update contributor data in article JSONs)
    print("\nRe-exporting all volumes...")
    for vol in range(1, 29):
        result = subprocess.run(
            ["uv", "run", "britannica", "export-articles", str(vol)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        lines = result.stdout.strip().splitlines()
        if lines:
            print(f"  Vol {vol}: {lines[-1]}")

    print("\nDone.")


if __name__ == "__main__":
    main()
