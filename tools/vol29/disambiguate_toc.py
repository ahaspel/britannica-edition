"""Disambiguate ambiguous TOC entries using Claude Haiku classification.

For each TOC entry whose name matches multiple article titles (e.g. "ABEL"
matches ABEL the biblical figure, ABEL, SIR FREDERICK AUGUSTUS the chemist,
ABEL, KARL FRIEDRICH the musician, etc.), pick the right article based on
the TOC's category context.

Uses the Anthropic Messages Batch API with prompt caching so the system
prompt is only billed once. Results are cached by (entry, category path,
candidate filenames) so stable-ID rebuilds don't re-pay the LLM cost.

Cost estimate: ~$1-3 total for ~2000 ambiguities (Haiku 4.5 + batch 50%
discount + prompt caching on the shared system prompt).

Usage:  uv run python tools/vol29/disambiguate_toc.py
Dry-run: --dry-run to report ambiguities without calling the API
"""
import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

CACHE_FILE = Path("data/derived/toc_disambiguation_cache.json")
TOC_FILE = Path("data/derived/classified_toc.json")
ARTICLES_DIR = Path("data/derived/articles")
INDEX_FILE = ARTICLES_DIR / "index.json"
MODEL = "claude-haiku-4-5"

SYSTEM_PROMPT = """You disambiguate encyclopedia index entries.

You will receive:
- A category path from the encyclopedia's classified index (e.g. "Chemistry > Biographies")
- An index entry name (usually a surname, e.g. "ABEL")
- A list of candidate articles from the encyclopedia, each with a title and short body excerpt

Choose the candidate that best matches the entry given the category context.

Examples:
- "Chemistry > Biographies > ABEL" → Sir Frederick Augustus Abel (British chemist, explosives)
- "Art > Music > Biographies > ABEL" → Karl Friedrich Abel (composer)
- "Mathematics > Biographies > ABEL" → Niels Henrik Abel (mathematician)
- "Religion > ... > Saints > ABEL" → the biblical Abel

Return JSON: {"filename": "<filename>"} where filename is chosen from the
candidate list verbatim. If no candidate fits the category context, return
{"filename": null}."""


def _norm(s: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "", s.upper())


def _clean_body(text: str, length: int = 240) -> str:
    text = re.sub(r"\x01PAGE:\d+\x01", "", text)
    text = re.sub(r"\u00ab[^\u00bb]*\u00bb", "", text)
    text = re.sub(r"\{\{IMG:[^}]*\}\}", "", text)
    text = re.sub(r"\{\{TABLE[A-Z]?:.*?\}TABLE\}", "", text, flags=re.DOTALL)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:length]


def _load_previews(filenames: set[str]) -> dict[str, str]:
    """Load a short body preview for each article filename (lazily)."""
    previews = {}
    for fn in filenames:
        try:
            with open(ARTICLES_DIR / fn, encoding="utf-8") as f:
                a = json.load(f)
            previews[fn] = _clean_body(a.get("body", ""))
        except Exception:
            previews[fn] = ""
    return previews


def _cache_key(target: str, path: str, filenames: list[str]) -> str:
    return f"{target}|{path}|{','.join(sorted(filenames))}"


def collect_ambiguities(toc: dict, title_candidates: dict) -> list[dict]:
    """Walk the TOC tree, return entries with multiple candidate articles."""
    results = []

    def walk(node, path):
        name = node.get("name", "")
        cur = f"{path} > {name}" if path else name
        for i, a in enumerate(node.get("articles", [])):
            target = a.get("target", "")
            norm = _norm(target)
            cands = title_candidates.get(norm, [])
            if len(cands) > 1:
                results.append({
                    "path": cur,
                    "target": target,
                    "candidates": cands,
                    "node": node,
                    "article_idx": i,
                })
        for ch in node.get("children", []):
            walk(ch, cur)
        for sub in node.get("subsections", []):
            walk(sub, cur)

    for cat in toc["categories"]:
        walk(cat, "")
    return results


def build_title_index() -> dict:
    """Map normalized title → list of {filename, title} candidates.

    Registers each article under multiple keys so a TOC entry matches
    all plausible variants:
      - full title as-is
      - title with (…) / […] qualifier stripped (PAMPHILUS (PAINTER)
        also registers under PAMPHILUS)
      - surname only for "SURNAME, FIRSTNAME" forms
    """
    article_idx = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    title_candidates = defaultdict(list)
    for e in article_idx:
        if e.get("article_type") != "article":
            continue
        title = e["title"]
        entry = {"filename": e["filename"], "title": title}
        keys = {_norm(title)}
        stripped = re.sub(r"\s*[\(\[][^\)\]]*[\)\]]", "", title).strip()
        if stripped and stripped != title:
            keys.add(_norm(stripped))
        if "," in stripped or "," in title:
            base = stripped if "," in stripped else title
            surname = base.split(",", 1)[0].strip()
            keys.add(_norm(surname))
        for k in keys:
            if k and not any(c["filename"] == entry["filename"]
                             for c in title_candidates[k]):
                title_candidates[k].append(entry)
    return title_candidates


