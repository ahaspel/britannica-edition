import re
import sys
sys.stdout.reconfigure(encoding="utf-8")

from britannica.db.models import Article
from britannica.db.session import SessionLocal

s = SessionLocal()
articles = s.query(Article).filter(Article.article_type == "article").all()
lc = [a for a in articles if re.search(r"[a-z]", a.title)]
print(f"Total lowercase-title articles: {len(lc)}")

categories = {}
for a in lc:
    t = a.title
    if re.search(r"\([^)]*[a-z]", t):
        cat = "paren_lowercase"
    elif re.search(r"\[[^]]*[a-z]", t):
        cat = "bracket_lowercase"
    elif re.match(r"^Mc[A-Z]|^Mac[A-Z]|^De[A-Z]|^La[A-Z]|^Di[A-Z]|^Van [A-Z]|^O\u2019[A-Z]", t):
        cat = "name_prefix"
    else:
        cat = "other"
    categories.setdefault(cat, []).append((t, a.volume, a.page_start))

for cat, rows in sorted(categories.items(), key=lambda x: -len(x[1])):
    print(f"\n=== {cat} ({len(rows)}) ===")
    for t, v, p in rows[:15]:
        print(f"  vol{v} p{p}: {t}")

s.close()
