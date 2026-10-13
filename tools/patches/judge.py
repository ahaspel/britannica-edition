"""Step 2 of evaluation: the JUDGE.  For each column of a page, the model gets
the column's scan and that column's disputed sites (disputes.json), each as
reading A and reading B in RANDOM order (it never knows which is ours), and
says which one the print bears out: A, B, both, or neither.

Calibration is blind and in the same calls: PLANT sites made from words both
texts agree on, one side given an OCR-like error at random (a letter swapped
or dropped, a confusable substituted), the other side the true word.  Every
planted site has a known answer; the judge's verdicts on them are its score.

Usage: judge.py STEM ... | --set FILE   [--plant N per column]
Answers cached in judge.json by page:column (one call each, never repeated)."""
import json
import random
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
from eb1911.scans import page_scan
from wikikit.scan import cut
from wikikit.scan.model import ask, metered, parse_json
sys.path.insert(0, str(Path(__file__).parent))
from paths import ANSWERS, DISPUTES, reading
from patterns import TOKEN

OUT = ANSWERS
DIS = json.loads(DISPUTES.read_text(encoding="utf-8"))


def payload_of(stem: str) -> dict:
    v = int(stem[3:5])
    src = reading(stem)
    return json.loads(src.read_text(encoding="utf-8"))

PROMPT = """This image is one column of a scanned page of an encyclopaedia.

Below are places where two transcriptions of this column differ. Each shows
the words just before and just after the place, on which both agree, and the
two readings of the words in between: A and B. Words are given in lower case,
without punctuation or formatting; a formula is given as its letters and
digits in order (a fraction a/b as "a b", a Greek letter as itself). Either
reading may be empty (nothing there).

For each place, find it in the column and say which reading matches what is
PRINTED there:
  "A" — A matches the print and B does not
  "B" — B matches the print and A does not
  "both" — they say the same thing as printed
  "neither" — neither matches the print
Judge by the print alone, letter by letter; do not prefer a reading because it
looks more correct or more modern.

{sites}

Answer with JSON only: {{"verdicts": [{{"id": "...", "verdict": "A" | "B" |
"both" | "neither", "printed": "only the words printed in between, in lower case,
given as the readings are"}}]}}"""

CONFUSE = [("rn", "m"), ("m", "rn"), ("e", "c"), ("c", "e"), ("l", "i"), ("i", "l"), ("h", "b"),
           ("u", "n"), ("n", "u"), ("o", "a"), ("a", "o"), ("t", "f"), ("f", "t"), ("s", "a")]


SYMBOL_SWAP = {"x": "y", "y": "x", "a": "o", "o": "a", "n": "u", "u": "n", "p": "q", "q": "p",
               "b": "h", "h": "b", "c": "e", "e": "c", "i": "l", "l": "i", "r": "v", "v": "r",
               "m": "n", "t": "f", "f": "t", "s": "z", "z": "s", "k": "h", "d": "a", "g": "q"}


def corrupt(word: str, rng: random.Random) -> str:
    """An OCR-like misreading of `word`: a confusable swapped, or a letter
    dropped; a formula's symbol (a digit or a letter or two) changed to
    another digit or a look-alike letter."""
    if len(word) <= 2:
        i = rng.randrange(len(word))
        ch = word[i]
        new = str((int(ch) + rng.randrange(1, 9)) % 10) if ch.isdigit() else \
            SYMBOL_SWAP.get(ch, "x" if ch != "x" else "y")
        return word[:i] + new + word[i + 1:]
    opts = [(i, a, b) for a, b in CONFUSE for i in [m.start() for m in re.finditer(re.escape(a), word)]]
    if opts and rng.random() < 0.7:
        i, a, b = rng.choice(opts)
        return word[:i] + b + word[i + len(a):]
    i = rng.randrange(1, len(word) - 1)
    return word[:i] + word[i + 1:]


#: The same print in another code point: Unicode compatibility forms (½ -> 1⁄2,
#: ₀ -> 0, ᵐ -> m) and these, which have none.
SAME = {"ƒ": "f", "℔": "lb", "Σ": "σ", "∑": "σ", "∏": "π", "Π": "π"}


def _norm(s) -> str:
    import unicodedata
    s = unicodedata.normalize("NFKC", s or "")
    s = "".join(SAME.get(ch, ch) for ch in s).lower()
    return " ".join(TOKEN.findall(s))


def _between(printed: str, before: str, after: str) -> str:
    """The words of `printed` at the site: what lies between the end of the
    agreed context before it and the start of the context after it, when the
    judge wrote out the context too; else `printed` as it is."""
    p, b, a = printed.split(), before.split()[-3:], after.split()[:3]
    start = next((i + len(b) for i in range(len(p) - len(b) + 1) if b and p[i:i + len(b)] == b), None)
    if start is None:
        return printed
    end = next((j for j in range(start, len(p) - len(a) + 1) if a and p[j:j + len(a)] == a), len(p))
    return " ".join(p[start:end])


