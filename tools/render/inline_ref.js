// Reference outputs of the viewer's REAL decodeInlineMarkers for a battery of inputs
// (inline_cases.json) — the target the Python inline engine (src/britannica/render/
// inline.py) must reproduce.  Uses the {escape:true} path (cells/captions): escape the
// text, then decode the markers.
//
//   node tools/render/inline_ref.js        # writes tools/render/inline_ref.json
const fs = require('fs');
const path = require('path');
const { makeWindow } = require('./viewer_env');

const cases = JSON.parse(fs.readFileSync(path.join(__dirname, 'inline_cases.json'), 'utf-8'));
const w = makeWindow();
const out = cases.map(input => ({
  input,
  output: w.decodeInlineMarkers(input, { escape: true }),
}));
fs.writeFileSync(path.join(__dirname, 'inline_ref.json'),
                 JSON.stringify(out, null, 1), 'utf-8');
console.log(`captured ${out.length} inline references -> tools/render/inline_ref.json`);
