"""Second-pass LLM cleanup: identify TOC entries that are OCR artifacts
rather than legitimate cross-references.

Targets single-candidate short entries whose target name appears ≥3 times
across the TOC and resolves to a plain generic-form article (e.g. "JOHN"
→ article "JOHN"). These are the ones most likely to be OCR bleed from
"see also" references or generic section fragments, and they slip through
the disambiguator because they have only one candidate article.

Asks Haiku: given (category path, entry name, article title + body
preview), is this a meaningful cross-reference or an OCR artifact?

Drops entries flagged as artifacts from classified_toc.json.
"""
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

CACHE_FILE = Path("data/derived/toc_artifact_cache.json")
TOC_FILE = Path("data/derived/classified_toc.json")
ARTICLES_DIR = Path("data/derived/articles")
MODEL = "claude-haiku-4-5"

SYSTEM_PROMPT = """You decide whether an encyclopedia index (TOC) entry is a legitimate cross-reference or an OCR artifact that should be removed.

Legitimate entry: the reader would follow this link to learn about the topic in the given category. Example — Literature > British > AUSTEN legitimately points to the article about Jane Austen.

OCR artifact: the link makes no sense in the category context. The word was captured from section headers, "see also" phrasing, or running text rather than being a real index entry. Common culprits include generic terms like SEE, GENERAL, NAMES, SUBJECTS, or common first names (JOHN, CHARLES, JAMES) pointing to generic articles about those names.

You will receive:
- A category path
- The index entry name
- The linked article's title and a short body excerpt

Return JSON:
- {"keep": true} if the link is a legitimate cross-reference in this category
- {"keep": false} if the entry is an OCR artifact and should be removed

When in doubt, prefer keep=true."""


def _clean_body(text: str, length: int = 240) -> str:
    text = re.sub(r"\x01PAGE:\d+\x01", "", text)
    text = re.sub(r"\u00ab[^\u00bb]*\u00bb", "", text)
    text = re.sub(r"\{\{IMG:[^}]*\}\}", "", text)
    text = re.sub(r"\{\{TABLE[A-Z]?:.*?\}TABLE\}", "", text, flags=re.DOTALL)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:length]


def _title_from_filename(fn: str) -> str:
    m = re.match(
        r"^\d{2}-\d{4}-[a-z0-9][a-z0-9-]*?-([A-Z0-9_][A-Z0-9_-]*)\.json$",
        fn)
    if not m:
        return ""
    return m.group(1).replace("_", " ").strip()


def find_candidates(toc):
    """Entries matching the artifact-suspicion criteria."""
    target_counts = Counter()
    occurrences = []

    def walk(node, path):
        name = node.get("name", "")
        cur = f"{path} > {name}" if path else name
        for idx, a in enumerate(node.get("articles", [])):
            t = a.get("target", "").strip()
            disp = a.get("display", "").strip()
            fn = a.get("filename", "")
            title = _title_from_filename(fn)
            if (t and disp == t
                    and len(t.split()) <= 2 and len(t) <= 15
                    and title == t):
                target_counts[t] += 1
                occurrences.append({
                    "path": cur,
                    "target": t,
                    "filename": fn,
                    "node": node,
                    "article_idx": idx,
                })
        for ch in node.get("children", []):
            walk(ch, cur)
        for sub in node.get("subsections", []):
            walk(sub, cur)

    for cat in toc["categories"]:
        walk(cat, "")
    hot = {t for t, n in target_counts.items() if n >= 3}
    return [o for o in occurrences if o["target"] in hot]


def load_preview(filename: str) -> str:
    try:
        with open(ARTICLES_DIR / filename, encoding="utf-8") as f:
            a = json.load(f)
        return _clean_body(a.get("body", ""))
    except Exception:
        return ""


