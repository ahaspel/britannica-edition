/** Check the compiled sample inside an isolated GoldenDict-ng WebEngine.
 * Launch a portable reader with QTWEBENGINE_REMOTE_DEBUGGING=127.0.0.1:9223,
 * load the sample, then: node tools/diagnostics/check_mdx_reader.mjs
 * Uses Node's built-in WebSocket; Playwright browser-context operations are
 * unsupported by Qt WebEngine. All HTTP(S) page requests are blocked during QA.
 */
import {readFileSync, writeFileSync, mkdirSync} from 'node:fs';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';

const output = process.argv[2] || 'mdx/sample';
const readerHome = process.argv[3] || 'mdx/reader/GoldenDict-ng-26.8.0-Qt6.10.3';
const manifest = JSON.parse(readFileSync(`${output}/manifest.json`, 'utf8'));
const complete = manifest.edition === 'complete';
const basename = complete ? 'Britannica11' : 'Britannica11-sample';
const config = readFileSync(`${readerHome}/portable/config`, 'utf8');
const ignoreDiacritics = /<ignoreDiacritics>1<\/ignoreDiacritics>/.test(config);
for (const section of ['mediawikis','websites','dictservers','programs']) {
  const body = config.match(new RegExp(`<${section}>([\\s\\S]*?)</${section}>`))?.[1] || '';
  const checked = section === 'programs' && manifest.native_search
    ? body.replace(/<program\b[^>]*>/g, tag => /id="eb1911-(?:title-search|name-lookup)"/.test(tag) ? '' : tag)
    : body;
  assert(!/enabled="1"/.test(checked), 'Disable native network sources before QA: ' + section);
}
const artifactHashes = {};
for (const ext of ['mdx','mdd']) {
  const name = basename + '.' + ext;
  const shipped = readFileSync(`${output}/${name}`);
  assert(shipped.equals(readFileSync(`${readerHome}/content/${name}`)), 'Reader copy differs: ' + name);
  artifactHashes[name] = createHash('sha256').update(shipped).digest('hex');
}
if (manifest.native_search) {
  for (const file of ['titles.json','articles.sqlite','lookup.cjs','search-api.js','install.py']) {
    const shipped = readFileSync(`${output}/search/${file}`);
    assert(shipped.equals(readFileSync(`${readerHome}/content/search/${file}`)), 'Reader helper differs: '+file);
    artifactHashes['search/'+file] = createHash('sha256').update(shipped).digest('hex');
  }
}
const endpoint = process.env.MDX_READER_CDP || 'http://127.0.0.1:9223';
const targets = await (await fetch(endpoint + '/json')).json();
const target = targets.find(t => t.type === 'page');
assert(target, 'Open a dictionary lookup in the portable GoldenDict-ng reader first');
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
let serial = 0;
const pending = new Map(), network = [];
ws.onmessage = e => {
  const m = JSON.parse(e.data);
  if (m.method === 'Network.requestWillBeSent') network.push(m.params.request.url);
  if (pending.has(m.id)) {
    const {resolve, reject, timer} = pending.get(m.id);
    clearTimeout(timer); pending.delete(m.id);
    m.error ? reject(new Error(JSON.stringify(m.error))) : resolve(m.result);
  }
};
function call(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = ++serial;
    const timer = setTimeout(() => { pending.delete(id); reject(new Error('CDP timeout: ' + method)); }, 15000);
    pending.set(id, {resolve, reject, timer});
    ws.send(JSON.stringify({id, method, params}));
  });
}
async function evaluate(expression) {
  const r = await call('Runtime.evaluate', {expression, returnByValue:true, awaitPromise:true});
  assert(!r.exceptionDetails, JSON.stringify(r.exceptionDetails));
  return r.result.value;
}
async function waitFor(expression) {
  for (let n = 0; n < 100; n++) {
    if (await evaluate(expression)) return;
    await new Promise(r => setTimeout(r, 100));
  }
  throw new Error('Reader wait failed: ' + expression);
}
async function lookup(word, expected) {
  await call('Page.navigate', {url:'about:blank'});
  await waitFor(`location.href==='about:blank'`);
  // Match the URL produced by native title lookup, including its preference.
  await call('Page.navigate', {url:'gdlookup://localhost/?word=' + encodeURIComponent(word) + '&group=4294967294' + (ignoreDiacritics ? '&ignore_diacritics=1' : '')});
  await waitFor(`document.readyState==='complete' && document.querySelector('.eb1911') && document.body.textContent.toLowerCase().includes(${JSON.stringify(expected.toLowerCase())})`);
  // Load offscreen lazy images too: this tests every MDD resource, not only
  // the first viewport of a long article. Normal rendering retains laziness.
  await evaluate(`[...document.querySelectorAll('.eb1911 img')].forEach(i=>i.loading='eager')`);
  await waitFor(`[...document.querySelectorAll('.eb1911 img')].every(i=>i.complete)`);
}
async function snapshot(name) {
  const r = await call('Page.captureScreenshot', {format:'png'});
  writeFileSync(`${output}/reader-qa/${name}.png`, Buffer.from(r.data, 'base64'));
}
const report = {checked_utc:new Date().toISOString(), reader_dir:readerHome, artifact_sha256:artifactHashes,
  native_network_sources:'disabled in portable config', endpoint,
  engine:await (await fetch(endpoint + '/json/version')).json(), checks:[]};