def ruling(s) -> str:
    """The site's ruling: the judge's verdict where its own reading of the
    print ("printed", read at the site) bears it out — the winning side
    equals what it says is printed, or (both/neither) is consistent with it —
    else "unsure"."""
    v = s.get("verdict")
    printed = _between(_norm(s.get("printed")), _norm(s["before"]), _norm(s["after"]))
    ws, ours = _norm(s["ws"]), _norm(s["ours"])
    # letters compared with spacing ignored: "zmƒ" and "z m f" are one print
    p, w, o = (x.replace(" ", "") for x in (printed, ws, ours))
    if w == o:
        return "same"                    # one print, two code points: no dispute
    if p and p == o:
        return "ours"                    # the judge's own reading of the print
    if p and p == w:
        return "ws"
    printed, ws, ours = p, w, o
    if v in ("ws", "ours"):
        win, lose = (ws, ours) if v == "ws" else (ours, ws)
        return v if printed == win and printed != lose else "unsure"
    if v == "both":
        return "both" if printed == ws == ours or ws == ours else "unsure"
    if v == "neither":
        # nothing printed where both readings have words: the judge did not
        # find the place (2 planted sites, vol 25 p130 and p459) — no ruling
        if not printed and ws and ours:
            return "unsure"
        return "neither" if printed not in (ws, ours) else "unsure"
    return "unsure"


def columns_of(d):
    """column -> (box over its text items, the item names in it)."""
    cols = {}
    for it in d["provenance"]["items"]:
        if it["kind"] not in ("text", "caption") or it["column"] == 0:
            continue
        x0, y0, x1, y1 = it["box"]
        b, names = cols.get(it["column"], ((x0, y0, x1, y1), []))
        cols[it["column"]] = ((min(b[0], x0), min(b[1], y0), max(b[2], x1), max(b[3], y1)), names + [it["name"]])
    return cols


def build(stem, rng, plant):
    v = int(stem[3:5])
    d = payload_of(stem)
    dis = DIS[stem]
    calls = []
    for col, (box, names) in sorted(columns_of(d).items()):
        real = [{"id": f"r{n}", "truth": None, "ws": s["ws"], "ours": s["ours"],
                 "before": s["before"], "after": s["after"]}
                for n, s in enumerate(dis["sites"]) if s["item"] in names
                and (stem, s["ws"], s["ours"], s["before"], s["after"]) not in JUDGED]
        if JUDGED and not real:
            continue
        words = [a for a in dis["agreed"] if a["item"] in names and a.get("kind", "word") == "word"]
        symbols = [a for a in dis["agreed"] if a["item"] in names and a.get("kind") == "symbol"]
        chunks = [real[i:i + CHUNK] for i in range(0, len(real), CHUNK)] or [[]]
        rng.shuffle(words)
        rng.shuffle(symbols)
        pool = [x for pair in zip(words, symbols) for x in pair] + words[len(symbols):] + symbols[len(words):]
        for c, sites in enumerate(chunks):
            for k, a in enumerate(pool[c * plant:(c + 1) * plant]):
                bad = corrupt(a["word"], rng)
                ws_bad = rng.random() < 0.5
                sites.append({"id": f"p{c}_{k}", "truth": "ours" if ws_bad else "ws", "kind": a.get("kind", "word"),
                              "ws": bad if ws_bad else a["word"], "ours": a["word"] if ws_bad else bad,
                              "before": a["before"], "after": a["after"]})
            rng.shuffle(sites)
            for s in sites:
                s["a_is"] = rng.choice(["ws", "ours"])
            # a --new call is named by the sites it carries: a later recount's
            # call over other sites never collides with it in the cache
            tag = ""
            if JUDGED:
                import hashlib
                sig = "\n".join(sorted(f'{s["ws"]}|{s["ours"]}|{s["before"]}|{s["after"]}'
                                       for s in sites if not s["truth"]))
                tag = "n" + hashlib.sha1(sig.encode("utf-8")).hexdigest()[:8] + "_"
            calls.append((f"{stem}:{col}:{tag}{c}", v, d, box, sites))
    return calls


#: --new: judge only the sites no earlier call judged (a recount of the
#: disputes changed some), by the site's exact text and context
JUDGED: set = set()
if "--new" in sys.argv and OUT.exists():
    for _key, _sites in json.loads(OUT.read_text(encoding="utf-8")).items():
        for _s in _sites:
            if not _s["truth"]:
                JUDGED.add((_key.split(":")[0], _s["ws"], _s["ours"], _s["before"], _s["after"]))


#: Sites per call: a column's answer for 100+ sites overran the reply (2 of 12
#: calibration calls returned no verdicts at all).
CHUNK = 35


def text_of(sites):
    out = []
    for s in sites:
        a = s[s["a_is"]]
        b = s["ours" if s["a_is"] == "ws" else "ws"]
        out.append(f'id {s["id"]}: …{s["before"]} [A: "{a}" | B: "{b}"] {s["after"]}…')
    return "\n".join(out)


