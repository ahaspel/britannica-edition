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


def _send_batch(batch, total_so_far):
    """Send a batch with retries."""
    import time
    for attempt in range(5):
        try:
            resp = requests.post(
                f"{MEILI_URL}/indexes/{INDEX_NAME}/documents",
                headers=HEADERS,
                json=batch,
                timeout=60,
            )
            resp.raise_for_status()
            print(f"Indexed {total_so_far + len(batch)} articles...")
            return
        except (requests.RequestException, ConnectionError) as e:
            wait = 5 * (attempt + 1)
            print(f"  Retry {attempt + 1}/5 after error: {e} (waiting {wait}s)")
            time.sleep(wait)
    print(f"  FAILED batch at {total_so_far}, continuing...")


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
                "page_end", "body", "body_start", "body_length", "filename",
                "contributors",
            ],
            "filterableAttributes": [
                "volume", "article_type", "body_length", "page_start", "page_end",
                "contributors",
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
        body = re.sub(r"\u00abFN(?:\[[^\]]+\])?:.*?\u00ab/FN\u00bb", " ", body,
                      flags=re.DOTALL)
        body = re.sub(r"\u00abLN:[^«]*\u00ab/LN\u00bb", " ", body)
        body = re.sub(r"\u00abMATH:.*?\u00ab/MATH\u00bb", " ", body, flags=re.DOTALL)
        # Strip image/table/verse markers — these aren't searchable text
        # and they leak into body_start previews as raw markup.
        body = re.sub(r"\{\{IMG:[^}]*\}\}", " ", body)
        body = re.sub(r"\{\{TABLE[A-Z]?:[\s\S]*?\}TABLE\}", " ", body)
        body = re.sub(r"\{\{VERSE:[\s\S]*?\}VERSE\}", " ", body)
        body = re.sub(
            r"\u00abHTMLTABLE:[\s\S]*?\u00ab/HTMLTABLE\u00bb", " ", body)
        body = re.sub(r"\u00abB\u00bb(.*?)\u00ab/B\u00bb", r"\1", body)
        body = re.sub(r"\u00abI\u00bb(.*?)\u00ab/I\u00bb", r"\1", body)
        body = re.sub(r"\u00abSC\u00bb(.*?)\u00ab/SC\u00bb", r"\1", body)
        body = re.sub(r"\u00abSH\u00bb(.*?)\u00ab/SH\u00bb", r"\1", body)
        body = re.sub(r"\u00abLN:[^|]*\|([^«]*)\u00ab/LN\u00bb", r"\1", body)
        body = re.sub(r"\u00ab/?[A-Z]+\u00bb", "", body)
        body = re.sub(r"  +", " ", body)
        words = body.split()
        body_start = " ".join(words[:10]) + "\u2026" if len(words) > 10 else " ".join(words)

        doc = {
            # Meilisearch doc ID uses the stable_id so search-result URLs
            # don't rot on rebuild. Falls back to numeric id for articles
            # exported before stable_ids landed.
            "id": article.get("stable_id") or str(article["id"]),
            "numeric_id": article["id"],
            "stable_id": article.get("stable_id"),
            "title": article["title"],
            "article_type": article.get("article_type", "article"),
            "volume": article["volume"],
            "page_start": article["page_start"],
            "page_end": article["page_end"],
            "body": body,
            "body_start": body_start,
            "body_length": len(words),
            "filename": f.split("/")[-1].split("\\")[-1],
            "contributors": ", ".join(
                c["full_name"] for c in article.get("contributors", [])
            ),
        }

        batch.append(doc)

        if len(batch) >= 5000:
            _send_batch(batch, total)
            total += len(batch)
            batch = []

    if batch:
        _send_batch(batch, total)
        total += len(batch)

    print(f"Done. Indexed {total} articles.")


if __name__ == "__main__":
    main()
