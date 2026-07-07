#!/usr/bin/env node
// Golden side of the full-corpus render diff: render EVERY article through the REAL viewer
// (jsdom) and stream {stem, html} JSONL to stdout for corpus_diff.py to check.
//
//   node tools/render/corpus_diff.js | python tools/render/corpus_diff.py
//
// The window is REUSED across articles (parsing viewer.html per article is the bottleneck).
// renderArticle resets every per-article counter EXCEPT the math-popout counter (mp-N);
// corpus_diff.py normalizes mp-\d+ on both sides, so reuse is safe.
const fs = require('fs');
const path = require('path');
const { makeWindow } = require('./viewer_env');

const REPO = path.resolve(__dirname, '..', '..');
const ARTICLES = path.join(REPO, 'data', 'derived', 'articles');

const files = fs.readdirSync(ARTICLES).filter(f => f.endsWith('.json'));
process.stderr.write(`corpus_diff: rendering ${files.length} articles (window reused)\n`);

const w = makeWindow();
let ok = 0, err = 0;
for (let i = 0; i < files.length; i++) {
  const f = files[i];
  const stem = f.slice(0, -5);
  try {
    const article = JSON.parse(fs.readFileSync(path.join(ARTICLES, f), 'utf-8'));
    if (Array.isArray(article) || typeof article !== 'object') continue;  // skip index.json / contributors.json
    article.filename = f;
    w.renderArticle(article);
    process.stdout.write(JSON.stringify({ stem, html: w.document.getElementById('app').innerHTML }) + '\n');
    ok++;
  } catch (e) {
    process.stdout.write(JSON.stringify({ stem, error: e.message }) + '\n');
    err++;
  }
  if ((i + 1) % 2000 === 0) process.stderr.write(`  rendered ${i + 1}/${files.length} (${err} viewer errors)\n`);
}
process.stderr.write(`corpus_diff: done rendering — ${ok} ok, ${err} errors\n`);
