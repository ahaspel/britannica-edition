// Shared Meilisearch client for full-text article search.
//
// Both index.html's main search typeahead and viewer.html's
// in-article typeahead call the same code path here.  Prior to
// extraction each page had its own inline ``runFulltext`` — duplicate
// logic with identical intent, which drifted: the plate-type
// exclusion fix landed in one file then had to be re-discovered and
// re-applied in the other.  Keeping the Meilisearch request body
// + post-filter in one place prevents recurrence of that class of
// drift.
//
// Usage:
//   const client = createSearchClient(MEILI_URL, MEILI_KEY);
//   const hits = await client.searchFulltext(q, {
//     limit: 8,
//     excludeFilenames: new Set(["alreadyShown.json", …]),
//     excludePlates: true,     // default
//   });
//
// Each hit is ``{title, filename, body}`` already post-filtered for
// substring match (case-insensitive) and caller-excluded filenames.
// Callers do their own rendering.

(function () {
  function createSearchClient(meiliUrl, meiliKey) {
    return {
      async searchFulltext(q, options) {
        options = options || {};
        const limit = options.limit || 8;
        const excludeFilenames = options.excludeFilenames || new Set();
        const excludePlates = options.excludePlates !== false;  // default true
        const body = {
          q: q,
          limit: limit,
          matchingStrategy: "all",
          attributesToRetrieve: ["title", "filename", "body"],
        };
        if (excludePlates) {
          // Plates inherit their parent article's title, so without
          // this filter searching "SHIPBUILDING" returns the main
          // article plus its plate duplicates.
          body.filter = 'NOT article_type = "plate"';
        }
        const resp = await fetch(
          `${meiliUrl}/indexes/articles/search`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "Authorization": `Bearer ${meiliKey}`,
            },
            body: JSON.stringify(body),
          });
        const data = await resp.json();
        const ql = q.toLowerCase();
        return (data.hits || [])
          .filter(h =>
            (h.body || "").toLowerCase().includes(ql)
            || (h.title || "").toLowerCase().includes(ql))
          .filter(h => !excludeFilenames.has(h.filename));
      },
    };
  }
  window.createSearchClient = createSearchClient;
})();
