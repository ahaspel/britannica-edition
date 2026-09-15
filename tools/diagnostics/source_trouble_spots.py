"""Rank transcription trouble spots using local text, without OCR or model calls.

Uses the canonical corpus loader and search-text converter, and reuses the
existing missing-period detector. Proposals are NOT corrections. Literal source
matches locate candidates; ambiguous/unmatched locations are retained separately.
Run: .venv/Scripts/python.exe tools/diagnostics/source_trouble_spots.py
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import re
import sys
import time
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from britannica.export.corpus import load_corpus
from britannica.markers import markers_to_text
from britannica.source_pages import load_pages
from britannica.corpora import current_corpus
from britannica.export.pages import leaf_for_ws
from missing_period_scan import find_hits, PATTERN, RELIGIOUS_TITLE_RE

WORD = re.compile(r"\b[^\W\d_]+\b", re.UNICODE)
ASCII_WORD = re.compile(r"[a-z]{4,24}\Z")
ENCODING = re.compile(r"Â[\u0080-\u00bf]|Ã[\u0080-\u00bf]|â[€\u0080-\u009f][^\s]?|�")
MIXED = re.compile(r"\b[A-Za-z01]{5,24}\b")
REPEAT = re.compile(r"\b([A-Za-z]{4,})[ \t]+\1\b", re.I)
# Wikisource's proofreading level, read the same way by both page scans below.
PAGEQUALITY = re.compile(r'<pagequality\s+level="(\d)"')
CONFUSIONS = (("rn", "m"), ("m", "rn"), ("cl", "d"), ("d", "cl"),
              ("li", "h"), ("h", "li"), ("vv", "w"), ("ii", "n"))
WEIGHTS = {"encoding": 8, "mixed_digit": 7, "local_variant": 6,
           "ocr_variant": 3, "repeated_word": 2, "missing_period": 1}


def alternatives(word: str):
    """Only single, named OCR confusions; no general fuzzy spelling guesses."""
    for old, new in CONFUSIONS:
        start = 0
        while (i := word.find(old, start)) >= 0:
            yield word[:i] + new + word[i + len(old):]
            start = i + 1


def context(text, start, end, width=100):
    return " ".join(text[max(0, start-width):min(len(text), end+width)].split())


def detect(text, title, local, vocab, variants):
    found = {}

    def add(start, end, kind, suggested="", reason=""):
        key = (start, end)
        row = found.setdefault(key, dict(offset=start, end=end, token=text[start:end],
                                        context=context(text, start, end), signals=[],
                                        suggested=suggested, reasons=[]))
        if kind not in row["signals"]:
            row["signals"].append(kind)
            row["reasons"].append(reason)
        if suggested:
            row["suggested"] = suggested

    for m in ENCODING.finditer(text):
        add(*m.span(), "encoding", reason="Characteristic encoding debris; reading unknown")
    for m in WORD.finditer(text):
        word = m[0].lower()
        if word not in variants or m[0].isupper():
            continue
        choices = variants[word]
        preferred = max(choices, key=lambda w: (local[w] >= 3, local[w], vocab[w]))
        kind = "local_variant" if local[preferred] >= 3 else "ocr_variant"
        add(*m.span(), kind, preferred,
            f"Corpus {word}={vocab[word]}, {preferred}={vocab[preferred]}; "
            f"article alternative={local[preferred]}; one OCR confusion")
    for m in MIXED.finditer(text):
        word = m[0]
        if not re.search("[01]", word) or not re.search("[a-z]{3}", word):
            continue
        proposals = {word.lower().replace("0", "o").replace("1", ch) for ch in ("l", "i")}
        proposals = [w for w in proposals if vocab[w] >= 30]
        if proposals:
            candidate = max(proposals, key=lambda w: vocab[w])
            add(*m.span(), "mixed_digit", candidate,
                f"Letter/digit mixture; {candidate} occurs {vocab[candidate]} times")
    for m in REPEAT.finditer(text):
        if m[1].lower() not in {"that", "what", "very", "murmur"}:
            add(*m.span(), "repeated_word", reason="Adjacent repeated word; may be intentional")
    if not RELIGIOUS_TITLE_RE.search(title):
        for offset, _ in find_hits(text):
            m = PATTERN.match(text, offset)
            if m:
                # The existing detector stops after the first letter of the next
                # word. Complete that word before the literal whole-word lookup.
                end = m.end()
                while end < len(text) and text[end].isalpha():
                    end += 1
                add(m.start(), end, "missing_period", reason="Existing missing_period_scan heuristic")
    return list(found.values())


def locate(row, pages):
    """Locate literal token/phrase in article pages, using context only as tie-break.

    This searches SOURCE; it does not convert or strip wikitext. A matching word
    is provenance evidence, not proof that the word is wrong. Ties stay ambiguous.
    """
    pattern = re.compile(r"(?<!\w)" + r"\s+".join(re.escape(s) for s in row["token"].split())
                         + r"(?!\w)") if row["signals"] != ["encoding"] else re.compile(re.escape(row["token"]))
    needle_words = set(w.lower() for w in WORD.findall(row["context"]) if len(w) > 3)
    matches = []
    for page in pages:
        for m in pattern.finditer(page.text):
            raw_context = context(page.text, m.start(), m.end(), 180)
            shared = len(needle_words & set(w.lower() for w in WORD.findall(raw_context)))
            matches.append((shared, page.page, m.start(), raw_context, str(page.path)))
    matches.sort(reverse=True)
    row["source_matches"] = len(matches)
    if not matches:
        row["location"] = "unmatched"
        return
    if len(matches) > 1 and (matches[0][0] < 3 or matches[0][0] - matches[1][0] < 2):
        row["location"] = "ambiguous"
        row["possible_pages"] = sorted({m[1] for m in matches})
        return
    _, page, offset, snippet, path = matches[0]
    row.update(location="literal_unique" if len(matches) == 1 else "context_disambiguated",
               ws_page=page, source_offset=offset, source_context=snippet, source_file=path,
               leaf=leaf_for_ws(row["volume"], page))
    row["source_url"] = "https://en.wikisource.org/wiki/" + quote(current_corpus().page_title(row["volume"], page), safe=":/")


def write_csv(path, rows, columns):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v
                             for k, v in row.items() if k in columns})


def quality_breakdown(out, page_meta=None):
    """Compare flag rates against all covered pages, not just shortlisted pages.

    Accept the main run's inventory, or reconstruct it through canonical loaders
    when adding this breakdown to an already completed report.
    """
    out = Path(out)
    if page_meta is None:
        corpus, _ = load_corpus(require=("id", "body", "volume", "ws_page_start", "ws_page_end"))
        covered = defaultdict(set)
        for d in corpus.values():
            covered[d["volume"]].update(range(d["ws_page_start"], d["ws_page_end"] + 1))
        del corpus
        page_meta = {}
        for volume, wanted in sorted(covered.items()):
            pages, _ = load_pages(volume, pages=wanted)
            for page in pages:
                quality = PAGEQUALITY.search(page.text)
                page_meta[(volume, page.page)] = dict(volume=volume, ws_page=page.page,
                    quality=int(quality[1]) if quality else "unknown")
    with (out / "pages.csv").open(encoding="utf-8-sig", newline="") as f:
        ranked = list(csv.DictReader(f))
    rows = [json.loads(line) for line in (out / "candidates.jsonl").read_text(encoding="utf-8").splitlines()]
    total = Counter(str(p["quality"]) for p in page_meta.values())
    flagged = Counter(p["quality"] for p in ranked)
    top = Counter(p["quality"] for p in ranked[:50])
    strong = Counter(p["quality"] for p in ranked
                     if set(json.loads(p["signals"])) - {"missing_period", "repeated_word"})
    names = {"0": "Without text", "1": "Unproofread", "2": "Problematic",
             "3": "Proofread", "4": "Validated", "unknown": "Unknown"}
    table = [dict(level=level, status=names[level], covered_pages=total[level],
                  flagged_pages=flagged[level], flag_rate_percent=round(100*flagged[level]/total[level], 2),
                  strong_signal_pages=strong[level],
                  strong_flag_rate_percent=round(100*strong[level]/total[level], 2),
                  top_50_pages=top[level]) for level in names if total[level]]
    write_csv(out / "quality.csv", table, list(table[0]))
    reviewed = [r for r in rows if "ws_page" in r and
                str(page_meta[(r["volume"], r["ws_page"])]["quality"]) in {"3", "4"}]
    reviewed.sort(key=lambda r: (-r["weight"], r.get("page_rank", 10**9)))
    lines = ["# Trouble spots by upstream proofreading status", "",
             "Status was not used to rank candidates. Rates below use all covered source pages as denominators. "
             "They measure detector flags, not verified errors; source status is from the local snapshot.", "",
             "| Status | Covered pages | Flagged pages | Flag rate | Strong-signal pages | Strong rate | In top 50 |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for r in table:
        lines.append(f"| {r['status']} | {r['covered_pages']:,} | {r['flagged_pages']:,} | "
                     f"{r['flag_rate_percent']:.2f}% | {r['strong_signal_pages']} | "
                     f"{r['strong_flag_rate_percent']:.2f}% | {r['top_50_pages']} |")
    lines += ["", "Strong signals exclude missing-period and repeated-word heuristics, which have substantial "
              "legitimate matches. This is still a heuristic distinction, not a calibrated confidence estimate.", "",
              "## Strongest leads on proofread or validated pages", "",
              "These are suggestions to inspect against scans. Correct historical/foreign spellings can appear here.", "",
              "| Candidate | Volume:WS page | Status | Article | Token | Possible reading | Signals |",
              "|---|---|---|---|---|---|---|"]
    for r in reviewed[:40]:
        q = str(page_meta[(r["volume"], r["ws_page"])]["quality"])
        lines.append(f"| {r['candidate_id']} | [{r['volume']}:{r['ws_page']}]({r['source_url']}) | "
                     f"{names[q]} | {r['title'].replace('|', '/')} | `{r['token']}` | "
                     f"`{r['suggested']}` | {', '.join(r['signals'])} |")
    (out / "quality.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    summary_path = out / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["quality_breakdown"] = table
    summary["script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    report_path = out / "report.md"
    report = report_path.read_text(encoding="utf-8")
    link = "[Flag rates by proofreading status and leads on proofread pages](quality.md)"
    if link not in report:
        report = report.replace("## Method and limits", link + "\n\n## Method and limits", 1)
        report_path.write_text(report, encoding="utf-8")
    print(json.dumps(table, indent=2), flush=True)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=Path("docs/reports/source-trouble-spots-2026-09-12"))
    args = ap.parse_args()
    started = time.monotonic()
    if current_corpus().key != "eb1911":
        raise SystemExit("This report requires the EB1911 corpus setting")
    print("Loading complete exported corpus", flush=True)
    corpus, _ = load_corpus(require=("id", "body", "title", "volume", "ws_page_start", "ws_page_end"))
    if not corpus:
        raise SystemExit("No articles found")
    digest = hashlib.sha256()
    articles = []
    empty_records = []
    vocab = Counter()
    words_total = 0
    for path, d in corpus.items():
        if not d["body"]:
            empty_records.append(dict(filename=path.name, title=d["title"]))
        digest.update(path.name.encode())
        digest.update(d["body"].encode())
        text = markers_to_text(d["body"])
        counts = Counter(w.lower() for w in WORD.findall(text))
        vocab.update(counts)
        words_total += sum(counts.values())
        articles.append(dict(filename=path.name, title=d["title"], volume=d["volume"],
                             ws_start=d["ws_page_start"], ws_end=d["ws_page_end"],
                             text=text, words=sum(counts.values()),
                             article_url="https://britannica11.org/article/" + d["stable_id"]))
    del corpus
    print(f"Vocabulary: {len(vocab):,} forms, {words_total:,} tokens", flush=True)
    variants = {}
    for word, count in vocab.items():
        if count > 3 or not ASCII_WORD.fullmatch(word):
            continue
        choices = sorted({w for w in alternatives(word) if vocab[w] >= max(50, 100*count)})
        if choices:
            variants[word] = choices
    print(f"Rare OCR-confusable forms: {len(variants):,}", flush=True)
    rows = []
    by_volume = defaultdict(list)
    for article_number, article in enumerate(articles, 1):
        text = article.pop("text")
        local = Counter(w.lower() for w in WORD.findall(text))
        hits = detect(text, article["title"], local, vocab, variants)
        for hit in hits:
            hit.update(article)
            hit["weight"] = max(WEIGHTS[s] for s in hit["signals"])
            rows.append(hit)
        by_volume[article["volume"]].append((article, hits))
        if article_number % 5000 == 0:
            print(f"  Detectors: {article_number:,}/{len(articles):,} records", flush=True)
    print(f"Candidates: {len(rows):,}; locating in corrected source pages", flush=True)
    page_meta = {}
    source_digest = hashlib.sha256()
    for volume, groups in sorted(by_volume.items()):
        loaded, _ = load_pages(volume)
        pages = {p.page: p for p in loaded}
        covered = set()
        for article, hits in groups:
            wanted = range(article["ws_start"], article["ws_end"] + 1)
            missing = set(wanted) - pages.keys()
            if missing:
                raise RuntimeError(f"Article source pages missing: {article['filename']} {missing}")
            covered.update(wanted)
            scoped = [pages[p] for p in wanted]
            for hit in hits:
                locate(hit, scoped)
        for p in loaded:
            source_digest.update(f"{volume}:{p.page}:".encode())
            source_digest.update(p.text.encode())
            if p.page not in covered:
                continue
            quality = PAGEQUALITY.search(p.text)
            page_meta[(volume, p.page)] = dict(volume=volume, ws_page=p.page,
                quality=int(quality[1]) if quality else "unknown",
                source_file=str(p.path), leaf=leaf_for_ws(volume, p.page))
        print(f"  Volume {volume}: {len(covered)} covered pages", flush=True)
    # One source occurrence can be present in multiple article exports. Count once.
    unique = {}
    for row in rows:
        key = ((row["volume"], row["ws_page"], row["source_offset"], row["token"])
               if "ws_page" in row else (row["filename"], row["offset"], row["token"]))
        if key in unique:
            old = unique[key]
            old["signals"] = sorted(set(old["signals"]) | set(row["signals"]))
            old["weight"] = max(old["weight"], row["weight"])
        else:
            unique[key] = row
    rows = list(unique.values())
    pages_found = defaultdict(list)
    for i, row in enumerate(rows, 1):
        row["candidate_id"] = f"C{i:06d}"
        row["review_status"] = "unreviewed"
        if "ws_page" in row:
            pages_found[(row["volume"], row["ws_page"])].append(row)
    ranked = []
    for key, hits in pages_found.items():
        families = sorted({s for h in hits for s in h["signals"]})
        # Cap repeated same-token signals: gibberish does not receive infinite credit.
        strongest = {}
        for h in hits:
            strongest[h["token"]] = max(strongest.get(h["token"], 0), h["weight"])
        score = sum(sorted(strongest.values(), reverse=True)[:12]) + 3*(len(families)-1)
        ranked.append(dict(**page_meta[key], score=score, candidates=len(hits), signals=families,
                           articles=sorted({h["title"] for h in hits}),
                           source_url=hits[0]["source_url"],
                           neighbors=sum((key[0], key[1]+delta) in pages_found for delta in (-1, 1))))
    ranked.sort(key=lambda r: (-r["score"], -len(r["signals"]), r["volume"], r["ws_page"]))
    for rank, page in enumerate(ranked, 1):
        page["rank"] = rank
        for row in pages_found[(page["volume"], page["ws_page"])]:
            row["page_rank"] = rank
    rows.sort(key=lambda r: (r.get("page_rank", 10**9), -r["weight"], r["candidate_id"]))
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    with (out / "candidates.jsonl").open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    write_csv(out / "candidates.csv", rows,
              ["candidate_id", "page_rank", "volume", "ws_page", "leaf", "title", "signals",
               "token", "suggested", "context", "reasons", "location", "source_matches",
               "source_context", "source_offset", "source_file", "source_url", "article_url", "review_status"])
    write_csv(out / "pages.csv", ranked,
              ["rank", "volume", "ws_page", "leaf", "quality", "score", "candidates", "signals",
               "neighbors", "articles", "source_url", "source_file"])
    # Diverse shortlist; no more than ten seed pages from one volume.
    selected = {}
    volume_counts = Counter()
    for family in WEIGHTS:
        for page in [p for p in ranked if family in p["signals"]][:3]:
            key = (page["volume"], page["ws_page"])
            if key not in selected:
                selected[key] = "ranked"
                volume_counts[key[0]] += 1
    for page in ranked:
        key = (page["volume"], page["ws_page"])
        if len(selected) >= 30:
            break
        if key not in selected and volume_counts[key[0]] < 10:
            selected[key] = "ranked"
            volume_counts[key[0]] += 1
    seeds = list(selected)
    for key in seeds:
        for delta in (-1, 1):
            neighbor = (key[0], key[1]+delta)
            if neighbor in page_meta and neighbor not in selected and len(selected) < 40:
                selected[neighbor] = "neighbor"
    rng = random.Random(20260912)
    pool = sorted(set(page_meta) - set(pages_found) - set(selected))
    for key in rng.sample(pool, min(10, len(pool))):
        selected[key] = "random_unflagged"
    sample = [dict(**page_meta[k], group=g, review_status="unreviewed") for k, g in selected.items()]
    write_csv(out / "review_sample.csv", sample,
              ["group", "volume", "ws_page", "leaf", "quality", "source_file", "review_status"])
    summary = dict(created_utc=datetime.now(timezone.utc).isoformat(), export_records=len(articles),
        nonempty_records=len(articles)-len(empty_records), empty_records=empty_records,
        prose_tokens=words_total, vocabulary=len(vocab), source_pages=len(page_meta),
        candidate_occurrences=len(rows), flagged_pages=len(ranked),
        signals=dict(Counter(s for r in rows for s in r["signals"])),
        locations=dict(Counter(r["location"] for r in rows)),
        body_manifest_sha256=digest.hexdigest(), corrected_source_sha256=source_digest.hexdigest(),
        corrections_sha256=hashlib.sha256(Path("data/corrections.json").read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        seconds=round(time.monotonic()-started, 1), paid_calls=0,
        review_sample=dict(Counter(selected.values())))
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    lines = ["# Source trouble spots — 2026-09-12", "", "Unreviewed candidates, not verified transcription errors.", "",
        f"Scanned **{len(articles)-len(empty_records):,} nonempty local exports** "
        f"({len(articles):,} records including {len(empty_records)} empty plate record), **{words_total:,} prose tokens**, "
        f"covering **{len(page_meta):,} source pages**. No OCR, model calls, network access, or source edits.", "",
        f"**{len(rows):,} candidate occurrences; {len(ranked):,} pages with located candidates.**", "",
        "## Method and limits", "",
        "Uses the canonical search-text converter, not a new wikitext stripper. Its non-prose exclusions "
        "include marked formulae, tables, footnotes and verse: this is a prose triage, not full-content proofreading. "
        "Unmarked garbled mathematics can still occur in the resulting text and is flagged as corruption. "
        "ASCII vocabulary candidates require corpus frequency ≤3, one named OCR confusion, and an alternative "
        "occurring ≥50 times and ≥100× as often. An alternative repeated ≥3 times in the article ranks higher. "
        "Historic words, foreign text and valid repetitions can still produce false alarms.", "",
        "Missing-period findings reuse the existing detector and its religious-title exclusions. "
        "Encoding and digit/letter signals rank highest. Page scores sum up to twelve distinct-token weights "
        "and reward independent signal families; they are heuristic priorities, not probabilities. "
        "Page length is not available in the converted article text, so no page word-density claim is made. "
        "Neighbor counts and raw proofread status are reported, not treated as correctness verdicts.", "",
        "Locations are literal matches in correction-applied source within the article's Wikisource page range. "
        "Repeated matches use context to disambiguate; tied or weak matches remain ambiguous. "
        "Presence in source is not scan verification. Suggestions never modify the text.", "",
        "## Detector counts", "", "| Signal | Candidate occurrences |", "|---|---:|"]
    lines += [f"| {s} | {n:,} |" for s, n in summary["signals"].items()]
    lines += ["", f"Location outcomes: `{json.dumps(summary['locations'])}`.", "",
              "## First 50 ranked pages", "", "| Rank | Volume:WS page | Score | Candidates | Signals | Articles |",
              "|---:|---|---:|---:|---|---|"]
    for page in ranked[:50]:
        titles = "; ".join(page["articles"]).replace("|", "\\|")
        lines.append(f"| {page['rank']} | [{page['volume']}:{page['ws_page']}]({page['source_url']}) "
                     f"| {page['score']} | {page['candidates']} | {', '.join(page['signals'])} | {titles} |")
    # An additional view exposes lexical damage beyond the encoding-heavy leaders.
    lexical = [r for r in rows if "ws_page" in r and
               any(s in r["signals"] for s in ("mixed_digit", "local_variant", "ocr_variant"))]
    lexical.sort(key=lambda r: (-r["weight"], r["volume"], r["ws_page"]))
    lines += ["", "## Word-level leads beyond the encoding ranking", "",
              "These are proposed readings, not scan-verified corrections.", "",
              "| Volume:WS page | Article | Source token | Possible reading |", "|---|---|---|---|"]
    for row in lexical[:50]:
        lines.append(f"| [{row['volume']}:{row['ws_page']}]({row['source_url']}) | "
                     f"{row['title'].replace('|', '/')} | `{row['token']}` | `{row['suggested']}` |")
    lines += ["", "## Passages from the first 30 pages", ""]
    for page in ranked[:30]:
        lines += [f"### {page['rank']}. Volume {page['volume']}, Wikisource page {page['ws_page']}", ""]
        for row in sorted(pages_found[(page["volume"], page["ws_page"])], key=lambda r: -r["weight"])[:5]:
            lines += [f"- **{row['candidate_id']} · {', '.join(row['signals'])}** — `{row['token']}`"
                      + (f" → possible `{row['suggested']}`" if row["suggested"] else ""),
                      f"  {row['context']}", ""]
    lines += ["## Review files", "", "- [All ranked pages](pages.csv)",
              "- [All candidates with source context](candidates.csv)",
              "- [Machine-readable candidates](candidates.jsonl)",
              "- [50-page review sample](review_sample.csv)", "- [Counts and input fingerprints](summary.json)", "",
              "The review sample is an allocation for subsequent scan inspection, not a completed evaluation. "
              "Neighbor pages are provisional until seed errors are verified. Random controls are selected "
              "from unflagged covered pages using seed 20260912; they are not a random sample of the entire book. "
              "Detector precision, recall and actual error counts remain unmeasured.", ""]
    (out / "report.md").write_text("\n".join(lines), encoding="utf-8")
    quality_breakdown(out, page_meta)
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    print(f"Report: {out / 'report.md'}", flush=True)


if __name__ == "__main__":
    main()
