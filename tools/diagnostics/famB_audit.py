"""Fast family-B (block-wrapper) strip-leak audit — parallel, prefiltered."""
import io, re, sys
from collections import Counter
from multiprocessing import Pool, cpu_count
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(ROOT/"src"))
from _corpus_cache import load_corpus
NAMES = ["fine block","eb1911 fine print","smaller block","dual line","bc","outdent",
         "margin-left","ti","left margin","dent","fs85","fs90","columns","fine","sm"]
NEEDLES = tuple("{{"+n for n in NAMES) + tuple("{{ "+n for n in NAMES)
_HITS=[]
def _init():
    global _tx
    from britannica.pipeline.stages.transform_articles import body_text as BT
    from britannica.pipeline.stages.transform_articles import _transform_text_v2 as tx
    sr=BT._STRIP_TEMPLATES_RE; orig=BT._strip_templates
    def spy(text):
        prev,t=None,text
        while prev!=t:
            prev=t
            for m in re.finditer(sr,t):
                nm=re.match(r"\{\{\s*([^|}\n]*)",m.group(0))
                if nm: _HITS.append(nm.group(1).strip().lower())
            t=re.sub(sr,"",t)
        return orig(text)
    BT._strip_templates=spy; globals()["_tx"]=tx
def _work(item):
    aid,vol,pg0,raw=item; _HITS.clear()
    try: _tx(raw,vol,pg0)
    except Exception: pass
    return [h for h in _HITS]
if __name__=="__main__":
    corpus=[r for r in load_corpus() if any(n in r[3].lower() for n in NAMES)]
    with Pool(max(1,cpu_count()-1),initializer=_init) as p:
        res=p.map(_work,corpus,chunksize=8)
    c=Counter(h for hits in res for h in hits)
    fam=[n.lower() for n in NAMES]
    print(f"scanned {len(corpus)} articles")
    print("=== family-B template deletions still leaking ===")
    for n,k in c.most_common():
        if n in fam: print(f"  {k:4d}  {{{{{n}}}}}")
