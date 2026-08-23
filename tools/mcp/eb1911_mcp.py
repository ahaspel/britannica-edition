"""An MCP server over the 1911 Encyclopaedia Britannica — the local spike.

    uv run --with mcp python tools/mcp/eb1911_mcp.py        # stdio, for a client
    uv run --with mcp python tools/mcp/eb1911_mcp.py --self-test

WHY STDIO FIRST.  A hosted, metered API is mostly commercial plumbing (auth,
quotas, Stripe, uptime) wrapped around a tool layer.  The plumbing is cheap and
the tool layer is the part that decides whether anyone wants it, so the tool
layer gets built and USED first, locally, with none of the plumbing.  The same
tool bodies serve `transport="streamable-http"` later without change.

IT READS THE DOWNLOAD BUNDLE, NOT THE INTERNAL CORPUS.  `data/derived/download/`
is the PUBLISHED contract — the same bytes anyone can download — so the API
cannot drift from what the corpus bundle says, and the server never depends on
an internal shape this project changes freely.  ([[project_tei_export]] makes the
same argument for the TEI edition being generated from the marker stream rather
than from our own HTML.)

THE CONTRACT IS `stable_id` AND NOTHING ELSE.  Not titles (`VILLIERS` is two
different men), not section slugs (they derive from heading text, which changed
twice this month).  `stable_id` is title-independent by construction and has
survived every refactor: it is the only identifier safe to freeze in a public
interface.

WHAT IS DELIBERATELY MISSING.  Full-text search over 40 million words belongs in
Meilisearch, which the site already runs; scanning the bundle per query would be
dishonest about latency.  This spike searches TITLES and topics, and says so.
"""
from __future__ import annotations

import json
import re
import sys
import collections
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
# The citation format has one owner — `util.strings.page_range` — shared with
# the site renderer and the TEI writer.  A second spelling here is how an
# en-dash drifts to a hyphen in one output and nobody notices.
from britannica.util.strings import page_range  # noqa: E402
BUNDLE = ROOT / "data" / "derived" / "download"
SITE = "https://britannica11.org"


class Corpus:
    """The bundle, indexed for lookup — built once at start-up.

    An OFFSET index rather than the records themselves: `articles.jsonl` carries
    every article's full Markdown, and holding all of it resident to answer one
    lookup is the kind of thing that is fine on a laptop and embarrassing on a
    server.  Seek and read the one line instead.
    """

    def __init__(self, bundle: Path = BUNDLE):
        self.bundle = bundle
        self.offsets: dict[str, tuple[int, int]] = {}
        self.titles: list[tuple[str, str]] = []          # (title, id)
        self.by_topic: dict[str, list[str]] = defaultdict(list)
        self.out_refs: dict[str, list[str]] = defaultdict(list)
        self.in_refs: dict[str, list[str]] = defaultdict(list)
        self.contributors: list[dict] = []
        self._load()

    def _load(self) -> None:
        art = self.bundle / "articles.jsonl"
        if not art.is_file():
            raise SystemExit(
                f"no bundle at {art} — run:  uv run python -m britannica.export.download")
        with art.open("rb") as f:
            pos = 0
            for line in f:
                rec = json.loads(line)
                aid = rec.get("id")
                if aid:
                    self.offsets[aid] = (pos, len(line))
                    self.titles.append(((rec.get("title") or ""), aid))
                    for cat in rec.get("categories") or []:
                        self.by_topic[str(cat).lower()].append(aid)
                pos += len(line)

        edges = self.bundle / "xref_edges.jsonl"
        if edges.is_file():
            with edges.open(encoding="utf-8") as f:
                for line in f:
                    e = json.loads(line)
                    a, b = e.get("from"), e.get("to")
                    if a and b:
                        self.out_refs[a].append(b)
                        self.in_refs[b].append(a)          # the inbound graph

        roster = self.bundle / "contributors.json"
        if roster.is_file():
            self.contributors = json.loads(roster.read_text(encoding="utf-8"))

    def record(self, stable_id: str) -> dict | None:
        loc = self.offsets.get(stable_id)
        if not loc:
            return None
        with (self.bundle / "articles.jsonl").open("rb") as f:
            f.seek(loc[0])
            return json.loads(f.read(loc[1]))

    def title_of(self, stable_id: str) -> str:
        rec = self.record(stable_id)
        return (rec or {}).get("title") or stable_id


