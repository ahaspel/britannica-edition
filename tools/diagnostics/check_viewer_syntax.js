const fs = require('fs');
const src = fs.readFileSync('tools/viewer/viewer.html', 'utf8');
const scripts = [...src.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)].map(m => m[1]);
const main = scripts.find(s => s.includes('function decodeInlineMarkers'));
if (!main) { console.log('main script not found'); process.exit(1); }
try { new Function(main); console.log('VIEWER SCRIPT SYNTAX: OK (' + main.length + ' chars)'); }
catch (e) { console.log('VIEWER SCRIPT SYNTAX ERROR: ' + e.message); process.exit(1); }