def take(done: dict, key: str, sites: list, text: str) -> None:
    """One column's answer, ruled and cached."""
    try:
        got = {x["id"]: x for x in parse_json(text)["verdicts"]}
    except (ValueError, KeyError):
        got = {}
    if not got:
        print(f"{key}: NO VERDICTS — not cached; answer ends {text[-150:]!r}", flush=True)
        return
    for s in sites:
        g = got.get(s["id"], {})
        verdict = g.get("verdict")
        # A/B back to the sources
        s["verdict"] = {"A": s["a_is"], "B": "ours" if s["a_is"] == "ws" else "ws"}.get(verdict, verdict)
        s["printed"] = g.get("printed")
        s["ruling"] = ruling(s)
    done[key] = sites
    OUT.write_text(json.dumps(done, indent=1, ensure_ascii=False), encoding="utf-8")
    planted = [s for s in sites if s["truth"]]
    right = sum(s["ruling"] == s["truth"] for s in planted)
    wrong = [s for s in planted if s["ruling"] not in (s["truth"], "unsure")]
    print(f"{key}: {len(sites) - len(planted)} disputes, planted {right}/{len(planted)} right"
          f", {len(wrong)} WRONG", flush=True)


#: --batch: the same calls through the Batch API (half price); the calls sent
#: are kept here until their answers are taken, so a run resumes at will
PENDING = OUT.with_name(OUT.stem + "_pending.json")
#: A batch's requests carry full column images: one batch of every call was
#: dropped by the server (2026-10-11); sent in parts of at most this size.
CHUNK_BYTES = 60 * 1024 * 1024


def chunks(reqs: dict) -> list[dict]:
    out, cur, size = [], {}, 0
    for cid, params in reqs.items():
        n = len(json.dumps(params))
        if cur and size + n > CHUNK_BYTES:
            out.append(cur)
            cur, size = {}, 0
        cur[cid], size = params, size + n
    if cur:
        out.append(cur)
    return out


def main():
    args = sys.argv[1:]
    plant = int(args[args.index("--plant") + 1]) if "--plant" in args else 4
    # --calibrate FILE: plant only on these pages (the calibration slice)
    slice_ = set(Path(args[args.index("--calibrate") + 1]).read_text().split()) if "--calibrate" in args else None
    stems = Path(args[args.index("--set") + 1]).read_text().split() if "--set" in args else \
        [a for a in args if a.startswith("vol")]
    done = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    rng = random.Random(1911)
    if "--batch" in args:
        return run_batch(stems, done, rng, plant, slice_)
    with metered() as m:
        for stem in stems:
            for key, v, d, box, sites in build(stem, rng, plant if slice_ is None or stem in slice_ else 0):
                if key in done or not sites:
                    continue
                level = cut.deskew(page_scan(v, d["page_number"]), d["provenance"]["angle"]).convert("L")
                take(done, key, sites, ask(level.crop(box), PROMPT.format(sites=text_of(sites)), max_tokens=8000))
    print("usage", m.record())


def run_batch(stems, done, rng, plant, slice_):
    import time
    from wikikit.scan.model import batch_status, collect, request, submit
    pending = json.loads(PENDING.read_text(encoding="utf-8")) if PENDING.exists() else None
    if pending is None:
        calls, reqs = {}, {}
        for stem in stems:
            level = None
            for key, v, d, box, sites in build(stem, rng, plant if slice_ is None or stem in slice_ else 0):
                if key in done or not sites:
                    continue
                if level is None:
                    level = cut.deskew(page_scan(v, d["page_number"]), d["provenance"]["angle"]).convert("L")
                cid = f"j{len(calls)}"
                calls[cid] = {"key": key, "sites": sites}
                reqs[cid] = request(level.crop(box), PROMPT.format(sites=text_of(sites)), max_tokens=8000)
        if not reqs:
            print("nothing to judge")
            return
        pending = {"batches": [submit(chunk) for chunk in chunks(reqs)], "calls": calls}
        PENDING.write_text(json.dumps(pending, ensure_ascii=False), encoding="utf-8")
        print(f"sent {len(reqs)} calls as {pending['batches']}", flush=True)
    results = {}
    for bid in pending["batches"]:
        while (st := batch_status(bid))[0] != "ended":
            print("waiting", bid, st, flush=True)
            time.sleep(300)
        results.update(collect(bid))
    tokens = {"in": 0, "out": 0}
    for cid, (status, text, usage) in results.items():
        c = pending["calls"][cid]
        if usage is not None:
            tokens["in"] += usage.input_tokens
            tokens["out"] += usage.output_tokens
        if status != "ok":
            print(f"{c['key']}: {status} {text[:150]!r} — not cached", flush=True)
            continue
        take(done, c["key"], c["sites"], text)
    PENDING.unlink()
    print("usage (batch)", tokens)


if __name__ == "__main__":
    main()
