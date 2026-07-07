// Shared jsdom environment that runs the REAL viewer.html decode headless.
// ONE owner for the stubs (the interactive/network layer we do NOT port): fetch,
// katex (→ a placeholder = the math normalization), article-urls.js's BritannicaUrls,
// search.  Used by every reference generator (reference.js, inline_ref.js).
const fs = require('fs');
const path = require('path');
const { JSDOM, VirtualConsole } = require('jsdom');

const VIEWER_HTML = fs.readFileSync(
  path.join(__dirname, '..', 'viewer', 'viewer.html'), 'utf-8');

function makeWindow() {
  const dom = new JSDOM(VIEWER_HTML, {
    runScripts: 'dangerously',
    pretendToBeVisual: true,
    virtualConsole: new VirtualConsole(),        // swallow stubbed-away init noise
    url: 'http://localhost/',
    beforeParse(w) {
      w.fetch = () => new Promise(() => {});                          // no network
      w.katex = { renderToString: () => '«MATHPH»' };       // math normalization
      w.BritannicaUrls = {                                            // from article-urls.js
        filenameToUrl: (f) => '/article/' + f,
        parseFilename: (f) => ({ page: '', slug: f }),
        pathnameToJsonPath: () => null,
        jsonPathToCleanUrl: (p) => p,
      };
      w.createSearchClient = () => ({ search: () => Promise.resolve({ hits: [] }) });
      w.IntersectionObserver = class { observe() {} disconnect() {} unobserve() {} };
      w.matchMedia = () => ({ matches: false, addListener() {}, addEventListener() {} });
    },
  });
  return dom.window;
}

module.exports = { makeWindow };
