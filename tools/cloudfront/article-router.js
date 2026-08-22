// CloudFront Function (viewer-request event) for britannica11.org  /article/*  routing.
// Deploy: replace the existing `article-rewrite` function on distribution E24BJKH0IB4I6
// with this, and re-associate it to the default behavior's viewer-request. Runtime:
// cloudfront-js-2.0 (needs the `crypto` module).  NOT runnable against localhost — validate
// in the CloudFront console test tab; the hash math is unit-checked against Python below.
//
// Two jobs in one function:
//   1. FORWARD legacy URLs.  Articles used to be keyed by a section-slug id
//      (/article/{VV}-{PPPP}-{section-slug}/…).  They're now keyed by a 6-hex hash of that
//      slug (/article/{VV}-{PPPP}-{hash}/…).  A legacy id is recomputed to the hash form
//      — sha1(slug)[:6] — and 301-redirected.  Table-free: the hash is a pure function of the
//      slug already in the URL (must stay byte-identical to article_json._base_stable_id).
//   2. REWRITE the hash-form SPA URL to /viewer.html so the client renders it.
//
// The id tail after {VV}-{PPPP}- is a hash iff it matches ^[0-9a-f]{6}$; else it's a legacy
// slug to forward.  (A legacy slug that happens to be exactly 6 hex chars — e.g. "facade" —
// would be treated as already-migrated; that's the one accepted edge case.)
var crypto = require('crypto');

var HEX6 = /^[0-9a-f]{6}$/;
var ARTICLE_RE = /^\/article\/(\d{2}-\d{4})-([^\/]+)(\/[^?#]*)?$/;

// Query-string rebuild, shared by both redirect paths below.
function queryString(qs) {
  var parts = [];
  for (var k in qs) {
    if (qs[k].multiValue) {
      for (var i = 0; i < qs[k].multiValue.length; i++) parts.push(k + '=' + qs[k].multiValue[i].value);
    } else {
      parts.push(qs[k].value === '' ? k : k + '=' + qs[k].value);
    }
  }
  return parts.length ? '?' + parts.join('&') : '';
}

function handler(event) {
  var request = event.request;
  var uri = request.uri;

  // ── www → apex, 301 ────────────────────────────────────────────────────────
  // The published download bundle and the HuggingFace dataset carry
  // `https://www.britannica11.org/article/<id>` in all 37,225 records, and that
  // host had NO DNS record at all — every URL an outside consumer followed was
  // NXDOMAIN.  Pointing `www` at this distribution fixes copies ALREADY
  // downloaded, which changing the generator cannot; redirecting rather than
  // serving both keeps ONE canonical address, so search engines and citations
  // do not split between two spellings of the site.
  //
  // Needs, alongside this function: `www.britannica11.org` added to the
  // distribution's alternate domain names, and an ALIAS record for it in the
  // Route 53 zone.  The ACM certificate already carries it as a SAN.
  var host = request.headers && request.headers.host ? request.headers.host.value : '';
  if (host.indexOf('www.') === 0) {
    return {
      statusCode: 301,
      statusDescription: 'Moved Permanently',
      headers: { 'location': { value: 'https://' + host.slice(4) + uri + queryString(request.querystring) } }
    };
  }

  var m = uri.match(ARTICLE_RE);
  if (!m) {
    // Any other /article/* path (legacy numeric, malformed): just serve the SPA.
    if (uri.indexOf('/article/') === 0) request.uri = '/viewer.html';
    return request;
  }

  var vp = m[1];             // "VV-PPPP"
  var tail = m[2];           // hash | legacy section slug
  var rest = m[3] || '';     // "/cosmetic-name" or ""

  if (HEX6.test(tail)) {
    // Already canonical — serve the SPA shell (client routes on the hash id).
    request.uri = '/viewer.html';
    return request;
  }

  // Legacy slug → recompute the hash, 301 to the canonical URL (preserving the query string).
  var hash = crypto.createHash('sha1').update(tail).digest('hex').substring(0, 6);
  var query = queryString(request.querystring);   // one spelling, shared with the www redirect

  return {
    statusCode: 301,
    statusDescription: 'Moved Permanently',
    headers: { 'location': { value: '/article/' + vp + '-' + hash + rest + query } }
  };
}
