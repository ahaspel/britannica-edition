#!/usr/bin/env python3
"""Index articles from S3 into local Meilisearch. Run on EC2.

Reads article JSONs from S3, strips markers, and POSTs to localhost:7700.
Uses only stdlib (no pip dependencies).

Usage:
    python3 index_search_ec2.py
"""
import json
import os
import re
import glob
import sys
import urllib.request

MEILI_URL = "http://localhost:7700"
MEILI_KEY = os.environ.get("MEILI_MASTER_KEY", "gibbon-winters-lewis")
INDEX_NAME = "articles"
ARTICLES_DIR = os.path.expanduser("~/articles")
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
            "page_end", "body_start", "body_length", "filename",
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

        body = article.get("body", "")
        body = re.sub(r"\x01PAGE:\d+\x01", " ", body)
        body = re.sub(r"\u00abFN:.*?\u00ab/FN\u00bb", " ", body,
                       flags=re.DOTALL)
        body = re.sub(r"\u00abLN:[^«]*\u00ab/LN\u00bb", " ", body)
        body = re.sub(r"\u00abMATH:.*?\u00ab/MATH\u00bb", " ", body,
                       flags=re.DOTALL)
        body = re.sub(r"\u00abB\u00bb(.*?)\u00ab/B\u00bb", r"\1", body)
        body = re.sub(r"\u00abI\u00bb(.*?)\u00ab/I\u00bb", r"\1", body)
        body = re.sub(r"\u00abSC\u00bb(.*?)\u00ab/SC\u00bb", r"\1", body)
        body = re.sub(r"\u00abSH\u00bb(.*?)\u00ab/SH\u00bb", r"\1", body)
        body = re.sub(r"\u00abLN:[^|]*\|([^«]*)\u00ab/LN\u00bb", r"\1",
                       body)
        body = re.sub(r"\u00ab/?[A-Z]+\u00bb", "", body)
        body = re.sub(r"  +", " ", body)
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