def _no_article(stable_id: str) -> dict:
    return {"error": f"no article with id {stable_id!r}"}


_MD_HEAD = re.compile(r"^(#{2,3})\s*(.+?)\s*$", re.M)


def _outline(md: str) -> list[dict]:
    """The article's own headings, with the extent of each.

    Read off the MARKDOWN, not the record's `sections` list: the two differ (84
    vs 80 in AFRICA, because an «ANCHOR» is a link target and emits no heading),
    and the thing being sliced is the markdown, so the markdown is what must be
    parsed.  Deriving the offsets from a different list is how a slice silently
    starts in the wrong place.
    """
    heads = list(_MD_HEAD.finditer(md))
    out = []
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(md)
        body = md[m.end():end]
        out.append({"index": i, "level": len(m.group(1)) - 1,
                    "title": m.group(2), "words": len(body.split()),
                    "_start": m.start(), "_end": end})
    return out

def _cite(rec: dict) -> dict:
    """Every response carries its citation.  An agent that cannot say WHERE a
    claim came from is not usefully grounded, and the whole argument for this
    corpus over a scrape is that each article has a permanent address and a
    printed page behind it."""
    pages = page_range(rec.get("page_start"), rec.get("page_end"))
    return {
        "id": rec.get("id"),
        "title": rec.get("title"),
        "url": rec.get("url") or f"{SITE}/article/{rec.get('id')}",
        "citation": (f"“{rec.get('title')}”, Encyclopædia Britannica, 11th ed., "
                     f"vol. {rec.get('volume')}, {pages} (Cambridge, 1911)"),
        "volume": rec.get("volume"),
        "pages": pages,
        "words": rec.get("word_count"),
    }


