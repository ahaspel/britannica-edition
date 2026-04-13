# Rebuild verification checklist (run started 2026-04-13 09:49)

## Fixes new this rebuild

### Data corrections
- [ ] **scan_map gap-fill** (`tools/fill_scan_map_gaps.py`): 7,489 ws→leaf entries filled by interpolating between consecutive same-offset anchors. Vol 24 had the worst symptoms (e.g. SEWING MACHINES "next" jumped to printed 739 SEWERAGE instead of 745). Vol 9 (497 gaps), vol 16 (506), vol 14 (447) had the biggest gap counts.
- [ ] **vol 3 scan_map**: explicit entries added for ws 15-18 → leaves 21-24 (vol 3 front matter + body offset differs from LEAF_OFFSET=9). Eliminates the duplicate printed-2/3/4 sequence at leaves 25-27.
- [ ] **printed_pages.json rebuilt** with corrected scan_map. Articles now have proper printed page ranges (e.g. WEIGHING MACHINES vol 28: 486-477 → 468-477).

### Pipeline fixes
- [ ] **`{{1911link|Target|Display}}` two-arg form** (`transform_articles.py`): regex extended from `[^{}|]*` to `[^{}|]+(?:\|([^{}]*))?`. Recovers ~2,031 instances across 897 pages that were silently dropped, leaving orphan commas (visible in AGRICULTURE's "See also" paragraph). Per article verify: `Horticulture, ,;` → `Horticulture, Fruit and Flower Farming, ...`.
- [ ] **Image+caption bundling** (`_bundle_raw_image_with_caption`): `{{raw image|X}}` (34 instances, vols 20/24/25/26/28) AND `[[File/Image:X|size|align]]` (119 instances corpus-wide) followed by `{{c|…}}` or `{|…|}` get bundled into a single `[[File:X|caption]]`. Eliminates the duplicate-caption paragraph beneath figures (was visible in WEIGHING MACHINES Fig 13, SEWING MACHINES Fig 2, etc.).
- [ ] **Defensive orphan-comma cleanup**: collapses `, , , ` → `, ` and `, ;` → `;` and `, .` → `.` at end of transform. Catches any future template-strip regressions.
- [ ] **Segment-based image extraction** (`extract_images.py`): uses `ArticleSegment.segment_text` instead of full-page wikitext. Fixes images on shared pages (e.g. vol 28 p.495 split between WEIGHING MACHINES + WEIGHTS AND MEASURES — Automatic Coal/Luggage now correctly under WEIGHING MACHINES).
- [ ] **Caption extraction from wrapper patterns** (`extract_images.py`): handles 4 wrapper forms — `<span>/<div>` with `<br>`, wikitable with caption row, loose `{{c|…}}` after image, separate wikitable with last-row caption. Fills `ArticleImage.caption` from previously-uncaptioned wrapper figures.
- [ ] **Caption sanitizer** (`_clean_caption_markup`): strips templates including `{{Fs|…|…}}` and any unhandled bare `{{template}}`, multi-attribute wikitable cell prefixes (`align="..." width="..." |`), wikilinks, stray braces.
- [ ] **Body-start title strip** (`article_json.py`): both article-file body AND index.json `body_start` strip the redundant bold article title from beginning. Fixes PIETAS / SEMMELWEISS preview text duplication.
- [ ] **Body IMG caption patching** (`article_json.py`): if an IMG marker in body lacks a caption but the `ArticleImage` table has one, patch the marker. Sanitizes `|` and `}}` to prevent template syntax corruption.

### Viewer fixes already deployed (should remain working)
- Title search 5-tier ranking (whitespace-first-word > comma-first-word).
- Autocomplete dropdown shows body_start subtitle.
- ALGAE / BREWING / CLEMENT (POPES) section TOC dedup + de-hyphenation; SEC/SH separation.
- Volume browse: "View volume scans →" link with `pinit=1` (opens at printed p.1).
- Scan viewer: leaf mode + page-jump input; printed page label only (leaf number removed).

## Spot-check targets

- **WEIGHING MACHINES**: page header "vol. 28, pp. 468-477"; 20 figures each with single Fig.N caption (no duplicates beneath).
- **SEWING MACHINES**: 7 figures, single captions.
- **AGRICULTURE**: "See also" paragraph reads cleanly: "...Horticulture, Fruit and Flower Farming, Poultry and Poultry-farming; Soil, Grass and Grassland, Manures and Manuring, Drainage of Land, Irrigation, Sowing, Reaping, Hay (fodder), Plough and Ploughing, Harrow, Thrashing." — no orphan commas.
- **Vol 24 navigation**: SEWING MACHINES p.744 → next → p.745 (not 739).
- **Vol 3 volume scans**: open at printed p.1.
- **Vol 28 navigation**: WEIGHING MACHINES → next pages stay in proper order.
- **Articles regaining lost continuation pages** (carried from prior rebuild): MECHANICS 64p, RUSSIA 46p, RAILWAYS 43p, AGRICULTURE 34p, CONDUCTION ELECTRIC 36p.
- **0 titles with `[[…]]`** in any article (was 8 before bracket-fallback fix).

## Pending after this rebuild

- Full vol 29 classified-TOC parser → "Browse by subject" UI.
- Vol 20 trailing black pages (data, Bengal scan artifact — low priority).
