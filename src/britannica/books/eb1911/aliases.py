"""EB1911's extra names for its articles — two of the alias sources the
resolver's overlay merges (``Corpus.alias_sources``).

  * ``build_alias_map``: the display text of EB1911's own link templates,
    ``{{EB1911 lkpl|Target|Display}}`` and ``{{1911link|Target|Display}}`` —
    human-curated mappings placed by Wikisource editors.
  * ``build_vol29_index_aliases``: the master index in volume 29, each
    topic mapped to the article at its first vol-page reference.

The Britannica's sources, not the engine's: moved out of
xrefs/alias_table.py (wikikit step 5).  The engine's own, generic source —
Wikisource ``<section begin>`` names — stays there.
"""
import json
import re
from collections import defaultdict

from britannica.corpora import current_corpus
from britannica.source_pages import load_pages
from britannica.util.strings import strip_html_tags, until_stable


def build_alias_map() -> dict[str, str]:
    """Build a map of alias -> canonical target from raw wikitext files.

    Returns dict mapping uppercased alias to uppercased canonical title.
    When multiple targets exist for an alias, the most common one wins.
    """
    # Collect alias -> list of targets (may have multiple)
    raw_aliases: dict[str, list[str]] = defaultdict(list)

    # One reader for the raw source ([[feedback_honesty_surface_failures]]): a page
    # it cannot read RAISES rather than dropping the aliases on it, which would
    # silently shrink the xref table and look like a corpus with fewer aliases.
    for page in load_pages()[0]:
        _extract_aliases_from_wikitext(page.text, raw_aliases)

    # Resolve to single target per alias (most frequent)
    alias_map: dict[str, str] = {}
    for alias, targets in raw_aliases.items():
        # Skip noisy aliases
        if len(alias) <= 2:
            continue
        if alias in ("ABOVE", "BELOW", "HERE", "THERE", "FURTHER"):
            continue

        # Pick the most common target
        from collections import Counter
        counts = Counter(targets)
        best_target = counts.most_common(1)[0][0]
        alias_map[alias] = best_target

    return alias_map


def _extract_aliases_from_wikitext(
    raw: str, aliases: dict[str, list[str]]
) -> None:
    """Extract alias mappings from a single page's raw wikitext."""
    # {{EB1911 lkpl|Target|Display}}
    #
    # EB1911 ONLY.  `DNB` was harvested here too and it is written backwards for
    # this purpose: `{{DNB lkpl|Walsh, Peter|Dict. Nat. Biog}}` names the PERSON
    # in the target slot and a fixed generic phrase in the display, so
    # `aliases[display].append(target)` taught the table that the words "Dict.
    # Nat. Biog." mean Peter Walsh.  `most_common` then crowned one owner per
    # spelling — WALSH, PETER for the bare form, WALSINGHAM for the one with a
    # trailing period — and every article citing the DNB linked its citation to
    # a stranger.  Sixteen reached production.
    #
    # The apostrophe guard below is why it was only SOME articles: it drops the
    # instances whose italics sit inside the braces and keeps the ones where they
    # sit outside, so which person won was decided by Wikisource punctuation.
    for m in re.finditer(
        r"\{\{EB1911\s+lkpl\|([^|}]+)\|([^}]+)\}\}", raw, re.I
    ):
        target = m.group(1).strip().upper()
        display = m.group(2).strip().upper()

        if target == display:
            continue
        if len(display) > 50:
            continue
        # Skip wiki markup fragments
        if any(c in display for c in "'{}|<>"):
            continue

        aliases[display].append(target)

    # {{1911link|Target|Display}}
    for m in re.finditer(
        r"\{\{1911link\|([^|}]+)\|([^}]+)\}\}", raw, re.I
    ):
        target = m.group(1).strip().upper()
        display = m.group(2).strip().upper()

        if target == display:
            continue
        if len(display) > 50:
            continue
        if any(c in display for c in "'{}|<>"):
            continue

        aliases[display].append(target)


