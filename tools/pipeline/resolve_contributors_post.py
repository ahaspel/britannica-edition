"""Phase 6b5: resolve ALL contributor attributions post-export.

One phase owns the whole contributor story, in confidence order, AFTER the kind
index (6b3) so the footprint can consult it:

  1. SIGNATURES  — the footer `(initials)` sign-offs harvested from each exported
     body (the source's own attribution; the authoritative anchor).
  2. FRONTMATTER — the per-volume contributor-table subject lists.
  3. FOOTPRINT   — each contributor's kind profile, from ONLY the two authoritative
     sources above (built here, before vol-29, so it is never circular).
  4. VOL-29      — the master-index credits, resolved by the KIND-VALIDATED matcher
     (vol29_kind_match): a credit's own disambiguator ∪ the contributor's footprint
     pick the right article; a kind-mismatched homonym is ABSTAINED, never bound.
  5. EMIT        — patch each article JSON's `contributors` + rebuild
     contributors.json from the final DB state.

Replaces the pre-export harvest / link_frontmatter / link_vol29 in assemble (the
export now writes empty `contributors`, filled here).  ([[project_resolver_consolidation]])
"""
import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, "src")
from britannica.contributors.link_frontmatter import link_from_frontmatter
from britannica.contributors.resolver import ContributorIndex
from britannica.contributors.vol29_index import parse_vol29_index
from britannica.contributors.vol29_kind_match import (
    candidate_ids, credit_expected_kinds, pick_article)
from britannica.db.models import (
    Article, ArticleContributor, Contributor, ContributorInitials)
from britannica.db.session import SessionLocal
from britannica.export.article_json import (
    _resolve_bio_articles, _safe_filename, register_stable_id_dedup, stable_id)
from britannica.contributors.author_links import (
    accrete_author_link_contributors, harvest_author_links)
from britannica.pipeline.stages.extract_contributors import _normalize_initials

ART = Path("data/derived/articles")
# Deferred [[Author:]] render marker: the walk emits «AL:name|display» neutrally
# and 6b4 resolves it against the FINISHED roster ([[project_roster_from_author_links]]).
_AL_RE = re.compile(r"«AL:([^|»]*)\|(.*?)«/AL»", re.DOTALL)

# A contributor's name string flattens THREE attributes (the user's decomposition):
# the NAME PROPER, an honorific/TITLE prefix, and a (DATE) disambiguator.  The
# step-5 mode must vote on ONLY the name proper — the title is kept from the
# authoritative front-matter form (footers casually drop it, so a mode would wrongly
# delete `Sir`/`Rev.`) and dates are stripped entirely (none wanted in the index).
_TITLE_RE = re.compile(
    r"^((?:(?:The\s+)?(?:Right\s+|Rt\.?\s+)?"
    r"(?:Hon|Rev|Revd|Sir|Dame|Dr|Prof|Professor|Mrs|Miss|Captain|Capt|"
    r"Lieutenant-General|Lieut\.?-Gen(?:eral)?|Major-General|Major|"
    r"Lieutenant-Colonel|Lieut\.?-Colonel|Lieutenant|Lieut|Colonel|Col|"
    r"Brigadier|Brig|General|Surgeon-General|Surgeon-Major|Surgeon|"
    r"Commander|Commodore|Rear-Admiral|Vice-Admiral|Admiral|"
    r"Monseigneur|Monsignor|Mgr|Cardinal|Archbishop|Bishop|Archdeacon|Canon|"
    r"Prince|Princess|Baron|Baroness|Countess|Count|Lord|Lady)\.?\s+)+)",
    re.IGNORECASE)
_NAME_DATE_RE = re.compile(r"\s*\(\s*(?:b\.\s*|d\.\s*|c\.\s*)?\d{3,4}[^)]*\)")


