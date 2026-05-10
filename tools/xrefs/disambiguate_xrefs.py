"""Disambiguate ambiguous cross-references using Claude Haiku.

For each xref whose normalized target is an ``ambiguous title`` —
defined as a title that exists as a standalone article AND has 3+
``TITLE, FirstName`` person-variant articles (Adam Smith, George
Smith, …) — pick the right article based on the surrounding page
context.

Static-source assumption: once a (source_stable_id, surface_text,
normalized_target) combination has been disambiguated, the answer
holds across rebuilds.  Cache by that key in
``data/derived/xref_disambiguation_cache.json``; subsequent rebuilds
read the cache, no LLM call needed.

Mirrors the ``tools/vol29/disambiguate_toc.py`` pattern: Anthropic
Messages Batch API + prompt caching on the system prompt + JSON
schema output.

Cache key: ``{source_stable_id}::{surface_text}::{normalized_target}``
all three components are stable across rebuilds.

Usage:
  uv run python tools/xrefs/disambiguate_xrefs.py
  uv run python tools/xrefs/disambiguate_xrefs.py --dry-run
  uv run python tools/xrefs/disambiguate_xrefs.py --apply-only
"""
from __future__ import annotations

import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

import anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

sys.stdout.reconfigure(encoding="utf-8")

from britannica.db.models import Article, CrossReference  # noqa: E402
from britannica.db.session import SessionLocal  # noqa: E402
from britannica.export.article_json import stable_id  # noqa: E402
from britannica.xrefs.normalizer import normalize_xref_target  # noqa: E402


CACHE_FILE = Path("data/derived/xref_disambiguation_cache.json")
MODEL = "claude-haiku-4-5"
PERSON_VARIANT_THRESHOLD = 3
CONTEXT_CHARS_BEFORE = 600
CONTEXT_CHARS_AFTER = 600


SYSTEM_PROMPT = """You disambiguate Encyclopaedia Britannica (1911) cross-references.

A bare-surname reference like "see Smith" or "compare Hamilton" might
point to the generic surname article OR to one of several specific
people (Adam Smith, William Hamilton, …).  Geographic / topical names
("Holland", "Ireland") are usually the country/place, not a person.

You will receive:
- A short excerpt from the source article around the reference
- The reference's surface text (the literal phrase containing it)
- A list of candidate articles, each with a stable_id, title, and
  short body excerpt

Choose the candidate that best matches the reference given the
context.  When in doubt about a geographic or topical bare name,
prefer the standalone article (likely the country/concept).  When the
context is clearly biographical (mentions a profession, era, or
existing first name), prefer the matching person.

**Calibration: prefer picking a plausible candidate over returning
null.**  Wrong-but-related links are not catastrophic — the ground
state is no link at all, and a related side-trip is usually still
useful for the reader.  Return null only when none of the candidates
is even plausibly the referent.

Return JSON: {"stable_id": "<stable_id>"} chosen verbatim from the
candidate list, or {"stable_id": null} only if no candidate is
plausibly the referent.
"""


from britannica.xrefs.llm_excerpt import clean_excerpt as _clean_excerpt  # noqa: E402


def _context_around(body: str, surface_text: str) -> str:
    """Excerpt of ``body`` centred on the first occurrence of
    ``surface_text``, ±N chars."""
    idx = body.find(surface_text)
    if idx < 0:
        # Fall back to the start of the body
        return _clean_excerpt(body, CONTEXT_CHARS_BEFORE + CONTEXT_CHARS_AFTER)
    start = max(0, idx - CONTEXT_CHARS_BEFORE)
    end = min(len(body), idx + len(surface_text) + CONTEXT_CHARS_AFTER)
    snippet = body[start:end]
    return _clean_excerpt(
        snippet, CONTEXT_CHARS_BEFORE + CONTEXT_CHARS_AFTER + len(surface_text)
    )