def _strip_vol29_wikitext(text: str) -> str:
    """Normalize vol 29 index page wikitext to a scannable plain form.

    Strips <noinclude>, page-heading + running-header templates, other
    decorative templates, and wiki link wrappers. Preserves punctuation
    that matters to the index grammar (commas, semicolons, dashes).
    """
    text = re.sub(r"<noinclude>.*?</noinclude>", "", text, flags=re.DOTALL)
    text = re.sub(r"\{\{EB1911 Page Heading[^}]*\}\}", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{running header[^}]*\}\}", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{EB1911 Shoulder Heading[^}]*\}\}", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{c\|[^}]*\}\}", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{center\|[^}]*\}\}", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{xx?-?larger\|[^}]*\}\}", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{sc\|([^}]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{11link\|([^|}]+)\|?[^}]*\}\}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{EB1911 lkpl\|([^|}]+)\|?[^}]*\}\}", r"\1", text, flags=re.IGNORECASE)
    # Strip any remaining templates
    text = until_stable(text, lambda t: re.sub(r"\{\{[^{}]*\}\}", "", t))
    # Replace wiki links [[X|Y]] -> Y, [[X]] -> X
    text = re.sub(r"\[\[[^\]|]*\|([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    # Strip HTML tags
    text = strip_html_tags(text)
    # Collapse whitespace
    text = re.sub(r"&nbsp;|&emsp;|&thinsp;", " ", text)
    text = re.sub(r"''", "", text)  # drop italic markers
    return text


# Matches one volume-page reference: "1-424" or "19-678 (A4)" or "7-736a".
_VOLPAGE_RE = re.compile(r"\b(\d{1,2})-(\d{1,4})[a-d]?\b")


def build_vol29_index_aliases() -> dict[str, str]:
    """Parse vol 29's transcribed index entries into topic → article title.

    Each entry is a topic (article title or subtopic) followed by one
    or more "vol-page" references. We pick the FIRST reference (that's
    the primary article on the topic per the index's conventions) and
    map to whichever article in our DB covers that vol+page.

    Only topics that map unambiguously and whose article exists are
    included. This catches things like "PENINSULAR WAR -> NAPOLEONIC
    CAMPAIGNS" when the index points there.
    """
    from britannica.db.models import Article
    from britannica.db.session import SessionLocal

    session = SessionLocal()
    try:
        articles = [
            a for a in session.query(Article).all()
            if a.article_type == "article"
        ]
    finally:
        session.close()

    # Index by (vol, page) -> article title. Each page can belong to
    # multiple articles (when an article spans one page); prefer the
    # article whose page range INCLUDES this page more specifically
    # (earlier start, later end are both fine; we just pick any).
    by_vol_page: dict[tuple[int, int], str] = {}
    for a in articles:
        if a.page_start is None or a.page_end is None:
            continue
        for p in range(a.page_start, a.page_end + 1):
            key = (a.volume, p)
            # First-wins keeps the canonical article for that page.
            if key not in by_vol_page:
                by_vol_page[key] = a.title.strip().upper()

    result: dict[str, str] = {}

    # The OCR fallback for pages Wikisource hasn't transcribed.  A REQUIRED
    # input: it was read only if present and silently skipped if unreadable,
    # so a lost or corrupt file shrank the alias table with no signal — the
    # untranscribed pages simply contributed nothing.  The same held for vol
    # 29's pages (`if not _VOL29_DIR.exists(): return {}`); `load_pages(29)`
    # raises on a missing volume now, as it does for every other caller.
    ocr_data: dict[str, str] = json.loads(
        current_corpus().derived("vol29_ocr.json").read_text(encoding="utf-8"))

    for page in load_pages(29)[0]:
        text = _strip_vol29_wikitext(page.text)
        if not text.strip():
            # Fall back to OCR for pages Wikisource has not transcribed.  This is
            # an EMPTY page, not an unreadable one — the reader raises on those.
            text = ocr_data.get("%04d" % page.page, "")
            if not text.strip():
                continue

        # Walk line by line looking for index entries.
        for line in text.splitlines():
            line = line.strip()
            if not line or len(line) < 6:
                continue
            # Entry grammar (approximate):
            #   TOPIC [, sub]*  [qualifier]  vol-page [; vol-page]...
            # We only need TOPIC and the first vol-page.
            m = _VOLPAGE_RE.search(line)
            if not m:
                continue
            vol = int(m.group(1))
            page = int(m.group(2))
            if not (1 <= vol <= 28 and 1 <= page <= 1200):
                continue
            topic = line[:m.start()].strip().rstrip(",;:")
            # Drop trailing qualifier words after the last comma (e.g.
            # "ABEOKUTA, Nig." -> keep only "ABEOKUTA").
            if "," in topic:
                head, _, tail = topic.partition(",")
                # Only drop the tail if it's a short qualifier (not a
                # real name like "NELSON, HORATIO")
                if len(tail.strip()) <= 10 and not tail.strip().isupper():
                    topic = head.strip()
            topic = topic.upper()
            if not topic or len(topic) < 3:
                continue
            # Skip topics that are obviously noise
            if not re.match(r"^[A-Z\u00C0-\u00DE]", topic):
                continue

            target_title = by_vol_page.get((vol, page))
            if target_title is None:
                continue

            # Don't overwrite the canonical article title with itself
            if topic == target_title:
                continue

            # First-wins dedup
            if topic not in result:
                result[topic] = target_title

    return result
