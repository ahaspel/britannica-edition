"""Audit: image-with-caption-below figures (the #24 cluster) corpus-wide.

The leaking/duplicating ACCUMULATOR figures share the shape
`[[File:…]]<br>…caption…`, wrapped variously: a float <div>, a
{{center|…}}, or bare.  Counts the population and the wrapper breakdown
so we know the blast radius before touching figure recognition.
Read-only; per-volume flushed.  Scans SourcePage.wikitext.
"""
import io, re, sys
from collections import Counter, defaultdict
sys.path.insert(0, "src")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from britannica.db.session import SessionLocal
from britannica.db.models import SourcePage

# image immediately followed by <br> = a figure with a caption beneath.
_IMG_BR = re.compile(
    r"\[\[(?:File|Image):[^\]]*\]\]\s*<br\s*/?>", re.IGNORECASE)
_CAP_SIG = re.compile(r"\{\{\s*(?:sc|small[\s-]?caps?)\s*\|\s*Fig", re.IGNORECASE)

s = SessionLocal()
wrapper = Counter()
capsig = Counter()
samples = defaultdict(list)
total = 0

vols = [v for (v,) in s.query(SourcePage.volume).distinct()
        .order_by(SourcePage.volume) if v and v < 29]
print(f"{'vol':>3} {'img<br>':>8}", flush=True)
for v in vols:
    n = 0
    for (w,) in s.query(SourcePage.wikitext).filter(SourcePage.volume == v):
        if not w:
            continue
        for m in _IMG_BR.finditer(w):
            total += 1
            n += 1
            back = w[max(0, m.start() - 90):m.start()]
            after = w[m.end():m.end() + 120]
            if re.search(r"<div\b[^>]*float", back, re.IGNORECASE):
                kind = "float-div"
            elif re.search(r"\{\{\s*center\b", back, re.IGNORECASE):
                kind = "center-wrapper"
            else:
                kind = "other/bare"
            wrapper[kind] += 1
            if _CAP_SIG.search(after):
                capsig["caption has {{sc|Fig}}"] += 1
            if len(samples[kind]) < 4:
                samples[kind].append(after[:90])
    print(f"{v:>3} {n:>8}", flush=True)

print(f"\n=== image-with-<br> figures: {total} ===")
print("\nwrapper:")
for k, c in wrapper.most_common():
    print(f"  {k:16}{c}")
print("\ncaption signal:")
for k, c in capsig.most_common():
    print(f"  {k:26}{c}")
print("\n--- samples (text after [[File:]]<br>) ---")
for k in samples:
    print(f"  [{k}]")
    for snip in samples[k]:
        print(f"    {snip!r}")
