#!/usr/bin/env python3
"""Index articles from S3 into local Meilisearch. Run on EC2.

Reads article JSONs from S3, strips markers, and POSTs to localhost:7700.
Uses only stdlib (no pip dependencies).

Usage:
    python3 index_search_ec2.py
"""
import json
import os
import glob
import sys
import urllib.request

# markers.py is pure-stdlib and is shipped to ~ next to this script by the
# rebuild deploy step, so search indexing uses the SAME marker->text converter
# as the export (britannica.markers) -- no separate EC2 copy of the strip logic.
# Locally (running from the repo) there is no shipped copy, so fall back to the
# real module on `src`.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from markers import markers_to_text
except ModuleNotFoundError:
    sys.path.insert(0, os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
    from britannica.markers import markers_to_text

# Env-overridable so ONE indexer serves both EC2 (defaults) and a local reindex:
#   MEILI_MASTER_KEY=britannica-dev-key ARTICLES_DIR=data/derived/articles \
#     uv run python tools/pipeline/index_search_ec2.py
MEILI_URL = os.environ.get("MEILI_URL", "http://localhost:7700")
MEILI_KEY = os.environ.get("MEILI_MASTER_KEY", "gibbon-winters-lewis")
INDEX_NAME = "articles"
ARTICLES_DIR = os.environ.get("ARTICLES_DIR", os.path.expanduser("~/articles"))
BATCH_SIZE = 500

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {MEILI_KEY}",
}


def meili_request(method, path, data=None):
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(
        f"{MEILI_URL}{path}",
        data=body,
        headers=HEADERS,
        method=method,
    )
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def list_article_files():
    """List all article .json files in the local articles directory."""
    files = sorted(glob.glob(os.path.join(ARTICLES_DIR, "*.json")))
    return [f for f in files
            if "index.json" not in f
            and "contributors.json" not in f
            and "front_matter" not in f
            and "volumes.json" not in f]


def main():
    # Delete and recreate index
    print("Recreating index...")
    meili_request("DELETE", f"/indexes/{INDEX_NAME}")
    meili_request("POST", "/indexes",
                  {"uid": INDEX_NAME, "primaryKey": "id"})
    meili_request("PATCH", f"/indexes/{INDEX_NAME}/settings", {
        "searchableAttributes": ["title", "body", "contributors"],
        "displayedAttributes": [
            "id", "title", "article_type", "volume", "page_start",
            "page_end", "body", "body_start", "body_length", "filename",
            "contributors",
        ],
        "filterableAttributes": [
            "volume", "article_type", "body_length", "page_start",
            "page_end", "contributors",
        ],
        "sortableAttributes": ["title", "volume", "page_start"],
    })

    # List all article files
    print("Listing article files...")
    files = list_article_files()
    print(f"Found {len(files)} article files")

    batch = []
    total = 0

    for i, filepath in enumerate(files):
        try:
            with open(filepath, encoding="utf-8") as fh:
                article = json.load(fh)
        except Exception as e:
            print(f"  Skip {filepath}: {e}", file=sys.stderr)
            continue

        if "id" not in article or "volume" not in article:
            continue

        # ONE marker->text converter (britannica.markers.markers_to_text,
        # shipped here as markers.py): strips the TITLE head (indexed directly
        # as the `title` field), drops non-prose block markers, keeps inline
        # prose, and collapses links to their display text.
        body = " ".join(markers_to_text(article.get("body", "")).split())
        words = body.split()
        body_start = (" ".join(words[:10]) + "\u2026"
                       if len(words) > 10 else " ".join(words))

        doc = {
            "id": article["id"],
            "title": article["title"],
            "article_type": article.get("article_type", "article"),
            "volume": article["volume"],
            "page_start": article["page_start"],
            "page_end": article["page_end"],
            "body": body,
            "body_start": body_start,
            "body_length": len(words),
            "filename": os.path.basename(filepath),
            "contributors": ", ".join(
                c["full_name"] for c in article.get("contributors", [])
            ),
        }
        batch.append(doc)

        if len(batch) >= BATCH_SIZE:
            status, _ = meili_request(
                "POST", f"/indexes/{INDEX_NAME}/documents", batch)
            total += len(batch)
            print(f"Indexed {total} articles... (HTTP {status})")
            sys.stdout.flush()
            batch = []

    if batch:
        meili_request("POST", f"/indexes/{INDEX_NAME}/documents", batch)
        total += len(batch)

    print(f"Done. Indexed {total} articles.")


if __name__ == "__main__":
    main()