def build_server(corpus: Corpus):
    from mcp.server.mcpserver import MCPServer

    server = MCPServer(name="eb1911")

    @server.tool()
    def search_articles(query: str, limit: int = 10, topic: str | None = None) -> list[dict]:
        """Find articles by TITLE in the 1911 Encyclopaedia Britannica.

        Titles only in this build — full-text search over the 40-million-word
        corpus is a separate index and is not wired here.  Optionally restrict
        to a topic from the edition's own subject taxonomy.
        """
        q = (query or "").strip().lower()
        if not q:
            return []
        allowed = set(corpus.by_topic.get((topic or "").lower(), [])) if topic else None
        hits = []
        for title, aid in corpus.titles:
            if allowed is not None and aid not in allowed:
                continue
            t = title.lower()
            if t == q:
                rank = 0
            elif t.startswith(q):
                rank = 1
            elif q in t:
                rank = 2
            else:
                continue
            hits.append((rank, len(title), title, aid))
        hits.sort()
        return [{"id": aid, "title": title, "url": f"{SITE}/article/{aid}"}
                for _, _, title, aid in hits[:max(1, min(limit, 50))]]

    @server.tool()
    def search_full_text(query: str, limit: int = 15) -> dict:
        """Find articles whose TEXT contains a phrase — not just their titles.

        Use this for "which articles mention X". Results are ranked by how often
        the phrase occurs, with the article's own title and citation.

        A MISSING TOOL DOES NOT PRODUCE "I CANNOT" — it produces the worst
        available workaround.  Without this, answering "which articles mention
        Hannibal" meant enumerating 37,226 files on disk, which hangs; the tool
        scans ONE file instead.
        """
        q = (query or "").strip()
        if len(q) < 3:
            return {"error": "query must be at least 3 characters"}
        needle = q.lower().encode("utf-8")
        # LEADING boundary only.  A trailing one looks tidy and is wrong: it
        # silently dropped 19 of 166 articles for "Hannibal", every one of which
        # mentions him as "the Hannibalic War" (32 occurrences), plus Hannibalis,
        # Hannibalicum, Hannibals, Hannibalianus.  A reader asking which articles
        # mention Hannibal wants those.  The cost is that a short query can catch
        # an unrelated longer word, so the matched FORMS are reported back rather
        # than left as an invisible judgement the caller cannot audit.
        pat = re.compile(r"(?<!\w)" + re.escape(q) + r"\w*", re.I)
        hits = []
        forms: collections.Counter = collections.Counter()
        # Byte pre-filter before parsing: most lines do not contain the phrase,
        # and json.loads on all 37,225 of them is the whole cost.
        with (corpus.bundle / "articles.jsonl").open("rb") as f:
            for raw in f:
                if needle not in raw.lower():
                    continue
                rec = json.loads(raw)
                found = pat.findall(rec.get("markdown") or "")
                if found:
                    hits.append((len(found), rec))
                    forms.update(found)
        hits.sort(key=lambda h: (-h[0], h[1].get("title") or ""))
        top = hits[:max(1, min(limit, 50))]
        return {
            "query": q,
            "articles_matching": len(hits),
            "total_mentions": sum(n for n, _ in hits),
            "forms_matched": dict(forms.most_common(8)),
            "results": [{"id": r.get("id"), "title": r.get("title"),
                         "mentions": n, "words": r.get("word_count"),
                         "url": r.get("url")} for n, r in top],
        }

    @server.tool()
    def article_outline(stable_id: str) -> dict:
        """The article's sections, with the size of each — read this BEFORE
        fetching a long article.

        Some articles are very large (AFRICA is 54,916 words), and pulling one
        whole to answer a question about one part of it wastes most of what it
        returns.  This is the cheap way to see what is in an article and choose.
        """
        rec = corpus.record(stable_id)
        if not rec:
            return _no_article(stable_id)
        secs = _outline(rec.get("markdown") or "")
        out = _cite(rec)
        out["sections"] = [{k: v for k, v in s.items() if not k.startswith("_")}
                           for s in secs]
        return out

    @server.tool()
    def get_article(stable_id: str, include_text: bool = True,
                    section: str | None = None) -> dict:
        """Retrieve one article by its stable id, with its citation.

        The stable id is the article's permanent address — the tail of
        https://britannica11.org/article/<id> — and is the only identifier this
        interface accepts, because titles are ambiguous and section slugs move.
        """
        rec = corpus.record(stable_id)
        if not rec:
            return _no_article(stable_id)
        out = _cite(rec)
        out["contributors"] = rec.get("contributors") or []
        out["sections"] = [s.get("title") for s in (rec.get("sections") or [])]
        out["topics"] = rec.get("categories") or []
        md = rec.get("markdown") or ""
        if section:
            # By INDEX or by title.  Index is what `article_outline` just
            # returned and is unambiguous; a title is what a person types.
            # Deliberately NOT the section slug — slugs derive from heading text
            # and move when a heading is corrected, so they are fine as a
            # convenience and wrong as an interface.
            secs = _outline(md)
            hit = None
            if section.isdigit():
                hit = next((s for s in secs if s["index"] == int(section)), None)
            if hit is None:
                q = section.strip().lower()
                hit = (next((s for s in secs if s["title"].lower() == q), None)
                       or next((s for s in secs if q in s["title"].lower()), None))
            if hit is None:
                return {"error": f"no section {section!r} in {stable_id}",
                        "sections": [s["title"] for s in secs]}
            out["section"] = hit["title"]
            out["text"] = md[hit["_start"]:hit["_end"]]
            out["words"] = hit["words"]
            return out
        if include_text:
            out["text"] = md
            out["hint"] = (
                "This article is long; call article_outline first and fetch one "
                "section." if len(md.split()) > 8000 else None)
        return out

    @server.tool()
    def cross_references(stable_id: str, limit: int = 40) -> dict:
        """What this article points to, AND what points at it.

        The inbound direction is the part that is hard to get anywhere else: it
        answers "what did the 1911 edition consider relevant to this subject",
        which is a different and often better question than what the article
        itself cites.
        """
        if stable_id not in corpus.offsets:
            return _no_article(stable_id)
        out = corpus.out_refs.get(stable_id, [])[:limit]
        inn = corpus.in_refs.get(stable_id, [])[:limit]
        return {
            "id": stable_id,
            "title": corpus.title_of(stable_id),
            "references_out": [{"id": i, "title": corpus.title_of(i)} for i in out],
            "referenced_by": [{"id": i, "title": corpus.title_of(i)} for i in inn],
            "counts": {"out": len(corpus.out_refs.get(stable_id, [])),
                       "in": len(corpus.in_refs.get(stable_id, []))},
        }

    @server.tool()
    def find_contributor(name: str, limit: int = 10) -> list[dict]:
        """Look up a contributor and everything they signed.

        EB1911 attributes by initials; this edition resolves those signatures to
        people, with credentials and — where the encyclopaedia has one — their own
        biographical article.
        """
        q = (name or "").strip().lower()
        out = []
        for c in corpus.contributors:
            hay = f"{c.get('name') or ''} {c.get('initials') or ''}".lower()
            if q and q not in hay:
                continue
            out.append({
                "name": c.get("name"),
                "initials": c.get("initials"),
                "credentials": c.get("credentials"),
                "articles": [{"id": a} for a in (c.get("articles") or [])[:limit]],
                "article_count": len(c.get("articles") or []),
            })
            if len(out) >= limit:
                break
        return out

    @server.tool()
    def browse_topic(topic: str, limit: int = 25) -> dict:
        """List articles under a subject from the edition's own taxonomy.

        The topic index is reproduced from the 1911 classification, not inferred:
        it is what the encyclopaedia's own editors considered the subject to be.
        """
        key = (topic or "").strip().lower().strip("/")
        if not key:
            return {"error": "no topic given",
                    "roots": sorted({t.split("/")[0] for t in corpus.by_topic})}
        # TOPICS ARE PATHS, not labels: the 1911 classification is a hierarchy
        # ("biology/zoology/natural-history/birds"), so a bare "zoology" must
        # match a SEGMENT, and a path prefix must match its whole subtree.  The
        # spike's first version compared whole strings and answered "no topic
        # 'Zoology'" while holding 378 of them.
        exact = corpus.by_topic.get(key)
        if exact:
            paths, ids = [key], list(exact)
        else:
            paths = sorted(t for t in corpus.by_topic
                           if t == key or t.startswith(key + "/")
                           or key in t.split("/"))
            ids = [i for t in paths for i in corpus.by_topic[t]]
        if not ids:
            near = sorted({t for t in corpus.by_topic if key in t})[:12]
            return {"error": f"no topic {topic!r}", "did_you_mean": near}
        seen, uniq = set(), []
        for i in ids:
            if i not in seen:
                seen.add(i)
                uniq.append(i)
        return {"topic": topic, "matched_paths": paths[:12], "count": len(uniq),
                "articles": [{"id": i, "title": corpus.title_of(i),
                              "url": f"{SITE}/article/{i}"} for i in uniq[:limit]]}

    return server


def self_test(corpus: Corpus) -> int:
    """Exercise every tool body without a client — the spike's own smoke test."""
    server = build_server(corpus)
    tools = {t.name: t for t in _tools_of(server)}
    print(f"  tools registered: {', '.join(sorted(tools))}")
    print(f"  articles indexed : {len(corpus.offsets):,}")
    print(f"  topics           : {len(corpus.by_topic):,}")
    print(f"  xref edges       : {sum(len(v) for v in corpus.out_refs.values()):,}")
    print(f"  contributors     : {len(corpus.contributors):,}")
    return 0


def _tools_of(server):
    """The registered tools, via the server's own listing."""
    import anyio
    return anyio.run(server.list_tools)


if __name__ == "__main__":
    corpus = Corpus()
    if "--self-test" in sys.argv[1:]:
        sys.stdout.reconfigure(encoding="utf-8")
        raise SystemExit(self_test(corpus))
    build_server(corpus).run(transport="stdio")
