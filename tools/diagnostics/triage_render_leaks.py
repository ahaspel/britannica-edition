"""Triage every render leak into PRODUCER BUG vs RAW-SOURCE ERROR.

The leak audit answers "what came out looking like markup?".  It does not answer
the question that decides who fixes it: *was the source well-formed?*  That is the
discriminator ([[feedback_source_is_the_only_excuse]]): a wrong render is faithful
ONLY if the raw source really had it; otherwise it is a producer bug.

THE OLD VERSION ANSWERED NOTHING.  It searched the raw source for the leaked
snippet's first 24 characters — but a leaked snippet is RENDERED output, so those
characters are `{{dent/e}}<p>Observe` or `</td></tr></table>{{outdent/e}}`, and no
raw page has ever contained a `<p>` we emitted.  Every lookup missed, every site
came back "not locatable", and the report read `PRODUCER: 0` — a false CLEAN over
83 leak sites we already knew were ours.  It also searched a whole VOLUME glued
into one string, where a template opened on page 100 is "closed" by an unrelated
`}}` on page 900, and it died on a UnicodeEncodeError before printing its last
section.

So the probe is now the SOURCE form of the construct, and the scope is the
article's own pages:

  * the construct is NOT in the article's source in any form -> PRODUCER; we
    invented it (`</template>`, a marker, a `:` we failed to peel).
  * it IS there and its own site is well-formed -> PRODUCER; the source was
    ordinary and we failed to recognize/recurse it.
  * it IS there and its own site is malformed -> SOURCE; the transcription is
    broken and a faithful pipeline surfaces it.  Fix belongs in
    `data/corrections.json` ([[feedback_corrections_json]]).

SCOPE IS THE ARTICLE'S PAGE RANGE, which is the tightest slice the DB can name:
`Article.body` is the marker stream, not wikitext, so there is no stored raw slice
per article.  A page carries several articles, so a construct left open by a
NEIGHBOUR on the same page reads here as balanced.  That is stated, not hidden —
it biases toward PRODUCER, the verdict that costs us work rather than the one that
excuses it.

Usage:  uv run python tools/diagnostics/triage_render_leaks.py [--limit N]
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, "src")
sys.stdout.reconfigure(encoding="utf-8")

from britannica.db.models import Article                    # noqa: E402
from britannica.db.session import SessionLocal              # noqa: E402
from britannica.export.corpus import load_corpus            # noqa: E402
from britannica.render.leaks import find_leaks              # noqa: E402
from britannica.source_pages import load_pages              # noqa: E402
from britannica.util.strings import HTML_TAG_RE             # noqa: E402
from britannica.wikitext import mask_non_template, template_end           # noqa: E402

PRODUCER, SOURCE = "PRODUCER", "SOURCE"

_ESC_TAG = re.compile(r"&lt;(/?)([a-zA-Z][a-zA-Z0-9]*)")
_TEMPLATE_OPEN = re.compile(r"\{\{\s*([^|{}\n<]{1,40})")
_ATTR = re.compile(
    r"\b(?:style|align|valign|colspan|rowspan|bgcolor|scope|cellpadding"
    r"|cellspacing|width|height)=[^|<\s]{0,30}")
# A colon run that OPENS content.  The lookbehind drops a CSS colon
# (`padding-left:1.6em`) belonging to one of our own tags caught in the window.
_COLONS = re.compile(r"(?<![A-Za-z]):+")
# HTML void elements: they never take a closing tag, so a `</br>` in the source
# is a stray by definition rather than one half of a pair.
_VOID_ELEMENTS = frozenset({"br", "hr", "img", "wbr", "col", "input", "meta", "link"})

_BRACES = (r"\{\{", r"\}\}")
# Sentinel pair meaning "unmatched by definition" — no counting required.
_VOID = ("VOID", "VOID")
# Sentinel pair meaning "decide by what ENCLOSES it in the source".
_ATTR_ENCLOSURE = ("ATTR", "ATTR")


def _every_occurrence_closes(src, opener):
    """Does EVERY `opener` occurrence in this source reach a matching `}}`?

    Per-occurrence depth scan, because balance is a property of the SITE, not of
    the page ([[feedback_measure_at_decision_site]]).  A page-wide `{{` vs `}}`
    tally convicts a well-formed template of the imbalance of some unrelated one
    five pages away — EXCHEQUER's `{{Flex wrap centre/s}}` is perfectly balanced
    and a count that was off by one across its five pages called it a source
    error.  -> True / False / None if the opener is not present.
    """
    s = mask_non_template(src)
    i = s.find(opener)
    if i < 0:
        return None
    while i >= 0:
        if template_end(s, i) is None:
            return False
        i = s.find(opener, i + 1)
    return True


def encloses(src, pos):
    """What construct contains ``pos`` — "template", "wikitable", or None.

    An attribute residue is OURS only if it sits inside something we were
    supposed to CONSUME.  A `{{fine block|…|style=…}}` named argument is one we
    failed to take, so that leak is a producer bug — but ROME's
    `See Ranke iv.|width=7.5(2) 285` sits loose inside a `<ref>` with no
    enclosing construct at all, and MediaWiki has nothing to consume it either,
    so a Wikisource reader sees the same text.

    Without this the rule was "the text is in the source, therefore we leaked
    it", which convicts us of every stray attribute the transcription contains
    ([[feedback_source_is_the_only_excuse]]).
    """
    if pos < 0:
        return None
    masked = mask_non_template(src)[:pos]
    if len(re.findall(r"\{\{", masked)) > len(re.findall(r"\}\}", masked)):
        return "template"
    if (len(re.findall(r"^\{\|", masked, re.M))
            > len(re.findall(r"^\|\}", masked, re.M))):
        return "wikitable"
    return None


def probe(cat, snippet):
    """-> (source-form text to look for, (open, close) balance pair, leaked_close).

    A ``None`` probe with no pair means the fragment has no source form at all —
    it is ours by construction, and no lookup can change that.
    """
    if cat in ("marker", "sentinel"):
        return None, None, False
    if cat == "tag":
        m = _ESC_TAG.search(snippet)
        if not m:
            return None, None, False
        slash, name = m.group(1), m.group(2)
        # A VOID element has no closing tag, so any `</br>` is unmatched BY
        # DEFINITION and no count can say otherwise.  Pairing `<br` against
        # `</br` made CONGO FREE STATE's `<br/>treaty of</br/>cession.` look
        # balanced — one open, one close — and blamed us for a transcription typo
        # MediaWiki also shows literally.
        if slash and name.lower() in _VOID_ELEMENTS:
            return "<" + slash + name, _VOID, True
        return ("<" + slash + name,
                (r"<" + name + r"\b", r"</" + name + r"\b"), bool(slash))
    if cat == "template":
        m = _TEMPLATE_OPEN.search(snippet)
        # An ORPHAN close carries no name to look for, so only the source's brace
        # SURPLUS can speak to it.
        return (m.group(0) if m else None), _BRACES, (m is None)
    if cat == "attr":
        m = _ATTR.search(snippet)
        return (m.group(0) if m else None), _ATTR_ENCLOSURE, False
    if cat == "indent":
        # The rendered mark plus the words after it, which survive the render
        # unchanged and so pin the line in the source.
        tail = HTML_TAG_RE.sub("", snippet)
        m = _COLONS.search(tail)
        if not m:
            return None, None, False
        # Stop at the first `<`: the snippet window can cut a tag in half, and a
        # half tag is not text the source ever contained.
        after = html.unescape(tail[m.end():].split("<")[0]).strip()[:14]
        # A mark with NOTHING after it cannot be looked up — but it is not
        # "invented" either, which is what a None probe would claim.  It is a
        # mark the producer emitted without the content it was marking, and
        # saying exactly that is the finding.
        if not after:
            return "", None, False
        return m.group(0) + after, None, False
    return None, None, False


def classify(cat, snippet, src):
    """-> (verdict, why).  Total: every leak site gets one of the two verdicts."""
    found, pair, leaked_close = probe(cat, snippet)
    if found == "":
        return PRODUCER, cat + ": the mark was emitted with no content after it"
    if found is None and pair is None:
        return PRODUCER, cat + ": no source form exists — we invented it"
    if found is not None and found not in src:
        return PRODUCER, cat + ": `" + found + "` is not in the article's source at all"
    if pair is None:
        return PRODUCER, cat + ": `" + found + "` is in the source and ordinary — we leaked it"

    if pair is _ATTR_ENCLOSURE:
        where = encloses(src, src.find(found))
        if where is None:
            return SOURCE, (cat + ": `" + found + "` is loose in the source — no "
                            "template or table encloses it, so nothing was ever "
                            "going to consume it")
        return PRODUCER, (cat + ": `" + found + "` is an argument of a " + where +
                          " we failed to consume")

    if pair is _VOID:
        return SOURCE, (cat + ": `" + found + "` closes a VOID element — the "
                        "transcription wrote a close tag that cannot exist")

    if pair is _BRACES and found is not None:
        if _every_occurrence_closes(src, found):
            return PRODUCER, cat + ": `" + found + "` closes at every site — the leak is ours"
        return SOURCE, cat + ": `" + found + "` is UNCLOSED in the transcription"

    # No site to scan (an orphan close, or a tag).  The source excuses this leak
    # only if it carries the matching SURPLUS: a leaked close needs surplus
    # closes, a leaked open needs surplus opens.  Direction is the whole test —
    # an imbalance the wrong way round cannot have produced this fragment.
    o, c = pair
    masked = mask_non_template(src)
    surplus = len(re.findall(c, masked)) - len(re.findall(o, masked))
    name = "`" + (found or "{{ }}") + "`"
    if leaked_close and surplus > 0:
        return SOURCE, cat + ": the source has " + str(surplus) + " unmatched close(s) of " + name
    if not leaked_close and surplus < 0:
        return SOURCE, cat + ": the source has " + str(-surplus) + " unmatched open(s) of " + name
    return PRODUCER, (cat + ": the source has no unmatched " +
                      ("close" if leaked_close else "open") + " of " + name +
                      " to explain it")


def article_source(session, aid, _cache={}):
    """The raw wikitext of the pages this article sits on, corrections applied."""
    if aid not in _cache:
        a = session.get(Article, aid) if aid is not None else None
        if a is None:
            _cache[aid] = ""
        else:
            pages, _ = load_pages(a.volume, pages=range(a.page_start, a.page_end + 1))
            _cache[aid] = "\n".join(p.text for p in pages)
    return _cache[aid]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="stop after N leaking articles")
    args = ap.parse_args()

    session = SessionLocal()
    try:
        payloads, _ = load_corpus()
        verdicts = defaultdict(list)
        n_art = n_sites = no_article = 0
        for path, d in sorted(payloads.items()):
            leaks = find_leaks(d.get("rendered_html") or "")
            if not leaks:
                continue
            n_art += 1
            src = article_source(session, d.get("id"))
            if not src:
                no_article += 1
            for cat, snip in leaks:
                s = re.sub(r"\s+", " ", snip).strip()
                n_sites += 1
                verdict, why = classify(cat, s, src)
                verdicts[verdict].append(
                    (d.get("title", "")[:26], path.name, cat, why, s[:70]))
            if args.limit and n_art >= args.limit:
                break
    finally:
        session.close()

    # COVERAGE, stated: the classification is total, so these numbers must add up
    # and the report says so rather than leaving a reader to assume it.
    # THE VERDICTS ARE ONLY VALID IF BOTH SIDES ARE THE SAME VINTAGE.  The leak
    # comes from `rendered_html`; the excuse comes from the raw source WITH
    # corrections applied.  Write a correction and the source balances while the
    # render still carries the leak — so every fixed site silently flips from
    # SOURCE to PRODUCER and the tool blames us for what we just fixed.  That
    # happened the moment 29 corrections landed: 39 SOURCE became 10.  A net that
    # inverts its own answer without saying so is the failure this arc is about.
    corr = Path("data/corrections.json")
    newest = max((p.stat().st_mtime for p in list(payloads)[:2000]), default=0)
    if corr.exists() and corr.stat().st_mtime > newest:
        print("*" * 78)
        print("WARNING: data/corrections.json is NEWER than the rendered corpus.")
        print("  SOURCE verdicts are unreliable until a full rebuild: a corrected")
        print("  source now balances while rendered_html still carries the leak,")
        print("  so already-fixed sites report as PRODUCER.  Rebuild, then re-run.")
        print("*" * 78)
    print("articles scanned : %d" % len(payloads))
    print("leaking articles : %d" % n_art)
    print("leak sites       : %d   (%s)"
          % (n_sites, " + ".join("%d %s" % (len(v), k)
                                 for k, v in sorted(verdicts.items()))))
    if no_article:
        print("  WARNING: %d leaking article(s) have no DB row, so their source "
              "could not be read — classified against empty source." % no_article)
    for v in (PRODUCER, SOURCE):
        rows = verdicts.get(v) or []
        print("\n" + "=" * 78 + "\n%s: %d leak site(s)\n" % (v, len(rows)) + "=" * 78)
        for why, n in Counter(r[3] for r in rows).most_common():
            print("  [%3d] %s" % (n, why))
        for title, fn, cat, why, s in rows:
            print("    %-26s %-8s %r" % (title, cat, s))
    return 0


if __name__ == "__main__":
    sys.exit(main())
