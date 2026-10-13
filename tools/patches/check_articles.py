"""After a rebuild: every article on a patched page, as the site renders it
(rendered_html), searched for markup printed as text — a literal '' or ''',
an unparsed {{ or }} or [[ — outside formulas.  Each instance is listed with
its context and whether a patch's new text holds that context (a patch's
fault) or not (Wikisource's own unpatched text).  A patch's fault fails it.
Usage: check_articles.py  (book root, after a rebuild)"""
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
from wikikit.export.corpus import load_corpus

PATCHES = {k: v for k, v in json.loads(Path("data/patches.json").read_text(encoding="utf-8")).items()
           if not k.startswith("_")}
LEAK = re.compile(r"''+|\{\{|\}\}|\[\[|\]\]")
TEX = re.compile(r'<span class="tex-math"[^>]*>[\s\S]*?</span>')


def plain(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s)))


def main():
    corpus, _ = load_corpus()
    t, faults = Counter(), []
    for a in corpus.values():
        v, p0, p1 = a.get("volume"), a.get("ws_page_start"), a.get("ws_page_end") or a.get("ws_page_start")
        if p0 is None:
            continue
        ps = [x for q in range(p0, p1 + 1) for x in PATCHES.get(f"{v}:{q}", [])]
        if not ps:
            continue
        t["articles"] += 1
        text = plain(TEX.sub(" ", a.get("rendered_html") or ""))
        news = " ".join(plain(x["new"]) for x in ps)
        for m in LEAK.finditer(text):
            ctx = text[max(0, m.start() - 30):m.end() + 30]
            near = text[max(0, m.start() - 12):m.start()].strip()[-10:]
            ours = bool(near) and near in news
            t["patch's text" if ours else "Wikisource's own text"] += 1
            if ours:
                faults.append((a["title"], ctx))
    print(dict(t))
    for title, ctx in faults:
        print(f"  PATCH FAULT {title}: …{ctx}…")
    sys.exit(1 if faults else 0)


if __name__ == "__main__":
    main()
