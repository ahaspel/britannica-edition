// Canonical filename ↔ URL helpers, shared across all viewer pages.
//
// Article JSON filenames follow a stable pattern:
//   {VV}-{PPPP}-{section-slug}-{TITLE}.json
// where VV is a 2-digit volume, PPPP a 4-digit page, section-slug is
// lowercase letters / digits / hyphens, and TITLE begins with any
// character that can NOT start a section-slug (uppercase letter,
// accented capital, digit, underscore, modifier apostrophe ʼʽʿ, …).
//
// Example: "02-0775-s4-_ASHER_BEN_YEHIEL.json"
//          stable-id = "02-0775-s4", title = "_ASHER_BEN_YEHIEL"
//
// The public URL form is /article/{stable-id}/{title-lowercased}.
//
// Five viewer pages were previously duplicating this regex inline,
// and the duplicates had drifted: fixes for apostrophe-prefix titles
// had been applied to index.html + viewer.html but not contributors /
// topics / preface, so any link with an underscore or modifier-
// apostrophe title first character 403'd.  One source of truth here
// prevents that class of drift.

(function () {
  // Title first char is the complement of the section-slug char set,
  // so deterministically "not a section-slug continuation".
  const FILENAME_RE =
    /^(\d{2}-\d{4}-[a-z0-9][a-z0-9-]*?)-([^a-z0-9-].*)$/u;

  function parseFilename(filename) {
    const base = String(filename || "").replace(/\.json$/, "");
    const m = base.match(FILENAME_RE);
    if (m) return { stableId: m[1], title: m[2], base };
    return { stableId: null, title: null, base };
  }

  // filename → link URL. isLocal controls local dev vs. production.
  function filenameToUrl(filename, isLocal) {
    if (isLocal) {
      return `viewer.html?article=/data/derived/articles/${encodeURIComponent(filename)}`;
    }
    const { stableId, title, base } = parseFilename(filename);
    if (stableId) {
      return `/article/${stableId}/${title.toLowerCase()}`;
    }
    // Legacy numeric-ID fallback for pre-stable-id bookmarks.
    const page = base.replace(/^0+/, "").split("-")[0];
    const slug = base.substring(base.indexOf("-") + 1).toLowerCase();
    return `/article/${page}/${slug}`;
  }

  // /article/{stable-id}/{slug}  →  {dataBase}/{stable-id}-{SLUG}.json
  function pathnameToJsonPath(pathname, dataBase) {
    let m = pathname.match(/^\/article\/(\d{2}-\d{4}-[a-z0-9-]+)\/(.+)$/);
    if (m) {
      const id = m[1];
      const slug = decodeURIComponent(m[2]).toUpperCase();
      return `${dataBase}/${id}-${slug}.json`;
    }
    m = pathname.match(/^\/article\/(\d+)\/(.+)$/);
    if (m) {
      const id = m[1];
      const slug = decodeURIComponent(m[2]).toUpperCase();
      return `${dataBase}/${id}-${slug}.json`;
    }
    return null;
  }

  // JSON path  →  clean /article/... URL (used by history.replaceState
  // after viewer.html loads an article via ?article=… or a redirect).
  function jsonPathToCleanUrl(jsonPath, suffix) {
    suffix = suffix || "";
    const m = jsonPath.match(/\/([^/]+)\.json$/);
    if (!m) return null;
    const url = filenameToUrl(m[1] + ".json", false);
    return url + suffix;
  }

  window.BritannicaUrls = {
    parseFilename,
    filenameToUrl,
    pathnameToJsonPath,
    jsonPathToCleanUrl,
  };
})();
