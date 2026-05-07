"""Scan exported articles for likely missing-period sites.

The wikisource transcription occasionally drops a sentence-ending
period at line wraps in the print, leaving the reader with text like
"defeated by Sir R. H. Inglis He took refuge..." where the print has
"defeated by Sir R. H. Inglis. He took refuge...".

This scanner uses a tight pattern that pairs:
  * a content word (not a preposition, conjunction, article, or
    auxiliary verb — those naturally precede a capitalized
    continuation), with
  * a capitalized sentence-starter (pronouns, articles, demonstratives,
    titles, adverbial connectives, &c.), with
  * a lowercase continuation word (filters out proper-noun phrases
    like "saw John leave").

Religious-title articles are excluded because they capitalize He /
His / Him / Her mid-sentence as a deity referent — false positives
the wiki text can't be distinguished from real drops.

Usage:
    uv run python tools/diagnostics/missing_period_scan.py             # full corpus, default thresholds
    uv run python tools/diagnostics/missing_period_scan.py --min-hits 5
    uv run python tools/diagnostics/missing_period_scan.py --article 21-0054-s2-PEEL__SIR_ROBERT.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys


# Words that DO NOT typically end a sentence — finding one immediately
# before a capitalized word means the capital is a sentence-internal
# continuation, not a new sentence start ("with His grace", "to The
# Hague", "of John smith").
NOT_SENT_END = {
    "a", "an", "the",
    "of", "to", "in", "on", "at", "for", "by", "with", "as", "from",
    "into", "upon", "without", "near", "between", "among", "against",
    "through", "throughout", "via", "across", "behind", "beneath",
    "beside", "below", "above",
    "and", "or", "but", "nor", "yet", "so", "than",
    "if", "when", "where", "while", "because", "since", "until",
    "unless", "before", "after", "during", "though", "although",
    "despite", "not",
    "is", "are", "was", "were", "be", "been", "being",
    "has", "have", "had", "do", "does", "did",
    "will", "would", "shall", "should", "may", "might", "must",
    "can", "could",
    "him", "her", "them", "us", "me",
}

# Capitalized words that TYPICALLY start a sentence.  Including "With"
# per the PEEL "satisfied With" example; including determiners and
# common adverbial connectives.
SENT_START = (
    r"The|He|She|It|They|His|Her|Their|This|That|These|Those|"
    r"But|However|Moreover|Hence|Thus|Therefore|Then|"
    r"After|Before|While|If|When|Although|"
    r"In|On|At|To|For|By|With|From|"
    r"And|Or|Such|All|Each|Both|Many|Most|Some|Few|"
    r"Mr|Mrs|Sir|Lord|Lady|Dr"
)
PATTERN = re.compile(
    r"\b([A-Za-z][a-z']+)\s+(" + SENT_START + r")\s+[a-z]"
)

# Articles whose subject inherently uses capitalized He / His / Him for
# a deity referent.  The heuristic can't distinguish "saw His grace"
# (deity, capitalized mid-sentence by convention) from "saw His grace"
# (ordinary phrase after a missing period), so we exclude these
# articles entirely.
RELIGIOUS_TITLE_RE = re.compile(
    r"\b(JESUS|CHRIST|GOD|GODS|MESSIAH|SAVIOUR|HOLY|GOSPEL|EPISTLE|"
    r"BIBLE|APOSTLE|MARTYR|SAINT|ST\.|"
    r"REDEMPTION|ATONEMENT|INCARNATION|CRUCIFIXION|RESURRECTION|"
    r"ASCENSION|REVELATION|SALVATION|BAPTISM|EUCHARIST|TRINITY|"
    r"PREDESTINATION|JUSTIFICATION|SANCTIFICATION|MONOTHEISM|"
    r"MONARCHIANISM|ARIANISM|NESTORIANISM|GNOSTICISM|PELAGIANISM|"
    r"ANABAPTIST|MONISM|DUALISM|"
    r"MIRACLE|MIRACLES|PROPHECY|PROPHET|PROPHETS|"
    r"SCRIPTURE|HEBREW|JUDAISM|CHRISTIANITY|ISLAM|BUDDHISM|"
    r"PSALMS?|PROVERBS|GENESIS|EXODUS|LEVITICUS|NUMBERS|"
    r"DEUTERONOMY|JOSHUA|JUDGES|RUTH|SAMUEL|KINGS|"
    r"CHRONICLES|EZRA|NEHEMIAH|ESTHER|JOB|ECCLESIASTES|"
    r"ISAIAH|JEREMIAH|LAMENTATIONS|EZEKIEL|DANIEL|HOSEA|"
    r"MATTHEW|MARK|LUKE|JOHN|ACTS|ROMANS|CORINTHIANS|"
    r"GALATIANS|EPHESIANS|PHILIPPIANS|COLOSSIANS|THESSALONIANS|"
    r"TIMOTHY|TITUS|PHILEMON|HEBREWS|PETER|JAMES|JUDE|"
    r"DIOGNETUS|VERONICA|APOLLINARIS|RITSCHL|MOLINA|"
    r"MELISSUS|MUGGLETON|MALACHI|XENOPHANES|PELAGIUS|"
    r"PHILO|MONOPHYSITE|MONOTHELITES|MONOPHYSITISM|EVANGELIST|"
    r"BISHOP|ARCHBISHOP|CARDINAL|POPE|PATRIARCH|DIVINITY|"
    r"SHEKINAH|CHERUBIM|SERAPHIM|ANGEL|ANGELS|DEMON|DEMONS|"
    r"CHURCH|CHURCHES|MONASTERY|MONK|FRIAR|NUN|MISSIONARY|"
    r"THEOLOGY|THEOLOGIAN|THEOLOGICAL|RELIGION|RELIGIONS|"
    r"FATHER|HOLY GHOST|PROVIDENCE|SACRAMENT|HEAVEN|HELL|"
    r"ESCHATOLOGY|SOTERIOLOGY|ECCLESIOLOGY|HAGIOGRAPHY|"
    r"ZECHARIAH|HABAKKUK|MICAH|NAHUM|ZEPHANIAH|HAGGAI|"
    r"OBADIAH|JONAH|JOEL|MALACHI|FOX, GEORGE|"
    r"INSPIRATION|MEDITATION|CONTEMPLATION|MYSTICISM|MYSTIC|"
    r"COVENANT|COMMANDMENTS|TESTAMENT|PARABLE|"
    r"PHARISEES|SADDUCEES|ESSENES|GNOSTICS|MANICHAEAN|"
    r"ARMINIUS|SOCINIANISM|ANTITRINITARIAN|UNITARIAN|"
    r"BAPTIST|METHODIST|PRESBYTERIAN|EPISCOPALIAN)"
)


def find_hits(body: str) -> list[tuple[int, str]]:
    """Return list of (offset, context) for every likely missing-period
    site in ``body``.  Each context is ~70 chars surrounding the hit
    so the caller can verify by eye."""
    body = re.sub(r"\x01PAGE:\d+\x01", "", body)
    body = re.sub(r"«[^«»]+»", "", body)
    out: list[tuple[int, str]] = []
    for m in PATTERN.finditer(body):
        if m.group(1).lower() in NOT_SENT_END:
            continue
        start = max(0, m.start() - 30)
        end = min(len(body), m.end() + 40)
        out.append((m.start(), body[start:end]))
    return out


def word_count(body: str) -> int:
    body = re.sub(r"\x01PAGE:\d+\x01", "", body)
    body = re.sub(r"«[^«»]+»", "", body)
    return len(body.split())


def scan_article(path: str, *, min_words: int = 1500
                 ) -> tuple[int, int, str, int, int, int] | None:
    """Score one article.  Returns
    ``(hits, words, title, volume, lowest_level, n_unproofed)`` or
    None if the article is filtered (religious title or too short).

    ``lowest_level`` is wikisource's lowest page-quality level across
    the article's pages (1=unproofread OCR, 2=problematic,
    3=proofread, 4=validated).  ``n_unproofed`` is the count of
    pages at level 1.
    """
    try:
        d = json.load(open(path, encoding="utf-8"))
    except Exception:
        return None
    if d.get("article_type") == "plate":
        return None
    body = d.get("body", "")
    if not body:
        return None
    title = d.get("title", "")
    if RELIGIOUS_TITLE_RE.search(title):
        return None
    n_words = word_count(body)
    if n_words < min_words:
        return None
    n_hits = len(find_hits(body))
    sq = d.get("source_quality") or {}
    lowest_level = int(sq.get("lowest_level") or 0)
    n_unproofed = len(sq.get("unproofed_pages") or {})
    return (n_hits, n_words, title, int(d.get("volume", 0)),
            lowest_level, n_unproofed)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--article", help="single article filename to dump every hit for")
    p.add_argument("--min-hits", type=int, default=5,
                   help="minimum absolute hits to include in summary (default 5)")
    p.add_argument("--min-rate", type=float, default=0.0,
                   help="minimum hits/1000-words to include (default 0)")
    p.add_argument("--min-words", type=int, default=1500,
                   help="skip articles shorter than this (default 1500)")
    p.add_argument("--top", type=int, default=40,
                   help="number of articles to print in summary (default 40)")
    p.add_argument("--min-quality", type=int, default=0,
                   help="exclude articles whose lowest source-page quality is "
                        "below this level.  Wikisource quality scale: 1 = "
                        "unproofread OCR, 2 = problematic, 3 = proofread, "
                        "4 = validated.  Use --min-quality 3 to focus on "
                        "supposedly-proofread articles where missing-period "
                        "anomalies are actionable (default 0 = include all).")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    if args.article:
        path = (args.article if os.path.isabs(args.article)
                else f"data/derived/articles/{args.article}")
        d = json.load(open(path, encoding="utf-8"))
        body = d.get("body", "")
        title = d.get("title", "")
        if RELIGIOUS_TITLE_RE.search(title):
            print(f"NOTE: {title} is on the religious-title exclude list; "
                  "scoring may be unreliable.")
        hits = find_hits(body)
        print(f"{title}  ({len(hits)} hits, {word_count(body)} words)")
        for _, ctx in hits:
            print(f"  ...{ctx!r}...")
        return

    rows: list[tuple[int, int, str, int, int, int]] = []
    for f in sorted(glob.glob("data/derived/articles/[0-2]*.json")):
        r = scan_article(f, min_words=args.min_words)
        if r is None:
            continue
        n, w, t, v, lvl, unproof = r
        if n < args.min_hits:
            continue
        rate = n * 1000 / max(1, w)
        if rate < args.min_rate:
            continue
        if args.min_quality and lvl and lvl < args.min_quality:
            continue
        rows.append((n, w, t, v, lvl, unproof))

    rows.sort(reverse=True)
    print(f"Articles with >= {args.min_hits} hits "
          f"and >= {args.min_rate:.1f}/1k rate "
          f"(non-religious title, >= {args.min_words} words): {len(rows)}")
    print()
    print(f"{'Hits':>5}  {'Words':>7}  {'Rate':>5}  {'Lvl':>3}  "
          f"{'Unprf':>5}  {'Vol':>3}  Title")
    print("-" * 90)
    for n, w, t, v, lvl, unproof in rows[:args.top]:
        rate = n * 1000 / max(1, w)
        lvl_s = str(lvl) if lvl else "?"
        unp_s = str(unproof) if unproof else ""
        print(f"{n:>5}  {w:>7}  {rate:>5.1f}  {lvl_s:>3}  "
              f"{unp_s:>5}  {v:>3}  {t[:55]}")


if __name__ == "__main__":
    main()
