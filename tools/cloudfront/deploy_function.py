"""Deploy tools/cloudfront/strip-search-prefix.js to the CloudFront Function of
the same name — tested BEFORE it goes live.

    uv run --with boto3 python tools/cloudfront/deploy_function.py          # test only
    uv run --with boto3 python tools/cloudfront/deploy_function.py --publish

1. Upload the source to the function's DEVELOPMENT stage (LIVE is untouched).
2. Run CloudFront's own test harness against DEVELOPMENT with the cases below;
   every case must give the expected verdict.
3. Only with --publish, and only if every case passed: publish DEVELOPMENT to
   LIVE.  The distribution already uses this function, so publishing is the
   change; rollback is re-publishing the previous code (printed before upload).
"""
import json
import sys
from pathlib import Path

import boto3

NAME = "strip-search-prefix"
SOURCE = Path(__file__).with_name("strip-search-prefix.js")

# (method, uri as the viewer sends it) -> expected: forwarded uri, or 403
CASES = [
    ("POST", "/search-api/indexes/articles/search", "/indexes/articles/search"),
    ("OPTIONS", "/search-api/indexes/articles/search", "/indexes/articles/search"),
    ("GET", "/search-api/health", "/health"),
    ("GET", "/search-api/keys", 403),
    ("GET", "/search-api/version", 403),
    ("DELETE", "/search-api/indexes/articles", 403),
    ("POST", "/search-api/indexes/articles/documents", 403),
    ("PATCH", "/search-api/indexes/articles/settings", 403),
    ("GET", "/search-api/indexes/articles/search", 403),
    ("GET", "/search-api/", 403),
    ("GET", "/article/01-0035-09906e", "/article/01-0035-09906e"),   # other paths untouched
]


def event(method, uri):
    return json.dumps({"version": "1.0", "context": {"eventType": "viewer-request"},
                       "viewer": {"ip": "198.51.100.1"},
                       "request": {"method": method, "uri": uri, "querystring": {},
                                   "headers": {}, "cookies": {}}}).encode()


cf = boto3.client("cloudfront")
live = cf.get_function(Name=NAME, Stage="LIVE")
print("== current LIVE code (for rollback):\n" + live["FunctionCode"].read().decode())
desc = cf.describe_function(Name=NAME, Stage="DEVELOPMENT")
config = desc["FunctionSummary"]["FunctionConfig"]
etag = desc["ETag"]
up = cf.update_function(Name=NAME, IfMatch=etag, FunctionCode=SOURCE.read_bytes(),
                        FunctionConfig={"Comment": config.get("Comment", ""),
                                        "Runtime": config["Runtime"]})
etag = up["ETag"]
print("uploaded to DEVELOPMENT")

failures = 0
for method, uri, want in CASES:
    r = cf.test_function(Name=NAME, IfMatch=etag, Stage="DEVELOPMENT",
                         EventObject=event(method, uri))["TestResult"]
    if r.get("FunctionErrorMessage"):
        got = "ERROR " + r["FunctionErrorMessage"]
    else:
        out = json.loads(r["FunctionOutput"])
        got = out["response"]["statusCode"] if "response" in out else out["request"]["uri"]
    ok = got == want
    failures += not ok
    print(f"  {'ok  ' if ok else 'FAIL'} {method:7} {uri:44} -> {got}")

if failures:
    sys.exit(f"{failures} case(s) failed — LIVE is unchanged")
if "--publish" in sys.argv:
    cf.publish_function(Name=NAME, IfMatch=etag)
    print("published to LIVE")
else:
    print("all cases pass; LIVE unchanged (rerun with --publish to go live)")