def build_ambiguous_set(
    session,
) -> tuple[set[str], dict[str, list[Article]]]:
    """Return (ambiguous_titles, candidates_by_title).

    ``candidates_by_title[title]`` lists the standalone article (if
    any) plus all ``TITLE, FirstName`` person-variants.
    """
    articles = (
        session.query(Article)
        .filter(Article.article_type == "article")
        .all()
    )

    person_variants: dict[str, list[Article]] = defaultdict(list)
    standalone: dict[str, Article] = {}
    for a in articles:
        if not a.title:
            continue
        n = normalize_xref_target(a.title)
        if not n:
            continue
        if "," in n:
            surname, _, first = n.partition(",")
            surname = surname.strip()
            first = first.strip()
            if surname and first:
                person_variants[surname].append(a)
        else:
            # First standalone wins for the disambiguation source.
            # In practice a clean title only resolves to one article.
            standalone.setdefault(n, a)

    ambiguous: set[str] = set()
    candidates_by_title: dict[str, list[Article]] = {}
    for surname, variants in person_variants.items():
        if surname in standalone and len(variants) >= PERSON_VARIANT_THRESHOLD:
            ambiguous.add(surname)
            cands = [standalone[surname]] + variants
            candidates_by_title[surname] = cands
    return ambiguous, candidates_by_title


def fetch_ambiguous_xrefs(
    session, ambiguous_titles: set[str]
) -> list[CrossReference]:
    """Pull every xref whose target is in the ambiguous set, regardless
    of current status.  Re-disambiguating already-resolved-to-generic
    cases is intentional — they may have been mis-linked."""
    if not ambiguous_titles:
        return []
    return (
        session.query(CrossReference)
        .filter(CrossReference.normalized_target.in_(ambiguous_titles))
        .all()
    )


def _cache_key(source_stable_id: str, surface_text: str,
               normalized_target: str) -> str:
    return f"{source_stable_id}::{surface_text}::{normalized_target}"


