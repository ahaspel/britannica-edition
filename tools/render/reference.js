#!/usr/bin/env node
// Golden-reference generator for the render-to-Python port (project_render_to_python).
//
// Renders each article through the REAL viewer decode (tools/viewer/viewer.html run in
// jsdom) and writes its mechanical HTML — the diff target the Python renderer must
// reproduce (corpus diff, UNEXPECTED=0).  Math is neutralized here (katex stubbed to a
// fixed placeholder), so this tests the STRUCTURAL port; math + interactivity get their
// own verification (Phase 2 / the shell).  The only stubs are the interactive/network
// layer we are NOT porting: fetch, katex, article-urls.js's BritannicaUrls, search.
//
// Usage (from repo root):
//   node tools/render/reference.js --seeds             # the transform-snapshot seed set
//   node tools/render/reference.js <stem> [<stem>…]    # specific article stems
//   node tools/render/reference.js --check [<stem>]    # reused-window vs fresh-window equality
//
// Writes tests/snapshots/render/<stem>.html.

const fs = require('fs');
const path = require('path');
const { makeWindow } = require('./viewer_env');

const REPO = path.resolve(__dirname, '..', '..');
const EXPORT = path.join(REPO, 'data', 'derived', 'articles');
const OUT = path.join(REPO, 'tests', 'snapshots', 'render');

// The same brutal-case seeds the transform snapshots use — one representative per
// element-producer concern, so the render port is stressed on the same articles.
const SEEDS = [
  '01-0032-a-A', '01-0036-s5-ABACUS', '01-0042-s5-ABBEY', '01-0127-s3-ACACIA',
  '01-0157-s2-ACCUMULATOR', '01-0426-agriculture-AGRICULTURE', '01-0358-africa-AFRICA',
  '01-0571-s4-ALDEHYDES', '01-0766-s5-ALPHABET', '02-0302-s5-ARACHNIDA',
  '02-0723-s2-ARTHUR', '03-0219-s5-BAG-PIPE', '04-0375-brachiopoda-BRACHIOPODA',
  '06-0411-cithara-CITHARA', '08-0783-dynamics-DYNAMICS', '14-0147-hydromedusae-HYDROMEDUSAE',
  '14-0737-s2-INTERPOLATION', '18-0684-s2-MOLECULE', '20-0215-s3-ORDNANCE',
  '25-0840-s3-STEAM_ENGINE', '26-0933-s2-THUCYDIDES',
];

function render(win, stem) {
  const json = JSON.parse(fs.readFileSync(path.join(EXPORT, stem + '.json'), 'utf-8'));
  win.renderArticle(json);
  return win.document.getElementById('app').innerHTML;
}

function main() {
  const args = process.argv.slice(2);

  if (args[0] === '--check') {
    const stem = args[1] || '18-0684-s2-MOLECULE';   // footnote-heavy: exposes counter carry
    const w = makeWindow();
    render(w, stem);                                  // dirty the window with a prior render
    const reused = render(w, stem);                   // same window, second render
    const fresh = render(makeWindow(), stem);         // pristine window
    console.log(`reuse === fresh for ${stem}: ${reused === fresh}` +
                `  (reused ${reused.length}, fresh ${fresh.length})`);
    if (reused !== fresh) {
      let i = 0; while (i < reused.length && reused[i] === fresh[i]) i++;
      console.log(`  first divergence @${i}: reuse ${JSON.stringify(reused.slice(i, i + 40))}`);
      console.log(`                          fresh ${JSON.stringify(fresh.slice(i, i + 40))}`);
    }
    return;
  }

  const stems = (args.includes('--seeds') || args.length === 0)
    ? SEEDS : args.filter(a => !a.startsWith('--'));
  fs.mkdirSync(OUT, { recursive: true });
  let ok = 0;
  for (const stem of stems) {
    try {
      // Fresh window per article: per-article 0-based counters (math-popout `mp-N`,
      // footnotes) match the Python renderer's per-article output with no normalization.
      // Window reuse carries the popout counter (see `--check`), so a full-corpus run
      // should reuse + normalize `mp-\d+` for speed instead.
      const html = render(makeWindow(), stem);
      fs.writeFileSync(path.join(OUT, stem + '.html'), html, 'utf-8');
      console.log(`  OK   ${stem}  ${html.length} chars`);
      ok++;
    } catch (e) {
      console.log(`  FAIL ${stem}  ${e.message}`);
    }
  }
  console.log(`\ncaptured ${ok}/${stems.length} references -> ${path.relative(REPO, OUT)}`);
}

main();