def _name_fold(s: str) -> str:
    """Case- and diacritic-insensitive key for a name-proper, so `M'Lennan` /
    `M'lennan` / `M'LENNAN` and `Léon` / `Leon` count as ONE spelling.  The vote
    picks the winning spelling by this key; the emit then restores real casing
    and accents.  Punctuation and spacing are dropped so only letters vote."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def _display_name(full_name: str) -> str:
    name = re.sub(r"\s*\([^)]*\)", "", full_name).strip().rstrip(",").strip()
    head, _, suffix = name.partition(",")
    parts = head.strip().rsplit(None, 1)
    rearranged = f"{parts[1]}, {parts[0]}" if len(parts) == 2 else head.strip()
    return f"{rearranged}, {suffix.strip()}" if suffix.strip() else rearranged


def _sort_key(full_name: str) -> str:
    name = re.sub(r"\s*\([^)]*\)", "", full_name).strip().rstrip(",").strip()
    head = name.partition(",")[0].strip()
    return head.rsplit(None, 1)[-1].lower() if head else ""


def bind_contributors(session, payloads: dict) -> bool:
    """Bind every contributor and patch each payload's ``contributors`` — IN
    MEMORY (the caller owns load/write), so the merged post-export pass applies
    it without a corpus round-trip of its own.  Writes ``contributors.json``
    (it is the sole writer of the roster).  Returns False when ``STEP5_DRYRUN``
    short-circuited it, so the caller writes nothing.

    NOTE the caller must have replayed ``register_stable_id_dedup`` first — every
    ``_safe_filename`` below depends on it."""
    arts = session.query(Article).filter(Article.article_type != "plate").all()
    sid_of = {a.id: stable_id(a) for a in arts}
    title_of = {a.id: a.title for a in arts}
    kind_index = json.loads(
        (ART.parent / "kind_index.json").read_text(encoding="utf-8"))
    kinds_of = lambda i: set(kind_index.get(sid_of.get(i, "") + ".json", []))

    # ── 0. ROSTER (relocated from Phase 1b/1c) — build the roster from the
    #    three UNAMBIGUOUS sources HERE, so it is COMPLETE before the ambiguous
    #    [[Author:]] links are resolved (for binding AND for the deferred
    #    render).  Truncate first so a standalone re-run rebuilds cleanly.
    #    ([[project_roster_from_author_links]])
    from build_contributor_table import (
        _clean_name, backfill_bios, build_contributor_table)
    import link_vol29_contributors
    session.query(ArticleContributor).delete()
    session.query(ContributorInitials).delete()
    session.query(Contributor).delete()
    session.commit()
    fm_entries = build_contributor_table()         # per-volume front-matter tables
    _saved_argv = sys.argv
    sys.argv = ["link_vol29_contributors", "--apply"]
    try:
        link_vol29_contributors.main()             # vol-29 master index
    finally:
        sys.argv = _saved_argv
    backfill_bios()                                # per-volume contributor bios
    session.expire_all()
    # Footer signers with no front-matter/vol-29 entry (Woolhouse) join here;
    # [[Author:]] is AMBIGUOUS and NEVER mints a contributor — it only expands
    # existing article lists.
    seed_inits: dict[int, list] = defaultdict(list)
    for ci in session.query(ContributorInitials).all():
        seed_inits[ci.contributor_id].append(ci.initials)
    seed_idx = ContributorIndex((c.id, c.full_name, seed_inits.get(c.id, []))
                                for c in session.query(Contributor).all())
    n_new = accrete_author_link_contributors(session, seed_idx)

    # ── 1. AUTHOR LINKS ─────────────────────────────────────────────────
    # Each article's own author-links, read from its segment_text: the footer
    # template, the [[Author:Name|Init]] signature wikilink, and the bare
    # {{EB1911 TAs}} shortcut.  The first two carry NAME + initials, so we
    # resolve by the COMBINATION (name-first) and a transcription slip in the
    # initials cannot misclassify (SCHUBERT's "W. H. H." NAMES Hadow, not
    # Howell).  Authoritative for the great majority of binds and drops NO
    # real author link; name-less bare parentheticals are NOT harvested here —
    # they are reserved for step-4 disambiguation.
    # ([[feedback_accrete_first_canonicalize_last]])
    session.query(ArticleContributor).delete()
    al_inits: dict[int, list] = defaultdict(list)
    for ci in session.query(ContributorInitials).all():
        al_inits[ci.contributor_id].append(ci.initials)
    al_cidx = ContributorIndex((c.id, c.full_name, al_inits.get(c.id, []))
                               for c in session.query(Contributor).all())
    binds, _al_unresolved, footer_votes = harvest_author_links(session, al_cidx)
    for aid, cid, seq in binds:
        session.add(ArticleContributor(
            article_id=aid, contributor_id=cid, sequence=seq))
    n_sig = len(binds)
    session.commit()

    # ── STEP 5 vote banks.  The NAME is whatever EB carries in its INDICES —
    #    the front-matter contributor tables (fed before emit) and the vol-29
    #    master index (fed in step 4).  A footer's/author-link's NAME field is a
    #    WIKISOURCE author-page link (`{{…footer…|Robert Crewe-Milnes|C.}}`), i.e.
    #    how Wikipedia names them, NOT how EB cites them — so it votes on the
    #    SIGNATURE (initials) only, never the name.  Canonical = the MODE of the
    #    index citations, which agree with each other; the initials are EB's own
    #    byline mark.  ([[feedback_accrete_first_canonicalize_last]])
    name_votes: dict[int, Counter] = defaultdict(Counter)
    init_votes: dict[int, Counter] = defaultdict(Counter)

    def _strip_date(s: str) -> str:
        return _NAME_DATE_RE.sub("", s).strip()

    def _split_title(s: str) -> tuple[str, str]:
        m = _TITLE_RE.match(s)
        return (m.group(1).strip(), s[m.end():].strip()) if m else ("", s)

    def _name_proper(raw: str) -> str:
        """The name-proper axis: trailing degrees off (already → credentials
        via _clean_name), dates stripped, leading title removed — so the mode
        votes on the name ITSELF, not its title/date decoration."""
        core = _clean_name(raw)[0]
        return _split_title(_strip_date(core))[1].strip()

    def _vote(cid: int, raw_name: str | None, raw_init: str | None) -> None:
        if raw_name:
            nm = _name_proper(raw_name)
            if nm:
                name_votes[cid][nm] += 1
        if raw_init:
            iv = _normalize_initials(raw_init)
            if iv:
                init_votes[cid][iv] += 1

    for _cid, _obs in footer_votes.items():
        for _nm, _it in _obs:      # footers/author-links: SIGNATURE only, no name
            if _it:
                _iv = _normalize_initials(_it)
                if _iv:
                    init_votes[_cid][_iv] += 1

    # ── 2. FRONTMATTER (own session; appends, dedups) ───────────────────
    link_from_frontmatter(apply_mode=True, kind_of=kinds_of)

    # ── 3. FOOTPRINTS — from the authoritative binds ONLY (all that exist
    #       right now, since vol-29 has not run) ──────────────────────────
    footprints: dict[int, Counter] = defaultdict(Counter)
    for ac in session.query(ArticleContributor).all():
        for k in kinds_of(ac.article_id):
            footprints[ac.contributor_id][k] += 1

    # ── 4. VOL-29 — kind-validated ──────────────────────────────────────
    title_map: dict[str, list[int]] = defaultdict(list)
    comma_index: dict[str, list[int]] = defaultdict(list)
    given_of: dict[int, str] = {}
    from britannica.contributors.link_vol29_articles import _normalize_vol29_title
    for a in arts:
        title_map[_normalize_vol29_title(a.title)].append(a.id)
        if "," in a.title:
            head, _, tail = a.title.partition(",")
            comma_index[head.strip().upper()].append(a.id)
            given_of[a.id] = tail.strip()

    inits = defaultdict(list)
    for ci in session.query(ContributorInitials).all():
        inits[ci.contributor_id].append(ci.initials)
    cidx = ContributorIndex((c.id, c.full_name, inits.get(c.id, []))
                            for c in session.query(Contributor).all())

    n_v29 = n_abstain = 0
    for entry in parse_vol29_index():
        if not entry.articles:
            continue
        cid = cidx.resolve(name=entry.full_name, initials=entry.initials)
        if cid is None:
            continue
        _vote(cid, entry.full_name, entry.initials)
        fp = footprints.get(cid, Counter())
        for credit in entry.articles:
            cands = candidate_ids(credit, title_map, comma_index,
                                  lambda i: given_of.get(i, ""))
            target = pick_article(cands, kinds_of,
                                  credit_expected_kinds(credit), fp)
            if target is None:
                n_abstain += 1
                continue
            exists = (session.query(ArticleContributor)
                      .filter(ArticleContributor.article_id == target,
                              ArticleContributor.contributor_id == cid).first())
            if exists:
                continue
            session.add(ArticleContributor(
                article_id=target, contributor_id=cid, sequence=99))
            n_v29 += 1
    session.commit()

    # ── 5. EMIT — patch JSONs + rebuild contributors.json ───────────────
    cred_of = {c.id: c for c in session.query(Contributor).all()}
    all_inits = defaultdict(list)
    for ci in session.query(ContributorInitials).all():
        all_inits[ci.contributor_id].append(ci.initials)

    # Front-matter spellings vote too — one per occurrence, attributed to the
    # final roster via the same index vol-29 used.
    for _fi, _fn, _fd in fm_entries:
        _fc = cidx.resolve(name=_clean_name(_fn)[0],
                           initials=_normalize_initials(_fi))
        if _fc is not None:
            _vote(_fc, _fn, _fi)

    def _canon_name(cid: int) -> str:
        """Display = the authoritative TITLE prefix (date dropped) + the winning
        name-proper spelling from EB's index votes.

        The winner is chosen by a CASE+DIACRITIC-FOLDED key (_name_fold), so an
        all-caps or de-accented index entry can't split the vote; a genuine tie
        is broken toward the DB (front-matter) spelling.  For casing/accents we
        emit the DB form when its spelling matches the winner (already correctly
        cased — `M'Lennan`, `Léon`), else the best-cased raw variant in the
        winning group.  Robertson still flips: his DB spelling folds to
        `roberston`, not the winning `robertson`."""
        title, _ = _split_title(_strip_date(cred_of[cid].full_name))
        db_core = _name_proper(cred_of[cid].full_name)
        v = name_votes.get(cid)
        if not v:
            return f"{title} {db_core}".strip() if title else db_core
        db_fold = _name_fold(db_core)
        groups: dict[str, Counter] = defaultdict(Counter)
        for raw_core, n in v.items():
            groups[_name_fold(raw_core)][raw_core] += n
        win = max(groups, key=lambda k: (sum(groups[k].values()),
                                         k == db_fold,   # tie → trust the DB spelling
                                         max(len(x) for x in groups[k]), k))
        if win == db_fold:
            core = db_core
        else:
            core = max(groups[win].items(),
                       key=lambda kv: (any(c.islower() for c in kv[0]),
                                       sum(ord(c) > 127 for c in kv[0]),
                                       kv[1], len(kv[0]), kv[0]))[0]
        return f"{title} {core}".strip() if title else core

    def _canon_init(cid: int) -> str:
        """The primary signature: the MODE of the observed initials (tie →
        shortest, then alphabetical); falls back to the first stored form."""
        v = init_votes.get(cid)
        if v:
            return max(v.items(), key=lambda kv: (kv[1], -len(kv[0]), kv[0]))[0]
        return (all_inits.get(cid) or [""])[0]

    # Resolve the deferred [[Author:]] render markers now that the roster is
    # FINAL: «AL:name|disp» → the bare-initials signoff when `disp` is a known
    # contributor's initials, else an «LN» xref for 6b5 to bake.  Consistent
    # with the binding gate (a signature's display IS a known contributor's
    # initials); no «AL» survives past here.  ([[project_roster_from_author_links]])
    known_inits = {i for inits in all_inits.values() for i in inits}

    def _resolve_author_markers(text: str) -> str:
        def _repl(m):
            name, disp = m.group(1), m.group(2)
            if _normalize_initials(disp.strip("() ")) in known_inits:
                return disp
            # NOT a signoff → a reference to a PERSON.  Leave the «AL» standing:
            # rewriting it to «LN» here erased the one fact 6b5 needs, and the
            # article ladder then matched these given-name-first citations
            # against surname-first EB titles (JOHN VENN → McADAM, JOHN LOUDON).
            # 6b5 resolves it on the person tier and bakes/strips it there, so
            # no «AL» survives the pipeline — the invariant just moves one phase.
            return m.group(0)
        return _AL_RE.sub(_repl, text)

    binds_by_article: dict[int, list[int]] = defaultdict(list)
    for ac in (session.query(ArticleContributor)
               .order_by(ArticleContributor.sequence).all()):
        binds_by_article[ac.article_id].append(ac.contributor_id)

    # STEP 5 diagnostic — what the mode changes vs. the build-time name, and
    # the bound roster size.  STEP5_DRYRUN prints this and writes nothing.
    bound_cids = {cid for cids in binds_by_article.values() for cid in cids}
    _changed = [(cred_of[cid].full_name, _canon_name(cid))
                for cid in bound_cids
                if cid in cred_of and _canon_name(cid) != cred_of[cid].full_name]
    print(f"[step5] roster(bound)={len(bound_cids)}  "
          f"canonical-name changes={len(_changed)}")
    for _old, _new in sorted(_changed):
        print(f"   {_old!r}  ->  {_new!r}")
    _watch = re.compile(
        r"robertson|croom|webber|phillp|philp|crewe|crewe-milnes|cyres|northcote|"
        r"wilhelm|pitcher|kendrick|car[oö]e|bhowna", re.I)
    for _wc in bound_cids:
        if _wc in cred_of and _watch.search(
                f"{cred_of[_wc].full_name} {_canon_name(_wc)}"):
            print(f"[step5:watch] db={cred_of[_wc].full_name!r} "
                  f"canon={_canon_name(_wc)!r} "
                  f"votes={dict(name_votes.get(_wc, {}))}")
    if os.environ.get("STEP5_DRYRUN"):
        print("[step5] DRY RUN — no JSONs written")
        return False

    contrib_map: dict[int, dict] = {}
    n_patched = 0
    for d in payloads.values():
        aid = d.get("id")
        d["body"] = _resolve_author_markers(d.get("body", ""))
        cids = binds_by_article.get(aid, [])
        d["contributors"] = [
            {"initials": _canon_init(cid),
             "full_name": _canon_name(cid),
             "credentials": cred_of[cid].credentials,
             "description": cred_of[cid].description}
            for cid in cids if cid in cred_of]
        n_patched += 1
        for cid in cids:
            c = cred_of.get(cid)
            if not c:
                continue
            e = contrib_map.setdefault(cid, {
                "full_name": _canon_name(cid),
                "initials": _canon_init(cid),
                "credentials": c.credentials or "",
                "description": c.description or "", "articles": []})
            if aid is not None:
                a = next((x for x in arts if x.id == aid), None)
                if a:
                    e["articles"].append({
                        "id": aid, "stable_id": sid_of[aid],
                        "title": a.title,
                        "filename": _safe_filename(a, a.title)})

    for e in contrib_map.values():
        e["display_name"] = _display_name(e["full_name"])
    _resolve_bio_articles(session, contrib_map)
    contrib_list = sorted(contrib_map.values(),
                          key=lambda e: _sort_key(e["full_name"]))
    (ART / "contributors.json").write_text(
        json.dumps(contrib_list, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"contributors: signatures={n_sig}, vol29 bound={n_v29}, "
          f"vol29 abstained={n_abstain}; patched {n_patched} JSONs; "
          f"{len(contrib_list)} contributors in roster")
    return True


def main() -> None:
    """Standalone: load the corpus, bind contributors, write back."""
    from britannica.export.corpus import load_corpus, write_corpus
    session = SessionLocal()
    try:
        register_stable_id_dedup(session.query(Article).all())
        payloads, _ = load_corpus(ART)
        if bind_contributors(session, payloads):
            write_corpus(payloads)
    finally:
        session.close()


if __name__ == "__main__":
    main()