def build_request(occ, idx, preview):
    title = _title_from_filename(occ["filename"])
    user_msg = (
        f"Category path: {occ['path']}\n"
        f"Index entry: {occ['target']}\n\n"
        f"Linked article: {title}\n"
        f"Excerpt: {preview}"
    )
    return Request(
        custom_id=f"art-{idx}",
        params=MessageCreateParamsNonStreaming(
            model=MODEL,
            max_tokens=50,
            system=[{
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }],
            output_config={
                "format": {
                    "type": "json_schema",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "keep": {"type": "boolean"},
                        },
                        "required": ["keep"],
                        "additionalProperties": False,
                    }
                }
            },
            messages=[{"role": "user", "content": user_msg}],
        ),
    )


def _cache_key(occ):
    return f"{occ['target']}|{occ['path']}|{occ['filename']}"


def main():
    dry_run = "--dry-run" in sys.argv
    apply = "--apply" in sys.argv

    cache = {}
    if CACHE_FILE.exists():
        cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))

    toc = json.loads(TOC_FILE.read_text(encoding="utf-8"))
    occs = find_candidates(toc)
    print(f"Suspicious entries: {len(occs)}")

    to_resolve = [o for o in occs if _cache_key(o) not in cache]
    print(f"Cached: {len(occs) - len(to_resolve)}")
    print(f"To resolve this run: {len(to_resolve)}")

    if dry_run:
        for o in to_resolve[:15]:
            print(f"  {o['path']}: {o['target']!r} -> {o['filename']}")
        return

    if to_resolve:
        previews = {o["filename"]: load_preview(o["filename"])
                    for o in to_resolve}
        requests = [build_request(o, i, previews[o["filename"]])
                    for i, o in enumerate(to_resolve)]
        client = anthropic.Anthropic()
        print("Submitting batch...")
        batch = client.messages.batches.create(requests=requests)
        print(f"Batch ID: {batch.id}")

        while True:
            batch = client.messages.batches.retrieve(batch.id)
            if batch.processing_status == "ended":
                break
            rc = batch.request_counts
            print(f"  {batch.processing_status} "
                  f"(processing={rc.processing}, succeeded={rc.succeeded}, "
                  f"errored={rc.errored})")
            time.sleep(30)

        for result in client.messages.batches.results(batch.id):
            idx = int(result.custom_id.split("-")[1])
            occ = to_resolve[idx]
            keep = True  # default to keep on any error
            if result.result.type == "succeeded":
                msg = result.result.message
                text = next(
                    (b.text for b in msg.content if b.type == "text"), "{}")
                try:
                    keep = json.loads(text).get("keep", True)
                except Exception:
                    keep = True
            cache[_cache_key(occ)] = keep

        CACHE_FILE.write_text(
            json.dumps(cache, indent=2, ensure_ascii=False),
            encoding="utf-8")
        print(f"Cache written: {CACHE_FILE}")

    # Collect proposed removals from the cache.
    proposed = [o for o in occs if cache.get(_cache_key(o)) is False]
    print(f"\nProposed removals: {len(proposed)}")
    for o in proposed:
        print(f"  {o['path']}: {o['target']!r} -> {o['filename']}")

    if not apply:
        print("\nReview the list above. Re-run with --apply to remove them "
              "from classified_toc.json.")
        return

    # Apply removals.
    to_remove = {(id(o["node"]), o["article_idx"]) for o in proposed}
    removed = 0

    def prune(node):
        nonlocal removed
        if "articles" in node:
            kept = []
            for i, a in enumerate(node["articles"]):
                if (id(node), i) in to_remove:
                    removed += 1
                    continue
                kept.append(a)
            node["articles"] = kept
        for ch in node.get("children", []):
            prune(ch)
        for sub in node.get("subsections", []):
            prune(sub)

    for cat in toc["categories"]:
        prune(cat)

    TOC_FILE.write_text(
        json.dumps(toc, indent=2, ensure_ascii=False),
        encoding="utf-8")
    print(f"\nRemoved {removed} artifact entries from {TOC_FILE}")


if __name__ == "__main__":
    main()