mkdirSync(`${output}/reader-qa`, {recursive:true});
try {
  await call('Network.enable');
  await call('Network.setBlockedURLs', {urls:['http://*', 'https://*']});
  await call('Emulation.setDeviceMetricsOverride', {width:1050, height:800, deviceScaleFactor:1, mobile:false});
  const entries = JSON.parse(readFileSync(`${output}/entries.json`, 'utf8'));
  for (const stem of Object.keys(manifest.sample)) {
    const key = 'EB1911:article:' + stem;
    const title = entries[key].match(/<h1[^>]*>(.*?)<\/h1>/s)?.[1].replace(/<[^>]*>/g, '');
    assert(title, 'No article heading: ' + key);
    await lookup(key, title);
    const result = await evaluate(`JSON.stringify({title:document.querySelector('.eb1911 h1').textContent,
      images:[...document.querySelectorAll('.eb1911 img')].map(i=>({src:i.src,width:i.naturalWidth})),
      svg:document.querySelectorAll('.eb1911 svg').length,tables:document.querySelectorAll('.eb1911 table').length,
      stylesheet:[...document.querySelectorAll('link')].some(l=>l.href.endsWith('/britannica.css')&&!!l.sheet)})`);
    const data = JSON.parse(result);
    assert.equal(data.svg, (entries[key].match(/<svg\b/g)||[]).length, 'SVG lost in reader');
    assert(data.stylesheet, 'MDD stylesheet failed');
    assert(data.images.every(i=>i.width>0 && i.src.startsWith('bres:')), 'MDD image failed: ' + result);
    report.checks.push({article:stem, ...data});
  }
  await lookup('MERCURY', 'Choose an article');
  assert.equal(await evaluate(`document.querySelectorAll('.eb1911 li a').length`), 3);
  await waitFor(`document.body.textContent.includes('QA control dictionary: unrelated mercury definition.')`);
  await snapshot('mercury-choices');
  await evaluate(`document.querySelector('.eb1911 li a').click()`);
  await waitFor(`!!document.querySelector('.eb1911 h1') && document.querySelector('.eb1911 h1').textContent==='MERCURY'`);
  assert(!(await evaluate(`document.body.textContent.includes('QA control dictionary: unrelated mercury definition.')`)));
  report.checks.push({lookup:'MERCURY', choices:3, click:true, other_local_dictionary_isolated:true});
  const history = await call('Page.getNavigationHistory');
  await call('Page.navigateToHistoryEntry', {entryId:history.entries[history.currentIndex-1].id});
  await waitFor(`document.querySelector('.eb1911')?.textContent.includes('Choose an article')`);
  report.checks.push({back_navigation:true});
  await lookup('Continued Fraction', 'CONTINUED FRACTIONS');
  report.checks.push({alias:'Continued Fraction', resolved:true});
  await lookup('ABABDA', 'ABĀBDA');
  report.checks.push({folded_lookup:'ABABDA', resolved:true});
  await lookup('AARON’S ROD', 'AARON’S ROD');
  report.checks.push({unicode_lookup:'AARON’S ROD', resolved:true});
  await lookup('AGRICULTURE', 'AGRICULTURE');
  const table = await evaluate(`(()=>{const t=[...document.querySelectorAll('.eb1911 table')].sort((a,b)=>b.scrollWidth-a.scrollWidth)[0];t.scrollIntoView({block:'start'});return {width:t.scrollWidth,viewport:innerWidth,rows:t.rows.length}})()`);
  await snapshot('agriculture-table');
  report.checks.push({table_rendering:table});
  await lookup('EB1911:article:02-0723-420571', 'ARTHUR');
  await evaluate(`document.querySelector('.eb1911 a[href$="#fn-1"]').click()`);
  await waitFor(`location.hash==='#fn-1'`);
  await evaluate(`document.querySelector('.eb1911 a[href$="#fnref-1"]').click()`);
  await waitFor(`location.hash==='#fnref-1'`);
  report.checks.push({footnote_and_return:true});
  await lookup('ALGEBRA', 'ALGEBRA');
  await evaluate(`document.querySelector('.eb1911 a[href*="contributor"]').click()`);
  await waitFor(`document.querySelector('.eb1911 h2')?.textContent.includes('Articles')`);
  assert(await evaluate(`document.querySelector('.eb1911 h1').textContent.includes('Sheppard')`));
  report.checks.push({contributor_navigation:true});
  await lookup('ALGEBRA', 'ALGEBRA');
  assert(await evaluate(`(()=>{const topics=document.querySelector('.eb1911 .article-topics');const byline=document.querySelector('.eb1911 .contributors');return !!topics && byline?.nextElementSibling===topics && !topics.closest('details') && topics.getBoundingClientRect().height>0})()`), 'Topics must be visible directly below the byline');
  await evaluate(`document.querySelector('.eb1911 a[href*="topic"]').click()`);
  await waitFor(`location.href.includes('topic') && document.querySelector('.eb1911 h1') && !document.querySelector('.eb1911 .body-text')`);
  report.checks.push({topic_navigation:true});
  if (complete) {
    await lookup('Jonathan Swift', 'SWIFT, JONATHAN');
    assert.equal(await evaluate(`document.querySelector('.eb1911 h1').innerText`), 'SWIFT, JONATHAN');
    report.checks.push({natural_name_lookup:'Jonathan Swift', resolved:true});
    if (manifest.native_search) {
      const {DatabaseSync} = await import('node:sqlite');
      const {inflateSync} = await import('node:zlib');
      const db = new DatabaseSync(`${output}/search/articles.sqlite`, {readOnly:true});
      for (const [query, stem, title] of [
        ['Continued Fraction','07-0045-9b7a0f','CONTINUED FRACTIONS'],
        ['Air Engines','01-0481-535ef5','AIR-ENGINE'],
      ]) {
        await lookup(query, title);
        const body = inflateSync(db.prepare('SELECT body FROM articles WHERE id=?').get(stem).body).toString('utf8');
        const data = await evaluate(`({images:[...document.querySelectorAll('.eb1911 img')].map(i=>({src:i.src,width:i.naturalWidth})),svg:document.querySelectorAll('.eb1911 svg').length,styled:getComputedStyle(document.querySelector('.eb1911')).fontFamily.includes('Georgia'),articles:document.querySelectorAll('.eb1911').length})`);
        assert.equal(data.articles, 1, 'Alias duplicated the article');
        assert.equal(data.svg, (body.match(/<svg\b/g)||[]).length);
        assert.equal(data.images.length, (body.match(/<img\b/g)||[]).length);
        assert(data.images.every(i=>i.width>0 && i.src.startsWith('bres:')));
        assert(data.styled, 'HTML program lost the article stylesheet');
        await snapshot('native-alias-'+stem);
        report.checks.push({native_alias_resources:query, ...data});
      }
      db.close();
    }
    await lookup('Britannica 11', 'Complete offline reference');
    const section = entries['EB1911:article:01-0639-46474b'].match(/id="(section-[^"]+)"/)[1];
    // An explicit QA link to a real anchor; no test text is shipped in the book.
    await evaluate(`(()=>{const a=document.createElement('a');a.textContent='Open a section within Algebra';a.href='gdlookup://localhost/?word='+encodeURIComponent('EB1911:article:01-0639-46474b')+'&group=4294967294&gdanchor='+${JSON.stringify(section)};document.querySelector('.eb1911').append(a)})()`);
  } else {
    await lookup('Britannica 11 sample', 'Section-link test');
  }
  await evaluate(`[...document.querySelectorAll('.eb1911 a')].find(a=>a.textContent==='Open a section within Algebra').click()`);
  await waitFor(`document.querySelector('.eb1911 h1')?.textContent==='ALGEBRA' && scrollY>0`);
  report.checks.push({cross_entry_section:true, url:await evaluate('location.href'), scrollY:await evaluate('scrollY')});
  await snapshot('algebra-section');
  await lookup('ALGEBRA', 'ALGEBRA');
  await evaluate(`document.querySelector('.eb1911 svg').scrollIntoView({block:'center'})`);
  await snapshot('algebra-math');
  await call('Emulation.setEmulatedMedia', {features:[{name:'prefers-color-scheme',value:'dark'}]});
  // This explicitly tests content against dark colors, not GoldenDict's native
  // theme preference UI. Record that distinction in the report.
  await evaluate(`document.documentElement.style.background='#202020';document.body.style.background='#202020';document.body.style.color='#eeeeee'`);
  await snapshot('algebra-math-dark');
  report.checks.push({dark_background_content:true, native_theme_ui_tested:false});
  await lookup('AEGEAN CIVILIZATION, PLATE I', 'AEGEAN CIVILIZATION');
  await snapshot('plate');
  if (complete) {
    const deepTopic = 'religion-and-theology/history-of-christianity/free-churches-(british-empire-and-u.s.,-including-established-church-of-scotland)';
    for (const suffix of ['', '/biographies', '/subjects']) {
      const key = 'EB1911:topic:' + createHash('sha256').update(deepTopic + suffix).digest('hex').slice(0,24);
      await lookup(key, 'Established Church of Scotland');
      assert(await evaluate(`document.querySelector('.eb1911 h1').textContent.includes('Free Churches')`));
      report.checks.push({deep_topic:key, resolved:true});
    }
    const largest = JSON.parse(readFileSync('data/derived/articles/index.json','utf8'))
      .sort((a,b)=>b.body_length-a.body_length).slice(0,3);
    for (const article of largest) {
      const started = performance.now();
      await lookup('EB1911:article:' + article.filename.replace(/\.json$/, ''), article.title);
      const data = await evaluate(`({characters:document.querySelector('.eb1911 .body-text').textContent.length,
        images:[...document.querySelectorAll('.eb1911 img')].length,
        images_loaded:[...document.querySelectorAll('.eb1911 img')].every(i=>i.naturalWidth>0)})`);
      assert(data.images_loaded);
      report.checks.push({long_entry:article.title, lookup_ms:Math.round(performance.now()-started), ...data});
    }
    for (const [key, text] of [['topics','Topics'], ['contributors','Contributors'], ['volumes','Volumes'], ['introduction','Introduction and prefaces'], ['page:guide.xhtml','Guide']]) {
      await lookup('EB1911:' + key, text);
      assert(await evaluate(`document.querySelectorAll('.eb1911 a').length>0`));
      report.checks.push({navigation:key, rendered:true});
    }
    await snapshot('readers-guide');
    await evaluate(`document.querySelector('.eb1911 a[href*="guide-part"]').click()`);
    await waitFor(`document.querySelector('.eb1911 a[href*="guide-ch-"]')`);
    await evaluate(`document.querySelector('.eb1911 a[href*="guide-ch-"]').click()`);
    await waitFor(`!!document.querySelector('.eb1911 a[href*="article"]')`);
    await snapshot('guide-chapter');
    report.checks.push({guide_hierarchy:true});
  }
  report.remote_requests = network.filter(u=>/^https?:/.test(u));
  assert.equal(report.remote_requests.length, 0, 'Unexpected remote dependency');
  report.status = 'passed';
  console.log(JSON.stringify({status:report.status,checks:report.checks.length,remote_requests:0}));
} catch (e) {
  report.status='failed'; report.error=String(e);
  console.error(e); process.exitCode=1;
} finally {
  writeFileSync(`${output}/reader-qa/report.json`, JSON.stringify(report,null,2));
  await call('Network.setBlockedURLs', {urls:[]});
  ws.close();
}
