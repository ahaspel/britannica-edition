# Rebuild Verification Checklist — 2026-04-12 (session 2)

This session produced two rebuilds' worth of fixes. The first rebuild
(this morning) is on the live site now. Items below marked **[LIVE]**
are verified or available to spot-check on britannica11.org now. Items
marked **[NEXT]** are staged in the code and will apply on the next
rebuild.

## Article structure

### Already fixed and verified on live site
- [x] BRITAIN "Geologists" restored (vol 4 — `{{SIC|Geologists}}` fix)
- [x] AUSTRIA-HUNGARY xrefs cleaned (LEOPOLD I. (EMPEROR) paren
  restored, no leaked `«LN:` markup, no EUROPE duplicate,
  EUROPE#HISTORY collapsed with EUROPE: HISTORY)
- [x] AUSTRIA-HUNGARY tables (Imports renders as HTMLTABLE like Exports;
  Raw material multi-line cell present; Sanitary Service row has 5
  cells)
- [x] ALGAE, BREWING: subsections absorbed into parent article
- [x] STRAFFORD, EARLS OF contains Thomas Wentworth bio
- [x] Major merged articles: BRITAIN, UNITED STATES, DRAMA, PHILOLOGY,
  STRAFFORD
- [x] ROPE plates have "Fig. 9. Rope-making, Pottinger Mill." etc.
- [x] CROWD Figs 1–3 with bundled captions (illustration-wrapper unwrap)
- [x] Vol 20 scans show correct DLI Bengal content
- [x] Volume browse sorted by reading order

### Staged for next rebuild

- [ ] **SUCCINIC ACID (vol 26)** — title no longer leaks `<big>` HTML
  tags. `_strip_templates` now strips `<big>`, `<small>`, `<sub>`,
  `<sup>`, `<span>`, `<font>`.
- [ ] **WEIGHING MACHINES (vol 28)** — Figs 10, 11, 12, 14 now render
  with images. Raw wikitext used `{{raw image|…}}` + `{{c|{{sc|Fig. N.}}}}`
  on a following line; now converted to `[[File:…]]` + caption-matched
  properly.
- [ ] **CLEMENT (POPES) (vol 6)** — contains Clement I through XIV as
  *navigable* subsections. CLEMENT XII no longer a separate article
  (relaxed first-word rule). The "Yet Clement" / "entertained high hopes"
  mid-sentence break across pages 502→503 is repaired (sections now
  flow in correct page order, not reordered by prefix-first processing).
  Each pope's name renders as an `<h3>` heading with `id="section-..."`.
- [ ] **ROOSEVELT, THEODORE / PIETAS / SEMMELWEISS** — title no longer
  duplicated at start of body. `_fix_swallowed_pages` now strips the
  leading `'''[[Author:…]]'''` bold heading from the first moved
  segment.
- [ ] **BEE, CROWD** — search-result snippet / `body_start` no longer
  shows raw `{{IMG:…}}` marker. article_json and index_search skip IMG,
  TABLE, VERSE, HTMLTABLE, SEC markers and pick the first real
  paragraph.
- [ ] **ALGAE, BREWING** — absorbed subsections (CYANOPHYCEAE,
  PHAEOPHYCEAE, TRADE, MATERIALS, etc.) render as navigable `<h3>`
  section headings with IDs. In-article ToC includes them.
- [ ] Regnal-numeral titles: **ALEXANDER I, II, III** (and same for
  ABBAS, HENRY, GEORGE, LOUIS, FRANCIS, FREDERICK, JOHN, PHILIP, ÆTHELRED
  etc.) now get proper titles with the Roman numeral, not just the
  stem. ~70 new correctly-titled articles corpus-wide.
- [ ] **CANARY ISLANDS** (was CANARY ISLANDS_P1) — `_p1` part marker
  suffix stripped from section IDs.
- [ ] **JADE (BAY)** (was JADE_(BAY)) — underscore-as-space fixed in
  section IDs.

## Page numbers

### Live on site
- [x] Anchors (first/last article leaf per volume) verified by user
- [x] printed_pages.json and printed_pages_leaf.json deployed
  (heading-sourced, 100% agreement with Wikisource headings, monotonic
  interpolation for gaps)
- [x] Vol 20 scan_map fixed to identity (DLI Bengal)
- [x] Scan viewer looks up by leaf (accurate labels)

### Staged for next rebuild
- [ ] Article header shows correct printed range (uses direct ws→printed
  lookup from heading-sourced map, not scan_map translation).
  Pre-fix bug: OHIO header showed `pp. 43–23`; next rebuild shows
  `pp. 25–32` or similar.

## Xrefs

### Live on site (via resolver improvements)
- [x] Resolved: ~25,013 (was 24,060 post-rebuild)
- [x] Unresolved: ~2,581 (was 3,074 pre-rebuild, 3,534 post-rebuild)
- [x] 263 xrefs resolved with specific section anchors

### Resolver strategies added this session
- Section-alias harvest: CLEMENT I → CLEMENT (POPES), CYANOPHYCEAE → ALGAE
- Section-suffix: EUROPE: HISTORY → EUROPE, GREECE: LANGUAGE → GREECE
- Strip parenthetical: JOINTS (ANATOMY) → JOINTS, ALEXANDER I. (TSAR) → ALEXANDER I
- Strip comma-qualifier: GRAIL, THE HOLY → GRAIL, NELSON, HORATIO NELSON, VISCOUNT → NELSON, HORATIO NELSON

### Staged for next rebuild
- [ ] Xref list entries with target_section now produce
  `#section-<slug>` URL fragments. Click "Clement I" → jumps to the
  Clement I section inside CLEMENT (POPES), not top of article.
- [ ] CrossReference model has `target_section` column (migration
  already ran against live DB so rebuild will populate it).

## Viewer HTML (all live now)

- [x] Scan page "← Back to article" link at top-left
- [x] Article header "vol. N, pp. X–Y" as single hyperlinked unit
- [x] Title autocomplete 5-tier ranking: exact → first-word →
  any-full-word → prefix → substring (try "paul")
- [x] Scan viewer loads leaf-keyed printed_pages for correct labels

## Remaining known issues (NOT addressed this session)

- Non-article references like PENINSULAR WAR, PARADISE LOST (29+ xrefs
  each) — these are topics covered inside other articles, not
  standalone article titles. Would need section-anchor targeting the
  containing article.
- 'AMR-IBN-EL-ASS, 'AQĪBA BEN JOSEPH — leading-apostrophe variants
  (would need a strip-leading-punct fuzzy strategy).
- EARLY MAN IN BRITAIN AND HIS PLACE IN THE TERTIARY PERIOD etc. —
  long section references.

## Sanity checks after next rebuild

- [ ] Article count: similar to this rebuild (~35,858) with minor
  changes from regnal-title fixes
- [ ] printed_pages.json ~25,700 ws mappings, printed_pages_leaf.json
  ~26,500 leaf mappings
- [ ] Resolved xrefs: ~25,500+ (should improve further with
  regnal-title fixes and parenthetical strip working against proper
  article titles)
- [ ] 197 unit tests still pass
- [ ] Home page, volume browse, search all work
