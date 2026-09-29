// CloudFront Function `strip-search-prefix` (viewer-request, cloudfront-js-2.0)
// on the /search-api/* behaviour of distribution E24BJKH0IB4I6.
//
// The behaviour forwards to Meilisearch on the EC2 host.  Until 2026-09-29 this
// function only stripped the /search-api prefix, so EVERY Meilisearch endpoint
// was reachable through britannica11.org — the admin ones included — guarded by
// nothing but the key, and the master key had been committed to this public
// repository.  It is now an allow-list: the site makes exactly one kind of call
// (tools/viewer/search-api.js: POST /indexes/articles/search), plus the health
// probe.  Everything else is refused here, before it reaches the server, so no
// key — leaked or not — can reach an admin endpoint from outside.
//
// CloudFront cannot restrict the behaviour's methods to "GET, HEAD, POST" (POST
// requires all seven), so this function is the gate.  Deployed with
// tools/cloudfront/deploy_function.py; this file is the source of truth.
function handler(event) {
    var request = event.request;
    var uri = request.uri;
    if (!uri.startsWith('/search-api')) {
        return request;
    }
    uri = uri.substring(11) || '/';
    var method = request.method;
    var allowed =
        (uri === '/indexes/articles/search' && (method === 'POST' || method === 'OPTIONS')) ||
        (uri === '/health' && (method === 'GET' || method === 'HEAD'));
    if (!allowed) {
        return {
            statusCode: 403,
            statusDescription: 'Forbidden',
            headers: {'cache-control': {value: 'no-store'}}
        };
    }
    request.uri = uri;
    return request;
}
