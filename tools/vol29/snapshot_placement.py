"""snapshot_placement — capture, for every category, which node each article
seats on and what orphans, so a producer change to build_buckets can be diffed:
only the intended subdivisions should move, and the ~36k seated articles must
not shift.  Run before and after the change, then diff the two JSONs.

  uv run python tools/vol29/snapshot_placement.py <out.json>
"""
import sys
import json

sys.path.insert(0, "tools/vol29")
import populate_classified_toc as P

N = P._normalize


def main(out: str) -> None:
    resolve = P.build_resolver()
    content = P.load_segmented_content()
    idx, _ = P._C.merge()
    placements = []          # [cat, norm(target), path]
    orphans = []             # [cat, name, count]
    for cat in P.CATEGORIES:
        nodes = idx.get(cat, [])
        bks = P.build_buckets(cat, content[cat])
        orph, _ = P.pour_category(cat, nodes, bks, resolve)
        for o in orph:
            orphans.append([cat, o.get("name", "?"),
                            len(o.get("arts", [])) + len(o.get("pr", []))])

        def walk(n, path):
            for a in n.get("articles", []):
                placements.append(
                    [cat, N(a.get("target") or a.get("display") or ""), path])
            for c in n.get("children", []):
                walk(c, path + " > " + c.get("name", "?"))
        for s in nodes:
            walk(s, cat + " > " + s.get("name", "?"))

    json.dump({"placements": placements, "orphans": orphans},
              open(out, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"placements={len(placements)} "
          f"orphan_entries={sum(o[2] for o in orphans)} "
          f"orphan_buckets={len(orphans)} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
