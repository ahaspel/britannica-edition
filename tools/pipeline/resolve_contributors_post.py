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
import re
import sys
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
from britannica.pipeline.stages.extract_contributors import (
    _harvest_signature_contributors)

ART = Path("data/derived/articles")
SKIP = {"index.json", "contributors.json"}


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


def main() -> None:
    session = SessionLocal()
    try:
        register_stable_id_dedup(session.query(Article).all())
        arts = session.query(Article).filter(Article.article_type != "plate").all()
        sid_of = {a.id: stable_id(a) for a in arts}
        title_of = {a.id: a.title for a in arts}
        kind_index = json.loads(
            (ART.parent / "kind_index.json").read_text(encoding="utf-8"))
        kinds_of = lambda i: set(kind_index.get(sid_of.get(i, "") + ".json", []))

        # Exported bodies, keyed by article id.
        bodies: dict[int, str] = {}
        for fn in ART.glob("*.json"):
            if fn.name in SKIP:
                continue
            try:
                d = json.loads(fn.read_text(encoding="utf-8"))
            except Exception:
                continue
            if isinstance(d, dict) and "id" in d:
                bodies[d["id"]] = d.get("body", "")

        # ── 1. SIGNATURES ───────────────────────────────────────────────────
        session.query(ArticleContributor).delete()
        initials_map = {ci.initials: ci.contributor_id
                        for ci in session.query(ContributorInitials).all()}
        n_sig = 0
        for aid, body in bodies.items():
            for seq, cid in enumerate(
                    _harvest_signature_contributors(body, initials_map), start=1):
                session.add(ArticleContributor(
                    article_id=aid, contributor_id=cid, sequence=seq))
                n_sig += 1
        session.commit()

        # ── 2. FRONTMATTER (own session; appends, dedups) ───────────────────
        link_from_frontmatter(apply_mode=True)

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
        binds_by_article: dict[int, list[int]] = defaultdict(list)
        for ac in (session.query(ArticleContributor)
                   .order_by(ArticleContributor.sequence).all()):
            binds_by_article[ac.article_id].append(ac.contributor_id)

        contrib_map: dict[str, dict] = {}
        n_patched = 0
        for fn in ART.glob("*.json"):
            if fn.name in SKIP:
                continue
            try:
                d = json.loads(fn.read_text(encoding="utf-8"))
            except Exception:
                continue
            aid = d.get("id")
            cids = binds_by_article.get(aid, [])
            d["contributors"] = [
                {"initials": (all_inits.get(cid) or [""])[0],
                 "full_name": cred_of[cid].full_name,
                 "credentials": cred_of[cid].credentials,
                 "description": cred_of[cid].description}
                for cid in cids if cid in cred_of]
            fn.write_text(json.dumps(d, indent=2, ensure_ascii=False),
                          encoding="utf-8")
            n_patched += 1
            for cid in cids:
                c = cred_of.get(cid)
                if not c:
                    continue
                e = contrib_map.setdefault(c.full_name, {
                    "full_name": c.full_name,
                    "initials": ", ".join(all_inits.get(cid, [])),
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

        print(f"6b5 contributors: signatures={n_sig}, vol29 bound={n_v29}, "
              f"vol29 abstained={n_abstain}; patched {n_patched} JSONs; "
              f"{len(contrib_list)} contributors in roster")
    finally:
        session.close()


if __name__ == "__main__":
    main()
