"""Headlessly render an article through the live viewer and dump the
resulting body-text HTML.

Purpose: serve as the ground-truth rendering oracle for regression
tests. Whatever this prints is what a reader sees in their browser,
so invariant checks built on top of this output are checks against
the actual user experience rather than intermediate transform state.

Prerequisites:
* The local dev webserver must be running on port 8000 from the
  project root (standard EB1911 dev setup).
* ``uv run playwright install chromium`` has been run once.

Usage:
    uv run python tools/qa/render_article.py 20-0196-s4-ORCHIDS
    uv run python tools/qa/render_article.py 20-0196-s4-ORCHIDS.json
    uv run python tools/qa/render_article.py --outer 27-0028-s3-TOOL

With ``--outer`` the whole article card is dumped, not just the body.
Useful when debugging surrounding elements (xrefs, footnotes, scan
links) — but for paragraph-level invariants ``--body`` (default) is
what you want.

Programmatic use (batch scanner):
    from render_article import Renderer
    with Renderer() as r:
        for name in fixtures:
            html = r.render(name)

The ``Renderer`` context manager keeps a single browser+page across
calls, which reduces per-article cost from ~3s (fresh launch) to
~0.5s (same browser, same page) — a 6× speedup when scanning many
articles.

Exit code 0 on success, nonzero if the viewer rejected the article
or failed to render within the timeout.
"""
from __future__ import annotations

import argparse
import sys
from urllib.parse import quote

from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

BASE_URL = "http://localhost:8000"
VIEWER_PATH = "/tools/viewer/viewer.html"
DEFAULT_ARTICLE_PATH = "/data/derived/articles"


def article_url(filename: str,
                base_path: str = DEFAULT_ARTICLE_PATH) -> str:
    if not filename.endswith(".json"):
        filename = filename + ".json"
    path = f"{base_path.rstrip('/')}/{filename}"
    return f"{BASE_URL}{VIEWER_PATH}?article={quote(path, safe='')}"


class Renderer:
    """Keeps a single browser+page open across many article renders.

    Use as a context manager when scanning multiple articles — cuts
    per-article cost roughly 6× by skipping the browser-launch and
    context-creation overhead on each call.
    """
    def __init__(self, timeout_ms: int = 20000,
                 base_path: str = DEFAULT_ARTICLE_PATH):
        self.timeout_ms = timeout_ms
        self.base_path = base_path
        self._pw = None
        self._browser = None
        self._page = None

    def __enter__(self) -> "Renderer":
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=True)
        return self

    def __exit__(self, *exc):
        try:
            if self._browser:
                self._browser.close()
        finally:
            if self._pw:
                self._pw.stop()

    def render(self, filename: str, outer: bool = False) -> str:
        assert self._browser is not None, "Use Renderer as a context manager"
        # Fresh context + page per article — avoids state leaks across
        # navigations (previous article's ``.body-text`` lingering into
        # the next load, handlers piling up, etc.). Browser stays up so
        # the per-article cost is still far lower than launching a
        # browser from scratch each time.
        ctx = self._browser.new_context()
        page = ctx.new_page()
        url = article_url(filename, base_path=self.base_path)
        errors: list[str] = []
        page.on("pageerror", lambda err: errors.append(f"pageerror: {err}"))
        try:
            # ``domcontentloaded`` returns as soon as the HTML is parsed;
            # the article JSON fetch + render happens after that. Using
            # ``load`` or ``networkidle`` can hang indefinitely when any
            # referenced image 404s (especially in baseline S3 renders
            # where local images differ from what the article file
            # expects).
            page.goto(url, timeout=self.timeout_ms,
                      wait_until="domcontentloaded")
            # Wait for the article renderer to populate ``.body-text``.
            # This is the true "render complete" signal.
            page.wait_for_selector(".body-text", state="attached",
                                    timeout=self.timeout_ms)
            selector = "#app" if outer else ".body-text"
            return page.eval_on_selector(selector, "el => el.innerHTML")
        except PwTimeout as e:
            diag = f"TIMEOUT rendering {filename}: {e}"
            for line in errors[-5:]:
                diag += f"\n  {line}"
            raise RuntimeError(diag)
        finally:
            ctx.close()


def render(filename: str, outer: bool = False,
           timeout_ms: int = 20000) -> str:
    """One-shot convenience — launches a browser per call.

    Fine for single-article use. For scanning many articles, use the
    ``Renderer`` context manager to reuse one browser.
    """
    with Renderer(timeout_ms=timeout_ms) as r:
        return r.render(filename, outer=outer)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("filename",
                    help="Article filename (e.g. 20-0196-s4-ORCHIDS) "
                         "with or without .json extension.")
    ap.add_argument("--outer", action="store_true",
                    help="Dump the entire article card, not just "
                         "the body-text region.")
    ap.add_argument("--timeout", type=int, default=20000,
                    help="Per-step timeout in ms (default 20000).")
    args = ap.parse_args()
    try:
        html = render(args.filename, outer=args.outer,
                       timeout_ms=args.timeout)
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 2
    print(html)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