def build_request(amb: dict, idx: int, previews: dict) -> Request:
    lines = []
    for c in amb["candidates"]:
        prev = previews.get(c["filename"], "")
        lines.append(f"- {c['filename']}\n  title: {c['title']}\n  excerpt: {prev}")
    candidates_text = "\n".join(lines)
    user_msg = (
        f"Category path: {amb['path']}\n"
        f"Index entry: {amb['target']}\n\n"
        f"Candidates:\n{candidates_text}"
    )
    return Request(
        custom_id=f"toc-{idx}",
        params=MessageCreateParamsNonStreaming(
            model=MODEL,
            max_tokens=100,
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
                            "filename": {"type": ["string", "null"]},
                        },
                        "required": ["filename"],
                        "additionalProperties": False,
                    }
                }
            },
            messages=[{"role": "user", "content": user_msg}],
        ),
    )


def main():
    dry_run = "--dry-run" in sys.argv

    print("Loading cache and TOC...")
    cache = {}
    if CACHE_FILE.exists():
        cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))

    toc = json.loads(TOC_FILE.read_text(encoding="utf-8"))
    title_candidates = build_title_index()

    ambiguities = collect_ambiguities(toc, title_candidates)
    print(f"Ambiguous TOC entries: {len(ambiguities)}")

    needed_filenames = {
        c["filename"]
        for amb in ambiguities
        for c in amb["candidates"]
    }
    print(f"Unique candidate articles to preview: {len(needed_filenames)}")

    to_resolve = []
    for amb in ambiguities:
        key = _cache_key(
            amb["target"], amb["path"],
            [c["filename"] for c in amb["candidates"]],
        )
        if key not in cache:
            to_resolve.append((amb, key))

    print(f"Already cached: {len(ambiguities) - len(to_resolve)}")
    print(f"To resolve this run: {len(to_resolve)}")

    if dry_run or not to_resolve:
        if dry_run:
            print("[dry-run — not calling API]")
        return

    print("Loading body previews...")
    previews = _load_previews(needed_filenames)

    print(f"Building {len(to_resolve)} batch requests...")
    requests = [
        build_request(amb, i, previews)
        for i, (amb, _key) in enumerate(to_resolve)
    ]

    client = anthropic.Anthropic()
    print("Submitting batch...")
    batch = client.messages.batches.create(requests=requests)
    print(f"Batch ID: {batch.id}")
    print(f"Status: {batch.processing_status}")

    while True:
        batch = client.messages.batches.retrieve(batch.id)
        if batch.processing_status == "ended":
            break
        rc = batch.request_counts
        print(f"  {batch.processing_status} "
              f"(processing={rc.processing}, succeeded={rc.succeeded}, "
              f"errored={rc.errored})")
        time.sleep(30)

    print(f"Batch complete. Succeeded: {batch.request_counts.succeeded}, "
          f"Errored: {batch.request_counts.errored}")

    for result in client.messages.batches.results(batch.id):
        idx = int(result.custom_id.split("-")[1])
        amb, key = to_resolve[idx]
        filename = None
        if result.result.type == "succeeded":
            msg = result.result.message
            text = next(
                (b.text for b in msg.content if b.type == "text"), "{}")
            try:
                parsed = json.loads(text)
                filename = parsed.get("filename")
                valid = {c["filename"] for c in amb["candidates"]}
                if filename not in valid:
                    filename = None
            except Exception:
                filename = None
        cache[key] = filename

    CACHE_FILE.write_text(
        json.dumps(cache, indent=2, ensure_ascii=False),
        encoding="utf-8")
    print(f"Cache written: {CACHE_FILE}")

    print("Applying to classified_toc.json...")
    updated = 0
    for amb in ambiguities:
        key = _cache_key(
            amb["target"], amb["path"],
            [c["filename"] for c in amb["candidates"]],
        )
        chosen = cache.get(key)
        if not chosen:
            continue
        node = amb["node"]
        entry = node["articles"][amb["article_idx"]]
        if entry.get("filename") == chosen:
            continue
        chosen_title = next(
            (c["title"] for c in amb["candidates"]
             if c["filename"] == chosen),
            None,
        )
        if chosen_title:
            entry["filename"] = chosen
            entry["display"] = chosen_title
            updated += 1

    TOC_FILE.write_text(
        json.dumps(toc, indent=2, ensure_ascii=False),
        encoding="utf-8")
    print(f"Updated {updated} TOC entries in {TOC_FILE}")


if __name__ == "__main__":
    main()
