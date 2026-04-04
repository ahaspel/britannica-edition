#!/usr/bin/env python3
"""Index all articles into Meilisearch for full-text search."""

import json
import glob
import os
import re
import sys
import requests

MEILI_URL = os.environ.get("MEILI_URL", "http://localhost:7700")
MEILI_KEY = os.environ.get("MEILI_MASTER_KEY", "britannica-dev-key")
INDEX_NAME = "articles"

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {MEILI_KEY}",
}


def main():
    # Delete existing index
    requests.delete(f"{MEILI_URL}/indexes/{INDEX_NAME}", headers=HEADERS)

    # Create index
    requests.post(
        f"{MEILI_URL}/indexes",
        headers=HEADERS,
        json={"uid": INDEX_NAME, "primaryKey": "id"},
    )

    # Configure searchable and displayed attributes
    requests.patch(
        f"{MEILI_URL}/indexes/{INDEX_NAME}/settings",
        headers=HEADERS,
        json={
            "searchableAttributes": ["title", "body", "contributors"],
            "displayedAttributes": [
                "id", "title", "article_type", "volume", "page_start",
                "page_end", "body_start", "filename", "contributors",
            ],
            "sortableAttributes": ["title", "volume", "page_start"],
        },
    )

    # Load and index articles in batches
    files = sorted(
        f for f in glob.glob("data/derived/articles/*.json")
        if "index.json" not in f and "contributors.json" not in f and "search" not in f
    )

    batch = []
    total = 0

    for f in files:
        with open(f, encoding="utf-8") as fh:
            article = json.load(fh)

        # Skip non-article files (front_matter.json, etc.)
        if "id" not in article or "volume" not in article:
            continue

        # Build search document — strip internal markers before indexing
        body = article.get("body", "")
        body = re.sub(r"\x01PAGE:\d+\x01", " ", body)
        body = re.sub(r"\u00abFN:.*?\u00ab/FN\u00bb", " ", body, flags=re.DOTALL)
        body = re.sub(r"\u00abLN:[^«]*\u00ab/LN\u00bb", " ", body)
        body = re.sub(r"\u00abMATH:.*?\u00ab/MATH\u00bb", " ", body, flags=re.DOTALL)
        body = re.sub(r"\u00ab/?(?:B|I|SC|SH)\u00bb", " ", body)
        body = re.sub(r"  +", " ", body)
        words = body.split()
        body_start = " ".join(words[:10]) + "\u2026" if len(words) > 10 else " ".join(words)

        doc = {
            "id": article["id"],
            "title": article["title"],
            "article_type": article.get("article_type", "article"),
            "volume": article["volume"],
            "page_start": article["page_start"],
            "page_end": article["page_end"],
            "body": body,
            "body_start": body_start,
            "filename": f.split("/")[-1].split("\\")[-1],
            "contributors": ", ".join(
                c["full_name"] for c in article.get("contributors", [])
            ),
        }

        batch.append(doc)

        if len(batch) >= 500:
            resp = requests.post(
                f"{MEILI_URL}/indexes/{INDEX_NAME}/documents",
                headers=HEADERS,
                json=batch,
            )
            total += len(batch)
            print(f"Indexed {total} articles...")
            batch = []

    if batch:
        requests.post(
            f"{MEILI_URL}/indexes/{INDEX_NAME}/documents",
            headers=HEADERS,
            json=batch,
        )
        total += len(batch)

    print(f"Done. Indexed {total} articles.")


if __name__ == "__main__":
    main()
