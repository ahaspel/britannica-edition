#!/usr/bin/env python3
"""Post-processing safety-net over exported article JSON files.

The body cleanup itself now lives in ``britannica.export.body_cleanup``
and runs inside ``export_articles_to_json``, so this script is a no-op
on freshly-exported article JSONs.  It's retained as a standalone way
to re-apply ``clean_body`` to any JSON files that weren't produced by
the article exporter (e.g. front-matter JSON, or hand-edited files).

``clean_body`` is idempotent, so running this after a full export is
harmless.
"""
import json
import glob
import sys

sys.path.insert(0, "src")
from britannica.export.body_cleanup import clean_body  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")


def main():
    files = sorted(
        f for f in glob.glob("data/derived/articles/*.json")
        if "index.json" not in f and "contributors.json" not in f
    )

    fixed = 0
    for f in files:
        with open(f, encoding="utf-8") as fh:
            article = json.load(fh)

        body = article.get("body", "")
        if not body:
            continue

        cleaned = clean_body(body)
        if cleaned != body:
            article["body"] = cleaned
            with open(f, "w", encoding="utf-8") as fh:
                json.dump(article, fh, indent=2, ensure_ascii=False)
            fixed += 1

    print(f"Post-processed {len(files)} files, fixed {fixed}.")


if __name__ == "__main__":
    main()