def build_request(idx: int, source_excerpt: str, surface_text: str,
                  candidates: list[dict]) -> Request:
    """One batch-API request per ambiguous xref."""
    candidate_lines = []
    for c in candidates:
        candidate_lines.append(
            f"- stable_id: {c['stable_id']}\n"
            f"  title: {c['title']}\n"
            f"  excerpt: {c['excerpt']}"
        )
    user_msg = (
        f"Source article excerpt (around the reference):\n{source_excerpt}\n\n"
        f"Reference surface text: {surface_text!r}\n\n"
        f"Candidate articles:\n" + "\n".join(candidate_lines)
    )
    return Request(
        custom_id=f"xref-{idx}",
        params=MessageCreateParamsNonStreaming(
            model=MODEL,
            max_tokens=120,
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
                            "stable_id": {"type": ["string", "null"]},
                        },
                        "required": ["stable_id"],
                        "additionalProperties": False,
                    }
                }
            },
            messages=[{"role": "user", "content": user_msg}],
        ),
    )


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    apply_only = "--apply-only" in sys.argv
    # ``--sync`` uses the synchronous Messages API instead of the
    # Batch API — instant results, no 50% discount, no queue wait.
    # Use for testing (small ``--limit``) or one-off interactive runs.
    sync_mode = "--sync" in sys.argv
    # ``--limit N`` caps the number of fresh LLM calls this run.
    # Cached entries are unaffected.  Useful for sample-testing
    # before committing to a full batch.
    limit = None
    for i, arg in enumerate(sys.argv):
        if arg == "--limit" and i + 1 < len(sys.argv):
            try:
                limit = int(sys.argv[i + 1])
            except ValueError:
                pass

    print("Loading cache + DB...")
    cache: dict = {}
    if CACHE_FILE.exists():
        cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))

    session = SessionLocal()
    try:
        ambiguous_titles, candidates_by_title = build_ambiguous_set(session)
        print(f"Ambiguous titles: {len(ambiguous_titles)}")

        xrefs = fetch_ambiguous_xrefs(session, ambiguous_titles)
        print(f"Xrefs targeting an ambiguous title: {len(xrefs)}")

        # Pre-fetch source articles + body excerpts.
        source_ids = {x.article_id for x in xrefs}
        source_articles = {
            a.id: a for a in (
                session.query(Article)
                .filter(Article.id.in_(source_ids))
                .all()
            )
        }

        # Pre-fetch candidate body excerpts (deduped by article id).
        cand_ids: set[int] = set()
        for cands in candidates_by_title.values():
            for a in cands:
                cand_ids.add(a.id)
        cand_articles = {
            a.id: a for a in (
                session.query(Article)
                .filter(Article.id.in_(cand_ids))
                .all()
            )
        }

        # Decide which xrefs need a fresh LLM call.
        to_resolve: list[tuple[CrossReference, str]] = []
        prepared: list[tuple[str, str, list[dict]]] = []
        for xref in xrefs:
            source = source_articles.get(xref.article_id)
            if source is None:
                continue
            sid = stable_id(source)
            key = _cache_key(sid, xref.surface_text, xref.normalized_target)
            if key in cache:
                continue
            cands_articles = candidates_by_title.get(xref.normalized_target, [])
            if len(cands_articles) < 2:
                continue
            cand_meta = []
            for a in cands_articles:
                full = cand_articles.get(a.id)
                excerpt = _clean_excerpt(full.body or "", 240) if full else ""
                cand_meta.append({
                    "stable_id": stable_id(a),
                    "title": a.title,
                    "excerpt": excerpt,
                })
            source_excerpt = _context_around(
                source.body or "", xref.surface_text
            )
            to_resolve.append((xref, key))
            prepared.append((source_excerpt, xref.surface_text, cand_meta))

        already_cached = len(xrefs) - len(to_resolve)
        if limit is not None and len(to_resolve) > limit:
            print(f"--limit {limit}: capping {len(to_resolve)} uncached "
                  f"candidates")
            skipped_for_limit = len(to_resolve) - limit
            to_resolve = to_resolve[:limit]
            prepared = prepared[:limit]
        else:
            skipped_for_limit = 0

        print(f"Already cached: {already_cached}")
        print(f"To resolve this run: {len(to_resolve)}")
        if skipped_for_limit:
            print(f"Skipped due to --limit: {skipped_for_limit}")

        if dry_run:
            print("[dry-run — no API call, no cache writes]")
            return 0

        if apply_only:
            if to_resolve:
                print(f"[apply-only — {len(to_resolve)} uncached entries "
                      f"will not be resolved]")
            return 0

        if not to_resolve:
            print("Nothing to do.")
            return 0

        client = anthropic.Anthropic()

        if sync_mode:
            # Synchronous Messages API — one call per candidate,
            # instant results, no batch discount.
            print(f"Calling Messages API synchronously "
                  f"({len(to_resolve)} requests)...")
            for i, (src_excerpt, surface, cand_meta) in enumerate(prepared):
                req = build_request(i, src_excerpt, surface, cand_meta)
                params = req["params"]
                msg = client.messages.create(**params)
                xref, key = to_resolve[i]
                chosen_stable_id = None
                text = next(
                    (b.text for b in msg.content if b.type == "text"), "{}"
                )
                try:
                    parsed = json.loads(text)
                    chosen_stable_id = parsed.get("stable_id")
                    valid_ids = {c["stable_id"] for c in cand_meta}
                    if chosen_stable_id not in valid_ids:
                        chosen_stable_id = None
                except Exception:
                    chosen_stable_id = None
                cache[key] = {
                    "chosen": chosen_stable_id,
                    "candidates": [c["stable_id"] for c in cand_meta],
                    "model": MODEL,
                }
                print(f"  [{i+1}/{len(to_resolve)}] {key}")
                print(f"      → {chosen_stable_id!r}")
        else:
            print(f"Building {len(to_resolve)} batch requests...")
            requests = [
                build_request(i, src_excerpt, surface, cands)
                for i, (src_excerpt, surface, cands) in enumerate(prepared)
            ]
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
                xref, key = to_resolve[idx]
                chosen_stable_id = None
                if result.result.type == "succeeded":
                    msg = result.result.message
                    text = next(
                        (b.text for b in msg.content if b.type == "text"),
                        "{}",
                    )
                    try:
                        parsed = json.loads(text)
                        chosen_stable_id = parsed.get("stable_id")
                        valid_ids = {
                            c["stable_id"] for c in prepared[idx][2]
                        }
                        if chosen_stable_id not in valid_ids:
                            chosen_stable_id = None
                    except Exception:
                        chosen_stable_id = None
                cache[key] = {
                    "chosen": chosen_stable_id,
                    "candidates": [c["stable_id"] for c in prepared[idx][2]],
                    "model": MODEL,
                }

        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(
            json.dumps(cache, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"Cache written: {CACHE_FILE}")
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
