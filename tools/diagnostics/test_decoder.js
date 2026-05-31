const fs = require('fs');
const src = fs.readFileSync('tools/viewer/viewer.html', 'utf8');

// Extract a `function NAME(...) {...}` body by brace-matching.
function extract(name) {
  const start = src.indexOf('function ' + name + '(');
  if (start < 0) throw new Error('not found: ' + name);
  let i = src.indexOf('{', start), d = 0;
  for (let j = i; j < src.length; j++) {
    if (src[j] === '{') d++;
    else if (src[j] === '}') { d--; if (d === 0) return src.slice(start, j + 1); }
  }
}
function articleUrl(f) { return '/article/' + f; }
function gardinerToUnicode(c) { return null; }
eval(extract('applySizeMarkers'));
eval(extract('decodeInlineMarkers'));

// REFERENCE: the body path's invariant sequence, hand-copied verbatim.
function refBody(h) {
  h = h.replace(/«MIRROR:(.*?)«\/MIRROR»/gs, '<span class="mirror-h">$1</span>');
  h = h.replace(/«B»(.*?)«\/B»/gs, "<b>$1</b>");
  h = h.replace(/«I»(.*?)«\/I»/gs, "<i>$1</i>");
  h = h.replace(/«SC»(.*?)«\/SC»/gs, '<span class="small-caps">$1</span>');
  h = h.replace(/«SS»(.*?)«\/SS»/gs, '<span class="sans-serif">$1</span>');
  h = h.replace(/«SR»(.*?)«\/SR»/gs, '<span class="explicit-serif">$1</span>');
  h = applySizeMarkers(h);
  h = h.replace(/«BAR\[(\d+)\]»/g, (_m, n) => `<span class="inline-bar" style="width:${n}em">&nbsp;</span>`);
  h = h.replace(/«DHR(?:\[[^\]]*\])?»/g, '<span class="dhr-block"></span>');
  h = h.replace(/«CTR»([\s\S]*?)«\/CTR»/g, '<div class="centered">$1</div>');
  h = h.replace(/«BRACE2\[(\d+)\|([lrud])\]»/g, (_m, _n, side) => {
    const g = side === 'l' ? '⎧' : side === 'r' ? '⎫' : side === 'u' ? '⏞' : '⏟';
    return `<span class="brace2 brace2-${side}">${g}</span>`;
  });
  h = h.replace(/\[hieroglyph:\s*([^\]]+)\]/g, (match, codes) => {
    const r = codes.trim().split(/[:\s\-]+/).map(code => {
      code = code.replace(/\\/g, "");
      if (!code || code === "<" || code === ">" || code === "!" || code === "-") return "";
      const cp = gardinerToUnicode(code);
      if (cp) return `<span class="hieroglyph">&#x${cp.toString(16)};</span>`;
      return `<span class="hieroglyph-fallback" title="Gardiner ${code}">${code}</span>`;
    }).join("");
    return r || match;
  });
  h = h.replace(/«LN:([^|]*)\|([^|«]*?)(?:\|([^«]*))?«\/LN»/g, (match, g1, g2, g3) => {
    const hf = g3 !== undefined;
    const t = hf ? g2 : g1, d = hf ? g3 : g2, f = hf ? g1 : null;
    const href = f ? articleUrl(f) : `/search.html?q=${encodeURIComponent(t)}`;
    return `<a href="${href}" class="article-link" title="${t}">${d}</a>`;
  });
  return h;
}

const corpus = [
  "«B»bold«/B» «I»it«/I» «SC»sc«/SC»",
  "«SS»ss«/SS» «SR»sr«/SR»",
  "«SM»sm«/SM» «XL»xl«/XL» «XXL»xxl«/XXL» «LG»lg«/LG» «XS»xs«/XS» «XXS»xxs«/XXS»",
  "«FS[120%]»fs«/FS» «LH[88%]»lh«/LH»",
  "«BAR[3]» and «DHR» and «DHR[50%]»",
  "«CTR»centered«/CTR»",
  "«BRACE2[2|l]» «BRACE2[3|r]»",
  "«MIRROR:Z«/MIRROR»",
  "[hieroglyph: A1:B2-C3]",
  "«LN:24-x.json|SCHLIEMANN|Schliemann«/LN»",
  "«LN:Formalin|Formalin«/LN»",
  "«CTR»«LH[88%]»«SC»Fig. 4.«/SC»— MIDDLE MINOAN VASE.<br />«SM»«I»B. S. A.«/I» ix.«/SM»«/LH»«/CTR»",
  "«CTR»«SC»Plate I.«/SC»«/CTR» «SM»Cf. «I»J.H.S.«/I»«/SM»",
];
let diffs = 0, leaks = 0;
for (const s of corpus) {
  const a = decodeInlineMarkers(s), b = refBody(s);
  if (a !== b) { diffs++; console.log("DIFF:\n  in : " + s + "\n  new: " + a + "\n  ref: " + b); }
  if (/«/.test(a)) { leaks++; console.log("LEAK (residual « after decode): " + a); }
}
console.log(`\n${corpus.length} cases | decoder-vs-body DIFFS: ${diffs} | residual-marker LEAKS: ${leaks}`);
console.log("\nplate caption renders as:\n  " + decodeInlineMarkers(corpus[11]));
