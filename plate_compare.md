# Plate parser regression report

- Baseline: `tools\diagnostics\plate_baseline.json`
- Plates rendered: **328**

## Verdict breakdown

| category | count |
|---|---|
| 🔽 regression | 0 |
| 🟡 mixed | 0 |
| ↔ equal scores, different output | 0 |
| 🟢 better | 0 |
| ✅ identical | 328 |

## Quality signals (totals across all plates)

| signal | baseline | current | delta |
|---|---|---|---|
| images | 1235 | 1235 | 0 |
| captioned | 1151 | 1151 | 0 |
| legends | 102 | 102 | 0 |
| broken_caps | 0 | 0 | 0 |
| header_present | 69 | 69 | 0 |
| footer_present | 56 | 56 | 0 |
| header_leak | 0 | 0 | 0 |
| footer_leak | 0 | 0 | 0 |
| header_cap_shape | 0 | 0 | 0 |
| footer_cap_shape | 2 | 2 | 0 |

## Signatures in this report

| count | signature |
|---|---|
| 69 | `wikitable depth=1 wt=1 ht=0` |
| 31 | `wikitable depth=1 wt=1 ht=0 has_colspan` |
| 31 | `html_table depth=0 wt=0 ht=1` |
| 28 | `wikitable depth=1 wt=multi ht=0` |
| 28 | `wikitable depth=2 wt=multi ht=0 has_colspan` |
| 20 | `html_table depth=0 wt=0 ht=1 has_colspan` |
| 15 | `html_table depth=0 wt=0 ht=multi` |
| 14 | `center_template depth=0 wt=0 ht=0 toplegend` |
| 12 | `wikitable depth=2 wt=multi ht=0` |
| 12 | `center_template depth=0 wt=0 ht=0` |
| 11 | `bare_image depth=0 wt=0 ht=0` |
| 9 | `wikitable depth=1 wt=multi ht=0 has_colspan` |
| 9 | `html_table depth=0 wt=0 ht=multi has_colspan` |
| 5 | `c_centered depth=0 wt=0 ht=0 toplegend` |
| 5 | `html_table depth=0 wt=0 ht=1 toplegend` |
| 5 | `wikitable depth=3 wt=multi ht=0 has_colspan` |
| 5 | `other depth=0 wt=0 ht=0 no_image` |
| 3 | `other depth=0 wt=0 ht=0` |
| 3 | `other depth=0 wt=0 ht=0 toplegend` |
| 2 | `illustration_html depth=0 wt=0 ht=multi has_illus` |
| 2 | `other depth=0 wt=0 ht=1` |
| 2 | `html_table depth=0 wt=0 ht=1 has_colspan toplegend` |
| 1 | `wikitable depth=3 wt=multi ht=0 toplegend` |
| 1 | `html_table depth=0 wt=0 ht=multi has_colspan toplegend` |
| 1 | `html_table depth=0 wt=0 ht=multi toplegend` |
| 1 | `wikitable depth=1 wt=1 ht=0 toplegend` |
| 1 | `wikitable depth=3 wt=multi ht=0` |
| 1 | `center_template depth=0 wt=0 ht=0 no_image` |
| 1 | `wikitable depth=4 wt=multi ht=0` |

---
## AEGEAN CIVILIZATION, PLATE I — vol 01

**Article ID:** 4186298  
**Signature:** `wikitable depth=1 wt=multi ht=0 has_colspan`

### Source excerpt
```
{{rh||{{larger|GRAPHIC ART}}|{{smaller|{{sc|Plate I.}}}}}}
{|align="center" cellpadding="3" cellspacing="0"
|[[File:1911 Britannica - Aegean - Phylakopi.png|center|500px|]] || [[File:1911 Britannica - Aegean -Tiryns.png|center|500px|]]
|-
|align="center"|{{sc|Fig. 1.}}&mdash; FLYING FISH FRESCO, PHYLAKOPI.
|align="center"|{{sc|Fig. 2.}}&mdash; BULL, WITH LEAPING BULL-FIGHTER, TIRYNS.
|-
|align="center"| {{smaller|Cf. ''J. H. S.'' Suppl. Papers, iv.}}
|align="center"| {{smaller|Cf. Schliemann, ''Tiryns'', Plate XIII.}}
|}
{| {{ts|mc|width:800px}}
|-
| {{ts|pr1|vtp|width:33%}} |<br /><br /><br /><br /><br />
[[File:1911 Britannica - Aegean -Lamp Stand.png|center|310px|]]
{{c|{{lh|88%|{{sc|Fig. 3.}}&mdash; LAMP-STAND, PHYLAKOPI.<br />{{smaller|Cf. ''J. H. S.'' Suppl. Papers, iv. Plate XXII.}}}}}}
| {{ts|pl1|vtp|width:34%}} |<br />
[[File:1911 Britannica - Aegean -Cnossus.png|center|340px|]]
{{c|{{lh|88%|{{sc|Fig. 4.}}&mdash; MIDDLE MINOAN VASE, CNOSSUS.<br />{{smaller|''B. S. A.'' ix. 120, Fig. 75}}}}}}
<br />
[[File:1911 Britannica - Aegean - Cnossus1.png|center|340px|]]
{{c|{{lh|88%|{{sc|Fig. 5.}}&mdash; MINIATURE FRESCOES, SHOWING SPECTATORS AT ATHLETIC SPORTS, CNOSSUS.<br />{{smaller|From Photo by Dr A. J. Evans.}}}}}}
| {{ts|pr1|vtp|width:33%}} |<br /><br /><br /><br />
[[File:1911 Britannica - Aegean - Zakro.png|right|310px|]]
{{c|{{lh|88%|{{sc|Fig. 6.}}&mdash; FILLER VASE, ZAKRO.<br />{{smaller|''J. H. S.'' vol. xxii. Plate XII.}}}}}}
|-
|align="right" colspan="3"|{{sm|By
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 6 | 6 |
| captioned       | 6 | 6 |
| legends         | 2 | 2 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **16** | **16** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | 'By permission of the Society for the Promotion of Hellenic Studies' | 'By permission of the Society for the Promotion of Hellenic Studies' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica - Aegean - Phylakopi.png|FLYING FISH FRESCO, PHYLAKOPI}}

{{IMG:1911 Britannica - Aegean -Tiryns.png|BULL, WITH LEAPING BULL-FIGHTER, TIRYNS}}

{{IMG:1911 Britannica - Aegean -Lamp Stand.png|LAMP-STAND, PHYLAKOPI. Cf. J. H. S. Suppl. Papers, iv. Plate XXII}}

{{IMG:1911 Britannica - Aegean -Cnossus.png|MIDDLE MINOAN VASE, CNOSSUS. B. S. A. ix. 120, Fig. 75}}

{{IMG:1911 Britannica - Aegean - Cnossus1.png|MINIATURE FRESCOES, SHOWING SPECTATORS AT ATHLETIC SPORTS, CNOSSUS. From Photo by Dr A. J. Evans}}

{{IMG:1911 Britannica - Aegean - Zakro.png|FILLER VASE, ZAKRO. J. H. S. vol. xxii. Plate XII}}

{{LEGEND:Cf. J. H. S. Suppl. Papers, iv}LEGEND}

{{LEGEND:Cf. Schliemann, Tiryns, Plate XIII}LEGEND}

By permission of the Society for the Promotion of Hellenic Studies
```

### Current body
```
{{IMG:1911 Britannica - Aegean - Phylakopi.png|FLYING FISH FRESCO, PHYLAKOPI}}

{{IMG:1911 Britannica - Aegean -Tiryns.png|BULL, WITH LEAPING BULL-FIGHTER, TIRYNS}}

{{IMG:1911 Britannica - Aegean -Lamp Stand.png|LAMP-STAND, PHYLAKOPI. Cf. J. H. S. Suppl. Papers, iv. Plate XXII}}

{{IMG:1911 Britannica - Aegean -Cnossus.png|MIDDLE MINOAN VASE, CNOSSUS. B. S. A. ix. 120, Fig. 75}}

{{IMG:1911 Britannica - Aegean - Cnossus1.png|MINIATURE FRESCOES, SHOWING SPECTATORS AT ATHLETIC SPORTS, CNOSSUS. From Photo by Dr A. J. Evans}}

{{IMG:1911 Britannica - Aegean - Zakro.png|FILLER VASE, ZAKRO. J. H. S. vol. xxii. Plate XII}}

{{LEGEND:Cf. J. H. S. Suppl. Papers, iv}LEGEND}

{{LEGEND:Cf. Schliemann, Tiryns, Plate XIII}LEGEND}

By permission of the Society for the Promotion of Hellenic Studies
```

---

## AEGEAN CIVILIZATION, PLATE II — vol 01

**Article ID:** 4186299  
**Signature:** `wikitable depth=1 wt=multi ht=0`

### Source excerpt
```
{{rh|{{smaller|{{sc|Plate II.}}}}|{{larger|PLASTIC ART}}|}}
{| {{ts|mc|width:1000px}}
|-
|[[File:1911 Britannica - Aegean - Cnossus2.png|center|450px|]]{{center|{{sc|Fig. 1.}}&mdash; FAÏENCE PLAQUE, CNOSSUS.<br />{{smaller|''B. S. A.'' ix. Plate III.}}}}
|[[File:1911 Britannica - Aegean - Marble Idols.png|center|450px|]]{{center|{{sc|Fig. 2.}}&mdash; MARBLE IDOLS, AMORGOS; 6-11; FIDDLE<br /> AND MALLET TYPES, 12-14, DEVELOPED TYPES.<br />{{smaller|''Man'', 1901, 185, No 146<br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;By permission of the Royal Anthropological Institute}}}}<br /><br />
|}
{| {{ts|mc|width:1000px}}
|-
|[[File:1911 Britannica - Aegean - Male Torso.png|center|320px|]]{{center|{{sc|Fig. 3.}}&mdash; COLOURED BAS-RELIEF IN GESSO<br /> DURO, REPRESENTING MALE TORSO<br /> WITH FLEUR-DE-LIS COLLAR.<br />{{smaller|''B. S. A.'' vii. 17 Fig. 6.}}}}
|[[File:1911 Britannica - Aegean - Marble Head.png|center|160px|]]{{center|{{sc|Fig. 4.}}&mdash; MARBLE HEAD<br /> FROM AMORGOS (ASH-<br />MOLEAN MUSEUM).}}
|[[File:1911 Britannica - Aegean - Cnossus3.png|center|350px|]]{{center|{{sc|Fig. 5.}}&mdash; BULL IN PAINTED PLASTER, CNOSSUS.<br />
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 7 | 7 |
| captioned       | 7 | 7 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **14** | **14** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica - Aegean - Cnossus2.png|FAÏENCE PLAQUE, CNOSSUS. B. S. A. ix. Plate III}}

{{IMG:1911 Britannica - Aegean - Marble Idols.png|MARBLE IDOLS, AMORGOS; 6-11; FIDDLE AND MALLET TYPES, 12-14, DEVELOPED TYPES. Man, 1901, 185, No 146 By permission of the Royal Anthropological Institute}}

{{IMG:1911 Britannica - Aegean - Male Torso.png|COLOURED BAS-RELIEF IN GESSO DURO, REPRESENTING MALE TORSO WITH FLEUR-DE-LIS COLLAR. B. S. A. vii. 17 Fig. 6}}

{{IMG:1911 Britannica - Aegean - Marble Head.png|MARBLE HEAD FROM AMORGOS (ASH- MOLEAN MUSEUM)}}

{{IMG:1911 Britannica - Aegean - Cnossus3.png|BULL IN PAINTED PLASTER, CNOSSUS. Photo by Dr A. J. Evans}}

{{IMG:1911 Britannica - Aegean - Cnossus4.png|Figs 6, 7— IVORY FIGURES AND HEADS OF ATHLETS, BULL-FIGHTERS OR ACROBATS, CNOSSUS}}

{{IMG:1911 Britannica - Aegean - Cnossus5.png|Plates II, and III, and p. 72 sq. By permission of the Society for the Promotion of Hellenic Studies}}
```

### Current body
```
{{IMG:1911 Britannica - Aegean - Cnossus2.png|FAÏENCE PLAQUE, CNOSSUS. B. S. A. ix. Plate III}}

{{IMG:1911 Britannica - Aegean - Marble Idols.png|MARBLE IDOLS, AMORGOS; 6-11; FIDDLE AND MALLET TYPES, 12-14, DEVELOPED TYPES. Man, 1901, 185, No 146 By permission of the Royal Anthropological Institute}}

{{IMG:1911 Britannica - Aegean - Male Torso.png|COLOURED BAS-RELIEF IN GESSO DURO, REPRESENTING MALE TORSO WITH FLEUR-DE-LIS COLLAR. B. S. A. vii. 17 Fig. 6}}

{{IMG:1911 Britannica - Aegean - Marble Head.png|MARBLE HEAD FROM AMORGOS (ASH- MOLEAN MUSEUM)}}

{{IMG:1911 Britannica - Aegean - Cnossus3.png|BULL IN PAINTED PLASTER, CNOSSUS. Photo by Dr A. J. Evans}}

{{IMG:1911 Britannica - Aegean - Cnossus4.png|Figs 6, 7— IVORY FIGURES AND HEADS OF ATHLETS, BULL-FIGHTERS OR ACROBATS, CNOSSUS}}

{{IMG:1911 Britannica - Aegean - Cnossus5.png|Plates II, and III, and p. 72 sq. By permission of the Society for the Promotion of Hellenic Studies}}
```

---

## AEGEAN CIVILIZATION, PLATE III — vol 01

**Article ID:** 4186300  
**Signature:** `wikitable depth=1 wt=multi ht=0`

### Source excerpt
```
{{rh||{{larger|RELIGION}}|{{smaller|{{sc|Plate III.}}}}}}
{| {{ts|mc|width:900px}}
|-
|[[File:1911 Britannica - Aegean - Cnossus6.png|center|320px|]] || [[File:1911 Britannica - Aegean - Crete.png|center|240px|]] || [[File:1911 Britannica - Aegean - Acropolis.png|center|330px|]]
|-
|align="center"|{{sc|Fig. 1.}}&mdash; LION-GUARDED GODDESS AND SHRINE, ON A CLAY SEALING FROM CNOSSUS.<br /><small>''B. S. A.'' vii. 29. Fig. 9.</small><br /><br /><br />
|align="center"|{{sc|Fig. 2.}}&mdash; MALE DIVINITY BETWEEN LIONS, ON A LENTOID GEM FROM KYDONIA, CRETE.<br /><small> ''J. H. S.'' xxi, 163, Fig. 43.</small><br /><br />
|align="center"|{{sc|Fig. 3.}}&mdash; GOLD SIGNET FROM ACROPOLIS TREASURE, MYCENAE, SHOWING THE GODDESS BENEATH A SACRED TREE, WITH ADORANTS AND SACRED EMBLEMS.<br /><small>''J. H. S.'' xxi, 108, Fig. 4.</small>
|}
{| {{ts|mc|width:900px}}
|-
|[[File:1911 Britannica - Aegean - Cnossus7.png|center|280px|]]{{center|{{sc|Fig. 4.}}&mdash; BIRDS ON A TRIAD OF PILLARS, CNOSSUS.<br /><small>''B. S. A.'' viii. 29, Fig. 14.</small>}}
|[[File:1911 Britannica - Aegean - Minotaur.png|center|600px|]]{{center|{{sc|Fig. 5.}}&mdash; CLAY SEALING FROM ZAKRO, WITH MINOTAUR TYPES.<br /><small>''B. S. A.'' viii. 133, Fig. 45.</small>}}
|}
{| {{ts|mc|width:900px}}
|-
| {{ts|pr1|vtp|width:50%}} |
[[File:1911 Britannica - Aegean - Cnossus9.png|center|460px|]]
{{c|{{lh|88%|{{sc|Fig. 7.}}&mdash; FAÏENCE FIGURE OF THE GODDESS, WITH SERPENT ATTRIBUTES, CNOSSUS.<br /><small>''B. S. A.'' ix. 
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 8 | 8 |
| captioned       | 8 | 8 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **16** | **16** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica - Aegean - Cnossus6.png|LION-GUARDED GODDESS AND SHRINE, ON A CLAY SEALING FROM CNOSSUS. B. S. A. vii. 29. Fig. 9}}

{{IMG:1911 Britannica - Aegean - Crete.png|MALE DIVINITY BETWEEN LIONS, ON A LENTOID GEM FROM KYDONIA, CRETE. J. H. S. xxi, 163, Fig. 43}}

{{IMG:1911 Britannica - Aegean - Acropolis.png|GOLD SIGNET FROM ACROPOLIS TREASURE, MYCENAE, SHOWING THE GODDESS BENEATH A SACRED TREE, WITH ADORANTS AND SACRED EMBLEMS. J. H. S. xxi, 108, Fig. 4}}

{{IMG:1911 Britannica - Aegean - Cnossus7.png|BIRDS ON A TRIAD OF PILLARS, CNOSSUS. B. S. A. viii. 29, Fig. 14}}

{{IMG:1911 Britannica - Aegean - Minotaur.png|CLAY SEALING FROM ZAKRO, WITH MINOTAUR TYPES. B. S. A. viii. 133, Fig. 45}}

{{IMG:1911 Britannica - Aegean - Cnossus9.png|FAÏENCE FIGURE OF THE GODDESS, WITH SERPENT ATTRIBUTES, CNOSSUS. B. S. A. ix. 75, Fig. 54}}

{{IMG:1911 Britannica - Aegean - Cnossus8.png|DUAL PILLAR WORSHIP, ON A GOLD SIGNET RING, CNOSSUS. J. H. S. xxi. 170, Fig. 48}}

{{IMG:1911 Britannica - Aegean - Cnossus10.png|FAÇADE OF SMALL TEMPLES, COMPLETED FROM A FRESCO PAINTING, CNOSSUS. J. H. S. xxi. 193, Fig. 66. By permission of the Society for the Promotion of Hellenic Studies}}
```

### Current body
```
{{IMG:1911 Britannica - Aegean - Cnossus6.png|LION-GUARDED GODDESS AND SHRINE, ON A CLAY SEALING FROM CNOSSUS. B. S. A. vii. 29. Fig. 9}}

{{IMG:1911 Britannica - Aegean - Crete.png|MALE DIVINITY BETWEEN LIONS, ON A LENTOID GEM FROM KYDONIA, CRETE. J. H. S. xxi, 163, Fig. 43}}

{{IMG:1911 Britannica - Aegean - Acropolis.png|GOLD SIGNET FROM ACROPOLIS TREASURE, MYCENAE, SHOWING THE GODDESS BENEATH A SACRED TREE, WITH ADORANTS AND SACRED EMBLEMS. J. H. S. xxi, 108, Fig. 4}}

{{IMG:1911 Britannica - Aegean - Cnossus7.png|BIRDS ON A TRIAD OF PILLARS, CNOSSUS. B. S. A. viii. 29, Fig. 14}}

{{IMG:1911 Britannica - Aegean - Minotaur.png|CLAY SEALING FROM ZAKRO, WITH MINOTAUR TYPES. B. S. A. viii. 133, Fig. 45}}

{{IMG:1911 Britannica - Aegean - Cnossus9.png|FAÏENCE FIGURE OF THE GODDESS, WITH SERPENT ATTRIBUTES, CNOSSUS. B. S. A. ix. 75, Fig. 54}}

{{IMG:1911 Britannica - Aegean - Cnossus8.png|DUAL PILLAR WORSHIP, ON A GOLD SIGNET RING, CNOSSUS. J. H. S. xxi. 170, Fig. 48}}

{{IMG:1911 Britannica - Aegean - Cnossus10.png|FAÇADE OF SMALL TEMPLES, COMPLETED FROM A FRESCO PAINTING, CNOSSUS. J. H. S. xxi. 193, Fig. 66. By permission of the Society for the Promotion of Hellenic Studies}}
```

---

## AEGEAN CIVILIZATION, PLATE IV — vol 01

**Article ID:** 4186301  
**Signature:** `wikitable depth=1 wt=multi ht=0`

### Source excerpt
```
{{rh|{{smaller|{{sc|Plate IV.}}}}|{{larger|TYPES AND COSTUMES, ETC.}}|}}
{| {{ts|mc|width:1000px}}
|-
|[[File:1911 Britannica - Aegean - Cnossus11.png|center|600px|]] || [[File:1911 Britannica - Aegean - Cnossus12.png|center|285px|]]
|-
|align="center"|{{sc|Fig. 1.}}&mdash; TESSERAE OF PORCELAIN MOSAIC IN FORM OF HOUSES<br /> AND TOWERS, CNOSSUS. &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<small>''B. S. A.'' viii. 15, Fig. 8.</small>
|align="center"|{{sc|Fig. 2.}}&mdash; CUP-BEARER, CNOSSUS.<br /><small> Photo by Dr A. J. Evans.</small>
|}
<br />
{| {{ts|mc|width:1000px}}
|-
|[[File:1911 Britannica - Aegean - Spata.png|center|270px|]]{{center|{{sc|Fig. 3, 5.}}&mdash; IVORY HEADS FROM SPATA (ATTICA).<br /><small>Reichel, ''Homerische Waffen'', 1901, p. 103<br />By permission of A. Hölder, Vienna.</small>}}
|[[File:1911 Britannica - Aegean - Cnossus13.png|center|270px|]]{{center|{{sc|Fig. 4.}}&mdash; FRESCO PAINTING OF GIRL, CNOSSUS.<br /><small>''B. S. A.'' vii. 57, Fig. 17.</small>}}<br />
|[[File:1911 Britannica - Aegean - Spata1.png|center|270px|]]{{center|{{sc|Fig. 5.}}&mdash; See {{sc|Fig. 3.}}}}<br /><br />
|}
{| {{ts|mc|width:1000px}}
|-
|[[File:1911 Britannica - Aegean - Cnossus14.png|center|400px|]]||{{sc|Fig. 6.}}&mdash; FAÏENCE FIGURE<br /> OF FEMALE VOTARY<br /> OF SNAKE-GODDESS,<br /> CNOSSUS.<br /><small>''B. S. A.'' ix. 77, Fig. 56.</small><br /><br /><br /><br /><br /><br />{{sc|Fig. 7.}}&mdash; KEFTIU (CRETAN)<br /> BEARING AEGEAN<br /> VASE AS TRIBUTE TO
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 7 | 7 |
| captioned       | 7 | 7 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **14** | **14** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica - Aegean - Cnossus11.png|TESSERAE OF PORCELAIN MOSAIC IN FORM OF HOUSES AND TOWERS, CNOSSUS. B. S. A. viii. 15, Fig. 8}}

{{IMG:1911 Britannica - Aegean - Cnossus12.png|CUP-BEARER, CNOSSUS. Photo by Dr A. J. Evans}}

{{IMG:1911 Britannica - Aegean - Spata.png|IVORY HEADS FROM SPATA (ATTICA). Reichel, Homerische Waffen, 1901, p. 103 By permission of A. Hölder, Vienna}}

{{IMG:1911 Britannica - Aegean - Cnossus13.png|FRESCO PAINTING OF GIRL, CNOSSUS. B. S. A. vii. 57, Fig. 17}}

{{IMG:1911 Britannica - Aegean - Spata1.png|See Fig. 3}}

{{IMG:1911 Britannica - Aegean - Cnossus14.png|FAÏENCE FIGURE OF FEMALE VOTARY OF SNAKE-GODDESS, CNOSSUS. B. S. A. ix. 77, Fig. 56. Fig. 7. — KEFTIU (CRETAN) BEARING AEGEAN VASE AS TRIBUTE TO PHARAOH. From H. R. Hall, Oldest Civilization in Greece (1901). By permission of the Society for the Promotion of Hellenic Studies}}

{{IMG:1911 Britannica - Aegean - Keftiu.png|TYPES AND COSTUMES, ETC}}
```

### Current body
```
{{IMG:1911 Britannica - Aegean - Cnossus11.png|TESSERAE OF PORCELAIN MOSAIC IN FORM OF HOUSES AND TOWERS, CNOSSUS. B. S. A. viii. 15, Fig. 8}}

{{IMG:1911 Britannica - Aegean - Cnossus12.png|CUP-BEARER, CNOSSUS. Photo by Dr A. J. Evans}}

{{IMG:1911 Britannica - Aegean - Spata.png|IVORY HEADS FROM SPATA (ATTICA). Reichel, Homerische Waffen, 1901, p. 103 By permission of A. Hölder, Vienna}}

{{IMG:1911 Britannica - Aegean - Cnossus13.png|FRESCO PAINTING OF GIRL, CNOSSUS. B. S. A. vii. 57, Fig. 17}}

{{IMG:1911 Britannica - Aegean - Spata1.png|See Fig. 3}}

{{IMG:1911 Britannica - Aegean - Cnossus14.png|FAÏENCE FIGURE OF FEMALE VOTARY OF SNAKE-GODDESS, CNOSSUS. B. S. A. ix. 77, Fig. 56. Fig. 7. — KEFTIU (CRETAN) BEARING AEGEAN VASE AS TRIBUTE TO PHARAOH. From H. R. Hall, Oldest Civilization in Greece (1901). By permission of the Society for the Promotion of Hellenic Studies}}

{{IMG:1911 Britannica - Aegean - Keftiu.png|TYPES AND COSTUMES, ETC}}
```

---

## AERONAUTICS, PLATE I — vol 01

**Article ID:** 4186329  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|{{Ts|ma|ac}}
|[[File:EB1911 Aeronautics Fig 1. -Clement-Bayard Dirigible.png|900px]]
|-
|{{rh|{{em|7}}|{{sc|Fig.}}1.—CLÉMENT-BAYARD DIRIGIBLE.|<sup>''Photo. Topical Press.''</sup>}}
|-
|&nbsp;
|-
|[[File:EB1911 Aeronautics Fig 2. - Zeppelin VII.png|900px]]<br>
|-
|{{rh|{{em|7}}|{{sc|Fig.}}2.—ZEPPELIN VII. (DEUTSCHLAND), WRECKED JUNE 28, 1910.|<sup>''Photo. Topical Press.''</sup>}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Aeronautics Fig 1. -Clement-Bayard Dirigible.png|CLÉMENT-BAYARD DIRIGIBLE. Photo. Topical Press}}

{{IMG:EB1911 Aeronautics Fig 2. - Zeppelin VII.png|ZEPPELIN VII. (DEUTSCHLAND), WRECKED JUNE 28, 1910. Photo. Topical Press}}
```

### Current body
```
{{IMG:EB1911 Aeronautics Fig 1. -Clement-Bayard Dirigible.png|CLÉMENT-BAYARD DIRIGIBLE. Photo. Topical Press}}

{{IMG:EB1911 Aeronautics Fig 2. - Zeppelin VII.png|ZEPPELIN VII. (DEUTSCHLAND), WRECKED JUNE 28, 1910. Photo. Topical Press}}
```

---

## AERONAUTICS, PLATE II — vol 01

**Article ID:** 4186330  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|{{Ts|ma}}
|{{ts|ac}}|[[File:EB1911 Aeronautics Fig 3. - British Army Dirigible.png|900px]]
|-
|{{rh|{{em|7}}|{{sc|Fig.}}3.—BRITISH ARMY DIRIGIBLE, BETA.|<sup>''Photo. Topical Press.''</sup>}}
|-
|&nbsp;
|-
|[[File:EB1911 Aeronautics Fig 4. - Parseval Dirigible.png|900px]]<br>
|-
|{{rh|{{em|7}}|{{sc|Fig.}}4.—PARSEVAL DIRIGIBLE.|<sup>''Photo. Topical Press.''</sup>}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Aeronautics Fig 3. - British Army Dirigible.png|BRITISH ARMY DIRIGIBLE, BETA. Photo. Topical Press}}

{{IMG:EB1911 Aeronautics Fig 4. - Parseval Dirigible.png|PARSEVAL DIRIGIBLE. Photo. Topical Press}}
```

### Current body
```
{{IMG:EB1911 Aeronautics Fig 3. - British Army Dirigible.png|BRITISH ARMY DIRIGIBLE, BETA. Photo. Topical Press}}

{{IMG:EB1911 Aeronautics Fig 4. - Parseval Dirigible.png|PARSEVAL DIRIGIBLE. Photo. Topical Press}}
```

---

## ALHAMBRA, PLATE I — vol 01

**Article ID:** 4186904  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|{{Ts|ma}}
|[[File:EB1911 Alhambra - The Court of the Myrtles.png|800px]]
|-
|{{ts|ac}}|THE COURT OF THE MYRTLES.
|-
|{{ts|ar|lh1|sm85}}|From Gayangos and Owen Jones, ''The Alhambra.''
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **3** | **3** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Alhambra - The Court of the Myrtles.png|THE COURT OF THE MYRTLES}}

{{LEGEND:From Gayangos and Owen Jones, The Alhambra}LEGEND}
```

### Current body
```
{{IMG:EB1911 Alhambra - The Court of the Myrtles.png|THE COURT OF THE MYRTLES}}

{{LEGEND:From Gayangos and Owen Jones, The Alhambra}LEGEND}
```

---

## ALHAMBRA, PLATE II — vol 01

**Article ID:** 4186905  
**Signature:** `bare_image depth=0 wt=0 ht=0`

### Source excerpt
```
[[File:EB1911 Alhambra - Plate II, Capitals, Fountain.png|center|800px]]
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 0 | 0 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **1** | **1** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Alhambra - Plate II, Capitals, Fountain.png}}
```

### Current body
```
{{IMG:EB1911 Alhambra - Plate II, Capitals, Fountain.png}}
```

---

## ALLOYS, PLATE — vol 01

**Article ID:** 4187007  
**Signature:** `html_table depth=0 wt=0 ht=1 has_colspan`

### Source excerpt
```
<table {{Ts|ma}}>
<tr>
<td>
[[Image:Britannica Alloys Plate Figure 01.jpg|center]]
</td>
<td>{{gap}}</td>
<td>
[[Image:Britannica Alloys Plate Figure 02.jpg|center]]
</td>
<td>{{gap}}</td>
<td>
[[Image:Britannica Alloys Plate Figure 03.jpg|center]]
</td>
</tr>

<tr {{Ts|ac}}>
<td>ALLOYS.</td>
<td></td>
<td>ALLOYS.</td>
<td></td>
<td>ALLOYS.</td>
</tr>

<tr {{Ts|sm92|lh12|vtp}}>
<td {{Ts|width:240px}}>
{{small-caps|Fig.}} 1.—(Heycock &amp; Neville, ''Phil. Trans.'') Bronze
containing 23.3% of tin. Slowly cooled. Magnified
18 diameters. Dark parts are rich in copper, light
parts in tin.
</td>
<td></td>
<td {{Ts|width:240px}}>
{{small-caps|Fig.}} 2.—(Ewing &amp; Rosenhain, ''Phil. Trans.'') Lead-tin
eutectic. Magnified 750 diameters.
</td>
<td></td>
<td {{Ts|width:240px}}>
{{small-caps|Fig.}} 3.—(F. Osmond.) Silver-copper [copper=15%,
silver=85%] reheated to purple colour. Magnified
600 diameters.
</td>
</tr>

<tr>
<td>
[[Image:Britannica Alloys Plate Figure 04.jpg|center]]
</td>
<td></td>
<td>
[[Image:Britannica Alloys Plate Figure 05.jpg|center]]
</td>
<td></td>
<td>
[[Image:Britannica Alloys Plate Figure 06.jpg|center]]
</td>
</tr>

<tr {{Ts|ac}}>
<td>
ALLOYS.
</td>
<td></td>
<td>
GUN-MAKING.
</td>
<td></td>
<td>
GUN-MAKING.
</td>
</tr>

<tr {{Ts|sm92|lh12|vtp}}>
<td {{Ts|width:240px}}>
{{small-caps|Fig.}} 4.—(Heycock & Neville, ''Phil. Trans.'') Copper-tin
[tin 27.7%] chilled at 731&deg; C. before complete
solidification. Magnified 18 diameters. Blacks rich,
whites less rich
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 15 | 15 |
| captioned       | 15 | 15 |
| legends         | 7 | 7 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **39** | **39** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | '(See Articles Metallography, Alloys, Gun, Iron and Steel.)' | '(See Articles Metallography, Alloys, Gun, Iron and Steel.)' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:Britannica Alloys Plate Figure 01.jpg|ALLOYS}}

{{IMG:Britannica Alloys Plate Figure 02.jpg|ALLOYS}}

{{IMG:Britannica Alloys Plate Figure 03.jpg|ALLOYS}}

{{IMG:Britannica Alloys Plate Figure 04.jpg|ALLOYS}}

{{IMG:Britannica Alloys Plate Figure 05.jpg|Gun steel, C.=0.30%. From top of ingot as cast, magnified 29 diameters. Whites, ferrite; blacks, carbide}}

{{IMG:Britannica Alloys Plate Figure 06.jpg|Gun steel, C.=0.30%. From bottom of ingot as cast, magnified 29 diameters. Whites, ferrite; blacks, carbide}}

{{IMG:Britannica Alloys Plate Figure 07.jpg|Gun steel, C.=0.30%. Top of ingot, forged and annealed, magnified 29 diameters. Whites, ferrite; blacks, carbide}}

{{IMG:Britannica Alloys Plate Figure 08.jpg|Gun steel, C.=0.30%. Bottom of ingot, forged and annealed, magnified 29 diameters. Whites, ferrite; blacks, carbide}}

{{IMG:Britannica Alloys Plate Figure 09.jpg|Gun steel, C.=0.30%. Forged and annealed, magnified 1000 diameters, showing pearlite}}

{{IMG:Britannica Alloys Plate Figure 10.jpg|Gun steel, C. = 0.30%. Oil hardened and annealed, magnified 50 diameters}}

{{IMG:Britannica Alloys Plate Figure 11.jpg|GUN-MAKING}}

{{IMG:Britannica Alloys Plate Figure 12.jpg|IRON AND STEEL}}

{{IMG:Britannica Alloys Plate Figure 13.jpg|IRON AND STEEL}}

{{IMG:Britannica Alloys Plate Figure 14.jpg|IRON AND STEEL}}

{{IMG:Britannica Alloys Plate Figure 15.jpg|IRON AND STEEL}}

{{LEGEND:Fig. 1.—(Heycock & Neville, Phil. Trans.) Bronze containing 23.3% of tin. Slowly cooled. Magnified 18 diameters. Dark parts are rich in copper, light parts in tin}LEGEND}

{{LEGEND:Fig. 2.—(Ewing & Rosenhain, Phil. Trans.) Lead-tin eutectic. Magnified 750 diameters}LEGEND}

{{LEGEND:Fig. 3.—(F. Osmond.) Silver-copper [copper=15%, silver=85%] reheated to purple colour. Magnified 600 diameters}LEGEND}

{{LEGEND:Fig. 4.—(Heycock & Neville, Phil. Trans.) Copper-tin [tin 27.7%] chilled at 731&deg; C. before complete solidification. Magnified 18 diameters. Blacks rich, whites less rich in copper}LEGEND}

{{LEGEND:Fig. 11.—(Osmond.) Pearlite, steel (carbon about 1%) forged and annealed at 800&deg; C. Magnified 1000 diameters}LEGEND}

{{LEGEND:Fig. 12.—(Stoughton.) Meshes of pearlite in a network of ferrite, from hypo-eutectoid steel. Magnified 250 diameters}LEGEND}

{{LEGEND:PHOTOMICROGRAPHS OF ALLOYS AND METALS}LEGEND}

(See Articles Metallography, Alloys, Gun, Iron and Steel.)
```

### Current body
```
{{IMG:Britannica Alloys Plate Figure 01.jpg|ALLOYS}}

{{IMG:Britannica Alloys Plate Figure 02.jpg|ALLOYS}}

{{IMG:Britannica Alloys Plate Figure 03.jpg|ALLOYS}}

{{IMG:Britannica Alloys Plate Figure 04.jpg|ALLOYS}}

{{IMG:Britannica Alloys Plate Figure 05.jpg|Gun steel, C.=0.30%. From top of ingot as cast, magnified 29 diameters. Whites, ferrite; blacks, carbide}}

{{IMG:Britannica Alloys Plate Figure 06.jpg|Gun steel, C.=0.30%. From bottom of ingot as cast, magnified 29 diameters. Whites, ferrite; blacks, carbide}}

{{IMG:Britannica Alloys Plate Figure 07.jpg|Gun steel, C.=0.30%. Top of ingot, forged and annealed, magnified 29 diameters. Whites, ferrite; blacks, carbide}}

{{IMG:Britannica Alloys Plate Figure 08.jpg|Gun steel, C.=0.30%. Bottom of ingot, forged and annealed, magnified 29 diameters. Whites, ferrite; blacks, carbide}}

{{IMG:Britannica Alloys Plate Figure 09.jpg|Gun steel, C.=0.30%. Forged and annealed, magnified 1000 diameters, showing pearlite}}

{{IMG:Britannica Alloys Plate Figure 10.jpg|Gun steel, C. = 0.30%. Oil hardened and annealed, magnified 50 diameters}}

{{IMG:Britannica Alloys Plate Figure 11.jpg|GUN-MAKING}}

{{IMG:Britannica Alloys Plate Figure 12.jpg|IRON AND STEEL}}

{{IMG:Britannica Alloys Plate Figure 13.jpg|IRON AND STEEL}}

{{IMG:Britannica Alloys Plate Figure 14.jpg|IRON AND STEEL}}

{{IMG:Britannica Alloys Plate Figure 15.jpg|IRON AND STEEL}}

{{LEGEND:Fig. 1.—(Heycock & Neville, Phil. Trans.) Bronze containing 23.3% of tin. Slowly cooled. Magnified 18 diameters. Dark parts are rich in copper, light parts in tin}LEGEND}

{{LEGEND:Fig. 2.—(Ewing & Rosenhain, Phil. Trans.) Lead-tin eutectic. Magnified 750 diameters}LEGEND}

{{LEGEND:Fig. 3.—(F. Osmond.) Silver-copper [copper=15%, silver=85%] reheated to purple colour. Magnified 600 diameters}LEGEND}

{{LEGEND:Fig. 4.—(Heycock & Neville, Phil. Trans.) Copper-tin [tin 27.7%] chilled at 731&deg; C. before complete solidification. Magnified 18 diameters. Blacks rich, whites less rich in copper}LEGEND}

{{LEGEND:Fig. 11.—(Osmond.) Pearlite, steel (carbon about 1%) forged and annealed at 800&deg; C. Magnified 1000 diameters}LEGEND}

{{LEGEND:Fig. 12.—(Stoughton.) Meshes of pearlite in a network of ferrite, from hypo-eutectoid steel. Magnified 250 diameters}LEGEND}

{{LEGEND:PHOTOMICROGRAPHS OF ALLOYS AND METALS}LEGEND}

(See Articles Metallography, Alloys, Gun, Iron and Steel.)
```

---

## ALTAR — vol 01

**Article ID:** 4187091  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|align=center
|-
|[[File:EB1911 Altar, Fig. 1-Sant' Ambrogio, Milan.png]]
|-
|{{ts|sm85|lh1}}|''Photo, Brogi.''
|-
|{{ts|ac|lh1}}|{{sc|Fig.}} 1.—SANT’ AMBROGIO, MILAN.
|-
|&nbsp;
|-
|[[File:EB1911 Altar, Fig. 2-Santa Cecilia, Rome.png]]
|-
|{{ts|sm85|lh1}}|''Photo, Alinari.''
|-
|{{ts|ac|lh1}}|{{sc|Fig.}} 2.—SANTA CECILIA, ROME.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Altar, Fig. 1-Sant' Ambrogio, Milan.png|SANT’ AMBROGIO, MILAN (Photo, Brogi)}}

{{IMG:EB1911 Altar, Fig. 2-Santa Cecilia, Rome.png|SANTA CECILIA, ROME (Photo, Alinari)}}
```

### Current body
```
{{IMG:EB1911 Altar, Fig. 1-Sant' Ambrogio, Milan.png|SANT’ AMBROGIO, MILAN (Photo, Brogi)}}

{{IMG:EB1911 Altar, Fig. 2-Santa Cecilia, Rome.png|SANTA CECILIA, ROME (Photo, Alinari)}}
```

---

## ALTAR — vol 01

**Article ID:** 4187092  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|align=center
|-
|[[File:EB1911 Altar, Fig. 3-St. Paul's, London.png]]
|-
|{{ts|sm85|lh1}}|''Photo, O. W. Wilson & Co.''
|-
|{{ts|ac|lh1}}|{{sc|Fig.}} 3.—ST. PAUL’S, LONDON.
|-
|&nbsp;
|-
|[[File:EB1911 Altar, Fig. 4-Certosa, Pavia.png]]
|-
|{{ts|sm85|lh1}}|''Photo, Brogi.''
|-
|{{ts|ac|lh1}}|{{sc|Fig.}} 4.—CERTOSA, PAVIA.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Altar, Fig. 3-St. Paul's, London.png|ST. PAUL’S, LONDON (Photo, O. W. Wilson & Co)}}

{{IMG:EB1911 Altar, Fig. 4-Certosa, Pavia.png|CERTOSA, PAVIA (Photo, Brogi)}}
```

### Current body
```
{{IMG:EB1911 Altar, Fig. 3-St. Paul's, London.png|ST. PAUL’S, LONDON (Photo, O. W. Wilson & Co)}}

{{IMG:EB1911 Altar, Fig. 4-Certosa, Pavia.png|CERTOSA, PAVIA (Photo, Brogi)}}
```

---

## AMERICA, PLATE I — vol 01

**Article ID:** 4187222  
**Signature:** `bare_image depth=0 wt=0 ht=0`

### Source excerpt
```
[[File:EB1911 - America - Plate I.png|center|800px]]
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 0 | 0 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **1** | **1** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - America - Plate I.png}}
```

### Current body
```
{{IMG:EB1911 - America - Plate I.png}}
```

---

## AMERICA, PLATE II — vol 01

**Article ID:** 4187223  
**Signature:** `bare_image depth=0 wt=0 ht=0`

### Source excerpt
```
[[File:EB1911 - America - Plate II.png|800px|center]]
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 0 | 0 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **1** | **1** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - America - Plate II.png}}
```

### Current body
```
{{IMG:EB1911 - America - Plate II.png}}
```

---

## AMERICA, PLATE III — vol 01

**Article ID:** 4187224  
**Signature:** `bare_image depth=0 wt=0 ht=0`

### Source excerpt
```
[[File:EB1911 - America - Plate III.png|800px|center]]
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 0 | 0 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **1** | **1** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - America - Plate III.png}}
```

### Current body
```
{{IMG:EB1911 - America - Plate III.png}}
```

---

## AMERICA, PLATE IV — vol 01

**Article ID:** 4187225  
**Signature:** `bare_image depth=0 wt=0 ht=0`

### Source excerpt
```
[[File:EB1911 - America - Plate IV.png|800px|center]]
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 0 | 0 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **1** | **1** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - America - Plate IV.png}}
```

### Current body
```
{{IMG:EB1911 - America - Plate IV.png}}
```

---

## AMERICA, PLATE V — vol 01

**Article ID:** 4187226  
**Signature:** `bare_image depth=0 wt=0 ht=0`

### Source excerpt
```
[[File:EB1911 - America - Plate V.png|800px|center]]
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 0 | 0 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **1** | **1** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - America - Plate V.png}}
```

### Current body
```
{{IMG:EB1911 - America - Plate V.png}}
```

---

## AMPHITHEATRE, PLATE I — vol 01

**Article ID:** 4187313  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{| style="margin-left: auto; margin-right: auto; border-collapse: collapse; width: 850px;" summary="Illustration" 
| style="text-align: center; margin: auto; margin-left: auto; margin-right: auto; padding-top: 1.5em;" |[[Image:1911 Britannica - Amphitheatre at Pola.JPG|center|600px|]]
|-
| style="font-size: 0.9em; text-align: center; padding-bottom: 1em; padding-left: 1em; padding-right: 1em;" |EXTERIOR OF THE AMPHITHEATRE AT POLA ''(Pietas Julia)'', ISTRIA.
|-
| style="text-align: center; margin: auto; margin-left: auto; margin-right: auto; padding-top: 1.5em;" |[[Image:1911 Britannica - Amphitheatre at Nîmes.png|center|600px|]]
|-
| style="font-size: 0.9em; text-align: center; padding-bottom: 1em; padding-left: 1em; padding-right: 1em;" |EXTERIOR OF THE AMPHITHEATRE AT NÎMES (NEMAUSUS).
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica - Amphitheatre at Pola.JPG|EXTERIOR OF THE AMPHITHEATRE AT POLA (Pietas Julia), ISTRIA}}

{{IMG:1911 Britannica - Amphitheatre at Nîmes.png|EXTERIOR OF THE AMPHITHEATRE AT NÎMES (NEMAUSUS)}}
```

### Current body
```
{{IMG:1911 Britannica - Amphitheatre at Pola.JPG|EXTERIOR OF THE AMPHITHEATRE AT POLA (Pietas Julia), ISTRIA}}

{{IMG:1911 Britannica - Amphitheatre at Nîmes.png|EXTERIOR OF THE AMPHITHEATRE AT NÎMES (NEMAUSUS)}}
```

---

## AMPHITHEATRE, PLATE II — vol 01

**Article ID:** 4187314  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{| style="margin-left: auto; margin-right: auto; border-collapse: collapse; width: 850px;" summary="Illustration" 
| style="text-align: center; margin: auto; margin-left: auto; margin-right: auto; padding-top: 1.5em;" |[[Image:1911 Britannica - Amphitheatre at Pompeii.png|center|600px|]]
|-
| style="font-size: 0.9em; text-align: center; padding-bottom: 1em; padding-left: 1em; padding-right: 1em;" |INTERIOR OF THE AMPHITHEATRE AT POMPEII.
|-
| style="text-align: center; margin: auto; margin-left: auto; margin-right: auto; padding-top: 1.5em;" |[[Image:1911 Britannica - Amphitheatre at Pozzuoli.png|center|600px|]]
|-
| style="font-size: 0.9em; text-align: center; padding-bottom: 1em; padding-left: 1em; padding-right: 1em;" |INTERIOR OF THE AMPHITHEATRE AT POZZUOLI (PUTEOLI).
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica - Amphitheatre at Pompeii.png|INTERIOR OF THE AMPHITHEATRE AT POMPEII}}

{{IMG:1911 Britannica - Amphitheatre at Pozzuoli.png|INTERIOR OF THE AMPHITHEATRE AT POZZUOLI (PUTEOLI)}}
```

### Current body
```
{{IMG:1911 Britannica - Amphitheatre at Pompeii.png|INTERIOR OF THE AMPHITHEATRE AT POMPEII}}

{{IMG:1911 Britannica - Amphitheatre at Pozzuoli.png|INTERIOR OF THE AMPHITHEATRE AT POZZUOLI (PUTEOLI)}}
```

---

## Anthropology, PLATE — vol 02

**Article ID:** 4187664  
**Signature:** `wikitable depth=1 wt=multi ht=0`

### Source excerpt
```
<section begin="Anthropology"/>
{| {{ts|mc|width:850px}}
|-
| {{ts|pr1|vtp|width:50%}} |
[[File:1911 Britannica-Anthropology-Amoenitates Academicae.png|center|300px|]]
{{center|{{lh|88%|{{smaller|{{sc|Fig.}} 1.}}}}}}

[[File:1911 Britannica-Anthropology-2.png|center|360px|]]
{{center|{{lh|88%|{{smaller|{{sc|Fig.}} 2.}}}}}}

| {{ts|vtp|pl1|width:50%}} |
[[File:1911 Britannica-Anthropology-3.png|center|270px|]]
{{center|{{lh|88%|{{smaller|{{sc|Fig.}} 3.}}}}}}

[[File:1911 Britannica-Anthropology-4.png|center|270px|]]
{{center|{{lh|88%|{{smaller|{{sc|Fig.}} 4.}}}}}}

[[File:1911 Britannica-Anthropology-5.png|center|270px|]]
{{center|{{lh|88%|{{smaller|{{sc|Fig.}} 5.}}}}}}
|}

{| style="margin-left: auto; margin-right: auto; border-collapse: collapse; width: 850px;" summary="Illustration" 
| style="text-align: center; margin: auto; margin-left: auto; margin-right: auto; padding-top: 1.5em;" |[[File:1911 Britannica-Anthropology-6.png|center|200px|]]
| style="text-align: center; margin: auto; margin-left: auto; margin-right: auto; padding-top: 1.5em;" |[[File:1911 Britannica-Anthropology-7.png|center|200px|]]
| style="text-align: center; margin: auto; margin-left: auto; margin-right: auto; padding-top: 1.5em;" |[[File:1911 Britannica-Anthropology-8.png|center|170px|]]
|-
| style="font-size: 0.9em; text-align: center; padding-bottom: 1em; padding-left: 1em; padding-right: 1em;" |{{center|{{lh|88%|{{smaller|{{sc|Fig.}} 6.}}}}}}
| style="font-size: 0.9em; text-align: center; padding-b
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 12 | 12 |
| captioned       | 12 | 12 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **24** | **24** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica-Anthropology-Amoenitates Academicae.png|Fig. 1}}

{{IMG:1911 Britannica-Anthropology-2.png|Fig. 2}}

{{IMG:1911 Britannica-Anthropology-3.png|Fig. 3}}

{{IMG:1911 Britannica-Anthropology-4.png|Fig. 4}}

{{IMG:1911 Britannica-Anthropology-5.png|Fig. 5}}

{{IMG:1911 Britannica-Anthropology-6.png|Fig. 6}}

{{IMG:1911 Britannica-Anthropology-7.png|Fig. 7}}

{{IMG:1911 Britannica-Anthropology-8.png|Fig. 8}}

{{IMG:1911 Britannica-Anthropology-9.png|Fig. 9}}

{{IMG:1911 Britannica-Anthropology-10.png|Fig. 10}}

{{IMG:1911 Britannica-Anthropology-11.png|Fig. 11}}

{{IMG:1911 Britannica-Anthropology-12.png|Fig. 12}}
```

### Current body
```
{{IMG:1911 Britannica-Anthropology-Amoenitates Academicae.png|Fig. 1}}

{{IMG:1911 Britannica-Anthropology-2.png|Fig. 2}}

{{IMG:1911 Britannica-Anthropology-3.png|Fig. 3}}

{{IMG:1911 Britannica-Anthropology-4.png|Fig. 4}}

{{IMG:1911 Britannica-Anthropology-5.png|Fig. 5}}

{{IMG:1911 Britannica-Anthropology-6.png|Fig. 6}}

{{IMG:1911 Britannica-Anthropology-7.png|Fig. 7}}

{{IMG:1911 Britannica-Anthropology-8.png|Fig. 8}}

{{IMG:1911 Britannica-Anthropology-9.png|Fig. 9}}

{{IMG:1911 Britannica-Anthropology-10.png|Fig. 10}}

{{IMG:1911 Britannica-Anthropology-11.png|Fig. 11}}

{{IMG:1911 Britannica-Anthropology-12.png|Fig. 12}}
```

---

## Aqueduct, PLATE I — vol 02

**Article ID:** 4187903  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
<section begin="s1"/>
{| style="margin-left: auto; margin-right: auto; border-collapse: collapse; width: 850px;" summary="Illustration" 
| style="text-align: center; margin: auto; margin-left: auto; margin-right: auto; padding-top: 1.5em;" |[[File:Aqueduct-aqua-claudia.jpg|center|750px|]]
|-
| style="font-size: 0.9em; text-align: center; padding-bottom: 1em; padding-left: 1em; padding-right: 1em;" |{{right|<small>''Photo, Alinari.''</small>}}<br />AQUA CLAUDIA, ROME.
|-
| style="text-align: center; margin: auto; margin-left: auto; margin-right: auto; padding-top: 1.5em;" |[[File:Aqueduct-pont-du-gard.jpg|center|750px|]]
|-
| style="font-size: 0.9em; text-align: center; padding-bottom: 1em; padding-left: 1em; padding-right: 1em;" |{{right|<small>''Photo, Neurdein.''</small>}}<br />PONT DU GARD, NÎMES (NEMAUSUS).
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:Aqueduct-aqua-claudia.jpg|Photo, Alinari. AQUA CLAUDIA, ROME}}

{{IMG:Aqueduct-pont-du-gard.jpg|Photo, Neurdein. PONT DU GARD, NÎMES (NEMAUSUS)}}
```

### Current body
```
{{IMG:Aqueduct-aqua-claudia.jpg|Photo, Alinari. AQUA CLAUDIA, ROME}}

{{IMG:Aqueduct-pont-du-gard.jpg|Photo, Neurdein. PONT DU GARD, NÎMES (NEMAUSUS)}}
```

---

## Aqueduct, PLATE II — vol 02

**Article ID:** 4187904  
**Signature:** `wikitable depth=1 wt=multi ht=0`

### Source excerpt
```
<section begin="s1"/>
{| style="margin-left: auto; margin-right: auto; border-collapse: collapse; width: 850px;" summary="Illustration" 
| style="text-align: center; margin: auto; margin-left: auto; margin-right: auto; padding-top: 1.5em;" |[[File:Aqueduct-segovia.jpg|center|750px|]]
|-
| style="font-size: 0.9em; text-align: center; padding-bottom: 1em; padding-left: 1em; padding-right: 1em;" |{{right|<small>''Photo, Laureal y Cia.''</small>}}<br />ROMAN AQUEDUCT AT SEGOVIA.
|-
|}
{| {{ts|mc|width:850px}}
|-
| {{ts|pr1|vtp|width:50%}} |
[[File:1911 Britannica-Aqueduct-Piscina Mirabilis.png|center|400px|]]
{{right|{{lh|88%|<small>''Photo, Brogi.''</small>}}<br />{{center|PISCINA MIRABILIS AT BAIAE.}}}}
| {{ts|vtp|pl1|width:50%}} |
[[File:1911 Britannica-Aqueduct-Roquefavour.png|center|300px|]]
{{center|{{lh|88%|AQUEDUCT OF ROQUEFAVOUR, MARSEILLES.<br /><small>Early nineteenth century.</small>}}}}
[[File:1911 Britannica-Aqueduct-Aqua Marcia.png|center|350px|]]
{{right|{{lh|88%|<small>''Photo, Dr T. Ashby.''</small>}}<br />{{center|AQUA MARCIA, ROME.}}}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:Aqueduct-segovia.jpg|PISCINA MIRABILIS AT BAIAE}}

{{IMG:1911 Britannica-Aqueduct-Piscina Mirabilis.png|AQUEDUCT OF ROQUEFAVOUR, MARSEILLES}}

{{IMG:1911 Britannica-Aqueduct-Roquefavour.png|AQUA MARCIA, ROME}}

{{IMG:1911 Britannica-Aqueduct-Aqua Marcia.png|Photo, Laureal y Cia. ROMAN AQUEDUCT AT SEGOVIA}}
```

### Current body
```
{{IMG:Aqueduct-segovia.jpg|PISCINA MIRABILIS AT BAIAE}}

{{IMG:1911 Britannica-Aqueduct-Piscina Mirabilis.png|AQUEDUCT OF ROQUEFAVOUR, MARSEILLES}}

{{IMG:1911 Britannica-Aqueduct-Roquefavour.png|AQUA MARCIA, ROME}}

{{IMG:1911 Britannica-Aqueduct-Aqua Marcia.png|Photo, Laureal y Cia. ROMAN AQUEDUCT AT SEGOVIA}}
```

---

## Archaeology, PLATE I — vol 02

**Article ID:** 4187992  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|align="center" cellpadding="0" cellspacing="0"
|[[File:1911 Britannica-Archaeology-Palaeolithic.png|700px]]
|-
|{{center|{{sc|PALAEOLITHIC PERIOD.}}}}<br />{{center|1. French Drift. 2. English Drift. 3. French transition (Le Moustier). 4. French Cave Period. 5. English Cave Period.}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **2** | **2** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica-Archaeology-Palaeolithic.png|English Drift. 3. French transition (Le Moustier). 4. French Cave Period. 5. English Cave Period}}
```

### Current body
```
{{IMG:1911 Britannica-Archaeology-Palaeolithic.png|English Drift. 3. French transition (Le Moustier). 4. French Cave Period. 5. English Cave Period}}
```

---

## Archaeology, PLATE II — vol 02

**Article ID:** 4187993  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|align="center" cellpadding="0" cellspacing="0"
|[[File:1911 Britannica-Archaeology-Dordogne.png|700px]]
|-
|{{center|{{sc|SCULPTURE AND ENGRAVINGS OF THE CAVE PERIOD.}}}}<br />{{center|{{sc|FROM DORDOGNE, FRANCE.}}}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **2** | **2** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica-Archaeology-Dordogne.png|SCULPTURE AND ENGRAVINGS OF THE CAVE PERIOD. FROM DORDOGNE, FRANCE}}
```

### Current body
```
{{IMG:1911 Britannica-Archaeology-Dordogne.png|SCULPTURE AND ENGRAVINGS OF THE CAVE PERIOD. FROM DORDOGNE, FRANCE}}
```

---

## Archaeology, PLATE III — vol 02

**Article ID:** 4187994  
**Signature:** `wikitable depth=1 wt=multi ht=0`

### Source excerpt
```
{|align="center" cellpadding="0" cellspacing="0"
|[[File:1911 Britannica-Archaeology-Altamira.png|700px]]
|-
|{{center|{{sc|WALL-PAINTINGS OF THE CAVE PERIOD,}}}}<br />{{center|{{sc|CAVERN OF ALTAMIRA, SANTANDER, SPAIN.}}}}
|}
<br />
{|align="center" cellpadding="0" cellspacing="0"
|[[File:1911 Britannica-Archaeology-Altamira2.png|700px]]
|-
|{{center|{{sc|OUTLINE OF WALL-PAINTINGS, ALTAMIRA, LENGTH ABOUT 45½ FT.}}}}<br />{{center|(''cf.'' {{sc|PAINTING, Plate I.}})}}
|-
|align="right"|{{smaller|By permission, from ''La Caverne d'Altamira'' by Cartailhac and Breuil, Monaco, 1906.}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica-Archaeology-Altamira.png|WALL-PAINTINGS OF THE CAVE PERIOD, CAVERN OF ALTAMIRA, SANTANDER, SPAIN}}

{{IMG:1911 Britannica-Archaeology-Altamira2.png|OUTLINE OF WALL-PAINTINGS, ALTAMIRA, LENGTH ABOUT 45½ FT. (cf. PAINTING, Plate I. )}}
```

### Current body
```
{{IMG:1911 Britannica-Archaeology-Altamira.png|WALL-PAINTINGS OF THE CAVE PERIOD, CAVERN OF ALTAMIRA, SANTANDER, SPAIN}}

{{IMG:1911 Britannica-Archaeology-Altamira2.png|OUTLINE OF WALL-PAINTINGS, ALTAMIRA, LENGTH ABOUT 45½ FT. (cf. PAINTING, Plate I. )}}
```

---

## Archaeology, PLATE IV — vol 02

**Article ID:** 4187995  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|align="center" cellpadding="0" cellspacing="0"
|[[File:1911 Britannica-Archaeology-Neolithic.png|700px]]
|-
|{{center|{{sc|NEOLITHIC PERIOD.}}}}<br />{{center|'''1.''' Flint and stone implements, England. '''2.''' Flint arrow-heads, England. '''3.''' Arrow-heads, Ireland.<br />'''4.''' Flint and stone implements, Denmark. '''5.''' Flint implements, France. '''6.''' Flint implements, Egypt.}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **2** | **2** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica-Archaeology-Neolithic.png|NEOLITHIC PERIOD. 1. Flint and stone implements, England. 2. Flint arrow-heads, England. 3. Arrow-heads, Ireland. 4. Flint and stone implements, Denmark. 5. Flint implements, France. 6. Flint implements, Egypt}}
```

### Current body
```
{{IMG:1911 Britannica-Archaeology-Neolithic.png|NEOLITHIC PERIOD. 1. Flint and stone implements, England. 2. Flint arrow-heads, England. 3. Arrow-heads, Ireland. 4. Flint and stone implements, Denmark. 5. Flint implements, France. 6. Flint implements, Egypt}}
```

---

## Archaeology, PLATE V — vol 02

**Article ID:** 4187996  
**Signature:** `wikitable depth=1 wt=multi ht=0`

### Source excerpt
```
{|{{Ts|mc|ac}}
|[[File:1911 Britannica-Archaeology-Sepulchral pottery1.png|400px]]<br>SEPULCHRAL POTTERY, BRITISH ISLES (BRONZE AGE).<br>1–3, Drinking cups or beakers. 4–9, Food vessels.<br>10–12, Cinerary urns.
|| 
||
|{{Ts|vtp}}|[[File:1911 Britannica-Archaeology-Sepulchral pottery2.png|407px]]<br>{{sc|SEPULCHRAL POTTERY FROM THE CONTINENT OF<br>EUROPE (NEOLITHIC, BRONZE, AND IRON AGES).}}
|}
<br>
{|{{Ts|mc|ac}}
|[[File:1911 Britannica-Archaeology-Celt.png|800px]]
|-
|STAGES IN THE EVOLUTION OF THE CELT OR IMPLEMENT OF CHISEL FORM.<br>(1) From stone to metallic form. (2) Growth of the stop ridge to palstave. (3) Growth of the wings to socket-celt.
|-
|{{Ts|ar|sm85}}|By permission, from the British Museum ''Guide to the Bronze Age''.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica-Archaeology-Sepulchral pottery1.png|SEPULCHRAL POTTERY, BRITISH ISLES (BRONZE AGE)}}

{{IMG:1911 Britannica-Archaeology-Sepulchral pottery2.png|SEPULCHRAL POTTERY FROM THE CONTINENT OF EUROPE (NEOLITHIC, BRONZE, AND IRON AGES)}}

{{IMG:1911 Britannica-Archaeology-Celt.png|STAGES IN THE EVOLUTION OF THE CELT OR IMPLEMENT OF CHISEL FORM. (1) From stone to metallic form. (2) Growth of the stop ridge to palstave. (3) Growth of the wings to socket-celt}}
```

### Current body
```
{{IMG:1911 Britannica-Archaeology-Sepulchral pottery1.png|SEPULCHRAL POTTERY, BRITISH ISLES (BRONZE AGE)}}

{{IMG:1911 Britannica-Archaeology-Sepulchral pottery2.png|SEPULCHRAL POTTERY FROM THE CONTINENT OF EUROPE (NEOLITHIC, BRONZE, AND IRON AGES)}}

{{IMG:1911 Britannica-Archaeology-Celt.png|STAGES IN THE EVOLUTION OF THE CELT OR IMPLEMENT OF CHISEL FORM. (1) From stone to metallic form. (2) Growth of the stop ridge to palstave. (3) Growth of the wings to socket-celt}}
```

---

## Archaeology, PLATE VI — vol 02

**Article ID:** 4187997  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{| {{ts|mc|width:900px}}
|-
| {{ts|pr1|vtp|width:45%}} |
[[File:1911 Britannica-Archaeology-Bronze shield.png|center|230px|]]
{{center|{{lh|88%|1. Bronze shield with red enamel<br>ornaments, found in the Thames<br> near Battersea; about 31 in. long.}}}}

[[File:1911 Britannica-Archaeology-Bronze bucket.png|center|295px|]]
{{center|{{lh|88%|Bronze mounted wooden bucket found in a pit burial<br>at Aylesford.{{dhr|60%}}Early Iron Age.}}<br />{{center|The objects here represented are all in the<br>British Museum.}}{{center|{{smaller|By permission, from the British Museum ''Guide to the Early Iron Age''.}}}}}}
| {{ts|pl1|vtp|width:55%}} |
[[File:1911 Britannica-Archaeology-Chariot burial.png|center|500px|]]
{{center|{{lh|88%|Chariot burial of a Gaulish chief, Somme Bionne, Marne, France.}}}}
<br />
[[File:1911 Britannica-Archaeology-Bronze helmet.png|center|370px|]]
{{center|{{lh|88%|Horned bronze helmet with traces of enamel ornament, found in the Thames near Waterloo Bridge.}}}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica-Archaeology-Bronze shield.png|Bronze shield with red enamel ornaments, found in the Thames near Battersea; about 31 in. long}}

{{IMG:1911 Britannica-Archaeology-Bronze bucket.png|Bronze mounted wooden bucket found in a pit burial at Aylesford. Early Iron Age}}

{{IMG:1911 Britannica-Archaeology-Chariot burial.png|Chariot burial of a Gaulish chief, Somme Bionne, Marne, France}}

{{IMG:1911 Britannica-Archaeology-Bronze helmet.png|Horned bronze helmet with traces of enamel ornament, found in the Thames near Waterloo Bridge}}
```

### Current body
```
{{IMG:1911 Britannica-Archaeology-Bronze shield.png|Bronze shield with red enamel ornaments, found in the Thames near Battersea; about 31 in. long}}

{{IMG:1911 Britannica-Archaeology-Bronze bucket.png|Bronze mounted wooden bucket found in a pit burial at Aylesford. Early Iron Age}}

{{IMG:1911 Britannica-Archaeology-Chariot burial.png|Chariot burial of a Gaulish chief, Somme Bionne, Marne, France}}

{{IMG:1911 Britannica-Archaeology-Bronze helmet.png|Horned bronze helmet with traces of enamel ornament, found in the Thames near Waterloo Bridge}}
```

---

## Architecture — vol 02

**Article ID:** 4188029  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|style="margin:auto; line-height:110%"
|style=text-align:right|{{sc|Plate I.}} &emsp;
|-
|[[File:1911 Britannica-Architecture-Pisa.png|700px|center]]
|-
|{{csc|Fig. 62.—PISA.}}
|-style=line-height:60%
|&nbsp;
|-
|[[File:1911 Britannica-Architecture-Venice.png|800px]]
|-
|{{rh|&emsp;{{smaller|''Photo Anderson.''}}||{{sc|Fig. 63}}.—ST MARK’S, VENICE.||&emsp; &emsp;&emsp;  &emsp; &emsp;}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica-Architecture-Pisa.png|PISA}}

{{IMG:1911 Britannica-Architecture-Venice.png|ST MARK’S, VENICE}}
```

### Current body
```
{{IMG:1911 Britannica-Architecture-Pisa.png|PISA}}

{{IMG:1911 Britannica-Architecture-Venice.png|ST MARK’S, VENICE}}
```

---

## Architecture — vol 02

**Article ID:** 4188030  
**Signature:** `wikitable depth=1 wt=1 ht=0 has_colspan`

### Source excerpt
```
{| {{ts|mc|width:800px|lh100}}
|{{Ts|ar}} colspan=2|{{sc|Plate II.}}&ensp;
|-
| {{ts|pr1|vtp|width:50%}} |
[[File:1911 Britannica-Architecture-Amiens Cathedral.png|center|400px|]]
{{left|{{lh|88%|&nbsp;{{smaller|''Photo'', ''Neurdein.''}}}}<br>{{center|{{sc|Fig. 64}}.—AMIENS CATHEDRAL.}}}}
{{dhr|70%}}
[[File:1911 Britannica-Architecture-St Paul's Cathedral.png|center|400px|]]
{{left|{{lh|88%|&nbsp;{{smaller|''Photo'', ''F. Frith & Co.''}}}}<br>{{center|{{sc|Fig. 66}}.—ST PAUL’S, LONDON.}}}}

| {{ts|pl1|vtp|width:50%}} |
[[File:1911 Britannica-Architecture-Burgos Cathedral.png|center|400px|]]
{{left|{{lh|88%|&nbsp;{{smaller|''Photo'', ''F. Frith & Co.''}}}}<br>{{center|{{sc|Fig. 65}}.—BURGOS CATHEDRAL.}}}}
{{dhr|70%}}
[[File:1911 Britannica-Architecture-Ely Cathedral.png|center|400px|]]
{{left|{{lh|88%|&nbsp;{{smaller|''Photo'', ''F. Frith & Co.''}}}}<br>{{center|{{sc|Fig. 67}}.—ELY CATHEDRAL.}}}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **10** | **10** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'Plate II.' | 'Plate II.' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
Plate II.

{{IMG:1911 Britannica-Architecture-Amiens Cathedral.png|AMIENS CATHEDRAL}}

{{IMG:1911 Britannica-Architecture-St Paul's Cathedral.png|ST PAUL’S, LONDON}}

{{IMG:1911 Britannica-Architecture-Burgos Cathedral.png|BURGOS CATHEDRAL}}

{{IMG:1911 Britannica-Architecture-Ely Cathedral.png|ELY CATHEDRAL}}
```

### Current body
```
Plate II.

{{IMG:1911 Britannica-Architecture-Amiens Cathedral.png|AMIENS CATHEDRAL}}

{{IMG:1911 Britannica-Architecture-St Paul's Cathedral.png|ST PAUL’S, LONDON}}

{{IMG:1911 Britannica-Architecture-Burgos Cathedral.png|BURGOS CATHEDRAL}}

{{IMG:1911 Britannica-Architecture-Ely Cathedral.png|ELY CATHEDRAL}}
```

---

## Architecture — vol 02

**Article ID:** 4188031  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|style="margin:auto; line-height:110%"
|style=text-align:right|{{sc|Plate III.}}
|-
|[[File:1911 Britannica-Architecture-Saint Peter's.png|740px|center]]
|-
|{{rh| <sup>''Photo'', ''Brogi.''</sup>|{{sc|Fig. 68}}.—ST PETER’S, ROME.|{{em|5}}}}
|-
|[[File:1911 Britannica-Architecture-Saint Peter's interior.png|760px]]
|-
|{{rh| <sup>''Photo'', ''Alinari.''</sup>|{{sc|Fig. 69}}.—INTERIOR OF ST PETER’S, ROME.|{{em|6}}}}
|}
<br><br>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica-Architecture-Saint Peter's.png|ST PETER’S, ROME}}

{{IMG:1911 Britannica-Architecture-Saint Peter's interior.png|INTERIOR OF ST PETER’S, ROME}}
```

### Current body
```
{{IMG:1911 Britannica-Architecture-Saint Peter's.png|ST PETER’S, ROME}}

{{IMG:1911 Britannica-Architecture-Saint Peter's interior.png|INTERIOR OF ST PETER’S, ROME}}
```

---

## Architecture — vol 02

**Article ID:** 4188032  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|{{Ts|ma|lh100}}
|{{Ts|ar}}|{{sc|Plate IV.}}&emsp;
|-
|[[File:1911 Britannica-Architecture-Bremen.png|700px|center]]
|-
|{{rh|    <sup>''Photo'', ''Koch.''</sup>|{{sc|Fig. 70}}.—TOWN HALL, BREMEN.|{{em|6}}}}
|-style=line-height:30%
|&nbsp;
|-
|[[File:1911 Britannica-Architecture-Vendramini Palace.png|760px]]
|-
|{{rh| <sup>''Photo'', ''Brogi.''</sup>|{{sc|Fig. 71}}.—VENDRAMINI PALACE. VENICE.|{{em|4.5}}}}
|}
<br>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica-Architecture-Bremen.png|TOWN HALL, BREMEN}}

{{IMG:1911 Britannica-Architecture-Vendramini Palace.png|VENDRAMINI PALACE. VENICE}}
```

### Current body
```
{{IMG:1911 Britannica-Architecture-Bremen.png|TOWN HALL, BREMEN}}

{{IMG:1911 Britannica-Architecture-Vendramini Palace.png|VENDRAMINI PALACE. VENICE}}
```

---

## Architecture — vol 02

**Article ID:** 4188033  
**Signature:** `wikitable depth=1 wt=1 ht=0 has_colspan`

### Source excerpt
```
{| {{ts|mc|width:840px|lh100}}
|{{Ts|ar}} colspan=3|{{sc|Plate V.}}&emsp;
|-
| {{ts|pr1|vtp|width:50%}} |
[[File:1911 Britannica-Architecture-Pavia.png|center|408px|]]
&emsp;{{lh|88%|{{smaller|''Photo, Alinari''.}}{{center|{{sc|Fig. 72}}.—DOOR OF SAN MICHELE, PAVIA.}}}}
|&emsp; &emsp;
| {{ts|pr1|vtp|width:50%}} |
[[File:1911 Britannica-Architecture-Salamanca.png|center|398px|]]
&emsp;{{lh|88%|{{smaller|''Photo, Lacoste''.}}{{center|{{sc|Fig. 73}}.—UNIVERSITY, SALAMANCA.}}}}
|-
|{{dhr|70%}}
|-
| {{ts|pr1|vtp|width:100%}}  colspan=3|
[[File:1911 Britannica-Architecture-Seville.png|center|840px|]]
&emsp;{{lh|88%|{{smaller|''Photo, Lacoste''.}}{{center|{{sc|Fig. 74}}.—TOWN HALL, SEVILLE.}}}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'Plate V.' | 'Plate V.' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
Plate V.

{{IMG:1911 Britannica-Architecture-Pavia.png|DOOR OF SAN MICHELE, PAVIA}}

{{IMG:1911 Britannica-Architecture-Salamanca.png|UNIVERSITY, SALAMANCA}}

{{IMG:1911 Britannica-Architecture-Seville.png|TOWN HALL, SEVILLE}}
```

### Current body
```
Plate V.

{{IMG:1911 Britannica-Architecture-Pavia.png|DOOR OF SAN MICHELE, PAVIA}}

{{IMG:1911 Britannica-Architecture-Salamanca.png|UNIVERSITY, SALAMANCA}}

{{IMG:1911 Britannica-Architecture-Seville.png|TOWN HALL, SEVILLE}}
```

---

## Architecture, PLATE VI — vol 02

**Article ID:** 4188034  
**Signature:** `wikitable depth=1 wt=multi ht=0`

### Source excerpt
```
{|align="center" cellpadding="0" cellspacing="0"
|[[File:1911 Britannica-Architecture-Whitehall.png|600px]]
|-
|{{left|{{smaller|''Photo, F. Frith & Co.''}}}}{{center|{{sc|Fig. 75}}.&mdash;BANQUETING HOUSE, WHITEHALL.}}
|}
<br /><br />
{|align="center" cellpadding="0" cellspacing="0"
|[[File:1911 Britannica-Architecture-Wollaton.png|800px]]
|-
|{{left|{{smaller|''Photo, F. Frith & Co.''}}}}{{center|{{sc|Fig. 76}}.&mdash;WOLLATON HALL.}}
|}
<br /><br />
{|align="center" cellpadding="0" cellspacing="0"
|[[File:1911 Britannica-Architecture-Hampton.png|800px]]
|-
|{{left|{{smaller|''Photo, Stuart.''}}}}{{center|{{sc|Fig. 77}}.&mdash;HAMPTON COURT.}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica-Architecture-Whitehall.png|BANQUETING HOUSE, WHITEHALL}}

{{IMG:1911 Britannica-Architecture-Wollaton.png|WOLLATON HALL}}

{{IMG:1911 Britannica-Architecture-Hampton.png|HAMPTON COURT}}
```

### Current body
```
{{IMG:1911 Britannica-Architecture-Whitehall.png|BANQUETING HOUSE, WHITEHALL}}

{{IMG:1911 Britannica-Architecture-Wollaton.png|WOLLATON HALL}}

{{IMG:1911 Britannica-Architecture-Hampton.png|HAMPTON COURT}}
```

---

## Architecture — vol 02

**Article ID:** 4188035  
**Signature:** `wikitable depth=1 wt=multi ht=0 has_colspan`

### Source excerpt
```
{| {{ts|mc|width:840px|lh100}}
|{{ts|ar}} colspan=3|{{sc|Plate VII.}}&emsp;
|-
| {{ts|pr1|vtp}} |
[[File:1911 Britannica-Architecture-Friedrichsbau.png|center|393px|]]
{{lh|88%|&emsp;{{smaller|''Photo L.L. Paris.''}}{{center|{{sc|Fig. 78}}.—HEIDELBERG CASTLE, FRIEDRICHSBAU.}}}}
|&emsp;
| {{ts|pr1|vtp}} |
[[File:1911 Britannica-Architecture-Ottheinrichsbau.png|center|410px|]]
{{lh|88%|&emsp;{{smaller|''Photo L.L. Paris.''}}{{center|{{sc|Fig. 79}}.—HEIDELBERG CASTLE, OTTO-HEINRICHSBAU.}}}}
|}
{{dhr|60%}}
{| {{ts|mc|width:840px|lh100}}
|-
| {{ts|pr1|vtp}} |
[[File:1911 Britannica-Architecture-Heidelberg Castle.png|center|840px|]]
{{lh|88%|&emsp;{{smaller|''Photo L.L. Paris.''}}{{center|{{sc|Fig. 80}}.—HEIDELBERG CASTLE, OTTO-HEINRICHSBAU.}}}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'Plate VII.' | 'Plate VII.' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
Plate VII.

{{IMG:1911 Britannica-Architecture-Friedrichsbau.png|HEIDELBERG CASTLE, FRIEDRICHSBAU}}

{{IMG:1911 Britannica-Architecture-Ottheinrichsbau.png|HEIDELBERG CASTLE, OTTO-HEINRICHSBAU}}

{{IMG:1911 Britannica-Architecture-Heidelberg Castle.png|HEIDELBERG CASTLE, OTTO-HEINRICHSBAU}}
```

### Current body
```
Plate VII.

{{IMG:1911 Britannica-Architecture-Friedrichsbau.png|HEIDELBERG CASTLE, FRIEDRICHSBAU}}

{{IMG:1911 Britannica-Architecture-Ottheinrichsbau.png|HEIDELBERG CASTLE, OTTO-HEINRICHSBAU}}

{{IMG:1911 Britannica-Architecture-Heidelberg Castle.png|HEIDELBERG CASTLE, OTTO-HEINRICHSBAU}}
```

---

## Architecture — vol 02

**Article ID:** 4188036  
**Signature:** `wikitable depth=1 wt=multi ht=0 has_colspan`

### Source excerpt
```
{| {{ts|mc|width:840px|lh100}}
|{{ts|ar|pr2}} colspan=2|{{sc|Plate VIII.}}
|-
| {{ts|pr1|vtp}} |
[[File:1911 Britannica-Architecture-Peterborough.png|center|390px|]]
&emsp;&emsp;{{lh|88%|{{smaller|''Photo'', ''J. Valentine, Ltd.''}}{{center|{{sc|Fig. 81}}.—PORCH, PETERBORO’ CATHEDRAL.}}}}

| {{ts|pr1|vtp}} |
[[File:1911 Britannica-Architecture-Ely interior.png|center|340px|]]
&emsp;&emsp;{{lh|88%|{{smaller|''Photo'', ''G. W. Wilson & Co.''}}{{center|{{sc|Fig. 82}}.—ELY CATHEDRAL.}}}}
|}
{{dhr|60%}}
{| {{ts|mc|width:840px|lh100}}
|-
| {{ts|pr1|vtp}} |
[[File:1911 Britannica-Architecture-Pavillon de l'Horloge.png|center|350px|]]
&emsp;&emsp;{{lh|88%|{{smaller|''Photo'', ''Neurdein.''}}{{center|{{sc|Fig. 83}}.—THE LOUVRE—PAVILLON HENRI II.{{dhr|36%}}(''Portion of Lescot’s work on left''.)}}}}
<br><br>
| {{ts|pr1|vtp}} |
[[File:1911 Britannica-Architecture-Spiral staircase.png|center|400px|]]
&emsp;&emsp;{{lh|88%|{{smaller|''Photo'', ''Neurdein.''}}{{center|{{sc|Fig. 84}}.—GRAND STAIRWAY, CHÂTEAU OF BLOIS.}}}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **10** | **10** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'Plate VIII.' | 'Plate VIII.' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
Plate VIII.

{{IMG:1911 Britannica-Architecture-Peterborough.png|PORCH, PETERBORO’ CATHEDRAL}}

{{IMG:1911 Britannica-Architecture-Ely interior.png|ELY CATHEDRAL}}

{{IMG:1911 Britannica-Architecture-Pavillon de l'Horloge.png|THE LOUVRE—PAVILLON HENRI II. (Portion of Lescot’s work on left.)}}

{{IMG:1911 Britannica-Architecture-Spiral staircase.png|GRAND STAIRWAY, CHÂTEAU OF BLOIS}}
```

### Current body
```
Plate VIII.

{{IMG:1911 Britannica-Architecture-Peterborough.png|PORCH, PETERBORO’ CATHEDRAL}}

{{IMG:1911 Britannica-Architecture-Ely interior.png|ELY CATHEDRAL}}

{{IMG:1911 Britannica-Architecture-Pavillon de l'Horloge.png|THE LOUVRE—PAVILLON HENRI II. (Portion of Lescot’s work on left.)}}

{{IMG:1911 Britannica-Architecture-Spiral staircase.png|GRAND STAIRWAY, CHÂTEAU OF BLOIS}}
```

---

## MODERN — vol 02

**Article ID:** 4188037  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|{{Ts|mc|lh100}}
|{{Ts|ar}}|{{sc|Plate IX.}}&nbsp;
|-
|[[File:1911 Britannica-Architecture-Parliament of Hungary.png|800px]]
|-
|{{rh|&emsp;<sup>''Photo'', ''Beer.''</sup>|{{sc|Fig. 115}}.—PARLIAMENT BUILDINGS, BUDAPEST. (STEINDL.)|&emsp;}}
|-style=line-height:40%
|&nbsp;
|-
|[[File:1911 Britannica-Architecture-Parliament of Austria.png|800px]]
|-
|{{rh|&emsp;<sup>''Photo'', ''Löwy.''</sup>|{{sc|Fig. 116}}.—PARLIAMENT BUILDINGS, VIENNA. (HANSEN.)|&emsp;}}
|-style=line-height:40%
|&nbsp;
|-
|[[File:1911 Britannica-Architecture-Reichstag.png|800px]]
|-
|{{rh|&emsp;<sup>''Photo'', ''Linde.''</sup>|{{sc|Fig. 117}}.—PARLIAMENT BUILDINGS, BERLIN. (WALLOT.)|&emsp;}}
|}
<br>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica-Architecture-Parliament of Hungary.png|PARLIAMENT BUILDINGS, BUDAPEST. (STEINDL.)}}

{{IMG:1911 Britannica-Architecture-Parliament of Austria.png|PARLIAMENT BUILDINGS, VIENNA. (HANSEN.)}}

{{IMG:1911 Britannica-Architecture-Reichstag.png|PARLIAMENT BUILDINGS, BERLIN. (WALLOT.)}}
```

### Current body
```
{{IMG:1911 Britannica-Architecture-Parliament of Hungary.png|PARLIAMENT BUILDINGS, BUDAPEST. (STEINDL.)}}

{{IMG:1911 Britannica-Architecture-Parliament of Austria.png|PARLIAMENT BUILDINGS, VIENNA. (HANSEN.)}}

{{IMG:1911 Britannica-Architecture-Reichstag.png|PARLIAMENT BUILDINGS, BERLIN. (WALLOT.)}}
```

---

## Architecture, PLATE X — vol 02

**Article ID:** 4188038  
**Signature:** `wikitable depth=1 wt=multi ht=0`

### Source excerpt
```
{|align="center" cellpadding="0" cellspacing="0"
|[[File:1911 Britannica-Architecture-Palace of Westminster.png|800px]]
|-
|{{smaller|''Photo, F.G.O. Stuart.''}}{{center|{{sc|Fig. 118}}.&mdash;HOUSES OF PARLIAMENT, LONDON. (BARRY.)}}
|}
<br /><br />
{|align="center" cellpadding="0" cellspacing="0"
|[[File:1911 Britannica-Architecture-Scotland Yard.png|800px]]
|-
|{{smaller|''Photo, Emery Walker.''}}{{center|{{sc|Fig. 119}}.&mdash;SCOTLAND YARD, LONDON. (SHAW.)}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica-Architecture-Palace of Westminster.png|HOUSES OF PARLIAMENT, LONDON. (BARRY.)}}

{{IMG:1911 Britannica-Architecture-Scotland Yard.png|SCOTLAND YARD, LONDON. (SHAW.)}}
```

### Current body
```
{{IMG:1911 Britannica-Architecture-Palace of Westminster.png|HOUSES OF PARLIAMENT, LONDON. (BARRY.)}}

{{IMG:1911 Britannica-Architecture-Scotland Yard.png|SCOTLAND YARD, LONDON. (SHAW.)}}
```

---

## MODERN, PLATE XI — vol 02

**Article ID:** 4188039  
**Signature:** `wikitable depth=1 wt=multi ht=0`

### Source excerpt
```
{|align="center" cellpadding="0" cellspacing="0"
|[[File:1911 Britannica-Architecture-Natural History Museum.png|750px]]
|-
|{{smaller|''Photo, Valentine & Sons, Dundee.''}}{{center|{{sc|Fig. 120}}.&mdash;NATURAL HISTORY MUSEUM, SOUTH KENSINGTON. (WATERHOUSE.)}}
|}
<br /><br />
{|align="center" cellpadding="0" cellspacing="0"
|[[File:1911 Britannica-Architecture-Law Courts of Brussels.png|750px]]
|-
|{{smaller|''Photo, M. Gerbeault.''}}{{center|{{sc|Fig. 121}}.&mdash;LAW COURTS, BRUSSELS. (POELAERT.)}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica-Architecture-Natural History Museum.png|NATURAL HISTORY MUSEUM, SOUTH KENSINGTON. (WATERHOUSE.)}}

{{IMG:1911 Britannica-Architecture-Law Courts of Brussels.png|LAW COURTS, BRUSSELS. (POELAERT.)}}
```

### Current body
```
{{IMG:1911 Britannica-Architecture-Natural History Museum.png|NATURAL HISTORY MUSEUM, SOUTH KENSINGTON. (WATERHOUSE.)}}

{{IMG:1911 Britannica-Architecture-Law Courts of Brussels.png|LAW COURTS, BRUSSELS. (POELAERT.)}}
```

---

## Architecture, PLATE XII — vol 02

**Article ID:** 4188040  
**Signature:** `wikitable depth=1 wt=multi ht=0`

### Source excerpt
```
{| {{ts|mc|width:800px}}
|-
| {{ts|pr1|vtp}} |
[[File:1911 Britannica-Architecture-Saint-Augustin de Paris.png|center|500px|]]
{{lh|94%|{{smaller|''Photo, Neurdein.''}}{{center|{{sc|Fig. 122}}.—CHURCH OF ST AUGUSTIN, PARIS.<br>(BALTARD.)}}}}

|  
| {{ts|pr1|vtp}} |
[[File:1911 Britannica-Architecture-Sainte-Trinité, Paris.png|center|270px|]]
{{lh|94%|&nbsp;{{smaller|''Photo, Neurdein.''}}{{center|{{sc|Fig. 123}}.—CHURCH OF LA TRINITÉ,<br>PARIS. (BALLU.)}}}}
|}


{| {{ts|mc|width:800px}}
|-
| {{ts|pr1|vtp|width:270px}} |
[[File:1911 Britannica-Architecture-Saint-Pierre-de-Montrouge.png|center|270px|]]
{{lh|94%|&nbsp;{{smaller|''Photo, A. Lévy.''}}{{center|{{sc|Fig. 124}}.—CHURCH OF ST PIERRE DE MONTROUGE, PARIS. (VAUDREMER.)}}}}

|  
| {{ts|pr1|vtp|width:500px}} |
[[File:1911 Britannica-Architecture-Saint-Vincent-de-Paul.png|center|500px|]]
{{lh|94%|{{smaller|''Photo, Neurdein.''}}{{center|{{sc|Fig. 125}}.—CHURCH OF ST VINCENT DE PAUL, PARIS.<br>(HITTORFF.)}}}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica-Architecture-Saint-Augustin de Paris.png|CHURCH OF ST AUGUSTIN, PARIS. (BALTARD.)}}

{{IMG:1911 Britannica-Architecture-Sainte-Trinité, Paris.png|CHURCH OF LA TRINITÉ, PARIS. (BALLU.)}}

{{IMG:1911 Britannica-Architecture-Saint-Pierre-de-Montrouge.png|CHURCH OF ST PIERRE DE MONTROUGE, PARIS. (VAUDREMER.)}}

{{IMG:1911 Britannica-Architecture-Saint-Vincent-de-Paul.png|CHURCH OF ST VINCENT DE PAUL, PARIS. (HITTORFF.)}}
```

### Current body
```
{{IMG:1911 Britannica-Architecture-Saint-Augustin de Paris.png|CHURCH OF ST AUGUSTIN, PARIS. (BALTARD.)}}

{{IMG:1911 Britannica-Architecture-Sainte-Trinité, Paris.png|CHURCH OF LA TRINITÉ, PARIS. (BALLU.)}}

{{IMG:1911 Britannica-Architecture-Saint-Pierre-de-Montrouge.png|CHURCH OF ST PIERRE DE MONTROUGE, PARIS. (VAUDREMER.)}}

{{IMG:1911 Britannica-Architecture-Saint-Vincent-de-Paul.png|CHURCH OF ST VINCENT DE PAUL, PARIS. (HITTORFF.)}}
```

---

## MODERN, PLATE XIII — vol 02

**Article ID:** 4188041  
**Signature:** `wikitable depth=1 wt=multi ht=0`

### Source excerpt
```
{| {{ts|mc|width:820px}}
|-
| {{ts|pr1|vtp|width:460px}} |
[[File:1911 Britannica-Architecture-Marseilles.png|center|460px|]]
{{lh|88%|{{smaller|''Photo, Neurdein.''}}{{center|{{sc|Fig. 126}}.—CATHEDRAL, MARSEILLES. (VAUDOYER AND ESPERANDIEU.)}}}}

| {{ts|pr1|vtp|width:320px}} |
[[File:1911 Britannica-Architecture-Mairie.png|center|320px|]]
{{lh|88%|{{smaller|''Photo, Neurdein.''}}{{center|{{sc|Fig. 127}}.—MAIRIE, {{sc|Xth}} ARRONDISSEMENT, PARIS. (ROUYER.)}}}}
|}
<br>
{| {{ts|mc}}
|-
| {{ts|pr1|vtp}} |
[[File:1911 Britannica-Architecture-Ste Geneviève.png|center|800px|]]
{{lh|88%|{{smaller|''Photo, A. Lévy.''}}{{center|{{sc|Fig. 128}}.—BIBLIOTHÈQUE STE GENEVIÈVE, PARIS. (LABROUSTE.)}}}}
|}
<br>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica-Architecture-Marseilles.png|CATHEDRAL, MARSEILLES. (VAUDOYER AND ESPERANDIEU.)}}

{{IMG:1911 Britannica-Architecture-Mairie.png|MAIRIE, Xth ARRONDISSEMENT, PARIS. (ROUYER.)}}

{{IMG:1911 Britannica-Architecture-Ste Geneviève.png|BIBLIOTHÈQUE STE GENEVIÈVE, PARIS. (LABROUSTE.)}}
```

### Current body
```
{{IMG:1911 Britannica-Architecture-Marseilles.png|CATHEDRAL, MARSEILLES. (VAUDOYER AND ESPERANDIEU.)}}

{{IMG:1911 Britannica-Architecture-Mairie.png|MAIRIE, Xth ARRONDISSEMENT, PARIS. (ROUYER.)}}

{{IMG:1911 Britannica-Architecture-Ste Geneviève.png|BIBLIOTHÈQUE STE GENEVIÈVE, PARIS. (LABROUSTE.)}}
```

---

## Architecture, PLATE XIV — vol 02

**Article ID:** 4188042  
**Signature:** `wikitable depth=1 wt=multi ht=0`

### Source excerpt
```
{|align="center" cellpadding="0" cellspacing="0"
|[[File:1911 Britannica-Architecture-Pavillon Richelieu.png|800px]]
|-
|{{smaller|''Photo, L.L. Paris.''}}{{center|{{sc|Fig. 129}}.&mdash;PAVILLON RICHELIEU, THE LOUVRE, PARIS. (VISCONTI.)}}
|}
<br /><br />
{|align="center" cellpadding="0" cellspacing="0"
|[[File:1911 Britannica-Architecture-Petit Palais.png|800px]]
|-
|{{smaller|''Photo, Neurdin.''}}{{center|{{sc|Fig. 130}}.&mdash;PETIT PALAIS, PARIS. (GIRAULT.)}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica-Architecture-Pavillon Richelieu.png|PAVILLON RICHELIEU, THE LOUVRE, PARIS. (VISCONTI.)}}

{{IMG:1911 Britannica-Architecture-Petit Palais.png|PETIT PALAIS, PARIS. (GIRAULT.)}}
```

### Current body
```
{{IMG:1911 Britannica-Architecture-Pavillon Richelieu.png|PAVILLON RICHELIEU, THE LOUVRE, PARIS. (VISCONTI.)}}

{{IMG:1911 Britannica-Architecture-Petit Palais.png|PETIT PALAIS, PARIS. (GIRAULT.)}}
```

---

## MODERN — vol 02

**Article ID:** 4188047  
**Signature:** `wikitable depth=1 wt=1 ht=0 has_colspan`

### Source excerpt
```
{| {{ts|mc|line-height:88%|width:800px}}
|{{Ts|ar}} colspan=2|{{sc|Plate XV.}}&ensp;
|-
| {{ts|pr1|vtp|width:320px}} |
[[File:1911 Britannica-Architecture-Flat-Iron.png|center|298px]]<br>
 {{smaller|Copyright 1903 by Detroit Photographic Co.}}{{c|{{sc|Fig.}} 131.—“FLAT-IRON” BUILDING, NEW YORK.<br>{{smaller|(For method of construction, see {{EB1911 article link|Steel Construction}},<br>and Plate II., Fig. 4, of that article.)}}}}

| {{ts|pl1|vtp|width:430px}} |
[[File:1911 Britannica-Architecture-The Breakers.png|center|430px]]<br>
 {{smaller|Copyright 1899 by Detroit Photographic Co.}}{{c|{{sc|Fig.}} 132.—A NEWPORT, R.I., “COTTAGE”: “THE BREAKERS.”}}

[[File:1911 Britannica-Architecture-Metropolitan Club.png|center|430px]]<br>
{{csc|Fig. 133.—THE METROPOLITAN CLUB, NEW YORK.}}


[[File:1911 Britannica-Architecture-University Club.png|center|430px]]
 {{smaller|Copyright 1905 by Detroit Publishing Co.}}{{csc|Fig. 134.—THE UNIVERSITY CLUB, NEW YORK.}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **9** | **9** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'Plate XV.' | 'Plate XV.' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
Plate XV.

{{IMG:1911 Britannica-Architecture-Flat-Iron.png|A NEWPORT, R.I., “COTTAGE”: “THE BREAKERS.”}}

{{IMG:1911 Britannica-Architecture-The Breakers.png|THE METROPOLITAN CLUB, NEW YORK}}

{{IMG:1911 Britannica-Architecture-Metropolitan Club.png|THE UNIVERSITY CLUB, NEW YORK}}

{{IMG:1911 Britannica-Architecture-University Club.png}}
```

### Current body
```
Plate XV.

{{IMG:1911 Britannica-Architecture-Flat-Iron.png|A NEWPORT, R.I., “COTTAGE”: “THE BREAKERS.”}}

{{IMG:1911 Britannica-Architecture-The Breakers.png|THE METROPOLITAN CLUB, NEW YORK}}

{{IMG:1911 Britannica-Architecture-Metropolitan Club.png|THE UNIVERSITY CLUB, NEW YORK}}

{{IMG:1911 Britannica-Architecture-University Club.png}}
```

---

## Architecture, PLATE XVI — vol 02

**Article ID:** 4188048  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{| {{ts|mc|width:1000px}}
|-
| {{ts|pr1|vtp|width:50%}} |
[[File:1911 Britannica-Architecture-Public Library Boston.png|center|500px|]]
{{left|{{lh|88%|{{smaller|''Photo, Detroit Publishing Co.''}}}}<br />{{center|{{sc|Fig. 135}}.&mdash;PUBLIC LIBRARY, BOSTON. (McKIM, MEAD & WHITE.)}}}}
<br /><br />
[[File:1911 Britannica-Architecture-Trinity Church.png|center|500px|]]
{{left|{{lh|88%|{{smaller|''Photo, Elmer Chickering.''}}}}<br />{{center|{{sc|Fig. 137}}.&mdash;TRINITY CHURCH, BOSTON. (H. H. RICHARDSON.)}}}}

| {{ts|pl1|vtp|width:50%}} |
[[File:1911 Britannica-Architecture-Public Library New York.png|center|520px|]]
{{left|{{lh|88%|{{smaller|''Photo, Geo. P. Hall & Son.''}}}}<br />{{center|{{sc|Fig. 136}}.&mdash;PUBLIC LIBRARY, NEW YORK. (CARRÈRE & HASTINGS.)}}}}
<br /><br />
[[File:1911 Britannica-Architecture-State Capitol.png|center|500px|]]
{{left|{{lh|88%|{{smaller|''Copyright 1906 by Detroit Publishing Co.''}}}}<br />{{center|{{sc|Fig. 138}}.&mdash;STATE CAPITOL, HARTFORD, CONNECTICUT.}}}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica-Architecture-Public Library Boston.png|PUBLIC LIBRARY, BOSTON. (McKIM, MEAD & WHITE.)}}

{{IMG:1911 Britannica-Architecture-Trinity Church.png|TRINITY CHURCH, BOSTON. (H. H. RICHARDSON.)}}

{{IMG:1911 Britannica-Architecture-Public Library New York.png|PUBLIC LIBRARY, NEW YORK. (CARRÈRE & HASTINGS.)}}

{{IMG:1911 Britannica-Architecture-State Capitol.png|STATE CAPITOL, HARTFORD, CONNECTICUT}}
```

### Current body
```
{{IMG:1911 Britannica-Architecture-Public Library Boston.png|PUBLIC LIBRARY, BOSTON. (McKIM, MEAD & WHITE.)}}

{{IMG:1911 Britannica-Architecture-Trinity Church.png|TRINITY CHURCH, BOSTON. (H. H. RICHARDSON.)}}

{{IMG:1911 Britannica-Architecture-Public Library New York.png|PUBLIC LIBRARY, NEW YORK. (CARRÈRE & HASTINGS.)}}

{{IMG:1911 Britannica-Architecture-State Capitol.png|STATE CAPITOL, HARTFORD, CONNECTICUT}}
```

---

## Armour Plates, PLATE I — vol 02

**Article ID:** 4188207  
**Signature:** `wikitable depth=1 wt=multi ht=0`

### Source excerpt
```
{|align="center" cellpadding="0" cellspacing="0"
|[[File:1911 Britannica - Harveyized Shield.png|600px]]
|-
|{{center|{{smaller|{{sc|Fig. 1}}.&mdash;HARVEYIZED SHIELD, 4.5 INCHES THICK, ON 6-INCH PEDESTAL MOUNT, AFTER ATTACK<br /> BY 5-INCH AND 6-INCH CAPPED ARMOUR-PIERCING SHOT.}}}}
|}
<br /><br />
{|align="center" cellpadding="0" cellspacing="0"
|[[File:1911 Britannica - Gun Shield.png|600px]]
|-
|{{center|{{smaller|{{sc|Fig. 2}}.&mdash;GUN SHIELD, 6 INCHES THICK, AFTER ATTACK.<br /> 
(HADFIELD.)}}}}
|}
<br /><br />
{|align="center" cellpadding="0" cellspacing="0"
|[[File:1911 Britannica - Krupp-Cemented Plate.png|600px]]
|-
|{{center|{{smaller|{{sc|Fig. 3}}.&mdash;KRUPP-CEMENTED PLATE, 11.8 INCHES THICK, AFTER ATTACK.<br /> 
(KRUPP, MEPPEN.)}}}}
|}
<br /><br />
{|align="center" cellpadding="0" cellspacing="0"
|[[File:1911 Britannica - Krupp-Cemented Plate2.png|600px]]
|-
|{{center|{{smaller|{{sc|Fig. 4}}.&mdash;KRUPP-CEMENTED PLATE, 9 INCHES THICK, AFTER ATTACK.<br /> 
(ARMSTRONG, WHITWORTH & CO.)}}}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica - Harveyized Shield.png|HARVEYIZED SHIELD, 4.5 INCHES THICK, ON 6-INCH PEDESTAL MOUNT, AFTER ATTACK BY 5-INCH AND 6-INCH CAPPED ARMOUR-PIERCING SHOT}}

{{IMG:1911 Britannica - Gun Shield.png|GUN SHIELD, 6 INCHES THICK, AFTER ATTACK. (HADFIELD.)}}

{{IMG:1911 Britannica - Krupp-Cemented Plate.png|KRUPP-CEMENTED PLATE, 11.8 INCHES THICK, AFTER ATTACK. (KRUPP, MEPPEN.)}}

{{IMG:1911 Britannica - Krupp-Cemented Plate2.png|KRUPP-CEMENTED PLATE, 9 INCHES THICK, AFTER ATTACK. (ARMSTRONG, WHITWORTH & CO.)}}
```

### Current body
```
{{IMG:1911 Britannica - Harveyized Shield.png|HARVEYIZED SHIELD, 4.5 INCHES THICK, ON 6-INCH PEDESTAL MOUNT, AFTER ATTACK BY 5-INCH AND 6-INCH CAPPED ARMOUR-PIERCING SHOT}}

{{IMG:1911 Britannica - Gun Shield.png|GUN SHIELD, 6 INCHES THICK, AFTER ATTACK. (HADFIELD.)}}

{{IMG:1911 Britannica - Krupp-Cemented Plate.png|KRUPP-CEMENTED PLATE, 11.8 INCHES THICK, AFTER ATTACK. (KRUPP, MEPPEN.)}}

{{IMG:1911 Britannica - Krupp-Cemented Plate2.png|KRUPP-CEMENTED PLATE, 9 INCHES THICK, AFTER ATTACK. (ARMSTRONG, WHITWORTH & CO.)}}
```

---

## Armour Plates, PLATE II — vol 02

**Article ID:** 4188208  
**Signature:** `wikitable depth=1 wt=multi ht=0`

### Source excerpt
```
{|align="center" cellpadding="0" cellspacing="0"
|[[File:1911 Britannica - Beardmore Cemented Plate.png|600px]]
|-
|{{center|{{smaller|{{sc|Fig. 5}}.&mdash;BEARDMORE CEMENTED PLATE, 6-INCHES THICK, AFTER ATTACK BY 6-INCH SHOT.<br />
{{smaller|(From Brassey’s Naval Annual, 1902 by permission.)}}}}}}
|}
<br /><br />
{|align="center" cellpadding="0" cellspacing="0"
|[[File:1911 Britannica - Krupp-Cemented Plate3.png|600px]]
|-
|{{center|{{smaller|{{sc|Fig. 6}}.&mdash;KRUPP-CEMENTED PLATE, 3 INCHES THICK, AFTER ATTACK.<br /> 
(VICKERS, SONS & MAXIM.)}}}}
|}
<br /><br />
{|align="center" cellpadding="0" cellspacing="0"
|[[File:1911 Britannica - Cemented Plate Back.png|600px]]
|-
|{{center|{{smaller|{{sc|Fig. 7}}.&mdash;BACK OF A 6-INCH PLATE SHOWING ACTION OF CAPPED AND UNCAPPED PROJECTILES.}}}}
|}
<br /><br />
{|align="center" cellpadding="0" cellspacing="0"
|[[File:1911 Britannica - Krupp Plate Back.png|600px]]
|-
|{{center|{{smaller|{{sc|Fig. 8}}.&mdash;BACK OF KRUPP PLATE 9.8 INCHES THICK, AFTER ATTACK, WITH CAPPED PROJECTILE.<br /> (KRUPP, MEPPEN.)<br />
{{smaller|(From Brassey’s Naval Annual, by permission.)}}}}}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica - Beardmore Cemented Plate.png|BEARDMORE CEMENTED PLATE, 6-INCHES THICK, AFTER ATTACK BY 6-INCH SHOT. (From Brassey’s Naval Annual, 1902 by permission.)}}

{{IMG:1911 Britannica - Krupp-Cemented Plate3.png|KRUPP-CEMENTED PLATE, 3 INCHES THICK, AFTER ATTACK. (VICKERS, SONS & MAXIM.)}}

{{IMG:1911 Britannica - Cemented Plate Back.png|BACK OF A 6-INCH PLATE SHOWING ACTION OF CAPPED AND UNCAPPED PROJECTILES}}

{{IMG:1911 Britannica - Krupp Plate Back.png|BACK OF KRUPP PLATE 9.8 INCHES THICK, AFTER ATTACK, WITH CAPPED PROJECTILE. (KRUPP, MEPPEN.) (From Brassey’s Naval Annual, by permission.)}}
```

### Current body
```
{{IMG:1911 Britannica - Beardmore Cemented Plate.png|BEARDMORE CEMENTED PLATE, 6-INCHES THICK, AFTER ATTACK BY 6-INCH SHOT. (From Brassey’s Naval Annual, 1902 by permission.)}}

{{IMG:1911 Britannica - Krupp-Cemented Plate3.png|KRUPP-CEMENTED PLATE, 3 INCHES THICK, AFTER ATTACK. (VICKERS, SONS & MAXIM.)}}

{{IMG:1911 Britannica - Cemented Plate Back.png|BACK OF A 6-INCH PLATE SHOWING ACTION OF CAPPED AND UNCAPPED PROJECTILES}}

{{IMG:1911 Britannica - Krupp Plate Back.png|BACK OF KRUPP PLATE 9.8 INCHES THICK, AFTER ATTACK, WITH CAPPED PROJECTILE. (KRUPP, MEPPEN.) (From Brassey’s Naval Annual, by permission.)}}
```

---

## Artillery, PLATE I — vol 02

**Article ID:** 4188329  
**Signature:** `wikitable depth=1 wt=multi ht=0`

### Source excerpt
```
{|align="center" cellpadding="5" cellspacing="0"
|[[File:1911 Britannica - 15th Century Field Artillery.png|center|470px|]] || [[File:1911 Britannica - Artillery Napoleon III.png|center|350px|]]
|}
{|align="center"
|{{smaller|{{sc|Figs.}} 1 and 2.&mdash;15th Century Field Artillery (Napoleon III).}}
|}
<br /><br />
{|align="center" cellpadding="2" cellspacing="0"
|[[File:1911 Britannica - Field Artillery 1525.png|350px]]
|-
|align="center"|{{smaller|{{sc|Fig.}} 3.&mdash;Field Artillery. 1525 (Napoleon III).}}
|}
<br /><br />
{|align="center" cellpadding="2" cellspacing="0"
|[[File:1911 Britannica - French Artillery 1735.png|600px]]
|-
|align="center"|{{smaller|{{sc|Fig.}} 4.&mdash;French Artillery 1735 (''Journal d’Armée'',1835).}}
|}
<br /><br />
{|align="center" cellpadding="2" cellspacing="0"
|[[File:1911 Britannica - French Artillery 1835.png|600px]]
|-
|align="center"|{{smaller|{{sc|Fig.}} 5.&mdash;French Field Artillery,1835 (''Journal d’Armée'',1835).}}
|}
<br /><br />
{|align="center" cellpadding="2" cellspacing="0"
|[[File:1911 Britannica - Roveredo 1796.png|1040px]]
|-
|align="center"|{{smaller|{{sc|Fig.}} 6.&mdash;Artillery in Action, Roveredo, 1796 (C. Vernet).}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 6 | 6 |
| captioned       | 5 | 5 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **11** | **11** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica - 15th Century Field Artillery.png|Figs. 1 and 2.— 15th Century Field Artillery (Napoleon III)}}

{{IMG:1911 Britannica - Artillery Napoleon III.png|Field Artillery. 1525 (Napoleon III)}}

{{IMG:1911 Britannica - Field Artillery 1525.png|French Artillery 1735 (Journal d’Armée,1835)}}

{{IMG:1911 Britannica - French Artillery 1735.png|French Field Artillery,1835 (Journal d’Armée,1835)}}

{{IMG:1911 Britannica - French Artillery 1835.png|Artillery in Action, Roveredo, 1796 (C. Vernet)}}

{{IMG:1911 Britannica - Roveredo 1796.png}}
```

### Current body
```
{{IMG:1911 Britannica - 15th Century Field Artillery.png|Figs. 1 and 2.— 15th Century Field Artillery (Napoleon III)}}

{{IMG:1911 Britannica - Artillery Napoleon III.png|Field Artillery. 1525 (Napoleon III)}}

{{IMG:1911 Britannica - Field Artillery 1525.png|French Artillery 1735 (Journal d’Armée,1835)}}

{{IMG:1911 Britannica - French Artillery 1735.png|French Field Artillery,1835 (Journal d’Armée,1835)}}

{{IMG:1911 Britannica - French Artillery 1835.png|Artillery in Action, Roveredo, 1796 (C. Vernet)}}

{{IMG:1911 Britannica - Roveredo 1796.png}}
```

---

## Artillery, PLATE II — vol 02

**Article ID:** 4188330  
**Signature:** `wikitable depth=1 wt=multi ht=0`

### Source excerpt
```
{|align="center" cellpadding="3" cellspacing="0"
|[[File:1911 Britannica - Breach Loading.png|800px]]
|-
|align="left"|{{smaller|''Photo, Gale & Polden.''}}
|-
|align="center"| {{sc|BREACH LOADING FIELD BATTERY (15-Pr. B.L.).}}
|}
<br />
{|align="center" cellpadding="3" cellspacing="0"
|[[File:1911 Britannica - Quick-Firing.png|800px]]
|-
|align="left"|{{smaller|''Photo, Gale & Polden.''}}
|-
|align="center"| {{sc|QUICK-FIRING HORSE ARTILLERY (ROYAL HORSE ARTILLERY, 13-Pr. Q.F.).}}
|}
<br />
{|align="center" cellpadding="3" cellspacing="0"
|[[File:1911 Britannica - Q.F. Field Artillery.png|center|400px|]] || [[File:1911 Britannica - Artillery Manoeuvring.png|center|400px|]]
|-
|align="left"|{{smaller|''Photo, Gale & Polden.''}}
|align="left"|{{smaller|''Photo, Topical Press.''}}
|-
|align="center"| {{sc|Q.F. FIELD ARTILLERY (18-Pr. Q.F., R.F.A.).}}
|align="center"| {{sc|FRENCH (75-Mm. Q.F.) FIELD ARTILLERY MANOEUVRING.}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica - Breach Loading.png|BREACH LOADING FIELD BATTERY (15-Pr. B.L.) (Photo, Gale & Polden)}}

{{IMG:1911 Britannica - Quick-Firing.png|QUICK-FIRING HORSE ARTILLERY (ROYAL HORSE ARTILLERY, 13-Pr. Q.F.) (Photo, Gale & Polden)}}

{{IMG:1911 Britannica - Q.F. Field Artillery.png|Q.F. FIELD ARTILLERY (18-Pr. Q.F., R.F.A.) (Photo, Gale & Polden)}}

{{IMG:1911 Britannica - Artillery Manoeuvring.png|FRENCH (75-Mm. Q.F.) FIELD ARTILLERY MANOEUVRING (Photo, Topical Press)}}
```

### Current body
```
{{IMG:1911 Britannica - Breach Loading.png|BREACH LOADING FIELD BATTERY (15-Pr. B.L.) (Photo, Gale & Polden)}}

{{IMG:1911 Britannica - Quick-Firing.png|QUICK-FIRING HORSE ARTILLERY (ROYAL HORSE ARTILLERY, 13-Pr. Q.F.) (Photo, Gale & Polden)}}

{{IMG:1911 Britannica - Q.F. Field Artillery.png|Q.F. FIELD ARTILLERY (18-Pr. Q.F., R.F.A.) (Photo, Gale & Polden)}}

{{IMG:1911 Britannica - Artillery Manoeuvring.png|FRENCH (75-Mm. Q.F.) FIELD ARTILLERY MANOEUVRING (Photo, Topical Press)}}
```

---

## PLATE (VOL. 2, P. 781) — vol 02

**Article ID:** 4188417  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|align="center" cellpadding="0" cellspacing="0"
|-
| width:50% |
[[File:1911 Britannica - Map of Asia1.png|center|500px|]]
| width:50% |
[[File:1911 Britannica - Map of Asia2.png|center|500px|]]
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 0 | 0 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **2** | **2** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica - Map of Asia1.png}}

{{IMG:1911 Britannica - Map of Asia2.png}}
```

### Current body
```
{{IMG:1911 Britannica - Map of Asia1.png}}

{{IMG:1911 Britannica - Map of Asia2.png}}
```

---

## Aurora, PLATE I — vol 02

**Article ID:** 4188754  
**Signature:** `wikitable depth=1 wt=multi ht=0`

### Source excerpt
```
{{EB1911 fine print/s}}
{|{{Ts|ma|ac|width:520px}}
|-
|[[File:1911 Britannica - Aurora Polaris - Auroral arcs.png|520px]]
|-
|align="center"|{{sc|Fig.}} 1—TWO TYPES OF AURORAL ARCS.
|}


{|{{Ts|ma|ac|width:500px}}
|[[File:1911 Britannica - Aurora Polaris - Auroral rays.png|500px]]
|-
|{{sc|Fig.}} 2—TWO TYPES OF AURORAL RAYS.
|}

{{center|{{EB1911 Fine Print|(From the ''Internationale Polarforschung'', 1882–1883, by permission of the<br>''Kaiserlichen Akademie der Wissenschaften'', Vienna.)}}}}
<br><br>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | '(From the Internationale Polarforschung, 1882–1883, by permission of the Kaiserlichen Akademie der Wissenschaften, Vienn' | '(From the Internationale Polarforschung, 1882–1883, by permission of the Kaiserlichen Akademie der Wissenschaften, Vienn' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica - Aurora Polaris - Auroral arcs.png|Fig. 1—TWO TYPES OF AURORAL ARCS}}

{{IMG:1911 Britannica - Aurora Polaris - Auroral rays.png|Fig. 2—TWO TYPES OF AURORAL RAYS}}

(From the Internationale Polarforschung, 1882–1883, by permission of the Kaiserlichen Akademie der Wissenschaften, Vienna.)
```

### Current body
```
{{IMG:1911 Britannica - Aurora Polaris - Auroral arcs.png|Fig. 1—TWO TYPES OF AURORAL ARCS}}

{{IMG:1911 Britannica - Aurora Polaris - Auroral rays.png|Fig. 2—TWO TYPES OF AURORAL RAYS}}

(From the Internationale Polarforschung, 1882–1883, by permission of the Kaiserlichen Akademie der Wissenschaften, Vienna.)
```

---

## Aurora, PLATE II — vol 02

**Article ID:** 4188755  
**Signature:** `wikitable depth=1 wt=multi ht=0`

### Source excerpt
```
{|align="center" cellpadding="0" cellspacing="0"
|[[File:1911 Britannica - Aurora Polaris - Auroral bands.png|550px]]
|-
|align="center"|{{smaller|{{sc|Fig.}} 3—AURORAL BANDS.}}
|}


{|align="center" cellpadding="0" cellspacing="0"
|[[File:1911 Britannica - Aurora Polaris - Auroral curtain.png|550px]]
|-
|align="center"|{{smaller|{{sc|Fig.}} 4—AURORAL CURTAIN BELOW AN ARC.}}
|}


{|align="center" cellpadding="0" cellspacing="0"
|[[File:1911 Britannica - Aurora Polaris - Auroral corona.png|550px]]
|-
|align="center"|{{smaller|{{sc|Fig.}} 5.—AURORAL CORONA.}}
|}
<br /><br />
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica - Aurora Polaris - Auroral bands.png|Fig. 3—AURORAL BANDS}}

{{IMG:1911 Britannica - Aurora Polaris - Auroral curtain.png|Fig. 4—AURORAL CURTAIN BELOW AN ARC}}

{{IMG:1911 Britannica - Aurora Polaris - Auroral corona.png|AURORAL CORONA}}
```

### Current body
```
{{IMG:1911 Britannica - Aurora Polaris - Auroral bands.png|Fig. 3—AURORAL BANDS}}

{{IMG:1911 Britannica - Aurora Polaris - Auroral curtain.png|Fig. 4—AURORAL CURTAIN BELOW AN ARC}}

{{IMG:1911 Britannica - Aurora Polaris - Auroral corona.png|AURORAL CORONA}}
```

---

## Babylonia and Assyria — vol 03

**Article ID:** 4237601  
**Signature:** `wikitable depth=1 wt=multi ht=0 has_colspan`

### Source excerpt
```
{|{{Ts|ma|ac|lh120}}
|{{Ts|al}}|''Photos'', ''Mansell & Co''.||colspan=4 {{Ts|ar}}|{{sc|Plate I.}}
|-
|[[File:1911 Britannica - Babylonia-Victory stele.png|center|250px]] ||  ||[[File:1911 Britannica - Babylonia-Patesi of Lagash.png|center|250px]]||  ||[[File:1911 Britannica - Babylonia-Khammurabi Code.png|center|250px]]
|-
|STELE OF VICTORY OF NARAM-SIN,<br>KING OF AGADE. Louvre.<br><br>||
|FIGURE OF GUDEA, PATESI OF<br> LAGASH. Louvre.<br><br>||
|FROM STELE ENGRAVED WITH<br>KHAMMURABI CODE OF LAWS.<br><br>
|-
|[[File:1911 Britannica - Babylonia-Aradsin.png|250px]] || ||[[File:1911 Britannica - Babylonia-Boundary-stone.png|250px]]|| ||[[File:1911 Britannica - Babylonia-Colossal winged.png|250px]] ||
|-
|COPPER VOTIVE FIGURE OF ARAD-<br>SIN, KING OF LARSA.<br>||
|BOUNDARY-STONE SCULPTURED<br> WITH EMBLEMS OF THE GODS;<br>REIGN OF NEBUCHADREZZAR I.||
|{{Ts|al}}|COLOSSAL WINGED AND HUMAN-<br> HEADED LION FROM THE<br> PALACE OF ASSUR-NAZIR-PAL.
|}


{| {{ts|mc|width:780px|lh120|ac}}
|-
| {{ts|pr1|vtp|width:33%}} |<br><br>
[[File:1911 Britannica - Babylonia-Assur-Nazir-Pal.png|center|250px]]
<br>STATUE OF ASSUR-NAZIR-PAL,<br>KING OF ASSYRIA.
| {{ts|pl1|vtp|width:34%}} |<br>
[[File:1911 Britannica - Babylonia-Relief Assur-Bani-Pal.png|center|250px]]<br>
RELIEF REPRESENTING ASSUR-<br>BANI-PAL SPEARING A LION.
<br>
[[File:1911 Britannica - Babylonia-Dying Lion.png|center|250px]]
<br>FIGURE OF A DYING LION, FROM THE LION-HUNT RELIEFS OF<br>ASSUR-BANI-PAL.     
| {{ts|pl15|vtp|width:3
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 10 | 10 |
| captioned       | 10 | 10 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **20** | **20** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica - Babylonia-Victory stele.png|STELE OF VICTORY OF NARAM-SIN, KING OF AGADE. Louvre}}

{{IMG:1911 Britannica - Babylonia-Patesi of Lagash.png|FIGURE OF GUDEA, PATESI OF LAGASH. Louvre}}

{{IMG:1911 Britannica - Babylonia-Khammurabi Code.png|FROM STELE ENGRAVED WITH KHAMMURABI CODE OF LAWS}}

{{IMG:1911 Britannica - Babylonia-Aradsin.png|COPPER VOTIVE FIGURE OF ARAD- SIN, KING OF LARSA}}

{{IMG:1911 Britannica - Babylonia-Boundary-stone.png|BOUNDARY-STONE SCULPTURED WITH EMBLEMS OF THE GODS; REIGN OF NEBUCHADREZZAR I}}

{{IMG:1911 Britannica - Babylonia-Colossal winged.png|COLOSSAL WINGED AND HUMAN- HEADED LION FROM THE PALACE OF ASSUR-NAZIR-PAL}}

{{IMG:1911 Britannica - Babylonia-Assur-Nazir-Pal.png|STATUE OF ASSUR-NAZIR-PAL, KING OF ASSYRIA}}

{{IMG:1911 Britannica - Babylonia-Relief Assur-Bani-Pal.png|RELIEF REPRESENTING ASSUR- BANI-PAL SPEARING A LION}}

{{IMG:1911 Britannica - Babylonia-Dying Lion.png|FIGURE OF A DYING LION, FROM THE LION-HUNT RELIEFS OF ASSUR-BANI-PAL}}

{{IMG:1911 Britannica - Babylonia-God Nebo.png|STATUE OF THE GOD NEBO; REIGN OF ADAD-NIRARI III}}
```

### Current body
```
{{IMG:1911 Britannica - Babylonia-Victory stele.png|STELE OF VICTORY OF NARAM-SIN, KING OF AGADE. Louvre}}

{{IMG:1911 Britannica - Babylonia-Patesi of Lagash.png|FIGURE OF GUDEA, PATESI OF LAGASH. Louvre}}

{{IMG:1911 Britannica - Babylonia-Khammurabi Code.png|FROM STELE ENGRAVED WITH KHAMMURABI CODE OF LAWS}}

{{IMG:1911 Britannica - Babylonia-Aradsin.png|COPPER VOTIVE FIGURE OF ARAD- SIN, KING OF LARSA}}

{{IMG:1911 Britannica - Babylonia-Boundary-stone.png|BOUNDARY-STONE SCULPTURED WITH EMBLEMS OF THE GODS; REIGN OF NEBUCHADREZZAR I}}

{{IMG:1911 Britannica - Babylonia-Colossal winged.png|COLOSSAL WINGED AND HUMAN- HEADED LION FROM THE PALACE OF ASSUR-NAZIR-PAL}}

{{IMG:1911 Britannica - Babylonia-Assur-Nazir-Pal.png|STATUE OF ASSUR-NAZIR-PAL, KING OF ASSYRIA}}

{{IMG:1911 Britannica - Babylonia-Relief Assur-Bani-Pal.png|RELIEF REPRESENTING ASSUR- BANI-PAL SPEARING A LION}}

{{IMG:1911 Britannica - Babylonia-Dying Lion.png|FIGURE OF A DYING LION, FROM THE LION-HUNT RELIEFS OF ASSUR-BANI-PAL}}

{{IMG:1911 Britannica - Babylonia-God Nebo.png|STATUE OF THE GOD NEBO; REIGN OF ADAD-NIRARI III}}
```

---

## Babylonia and Assyria, PLATE II — vol 03

**Article ID:** 4237602  
**Signature:** `wikitable depth=1 wt=multi ht=0`

### Source excerpt
```
{| {{ts|mc|width:800px}}
|-
| {{ts|pr1|vtp|width:34%}} |[[File:1911 Britannica - Babylonia-Sculptured relief.png|center|270px|]]
{{c|{{lh|88%|SCULPTURED RELIEF OF THE REIGN OF ASSUR-NAZIR-PAL; FOREIGNERS BRINGING TRIBUTE.}}}}
[[File:1911 Britannica - Babylonia-Ivory panels.png|center|270px|]]
{{c|{{lh|88%|IVORY PANELS WITH LINE ENGRAVING; FROM NIMRUD.}}}}
| {{ts|pl1|vtp|width:32%}} |
[[File:1911 Britannica - Babylonia-Nimrud.png|center|280px|]]
{{c|{{lh|88%|ARCHITECTURAL ORNAMENTS OF PAINTED TERRA-COTTA; FROM  NIMRUD.}}}}
[[File:1911 Britannica - Babylonia-Section of bronze.png|center|280px|]]
{{c|{{lh|88%|SECTION OF BRONZE SHEATHING FROM GATES OF SHALMANESER II.}}}}
[[File:1911 Britannica - Babylonia-Bronze lion.png|center|280px|]]
{{c|{{lh|88%|BRONZE LION-WEIGHT.}}}}
| {{ts|pr1|vtp|width:34%}} |[[File:1911 Britannica - Babylonia-Relief.png|right|250px|]]
{{c|{{lh|88%|SCULPTURED RELIEF OF THE REIGN OF ASSUR-BANI-PAL; MYTHOLOGICAL BEINGS IN CONFLICT.}}}}
[[File:1911 Britannica - Babylonia-Sculptured paving slab.png|right|250px|]]
{{c|{{lh|88%|PORTION OF SCULPTURED PAVING SLAB FROM A DOORWAY IN ASSUR-BANI-PAL'S PALACE AT KUYUNJIK (NINEVEH).}}}}
|}
{| {{ts|mc|width:800px}}
|-
| {{ts|pr1|vtp|width:25%}} |[[File:1911 Britannica - Babylonia-Pur-Sin.png|center|190px|]]
{{c|{{lh|88%|STAMPED BRICK-INSCRIPTION OF BŪR-SIN, KING OF UR.}}}}
| {{ts|pr1|vtp|width:25%}} |[[File:1911 Britannica - Babylonia-Tushratta.png|center|270px|]]
{{c|{{lh|88%|LETTER FROM TUSHRATTA, KING OF MITANI, TO A
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 11 | 11 |
| captioned       | 11 | 11 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **22** | **22** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica - Babylonia-Sculptured relief.png|SCULPTURED RELIEF OF THE REIGN OF ASSUR-NAZIR-PAL; FOREIGNERS BRINGING TRIBUTE}}

{{IMG:1911 Britannica - Babylonia-Ivory panels.png|IVORY PANELS WITH LINE ENGRAVING; FROM NIMRUD}}

{{IMG:1911 Britannica - Babylonia-Nimrud.png|ARCHITECTURAL ORNAMENTS OF PAINTED TERRA-COTTA; FROM NIMRUD}}

{{IMG:1911 Britannica - Babylonia-Section of bronze.png|SECTION OF BRONZE SHEATHING FROM GATES OF SHALMANESER II}}

{{IMG:1911 Britannica - Babylonia-Bronze lion.png|BRONZE LION-WEIGHT}}

{{IMG:1911 Britannica - Babylonia-Relief.png|SCULPTURED RELIEF OF THE REIGN OF ASSUR-BANI-PAL; MYTHOLOGICAL BEINGS IN CONFLICT}}

{{IMG:1911 Britannica - Babylonia-Sculptured paving slab.png|PORTION OF SCULPTURED PAVING SLAB FROM A DOORWAY IN ASSUR-BANI-PAL'S PALACE AT KUYUNJIK (NINEVEH)}}

{{IMG:1911 Britannica - Babylonia-Pur-Sin.png|STAMPED BRICK-INSCRIPTION OF BŪR-SIN, KING OF UR}}

{{IMG:1911 Britannica - Babylonia-Tushratta.png|LETTER FROM TUSHRATTA, KING OF MITANI, TO AMENOPHIS III}}

{{IMG:1911 Britannica - Babylonia-Sennacherib.png|PRISM OF SENNACHERIB, INSCRIBED WITH HISTORICAL ANNALS OF HIS REIGN}}

{{IMG:1911 Britannica - Babylonia-Tablet.png|TABLET FROM ASSUR-BANI-PAL'S LIBRARY, INSCRIBED WITH MYTHOLOGICAL TEXT}}
```

### Current body
```
{{IMG:1911 Britannica - Babylonia-Sculptured relief.png|SCULPTURED RELIEF OF THE REIGN OF ASSUR-NAZIR-PAL; FOREIGNERS BRINGING TRIBUTE}}

{{IMG:1911 Britannica - Babylonia-Ivory panels.png|IVORY PANELS WITH LINE ENGRAVING; FROM NIMRUD}}

{{IMG:1911 Britannica - Babylonia-Nimrud.png|ARCHITECTURAL ORNAMENTS OF PAINTED TERRA-COTTA; FROM NIMRUD}}

{{IMG:1911 Britannica - Babylonia-Section of bronze.png|SECTION OF BRONZE SHEATHING FROM GATES OF SHALMANESER II}}

{{IMG:1911 Britannica - Babylonia-Bronze lion.png|BRONZE LION-WEIGHT}}

{{IMG:1911 Britannica - Babylonia-Relief.png|SCULPTURED RELIEF OF THE REIGN OF ASSUR-BANI-PAL; MYTHOLOGICAL BEINGS IN CONFLICT}}

{{IMG:1911 Britannica - Babylonia-Sculptured paving slab.png|PORTION OF SCULPTURED PAVING SLAB FROM A DOORWAY IN ASSUR-BANI-PAL'S PALACE AT KUYUNJIK (NINEVEH)}}

{{IMG:1911 Britannica - Babylonia-Pur-Sin.png|STAMPED BRICK-INSCRIPTION OF BŪR-SIN, KING OF UR}}

{{IMG:1911 Britannica - Babylonia-Tushratta.png|LETTER FROM TUSHRATTA, KING OF MITANI, TO AMENOPHIS III}}

{{IMG:1911 Britannica - Babylonia-Sennacherib.png|PRISM OF SENNACHERIB, INSCRIBED WITH HISTORICAL ANNALS OF HIS REIGN}}

{{IMG:1911 Britannica - Babylonia-Tablet.png|TABLET FROM ASSUR-BANI-PAL'S LIBRARY, INSCRIBED WITH MYTHOLOGICAL TEXT}}
```

---

## Bayeux Tapestry, PLATE I — vol 03

**Article ID:** 4238448  
**Signature:** `wikitable depth=1 wt=multi ht=0`

### Source excerpt
```
{|align="center" cellpadding="3" cellspacing="0"
|[[File:1911 Britannica - Bayeux Tapestry - Siege of Dinant1.png|center|400px|]] || [[File:1911 Britannica - Bayeux Tapestry - Siege of Dinant2.png|center|400px|]]
|-
|}
{{center|1. SIEGE OF DINANT. Note the wooden castle on a mound, and the knight handing over the keys on his lance tip.}}


{|align="center" cellpadding="3" cellspacing="0"
|[[File:1911 Britannica - Bayeux Tapestry - Funeral of Edward1.png|center|400px|]] || [[File:1911 Britannica - Bayeux Tapestry - Funeral of Edward2.png|center|400px|]]
|-
|}
{{center|2. THE FUNERAL OF EDWARD THE CONFESSOR AT WESTMINSTER ABBEY.}}


{|align="center" cellpadding="3" cellspacing="0"
|[[File:1911 Britannica - Bayeux Tapestry - Coronation of Harold.png|center|400px|]] || [[File:1911 Britannica - Bayeux Tapestry - Halley comet.png|center|400px|]]
|-
|}
{{center|3. CORONATION OF HAROLD.{{gap}}{{gap}}{{gap}}{{gap}}{{gap}}{{gap}}4. APPEARANCE OF HALLEY’S COMET.}}


{|align="center" cellpadding="3" cellspacing="0"
|[[File:1911 Britannica - Bayeux Tapestry - Normans1.png|center|400px|]] || [[File:1911 Britannica - Bayeux Tapestry - Normans2.png|center|400px|]]
|-
|}
{{center|5. THE NORMANS CARRY THEIR ARMS TO THE SHIPS.}}
{{center|{{smaller|(''By permission of G, Bell & Sons''.)}}}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 8 | 8 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **12** | **12** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica - Bayeux Tapestry - Siege of Dinant1.png|SIEGE OF DINANT. Note the wooden castle on a mound, and the knight handing over the keys on his lance tip}}

{{IMG:1911 Britannica - Bayeux Tapestry - Siege of Dinant2.png|THE FUNERAL OF EDWARD THE CONFESSOR AT WESTMINSTER ABBEY}}

{{IMG:1911 Britannica - Bayeux Tapestry - Funeral of Edward1.png|CORONATION OF HAROLD. 4. APPEARANCE OF HALLEY’S COMET}}

{{IMG:1911 Britannica - Bayeux Tapestry - Funeral of Edward2.png|THE NORMANS CARRY THEIR ARMS TO THE SHIPS. (By permission of G, Bell & Sons.)}}

{{IMG:1911 Britannica - Bayeux Tapestry - Coronation of Harold.png}}

{{IMG:1911 Britannica - Bayeux Tapestry - Halley comet.png}}

{{IMG:1911 Britannica - Bayeux Tapestry - Normans1.png}}

{{IMG:1911 Britannica - Bayeux Tapestry - Normans2.png}}
```

### Current body
```
{{IMG:1911 Britannica - Bayeux Tapestry - Siege of Dinant1.png|SIEGE OF DINANT. Note the wooden castle on a mound, and the knight handing over the keys on his lance tip}}

{{IMG:1911 Britannica - Bayeux Tapestry - Siege of Dinant2.png|THE FUNERAL OF EDWARD THE CONFESSOR AT WESTMINSTER ABBEY}}

{{IMG:1911 Britannica - Bayeux Tapestry - Funeral of Edward1.png|CORONATION OF HAROLD. 4. APPEARANCE OF HALLEY’S COMET}}

{{IMG:1911 Britannica - Bayeux Tapestry - Funeral of Edward2.png|THE NORMANS CARRY THEIR ARMS TO THE SHIPS. (By permission of G, Bell & Sons.)}}

{{IMG:1911 Britannica - Bayeux Tapestry - Coronation of Harold.png}}

{{IMG:1911 Britannica - Bayeux Tapestry - Halley comet.png}}

{{IMG:1911 Britannica - Bayeux Tapestry - Normans1.png}}

{{IMG:1911 Britannica - Bayeux Tapestry - Normans2.png}}
```

---

## Bayeux Tapestry, PLATE II — vol 03

**Article ID:** 4238449  
**Signature:** `wikitable depth=1 wt=multi ht=0`

### Source excerpt
```
{|align="center" cellpadding="3" cellspacing="0"
|[[File:1911 Britannica - Bayeux Tapestry - Normans3.png|center|400px|]] || [[File:1911 Britannica - Bayeux Tapestry - Normans4.png|center|400px|]]
|-
|}
{{center|6. THE NORMANS CROSS TO PEVENSEY.}}


{|align="center" cellpadding="3" cellspacing="0"
|[[File:1911 Britannica - Bayeux Tapestry - Hastings castle.png|center|400px|]] || [[File:1911 Britannica - Bayeux Tapestry - Burning of Hastings.png|center|400px|]]
|-
|}
{{center|7. BUILDING OF HASTINGS CASTLE.{{gap}}8. HAROLD’S ADVANCE ANNOUNCED TO WILLIAM. THE BURNING OF HASTINGS.}}


{|align="center" cellpadding="3" cellspacing="0"
|[[File:1911 Britannica - Bayeux Tapestry - Normans5.png|center|400px|]] || [[File:1911 Britannica - Bayeux Tapestry - Normans6.png|center|400px|]]
|-
|}
{{center|9. THE NORMAN CAVALRY ATTACKS THE ENGLISH SHIELD WALL.}}


{|align="center" cellpadding="3" cellspacing="0"
|[[File:1911 Britannica - Bayeux Tapestry - William.png|center|400px|]] || [[File:1911 Britannica - Bayeux Tapestry - Odo Bishop.png|center|400px|]]
|-
|}
{{center|10. WILLIAM RAISES HIS HELMET TO RALLY HIS MEN.{{gap}}{{gap}}11. ODO, BISHOP OF BAYEUX, WIELDING HIS MACE.}}
{{center|{{smaller|(''By permission of G, Bell & Sons''.)}}}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 8 | 8 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **12** | **12** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica - Bayeux Tapestry - Normans3.png|THE NORMANS CROSS TO PEVENSEY}}

{{IMG:1911 Britannica - Bayeux Tapestry - Normans4.png|BUILDING OF HASTINGS CASTLE. 8. HAROLD’S ADVANCE ANNOUNCED TO WILLIAM. THE BURNING OF HASTINGS}}

{{IMG:1911 Britannica - Bayeux Tapestry - Hastings castle.png|THE NORMAN CAVALRY ATTACKS THE ENGLISH SHIELD WALL}}

{{IMG:1911 Britannica - Bayeux Tapestry - Burning of Hastings.png|WILLIAM RAISES HIS HELMET TO RALLY HIS MEN. 11. ODO, BISHOP OF BAYEUX, WIELDING HIS MACE. (By permission of G, Bell & Sons.)}}

{{IMG:1911 Britannica - Bayeux Tapestry - Normans5.png}}

{{IMG:1911 Britannica - Bayeux Tapestry - Normans6.png}}

{{IMG:1911 Britannica - Bayeux Tapestry - William.png}}

{{IMG:1911 Britannica - Bayeux Tapestry - Odo Bishop.png}}
```

### Current body
```
{{IMG:1911 Britannica - Bayeux Tapestry - Normans3.png|THE NORMANS CROSS TO PEVENSEY}}

{{IMG:1911 Britannica - Bayeux Tapestry - Normans4.png|BUILDING OF HASTINGS CASTLE. 8. HAROLD’S ADVANCE ANNOUNCED TO WILLIAM. THE BURNING OF HASTINGS}}

{{IMG:1911 Britannica - Bayeux Tapestry - Hastings castle.png|THE NORMAN CAVALRY ATTACKS THE ENGLISH SHIELD WALL}}

{{IMG:1911 Britannica - Bayeux Tapestry - Burning of Hastings.png|WILLIAM RAISES HIS HELMET TO RALLY HIS MEN. 11. ODO, BISHOP OF BAYEUX, WIELDING HIS MACE. (By permission of G, Bell & Sons.)}}

{{IMG:1911 Britannica - Bayeux Tapestry - Normans5.png}}

{{IMG:1911 Britannica - Bayeux Tapestry - Normans6.png}}

{{IMG:1911 Britannica - Bayeux Tapestry - William.png}}

{{IMG:1911 Britannica - Bayeux Tapestry - Odo Bishop.png}}
```

---

## Bible, PLATE I — vol 03

**Article ID:** 4239088  
**Signature:** `wikitable depth=1 wt=multi ht=0`

### Source excerpt
```
{|{{Ts|ma|sm92|lh12}}
|[[File:1911 Britannica-Bible-Codex Vaticanus.png|440px]] ||  || [[File:1911 Britannica-Bible-Codex Sinaiticus.png|440px]] 
|- {{Ts|ac}}
|{{sc|Fig.}} 1.—''Codex Vaticanus'' (''From facsimile ed. by<br>J. Cozza-Luzi'', 1889–1890.) || ||{{sc|Fig.}} 2.—''Codex Sinaiticus'' (''From facsimile published by<br>Palaeographical Soc.'' 1873.)
|}


{|{{Ts|ma|sm92|lh12}}
|[[File:1911 Britannica-Bible-Codex Alexandrinus.png|420px]]||  || [[File:1911 Britannica-Bible-Codex Amiatinus.png|470px]] 
|- {{Ts|ac}}
|{{sc|Fig.}} 3.—''Codex Alexandrinus''. (''British Museum''.)<br>&nbsp;|| ||{{sc|Fig.}} 4.—From a probable Northumbrian Copy of the ''Codex Amiatinus''.<br>(''British Museum''.)
|}


{|{{Ts|ma|sm92|lh12}}
|[[File:1911 Britannica-Bible-Pentateuch.png|360px]] ||  || [[File:1911 Britannica-Bible-Vulgate.png|520px]] 
|- {{Ts|ac}}
|{{sc|Fig.}} 5.—''Pentateuch'' in Hebrew, 9th Century.<br>(''British Museum''.)|| || {{sc|Fig.}} 6.—Vulgate. (''From MS written for the monastery of Ste Marie de Parco'', <br>''Louvain'', {{asc|A.D.}} 1148. ''British Museum''.)
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 6 | 6 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **10** | **10** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica-Bible-Codex Vaticanus.png|Codex Vaticanus (From facsimile ed. by J. Cozza-Luzi, 1889–1890.) Fig. 2.—Codex Sinaiticus (From facsimile published by Palaeographical Soc. 1873.)}}

{{IMG:1911 Britannica-Bible-Codex Sinaiticus.png|Codex Alexandrinus. (British Museum.) Fig. 4.—From a probable Northumbrian Copy of the Codex Amiatinus. (British Museum.)}}

{{IMG:1911 Britannica-Bible-Codex Alexandrinus.png|Pentateuch in Hebrew, 9th Century. (British Museum.)}}

{{IMG:1911 Britannica-Bible-Codex Amiatinus.png|Vulgate. (From MS written for the monastery of Ste Marie de Parco, Louvain, A.D. 1148. British Museum.)}}

{{IMG:1911 Britannica-Bible-Pentateuch.png}}

{{IMG:1911 Britannica-Bible-Vulgate.png}}
```

### Current body
```
{{IMG:1911 Britannica-Bible-Codex Vaticanus.png|Codex Vaticanus (From facsimile ed. by J. Cozza-Luzi, 1889–1890.) Fig. 2.—Codex Sinaiticus (From facsimile published by Palaeographical Soc. 1873.)}}

{{IMG:1911 Britannica-Bible-Codex Sinaiticus.png|Codex Alexandrinus. (British Museum.) Fig. 4.—From a probable Northumbrian Copy of the Codex Amiatinus. (British Museum.)}}

{{IMG:1911 Britannica-Bible-Codex Alexandrinus.png|Pentateuch in Hebrew, 9th Century. (British Museum.)}}

{{IMG:1911 Britannica-Bible-Codex Amiatinus.png|Vulgate. (From MS written for the monastery of Ste Marie de Parco, Louvain, A.D. 1148. British Museum.)}}

{{IMG:1911 Britannica-Bible-Pentateuch.png}}

{{IMG:1911 Britannica-Bible-Vulgate.png}}
```

---

## Bible, PLATE II — vol 03

**Article ID:** 4239089  
**Signature:** `wikitable depth=1 wt=multi ht=0`

### Source excerpt
```
{|{{Ts|ma|sm92|lh12|ac}}
|[[File:1911 Britannica-Bible-Latin Bible.png|440px]] ||  ||[[File:1911 Britannica-Bible-Wycliffite Version.png|470px]] 
|-
|{{sc|Fig.}} 7.—13th Century Latin Bible. (''From copy belonging to Robert<br>de Bello'', ''abbot of St Augustine’s'', ''Canterbury. British Museum''.)|| ||{{sc|Fig.}} 8.—Early Wycliffite Version. (''From copy belonging to Thomas of Woodstock'',<br> ''duke of Gloucester'', ''written towards the end of 14th century. British Museum.'')
|}


{|{{Ts|ma|sm92|lh12|ac}}
|[[File:1911 Britannica-Bible-Line Bible.png|440px]]||  ||[[File:1911 Britannica-Bible-Tyndale.png|440px]] 
|-
|{{sc|Fig.}} 9.—The 42-Line Bible. (''Printed at Mainz'', 1452–6. ''British Museum.'')<br />&nbsp;|| ||{{sc|Fig.}} 10.—Tyndale’s Quarto Edition of New Testament. (''Printed by P. Quentel,<br> Cologne'', 1525, ''from the only remaining fragment'', ''in British Museum.'')
|}


{|{{Ts|ma|sm92|lh12|ac}}
|[[File:1911 Britannica-Bible-English Bible.png|440px]]||  ||[[File:1911 Britannica-Bible-Authorized Version.png|440px]] 
|-
|{{sc|Fig.}} 11.—First printed English Bible, 1535. (''British Museum''.)|| ||{{sc|Fig.}} 12.—First Edition of the Authorized Version, 1611. (''British Museum.'')
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 6 | 6 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **10** | **10** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica-Bible-Latin Bible.png|Fig. 7.—13th Century Latin Bible. (From copy belonging to Robert de Bello, abbot of St Augustine’s, Canterbury. British Museum.)}}

{{IMG:1911 Britannica-Bible-Wycliffite Version.png|Early Wycliffite Version. (From copy belonging to Thomas of Woodstock, duke of Gloucester, written towards the end of 14th century. British Museum.)}}

{{IMG:1911 Britannica-Bible-Line Bible.png|The 42-Line Bible. (Printed at Mainz, 1452–6. British Museum.) Fig. 10.—Tyndale’s Quarto Edition of New Testament. (Printed by P. Quentel, Cologne, 1525, from the only remaining fragment, in British Museum.)}}

{{IMG:1911 Britannica-Bible-Tyndale.png|First printed English Bible, 1535. (British Museum.) Fig. 12.—First Edition of the Authorized Version, 1611. (British Museum.)}}

{{IMG:1911 Britannica-Bible-English Bible.png}}

{{IMG:1911 Britannica-Bible-Authorized Version.png}}
```

### Current body
```
{{IMG:1911 Britannica-Bible-Latin Bible.png|Fig. 7.—13th Century Latin Bible. (From copy belonging to Robert de Bello, abbot of St Augustine’s, Canterbury. British Museum.)}}

{{IMG:1911 Britannica-Bible-Wycliffite Version.png|Early Wycliffite Version. (From copy belonging to Thomas of Woodstock, duke of Gloucester, written towards the end of 14th century. British Museum.)}}

{{IMG:1911 Britannica-Bible-Line Bible.png|The 42-Line Bible. (Printed at Mainz, 1452–6. British Museum.) Fig. 10.—Tyndale’s Quarto Edition of New Testament. (Printed by P. Quentel, Cologne, 1525, from the only remaining fragment, in British Museum.)}}

{{IMG:1911 Britannica-Bible-Tyndale.png|First printed English Bible, 1535. (British Museum.) Fig. 12.—First Edition of the Authorized Version, 1611. (British Museum.)}}

{{IMG:1911 Britannica-Bible-English Bible.png}}

{{IMG:1911 Britannica-Bible-Authorized Version.png}}
```

---

## BOOKBINDING, PLATE — vol 04

**Article ID:** 4190994  
**Signature:** `wikitable depth=2 wt=multi ht=0`

### Source excerpt
```
{|align=center style="font-size:92%; line-height:130%;"
|
{|width="100%"
|valign=bottom|[[Image:Britannica Bookbinding - Winchester Domesday Book.jpg|250px]]&emsp;
|valign=bottom align=center|[[Image:Britannica Bookbinding - St. Cuthbert's Gospels.jpg|250px]]
|valign=bottom align=right|&emsp;[[Image:Britannica Bookbinding - James I binding.jpg|250px]]
|-
|valign="top" align=left|<div style="width: 250px">{{small-caps|Fig.}} 1.—WINCHESTER DOMESDAY BOOK OF THE 12TH CENTURY.</div><div style="width: 250px; text-align: center; font-size:92%;">Dark brown morocco, blind stamped.</div>
|valign="top" align=center|<div style="width: 250px; text-align: left">{{small-caps|Fig.}} 2.—ST. CUTHBERT’S GOSPELS.<br/>{{EB1911 Fine Print|Red leather with repoussé design, probably<br/>the work of the 7th or 8th century. The fine<br/>lines are impressed by hand, and painted blue and yellow.}}</div>
|valign="top" align=right|<div style="width: 250px; text-align: left">{{small-caps|Fig.}} 4.—BINDING MADE FOR JAMES I.<br/>{{EB1911 Fine Print|Dark blue morocco, gold tooled. The red in the coat-of-arms inlaid with red morocco.}}</div>
|}
|-
|
{|width=100%
|valign="bottom"|[[Image:Britannica Bookbinding - Jean Grolier binding.jpg|500px]]
|valign="bottom" align=right|&emsp;[[Image:Britannica Bookbinding - Book of Common Prayer binding 1678.jpg|300px]]
|-
|valign="top" align=center|{{small-caps|Fig.}} 3.—BINDING MADE FOR JEAN GROLIER.<br/>{{EB1911 Fine Print|Pale brown morocco, gold tooled.}}
|valign="top"
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 8 | 8 |
| captioned       | 8 | 8 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **16** | **16** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:Britannica Bookbinding - Winchester Domesday Book.jpg|WINCHESTER DOMESDAY BOOK OF THE 12TH CENTURY.Dark brown morocco, blind stamped}}

{{IMG:Britannica Bookbinding - St. Cuthbert's Gospels.jpg|ST. CUTHBERT’S GOSPELS. Red leather with repoussé design, probably the work of the 7th or 8th century. The fine lines are impressed by hand, and painted blue and yellow}}

{{IMG:Britannica Bookbinding - James I binding.jpg|BINDING MADE FOR JAMES I. Dark blue morocco, gold tooled. The red in the coat-of-arms inlaid with red morocco}}

{{IMG:Britannica Bookbinding - Jean Grolier binding.jpg|BINDING MADE FOR JEAN GROLIER. Pale brown morocco, gold tooled}}

{{IMG:Britannica Bookbinding - Book of Common Prayer binding 1678.jpg|COMMON PRAYER (LONDON, 1678). Smooth red morocco, gold tooled with black fillets. Bound by Samuel Mearne}}

{{IMG:Britannica Bookbinding - Statuts et Ordonnances de l'Ordre du Benvist Sainct Esprit.jpg|LE LIVRE DES STATUTS ET ORDONNANCES DE L'ORDRE DU BENVIST SAINCT ESPRIT (PARIS, 1578). Brown morocco, gold tooled, arms of Henry III., King of France. Bound by Nicholas Eve}}

{{IMG:Britannica Bookbinding - Hagley Hall picture catalogue.jpg|CATALOGUE OF THE PICTURES AT HAGLEY HALL.Red niger morocco, gold tooled. Bound by Douglas Cockerell}}

{{IMG:Britannica Bookbinding - Compleat Angler 1772 binding.jpg|WALTON’S COMPLEAT ANGLER (1772).Golden brown morocco, gold tooled. Bound by Miss E. M. MacColl}}
```

### Current body
```
{{IMG:Britannica Bookbinding - Winchester Domesday Book.jpg|WINCHESTER DOMESDAY BOOK OF THE 12TH CENTURY.Dark brown morocco, blind stamped}}

{{IMG:Britannica Bookbinding - St. Cuthbert's Gospels.jpg|ST. CUTHBERT’S GOSPELS. Red leather with repoussé design, probably the work of the 7th or 8th century. The fine lines are impressed by hand, and painted blue and yellow}}

{{IMG:Britannica Bookbinding - James I binding.jpg|BINDING MADE FOR JAMES I. Dark blue morocco, gold tooled. The red in the coat-of-arms inlaid with red morocco}}

{{IMG:Britannica Bookbinding - Jean Grolier binding.jpg|BINDING MADE FOR JEAN GROLIER. Pale brown morocco, gold tooled}}

{{IMG:Britannica Bookbinding - Book of Common Prayer binding 1678.jpg|COMMON PRAYER (LONDON, 1678). Smooth red morocco, gold tooled with black fillets. Bound by Samuel Mearne}}

{{IMG:Britannica Bookbinding - Statuts et Ordonnances de l'Ordre du Benvist Sainct Esprit.jpg|LE LIVRE DES STATUTS ET ORDONNANCES DE L'ORDRE DU BENVIST SAINCT ESPRIT (PARIS, 1578). Brown morocco, gold tooled, arms of Henry III., King of France. Bound by Nicholas Eve}}

{{IMG:Britannica Bookbinding - Hagley Hall picture catalogue.jpg|CATALOGUE OF THE PICTURES AT HAGLEY HALL.Red niger morocco, gold tooled. Bound by Douglas Cockerell}}

{{IMG:Britannica Bookbinding - Compleat Angler 1772 binding.jpg|WALTON’S COMPLEAT ANGLER (1772).Golden brown morocco, gold tooled. Bound by Miss E. M. MacColl}}
```

---

## BOOK-PLATES, PLATE — vol 04

**Article ID:** 4191000  
**Signature:** `c_centered depth=0 wt=0 ht=0 toplegend`

### Source excerpt
```
{{col-begin}}
{{col-break}}
{{c|[[Image:Britannica Book-Plates - Robert Pinkney by Thomas Bewick.jpg|400px]]

BOOK-PLATE OF ROBERT PINKNEY.<br>
{{smaller|By {{sc|Thomas Bewick.}}}}
}}









{{c|[[Image:Britannica Book-Plates - Lipperheide by Karl Rickelt.jpg|400px]]

BOOK-PLATE OF FREIHERR V. LIPPERHEIDE.<br>
{{smaller|By {{sc|Karl Rickelt.}}}}
}}


{{col-break}}
{{c|[[Image:Britannica Book-Plates - Charles Dexter Allen by E. D. French.jpg|300px]]

BOOK-PLATE OF CHARLES DEXTER ALLEN.<br>
{{smaller|By {{sc|E. D. French.}}}}
}}


{{c|[[Image:Britannica Book-Plates - Arthur Vicars by C. W. Sherborn.jpg|350px]]

BOOK-PLATE OF SIR ARTHUR VICARS.<br>
{{smaller|By {{sc|C. W. Sherborn.}}}}
}}


{{col-end}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **12** | **12** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **2** | **2** |
| header text     | 'c' | 'c' |
| footer text     | 'By C. W. Sherborn' | 'By C. W. Sherborn' |

**Verdict:** ✅ identical

### Baseline body
```
c

{{IMG:Britannica Book-Plates - Robert Pinkney by Thomas Bewick.jpg|BOOK-PLATE OF ROBERT PINKNEY}}

{{IMG:Britannica Book-Plates - Lipperheide by Karl Rickelt.jpg|LIPPERHEIDE. By Karl Rickelt}}

{{IMG:Britannica Book-Plates - Charles Dexter Allen by E. D. French.jpg|BOOK-PLATE OF CHARLES DEXTER ALLEN}}

{{IMG:Britannica Book-Plates - Arthur Vicars by C. W. Sherborn.jpg|BOOK-PLATE OF SIR ARTHUR VICARS}}

By C. W. Sherborn
```

### Current body
```
c

{{IMG:Britannica Book-Plates - Robert Pinkney by Thomas Bewick.jpg|BOOK-PLATE OF ROBERT PINKNEY}}

{{IMG:Britannica Book-Plates - Lipperheide by Karl Rickelt.jpg|LIPPERHEIDE. By Karl Rickelt}}

{{IMG:Britannica Book-Plates - Charles Dexter Allen by E. D. French.jpg|BOOK-PLATE OF CHARLES DEXTER ALLEN}}

{{IMG:Britannica Book-Plates - Arthur Vicars by C. W. Sherborn.jpg|BOOK-PLATE OF SIR ARTHUR VICARS}}

By C. W. Sherborn
```

---

## BRASSES, MONUMENTAL, PLATE I — vol 04

**Article ID:** 4191374  
**Signature:** `html_table depth=0 wt=0 ht=multi has_colspan`

### Source excerpt
```
<table  align=center style="font-size:92%; line-height:125%; text-align:center;">
<tr><td style="padding-right:1.0em;">[[File:EB1911 Brasses, Monumental - Fig. 1.—Sir John D’Abernon.jpg]]</td>
<td style="padding-left:1.0em; padding-right:1.0em;">[[File:EB1911 Brasses, Monumental - Fig. 2.—Margaret de Camoys.jpg]]</td>
<td style="padding-left:1.0em; padding-right:1.0em;">[[File:EB1911 Brasses, Monumental - Fig. 3.—Henry de Grofhurst.jpg]]</td>
<td style="padding-left:1.5em;">[[File:EB1911 Brasses, Monumental - Fig. 4.—Sir Nicholas Burnell.jpg]]</td></tr>
<tr><td>Fig. 1.—Sir John D’Abernon, 1277.<br />
Stoke D’Abernon Surrey.</td>
<td>Fig. 2.—Margaret de Camoys. 1310.<br />
Trotton, Sussex.</td>
<td style="padding-left:1.0em; padding-right:1.0em;">Fig. 3.—Henry de Grofhurst, ''c''. 1330<br />
Horsemonden, Kent.</td>
<td>Fig. 4.—Sir Nicholas Burnell, 1382.<br />
Acton Burnell, Shropshire.</td></tr></table>


<table align=center style="font-size:92%; line-height:125%; text-align:center;">
<tr>
<td>[[File:EB1911 Brasses, Monumental - Fig. 5.—Margaret Lady Cobham.jpg]]</td>
<td style="padding-right:2.0em;">[[File:EB1911 Brasses, Monumental - Fig. 6.—Sir John Corp and Eleanor.jpg]]</td>
<td>[[File:EB1911 Brasses, Monumental - Fig. 7.—Sir Symon de Felbrigge.jpg]]</td></tr>
<tr><td>Fig. 5.—Margaret Lady Cobham,<br />
1385. Cobham, Kent.</td>
<td>Fig. 6.—Sir John Corp and Eleanor, his grand-daughter<br />
1391, 1361. Stoke Fleming, Devonshire.</td>
<td>Fig. 7.—Sir Symon de Felbrigge an
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 7 | 7 |
| captioned       | 7 | 7 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **17** | **17** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | 'Figs. 5 and 7 from Boutell’s Monumental Brasses. Figs. 2, 3, and 4 by permission of the Monumental Brass Society' | 'Figs. 5 and 7 from Boutell’s Monumental Brasses. Figs. 2, 3, and 4 by permission of the Monumental Brass Society' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Brasses, Monumental - Fig. 1.—Sir John D’Abernon.jpg|Sir John D’Abernon, 1277. Stoke D’Abernon Surrey}}

{{IMG:EB1911 Brasses, Monumental - Fig. 2.—Margaret de Camoys.jpg|Margaret de Camoys. 1310. Trotton, Sussex}}

{{IMG:EB1911 Brasses, Monumental - Fig. 3.—Henry de Grofhurst.jpg|Henry de Grofhurst, c. 1330 Horsemonden, Kent}}

{{IMG:EB1911 Brasses, Monumental - Fig. 4.—Sir Nicholas Burnell.jpg|Sir Nicholas Burnell, 1382. Acton Burnell, Shropshire}}

{{IMG:EB1911 Brasses, Monumental - Fig. 5.—Margaret Lady Cobham.jpg|Margaret Lady Cobham, 1385. Cobham, Kent}}

{{IMG:EB1911 Brasses, Monumental - Fig. 6.—Sir John Corp and Eleanor.jpg|Sir John Corp and Eleanor, his grand-daughter 1391, 1361. Stoke Fleming, Devonshire}}

{{IMG:EB1911 Brasses, Monumental - Fig. 7.—Sir Symon de Felbrigge.jpg|Sir Symon de Felbrigge and Margaret his wife, 1400. Felbrigge, Norfolk}}

{{LEGEND:Figs. 1 and 6 from Waller’s Monumental Brasses}LEGEND}

Figs. 5 and 7 from Boutell’s Monumental Brasses. Figs. 2, 3, and 4 by permission of the Monumental Brass Society
```

### Current body
```
{{IMG:EB1911 Brasses, Monumental - Fig. 1.—Sir John D’Abernon.jpg|Sir John D’Abernon, 1277. Stoke D’Abernon Surrey}}

{{IMG:EB1911 Brasses, Monumental - Fig. 2.—Margaret de Camoys.jpg|Margaret de Camoys. 1310. Trotton, Sussex}}

{{IMG:EB1911 Brasses, Monumental - Fig. 3.—Henry de Grofhurst.jpg|Henry de Grofhurst, c. 1330 Horsemonden, Kent}}

{{IMG:EB1911 Brasses, Monumental - Fig. 4.—Sir Nicholas Burnell.jpg|Sir Nicholas Burnell, 1382. Acton Burnell, Shropshire}}

{{IMG:EB1911 Brasses, Monumental - Fig. 5.—Margaret Lady Cobham.jpg|Margaret Lady Cobham, 1385. Cobham, Kent}}

{{IMG:EB1911 Brasses, Monumental - Fig. 6.—Sir John Corp and Eleanor.jpg|Sir John Corp and Eleanor, his grand-daughter 1391, 1361. Stoke Fleming, Devonshire}}

{{IMG:EB1911 Brasses, Monumental - Fig. 7.—Sir Symon de Felbrigge.jpg|Sir Symon de Felbrigge and Margaret his wife, 1400. Felbrigge, Norfolk}}

{{LEGEND:Figs. 1 and 6 from Waller’s Monumental Brasses}LEGEND}

Figs. 5 and 7 from Boutell’s Monumental Brasses. Figs. 2, 3, and 4 by permission of the Monumental Brass Society
```

---

## BRASSES, MONUMENTAL, PLATE II — vol 04

**Article ID:** 4191375  
**Signature:** `html_table depth=0 wt=0 ht=multi has_colspan`

### Source excerpt
```
<table align=center style="font-size:92%; line-height:125%; text-align:center;">
<tr><td style="width:36%;padding-right:1.0em;">[[File:EB1911 Brasses, Monumental II - Fig. 1.—Thomas de Beauchamp.jpg]]</td>
<td style="width:29%;">[[File:EB1911 Brasses, Monumental II - Fig. 2.—Thomas Cranley.jpg]]</td>
<td style="width:35%; padding-left:1.0em;">[[File:EB1911 Brasses, Monumental II - Fig. 3.—Sir William Vernon.jpg]]</td></tr>
<tr><td>Fig. 1.—Thomas de Beauchamp, Earl of Warwick and Lady,<br />
1406 and 1401. St. Mary’s Church, Warwick.</td>
<td style="padding-left:1.0em; padding-right:1.0em;>Fig. 2.—Thomas Cranley, Archbishop of Dublin,<br />
1417. New College, Oxford.</td>
<td>Fig. 3.—Sir William Vernon and Lady, 1467.<br />
Tong Church, Shropshire.</td></tr></table>


<table align=center style="font-size:92%; line-height:125%; text-align:center;">
<tr><td style="width:36%; padding-right:1.0em;">[[File:EB1911 Brasses, Monumental II - Fig. 4.—John Shelley, Esq.jpg]]</td>
<td style="width:29%; padding-left:1.0em; padding-right:1.0em;">[[File:EB1911 Brasses, Monumental II - Fig. 5.—Dame Margaret Chute.jpg]]</td>
<td style="width:35%; padding-left:1.0em;">[[File:EB1911 Brasses, Monumental II - Fig. 6.—Sir Edward Filmer.jpg]]</td></tr>
<tr><td>Fig. 4.—John Shelley, Esq., 1526, and his wife Elizabeth, 1513.<br />
Clapham, Sussex.</td>
<td>Fig. 5.—Dame Margaret Chute, 1614.<br />Mardon, Herefordshire.</td>
<td>Fig. 6.—Sir Edward Filmer and Lady, 1638.<br />East Sutton, Kent.</td></tr>
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 6 | 6 |
| captioned       | 6 | 6 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **15** | **15** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | '3Figs. 4 and 5 by permission of the Monumental Brass Society' | '3Figs. 4 and 5 by permission of the Monumental Brass Society' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Brasses, Monumental II - Fig. 1.—Thomas de Beauchamp.jpg|Thomas de Beauchamp, Earl of Warwick and Lady, 1406 and 1401. St. Mary’s Church, Warwick}}

{{IMG:EB1911 Brasses, Monumental II - Fig. 2.—Thomas Cranley.jpg|Thomas Cranley, Archbishop of Dublin, 1417. New College, Oxford}}

{{IMG:EB1911 Brasses, Monumental II - Fig. 3.—Sir William Vernon.jpg|Sir William Vernon and Lady, 1467. Tong Church, Shropshire}}

{{IMG:EB1911 Brasses, Monumental II - Fig. 4.—John Shelley, Esq.jpg|John Shelley, Esq., 1526, and his wife Elizabeth, 1513. Clapham, Sussex}}

{{IMG:EB1911 Brasses, Monumental II - Fig. 5.—Dame Margaret Chute.jpg|Dame Margaret Chute, 1614. Mardon, Herefordshire}}

{{IMG:EB1911 Brasses, Monumental II - Fig. 6.—Sir Edward Filmer.jpg|Sir Edward Filmer and Lady, 1638. East Sutton, Kent}}

{{LEGEND:Figs. 1, 2, 3 and 6 from Waller’s Monumental Brasses}LEGEND}

3Figs. 4 and 5 by permission of the Monumental Brass Society
```

### Current body
```
{{IMG:EB1911 Brasses, Monumental II - Fig. 1.—Thomas de Beauchamp.jpg|Thomas de Beauchamp, Earl of Warwick and Lady, 1406 and 1401. St. Mary’s Church, Warwick}}

{{IMG:EB1911 Brasses, Monumental II - Fig. 2.—Thomas Cranley.jpg|Thomas Cranley, Archbishop of Dublin, 1417. New College, Oxford}}

{{IMG:EB1911 Brasses, Monumental II - Fig. 3.—Sir William Vernon.jpg|Sir William Vernon and Lady, 1467. Tong Church, Shropshire}}

{{IMG:EB1911 Brasses, Monumental II - Fig. 4.—John Shelley, Esq.jpg|John Shelley, Esq., 1526, and his wife Elizabeth, 1513. Clapham, Sussex}}

{{IMG:EB1911 Brasses, Monumental II - Fig. 5.—Dame Margaret Chute.jpg|Dame Margaret Chute, 1614. Mardon, Herefordshire}}

{{IMG:EB1911 Brasses, Monumental II - Fig. 6.—Sir Edward Filmer.jpg|Sir Edward Filmer and Lady, 1638. East Sutton, Kent}}

{{LEGEND:Figs. 1, 2, 3 and 6 from Waller’s Monumental Brasses}LEGEND}

3Figs. 4 and 5 by permission of the Monumental Brass Society
```

---

## BREWING, PLATE I — vol 04

**Article ID:** 4191467  
**Signature:** `center_template depth=0 wt=0 ht=0 toplegend`

### Source excerpt
```
{{center|[[image:brewing_5.jpg]]<br>
{{EB1911 Fine Print|{{sc|Fig.}} 5.—REFRIGERATORS IN “LAGER” BREWERY OF MESSRS. ALLSOPP.<br>
The hot wort trickles over the outside of the series of pipes, and is cooled by the cold water which circulates in them.<br>From the shallow collecting trays the cooled wort is conducted to the fermenting backs.}}}}
<br>
{{nop}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'center' | 'center' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
center

{{IMG:brewing_5.jpg|REFRIGERATORS IN “LAGER” BREWERY OF MESSRS. ALLSOPP. The hot wort trickles over the outside of the series of pipes, and is cooled by the cold water which circulates in them. From the shallow collecting trays the cooled wort is conducted to the fermenting backs}}
```

### Current body
```
center

{{IMG:brewing_5.jpg|REFRIGERATORS IN “LAGER” BREWERY OF MESSRS. ALLSOPP. The hot wort trickles over the outside of the series of pipes, and is cooled by the cold water which circulates in them. From the shallow collecting trays the cooled wort is conducted to the fermenting backs}}
```

---

## BREWING, PLATE II — vol 04

**Article ID:** 4191468  
**Signature:** `center_template depth=0 wt=0 ht=0 toplegend`

### Source excerpt
```
{{center|[[image:brewing_6.jpg|850px]]<br>
{{EB1911 Fine Print|{{sc|Fig.}} 6.—BURTON-UNION SYSTEM OF CLEANSING. (MESSRS. ALLSOPP’S BREWERY.)<br>
The green beer is filled into the casks, and the excess of yeast, &c., then works out through the swan necks into the long common gutter shown.}}}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'center' | 'center' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
center

{{IMG:brewing_6.jpg|BURTON-UNION SYSTEM OF CLEANSING. (MESSRS. ALLSOPP’S BREWERY.) The green beer is filled into the casks, and the excess of yeast, &c., then works out through the swan necks into the long common gutter shown}}
```

### Current body
```
center

{{IMG:brewing_6.jpg|BURTON-UNION SYSTEM OF CLEANSING. (MESSRS. ALLSOPP’S BREWERY.) The green beer is filled into the casks, and the excess of yeast, &c., then works out through the swan necks into the long common gutter shown}}
```

---

## BYZANTINE ART, PLATE I — vol 04

**Article ID:** 4192153  
**Signature:** `wikitable depth=1 wt=multi ht=0 has_colspan`

### Source excerpt
```
{|{{Ts|width:770px|ma|ac|sm92|lh13}}
|[[Image:byzantine_art_1.png|770px]]
|-
|INTERIOR OF THE HOLY WISDOM (S. SOPHIA), CONSTANTINOPLE.<br>{{EB1911 Fine Print|Sixth century, the dome was rebuilt in the tenth century. The metal balustrades, pulpits, and the large discs are Turkish.}}
|}


{|{{Ts|ma|ac|sm92|lh13}}
|[[Image:byzantine_art_2.png|250px]]
|{{Ts|pl1|pr1}}|[[Image:byzantine_art_3.png|250px]]
|[[Image:byzantine_art_4.png|250px]]
|-
|colspan=3 {{Ts|ac}}|CAPITALS OF COLUMNS.
|-
|S. VITALI, RAVENNA.<br>Sixth century.
|S. MARK, VENICE.<br>Eleventh century.
|S. APOLLINARI, RAVENNA.<br>Sixth century.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **9** | **9** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:byzantine_art_1.png|INTERIOR OF THE HOLY WISDOM (S. SOPHIA), CONSTANTINOPLE. Sixth century, the dome was rebuilt in the tenth century. The metal balustrades, pulpits, and the large discs are Turkish}}

{{IMG:byzantine_art_2.png|CAPITALS OF COLUMNS}}

{{IMG:byzantine_art_3.png|S. VITALI, RAVENNA. Sixth century}}

{{IMG:byzantine_art_4.png|S. MARK, VENICE. Eleventh century}}

{{LEGEND:S. APOLLINARI, RAVENNA. Sixth century}LEGEND}
```

### Current body
```
{{IMG:byzantine_art_1.png|INTERIOR OF THE HOLY WISDOM (S. SOPHIA), CONSTANTINOPLE. Sixth century, the dome was rebuilt in the tenth century. The metal balustrades, pulpits, and the large discs are Turkish}}

{{IMG:byzantine_art_2.png|CAPITALS OF COLUMNS}}

{{IMG:byzantine_art_3.png|S. VITALI, RAVENNA. Sixth century}}

{{IMG:byzantine_art_4.png|S. MARK, VENICE. Eleventh century}}

{{LEGEND:S. APOLLINARI, RAVENNA. Sixth century}LEGEND}
```

---

## BYZANTINE ART, PLATE II — vol 04

**Article ID:** 4192154  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|{{Ts|ma|ac|sm92|lh13|width:670px}}
|[[Image:byzantine_art_5.png|670px]]
|-
|{{Ts|ar|pr.5|sm90|lh10}}|''Photo. Emery Walker.''
|-
|SMALL MEDIEVAL CATHEDRAL, ATHENS.<br>&nbsp;
|-
|[[Image:byzantine_art_6.png|670px]]
|-
|{{Ts|ar|pr.5|sm90|lh10}}|''From a Drawing by Sidney Barnsley.''
|-
|INTERIOR OF ST. LUKE’S, NEAR DELPHI.
|-
|Showing a typical scheme of internal decoration. The lower parts of the walls are covered with marble, and<br>the upper surfaces and vaults with mosaics and paintings. Eleventh century.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 2 | 2 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:byzantine_art_5.png|SMALL MEDIEVAL CATHEDRAL, ATHENS}}

{{IMG:byzantine_art_6.png|From a Drawing by Sidney Barnsley}}

{{LEGEND:INTERIOR OF ST. LUKE’S, NEAR DELPHI}LEGEND}

{{LEGEND:Showing a typical scheme of internal decoration. The lower parts of the walls are covered with marble, and the upper surfaces and vaults with mosaics and paintings. Eleventh century}LEGEND}
```

### Current body
```
{{IMG:byzantine_art_5.png|SMALL MEDIEVAL CATHEDRAL, ATHENS}}

{{IMG:byzantine_art_6.png|From a Drawing by Sidney Barnsley}}

{{LEGEND:INTERIOR OF ST. LUKE’S, NEAR DELPHI}LEGEND}

{{LEGEND:Showing a typical scheme of internal decoration. The lower parts of the walls are covered with marble, and the upper surfaces and vaults with mosaics and paintings. Eleventh century}LEGEND}
```

---

## CARPET — vol 05

**Article ID:** 4192844  
**Signature:** `html_table depth=0 wt=0 ht=1 has_colspan`

### Source excerpt
```
<table style="margin:auto">
<tr><td>[[File:EB1911 Carpet - Fig. 1.—Linen covering, coloured wools.jpg]]</td>
<td>[[File:EB1911 Carpet - Fig. 2.—Linen covering, dark-brown wool.jpg]]</td></tr>
<tr><td style="padding-left:2em;">{{EB1911 Fine Print|{{sc|Fig.}} 1.—PART OF A LINEN COVERING OVER-WROUGHT<br/>{{em|2}}WITH ORNAMENT IN LOOPS OF COLOURED WOOLS.}}</td>
<td style="padding-left:2em;>{{EB1911 Fine Print|{{sc|Fig.}} 2.—PART OF A LINEN COVERING OVER-WROUGHT<br/>{{em|2}}WITH ORNAMENT IN LOOPS OF DARK-BROWN WOOL.}}</td></tr>
<tr style="text-align:center; font-size:85%; line-height:120%;"><td>Egypto-Roman of the 3rd or 4th century {{asc|A.D.}}<br/>(Victoria and Albert Museum, South Kensington.)</td><td>Egypto-Roman of the 3rd or 4th century {{asc|A.D.}}<br/>(Victoria and Albert Museum, South Kensington.)<br/></td></tr>
<tr><td colspan="2"><br/>[[File:EB1911 Carpet - Fig. 3.—Cut pile Turkish Carpet.jpg]]</td></tr>
<tr style="font-size:92%; line-height:125%;"><td colspan="2">{{sc|Fig.}} 3.—CUT PILE TURKEY CARPET, 18{{sc|th}} CENTURY, EXEMPLIFYING SUCH CHARACTERISTIC ANGULAR TREATMENT OF QUASI-BOTANICAL<br/>{{em|2}}FORMS AS IS USUALLY FOUND IN CARPETS AND RUGS MADE IN ASIA MINOR.
FROM DESIGNS OF PERSIAN OR MOSIL ORIGIN. {{fs90|{{em|2.3}}(Victoria and Albert Museum, South Kensington.)}}</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 2 | 2 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Carpet - Fig. 1.—Linen covering, coloured wools.jpg|PART OF A LINEN COVERING OVER-WROUGHT WITH ORNAMENT IN LOOPS OF COLOURED WOOLS}}

{{IMG:EB1911 Carpet - Fig. 2.—Linen covering, dark-brown wool.jpg|PART OF A LINEN COVERING OVER-WROUGHT WITH ORNAMENT IN LOOPS OF DARK-BROWN WOOL}}

{{IMG:EB1911 Carpet - Fig. 3.—Cut pile Turkish Carpet.jpg|CUT PILE TURKEY CARPET, 18th CENTURY, EXEMPLIFYING SUCH CHARACTERISTIC ANGULAR TREATMENT OF QUASI-BOTANICAL FORMS AS IS USUALLY FOUND IN CARPETS AND RUGS MADE IN ASIA MINOR. FROM DESIGNS OF PERSIAN OR MOSIL ORIGIN. (Victoria and Albert Museum, South Kensington.)}}

{{LEGEND:Egypto-Roman of the 3rd or 4th century A.D. (Victoria and Albert Museum, South Kensington.)}LEGEND}

{{LEGEND:Egypto-Roman of the 3rd or 4th century A.D. (Victoria and Albert Museum, South Kensington.)}LEGEND}
```

### Current body
```
{{IMG:EB1911 Carpet - Fig. 1.—Linen covering, coloured wools.jpg|PART OF A LINEN COVERING OVER-WROUGHT WITH ORNAMENT IN LOOPS OF COLOURED WOOLS}}

{{IMG:EB1911 Carpet - Fig. 2.—Linen covering, dark-brown wool.jpg|PART OF A LINEN COVERING OVER-WROUGHT WITH ORNAMENT IN LOOPS OF DARK-BROWN WOOL}}

{{IMG:EB1911 Carpet - Fig. 3.—Cut pile Turkish Carpet.jpg|CUT PILE TURKEY CARPET, 18th CENTURY, EXEMPLIFYING SUCH CHARACTERISTIC ANGULAR TREATMENT OF QUASI-BOTANICAL FORMS AS IS USUALLY FOUND IN CARPETS AND RUGS MADE IN ASIA MINOR. FROM DESIGNS OF PERSIAN OR MOSIL ORIGIN. (Victoria and Albert Museum, South Kensington.)}}

{{LEGEND:Egypto-Roman of the 3rd or 4th century A.D. (Victoria and Albert Museum, South Kensington.)}LEGEND}

{{LEGEND:Egypto-Roman of the 3rd or 4th century A.D. (Victoria and Albert Museum, South Kensington.)}LEGEND}
```

---

## CARPET, PLATE II — vol 05

**Article ID:** 4192845  
**Signature:** `html_table depth=0 wt=0 ht=1`

### Source excerpt
```
<table style="margin:auto">
<tr><td>[[File:EB1911 Carpet - Fig. 4.—Persian rug using tapestry weave.jpg]]</td></tr>
<tr><td align=center>{{EB1911 Fine Print|{{sc|Fig.}} 4.—RUG MADE IN PERSIA IN THE MANNER OF TAPESTRY WEAVING.}}</td></tr>
<tr><td>[[File:EB1911 Carpet - Fig. 5.—Carpet of stout Flax.jpg]]</td></tr>
<tr><td style="text-align:center">{{EB1911 Fine Print|{{sc|Fig.}} 5.—CARPET OF STOUT FLAX OR HEMP WOVEN AND THEN COMPLETELY COVERED WITH ORNAMENT<br/>WORKED IN CLOSE NEEDLE STITCHES IN COLOURED THREADS.}}</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Carpet - Fig. 4.—Persian rug using tapestry weave.jpg|RUG MADE IN PERSIA IN THE MANNER OF TAPESTRY WEAVING}}

{{IMG:EB1911 Carpet - Fig. 5.—Carpet of stout Flax.jpg|CARPET OF STOUT FLAX OR HEMP WOVEN AND THEN COMPLETELY COVERED WITH ORNAMENT WORKED IN CLOSE NEEDLE STITCHES IN COLOURED THREADS}}
```

### Current body
```
{{IMG:EB1911 Carpet - Fig. 4.—Persian rug using tapestry weave.jpg|RUG MADE IN PERSIA IN THE MANNER OF TAPESTRY WEAVING}}

{{IMG:EB1911 Carpet - Fig. 5.—Carpet of stout Flax.jpg|CARPET OF STOUT FLAX OR HEMP WOVEN AND THEN COMPLETELY COVERED WITH ORNAMENT WORKED IN CLOSE NEEDLE STITCHES IN COLOURED THREADS}}
```

---

## CARPET, PLATE III — vol 05

**Article ID:** 4192846  
**Signature:** `html_table depth=0 wt=0 ht=1`

### Source excerpt
```
<table style="margin:auto">
<tr><td>[[File:EB1911 Carpet - Fig. 6.—Cut pile worsted carpet.jpg]]&ensp;</td>
<td>&ensp;[[File:EB1911 Carpet - Fig. 7.—Persian Holy Carpet.jpg]]</td></tr>
<tr><td align=center>{{sc|Fig.}} 6.—CUT PILE WORSTED CARPET,
{{fs90|BEARING ROYAL ARMS OF ENGLAND WITH<br/> E.R. (ELIZABETH REGINA);  DATE 1570.}} &emsp;</td>
<td {{Ts|vtt|ac}}>{{sc|Fig.}} 7.—VERY FINE CUT PILE PERSIAN CARPET KNOWN AS THE<br/>HOLY CARPET OF THE MOSQUE AT ARDEBIL.<br/></td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Carpet - Fig. 6.—Cut pile worsted carpet.jpg|CUT PILE WORSTED CARPET, BEARING ROYAL ARMS OF ENGLAND WITH E.R. (ELIZABETH REGINA); DATE 1570}}

{{IMG:EB1911 Carpet - Fig. 7.—Persian Holy Carpet.jpg|VERY FINE CUT PILE PERSIAN CARPET KNOWN AS THE HOLY CARPET OF THE MOSQUE AT ARDEBIL}}
```

### Current body
```
{{IMG:EB1911 Carpet - Fig. 6.—Cut pile worsted carpet.jpg|CUT PILE WORSTED CARPET, BEARING ROYAL ARMS OF ENGLAND WITH E.R. (ELIZABETH REGINA); DATE 1570}}

{{IMG:EB1911 Carpet - Fig. 7.—Persian Holy Carpet.jpg|VERY FINE CUT PILE PERSIAN CARPET KNOWN AS THE HOLY CARPET OF THE MOSQUE AT ARDEBIL}}
```

---

## CARPET, PLATE IV — vol 05

**Article ID:** 4192847  
**Signature:** `html_table depth=0 wt=0 ht=1`

### Source excerpt
```
<table style="margin:auto; text-align:center;">
<tr><td rowspan="3">[[File:EB1911 Carpet - Fig. 8.—Lahore cut pile Carpet.jpg]]</td>
<td>&emsp;[[File:EB1911 Carpet - Fig. 9.—Persian cut pile Carpet.jpg]]</td></tr>
<tr><td>{{sc|Fig.}} 9.—CORNER OF A CUT PILE CARPET OF PERSIAN<br/>MANUFACTURE, 16{{sc|th}} CENTURY.</td></tr>
<tr><td>&emsp;[[File:EB1911 Carpet - Fig. 10.—Spanish Carpet.jpg]]</td></tr>
<tr><td>{{sc|Fig.}} 8.—FINE CUT PILE LAHORE CARPET (''c.'' 1664)<br/>BELONGING TO GIRDLERS’ COMPANY IN<br/>LONDON. OF PERSIAN DESIGN.</td>
<td>{{sc|Fig.}} 10.—CUT PILE CARPET OF SPANISH MANUFACTURE,<br/>EARLY 16{{sc|th}} CENTURY.</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Carpet - Fig. 8.—Lahore cut pile Carpet.jpg|CORNER OF A CUT PILE CARPET OF PERSIAN MANUFACTURE, 16th CENTURY}}

{{IMG:EB1911 Carpet - Fig. 9.—Persian cut pile Carpet.jpg|FINE CUT PILE LAHORE CARPET (c. 1664) BELONGING TO GIRDLERS’ COMPANY IN LONDON. OF PERSIAN DESIGN}}

{{IMG:EB1911 Carpet - Fig. 10.—Spanish Carpet.jpg|CUT PILE CARPET OF SPANISH MANUFACTURE, EARLY 16th CENTURY}}
```

### Current body
```
{{IMG:EB1911 Carpet - Fig. 8.—Lahore cut pile Carpet.jpg|CORNER OF A CUT PILE CARPET OF PERSIAN MANUFACTURE, 16th CENTURY}}

{{IMG:EB1911 Carpet - Fig. 9.—Persian cut pile Carpet.jpg|FINE CUT PILE LAHORE CARPET (c. 1664) BELONGING TO GIRDLERS’ COMPANY IN LONDON. OF PERSIAN DESIGN}}

{{IMG:EB1911 Carpet - Fig. 10.—Spanish Carpet.jpg|CUT PILE CARPET OF SPANISH MANUFACTURE, EARLY 16th CENTURY}}
```

---

## CAT — vol 05

**Article ID:** 4193046  
**Signature:** `html_table depth=0 wt=0 ht=1 has_colspan`

### Source excerpt
```
{{EB1911 fine print/s}}
{{right|{{sc|Plate I.}}}}
<table {{Ts|ma}}>
<tr><td {{Ts|width:420px}}>[[File:EB1911 Cat - Fig. 1.—SKINS OF THE BLOTCHED DOMESTIC CAT.jpg|EB1911 Cat - Fig. 1.—SKINS OF THE BLOTCHED DOMESTIC CAT.jpg]]&emsp;</td>
<td {{Ts|width:420px}}>&emsp;[[File:EB1911 Cat - Fig. 2.—SKINS OF THE STRIPED DOMESTIC CAT.jpg]]</td></tr>
<tr><td {{Ts|pl2|sm92|lh12}}>{{sc|Fig}}. 1.—SKINS OF THE BLOTCHED DOMESTIC CAT, SHOWING<br>&emsp;SOME OF THE VARIATIONS TO WHICH THE PATTERN IS<br>&emsp;LIABLE.&emsp;<span style="font-size:92%;>&emsp;(Cf. Fig. 5 on Plate II.)</span></td>
<td {{Ts|pl4|sm92|lh12}}>{{sc|Fig}}. 2.—SKINS OF THE STRIPED DOMESTIC CAT, GIVING<br>&emsp;THE “TICKED” BREED AND A PARTIALLY ALBINO<br>&emsp;SPECIMEN. <span style="font-size:92%;>&emsp;(Cf. Fig. 4 on Plate II.)</span></td></tr>

<tr {{Ts|ac}}><td colspan="2"><br>[[File:EB1911 Cat - Fig. 3.—SKINS OF THE EUROPEAN WILD CAT.jpg]]</td></tr>
<tr><td colspan="2" {{Ts|ac|sm92|lh12}}>{{sc|Fig}}. 3.—SKINS OF THE EUROPEAN WILD CAT, FROM<br>
ROSS-SHIRE, SCOTLAND. <span style="font-size:92%;>&emsp;(Cf. Fig. 1 on Plate II.)</span></td></tr>
</table>


{{c|{{fs90|''Note''—Of the two types of colouration found in modern domestic cats, the striped type obviously corresponds to the original
wild cat as seen in various parts of North Europe to-day. The origin of the blotched as a special type is wholly unknown.}}

{{fs90|(Photos from Plates VIII., IX., and X., ''P.Z.S.'', 1907, by permission of the Zoological Society of Lond
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **10** | **10** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **2** | **2** |
| header text     | 'Plate I' | 'Plate I' |
| footer text     | 'Note—Of the two types of colouration found in modern domestic cats, the striped type obviously corresponds to the origin' | 'Note—Of the two types of colouration found in modern domestic cats, the striped type obviously corresponds to the origin' |

**Verdict:** ✅ identical

### Baseline body
```
Plate I

{{IMG:EB1911 Cat - Fig. 1.—SKINS OF THE BLOTCHED DOMESTIC CAT.jpg|SKINS OF THE BLOTCHED DOMESTIC CAT, SHOWING SOME OF THE VARIATIONS TO WHICH THE PATTERN IS LIABLE. (Cf. Fig. 5 on Plate II.)}}

{{IMG:EB1911 Cat - Fig. 2.—SKINS OF THE STRIPED DOMESTIC CAT.jpg|SKINS OF THE STRIPED DOMESTIC CAT, GIVING THE “TICKED” BREED AND A PARTIALLY ALBINO SPECIMEN. (Cf. Fig. 4 on Plate II.)}}

{{IMG:EB1911 Cat - Fig. 3.—SKINS OF THE EUROPEAN WILD CAT.jpg|SKINS OF THE EUROPEAN WILD CAT, FROM ROSS-SHIRE, SCOTLAND. (Cf. Fig. 1 on Plate II.)}}

Note—Of the two types of colouration found in modern domestic cats, the striped type obviously corresponds to the original wild cat as seen in various parts of North Europe to-day. The origin of the blotched as a special type is wholly unknown. (Photos from Plates VIII., IX., and X., P.Z.S., 1907, by permission of the Zoological Society of London.)
```

### Current body
```
Plate I

{{IMG:EB1911 Cat - Fig. 1.—SKINS OF THE BLOTCHED DOMESTIC CAT.jpg|SKINS OF THE BLOTCHED DOMESTIC CAT, SHOWING SOME OF THE VARIATIONS TO WHICH THE PATTERN IS LIABLE. (Cf. Fig. 5 on Plate II.)}}

{{IMG:EB1911 Cat - Fig. 2.—SKINS OF THE STRIPED DOMESTIC CAT.jpg|SKINS OF THE STRIPED DOMESTIC CAT, GIVING THE “TICKED” BREED AND A PARTIALLY ALBINO SPECIMEN. (Cf. Fig. 4 on Plate II.)}}

{{IMG:EB1911 Cat - Fig. 3.—SKINS OF THE EUROPEAN WILD CAT.jpg|SKINS OF THE EUROPEAN WILD CAT, FROM ROSS-SHIRE, SCOTLAND. (Cf. Fig. 1 on Plate II.)}}

Note—Of the two types of colouration found in modern domestic cats, the striped type obviously corresponds to the original wild cat as seen in various parts of North Europe to-day. The origin of the blotched as a special type is wholly unknown. (Photos from Plates VIII., IX., and X., P.Z.S., 1907, by permission of the Zoological Society of London.)
```

---

## CAT — vol 05

**Article ID:** 4193047  
**Signature:** `html_table depth=0 wt=0 ht=1 has_colspan`

### Source excerpt
```
{{EB1911 fine print/s}}
{{sc|Plate II.}}
<table {{Ts|ma}}>
<tr><td>[[File:EB1911 Cat - Plate II, Fig. 1.—EUROPEAN WILD CAT.jpg]]</td>
<td>&emsp;[[File:EB1911 Cat - Plate II, Fig. 2.—PALLAS’S CAT.jpg]]</td></tr>
<tr><td  style="font-size:85%;">&emsp;<i>Photo, W. G. Berridge</i>.</td>
<td  style="font-size:85%;">{{gap}}''Photo, W. G. Berridge''.</td></tr>
<tr><td  align=center style="font-size:92%">{{sc|Fig}}. 1.—EUROPEAN WILD CAT.</td>
<td  align=center style="font-size:92%">{{sc|Fig}}. 2.—PALLAS’S CAT.</td></tr>

<tr><td>[[File:EB1911 Cat - Plate II, Fig. 3.—ROYAL SIAMESE CAT.jpg]]</td>
<td>&emsp;[[File:EB1911 Cat - Plate II, Fig. 4.—STRIPED DOMESTIC CAT.jpg]]</td></tr>
<tr><td  style="font-size:85%;">&emsp;<i>Photo, R. C. Ryan</i>.</td>
<td  style="font-size:85%;">{{gap}}''Photo, Topical Press Agency''.</td></tr>
<tr><td  align=center style="font-size:92%">{{sc|Fig}}. 3.—ROYAL SIAMESE CAT.</td>
<td  align=center style="font-size:92%">{{sc|Fig}}. 4.—STRIPED DOMESTIC CAT.</td></tr>

<tr><td>[[File:EB1911 Cat - Plate II, Fig. 5.—BLOTCHED DOMESTIC CAT.jpg]]</td>
<td>&emsp;[[File:EB1911 Cat - Plate II, Fig. 6.—TAIL-LESS CAT.jpg]]</td></tr>
<tr><td  style="font-size:85%;">&emsp;<i>Photo, Topical Press Agency</i></td>
<td  style="font-size:85%;">{{gap}}<i>Photo, R. C. Ryan</i></td></tr>
<tr><td  align=center style="font-size:92%">{{sc|Fig}}. 5.—BLOTCHED DOMESTIC CAT.</td>
<td  align=center style="font-size:92%">{{sc|Fig}}. 6.—TAIL-LESS CAT.</td></tr>

<tr><td>[[File:EB1911 Cat - Pl
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 9 | 9 |
| captioned       | 9 | 9 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **20** | **20** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'Plate II' | 'Plate II' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
Plate II

{{IMG:EB1911 Cat - Plate II, Fig. 1.—EUROPEAN WILD CAT.jpg|EUROPEAN WILD CAT (Photo, W. G. Berridge)}}

{{IMG:EB1911 Cat - Plate II, Fig. 2.—PALLAS’S CAT.jpg|PALLAS’S CAT (Photo, W. G. Berridge)}}

{{IMG:EB1911 Cat - Plate II, Fig. 3.—ROYAL SIAMESE CAT.jpg|ROYAL SIAMESE CAT (Photo, R. C. Ryan)}}

{{IMG:EB1911 Cat - Plate II, Fig. 4.—STRIPED DOMESTIC CAT.jpg|STRIPED DOMESTIC CAT (Photo, Topical Press Agency)}}

{{IMG:EB1911 Cat - Plate II, Fig. 5.—BLOTCHED DOMESTIC CAT.jpg|BLOTCHED DOMESTIC CAT (Photo, Topical Press Agency)}}

{{IMG:EB1911 Cat - Plate II, Fig. 6.—TAIL-LESS CAT.jpg|TAIL-LESS CAT (Photo, R. C. Ryan)}}

{{IMG:EB1911 Cat - Plate II, Fig. 7.—WHITE PERSIAN KITTEN.jpg|WHITE PERSIAN KITTEN (Photo, Topical Press Agency)}}

{{IMG:EB1911 Cat - Plate II, Fig. 8.—BLUE PERSIAN CAT.jpg|BLUE PERSIAN CAT (Photo, Topical Press Agency)}}

{{IMG:EB1911 Cat - Plate II, Fig. 9.—BLACK PERSIAN KITTEN.jpg|BLACK PERSIAN KITTEN (Photo, Topical Press Agency)}}
```

### Current body
```
Plate II

{{IMG:EB1911 Cat - Plate II, Fig. 1.—EUROPEAN WILD CAT.jpg|EUROPEAN WILD CAT (Photo, W. G. Berridge)}}

{{IMG:EB1911 Cat - Plate II, Fig. 2.—PALLAS’S CAT.jpg|PALLAS’S CAT (Photo, W. G. Berridge)}}

{{IMG:EB1911 Cat - Plate II, Fig. 3.—ROYAL SIAMESE CAT.jpg|ROYAL SIAMESE CAT (Photo, R. C. Ryan)}}

{{IMG:EB1911 Cat - Plate II, Fig. 4.—STRIPED DOMESTIC CAT.jpg|STRIPED DOMESTIC CAT (Photo, Topical Press Agency)}}

{{IMG:EB1911 Cat - Plate II, Fig. 5.—BLOTCHED DOMESTIC CAT.jpg|BLOTCHED DOMESTIC CAT (Photo, Topical Press Agency)}}

{{IMG:EB1911 Cat - Plate II, Fig. 6.—TAIL-LESS CAT.jpg|TAIL-LESS CAT (Photo, R. C. Ryan)}}

{{IMG:EB1911 Cat - Plate II, Fig. 7.—WHITE PERSIAN KITTEN.jpg|WHITE PERSIAN KITTEN (Photo, Topical Press Agency)}}

{{IMG:EB1911 Cat - Plate II, Fig. 8.—BLUE PERSIAN CAT.jpg|BLUE PERSIAN CAT (Photo, Topical Press Agency)}}

{{IMG:EB1911 Cat - Plate II, Fig. 9.—BLACK PERSIAN KITTEN.jpg|BLACK PERSIAN KITTEN (Photo, Topical Press Agency)}}
```

---

## CATTLE, PLATE I — vol 05

**Article ID:** 4193118  
**Signature:** `center_template depth=0 wt=0 ht=0 toplegend`

### Source excerpt
```
{{center|[[File:EB1911 Cattle - SHORTHORN BULL.jpg]]<br/>
SHORTHORN BULL.

[[File:EB1911 Cattle - DEVON BULL.jpg]]<br/>
DEVON BULL.

[[File:EB1911 Cattle - HEREFORD BULL.jpg]]<br/>
HEREFORD BULL.

[[File:EB1911 Cattle - SOUTH DEVON BULL.jpg]]<br/>
SOUTH DEVON BULL.{{em|2}}

BREEDS OF ENGLISH CATTLE.{{em|4}}<small>(From photographs by F. Babbage.)</small>}}
{{nop}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **12** | **12** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **2** | **2** |
| header text     | 'center' | 'center' |
| footer text     | 'BREEDS OF ENGLISH CATTLE.4(From photographs by F. Babbage.)' | 'BREEDS OF ENGLISH CATTLE.4(From photographs by F. Babbage.)' |

**Verdict:** ✅ identical

### Baseline body
```
center

{{IMG:EB1911 Cattle - SHORTHORN BULL.jpg|SHORTHORN BULL}}

{{IMG:EB1911 Cattle - DEVON BULL.jpg|DEVON BULL}}

{{IMG:EB1911 Cattle - HEREFORD BULL.jpg|HEREFORD BULL}}

{{IMG:EB1911 Cattle - SOUTH DEVON BULL.jpg|SOUTH DEVON BULL}}

BREEDS OF ENGLISH CATTLE.4(From photographs by F. Babbage.)
```

### Current body
```
center

{{IMG:EB1911 Cattle - SHORTHORN BULL.jpg|SHORTHORN BULL}}

{{IMG:EB1911 Cattle - DEVON BULL.jpg|DEVON BULL}}

{{IMG:EB1911 Cattle - HEREFORD BULL.jpg|HEREFORD BULL}}

{{IMG:EB1911 Cattle - SOUTH DEVON BULL.jpg|SOUTH DEVON BULL}}

BREEDS OF ENGLISH CATTLE.4(From photographs by F. Babbage.)
```

---

## CATTLE, PLATE II — vol 05

**Article ID:** 4193119  
**Signature:** `center_template depth=0 wt=0 ht=0 toplegend`

### Source excerpt
```
{{center|[[File:EB1911 Cattle - LONGHORN BULL.jpg]]<br/>
LONGHORN BULL.

[[File:EB1911 Cattle - RED POLLED BULL.jpg]]<br/>
RED POLLED BULL.

[[File:EB1911 Cattle - WELSH BULL.jpg]]<br/>
WELSH BULL.

[[File:EB1911 Cattle - SUSSEX BULL.jpg]]<br/>
SUSSEX BULL.

BREEDS OF ENGLISH AND WELSH CATTLE.<br>
{{smaller|(From photographs by F. Babbage.)}}}}
{{nop}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **13** | **13** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **2** | **2** |
| header text     | 'center' | 'center' |
| footer text     | '(From photographs by F. Babbage.)' | '(From photographs by F. Babbage.)' |

**Verdict:** ✅ identical

### Baseline body
```
center

{{IMG:EB1911 Cattle - LONGHORN BULL.jpg|LONGHORN BULL}}

{{IMG:EB1911 Cattle - RED POLLED BULL.jpg|RED POLLED BULL}}

{{IMG:EB1911 Cattle - WELSH BULL.jpg|WELSH BULL}}

{{IMG:EB1911 Cattle - SUSSEX BULL.jpg|SUSSEX BULL}}

{{LEGEND:BREEDS OF ENGLISH AND WELSH CATTLE}LEGEND}

(From photographs by F. Babbage.)
```

### Current body
```
center

{{IMG:EB1911 Cattle - LONGHORN BULL.jpg|LONGHORN BULL}}

{{IMG:EB1911 Cattle - RED POLLED BULL.jpg|RED POLLED BULL}}

{{IMG:EB1911 Cattle - WELSH BULL.jpg|WELSH BULL}}

{{IMG:EB1911 Cattle - SUSSEX BULL.jpg|SUSSEX BULL}}

{{LEGEND:BREEDS OF ENGLISH AND WELSH CATTLE}LEGEND}

(From photographs by F. Babbage.)
```

---

## CATTLE, PLATE III — vol 05

**Article ID:** 4193120  
**Signature:** `center_template depth=0 wt=0 ht=0 toplegend`

### Source excerpt
```
{{center|[[File:EB1911 Cattle - ABERDEEN-ANGUS BULL.jpg]]<br/>
ABERDEEN-ANGUS BULL.

[[File:EB1911 Cattle - GALLOWAY BULL.jpg]]<br/>
GALLOWAY BULL.

[[File:EB1911 Cattle - AYRSHIRE COW.jpg]]<br/>
AYRSHIRE COW.

[[File:EB1911 Cattle - HIGHLAND BULL.jpg]]<br/>
HIGHLAND  BULL.

{{em|13}}BREEDS OF SCOTCH CATTLE.&emsp;{{smaller|(From photographs by F. Babbage.)}}}}
{{nop}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **12** | **12** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **2** | **2** |
| header text     | 'center' | 'center' |
| footer text     | '13BREEDS OF SCOTCH CATTLE. (From photographs by F. Babbage.)' | '13BREEDS OF SCOTCH CATTLE. (From photographs by F. Babbage.)' |

**Verdict:** ✅ identical

### Baseline body
```
center

{{IMG:EB1911 Cattle - ABERDEEN-ANGUS BULL.jpg|ABERDEEN-ANGUS BULL}}

{{IMG:EB1911 Cattle - GALLOWAY BULL.jpg|GALLOWAY BULL}}

{{IMG:EB1911 Cattle - AYRSHIRE COW.jpg|AYRSHIRE COW}}

{{IMG:EB1911 Cattle - HIGHLAND BULL.jpg|HIGHLAND BULL}}

13BREEDS OF SCOTCH CATTLE. (From photographs by F. Babbage.)
```

### Current body
```
center

{{IMG:EB1911 Cattle - ABERDEEN-ANGUS BULL.jpg|ABERDEEN-ANGUS BULL}}

{{IMG:EB1911 Cattle - GALLOWAY BULL.jpg|GALLOWAY BULL}}

{{IMG:EB1911 Cattle - AYRSHIRE COW.jpg|AYRSHIRE COW}}

{{IMG:EB1911 Cattle - HIGHLAND BULL.jpg|HIGHLAND BULL}}

13BREEDS OF SCOTCH CATTLE. (From photographs by F. Babbage.)
```

---

## CATTLE, PLATE IV — vol 05

**Article ID:** 4193121  
**Signature:** `center_template depth=0 wt=0 ht=0 toplegend`

### Source excerpt
```
{{center|[[File:EB1911 Cattle - DEXTER BULL.jpg]]<br/>
DEXTER BULL.

[[File:EB1911 Cattle - KERRY COW.jpg]]<br/>
KERRY COW.

[[File:EB1911 Cattle - GUERNSEY COW.jpg]]<br/>
GUERNSEY COW.

[[File:EB1911 Cattle - JERSEY COW.jpg]]<br/>
JERSEY COW.

{{em}}BREEDS OF IRISH AND CHANNEL ISLANDS CATTLE.{{em}}{{smaller|(From photographs by F. Babbage.}})<br/>

{{em|2}}{{smaller|The comparative sizes of the animals are indicated by the scale of reproduction of the photographs.}}}}
{{nop}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **13** | **13** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **2** | **2** |
| header text     | 'center' | 'center' |
| footer text     | '2The comparative sizes of the animals are indicated by the scale of reproduction of the photographs' | '2The comparative sizes of the animals are indicated by the scale of reproduction of the photographs' |

**Verdict:** ✅ identical

### Baseline body
```
center

{{IMG:EB1911 Cattle - DEXTER BULL.jpg|DEXTER BULL}}

{{IMG:EB1911 Cattle - KERRY COW.jpg|KERRY COW}}

{{IMG:EB1911 Cattle - GUERNSEY COW.jpg|GUERNSEY COW}}

{{IMG:EB1911 Cattle - JERSEY COW.jpg|JERSEY COW}}

{{LEGEND:BREEDS OF IRISH AND CHANNEL ISLANDS CATTLE. (From photographs by F. Babbage. )}LEGEND}

2The comparative sizes of the animals are indicated by the scale of reproduction of the photographs
```

### Current body
```
center

{{IMG:EB1911 Cattle - DEXTER BULL.jpg|DEXTER BULL}}

{{IMG:EB1911 Cattle - KERRY COW.jpg|KERRY COW}}

{{IMG:EB1911 Cattle - GUERNSEY COW.jpg|GUERNSEY COW}}

{{IMG:EB1911 Cattle - JERSEY COW.jpg|JERSEY COW}}

{{LEGEND:BREEDS OF IRISH AND CHANNEL ISLANDS CATTLE. (From photographs by F. Babbage. )}LEGEND}

2The comparative sizes of the animals are indicated by the scale of reproduction of the photographs
```

---

## CAVALRY, PLATE I — vol 05

**Article ID:** 4193163  
**Signature:** `html_table depth=0 wt=0 ht=1 has_colspan`

### Source excerpt
```
<table {{Ts|ma|ac}}>
<tr><td align=center colspan="2">[[File:EB1911 Cavalry - Plate I a - Dragoons.jpg]]</td></tr>

<tr><td colspan="2">[[File:EB1911 Cavalry - Plate I b - Infantry v. Reiters.jpg]]</td></tr>
<tr><td  rowspan="2">[[File:EB1911 Cavalry - Plate I c - Squadron of Lancers.jpg]]</td>
<td><br /><br />SIXTEENTH-CENTURY CAVALRY.<br />
(Walthausen’s ''Art militaire de la cavalerie'', circa 1600.)</td></tr>
<tr><td>[[File:EB1911 Cavalry - Plate I d - Lancer.jpg]]</td></tr>
</table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 1 | 1 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **5** | **5** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Cavalry - Plate I a - Dragoons.jpg|SIXTEENTH-CENTURY CAVALRY. (Walthausen’s Art militaire de la cavalerie, circa 1600.)}}

{{IMG:EB1911 Cavalry - Plate I b - Infantry v. Reiters.jpg}}

{{IMG:EB1911 Cavalry - Plate I c - Squadron of Lancers.jpg}}

{{IMG:EB1911 Cavalry - Plate I d - Lancer.jpg}}
```

### Current body
```
{{IMG:EB1911 Cavalry - Plate I a - Dragoons.jpg|SIXTEENTH-CENTURY CAVALRY. (Walthausen’s Art militaire de la cavalerie, circa 1600.)}}

{{IMG:EB1911 Cavalry - Plate I b - Infantry v. Reiters.jpg}}

{{IMG:EB1911 Cavalry - Plate I c - Squadron of Lancers.jpg}}

{{IMG:EB1911 Cavalry - Plate I d - Lancer.jpg}}
```

---

## CAVALRY, PLATE II — vol 05

**Article ID:** 4193164  
**Signature:** `html_table depth=0 wt=0 ht=1`

### Source excerpt
```
<table {{Ts|ma|ac}}>
<tr><td>[[File:EB1911 Cavalry - Plate II - BATTLE OF STAFFARDA, 1690.jpg]]</td></tr>
<tr><td>BATTLE OF STAFFARDA, 1690. (''From a contemporary engraving.'')<br/>&nbsp;</td></tr>
<tr><td>[[File:EB1911 Cavalry - Plate II - ACTION ON THE BULGANAK, 1854.jpg]]</td></tr>
<tr><td>ACTION ON THE BULGANAK, 1854. (''From a lithograph by W. Simpson.'')<br/>&nbsp;</td></tr>
<tr><td>[[File:EB1911 Cavalry - Plate II - GERMAN GUARD DRAGOONS.jpg]]</td></tr>
<tr><td>GERMAN GUARD DRAGOONS. (''Photo, Gebruder Haeckel.'')<br/>&nbsp;</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Cavalry - Plate II - BATTLE OF STAFFARDA, 1690.jpg|BATTLE OF STAFFARDA, 1690. (From a contemporary engraving.)}}

{{IMG:EB1911 Cavalry - Plate II - ACTION ON THE BULGANAK, 1854.jpg|ACTION ON THE BULGANAK, 1854. (From a lithograph by W. Simpson.)}}

{{IMG:EB1911 Cavalry - Plate II - GERMAN GUARD DRAGOONS.jpg|GERMAN GUARD DRAGOONS. (Photo, Gebruder Haeckel.)}}
```

### Current body
```
{{IMG:EB1911 Cavalry - Plate II - BATTLE OF STAFFARDA, 1690.jpg|BATTLE OF STAFFARDA, 1690. (From a contemporary engraving.)}}

{{IMG:EB1911 Cavalry - Plate II - ACTION ON THE BULGANAK, 1854.jpg|ACTION ON THE BULGANAK, 1854. (From a lithograph by W. Simpson.)}}

{{IMG:EB1911 Cavalry - Plate II - GERMAN GUARD DRAGOONS.jpg|GERMAN GUARD DRAGOONS. (Photo, Gebruder Haeckel.)}}
```

---

## CERAMICS, PLATE I — vol 05

**Article ID:** 4193277  
**Signature:** `html_table depth=0 wt=0 ht=1`

### Source excerpt
```
<table style="font-size: 92%; line-height:125%; margin:auto; text-align:center;">
<tr><td>[[File:EB1911 Ceramics Fig. 52.—CORINTHIAN JAR.jpg]]&ensp;</td>
<td>&ensp;[[File:EB1911 Ceramics Fig. 53.—FRANÇOIS VASE.jpg]]</td></tr>
<tr><td style="vertical-align:top;">{{sc|Fig.}} 52.—CORINTHIAN JAR.</td>
<td style="text-align:center;">{{sc|Fig.}} 53.—FRANÇOIS VASE.<br />
<span style="font-size: 92%;">(From Furtwängler and Reichhold, ''Griechische Vasenmalerei'',<br>by permission of F. Bruckmann.)</span></td></tr>

<tr><td>[[File:EB1911 Ceramics Fig. 54.—BLACK-FIGURED AMPHORA BY EXEKIAS.jpg]]&ensp;</td>
<td><br/><br/>&ensp;[[File:EB1911 Ceramics Fig. 55.—VASE FROM SOUTHERN ITALY, signed by Python.jpg]]</td></tr>
<tr><td>{{sc|Fig.}} 54.—BLACK-FIGURED AMPHORA<br>BY EXEKIAS.</td>
<td style="text-align:center;">{{sc|Fig.}} 55.—VASE FROM SOUTHERN ITALY.<br />
<span style="font-size: 92%;">Signed by Python.</span></td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Ceramics Fig. 52.—CORINTHIAN JAR.jpg|CORINTHIAN JAR}}

{{IMG:EB1911 Ceramics Fig. 53.—FRANÇOIS VASE.jpg|FRANÇOIS VASE. (From Furtwängler and Reichhold, Griechische Vasenmalerei, by permission of F. Bruckmann.)}}

{{IMG:EB1911 Ceramics Fig. 54.—BLACK-FIGURED AMPHORA BY EXEKIAS.jpg|BLACK-FIGURED AMPHORA BY EXEKIAS}}

{{IMG:EB1911 Ceramics Fig. 55.—VASE FROM SOUTHERN ITALY, signed by Python.jpg|VASE FROM SOUTHERN ITALY. Signed by Python}}
```

### Current body
```
{{IMG:EB1911 Ceramics Fig. 52.—CORINTHIAN JAR.jpg|CORINTHIAN JAR}}

{{IMG:EB1911 Ceramics Fig. 53.—FRANÇOIS VASE.jpg|FRANÇOIS VASE. (From Furtwängler and Reichhold, Griechische Vasenmalerei, by permission of F. Bruckmann.)}}

{{IMG:EB1911 Ceramics Fig. 54.—BLACK-FIGURED AMPHORA BY EXEKIAS.jpg|BLACK-FIGURED AMPHORA BY EXEKIAS}}

{{IMG:EB1911 Ceramics Fig. 55.—VASE FROM SOUTHERN ITALY, signed by Python.jpg|VASE FROM SOUTHERN ITALY. Signed by Python}}
```

---

## CERAMICS, PLATE II — vol 05

**Article ID:** 4193278  
**Signature:** `html_table depth=0 wt=0 ht=1 has_colspan`

### Source excerpt
```
<table style="font-size: 92%;" align=center>
<tr><td colspan="2">[[File:EB1911 Ceramics Fig. 56.—BOWL MADE AT CALES IN IMITATION OF METAL. (2nd Cent. B.C.).jpg]]</td>
<td rowspan="5">[[File:EB1911 Ceramics Fig. 60.—AMPHORA OF APULIAN STYLE, WITH SCENE FROM EURIPIDES’ “HECUBA.”.jpg]]</td></tr>
<tr><td style="text-align:center;" colspan="2">{{sc|Fig.}} 56.—BOWL MADE AT CALES IN IMITATION OF METAL. (2ND CENT. {{asc|B.C.}})</td></tr>

<tr><td>[[File:EB1911 Ceramics Fig. 57.—VASE OF 5th Cent. B.C., MODELLED IN FORM OF HEAD.jpg]]</td>
<td>[[File:EB1911 Ceramics Fig. 58.—VASE OF 6th CENT. B.C., IN FORM OF HELMETED HEAD.jpg]]</td></tr>
<tr><td style="text-align:center;">{{sc|Fig.}} 57.—VASE OF {{sc|5th}} CENT. B.C.,<br>MODELLED IN FORM OF HEAD.</td>
<td style="text-align:center;">{{sc|Fig.}} 58.—VASE OF {{sc|6th}}<br>CENT. B.C., IN FORM<br>OF HELMETED HEAD.</td></tr>

<tr><td colspan="2">[[File:EB1911 Ceramics Fig. 59.—FLASK OF VITREOUS GLAZED WARE. (ROMAN PERIOD.).jpg]]</td></tr>
<tr><td style="text-align:center;" colspan="2">{{sc|Fig.}} 59.—FLASK OF VITREOUS GLAZED WARE.<br>(ROMAN PERIOD.)</td>
<td style="text-align:center;">{{sc|Fig.}} 60.—AMPHORA OF APULIAN STYLE, WITH<br>SCENE FROM EURIPIDES’ “HECUBA.”</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 5 | 5 |
| captioned       | 5 | 5 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **10** | **10** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Ceramics Fig. 56.—BOWL MADE AT CALES IN IMITATION OF METAL. (2nd Cent. B.C.).jpg|BOWL MADE AT CALES IN IMITATION OF METAL. (2ND CENT. B.C.)}}

{{IMG:EB1911 Ceramics Fig. 60.—AMPHORA OF APULIAN STYLE, WITH SCENE FROM EURIPIDES’ “HECUBA.”.jpg|VASE OF 5th CENT. B.C., MODELLED IN FORM OF HEAD}}

{{IMG:EB1911 Ceramics Fig. 57.—VASE OF 5th Cent. B.C., MODELLED IN FORM OF HEAD.jpg|VASE OF 6th CENT. B.C., IN FORM OF HELMETED HEAD}}

{{IMG:EB1911 Ceramics Fig. 58.—VASE OF 6th CENT. B.C., IN FORM OF HELMETED HEAD.jpg|FLASK OF VITREOUS GLAZED WARE. (ROMAN PERIOD.)}}

{{IMG:EB1911 Ceramics Fig. 59.—FLASK OF VITREOUS GLAZED WARE. (ROMAN PERIOD.).jpg|AMPHORA OF APULIAN STYLE, WITH SCENE FROM EURIPIDES’ “HECUBA.”}}
```

### Current body
```
{{IMG:EB1911 Ceramics Fig. 56.—BOWL MADE AT CALES IN IMITATION OF METAL. (2nd Cent. B.C.).jpg|BOWL MADE AT CALES IN IMITATION OF METAL. (2ND CENT. B.C.)}}

{{IMG:EB1911 Ceramics Fig. 60.—AMPHORA OF APULIAN STYLE, WITH SCENE FROM EURIPIDES’ “HECUBA.”.jpg|VASE OF 5th CENT. B.C., MODELLED IN FORM OF HEAD}}

{{IMG:EB1911 Ceramics Fig. 57.—VASE OF 5th Cent. B.C., MODELLED IN FORM OF HEAD.jpg|VASE OF 6th CENT. B.C., IN FORM OF HELMETED HEAD}}

{{IMG:EB1911 Ceramics Fig. 58.—VASE OF 6th CENT. B.C., IN FORM OF HELMETED HEAD.jpg|FLASK OF VITREOUS GLAZED WARE. (ROMAN PERIOD.)}}

{{IMG:EB1911 Ceramics Fig. 59.—FLASK OF VITREOUS GLAZED WARE. (ROMAN PERIOD.).jpg|AMPHORA OF APULIAN STYLE, WITH SCENE FROM EURIPIDES’ “HECUBA.”}}
```

---

## CERAMICS — vol 05

**Article ID:** 4193279  
**Signature:** `html_table depth=0 wt=0 ht=multi has_colspan`

### Source excerpt
```
<table {{Ts|ma|sm92|ac}}>
<tr><td {{Ts|ar}} colspan=3>{{sc|Plate III.}}</td></tr>
<tr><td style="padding-top: 1.5em; vertical-align:bottom;">[[File:EB1911 Ceramics Fig. 61.—MOULD FOR ARRETINE BOWL.jpg]]</td><td>{{gap}}</td>
<td style="padding-top: 1.5em;">[[File:EB1911 Ceramics Fig. 62.—JAR OF ARRETINE WARE FROM CAPUA.jpg]]</td></tr>
<tr><td style="padding-bottom: 1em; padding-left: 1em; padding-right: 1em;">{{sc|Fig.}} 61.—MOULD FOR ARRETINE BOWL.</td><td></td>
<td style="padding-bottom: 1em; padding-left: 1em; padding-right: 1em;">{{sc|Fig.}} 62.—JAR OF ARRETINE WARE FROM CAPUA.</td></tr></table>
<table {{Ts|ma|sm92|lh12|ac}}>
<tr><td style="padding-top: 1.5em;">[[File:EB1911 Ceramics Fig. 63.—EARLY ETRUSCAN JAR.jpg]]</td>
<td style="padding-top: 1.5em;">[[File:EB1911 Ceramics Fig. 64.—STAMP FOR ORNAMENTING ARRETINE VASE.jpg]]</td>
<td style="padding-top: 1.5em;">[[File:EB1911 Ceramics Fig. 65.—ETRUSCAN “CANOPIC” JAR PLACED IN BRONZE CHAIR.jpg]]</td></tr>
<tr><td style="padding-bottom: 1em; padding-left: 1em; padding-right: 1em;">{{sc|Fig.}} 63.—EARLY ETRUSCAN JAR.<br>(VILLANOVA PERIOD.)</td>
<td style="padding-bottom: 1em; padding-left: 1em; padding-right: 1em;">{{sc|Fig.}} 64.—STAMP FOR ORNAMENTING<br>ARRETINE VASE.</td>
<td style="padding-bottom: 1em; padding-left: 1em; padding-right: 1em;">{{sc|Fig.}} 65.—ETRUSCAN “CANOPIC”<br>JAR PLACED IN BRONZE CHAIR.</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 5 | 5 |
| captioned       | 5 | 5 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **12** | **12** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'Plate III' | 'Plate III' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
Plate III

{{IMG:EB1911 Ceramics Fig. 61.—MOULD FOR ARRETINE BOWL.jpg|MOULD FOR ARRETINE BOWL}}

{{IMG:EB1911 Ceramics Fig. 62.—JAR OF ARRETINE WARE FROM CAPUA.jpg|JAR OF ARRETINE WARE FROM CAPUA}}

{{IMG:EB1911 Ceramics Fig. 63.—EARLY ETRUSCAN JAR.jpg|EARLY ETRUSCAN JAR. (VILLANOVA PERIOD.)}}

{{IMG:EB1911 Ceramics Fig. 64.—STAMP FOR ORNAMENTING ARRETINE VASE.jpg|STAMP FOR ORNAMENTING ARRETINE VASE}}

{{IMG:EB1911 Ceramics Fig. 65.—ETRUSCAN “CANOPIC” JAR PLACED IN BRONZE CHAIR.jpg|ETRUSCAN “CANOPIC” JAR PLACED IN BRONZE CHAIR}}
```

### Current body
```
Plate III

{{IMG:EB1911 Ceramics Fig. 61.—MOULD FOR ARRETINE BOWL.jpg|MOULD FOR ARRETINE BOWL}}

{{IMG:EB1911 Ceramics Fig. 62.—JAR OF ARRETINE WARE FROM CAPUA.jpg|JAR OF ARRETINE WARE FROM CAPUA}}

{{IMG:EB1911 Ceramics Fig. 63.—EARLY ETRUSCAN JAR.jpg|EARLY ETRUSCAN JAR. (VILLANOVA PERIOD.)}}

{{IMG:EB1911 Ceramics Fig. 64.—STAMP FOR ORNAMENTING ARRETINE VASE.jpg|STAMP FOR ORNAMENTING ARRETINE VASE}}

{{IMG:EB1911 Ceramics Fig. 65.—ETRUSCAN “CANOPIC” JAR PLACED IN BRONZE CHAIR.jpg|ETRUSCAN “CANOPIC” JAR PLACED IN BRONZE CHAIR}}
```

---

## CERAMICS — vol 05

**Article ID:** 4193280  
**Signature:** `html_table depth=0 wt=0 ht=1 has_colspan`

### Source excerpt
```
<table {{Ts|ma|sm92|lh12|ac}}>
<tr><td {{Ts|ar}} colspan=2>{{sc|Plate}} IV.</td></tr>
<tr><td style="padding-top: 1.5em;" rowspan="3">[[File:EB1911 Ceramics Fig. 66.—MOULD FOR BOWL OF GERMAN WARE.jpg]]</td>
<td style="padding-top: 1.5em;">[[File:EB1911 Ceramics Fig. 67.—MEDALLION FROM VASE MADE IN S. FRANCE.jpg]]</td></tr>
<tr><td style="padding-bottom: 1em; padding-left: 1em; padding-right: 1em;">{{sc|Fig.}} 67.—MEDALLION FROM VASE MADE IN<br>S. FRANCE, WITH SCENE FROM TRAGEDY.<br>({{sc|3rd}} CENT. AFTER CHRIST.)</td></tr>
<tr><td style="padding-top: 1.5em;">[[File:EB1911 Ceramics Fig. 68.—JAR OF RHENISH WARE WITH INSCRIPTION.jpg]]</td></tr>
<tr><td style="padding-bottom: 1em; padding-left: 1em; padding-right: 1em;">{{sc|Fig.}} 66.—MOULD FOR BOWL OF GERMAN WARE.<br>({{sc|2nd}} CENT. AFTER CHRIST.)</td>
<td style="padding-bottom: 1em; padding-left: 1em; padding-right: 1em;">{{sc|Fig.}} 68.—JAR OF RHENISH WARE WITH<br>INSCRIPTION. ({{sc|3rd}} CENT. AFTER CHRIST.)</td></tr>

<tr><td style="padding-top: 1.5em;">[[File:EB1911 Ceramics Fig. 69.—BOWL OF GAULISH (LEZOUX) WARE.jpg]]</td>
<td style="padding-top: 1.5em;">[[File:EB1911 Ceramics Fig. 70.—JAR OF LATER LEZOUX WARE.jpg]]</td></tr>
<tr><td style="padding-bottom: 1em; padding-left: 1em; padding-right: 1em;">{{sc|Fig.}} 69.—BOWL OF GAULISH (LEZOUX) WARE WITH FIGURES<br>IN “FREE” STYLE. ({{sc|2nd}} CENT. AFTER CHRIST.)</td>
<td style="padding-bottom: 1em; padding-left: 1em; padding-right: 1em;">{{sc|Fig.}} 70.—JAR OF LATER LEZO
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 5 | 5 |
| captioned       | 5 | 5 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **12** | **12** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'Plate IV' | 'Plate IV' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
Plate IV

{{IMG:EB1911 Ceramics Fig. 66.—MOULD FOR BOWL OF GERMAN WARE.jpg|MEDALLION FROM VASE MADE IN S. FRANCE, WITH SCENE FROM TRAGEDY. (3rd CENT. AFTER CHRIST.)}}

{{IMG:EB1911 Ceramics Fig. 67.—MEDALLION FROM VASE MADE IN S. FRANCE.jpg|MOULD FOR BOWL OF GERMAN WARE. (2nd CENT. AFTER CHRIST.)}}

{{IMG:EB1911 Ceramics Fig. 68.—JAR OF RHENISH WARE WITH INSCRIPTION.jpg|JAR OF RHENISH WARE WITH INSCRIPTION. (3rd CENT. AFTER CHRIST.)}}

{{IMG:EB1911 Ceramics Fig. 69.—BOWL OF GAULISH (LEZOUX) WARE.jpg|BOWL OF GAULISH (LEZOUX) WARE WITH FIGURES IN “FREE” STYLE. (2nd CENT. AFTER CHRIST.)}}

{{IMG:EB1911 Ceramics Fig. 70.—JAR OF LATER LEZOUX WARE.jpg|JAR OF LATER LEZOUX WARE. (3rd CENT. AFTER CHRIST.)}}
```

### Current body
```
Plate IV

{{IMG:EB1911 Ceramics Fig. 66.—MOULD FOR BOWL OF GERMAN WARE.jpg|MEDALLION FROM VASE MADE IN S. FRANCE, WITH SCENE FROM TRAGEDY. (3rd CENT. AFTER CHRIST.)}}

{{IMG:EB1911 Ceramics Fig. 67.—MEDALLION FROM VASE MADE IN S. FRANCE.jpg|MOULD FOR BOWL OF GERMAN WARE. (2nd CENT. AFTER CHRIST.)}}

{{IMG:EB1911 Ceramics Fig. 68.—JAR OF RHENISH WARE WITH INSCRIPTION.jpg|JAR OF RHENISH WARE WITH INSCRIPTION. (3rd CENT. AFTER CHRIST.)}}

{{IMG:EB1911 Ceramics Fig. 69.—BOWL OF GAULISH (LEZOUX) WARE.jpg|BOWL OF GAULISH (LEZOUX) WARE WITH FIGURES IN “FREE” STYLE. (2nd CENT. AFTER CHRIST.)}}

{{IMG:EB1911 Ceramics Fig. 70.—JAR OF LATER LEZOUX WARE.jpg|JAR OF LATER LEZOUX WARE. (3rd CENT. AFTER CHRIST.)}}
```

---

## CERAMICS, PLATE V — vol 05

**Article ID:** 4193281  
**Signature:** `html_table depth=0 wt=0 ht=1`

### Source excerpt
```
<table style="margin:auto">
<tr><td style="text-align: center; margin: auto; padding-top: 1.5em;">[[File:EB1911 Ceramics - Plate V. Rhodian or Turkish (a).jpg]]</td>
<td style="text-align: center; margin: auto; padding-top: 1.5em;">[[File:EB1911 Ceramics - Plate V. Syro-Persian.jpg]]</td></tr>
<tr><td style="text-align: center;">Rhodian or Turkish:
16th century.</td>
<td style="text-align: center;">Syro-Persian:
13th century.</td></tr>

<tr><td style="text-align: center; margin: auto; padding-top: 1.5em;">[[File:EB1911 Ceramics - Plate V. Rhodian or Turkish; (b).jpg]]</td>
<td style="text-align: center; margin: auto; padding-top: 1.5em;">[[File:EB1911 Ceramics - Plate V. Rhodian or Turkish (c).jpg]]</td></tr>
<tr><td style="text-align: center;"> Rhodian or Turkish:
16th century.</td>
<td style="text-align: center;"> Rhodian or Turkish:
16th century.</td></tr>

<tr><td style="text-align: center; margin: auto; padding-top: 1.5em;">[[File:EB1911 Ceramics - Plate V. Damascus.jpg]]&emsp;</td>
<td style="text-align: center; margin: auto; padding-top: 1.5em;">&emsp;[[File:EB1911 Ceramics - Plate V. Persian.jpg]]</td></tr>
<tr><td style="text-align: center;">Damascus: 16th century.</td>
<td style="text-align: center;">Persian, lustre and underglaze colour: 13th century.</td></tr>
</table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 6 | 6 |
| captioned       | 6 | 6 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **12** | **12** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Ceramics - Plate V. Rhodian or Turkish (a).jpg|Rhodian or Turkish: 16th century}}

{{IMG:EB1911 Ceramics - Plate V. Syro-Persian.jpg|Syro-Persian: 13th century}}

{{IMG:EB1911 Ceramics - Plate V. Rhodian or Turkish; (b).jpg|Rhodian or Turkish: 16th century}}

{{IMG:EB1911 Ceramics - Plate V. Rhodian or Turkish (c).jpg|Rhodian or Turkish: 16th century}}

{{IMG:EB1911 Ceramics - Plate V. Damascus.jpg|Damascus: 16th century}}

{{IMG:EB1911 Ceramics - Plate V. Persian.jpg|Persian, lustre and underglaze colour: 13th century}}
```

### Current body
```
{{IMG:EB1911 Ceramics - Plate V. Rhodian or Turkish (a).jpg|Rhodian or Turkish: 16th century}}

{{IMG:EB1911 Ceramics - Plate V. Syro-Persian.jpg|Syro-Persian: 13th century}}

{{IMG:EB1911 Ceramics - Plate V. Rhodian or Turkish; (b).jpg|Rhodian or Turkish: 16th century}}

{{IMG:EB1911 Ceramics - Plate V. Rhodian or Turkish (c).jpg|Rhodian or Turkish: 16th century}}

{{IMG:EB1911 Ceramics - Plate V. Damascus.jpg|Damascus: 16th century}}

{{IMG:EB1911 Ceramics - Plate V. Persian.jpg|Persian, lustre and underglaze colour: 13th century}}
```

---

## CERAMICS, PLATE VI — vol 05

**Article ID:** 4193282  
**Signature:** `html_table depth=0 wt=0 ht=1 has_colspan`

### Source excerpt
```
<table style="font-size: 92%; line-height:125%; margin:auto; text-align:center;">
<tr><td>[[File:EB1911 Ceramics Plate VI - Calaggiolo - 16th century.jpg]] </td>
<td> [[File:EB1911 Ceramics Plate VI - Faenza. Casa Pirota, 1525.jpg]]</td></tr>
<tr><td>Calaggiolo: 16th century.</td>
<td>Faenza. Casa Pirota, 1525.</td></tr>

<tr><td colspan="2" align=center>[[File:EB1911 Ceramics Plate VI - Urbino. Decorated by Orario Fontana.jpg]]</td></tr>
<tr><td colspan="2">Urbino. Decorated by Orario Fontana.</td></tr>

<tr><td>[[File:EB1911 Ceramics Plate VI - Urbino. 1525 - Gonzaga Este.jpg]] </td>
<td> [[File:EB1911 Ceramics Plate VI - Faenza 15th C.jpg]]</td></tr>
<tr><td>Urbino. 1525 (?).<br/>A plate of the famous Gonzaga Este service.</td>
<td>Faenza: early 15th century.</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 5 | 5 |
| captioned       | 4 | 4 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **10** | **10** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Ceramics Plate VI - Calaggiolo - 16th century.jpg|Calaggiolo: 16th century}}

{{IMG:EB1911 Ceramics Plate VI - Faenza. Casa Pirota, 1525.jpg|Faenza. Casa Pirota, 1525}}

{{IMG:EB1911 Ceramics Plate VI - Urbino. Decorated by Orario Fontana.jpg|Urbino. 1525 (?). A plate of the famous Gonzaga Este service}}

{{IMG:EB1911 Ceramics Plate VI - Urbino. 1525 - Gonzaga Este.jpg|Faenza: early 15th century}}

{{IMG:EB1911 Ceramics Plate VI - Faenza 15th C.jpg}}

{{LEGEND:Urbino. Decorated by Orario Fontana}LEGEND}
```

### Current body
```
{{IMG:EB1911 Ceramics Plate VI - Calaggiolo - 16th century.jpg|Calaggiolo: 16th century}}

{{IMG:EB1911 Ceramics Plate VI - Faenza. Casa Pirota, 1525.jpg|Faenza. Casa Pirota, 1525}}

{{IMG:EB1911 Ceramics Plate VI - Urbino. Decorated by Orario Fontana.jpg|Urbino. 1525 (?). A plate of the famous Gonzaga Este service}}

{{IMG:EB1911 Ceramics Plate VI - Urbino. 1525 - Gonzaga Este.jpg|Faenza: early 15th century}}

{{IMG:EB1911 Ceramics Plate VI - Faenza 15th C.jpg}}

{{LEGEND:Urbino. Decorated by Orario Fontana}LEGEND}
```

---

## CERAMICS, PLATE VII — vol 05

**Article ID:** 4193283  
**Signature:** `html_table depth=0 wt=0 ht=multi has_colspan`

### Source excerpt
```
<table style="font-size: 92%" align=center>
<tr><td>[[File:EB1911 Ceramics Plate VII - Chinese. Sang de Bœuf.jpg]]</td>
<td>[[File:EB1911 Ceramics Plate VII - Chinese. Turquoise glaze.jpg]]</td>
<td>[[File:EB1911 Ceramics Plate VII - Chinese. Flambé.jpg]]</td></tr>
<tr><td style="text-align:center;">Chinese. Sang de B&oelig;uf.</td>
<td style="text-align:center;">Chinese. Turquoise glaze “crackled.”</td>
<td style="text-align:center;">Chinese. Flambé.</td></tr></table>

<table style="font-size: 92%" align=center>
<tr><td colspan="5">[[File:EB1911 Ceramics Plate VII - Various Vases.jpg]]</td></tr>
<tr><td style="text-align:center;">Purple Soufflé.</td>
<td style="text-align:center;">Coral red.</td>
<td style="text-align:center;">Peach blow.<br />Pigeon’s blood.</td>
<td style="text-align:center;">Lemon yellow.</td>
<td style="text-align:center;">Apple green.</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **9** | **9** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Ceramics Plate VII - Chinese. Sang de Bœuf.jpg|Chinese. Sang de B&oelig;uf}}

{{IMG:EB1911 Ceramics Plate VII - Chinese. Turquoise glaze.jpg|Chinese. Turquoise glaze “crackled.”}}

{{IMG:EB1911 Ceramics Plate VII - Chinese. Flambé.jpg|Chinese. Flambé}}

{{IMG:EB1911 Ceramics Plate VII - Various Vases.jpg|Purple Soufflé}}

{{LEGEND:Peach blow. Pigeon’s blood}LEGEND}
```

### Current body
```
{{IMG:EB1911 Ceramics Plate VII - Chinese. Sang de Bœuf.jpg|Chinese. Sang de B&oelig;uf}}

{{IMG:EB1911 Ceramics Plate VII - Chinese. Turquoise glaze.jpg|Chinese. Turquoise glaze “crackled.”}}

{{IMG:EB1911 Ceramics Plate VII - Chinese. Flambé.jpg|Chinese. Flambé}}

{{IMG:EB1911 Ceramics Plate VII - Various Vases.jpg|Purple Soufflé}}

{{LEGEND:Peach blow. Pigeon’s blood}LEGEND}
```

---

## CERAMICS, PLATE VIII — vol 05

**Article ID:** 4193284  
**Signature:** `html_table depth=0 wt=0 ht=multi`

### Source excerpt
```
<table style="font-size: 92%" align=center>
<tr><td style="padding-right:1.5em;">[[File:EB1911 Ceramics Plate VIII - Chinese. K’ang-hsi period.jpg]]</td>
<td style="padding-left:1.5em; padding-right:1.5em;" align=center>[[File:EB1911 Ceramics Plate VIII - Chinese. Black, K’ang-hsi.jpg]]</td>
<td style="padding-left:1.5em;">[[File:EB1911 Ceramics Plate VIII - Chinese (Famille Verte). K’ang-hsi.jpg]]</td></tr>
<tr><td style="text-align:center;">Chinese.&emsp;K’ang-hsi period.<br>&emsp;</td>
<td style="text-align:center;">Chinese.&emsp;Black ground.<br>K’ang-hsi period.</td>
<td style="text-align:center;">Chinese (''Famille Verte'').<br>
K’ang-hsi period.</td></tr></table>


<table style="font-size: 92%" align=center>
<tr><td>[[File:EB1911 Ceramics Plate VIII - Chinese (Famille Rose). Ch’ien-lung.jpg]]</td>
<td>[[File:EB1911 Ceramics Plate VIII - Chinese. Plum-blossom jar. K’ang-hsi.jpg]]</td></tr>
<tr><td style="text-align:center;">Chinese (''Famille Rose'').&emsp;Ch’ien-lung period.</td>
<td style="text-align:center;">Chinese.&emsp;Plum-blossom jar.&emsp;K’ang-hsi period.</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 5 | 5 |
| captioned       | 5 | 5 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **10** | **10** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Ceramics Plate VIII - Chinese. K’ang-hsi period.jpg|Chinese. K’ang-hsi period}}

{{IMG:EB1911 Ceramics Plate VIII - Chinese. Black, K’ang-hsi.jpg|Chinese. Black ground. K’ang-hsi period}}

{{IMG:EB1911 Ceramics Plate VIII - Chinese (Famille Verte). K’ang-hsi.jpg|Chinese (Famille Verte). K’ang-hsi period}}

{{IMG:EB1911 Ceramics Plate VIII - Chinese (Famille Rose). Ch’ien-lung.jpg|Chinese (Famille Rose). Ch’ien-lung period}}

{{IMG:EB1911 Ceramics Plate VIII - Chinese. Plum-blossom jar. K’ang-hsi.jpg|Chinese. Plum-blossom jar. K’ang-hsi period}}
```

### Current body
```
{{IMG:EB1911 Ceramics Plate VIII - Chinese. K’ang-hsi period.jpg|Chinese. K’ang-hsi period}}

{{IMG:EB1911 Ceramics Plate VIII - Chinese. Black, K’ang-hsi.jpg|Chinese. Black ground. K’ang-hsi period}}

{{IMG:EB1911 Ceramics Plate VIII - Chinese (Famille Verte). K’ang-hsi.jpg|Chinese (Famille Verte). K’ang-hsi period}}

{{IMG:EB1911 Ceramics Plate VIII - Chinese (Famille Rose). Ch’ien-lung.jpg|Chinese (Famille Rose). Ch’ien-lung period}}

{{IMG:EB1911 Ceramics Plate VIII - Chinese. Plum-blossom jar. K’ang-hsi.jpg|Chinese. Plum-blossom jar. K’ang-hsi period}}
```

---

## CERAMICS, PLATE IX — vol 05

**Article ID:** 4193285  
**Signature:** `html_table depth=0 wt=0 ht=1`

### Source excerpt
```
<table style="font-size: 92%" align=center>
<tr><td>[[File:EB1911 Ceramics Plate IX - Sèvres. Pâte-tendre c.1757.jpg]]</td>
<td align=center style="padding-left:2.5em;">[[File:EB1911 Ceramics Plate IX -Meissen. May-flower vase.jpg]]</td></tr>
<tr><td style="text-align:center;">Sèvres. Pâte-tendre, ''c''. 1757, painted by Falot and Morin.</td>
<td style="text-align:center; padding-left:2.5em;">Meissen. May-flower vase mounted in ormolu. Pâte-dure.</td></tr>
<tr><td>&nbsp;</td></tr>
<tr><td>[[File:EB1911 Ceramics Plate IX - Meissen. Crinoline figure.jpg]]</td>
<td style="padding-left:2.5em;">[[File:EB1911 Ceramics Plate IX - Sèvres. Pâte-tendre c.1756.jpg]]</td></tr>
<tr><td style="text-align:center;">Meissen. Crinoline figure (Kandler), Pâte-dure.</td>
<td style="text-align:center; padding-left:2.5em;">Sèvres. Pâte-tendre, ''c''. 1756.</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Ceramics Plate IX - Sèvres. Pâte-tendre c.1757.jpg|Sèvres. Pâte-tendre, c. 1757, painted by Falot and Morin}}

{{IMG:EB1911 Ceramics Plate IX -Meissen. May-flower vase.jpg|Meissen. May-flower vase mounted in ormolu. Pâte-dure}}

{{IMG:EB1911 Ceramics Plate IX - Meissen. Crinoline figure.jpg|Meissen. Crinoline figure (Kandler), Pâte-dure}}

{{IMG:EB1911 Ceramics Plate IX - Sèvres. Pâte-tendre c.1756.jpg|Sèvres. Pâte-tendre, c. 1756}}
```

### Current body
```
{{IMG:EB1911 Ceramics Plate IX - Sèvres. Pâte-tendre c.1757.jpg|Sèvres. Pâte-tendre, c. 1757, painted by Falot and Morin}}

{{IMG:EB1911 Ceramics Plate IX -Meissen. May-flower vase.jpg|Meissen. May-flower vase mounted in ormolu. Pâte-dure}}

{{IMG:EB1911 Ceramics Plate IX - Meissen. Crinoline figure.jpg|Meissen. Crinoline figure (Kandler), Pâte-dure}}

{{IMG:EB1911 Ceramics Plate IX - Sèvres. Pâte-tendre c.1756.jpg|Sèvres. Pâte-tendre, c. 1756}}
```

---

## CERAMICS, PLATE X — vol 05

**Article ID:** 4193286  
**Signature:** `html_table depth=0 wt=0 ht=1 has_colspan`

### Source excerpt
```
<table style="font-size: 92%" align=center>
<tr><td>[[File:EB1911 Ceramics Plate X - Chelsea porcelain.jpg]]</td>
<td style="text-align:center; padding-left:2.0em;">[[File:EB1911 Ceramics Plate X - Worcester Porcelain.jpg]]</td></tr>
<tr><td style="text-align:center;">Chelsea porcelain; 1745–1770.<br>
Figure after Watteau.</td>
<td style="text-align:center; padding-left:2.0em;">Worcester Porcelain; ''c''. 1760–1770.</td></tr>

<tr><td colspan="2" align=center>[[File:EB1911 Ceramics Plate X - Whieldon and Wedgwood.jpg]]</td></tr>
<tr><td style="text-align:center;" colspan="2">Whieldon and Wedgwood,<br />
cauliflower ware; c. 1750–1760.</td></tr>

<tr><td>[[File:EB1911 Ceramics Plate X - Wedgwood’s jasper.jpg]]</td>
<td style="padding-left:2.0em;">[[File:EB1911 Ceramics Plate X - Turner’s jasper.jpg]]</td></tr>
<tr><td style="text-align:center;">Wedgwood’s jasper; ''c''. 1780.</td>
<td style="text-align:center; padding-left:2.0em;"">Turner’s jasper; ''c''. 1780.</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 5 | 5 |
| captioned       | 4 | 4 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **10** | **10** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Ceramics Plate X - Chelsea porcelain.jpg|Chelsea porcelain; 1745–1770. Figure after Watteau}}

{{IMG:EB1911 Ceramics Plate X - Worcester Porcelain.jpg|Worcester Porcelain; c. 1760–1770}}

{{IMG:EB1911 Ceramics Plate X - Whieldon and Wedgwood.jpg|Wedgwood’s jasper; c. 1780}}

{{IMG:EB1911 Ceramics Plate X - Wedgwood’s jasper.jpg|Turner’s jasper; c. 1780}}

{{IMG:EB1911 Ceramics Plate X - Turner’s jasper.jpg}}

{{LEGEND:Whieldon and Wedgwood, cauliflower ware; c. 1750–1760}LEGEND}
```

### Current body
```
{{IMG:EB1911 Ceramics Plate X - Chelsea porcelain.jpg|Chelsea porcelain; 1745–1770. Figure after Watteau}}

{{IMG:EB1911 Ceramics Plate X - Worcester Porcelain.jpg|Worcester Porcelain; c. 1760–1770}}

{{IMG:EB1911 Ceramics Plate X - Whieldon and Wedgwood.jpg|Wedgwood’s jasper; c. 1780}}

{{IMG:EB1911 Ceramics Plate X - Wedgwood’s jasper.jpg|Turner’s jasper; c. 1780}}

{{IMG:EB1911 Ceramics Plate X - Turner’s jasper.jpg}}

{{LEGEND:Whieldon and Wedgwood, cauliflower ware; c. 1750–1760}LEGEND}
```

---

## CHASUBLE, PLATE I — vol 05

**Article ID:** 4193636  
**Signature:** `html_table depth=0 wt=0 ht=multi has_colspan`

### Source excerpt
```
<table {{Ts|ma}}>
<tr style="text-align:center"><td>[[File:EB1911 Chasuble - Fig. 2.—Chasuble of Pope Calixtus III.jpg]]&emsp;</td>
<td>&emsp;[[File:EB1911 Chasuble - Fig. 3.—Chasuble of Pope Pius V.jpg]]</td></tr>

<tr {{Ts|sm92|lh13}}><td>{{sc|Fig}}. 2.—Chasuble of Pope Calixtus III. (15th century) preserved at Valencia.</td>

<td>{{sc|Fig}}. 3.—Chasuble of Pope Pius V. (late 15th century)<br/>at S. Maria Maggiore at Rome.</td></tr>

<tr {{Ts|sm85|lh11}}><td>From a photograph by Father J. L. Braun in ''Die liturg Gewandung'',<br/>by permission of the publisher, B. Herder.</td>

<td>From a photograph by Father J. L. Braun<br/>in ''Die liturg Gewandung''.</td></tr>

<tr style="text-align:center"><td colspan=2><br/>[[File:EB1911 Chasuble - Fig. 4.—Chasuble dedicated by Stephen of Hungary.jpg]]</td></tr>
<tr {{Ts|sm92|lh13|ac}}><td colspan=2>{{sc|Fig}}. 4.—Chasuble dedicated by Stephen of Hungary (997–1038) and his wife Gisela,<br/>used as the Hungarian Coronation Robe.</td></tr>
<tr {{Ts|sm85|lh11|ac}}><td colspan=2>(From Braun, ''Die liturg.  Gewandung''.)</td></tr></table>


<table {{Ts|ma}}>
<tr style="text-align:center"><td>[[File:EB1911 Chasuble - Fig. 5.—Modern Roman Chasuble of Archbishop Bourne of Westminster.jpg]]&emsp;</td>
<td>&emsp;[[File:EB1911 Chasuble - Fig. 6.—Modern English Chasuble.jpg]]</td></tr>

<tr {{Ts|sm92|lh13|ac}}><td>{{sc|Fig}}. 5.—Modern Roman Chasuble of Archbishop<br/>Bourne of Westminster.</td>
<td>{{sc|Fig}}. 6.—Modern English Chasuble, used at 
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 5 | 5 |
| captioned       | 5 | 5 |
| legends         | 3 | 3 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **13** | **13** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Chasuble - Fig. 2.—Chasuble of Pope Calixtus III.jpg|Chasuble of Pope Calixtus III. (15th century) preserved at Valencia}}

{{IMG:EB1911 Chasuble - Fig. 3.—Chasuble of Pope Pius V.jpg|Chasuble of Pope Pius V. (late 15th century) at S. Maria Maggiore at Rome}}

{{IMG:EB1911 Chasuble - Fig. 4.—Chasuble dedicated by Stephen of Hungary.jpg|Chasuble dedicated by Stephen of Hungary (997–1038) and his wife Gisela, used as the Hungarian Coronation Robe}}

{{IMG:EB1911 Chasuble - Fig. 5.—Modern Roman Chasuble of Archbishop Bourne of Westminster.jpg|Modern Roman Chasuble of Archbishop Bourne of Westminster}}

{{IMG:EB1911 Chasuble - Fig. 6.—Modern English Chasuble.jpg|Modern English Chasuble, used at St Paul’s Church, Knightsbridge, London}}

{{LEGEND:From a photograph by Father J. L. Braun in Die liturg Gewandung, by permission of the publisher, B. Herder}LEGEND}

{{LEGEND:From a photograph by Father J. L. Braun in Die liturg Gewandung}LEGEND}

{{LEGEND:(From Braun, Die liturg. Gewandung.)}LEGEND}
```

### Current body
```
{{IMG:EB1911 Chasuble - Fig. 2.—Chasuble of Pope Calixtus III.jpg|Chasuble of Pope Calixtus III. (15th century) preserved at Valencia}}

{{IMG:EB1911 Chasuble - Fig. 3.—Chasuble of Pope Pius V.jpg|Chasuble of Pope Pius V. (late 15th century) at S. Maria Maggiore at Rome}}

{{IMG:EB1911 Chasuble - Fig. 4.—Chasuble dedicated by Stephen of Hungary.jpg|Chasuble dedicated by Stephen of Hungary (997–1038) and his wife Gisela, used as the Hungarian Coronation Robe}}

{{IMG:EB1911 Chasuble - Fig. 5.—Modern Roman Chasuble of Archbishop Bourne of Westminster.jpg|Modern Roman Chasuble of Archbishop Bourne of Westminster}}

{{IMG:EB1911 Chasuble - Fig. 6.—Modern English Chasuble.jpg|Modern English Chasuble, used at St Paul’s Church, Knightsbridge, London}}

{{LEGEND:From a photograph by Father J. L. Braun in Die liturg Gewandung, by permission of the publisher, B. Herder}LEGEND}

{{LEGEND:From a photograph by Father J. L. Braun in Die liturg Gewandung}LEGEND}

{{LEGEND:(From Braun, Die liturg. Gewandung.)}LEGEND}
```

---

## CHASUBLE, PLATE II — vol 05

**Article ID:** 4193637  
**Signature:** `html_table depth=0 wt=0 ht=1`

### Source excerpt
```
<table {{Ts|ma}}>
<tr><td>[[File:EB1911 Chasuble - Fig. 7.—Back of a Chasuble of Italian Brocaded Damask.jpg]]</td></tr>
<tr {{Ts|sm92|lh13|pl2|ac}}><td>{{sc|Fig}}. 7.—Back of a Chasuble of Italian Brocaded Damask (Red) with Embroidered Orphreys. The Vestment is of the early<br/>16th century, the Orphreys of the late 14th century.&ensp;(English.&ensp;In the Victoria and Albert Museum.)</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **2** | **2** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Chasuble - Fig. 7.—Back of a Chasuble of Italian Brocaded Damask.jpg|Back of a Chasuble of Italian Brocaded Damask (Red) with Embroidered Orphreys. The Vestment is of the early 16th century, the Orphreys of the late 14th century. (English. In the Victoria and Albert Museum.)}}
```

### Current body
```
{{IMG:EB1911 Chasuble - Fig. 7.—Back of a Chasuble of Italian Brocaded Damask.jpg|Back of a Chasuble of Italian Brocaded Damask (Red) with Embroidered Orphreys. The Vestment is of the early 16th century, the Orphreys of the late 14th century. (English. In the Victoria and Albert Museum.)}}
```

---

## CHINA, PLATE I — vol 06

**Article ID:** 4193864  
**Signature:** `wikitable depth=2 wt=multi ht=0 has_colspan`

### Source excerpt
```
{|align="center"
|valign="bottom" align="center"|
{|
|align="center"|[[Image:EB1911 China - Ku K‘ai-chih- Toilet Scene.jpg|375px]]
|-
|align="center"|{{sc|Fig.}} 1.—KU K&lsquo;AI-CHIH. TOILET SCENE.<br/>(British Museum. 4th Cent. {{asc|A.D.}}).
|-
|align="center"|[[Image:EB1911 China - Chao Mêng-fu - Scene on the Wang Ch‘uan.jpg|375px]]
|-
|align="center"|{{sc|Fig.}} 3.—CHAO MÊNG-FU, AFTER WANG WEI<br/>(8th CENT.). SCENE ON THE WANG CH&lsquo;UAN.<br/>(Dated 1309. British Museum.)
|}
|valign="bottom" align="center"|
{|
|align="center"|[[Image:EB1911 China - Kiu Ying - Court Ladies.jpg|375px]]
|-
|align="center"|{{sc|Fig.}} 6.—KIU YING. COURT LADIES.<br/>(British Museum. 15th Cent.)
|-
|align="center"|[[Image:EB1911 China - Hsü Hsi - Bird on Apple-bough.jpg|375px]]
|-
|align="center"|{{sc|Fig.}}4.—HSÜ HSI. BIRD ON APPLE-BOUGH.<br/>(10th Cent.)
|}
|-
|colspan="2" align="center"|
{|
|align="center"|[[Image:EB1911 China - Wu Taotzü- Sakyamuni.jpg|x500px]]
|align="center"|[[Image:EB1911 China - Chien Shun-chü - Emperor Huan-yeh.jpg|x500px]]
|align="center"|[[Image:EB1911 China - Lin Liang - Eagle.jpg|x500px]]
|-
|align="center"|{{sc|Fig.}}&nbsp;2.—ATTRIBUTED&nbsp;TO&nbsp;WU&nbsp;TAOTZÜ.<br/>SAKYAMUNI. (8th Cent.)
|align="center"|{{sc|Fig.}} 5.—CHIEN SHUN-CHU.<br/>THE&nbsp;EMPEROR&nbsp;HUAN-YEH.&nbsp;(15th&nbsp;Cent.)
|align="center"|{{sc|Fig.}} 7.—EAGLE. By LIN LIANG.<br/>(15th Cent. British Museum.)
|}
|-
|colspan="2" align="center"|
{{sm|Figs. 2, 4, and 5 are reproduced by permis
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 7 | 7 |
| captioned       | 7 | 7 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **16** | **16** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | 'Figs. 2, 4, and 5 are reproduced by permission of the Kokka Company, Tokyo' | 'Figs. 2, 4, and 5 are reproduced by permission of the Kokka Company, Tokyo' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 China - Ku K‘ai-chih- Toilet Scene.jpg|KU K&lsquo;AI-CHIH. TOILET SCENE. (British Museum. 4th Cent. A.D.)}}

{{IMG:EB1911 China - Chao Mêng-fu - Scene on the Wang Ch‘uan.jpg|CHAO MÊNG-FU, AFTER WANG WEI (8th CENT.). SCENE ON THE WANG CH&lsquo;UAN. (Dated 1309. British Museum.)}}

{{IMG:EB1911 China - Kiu Ying - Court Ladies.jpg|KIU YING. COURT LADIES. (British Museum. 15th Cent.)}}

{{IMG:EB1911 China - Hsü Hsi - Bird on Apple-bough.jpg|HSÜ HSI. BIRD ON APPLE-BOUGH. (10th Cent.)}}

{{IMG:EB1911 China - Wu Taotzü- Sakyamuni.jpg|ATTRIBUTED TO WU TAOTZÜ. SAKYAMUNI. (8th Cent.)}}

{{IMG:EB1911 China - Chien Shun-chü - Emperor Huan-yeh.jpg|CHIEN SHUN-CHU. THE EMPEROR HUAN-YEH. (15th Cent.)}}

{{IMG:EB1911 China - Lin Liang - Eagle.jpg|EAGLE. By LIN LIANG. (15th Cent. British Museum.)}}

Figs. 2, 4, and 5 are reproduced by permission of the Kokka Company, Tokyo
```

### Current body
```
{{IMG:EB1911 China - Ku K‘ai-chih- Toilet Scene.jpg|KU K&lsquo;AI-CHIH. TOILET SCENE. (British Museum. 4th Cent. A.D.)}}

{{IMG:EB1911 China - Chao Mêng-fu - Scene on the Wang Ch‘uan.jpg|CHAO MÊNG-FU, AFTER WANG WEI (8th CENT.). SCENE ON THE WANG CH&lsquo;UAN. (Dated 1309. British Museum.)}}

{{IMG:EB1911 China - Kiu Ying - Court Ladies.jpg|KIU YING. COURT LADIES. (British Museum. 15th Cent.)}}

{{IMG:EB1911 China - Hsü Hsi - Bird on Apple-bough.jpg|HSÜ HSI. BIRD ON APPLE-BOUGH. (10th Cent.)}}

{{IMG:EB1911 China - Wu Taotzü- Sakyamuni.jpg|ATTRIBUTED TO WU TAOTZÜ. SAKYAMUNI. (8th Cent.)}}

{{IMG:EB1911 China - Chien Shun-chü - Emperor Huan-yeh.jpg|CHIEN SHUN-CHU. THE EMPEROR HUAN-YEH. (15th Cent.)}}

{{IMG:EB1911 China - Lin Liang - Eagle.jpg|EAGLE. By LIN LIANG. (15th Cent. British Museum.)}}

Figs. 2, 4, and 5 are reproduced by permission of the Kokka Company, Tokyo
```

---

## CHINA, PLATE II — vol 06

**Article ID:** 4193865  
**Signature:** `wikitable depth=1 wt=1 ht=0 has_colspan`

### Source excerpt
```
{|align="center"
|align="center"|[[Image:EB1911 China - Temple Vase.jpg|x400px]]
|align="center"|[[Image:EB1911 China - Wine Vase.jpg|x400px]]
|align="center"|[[Image:EB1911 China - Wine Vase (2).jpg|x400px]]
|-
|align="center"|{{sc|Fig.}} 9.—TEMPLE VASE (''c''. 1200 {{asc|B.C.}}).
|align="center"|{{sc|Fig.}} 10.—WINE VASE (''c''. 1000 {{asc|B.C.}}).
|align="center"|{{sc|Fig.}} 11—WINE VASE (''c''. 600 {{asc|B.C.}}).
|-
|align="center"|[[Image:EB1911 China - Inlaid Vessel.jpg|x400px]]
|align="center"|[[Image:EB1911 China - Wine Vessel.jpg|x400px]]
|align="center"|[[Image:EB1911 China - Inlaid Vase.jpg|x400px]]
|-
|align="center" valign="top"|{{sc|Fig.}} 12.—INLAID VESSEL<br/>(''c''. 500 {{asc|B.C.}}).
|align="center" valign="top"|{{sc|Fig.}} 13.—WINE VESSEL (''c''. 100 {{asc|B.C.}}).
|align="center" valign="top"|{{sc|Fig.}} 14.—INLAID VASE (''c''. 200 {{asc|A.D.}}).<br/>In possession of C.J. Holmes.
|-
|align="center"|[[Image:EB1911 China - Vase.jpg|x400px]]
|align="center"|[[Image:EB1911 China - Wine Vessel (2).jpg|x400px]]
|align="center"|[[Image:EB1911 China - Temple Vase (2).jpg|x400px]]
|-
|align="center"|{{sc|Fig.}} 15.—VASE (''c''. 1450 {{asc|A.D.}}).
|align="center"|{{sc|Fig.}} 16.—WINE VESSEL (''c''. 1450 {{asc|A.D.}}).
|align="center"|{{sc|Fig.}} 17.—TEMPLE VASE (''c''. 1700 {{asc|A.D.}}).
|-
|colspan="3" align="center"|{{sm|Figs. 9-13 and 15-17 are from originals in the Victoria and Albert Museum, South Kensington.}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 9 | 9 |
| captioned       | 9 | 9 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **20** | **20** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | 'Figs. 9-13 and 15-17 are from originals in the Victoria and Albert Museum, South Kensington' | 'Figs. 9-13 and 15-17 are from originals in the Victoria and Albert Museum, South Kensington' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 China - Temple Vase.jpg|TEMPLE VASE (c. 1200 B.C.)}}

{{IMG:EB1911 China - Wine Vase.jpg|WINE VASE (c. 1000 B.C.)}}

{{IMG:EB1911 China - Wine Vase (2).jpg|Fig. 11—WINE VASE (c. 600 B.C.)}}

{{IMG:EB1911 China - Inlaid Vessel.jpg|INLAID VESSEL (c. 500 B.C.)}}

{{IMG:EB1911 China - Wine Vessel.jpg|WINE VESSEL (c. 100 B.C.)}}

{{IMG:EB1911 China - Inlaid Vase.jpg|INLAID VASE (c. 200 A.D.). In possession of C.J. Holmes}}

{{IMG:EB1911 China - Vase.jpg|VASE (c. 1450 A.D.)}}

{{IMG:EB1911 China - Wine Vessel (2).jpg|WINE VESSEL (c. 1450 A.D.)}}

{{IMG:EB1911 China - Temple Vase (2).jpg|TEMPLE VASE (c. 1700 A.D.)}}

Figs. 9-13 and 15-17 are from originals in the Victoria and Albert Museum, South Kensington
```

### Current body
```
{{IMG:EB1911 China - Temple Vase.jpg|TEMPLE VASE (c. 1200 B.C.)}}

{{IMG:EB1911 China - Wine Vase.jpg|WINE VASE (c. 1000 B.C.)}}

{{IMG:EB1911 China - Wine Vase (2).jpg|Fig. 11—WINE VASE (c. 600 B.C.)}}

{{IMG:EB1911 China - Inlaid Vessel.jpg|INLAID VESSEL (c. 500 B.C.)}}

{{IMG:EB1911 China - Wine Vessel.jpg|WINE VESSEL (c. 100 B.C.)}}

{{IMG:EB1911 China - Inlaid Vase.jpg|INLAID VASE (c. 200 A.D.). In possession of C.J. Holmes}}

{{IMG:EB1911 China - Vase.jpg|VASE (c. 1450 A.D.)}}

{{IMG:EB1911 China - Wine Vessel (2).jpg|WINE VESSEL (c. 1450 A.D.)}}

{{IMG:EB1911 China - Temple Vase (2).jpg|TEMPLE VASE (c. 1700 A.D.)}}

Figs. 9-13 and 15-17 are from originals in the Victoria and Albert Museum, South Kensington
```

---

## CLIMATE, PLATE I — vol 06

**Article ID:** 4194322  
**Signature:** `c_centered depth=0 wt=0 ht=0 toplegend`

### Source excerpt
```
[[File:EB1911 - Climate Plate 1.jpg|966px|center]]
{{c|ANNUAL DISTRIBUTION OF TEMPERATURE AND PRESSURE.}}
<br/>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **2** | **2** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Climate Plate 1.jpg|ANNUAL DISTRIBUTION OF TEMPERATURE AND PRESSURE}}
```

### Current body
```
{{IMG:EB1911 - Climate Plate 1.jpg|ANNUAL DISTRIBUTION OF TEMPERATURE AND PRESSURE}}
```

---

## CLIMATE, PLATE II — vol 06

**Article ID:** 4194323  
**Signature:** `center_template depth=0 wt=0 ht=0 toplegend`

### Source excerpt
```
[[File:EB1911 - Climate Plate 2.jpg|966px|center]]

{{center|SEASONAL DISTRIBUTION OF TEMPERATURE AND PRESSURE}}
<br/>
{{nop}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **2** | **2** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Climate Plate 2.jpg|SEASONAL DISTRIBUTION OF TEMPERATURE AND PRESSURE}}
```

### Current body
```
{{IMG:EB1911 - Climate Plate 2.jpg|SEASONAL DISTRIBUTION OF TEMPERATURE AND PRESSURE}}
```

---

## COCCIDIA, PLATE I — vol 06

**Article ID:** 4194436  
**Signature:** `html_table depth=0 wt=0 ht=multi`

### Source excerpt
```
<table style="margin:auto; width:500px">
<tr><td>[[File:EB1911 Coccidia, Fig. 1—Section through Rabbit's Liver.jpg]]</td></tr>
<tr><td {{ts|ac|sm92|lh13}}>{{sc|Fig. 1.}}—SECTION THROUGH RABBIT’S LIVER, INFECTED WITH<br/>''COCCIDIUM CUNICULI''. (AFTER THOMA.)</td></tr></table>


<table style="margin:auto; width:245px;">
<tr><td>[[File:EB1911 Coccidia, Fig. 2.—KLOSSIA HELICINA.jpg]]</td></tr>
<tr><td {{ts|ac|sm92|lh12}}>{{sc|Fig. 2.}}—''KLOSSIA HELICINA'', FROM KIDNEY OF HELIX HORTENSIS.</td></tr>
<tr><td {{ts|al|sm92|lh12|pl1|pr1}}>''a'', Portion of a section of the kidney showing normal epithelial cells containing concretions (''c''), and enlarged epithelial cells containing the parasite (''k'') in various stages; ''b'', cyst of the ''Klossia'' containing sporoblasts; ''c'', cyst with ripe spores, each enclosing four sporozoites and a patch of residual protoplasm. (From Wasielewski, after Balbiani.)
</table>


<table style="margin:auto; width:520px;">
<tr><td>[[File:EB1911 Coccidia, Fig. 4.—PHASES OF CARYOTROPHA MESNILII.jpg|508px]]</td></tr>
<tr><td {{ts|ac|sm92|lh12}}>{{sc|Fig. 3.}}—THE LIFE-CYCLE OF ''COCCIDIUM SCHUBERGI'', SCHAUD.<br />(PAR. ''LITHOBIUS FORFICATUS''). (FROM MINCHIN, AFTER SCHAUDINN.)</td></tr>
<tr><td {{ts|al|sm92|lh12|pl1|pr1}}>I.-IV represents the schizogony, commencing with infection of an epithelial cell by a sporozoite or merozoite. After stage IV the development may start again at stage I, as indicated by the arrows; or it may go on to the formation
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **10** | **10** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | 'a, Young schizont in a cluster of spermatogonia; the host-cell (represented granulated) and two of its neighbours are gr' | 'a, Young schizont in a cluster of spermatogonia; the host-cell (represented granulated) and two of its neighbours are gr' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Coccidia, Fig. 1—Section through Rabbit's Liver.jpg|SECTION THROUGH RABBIT’S LIVER, INFECTED WITH COCCIDIUM CUNICULI. (AFTER THOMA.)}}

{{IMG:EB1911 Coccidia, Fig. 2.—KLOSSIA HELICINA.jpg|KLOSSIA HELICINA, FROM KIDNEY OF HELIX HORTENSIS}}

{{IMG:EB1911 Coccidia, Fig. 4.—PHASES OF CARYOTROPHA MESNILII.jpg|THE LIFE-CYCLE OF COCCIDIUM SCHUBERGI, SCHAUD. (PAR. LITHOBIUS FORFICATUS). (FROM MINCHIN, AFTER SCHAUDINN.)}}

{{IMG:EB1911 Coccidia, Fig. 3.—LIFE-CYCLE OF COCCIDIUM SCHUBERGI.jpg|PHASES OF CARYOTROPHA MESNILII, SIEDL. (PAR. POLYMNIA NEBULOSA)}}

a, Young schizont in a cluster of spermatogonia; the host-cell (represented granulated) and two of its neighbours are greatly hypertrophied, with very large nuclei, and have fused into a single mass containing the parasite (represented clear, with a thick outline). The other spermatogonia are normal. b, Intracellular schizont divided up into schizontocytes (c), each schizontocyte giving rise to a cluster of merozoites arranged as a “corps en barillet”; spg, spermatogonia; h.c, host-cell; N, nucleus of host-cell or cells; n, nucleus of parasite; szc, schizontocyte; mz, merozoites; r.b, residual bodies of the schizontocytes. (From Minchin, after Siedlecki.)
```

### Current body
```
{{IMG:EB1911 Coccidia, Fig. 1—Section through Rabbit's Liver.jpg|SECTION THROUGH RABBIT’S LIVER, INFECTED WITH COCCIDIUM CUNICULI. (AFTER THOMA.)}}

{{IMG:EB1911 Coccidia, Fig. 2.—KLOSSIA HELICINA.jpg|KLOSSIA HELICINA, FROM KIDNEY OF HELIX HORTENSIS}}

{{IMG:EB1911 Coccidia, Fig. 4.—PHASES OF CARYOTROPHA MESNILII.jpg|THE LIFE-CYCLE OF COCCIDIUM SCHUBERGI, SCHAUD. (PAR. LITHOBIUS FORFICATUS). (FROM MINCHIN, AFTER SCHAUDINN.)}}

{{IMG:EB1911 Coccidia, Fig. 3.—LIFE-CYCLE OF COCCIDIUM SCHUBERGI.jpg|PHASES OF CARYOTROPHA MESNILII, SIEDL. (PAR. POLYMNIA NEBULOSA)}}

a, Young schizont in a cluster of spermatogonia; the host-cell (represented granulated) and two of its neighbours are greatly hypertrophied, with very large nuclei, and have fused into a single mass containing the parasite (represented clear, with a thick outline). The other spermatogonia are normal. b, Intracellular schizont divided up into schizontocytes (c), each schizontocyte giving rise to a cluster of merozoites arranged as a “corps en barillet”; spg, spermatogonia; h.c, host-cell; N, nucleus of host-cell or cells; n, nucleus of parasite; szc, schizontocyte; mz, merozoites; r.b, residual bodies of the schizontocytes. (From Minchin, after Siedlecki.)
```

---

## COCCIDIA, PLATE II — vol 06

**Article ID:** 4194437  
**Signature:** `html_table depth=0 wt=0 ht=multi`

### Source excerpt
```
<table align=center {{Ts|width:469px}}>
<tr><td {{Ts|ac}}>[[File:EB1911 Coccidia, Fig. 5.—SCHIZOGONY OF ADELEA OVATA.jpg]]</td></tr>
<tr><td {{ts|ac|sm90}}>{{sc|Fig. 5.}}—SCHIZOGONY OF ''ADELEA OVATA'', A. SCHN. (PAR. ''LITHOBIUS FORFICATUS'').</td></tr>
<tr><td {{ts|sm90}}>''a-c'', &#9792; generation; ''d-f'', &#9794; generation. ''a'', Full-grown &#9792; schizont (''megaschizont''), with a large nucleus (''n'') containing a conspicuous karyosome (''ky''). ''b'', Commencement of schizogony; the nucleus has divided up to form a number of daughter-nuclei (''d.n''). The karyosome of stage a has broken up into a great number of daughter-karyosomes, each of which forms at first the centre of one of the star-shaped daughter-nuclei; but in a short time the daughter-karyosomes become inconspicuous. ''c'', Completion of schizogony; the &#9792; schizont has broken up into a number of ''megamerozoites'' (&#9792; ''mz'') implanted on a small quantity of residual protoplasm (''r.p.''). Each &#9792; merozoite has a chromatic nucleus (''n'') without a karyosome. ''d'', Full-grown &#9794; schizont (''microschizont''), with nucleus (''n''), karyosome (''ky''), and a number of characteristic pigment-granules (''p.gr''). ''e'', Commencement of schizogony. The nucleus is dividing up into a number of daughter-nuclei (''d.n''), each with a conspicuous karyosome (''ky''). ''f'', Completion of schizogony. The numerous micro-merozoites (&#9794; ''mz'') have each a nucleus with a conspicuous karyosom
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **11** | **11** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | 'a, Oocyst with sporoblasts; b, oocyst with ripe spores; c, a spore highly magnified, showing the single sporozoite bent ' | 'a, Oocyst with sporoblasts; b, oocyst with ripe spores; c, a spore highly magnified, showing the single sporozoite bent ' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Coccidia, Fig. 5.—SCHIZOGONY OF ADELEA OVATA.jpg|SCHIZOGONY OF ADELEA OVATA, A. SCHN. (PAR. LITHOBIUS FORFICATUS)}}

{{IMG:EB1911 Coccidia, Fig. 6.—ASSOCIATION AND CONJUGATION IN ADELEA OVATA.jpg|ASSOCIATION AND CONJUGATION IN ADELEA OVATA}}

{{IMG:EB1911 Coccidia, Fig. 7.—SPORES OF VARIOUS COCCIDIAN GENERA.jpg|SPORES OF VARIOUS COCCIDIAN GENERA}}

{{IMG:EB1911 Coccidia, Fig. 8.—SPOROGONY AND SPORE-GERMINATION IN BARROUSSIA ORNATA.jpg|SPOROGONY AND SPORE-GERMINATION IN BARROUSSIA ORNATA, A. SCH., FROM THE GUT OF NEPA CINERA}}

{{LEGEND:a, Minchinia chitonis (E.R.L.), (par. (Chiton); b, Diaspora hydatidea, Léger (par. Polydesmus); c, Echinospora labbei, Léger (par. Lithobius mutabilis); d, Goussia motellae, Labbé; e, Diplospora (Hyaloklossia), lieberkuhni (Labbé), (par. Rana esculenta); f, Crystallospora crystalloides (Thél.), (par. Motella tricirrata). (From Minchin; b and c after Léger, the others after Labbé.)}LEGEND}

a, Oocyst with sporoblasts; b, oocyst with ripe spores; c, a spore highly magnified, showing the single sporozoite bent on itself; d, the spore has split along its outer coat or epispore, but the sporozoite is still enclosed in the endospore; e, the sporozoite, freed from the endospore, is emerging; f, the sporozoite has straightened itself out and is freed from its envelopes. (From Wasielewski, after A. Schneider.)
```

### Current body
```
{{IMG:EB1911 Coccidia, Fig. 5.—SCHIZOGONY OF ADELEA OVATA.jpg|SCHIZOGONY OF ADELEA OVATA, A. SCHN. (PAR. LITHOBIUS FORFICATUS)}}

{{IMG:EB1911 Coccidia, Fig. 6.—ASSOCIATION AND CONJUGATION IN ADELEA OVATA.jpg|ASSOCIATION AND CONJUGATION IN ADELEA OVATA}}

{{IMG:EB1911 Coccidia, Fig. 7.—SPORES OF VARIOUS COCCIDIAN GENERA.jpg|SPORES OF VARIOUS COCCIDIAN GENERA}}

{{IMG:EB1911 Coccidia, Fig. 8.—SPOROGONY AND SPORE-GERMINATION IN BARROUSSIA ORNATA.jpg|SPOROGONY AND SPORE-GERMINATION IN BARROUSSIA ORNATA, A. SCH., FROM THE GUT OF NEPA CINERA}}

{{LEGEND:a, Minchinia chitonis (E.R.L.), (par. (Chiton); b, Diaspora hydatidea, Léger (par. Polydesmus); c, Echinospora labbei, Léger (par. Lithobius mutabilis); d, Goussia motellae, Labbé; e, Diplospora (Hyaloklossia), lieberkuhni (Labbé), (par. Rana esculenta); f, Crystallospora crystalloides (Thél.), (par. Motella tricirrata). (From Minchin; b and c after Léger, the others after Labbé.)}LEGEND}

a, Oocyst with sporoblasts; b, oocyst with ripe spores; c, a spore highly magnified, showing the single sporozoite bent on itself; d, the spore has split along its outer coat or epispore, but the sporozoite is still enclosed in the endospore; e, the sporozoite, freed from the endospore, is emerging; f, the sporozoite has straightened itself out and is freed from its envelopes. (From Wasielewski, after A. Schneider.)
```

---

## COMET, PLATE I — vol 06

**Article ID:** 4194700  
**Signature:** `html_table depth=0 wt=0 ht=1`

### Source excerpt
```
<table {{Ts|ma|sm92|ac}}>
<tr><td>[[File:EB1911 - Comet Fig.1.—Comet 1892, I.jpg|650px]]</td></tr>
<tr><td>{{sc|Fig. 1.}}—COMET 1892, I. (SWIFT), 1892, APRIL 26.<br>
<p style="font-size:85%;">{{em|36}}By permission of Lick Observatory (E. E. Barnard)</p><br></td></tr>

<tr><td>[[File:EB1911 - Comet Fig. 2.—Comet C, 1908.jpg]]</td></tr>
<tr><td>{{sc|Fig. 2.}}—COMET C, 1908, NOV. 16d. 13h. 10m.<br>
<p style="font-size:85%;">{{em|36}}By permission of Yerkes Observatory (E. E. Barnard).</p></td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Comet Fig.1.—Comet 1892, I.jpg|COMET 1892, I. (SWIFT), 1892, APRIL 26. By permission of Lick Observatory (E. E. Barnard)}}

{{IMG:EB1911 - Comet Fig. 2.—Comet C, 1908.jpg|COMET C, 1908, NOV. 16d. 13h. 10m. By permission of Yerkes Observatory (E. E. Barnard)}}
```

### Current body
```
{{IMG:EB1911 - Comet Fig.1.—Comet 1892, I.jpg|COMET 1892, I. (SWIFT), 1892, APRIL 26. By permission of Lick Observatory (E. E. Barnard)}}

{{IMG:EB1911 - Comet Fig. 2.—Comet C, 1908.jpg|COMET C, 1908, NOV. 16d. 13h. 10m. By permission of Yerkes Observatory (E. E. Barnard)}}
```

---

## COMET, PLATE II — vol 06

**Article ID:** 4194701  
**Signature:** `html_table depth=0 wt=0 ht=1`

### Source excerpt
```
<table {{Ts|ma|sm92|ac}}>
<tr><td>[[File:EB1911 - Comet Fig. 3.—Halley’s Comet, 1910.jpg|600px]]</td></tr>
<tr><td>{{sc|Fig. 3.}}—HALLEY’S COMET, 1910, APRIL 27.<br>
<p style="font-size:85%;">{{em|34}}By permission of Helwân Observatory, Egypt.<br><br></p>
</td></tr>

<tr><td>[[File:EB1911 - Comet Fig. 4.—Halley’s Comet, 1910.jpg]]</td></tr>
<tr><td>{{sc|Fig. 4.}}—HALLEY’S COMET, 1910, MAY 4.<br>
<p style="font-size:85%;">{{em|37}}By permission of Yerkes Observatory (E. E. Barnard).</p></td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Comet Fig. 3.—Halley’s Comet, 1910.jpg|HALLEY’S COMET, 1910, APRIL 27. By permission of Helwân Observatory, Egypt}}

{{IMG:EB1911 - Comet Fig. 4.—Halley’s Comet, 1910.jpg|HALLEY’S COMET, 1910, MAY 4. By permission of Yerkes Observatory (E. E. Barnard)}}
```

### Current body
```
{{IMG:EB1911 - Comet Fig. 3.—Halley’s Comet, 1910.jpg|HALLEY’S COMET, 1910, APRIL 27. By permission of Helwân Observatory, Egypt}}

{{IMG:EB1911 - Comet Fig. 4.—Halley’s Comet, 1910.jpg|HALLEY’S COMET, 1910, MAY 4. By permission of Yerkes Observatory (E. E. Barnard)}}
```

---

## CONSTELLATION, PLATE I — vol 07

**Article ID:** 4194944  
**Signature:** `other depth=0 wt=0 ht=0`

### Source excerpt
```
<section begin="Constellation" />[[File:1911 Britannica-Constellation-1.jpg|center|900px|]]

<div class="center" style="width: auto; margin-left: auto; margin-right: auto; margin-top: 1em; margin-bottom: 2em;">CONSTELLATIONS OF THE NORTHERN HEMISPHERE.
</div>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 0 | 0 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **3** | **3** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | 'CONSTELLATIONS OF THE NORTHERN HEMISPHERE' | 'CONSTELLATIONS OF THE NORTHERN HEMISPHERE' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica-Constellation-1.jpg}}

CONSTELLATIONS OF THE NORTHERN HEMISPHERE
```

### Current body
```
{{IMG:1911 Britannica-Constellation-1.jpg}}

CONSTELLATIONS OF THE NORTHERN HEMISPHERE
```

---

## CONSTELLATION, PLATE II — vol 07

**Article ID:** 4194945  
**Signature:** `other depth=0 wt=0 ht=0`

### Source excerpt
```
<section begin="Constellation" />[[File:1911 Britannica-Constellation-2.jpg|center|900px|]]

<div class="center" style="width: auto; margin-left: auto; margin-right: auto; margin-top: 1em; margin-bottom: 2em;">CONSTELLATIONS OF THE SOUTHERN HEMISPHERE.
</div>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 0 | 0 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **3** | **3** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | 'CONSTELLATIONS OF THE SOUTHERN HEMISPHERE' | 'CONSTELLATIONS OF THE SOUTHERN HEMISPHERE' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica-Constellation-2.jpg}}

CONSTELLATIONS OF THE SOUTHERN HEMISPHERE
```

### Current body
```
{{IMG:1911 Britannica-Constellation-2.jpg}}

CONSTELLATIONS OF THE SOUTHERN HEMISPHERE
```

---

## COPE, PLATE I — vol 07

**Article ID:** 4195047  
**Signature:** `html_table depth=0 wt=0 ht=multi`

### Source excerpt
```
<table align=center>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 Cope Fig. 2.—THE SYON COPE.jpg]]</td></tr>
<tr><td {{Ts|sm90|ac|pl1|pr1}}>{{sc|Fig. 2.}}—THE SYON COPE. ({{sc|English, 13th Century.}})</td></tr></table>

<p {{Ts|sm90|pl2|pr2|lh13}}>The medallions with which it is embroidered contain representations of Christ on the Cross, Christ and St Mary Magdalene, Christ and Thomas, the death of the Virgin, the burial and coronation of the Virgin, St Michael and the twelve Apostles. Of the latter, four survive only in tiny fragments. The spaces between the four rows of medallions are filled with six-winged cherubim. The ground-work of the vestment is green silk embroidery, that of the medallions red. The figures are worked in silver and gold thread and coloured silks. The lower border and the orphrey with coats of arms do not belong to the original cope and are of somewhat later date. The cope belonged to the convent of Syon near Isleworth, was taken to Portugal at the Reformation, brought back early in the 19th century to England by exiled nuns and given by them to the Earl of Shrewsbury. In 1864 it was bought by the South Kensington Museum.</p>

<table align=center>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 Cope Fig. 3.—COPE OF BLUE SILK VELVET.jpg]]</td></tr>
<tr><td {{Ts|sm90|ac|pl1|pr1}}>{{sc|Fig. 3.}}—COPE OF BLUE SILK VELVET, WITH APPLIQUÉ WORK AND EMBROIDERY.</td></tr></table>

<p {{Ts|sm90|pl2|pr2|lh13}}>In the middle of the orphrey is a figure of Our Lord holding t
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | 'In the middle of the orphrey is a figure of Our Lord holding the orb in His left hand and with His right hand raised in ' | 'In the middle of the orphrey is a figure of Our Lord holding the orb in His left hand and with His right hand raised in ' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Cope Fig. 2.—THE SYON COPE.jpg|THE SYON COPE. (English, 13th Century. )}}

{{IMG:EB1911 Cope Fig. 3.—COPE OF BLUE SILK VELVET.jpg|COPE OF BLUE SILK VELVET, WITH APPLIQUÉ WORK AND EMBROIDERY}}

In the middle of the orphrey is a figure of Our Lord holding the orb in His left hand and with His right hand raised in benediction. To the right are figures of St Peter, St Bartholomew and St Ursula; and to the left, St Paul, St John the Evangelist and St Andrew. On the hood is a seated figure of the Virgin Mary holding the Infant Saviour. German: early 16th century. (In the Victoria and Albert Museum, No. 91. 1904.)
```

### Current body
```
{{IMG:EB1911 Cope Fig. 2.—THE SYON COPE.jpg|THE SYON COPE. (English, 13th Century. )}}

{{IMG:EB1911 Cope Fig. 3.—COPE OF BLUE SILK VELVET.jpg|COPE OF BLUE SILK VELVET, WITH APPLIQUÉ WORK AND EMBROIDERY}}

In the middle of the orphrey is a figure of Our Lord holding the orb in His left hand and with His right hand raised in benediction. To the right are figures of St Peter, St Bartholomew and St Ursula; and to the left, St Paul, St John the Evangelist and St Andrew. On the hood is a seated figure of the Virgin Mary holding the Infant Saviour. German: early 16th century. (In the Victoria and Albert Museum, No. 91. 1904.)
```

---

## COPE — vol 07

**Article ID:** 4195048  
**Signature:** `html_table depth=0 wt=0 ht=1 has_colspan`

### Source excerpt
```
<table {{Ts|ma|sm92|lh110}}>
<tr><td {{Ts|ar}} colspan=2>{{sc|PLATE II.}}</td></tr>
<tr><td {{Ts|ac|pt1}} colspan=2>[[File:EB1911 Cope Fig. 4.—COPE OF EMBROIDERED PURPLE SILK VELVET.jpg]]</td></tr>
<tr><td {{Ts|ac|pl1|pr1}} colspan=2>{{sc|Fig. 4.}}—COPE OF EMBROIDERED PURPLE SILK VELVET.<br>
In the middle is represented the Assumption of the Virgin, on the hood is a seated figure of the Almighty bearing<br>
three souls in a napkin. {{sc|English}}, about 1500. (In the Victoria and Albert Museum.)
</td></tr>
<tr><td {{Ts|ac|mc|ma|pt2}} colspan=2>[[File:EB1911 Cope Figs. 5. & 6.—COPE MORSE.jpg]]</td></tr>
<tr><td {{Ts|ac|pl1|pr1}}>{{sc|Fig. 5.}}—COPE MORSE ({{sc|German, 14th Century}}) IN THE
CATHEDRAL AT AIX-LA-CHAPELLE.<br>
<span {{Ts|sm90}}>(''From a photograph by Father Joseph Braun'', ''S. J.'')</span></td>
<td {{Ts|ac|pl1|pr1}}>{{sc|Fig. 6.}}—COPE MORSE ({{sc|German, Early 14th Century}}),
IN THE PARISH CHURCH AT ELTEN.<br>
<span {{Ts|sm90}}>(''From a photograph by Father Joseph Braun'', ''S. J.'')</span></td>
</tr></table>
{{nop}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **7** | **7** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'PLATE II' | 'PLATE II' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
PLATE II

{{IMG:EB1911 Cope Fig. 4.—COPE OF EMBROIDERED PURPLE SILK VELVET.jpg|COPE OF EMBROIDERED PURPLE SILK VELVET. In the middle is represented the Assumption of the Virgin, on the hood is a seated figure of the Almighty bearing three souls in a napkin. English , about 1500. (In the Victoria and Albert Museum.)}}

{{IMG:EB1911 Cope Figs. 5. & 6.—COPE MORSE.jpg|COPE MORSE (German, 14th Century ) IN THE CATHEDRAL AT AIX-LA-CHAPELLE. (From a photograph by Father Joseph Braun, S. J.)}}

{{LEGEND:COPE MORSE (German, Early 14th Century ), IN THE PARISH CHURCH AT ELTEN. (From a photograph by Father Joseph Braun, S. J.)}LEGEND}
```

### Current body
```
PLATE II

{{IMG:EB1911 Cope Fig. 4.—COPE OF EMBROIDERED PURPLE SILK VELVET.jpg|COPE OF EMBROIDERED PURPLE SILK VELVET. In the middle is represented the Assumption of the Virgin, on the hood is a seated figure of the Almighty bearing three souls in a napkin. English , about 1500. (In the Victoria and Albert Museum.)}}

{{IMG:EB1911 Cope Figs. 5. & 6.—COPE MORSE.jpg|COPE MORSE (German, 14th Century ) IN THE CATHEDRAL AT AIX-LA-CHAPELLE. (From a photograph by Father Joseph Braun, S. J.)}}

{{LEGEND:COPE MORSE (German, Early 14th Century ), IN THE PARISH CHURCH AT ELTEN. (From a photograph by Father Joseph Braun, S. J.)}LEGEND}
```

---

## COSTUME — vol 07

**Article ID:** 4195258  
**Signature:** `html_table depth=0 wt=0 ht=1`

### Source excerpt
```
<table align=center>
<tr><td {{Ts|ac|mc|ma|pt1|pr.5}}>[[File:EB1911 Costume Fig. 21.—GRAVE-STATUE.jpg]]</td>
 <td {{Ts|ac|mc|ma|pt1|pl.5}}>[[File:EB1911 Costume Fig. 22.—THE ORATOR.jpg]]</td></tr>
<tr {{Ts|lh11}}><td {{Ts|pl1|vtp|al|sm}}>''Photo, Walker.''</td>
 <td {{Ts|pl1|vtp|al|sm}}>''Photo, Alinari.''</td></tr>
<tr {{Ts|lh12}}><td {{Ts|sm92|ac}}>{{sc|Fig. 21.}}—GRAVE-STATUE.</td>
 <td {{Ts|sm92|ac}}>{{sc|Fig. 22.}}—THE ORATOR ({{sc|R. Arch. Mus., Florence}}).</td></tr>

<tr><td {{Ts|ac|mc|ma|pt15}}>[[File:EB1911 Costume Fig. 23.—PHILIP THE ARABIAN.jpg]]</td>
 <td {{Ts|ac|mc|ma|pt15}}>[[File:EB1911 Costume Fig. 24.—TITUS.jpg]]</td></tr>
<tr {{Ts|lh11}}><td {{Ts|pl1|vtp|al|sm}}>''Photo, Anderson.''</td>
 <td {{Ts|pl1|vtp|al|sm}}>''Photo, Moscioni.''</td></tr>
<tr {{Ts|lh12}}><td {{Ts|sm92|ac}}>{{sc|Fig. 23.}}—BUST OF PHILIP THE ARABIAN ({{sc|Vatican}}).</td>
 <td {{Ts|sm92|ac}}>{{sc|Fig. 24.}}—TITUS ({{sc|Vatican}}).</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Costume Fig. 21.—GRAVE-STATUE.jpg|GRAVE-STATUE (Photo, Walker)}}

{{IMG:EB1911 Costume Fig. 22.—THE ORATOR.jpg|THE ORATOR (R. Arch. Mus., Florence ) (Photo, Alinari)}}

{{IMG:EB1911 Costume Fig. 23.—PHILIP THE ARABIAN.jpg|BUST OF PHILIP THE ARABIAN (Vatican ) (Photo, Anderson)}}

{{IMG:EB1911 Costume Fig. 24.—TITUS.jpg|TITUS (Vatican ) (Photo, Moscioni)}}
```

### Current body
```
{{IMG:EB1911 Costume Fig. 21.—GRAVE-STATUE.jpg|GRAVE-STATUE (Photo, Walker)}}

{{IMG:EB1911 Costume Fig. 22.—THE ORATOR.jpg|THE ORATOR (R. Arch. Mus., Florence ) (Photo, Alinari)}}

{{IMG:EB1911 Costume Fig. 23.—PHILIP THE ARABIAN.jpg|BUST OF PHILIP THE ARABIAN (Vatican ) (Photo, Anderson)}}

{{IMG:EB1911 Costume Fig. 24.—TITUS.jpg|TITUS (Vatican ) (Photo, Moscioni)}}
```

---

## COTTON-SPINNING MACHINERY — vol 07

**Article ID:** 4195289  
**Signature:** `html_table depth=0 wt=0 ht=multi`

### Source excerpt
```
<table align=center>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 Cotton-spinning Machinery - Fig. 10. Blowing Room.jpg]]</td></tr>
<tr><td {{Ts|sm92|ac|pl1|pr1}}>{{sc|Fig. 10.}}—BLOWING ROOM.</td></tr></table>

<table align=center>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 Cotton-spinning Machinery - Fig. 11. Carding Room.jpg]]</td></tr>
<tr><td {{Ts|sm92|ac|pl1|pr1}}>{{sc|Fig. 11.}}—CARDING ROOM.<br />
<span {{Ts|sm}}>(''From Photographs taken in a Manchester Fine Cotton-spinning Mill, by R. Banks.'')</span></td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Cotton-spinning Machinery - Fig. 10. Blowing Room.jpg|BLOWING ROOM}}

{{IMG:EB1911 Cotton-spinning Machinery - Fig. 11. Carding Room.jpg|CARDING ROOM. (From Photographs taken in a Manchester Fine Cotton-spinning Mill, by R. Banks.)}}
```

### Current body
```
{{IMG:EB1911 Cotton-spinning Machinery - Fig. 10. Blowing Room.jpg|BLOWING ROOM}}

{{IMG:EB1911 Cotton-spinning Machinery - Fig. 11. Carding Room.jpg|CARDING ROOM. (From Photographs taken in a Manchester Fine Cotton-spinning Mill, by R. Banks.)}}
```

---

## COTTON-SPINNING MACHINERY, PLATE — vol 07

**Article ID:** 4195290  
**Signature:** `html_table depth=0 wt=0 ht=1`

### Source excerpt
```
<table align=center>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 Cotton-spinning Machinery - Fig. 12. Jack-Frame Room.jpg]]</td></tr>
<tr><td {{Ts|sm92|ac}}>{{sc|Fig. 12.}}—JACK-FRAME ROOM.</td></tr>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 Cotton-spinning Machinery - Fig. 13. Spinning-Room.jpg]]</td></tr>
<tr><td {{Ts|sm92|ac}}>{{sc|Fig. 13.}}—SPINNING-ROOM.<br />
<span {{Ts|sm85}}>(''From Photographs taken in a Manchester Fine Cotton-spinning Mill'', ''by R. Banks.'')</span></td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Cotton-spinning Machinery - Fig. 12. Jack-Frame Room.jpg|JACK-FRAME ROOM}}

{{IMG:EB1911 Cotton-spinning Machinery - Fig. 13. Spinning-Room.jpg|SPINNING-ROOM. (From Photographs taken in a Manchester Fine Cotton-spinning Mill, by R. Banks.)}}
```

### Current body
```
{{IMG:EB1911 Cotton-spinning Machinery - Fig. 12. Jack-Frame Room.jpg|JACK-FRAME ROOM}}

{{IMG:EB1911 Cotton-spinning Machinery - Fig. 13. Spinning-Room.jpg|SPINNING-ROOM. (From Photographs taken in a Manchester Fine Cotton-spinning Mill, by R. Banks.)}}
```

---

## CRAB — vol 07

**Article ID:** 4195407  
**Signature:** `illustration_html depth=0 wt=0 ht=multi has_illus`

### Source excerpt
```
<table summary="Illustration">
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 Crab - Fig. 3.—Gecarcinus ruricola (Violet Land Crab).jpg]]</td>
<td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 Crab - Fig. 4.—Portunus puber (Velvet Swimming Crab).jpg]]</td></tr>
<tr><td {{Ts|sm92|ac|pl1|pr1}}>{{sc|Fig. 3.}}—''Gecarcinus ruricola''
(Violet Land Crab).</td>
<td {{Ts|sm92|ac|pl1|pr1}}>{{sc|Fig. 4.}}—''Portunus puber''
(Velvet Swimming Crab).</td></tr></table>

<table summary="Illustration">
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 Crab - Fig. 6.—Eupagurus Bernhardus (Soldier Crab).jpg]]</td>
<td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 Crab - Fig. 5. Podophthalmus vigil (Sentinel Spinous Crab).jpg]]</td>
<td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 Crab - Fig. 7.—Pinnotheres pisum (Pea Crab).jpg]]</td></tr>
<tr><td {{Ts|sm92|ac|pl1|pr1}}>{{sc|Fig. 6.}}—''Eupagurus Bernhardus'' (Soldier Crab).</td>
<td {{Ts|sm92|ac|pl1|pr1}}>{{sc|Fig. 5.}} ''Podophthalmus vigil'' (Sentinel Spinous Crab).</td>
<td {{Ts|sm92|ac|pl1|pr1}}>{{sc|Fig. 7.}}—''Pinnotheres pisum'' (Pea Crab).</td></tr></table>

<table summary="Illustration">
<tr><td {{Ts|ac|mc|ma|pt1|pl2}}>[[File:EB1911 Crab - Fig. 8.—Corystes Cassivelaunus (Masked Crab).jpg]]</td>
<td {{Ts|ac|mc|ma|pt1|pl3}}>[[File:EB1911 Crab - Fig. 9.—Eupagurus angulatus (Hermit Crab).jpg]]</td></tr>
<tr><td {{Ts|sm92|ac|pl2|pr1}}>{{sc|Fig. 8.}}—''Corystes'' ''Cassivelaunus'' (Masked Crab).</td>
<td {{Ts|sm92|ac|pl4|pr1}}>{{sc|Fig. 9.}}—''Eupagurus angulatus'' (a Hermit Crab).</td><
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 7 | 7 |
| captioned       | 7 | 7 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **14** | **14** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Crab - Fig. 3.—Gecarcinus ruricola (Violet Land Crab).jpg|Gecarcinus ruricola (Violet Land Crab)}}

{{IMG:EB1911 Crab - Fig. 4.—Portunus puber (Velvet Swimming Crab).jpg|Portunus puber (Velvet Swimming Crab)}}

{{IMG:EB1911 Crab - Fig. 6.—Eupagurus Bernhardus (Soldier Crab).jpg|Eupagurus Bernhardus (Soldier Crab)}}

{{IMG:EB1911 Crab - Fig. 5. Podophthalmus vigil (Sentinel Spinous Crab).jpg|Podophthalmus vigil (Sentinel Spinous Crab)}}

{{IMG:EB1911 Crab - Fig. 7.—Pinnotheres pisum (Pea Crab).jpg|Pinnotheres pisum (Pea Crab)}}

{{IMG:EB1911 Crab - Fig. 8.—Corystes Cassivelaunus (Masked Crab).jpg|Corystes Cassivelaunus (Masked Crab)}}

{{IMG:EB1911 Crab - Fig. 9.—Eupagurus angulatus (Hermit Crab).jpg|Eupagurus angulatus (a Hermit Crab)}}
```

### Current body
```
{{IMG:EB1911 Crab - Fig. 3.—Gecarcinus ruricola (Violet Land Crab).jpg|Gecarcinus ruricola (Violet Land Crab)}}

{{IMG:EB1911 Crab - Fig. 4.—Portunus puber (Velvet Swimming Crab).jpg|Portunus puber (Velvet Swimming Crab)}}

{{IMG:EB1911 Crab - Fig. 6.—Eupagurus Bernhardus (Soldier Crab).jpg|Eupagurus Bernhardus (Soldier Crab)}}

{{IMG:EB1911 Crab - Fig. 5. Podophthalmus vigil (Sentinel Spinous Crab).jpg|Podophthalmus vigil (Sentinel Spinous Crab)}}

{{IMG:EB1911 Crab - Fig. 7.—Pinnotheres pisum (Pea Crab).jpg|Pinnotheres pisum (Pea Crab)}}

{{IMG:EB1911 Crab - Fig. 8.—Corystes Cassivelaunus (Masked Crab).jpg|Corystes Cassivelaunus (Masked Crab)}}

{{IMG:EB1911 Crab - Fig. 9.—Eupagurus angulatus (Hermit Crab).jpg|Eupagurus angulatus (a Hermit Crab)}}
```

---

## CRETE, PLATE I — vol 07

**Article ID:** 4195539  
**Signature:** `wikitable depth=2 wt=multi ht=0`

### Source excerpt
```
{|align="center" cellspacing="0" cellpadding="0"
|
{|cellspacing="0" cellpadding="0" border="1"
|[[Image:EB1911 Crete - Palace of Cnossus.jpg|700px]]
|}
|-
|align="center" width="702"|{{sc|Fig. 1.}}—PALACE OF CNOSSUS. GENERAL VIEW OF THE SITE FROM THE EAST.
|-
|&nbsp;
|-
|
{|cellspacing="0" cellpadding="0" border="1"
|[[Image:EB1911 Crete - Palace of Cnossus - Part of Grand Staircase and Hall of Colonnades.jpg|700px]]
|}
|-
|align="center" style="line-height:120%;"|{{sc|Fig. 2.}}—VIEW OF PART OF GRAND STAIRCASE AND HALL OF COLONNADES<br />(WOODEN COLUMNS RESTORED)&emsp;(CNOSSUS).<br />{{EB1911 fine print|(''By permission of Dr A. J. Evans.'')}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Crete - Palace of Cnossus.jpg|PALACE OF CNOSSUS. GENERAL VIEW OF THE SITE FROM THE EAST}}

{{IMG:EB1911 Crete - Palace of Cnossus - Part of Grand Staircase and Hall of Colonnades.jpg|VIEW OF PART OF GRAND STAIRCASE AND HALL OF COLONNADES (WOODEN COLUMNS RESTORED) (CNOSSUS). (By permission of Dr A. J. Evans.)}}
```

### Current body
```
{{IMG:EB1911 Crete - Palace of Cnossus.jpg|PALACE OF CNOSSUS. GENERAL VIEW OF THE SITE FROM THE EAST}}

{{IMG:EB1911 Crete - Palace of Cnossus - Part of Grand Staircase and Hall of Colonnades.jpg|VIEW OF PART OF GRAND STAIRCASE AND HALL OF COLONNADES (WOODEN COLUMNS RESTORED) (CNOSSUS). (By permission of Dr A. J. Evans.)}}
```

---

## CRETE, PLATE II — vol 07

**Article ID:** 4195540  
**Signature:** `wikitable depth=2 wt=multi ht=0 has_colspan`

### Source excerpt
```
{|align="center" cellspacing="0" cellpadding="0"
|colspan="3" align="center"|
{|cellspacing="0" cellpadding="0" border="1"
|[[Image:EB1911 Crete - Palace of Cnossus - Large Oil-Jars in East Magazines.jpg|700px]]
|}
|-
|colspan="3" align="center" width="702"|{{sc|Fig. 3.}}—LARGE OIL-JARS IN EAST MAGAZINES (CNOSSUS).
|-
|&nbsp;
|-
|valign="bottom" align="center"|
{|cellspacing="0" cellpadding="0" border="1"
|[[Image:EB1911 Crete - Palace of Cnossus - Gypsum Throne.jpg|335px]]
|}
|&emsp;
|valign="bottom" align="center"|
{|cellspacing="0" cellpadding="0" border="1"
|[[Image:EB1911 Crete - Palace of Cnossus - base of West Wall.jpg|333px]]
|}
|-
|valign="top" align="center" width="325" style="line-height:120%;"|{{sc|Fig. 4.}}—GYPSUM THRONE (FRESCO PAINTING VISIBLE ON WALL) (CNOSSUS).
|
|valign="top" align="center" width="350" style="line-height:120%;"|{{sc|Fig. 5.}}—BASE OF WEST WALL NEAR ROYAL ENTRANCE (CNOSSUS).
|-
|colspan="3" align="center"  style="line-height:140%;"|{{EB1911 fine print|(''By permission of Dr A. J. Evans.'')}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | '(By permission of Dr A. J. Evans.)' | '(By permission of Dr A. J. Evans.)' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Crete - Palace of Cnossus - Large Oil-Jars in East Magazines.jpg|LARGE OIL-JARS IN EAST MAGAZINES (CNOSSUS)}}

{{IMG:EB1911 Crete - Palace of Cnossus - Gypsum Throne.jpg|GYPSUM THRONE (FRESCO PAINTING VISIBLE ON WALL) (CNOSSUS)}}

{{IMG:EB1911 Crete - Palace of Cnossus - base of West Wall.jpg|BASE OF WEST WALL NEAR ROYAL ENTRANCE (CNOSSUS)}}

(By permission of Dr A. J. Evans.)
```

### Current body
```
{{IMG:EB1911 Crete - Palace of Cnossus - Large Oil-Jars in East Magazines.jpg|LARGE OIL-JARS IN EAST MAGAZINES (CNOSSUS)}}

{{IMG:EB1911 Crete - Palace of Cnossus - Gypsum Throne.jpg|GYPSUM THRONE (FRESCO PAINTING VISIBLE ON WALL) (CNOSSUS)}}

{{IMG:EB1911 Crete - Palace of Cnossus - base of West Wall.jpg|BASE OF WEST WALL NEAR ROYAL ENTRANCE (CNOSSUS)}}

(By permission of Dr A. J. Evans.)
```

---

## DALMATIC, PLATE I — vol 07

**Article ID:** 4195974  
**Signature:** `html_table depth=0 wt=0 ht=1`

### Source excerpt
```
<table style="clear: both;" align=center>
<tr><td {{Ts|ac|mc|ma}}>[[File:EB1911 Dalmatic - Fig. 2.—TUNIC OF LINEN.jpg]]</td></tr>
<tr><td {{Ts|sm92|ac|pl1|pr1}}>{{sc|Fig. 2.}}—TUNIC OF LINEN, WOVEN WITH BANDS OF PURPLE WOOL EMBROIDERED WITH WHITE FLAX.</td></tr>
<tr><td {{Ts|ac|sm|lh11}}>From the tombs at Akhmim. Egypto-Roman; 1st to 4th century. (In the Victoria and Albert Museum.)</td></tr>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 Dalmatic - Fig. 3.—BACK OF A DALMATIC.jpg]]</td></tr>
<tr><td {{Ts|sm92|ac|lh12}}>{{sc|Fig. 3.}}—BACK OF A DALMATIC OF STAMPED GREEN WOOLLEN VELVET: THE ORPHREYS AND APPARELS<br />ARE OF EMBROIDERED SILK VELVET.</td></tr>
<tr><td {{Ts|pl5|vtp|al|sm|lh10}}>The two figures on the cross-band or apparel represent St. Gregory the Great and St. Augustine. The shields of arms are for the
dukes of Jülich and Berg, counts of Ravensberg, and for the electors of Bavaria. Said to have come from the church of St. Severin,
Cologne. German (Cologne); second half of 15th century. (In the Victoria and Albert Museum.)</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 2 | 2 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Dalmatic - Fig. 2.—TUNIC OF LINEN.jpg|TUNIC OF LINEN, WOVEN WITH BANDS OF PURPLE WOOL EMBROIDERED WITH WHITE FLAX}}

{{IMG:EB1911 Dalmatic - Fig. 3.—BACK OF A DALMATIC.jpg|BACK OF A DALMATIC OF STAMPED GREEN WOOLLEN VELVET: THE ORPHREYS AND APPARELS ARE OF EMBROIDERED SILK VELVET}}

{{LEGEND:From the tombs at Akhmim. Egypto-Roman; 1st to 4th century. (In the Victoria and Albert Museum.)}LEGEND}

{{LEGEND:The two figures on the cross-band or apparel represent St. Gregory the Great and St. Augustine. The shields of arms are for the dukes of Jülich and Berg, counts of Ravensberg, and for the electors of Bavaria. Said to have come from the church of St. Severin, Cologne. German (Cologne); second half of 15th century. (In the Victoria and Albert Museum.)}LEGEND}
```

### Current body
```
{{IMG:EB1911 Dalmatic - Fig. 2.—TUNIC OF LINEN.jpg|TUNIC OF LINEN, WOVEN WITH BANDS OF PURPLE WOOL EMBROIDERED WITH WHITE FLAX}}

{{IMG:EB1911 Dalmatic - Fig. 3.—BACK OF A DALMATIC.jpg|BACK OF A DALMATIC OF STAMPED GREEN WOOLLEN VELVET: THE ORPHREYS AND APPARELS ARE OF EMBROIDERED SILK VELVET}}

{{LEGEND:From the tombs at Akhmim. Egypto-Roman; 1st to 4th century. (In the Victoria and Albert Museum.)}LEGEND}

{{LEGEND:The two figures on the cross-band or apparel represent St. Gregory the Great and St. Augustine. The shields of arms are for the dukes of Jülich and Berg, counts of Ravensberg, and for the electors of Bavaria. Said to have come from the church of St. Severin, Cologne. German (Cologne); second half of 15th century. (In the Victoria and Albert Museum.)}LEGEND}
```

---

## DALMATIC, PLATE II — vol 07

**Article ID:** 4195975  
**Signature:** `html_table depth=0 wt=0 ht=multi`

### Source excerpt
```
<table style="clear: both;" align=center>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 Dalmatic - Fig. 4.—DALMATIC OF WHITE SATIN.jpg]]</td></tr>
<tr><td {{Ts|sm92|ac|lh12}}>{{sc|Fig. 4.}}—DALMATIC OF WHITE SATIN EMRROIDERED WITH COLOURED SILKS AND SILVER-GILT AND SILVER THREAD.</td></tr>
<tr><td {{Ts|lh10|ac|sm}}>Spanish; early 17th century. (In the Victoria and Albert Museum.)</td></tr></table>

<table style="clear: both;" align=center>
<tr><td {{Ts|ac|mc|ma|pt1|pr1}}>[[File:EB1911 Dalmatic - Fig. 5.—GREEK SAKKOS.jpg]]</td>
<td {{Ts|ac|mc|ma|pt1|pl1}}>[[File:EB1911 Dalmatic - Fig. 6.—DALMATIC OF POPE PIUS V.jpg]]</td></tr>
<tr><td {{Ts|sm92|ac|lh12}}>{{sc|Fig. 5.}}—GREEK SAKKOS, OF RED SATIN EMBROIDERED<br />WITH SILVER-GILT AND SILVER THREAD WITH SILK.</td>
<td {{Ts|sm92|ac|vbm|lh12}}>{{sc|Fig. 6.}}—DALMATIC OF POPE PIUS V.</td></tr>
<tr><td {{Ts|pl.5|pr.5|vtp|al|sm|lh10}}>It has the names and arms of two archbishops.<br />18th
century. (In the Victoria and Albert Museum.)</td>
<td {{Ts|pl4||vtp|al|sm|lh10}}>An early example of the modern Roman type. Roman; 16th century.<br />Preserved at Santa Maria Maggiore, Rome. From a photograph taken by<br />Father J. Braun (in ''Die liturgische Gewandung''), by permission of B. Herder.</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 3 | 3 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **9** | **9** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Dalmatic - Fig. 4.—DALMATIC OF WHITE SATIN.jpg|DALMATIC OF WHITE SATIN EMRROIDERED WITH COLOURED SILKS AND SILVER-GILT AND SILVER THREAD}}

{{IMG:EB1911 Dalmatic - Fig. 5.—GREEK SAKKOS.jpg|GREEK SAKKOS, OF RED SATIN EMBROIDERED WITH SILVER-GILT AND SILVER THREAD WITH SILK}}

{{IMG:EB1911 Dalmatic - Fig. 6.—DALMATIC OF POPE PIUS V.jpg|DALMATIC OF POPE PIUS V}}

{{LEGEND:Spanish; early 17th century. (In the Victoria and Albert Museum.)}LEGEND}

{{LEGEND:It has the names and arms of two archbishops. 18th century. (In the Victoria and Albert Museum.)}LEGEND}

{{LEGEND:An early example of the modern Roman type. Roman; 16th century. Preserved at Santa Maria Maggiore, Rome. From a photograph taken by Father J. Braun (in Die liturgische Gewandung), by permission of B. Herder}LEGEND}
```

### Current body
```
{{IMG:EB1911 Dalmatic - Fig. 4.—DALMATIC OF WHITE SATIN.jpg|DALMATIC OF WHITE SATIN EMRROIDERED WITH COLOURED SILKS AND SILVER-GILT AND SILVER THREAD}}

{{IMG:EB1911 Dalmatic - Fig. 5.—GREEK SAKKOS.jpg|GREEK SAKKOS, OF RED SATIN EMBROIDERED WITH SILVER-GILT AND SILVER THREAD WITH SILK}}

{{IMG:EB1911 Dalmatic - Fig. 6.—DALMATIC OF POPE PIUS V.jpg|DALMATIC OF POPE PIUS V}}

{{LEGEND:Spanish; early 17th century. (In the Victoria and Albert Museum.)}LEGEND}

{{LEGEND:It has the names and arms of two archbishops. 18th century. (In the Victoria and Albert Museum.)}LEGEND}

{{LEGEND:An early example of the modern Roman type. Roman; 16th century. Preserved at Santa Maria Maggiore, Rome. From a photograph taken by Father J. Braun (in Die liturgische Gewandung), by permission of B. Herder}LEGEND}
```

---

## DIAMOND, PLATE I — vol 08

**Article ID:** 4243299  
**Signature:** `wikitable depth=1 wt=1 ht=0 has_colspan`

### Source excerpt
```
<section begin="Diamond" />
{|{{Ts|ma|lh12}}
|[[Image:Britannica Diamond 9.jpg|390px|left]]
{{center|{{sc|Fig.}} 9.—DE BEERS MINE, 1874.}}
|[[Image:Britannica Diamond 10.jpg|390px|right]]
{{center|{{sc|Fig.}} 10.—KIMBERLEY MINE, 1874.}}
|-
| colspan="2" | {{center|[[Image:Britannica Diamond 11.jpg|800px|]]<br>
{{sc|Fig.}} 11.—DE BEERS MINE, 1873.<br>{{Fs|92%|(From photographs by C. Evans.)}}}}
|-
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:Britannica Diamond 9.jpg|DE BEERS MINE, 1874}}

{{IMG:Britannica Diamond 10.jpg|KIMBERLEY MINE, 1874}}

{{IMG:Britannica Diamond 11.jpg|DE BEERS MINE, 1873. (From photographs by C. Evans.)}}
```

### Current body
```
{{IMG:Britannica Diamond 9.jpg|DE BEERS MINE, 1874}}

{{IMG:Britannica Diamond 10.jpg|KIMBERLEY MINE, 1874}}

{{IMG:Britannica Diamond 11.jpg|DE BEERS MINE, 1873. (From photographs by C. Evans.)}}
```

---

## DIAMOND, PLATE II — vol 08

**Article ID:** 4243300  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
<section begin="Diamond" />
{|{{Ts|ma|lh12}}
|{{center|[[Image:Britannica Diamond 12.jpg|800px]]<br>
{{sc|Fig. 12.}}—KIMBERLEY MINE, 1874}}
|-
| {{center|[[Image:Britannica Diamond 13.jpg|800px]]<br>
{{sc|Fig. 13.}}—KIMBERLEY MINE, 1902<br>
{{Fs|92%|(From Photographs by C. Evans.)}}}}
|-
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'center' | 'center' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
center

{{IMG:Britannica Diamond 12.jpg|KIMBERLEY MINE, 1874}}

{{IMG:Britannica Diamond 13.jpg|KIMBERLEY MINE, 1902 (From Photographs by C. Evans.)}}
```

### Current body
```
center

{{IMG:Britannica Diamond 12.jpg|KIMBERLEY MINE, 1874}}

{{IMG:Britannica Diamond 13.jpg|KIMBERLEY MINE, 1902 (From Photographs by C. Evans.)}}
```

---

## DOG, PLATE I — vol 08

**Article ID:** 4243601  
**Signature:** `wikitable depth=1 wt=multi ht=0 has_colspan`

### Source excerpt
```
<section begin="Dog" />
{| style="margin-left: auto; margin-right: auto; border-collapse: collapse; width: 850px;" summary="Illustration" 
| style="text-align: center; margin: auto; margin-left: auto; margin-right: auto; padding-top: 1.5em;" |[[Image:Britannica Dog 1.jpg|center|406px|]]
| style="text-align: center; margin: auto; margin-left: auto; margin-right: auto; padding-top: 1.5em;" |[[Image:Britannica Dog 2.jpg|center|402px|]]
|-
| style="font-size: 0.9em; text-align: center; padding-bottom: 1em; padding-left: 1em; padding-right: 1em;" |GREAT DANE.
| style="font-size: 0.9em; text-align: center; padding-bottom: 1em; padding-left: 1em; padding-right: 1em;" |SAINT BERNARD.
|}
{| style="margin-left: auto; margin-right: auto; border-collapse: collapse; width: 850px;" summary="Illustration" 
| style="text-align: center; margin: auto; margin-left: auto; margin-right: auto; padding-top: 1.5em;" |[[Image:Britannica Dog 3.jpg|center|256px|]]
| style="text-align: center; margin: auto; margin-left: auto; margin-right: auto; padding-top: 1.5em;" |[[Image:Britannica Dog 4.jpg|center|266px|]]
| style="text-align: center; margin: auto; margin-left: auto; margin-right: auto; padding-top: 1.5em;" |[[Image:Britannica Dog 5.jpg|center|250px|]]
|-
| style="font-size: 0.9em; text-align: center; padding-bottom: 1em; padding-left: 1em; padding-right: 1em;" |DALMATIAN.
| style="font-size: 0.9em; text-align: center; padding-bottom: 1em; padding-left: 1em; padding-right: 1em;" |MASTIFF.
| style="
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 12 | 12 |
| captioned       | 12 | 12 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **26** | **26** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | '(From Photos by Bowden Bros.) TYPICAL NON-SPORTING DOGS' | '(From Photos by Bowden Bros.) TYPICAL NON-SPORTING DOGS' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:Britannica Dog 1.jpg|GREAT DANE}}

{{IMG:Britannica Dog 2.jpg|SAINT BERNARD}}

{{IMG:Britannica Dog 3.jpg|DALMATIAN}}

{{IMG:Britannica Dog 4.jpg|MASTIFF}}

{{IMG:Britannica Dog 5.jpg|OLD ENGLISH SHEEP DOG}}

{{IMG:Britannica Dog 6.jpg|COLLIE}}

{{IMG:Britannica Dog 7.jpg|CHOW}}

{{IMG:Britannica Dog 8.jpg|NEWFOUNDLAND}}

{{IMG:Britannica Dog 9.jpg|POODLE}}

{{IMG:Britannica Dog 10.jpg|BULL DOG}}

{{IMG:Britannica Dog 11.jpg|FRENCH BULL DOG}}

{{IMG:Britannica Dog 12.jpg|From “Country Life in America.” BOSTON TERRIER}}

(From Photos by Bowden Bros.) TYPICAL NON-SPORTING DOGS
```

### Current body
```
{{IMG:Britannica Dog 1.jpg|GREAT DANE}}

{{IMG:Britannica Dog 2.jpg|SAINT BERNARD}}

{{IMG:Britannica Dog 3.jpg|DALMATIAN}}

{{IMG:Britannica Dog 4.jpg|MASTIFF}}

{{IMG:Britannica Dog 5.jpg|OLD ENGLISH SHEEP DOG}}

{{IMG:Britannica Dog 6.jpg|COLLIE}}

{{IMG:Britannica Dog 7.jpg|CHOW}}

{{IMG:Britannica Dog 8.jpg|NEWFOUNDLAND}}

{{IMG:Britannica Dog 9.jpg|POODLE}}

{{IMG:Britannica Dog 10.jpg|BULL DOG}}

{{IMG:Britannica Dog 11.jpg|FRENCH BULL DOG}}

{{IMG:Britannica Dog 12.jpg|From “Country Life in America.” BOSTON TERRIER}}

(From Photos by Bowden Bros.) TYPICAL NON-SPORTING DOGS
```

---

## DOG, PLATE II — vol 08

**Article ID:** 4243602  
**Signature:** `wikitable depth=1 wt=multi ht=0 has_colspan`

### Source excerpt
```
<section begin="Dog" />
{| style="margin-left: auto; margin-right: auto; border-collapse: collapse; width: 850px;" summary="Illustration" 
| style="text-align: center; margin: auto; margin-left: auto; margin-right: auto; padding-top: 1.5em;" |[[Image:Britannica Dog 13.jpg|center|395px|]]
| style="text-align: center; margin: auto; margin-left: auto; margin-right: auto; padding-top: 1.5em;" |[[Image:Britannica Dog 14.jpg|center|403px|]]
|-
| style="font-size: 0.9em; text-align: center; padding-bottom: 1em; padding-left: 1em; padding-right: 1em;" |ENGLISH SETTER.
| style="font-size: 0.9em; text-align: center; padding-bottom: 1em; padding-left: 1em; padding-right: 1em;" |POINTER.
|-
| style="text-align: center; margin: auto; margin-left: auto; margin-right: auto; padding-top: 1.5em;" |[[Image:Britannica Dog 15.jpg|center|402px|]]
| style="text-align: center; margin: auto; margin-left: auto; margin-right: auto; padding-top: 1.5em;" |[[Image:Britannica Dog 16.jpg|center|402px|]]
|-
| style="font-size: 0.9em; text-align: center; padding-bottom: 1em; padding-left: 1em; padding-right: 1em;" |IRISH SETTER.
| style="font-size: 0.9em; text-align: center; padding-bottom: 1em; padding-left: 1em; padding-right: 1em;" |LABRADOR RETRIEVER.
|-
| style="text-align: center; margin: auto; margin-left: auto; margin-right: auto; padding-top: 1.5em;" |[[Image:Britannica Dog 17.jpg|center|399px|]]
| style="text-align: center; margin: auto; margin-left: auto; margin-right: auto; padding-top: 1.5em;" |
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 10 | 10 |
| captioned       | 10 | 10 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **22** | **22** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | '(From Photos by Bowden Bros.) TYPICAL SPORTING DOGS' | '(From Photos by Bowden Bros.) TYPICAL SPORTING DOGS' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:Britannica Dog 13.jpg|ENGLISH SETTER}}

{{IMG:Britannica Dog 14.jpg|POINTER}}

{{IMG:Britannica Dog 15.jpg|IRISH SETTER}}

{{IMG:Britannica Dog 16.jpg|LABRADOR RETRIEVER}}

{{IMG:Britannica Dog 17.jpg|FLAT-COATED RETRIEVER}}

{{IMG:Britannica Dog 18.jpg|IRISH WOLF-HOUND}}

{{IMG:Britannica Dog 19.jpg|IRISH TERRIER}}

{{IMG:Britannica Dog 20.jpg|DACHSHUND}}

{{IMG:Britannica Dog 21.jpg|ROUGH-COATED FOX TERRIER}}

{{IMG:Britannica Dog 22.jpg|FIELD SPANIEL}}

(From Photos by Bowden Bros.) TYPICAL SPORTING DOGS
```

### Current body
```
{{IMG:Britannica Dog 13.jpg|ENGLISH SETTER}}

{{IMG:Britannica Dog 14.jpg|POINTER}}

{{IMG:Britannica Dog 15.jpg|IRISH SETTER}}

{{IMG:Britannica Dog 16.jpg|LABRADOR RETRIEVER}}

{{IMG:Britannica Dog 17.jpg|FLAT-COATED RETRIEVER}}

{{IMG:Britannica Dog 18.jpg|IRISH WOLF-HOUND}}

{{IMG:Britannica Dog 19.jpg|IRISH TERRIER}}

{{IMG:Britannica Dog 20.jpg|DACHSHUND}}

{{IMG:Britannica Dog 21.jpg|ROUGH-COATED FOX TERRIER}}

{{IMG:Britannica Dog 22.jpg|FIELD SPANIEL}}

(From Photos by Bowden Bros.) TYPICAL SPORTING DOGS
```

---

## DOG, PLATE III — vol 08

**Article ID:** 4243603  
**Signature:** `wikitable depth=1 wt=multi ht=0 has_colspan`

### Source excerpt
```
<section begin="Dog" />
{|{{Ts|ma|sm92|lh12|ac|width:850px}} 
|[[Image:Britannica Dog 23.jpg|center|406px|]]
|[[Image:Britannica Dog 24.jpg|center|405px|]]
|-
|BORZOI.
|GREYHOUND.
|-
| style="margin:auto; padding-top: 1.5em;" |[[Image:Britannica Dog 25.jpg|center|404px|]]
| style="margin:auto; padding-top: 1.5em;" |[[Image:Britannica Dog 26.jpg|center|286px|]]
|-
|DEERHOUND.
|BLOODHOUND.
|}
{|{{Ts|ma|sm92|lh12|ac|width:850px}} 
| style="margin:auto; padding-top: 1.5em;" |[[Image:Britannica Dog 27.jpg|center|265px|]]
| style="margin:auto; padding-top: 1.5em;" |[[Image:Britannica Dog 28.jpg|center|258px|]]
| style="margin:auto; padding-top: 1.5em;" |[[Image:Britannica Dog 29.jpg|center|270px|]]
|-
| style="padding-bottom:.5em;" |FOX HOUND.
| style="padding-bottom:.5em;" |HARRIER.
| style="padding-bottom:.5em;" |OTTER HOUND.
|}
{|{{Ts|ma|sm92|lh12|ac|width:850px}} 
| style="margin:auto; padding-top: 1.5em;" |[[Image:Britannica Dog 30.jpg|center|167px|]]
| style="margin:auto; padding-top: 1.5em;" |[[Image:Britannica Dog 31.jpg|center|202px|]]
| style="margin:auto; padding-top: 1.5em;" |[[Image:Britannica Dog 32.jpg|center|188px|]]
| style="margin:auto; padding-top: 1.5em;" |[[Image:Britannica Dog 33.jpg|center|197px|]]
|-
| style="padding-bottom: 1em;" |AUSTRALIAN TERRIER.
| style="padding-bottom: 1em;" |SKYE TERRIER.
| style="padding-bottom: 1em;" |SCOTCH TERRIER.
| style="padding-bottom: 1em;" |BEDLINGTON TERRIER.
|-
| style="padding-bottom: 1em; padding-left: 1em; padding-righ
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 11 | 11 |
| captioned       | 11 | 11 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **24** | **24** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | '(From Photos by Bowden Bros.)TYPICAL SPORTING DOGS' | '(From Photos by Bowden Bros.)TYPICAL SPORTING DOGS' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:Britannica Dog 23.jpg|BORZOI}}

{{IMG:Britannica Dog 24.jpg|GREYHOUND}}

{{IMG:Britannica Dog 25.jpg|DEERHOUND}}

{{IMG:Britannica Dog 26.jpg|BLOODHOUND}}

{{IMG:Britannica Dog 27.jpg|FOX HOUND}}

{{IMG:Britannica Dog 28.jpg|HARRIER}}

{{IMG:Britannica Dog 29.jpg|OTTER HOUND}}

{{IMG:Britannica Dog 30.jpg|AUSTRALIAN TERRIER}}

{{IMG:Britannica Dog 31.jpg|SKYE TERRIER}}

{{IMG:Britannica Dog 32.jpg|SCOTCH TERRIER}}

{{IMG:Britannica Dog 33.jpg|BEDLINGTON TERRIER}}

(From Photos by Bowden Bros.)TYPICAL SPORTING DOGS
```

### Current body
```
{{IMG:Britannica Dog 23.jpg|BORZOI}}

{{IMG:Britannica Dog 24.jpg|GREYHOUND}}

{{IMG:Britannica Dog 25.jpg|DEERHOUND}}

{{IMG:Britannica Dog 26.jpg|BLOODHOUND}}

{{IMG:Britannica Dog 27.jpg|FOX HOUND}}

{{IMG:Britannica Dog 28.jpg|HARRIER}}

{{IMG:Britannica Dog 29.jpg|OTTER HOUND}}

{{IMG:Britannica Dog 30.jpg|AUSTRALIAN TERRIER}}

{{IMG:Britannica Dog 31.jpg|SKYE TERRIER}}

{{IMG:Britannica Dog 32.jpg|SCOTCH TERRIER}}

{{IMG:Britannica Dog 33.jpg|BEDLINGTON TERRIER}}

(From Photos by Bowden Bros.)TYPICAL SPORTING DOGS
```

---

## DOG, PLATE IV — vol 08

**Article ID:** 4243604  
**Signature:** `wikitable depth=1 wt=multi ht=0 has_colspan`

### Source excerpt
```
<section begin="Dog" />
{|{{Ts|ma|sm92|lh12|ac|width:850px}} 
| style="margin: auto; padding-top: 1.5em;" |[[Image:Britannica Dog 34.jpg|center|302px|]]
| style="margin: auto; padding-top: 1.5em;" |[[Image:Britannica Dog 35.jpg|center|196px|]]
| style="margin: auto; padding-top: 1.5em;" |[[Image:Britannica Dog 36.jpg|center|260px|]]
|-
| style="padding-bottom: 1em;" |{{smaller|''Photo, Bowden Bros.''}}<br>POMERANIAN.
| style="padding-bottom: 1em;" |{{smaller|''Photo, Thos. Fall.''}}<br>ITALIAN GREYHOUND.
| style="padding-bottom: 1em;" |{{smaller|''Photo, Bowden Bros.''}}<br>TOY BULL TERRIER.
|}
{|{{Ts|ma|sm92|lh12|ac|width:850px}} 
| style="margin: auto; padding-top: 1.5em;" |[[Image:Britannica Dog 37.jpg|center|218px|]]
| style="margin: auto; padding-top: 1.5em;" |[[Image:Britannica Dog 38.jpg|center|208px|]]
| style="margin: auto; padding-top: 1.5em;" |[[Image:Britannica Dog 39.jpg|center|114px|]]
| style="margin: auto; padding-top: 1.5em;" |[[Image:Britannica Dog 40.jpg|center|197px|]]
|-
| style="padding-bottom: 1em;" |{{smaller|''Photo, Bowden Bros.''}}<br>TOY SPANIEL.
| style="padding-bottom: 1em;" |{{smaller|''Photo, Walker.''}}<br>BLENHEIM.
| style="padding-bottom: 1em;" |{{smaller|''Photo, Thos. Fall.''}}<br>PAPILLON.
| style="padding-bottom: 1em;" |{{smaller|''Photo, Bowden Bros.''}}<br>SCHIPPERKE.
|}
{|{{Ts|ma|sm92|lh12|ac|width:850px}} 
| style="margin: auto; padding-top: 1.5em;" |[[Image:Britannica Dog 41.jpg|center|310px|]]
| style="margin: auto; padding-top: 1.
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 14 | 14 |
| captioned       | 14 | 14 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **30** | **30** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | 'TYPICAL TOY DOGS' | 'TYPICAL TOY DOGS' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:Britannica Dog 34.jpg|Photo, Bowden Bros. POMERANIAN}}

{{IMG:Britannica Dog 35.jpg|Photo, Thos. Fall. ITALIAN GREYHOUND}}

{{IMG:Britannica Dog 36.jpg|Photo, Bowden Bros. TOY BULL TERRIER}}

{{IMG:Britannica Dog 37.jpg|Photo, Bowden Bros. TOY SPANIEL}}

{{IMG:Britannica Dog 38.jpg|Photo, Walker. BLENHEIM}}

{{IMG:Britannica Dog 39.jpg|Photo, Thos. Fall. PAPILLON}}

{{IMG:Britannica Dog 40.jpg|Photo, Bowden Bros. SCHIPPERKE}}

{{IMG:Britannica Dog 41.jpg|Photo, Bowden Bros. MALTESE}}

{{IMG:Britannica Dog 42.jpg|Photo, Thos. Fall. TOY BLACK AND TAN}}

{{IMG:Britannica Dog 43.jpg|Photo, Bowden Bros. YORKSHIRE TERRIER}}

{{IMG:Britannica Dog 44.jpg|Photo, Bowden Bros. PUG}}

{{IMG:Britannica Dog 45.jpg|Photo, Bowden Bros. GRIFFON}}

{{IMG:Britannica Dog 46.jpg|Photo, Bowden Bros. JAPANESE}}

{{IMG:Britannica Dog 47.jpg|Photo, Bowden Bros. PEKINGESE}}

TYPICAL TOY DOGS
```

### Current body
```
{{IMG:Britannica Dog 34.jpg|Photo, Bowden Bros. POMERANIAN}}

{{IMG:Britannica Dog 35.jpg|Photo, Thos. Fall. ITALIAN GREYHOUND}}

{{IMG:Britannica Dog 36.jpg|Photo, Bowden Bros. TOY BULL TERRIER}}

{{IMG:Britannica Dog 37.jpg|Photo, Bowden Bros. TOY SPANIEL}}

{{IMG:Britannica Dog 38.jpg|Photo, Walker. BLENHEIM}}

{{IMG:Britannica Dog 39.jpg|Photo, Thos. Fall. PAPILLON}}

{{IMG:Britannica Dog 40.jpg|Photo, Bowden Bros. SCHIPPERKE}}

{{IMG:Britannica Dog 41.jpg|Photo, Bowden Bros. MALTESE}}

{{IMG:Britannica Dog 42.jpg|Photo, Thos. Fall. TOY BLACK AND TAN}}

{{IMG:Britannica Dog 43.jpg|Photo, Bowden Bros. YORKSHIRE TERRIER}}

{{IMG:Britannica Dog 44.jpg|Photo, Bowden Bros. PUG}}

{{IMG:Britannica Dog 45.jpg|Photo, Bowden Bros. GRIFFON}}

{{IMG:Britannica Dog 46.jpg|Photo, Bowden Bros. JAPANESE}}

{{IMG:Britannica Dog 47.jpg|Photo, Bowden Bros. PEKINGESE}}

TYPICAL TOY DOGS
```

---

## DOVE, PLATE I — vol 08

**Article ID:** 4243762  
**Signature:** `wikitable depth=1 wt=1 ht=0 has_colspan`

### Source excerpt
```
<section begin="Dove (bird)" />
{|{{Ts|ma|sm92|lh12|ac}}
| {{Ts|pt1|pr1}} |[[Image:Britannica Dove 1.jpg|center|395px|]]
| {{Ts|pt1|pl1}} |[[Image:Britannica Dove 2.jpg|center|405px|]]
|-
| style="padding-bottom: 1em;" |ROCK DOVE OR BLUE ROCK PIGEON, ''Columba livia''.
| style="padding-bottom: 1em;" |STOCK DOVE, ''Columba oenas''.
|-
|{{Ts|pt1|pr1}} |[[Image:Britannica Dove 3.jpg|center|397px|]]
|{{Ts|pt1}} |[[Image:Britannica Dove 4.jpg|right|400px|]]
|-
| style="padding-bottom: 1em;" |AMERICAN WILD CARRIER PIGEON,<br> ''Ectopistes migratorius''.
| style="padding-bottom: 1em;" |RING DOVE OR WOOD PIGEON,<br> ''Columba palumbus''.
|-
| style="padding-bottom: 1.5em;" colspan="2" |(After the coloured drawings by Mme. Knip (Pauline de Courcelles), painter to the Empress Marie Louise, in ''Les Pigeons''.<br>Text by C. J. Themminck, Paris, 1811.) 
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **10** | **10** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | '(After the coloured drawings by Mme. Knip (Pauline de Courcelles), painter to the Empress Marie Louise, in Les Pigeons. ' | '(After the coloured drawings by Mme. Knip (Pauline de Courcelles), painter to the Empress Marie Louise, in Les Pigeons. ' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:Britannica Dove 1.jpg|ROCK DOVE OR BLUE ROCK PIGEON, Columba livia}}

{{IMG:Britannica Dove 2.jpg|STOCK DOVE, Columba oenas}}

{{IMG:Britannica Dove 3.jpg|AMERICAN WILD CARRIER PIGEON, Ectopistes migratorius}}

{{IMG:Britannica Dove 4.jpg|RING DOVE OR WOOD PIGEON, Columba palumbus}}

(After the coloured drawings by Mme. Knip (Pauline de Courcelles), painter to the Empress Marie Louise, in Les Pigeons. Text by C. J. Themminck, Paris, 1811.)
```

### Current body
```
{{IMG:Britannica Dove 1.jpg|ROCK DOVE OR BLUE ROCK PIGEON, Columba livia}}

{{IMG:Britannica Dove 2.jpg|STOCK DOVE, Columba oenas}}

{{IMG:Britannica Dove 3.jpg|AMERICAN WILD CARRIER PIGEON, Ectopistes migratorius}}

{{IMG:Britannica Dove 4.jpg|RING DOVE OR WOOD PIGEON, Columba palumbus}}

(After the coloured drawings by Mme. Knip (Pauline de Courcelles), painter to the Empress Marie Louise, in Les Pigeons. Text by C. J. Themminck, Paris, 1811.)
```

---

## DOVE, PLATE II — vol 08

**Article ID:** 4243763  
**Signature:** `wikitable depth=1 wt=1 ht=0 has_colspan`

### Source excerpt
```
<section begin="Dove (bird)" />
{|{{Ts|ma|sm92|lh12|ac}}
| {{Ts|pr1}} |[[Image:Britannica Dove 5.jpg|center|400px|]]
| {{Ts|pl1}} |[[Image:Britannica Dove 6.jpg|center|400px|]]<br>NICOBAR PIGEON, ''Caloenas nicobarica''.<br> (After Mme. Knip, as above.)
|-
|CROWNED PIGEON, ''Goura coronata''<br> (After Mme. Knip, as above.)
| 
|-
| {{Ts|vbm|pr1}} |[[Image:Britannica Dove 7.jpg|center|400px|]]
| {{Ts|pl1}} |[[Image:Britannica Dove 8.jpg|center|400px|]]
|-
| {{Ts|pb1}} colspan=2 |Photographs of two typical pedigree Homing or Racing Pigeons, colours black and blue chequer, bred and shown by<br>Frederick Romer, Esq., prize-winners in races from France to England.
|-
| style="line-height:100%; text-align: right; vertical-align: top; font-size: 80%;" colspan="2" |By permission of the proprietors of the ''Racing Pigeon''.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **9** | **9** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | 'By permission of the proprietors of the Racing Pigeon' | 'By permission of the proprietors of the Racing Pigeon' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:Britannica Dove 5.jpg|CROWNED PIGEON, Goura coronata (After Mme. Knip, as above.)}}

{{IMG:Britannica Dove 6.jpg|Photographs of two typical pedigree Homing or Racing Pigeons, colours black and blue chequer, bred and shown by Frederick Romer, Esq., prize-winners in races from France to England}}

{{IMG:Britannica Dove 7.jpg|By permission of the proprietors of the Racing Pigeon}}

{{IMG:Britannica Dove 8.jpg}}

By permission of the proprietors of the Racing Pigeon
```

### Current body
```
{{IMG:Britannica Dove 5.jpg|CROWNED PIGEON, Goura coronata (After Mme. Knip, as above.)}}

{{IMG:Britannica Dove 6.jpg|Photographs of two typical pedigree Homing or Racing Pigeons, colours black and blue chequer, bred and shown by Frederick Romer, Esq., prize-winners in races from France to England}}

{{IMG:Britannica Dove 7.jpg|By permission of the proprietors of the Racing Pigeon}}

{{IMG:Britannica Dove 8.jpg}}

By permission of the proprietors of the Racing Pigeon
```

---

## DREDGING, PLATE I — vol 08

**Article ID:** 4243841  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
<section begin="Dredge" />
{|{{Ts|ma|sm92|lh12|ac}} 
| style="margin: auto; margin-left: auto; margin-right: auto; padding-top: .5em;" |[[Image:Britannica Dredge and Dredging 3.jpg|center|399px|]]||{{em|2}}
| style="margin: auto; margin-left: auto; margin-right: auto; padding-top: .5em;" |[[Image:Britannica Dredge and Dredging 4.jpg|center|400px|]]
|-
| style="padding-bottom: 1em; padding-left: 1em; padding-right: 1em;" |{{sc|Fig. 3.}}—Barge-loading dredger, “St Austell,” constructed for<br>the British Government by Wm. Simons & Co.|| 
|style="padding-bottom: 1em; padding-left: 1em; padding-right: 1em;" |{{sc|Fig. 4.}}—Stern-well hopper-dredger “La Puissante,” by Wm.<br>Simons & Co. Length 275 ft., breadth 47 ft., depth 19 ft.
|-
| style="margin: auto; margin-left: auto; margin-right: auto; padding-top: 1em;" |[[Image:Britannica Dredge and Dredging 5.jpg|center|402px|]]|| 
| style="margin: auto; margin-left: auto; margin-right: auto; padding-top: 1em;" |[[Image:Britannica Dredge and Dredging 6.jpg|center|403px|]]
|-
|style="padding-bottom: 1em; padding-left: 1em; padding-right: 1em;" |{{sc|Fig. 5.}}—Dredger constructed for the Lake Copais Co.<br>by Hunter & English.|| 
| style="padding-bottom: 1em; padding-left: 1em; padding-right: 1em;" |{{sc|Fig. 6.}}—Light-draught dredger, with delivery apparatus<br>working round an arc of 210°, by Hunter & English.
|-
| style="margin: auto; margin-left: auto; margin-right: auto; padding-top: 1em;" |[[Image:Britannica Dredge and Dredging 7
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 8 | 8 |
| captioned       | 8 | 8 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **16** | **16** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:Britannica Dredge and Dredging 3.jpg|Barge-loading dredger, “St Austell,” constructed for the British Government by Wm. Simons & Co}}

{{IMG:Britannica Dredge and Dredging 4.jpg|Stern-well hopper-dredger “La Puissante,” by Wm. Simons & Co. Length 275 ft., breadth 47 ft., depth 19 ft}}

{{IMG:Britannica Dredge and Dredging 5.jpg|Dredger constructed for the Lake Copais Co. by Hunter & English}}

{{IMG:Britannica Dredge and Dredging 6.jpg|Light-draught dredger, with delivery apparatus working round an arc of 210°, by Hunter & English}}

{{IMG:Britannica Dredge and Dredging 7.jpg|Twin-screw sand-pump dredger, “Kate,” built for the East London Harbour Board by Wm. Simons & Co}}

{{IMG:Britannica Dredge and Dredging 8.jpg|Twin-screw hopper-dredger, “Percy Sanderson,” built for the European Danube Commission by Wm. Simons & Co}}

{{IMG:Britannica Dredge and Dredging 9.jpg|Twin-screw grab-dredger, “Miles K. Burton,” built for the Mersey Docks and Harbour Board by Wm. Simons & Co}}

{{IMG:Britannica Dredge and Dredging 10.jpg|Hopper-dredger, “David Dale,” with buckets of 54 cub. ft. capacity (see fig. 11) built for the North Eastern Railway Company by Lobnitz & Co}}
```

### Current body
```
{{IMG:Britannica Dredge and Dredging 3.jpg|Barge-loading dredger, “St Austell,” constructed for the British Government by Wm. Simons & Co}}

{{IMG:Britannica Dredge and Dredging 4.jpg|Stern-well hopper-dredger “La Puissante,” by Wm. Simons & Co. Length 275 ft., breadth 47 ft., depth 19 ft}}

{{IMG:Britannica Dredge and Dredging 5.jpg|Dredger constructed for the Lake Copais Co. by Hunter & English}}

{{IMG:Britannica Dredge and Dredging 6.jpg|Light-draught dredger, with delivery apparatus working round an arc of 210°, by Hunter & English}}

{{IMG:Britannica Dredge and Dredging 7.jpg|Twin-screw sand-pump dredger, “Kate,” built for the East London Harbour Board by Wm. Simons & Co}}

{{IMG:Britannica Dredge and Dredging 8.jpg|Twin-screw hopper-dredger, “Percy Sanderson,” built for the European Danube Commission by Wm. Simons & Co}}

{{IMG:Britannica Dredge and Dredging 9.jpg|Twin-screw grab-dredger, “Miles K. Burton,” built for the Mersey Docks and Harbour Board by Wm. Simons & Co}}

{{IMG:Britannica Dredge and Dredging 10.jpg|Hopper-dredger, “David Dale,” with buckets of 54 cub. ft. capacity (see fig. 11) built for the North Eastern Railway Company by Lobnitz & Co}}
```

---

## DREDGING, PLATE II — vol 08

**Article ID:** 4243842  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
<section begin="Dredge" />
{| style="margin-left: auto; margin-right: auto; border-collapse: collapse;" summary="Illustration" 
| style="text-align: text-align: center;; margin: auto; margin-left: auto; margin-right: auto; padding-top: 1.5em;" |[[Image:Britannica Dredge and Dredging 11.jpg|center|850px|]]
|-
| style="font-size: 0.9em; text-align: center; padding-bottom: 1em; padding-left: 1em; padding-right: 1em;" |{{sc|Fig. 11.}}—BUCKETS OF 5 AND 54 CUBIC FEET CAPACITY COMPARED.<br /> The latter, the largest ever made, were for the hopper-dredger “David Dale” (Plate I. fig. 10), built by Lobnitz & Co.
|-
| style="text-align: text-align: center;; margin: auto; margin-left: auto; margin-right: auto; padding-top: 1.5em;" |[[Image:Britannica Dredge and Dredging 12.jpg|center|850px|]]
|-
| style="font-size: 0.9em; text-align: center; padding-bottom: 1em; padding-left: 1em; padding-right: 1em;" |{{sc|Fig. 12.}}—MODEL OF ROCK-CUTTING DREDGER, “DEROCHEUSE.”<br /> Built for special work on the Suez Canal by Lobnitz & Co. Length 180 ft., breadth 40 ft., depth 12 ft.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:Britannica Dredge and Dredging 11.jpg|BUCKETS OF 5 AND 54 CUBIC FEET CAPACITY COMPARED. The latter, the largest ever made, were for the hopper-dredger “David Dale” (Plate I. fig. 10), built by Lobnitz & Co}}

{{IMG:Britannica Dredge and Dredging 12.jpg|MODEL OF ROCK-CUTTING DREDGER, “DEROCHEUSE.” Built for special work on the Suez Canal by Lobnitz & Co. Length 180 ft., breadth 40 ft., depth 12 ft}}
```

### Current body
```
{{IMG:Britannica Dredge and Dredging 11.jpg|BUCKETS OF 5 AND 54 CUBIC FEET CAPACITY COMPARED. The latter, the largest ever made, were for the hopper-dredger “David Dale” (Plate I. fig. 10), built by Lobnitz & Co}}

{{IMG:Britannica Dredge and Dredging 12.jpg|MODEL OF ROCK-CUTTING DREDGER, “DEROCHEUSE.” Built for special work on the Suez Canal by Lobnitz & Co. Length 180 ft., breadth 40 ft., depth 12 ft}}
```

---

## DRINKING VESSELS, PLATE I — vol 08

**Article ID:** 4243859  
**Signature:** `wikitable depth=1 wt=multi ht=0`

### Source excerpt
```
<section begin="Drinking Vessels" />
{| style="margin-left: auto; margin-right: auto; border-collapse: collapse; width: 900px;" summary="Illustration" 
| style="text-align: text-align: center;; margin: auto; margin-left: auto; margin-right: auto; padding-top: 1.5em;" |[[Image:Britannica Drinking Vessels 1.jpg|center|291px|]]
| style="text-align: text-align: center;; margin: auto; margin-left: auto; margin-right: auto; padding-top: 1.5em;" |[[Image:Britannica Drinking Vessels 2.jpg|center|291px|]]
| style="text-align: text-align: center;; margin: auto; margin-left: auto; margin-right: auto; padding-top: 1.5em;" |[[Image:Britannica Drinking Vessels 3.jpg|center|271px|]]
|-
| style="font-size: 0.9em; text-align: center; padding-bottom: 1em; padding-left: 1em; padding-right: 1em;" |{{sc|Fig. 1.}}—ROMAN GLASS CUP. With representation of a chariot race. Found at Colchester.
| style="font-size: 0.9em; text-align: center; padding-bottom: 1em; padding-left: 1em; padding-right: 1em;" |{{sc|Fig. 2.}}—TEUTONIC GLASS CUP. From a grave at Selzen, Rhenish Hesse.
| style="font-size: 0.9em; text-align: center; padding-bottom: 1em; padding-left: 1em; padding-right: 1em;" |{{sc|Fig. 3.}}—SAXON GLASS “TUMBLER.”
|}
{| style="margin-left: auto; margin-right: auto; border-collapse: collapse; width: 900px;" summary="Illustration" 
| style="text-align: text-align: center;; margin: auto; margin-left: auto; margin-right: auto; padding-top: 1.5em;" |[[Image:Britannica Drinking Vessels 4.jpg|center|411px
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 8 | 8 |
| captioned       | 8 | 8 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **16** | **16** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:Britannica Drinking Vessels 1.jpg|ROMAN GLASS CUP. With representation of a chariot race. Found at Colchester}}

{{IMG:Britannica Drinking Vessels 2.jpg|TEUTONIC GLASS CUP. From a grave at Selzen, Rhenish Hesse}}

{{IMG:Britannica Drinking Vessels 3.jpg|SAXON GLASS “TUMBLER.”}}

{{IMG:Britannica Drinking Vessels 4.jpg|FRANKISH GLASS DRINKING HORN. Bingerbrück}}

{{IMG:Britannica Drinking Vessels 5.jpg|SAXON COW’S HORN. Mounted in silver. Taplow}}

{{IMG:Britannica Drinking Vessels 6.jpg|SAXON TRUMPET-SHAPED DRINKING VESSEL. With hollow tubular ornamentation}}

{{IMG:Britannica Drinking Vessels 7.jpg|THE ROYAL GOLD ENAMELLED HANAP. Made about 1380}}

{{IMG:Britannica Drinking Vessels 8.jpg|SARACENIC ENAMELLED GOBLET. With French silver mountings. Fourteenth century}}
```

### Current body
```
{{IMG:Britannica Drinking Vessels 1.jpg|ROMAN GLASS CUP. With representation of a chariot race. Found at Colchester}}

{{IMG:Britannica Drinking Vessels 2.jpg|TEUTONIC GLASS CUP. From a grave at Selzen, Rhenish Hesse}}

{{IMG:Britannica Drinking Vessels 3.jpg|SAXON GLASS “TUMBLER.”}}

{{IMG:Britannica Drinking Vessels 4.jpg|FRANKISH GLASS DRINKING HORN. Bingerbrück}}

{{IMG:Britannica Drinking Vessels 5.jpg|SAXON COW’S HORN. Mounted in silver. Taplow}}

{{IMG:Britannica Drinking Vessels 6.jpg|SAXON TRUMPET-SHAPED DRINKING VESSEL. With hollow tubular ornamentation}}

{{IMG:Britannica Drinking Vessels 7.jpg|THE ROYAL GOLD ENAMELLED HANAP. Made about 1380}}

{{IMG:Britannica Drinking Vessels 8.jpg|SARACENIC ENAMELLED GOBLET. With French silver mountings. Fourteenth century}}
```

---

## DRINKING VESSELS, PLATE II — vol 08

**Article ID:** 4243860  
**Signature:** `wikitable depth=2 wt=multi ht=0`

### Source excerpt
```
<section begin="Drinking Vessels" />
{| style="margin-left: auto; margin-right: auto; border-collapse: collapse;" summary="Illustration" 
| style="padding-right: 0.5em; padding-left: 0.5em; text-align: center; vertical-align: middle;" |
{| style="margin-left: auto; margin-right: auto; border-collapse: collapse;" summary="Illustration" 
| style="text-align: text-align: center;; margin: auto; margin-left: auto; margin-right: auto; padding-top: 1.5em;" |[[Image:Britannica Drinking Vessels 16.jpg|center|106px|]]
|-
| style="font-size: 0.9em; text-align: center; padding-bottom: 1em; padding-left: 1em; padding-right: 1em;" |{{sc|Fig. 8.}}—A GLASS “YARD OF ALE” (English).  Eighteenth century.
|}
| style="padding-right: 0.5em; padding-left: 0.5em; text-align: center; vertical-align: middle;" |
{| style="margin-left: auto; margin-right: auto; border-collapse: collapse; width: 720px;" summary="Illustration" 
| style="text-align: text-align: center;; margin: auto; margin-left: auto; margin-right: auto; padding-top: 1.5em;" |[[Image:Britannica Drinking Vessels 9.jpg|center|370px|]]
| style="text-align: text-align: center;; margin: auto; margin-left: auto; margin-right: auto; padding-top: 1.5em;" |[[Image:Britannica Drinking Vessels 10.jpg|center|319px|]]
|-
| style="font-size: 0.9em; text-align: center; padding-bottom: 1em; padding-left: 1em; padding-right: 1em;" |{{sc|Fig. 1.}}—VENETIAN GLASS GOBLET. With enamelled decoration. Fifteenth century.
| style="font-size: 0.9em; text-align: ce
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 8 | 8 |
| captioned       | 8 | 8 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **16** | **16** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:Britannica Drinking Vessels 16.jpg|A GLASS “YARD OF ALE” (English). Eighteenth century}}

{{IMG:Britannica Drinking Vessels 9.jpg|VENETIAN GLASS GOBLET. With enamelled decoration. Fifteenth century}}

{{IMG:Britannica Drinking Vessels 10.jpg|ENGLISH “BLACKJACK.” With initials of Charles I. and date 1646}}

{{IMG:Britannica Drinking Vessels 11.jpg|THE ROCHESTER MAZER. Presented by Brother Robert Peacham. Sixteenth century}}

{{IMG:Britannica Drinking Vessels 12.jpg|CHINESE CUP. Carved from rhinoceros horn. Eighteenth century}}

{{IMG:Britannica Drinking Vessels 13.jpg|ENGLISH GLASS TANKARD. Bearing the Arms of Lord Burleigh}}

{{IMG:Britannica Drinking Vessels 14.jpg|COCO-NUT CUP. German, about 1600}}

{{IMG:Britannica Drinking Vessels 15.jpg|SWISS “TANZENMANN.” Seventeenth century}}
```

### Current body
```
{{IMG:Britannica Drinking Vessels 16.jpg|A GLASS “YARD OF ALE” (English). Eighteenth century}}

{{IMG:Britannica Drinking Vessels 9.jpg|VENETIAN GLASS GOBLET. With enamelled decoration. Fifteenth century}}

{{IMG:Britannica Drinking Vessels 10.jpg|ENGLISH “BLACKJACK.” With initials of Charles I. and date 1646}}

{{IMG:Britannica Drinking Vessels 11.jpg|THE ROCHESTER MAZER. Presented by Brother Robert Peacham. Sixteenth century}}

{{IMG:Britannica Drinking Vessels 12.jpg|CHINESE CUP. Carved from rhinoceros horn. Eighteenth century}}

{{IMG:Britannica Drinking Vessels 13.jpg|ENGLISH GLASS TANKARD. Bearing the Arms of Lord Burleigh}}

{{IMG:Britannica Drinking Vessels 14.jpg|COCO-NUT CUP. German, about 1600}}

{{IMG:Britannica Drinking Vessels 15.jpg|SWISS “TANZENMANN.” Seventeenth century}}
```

---

## EGYPT — vol 09

**Article ID:** 4197728  
**Signature:** `wikitable depth=3 wt=multi ht=0 toplegend`

### Source excerpt
```
{{right|{{sc|Plate I.}}}}

{{c|EARLIEST EGYPTIAN ART}}

{|align="center"
|align="center"|
{|cellpadding="0" cellspacing="0"
|align="center"|[[Image:EB1911 Egypt - Earliest Art - Tatooed Female.jpg|x250px]]
|{{gap}}
|align="center"|[[Image:EB1911 Egypt - Earliest Art - Heads on Ivory Tusks.jpg|x250px]]
|{{gap}}
|align="center"|[[Image:EB1911 Egypt - Earliest Art - Animals on Bone Combs.jpg|x250px]]
|-valign="top"
|align="center" width="225"|1. TATOOED FEMALE, LIMESTONE SLAG.
|
|align="center" width="225"|2. HEADS ON IVORY TUSKS. 3.
|
|align="center" width="225"|4. ANIMALS ON BONE COMBS.
|-
|align="center"|[[Image:EB1911 Egypt - Earliest Art - Ivory Hawk.jpg|x125px]]
|
|align="center"|[[Image:EB1911 Egypt - Earliest Art - Ivory Dog and Gazelle.jpg|x100px]]
|
|align="center" rowspan="2"|[[Image:EB1911 Egypt - Earliest Art - White on Red Vases.jpg|x250px]]
|-valign="top"
|align="center"|[[Image:EB1911 Egypt - Earliest Art - Limestone Lion.jpg|x125px]]
|
|align="center"|[[Image:EB1911 Egypt - Earliest Art - Ivory Handle of Knife.jpg|x150px]]
|-valign="top"
|{{gap}}6. IVORY HAWK.
|
|align="center"|8. IVORY DOG AND GAZELLE.
|
|align="center" width="250" rowspan="2"|
{|cellpadding="0" cellspacing="0"
|10.
|rowspan="2"|{{brace2|2|r}}
|WHITE ON RED VASES;
|-
|11.
|align="center"|MEN AND ANIMALS.
|}
|-
|{{gap}}7. LIMESTONE LION.
|
|align="center"|9. IVORY HANDLE OF KNIFE.
|}
|-
|align="center"|
{|cellpadding="0" cellspacing="0"
|[[Image:EB1911 Egypt - Earliest Art - Ship on a Vase.jpg|x
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 13 | 13 |
| captioned       | 13 | 13 |
| legends         | 2 | 2 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **28** | **28** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Egypt - Earliest Art - Tatooed Female.jpg|TATOOED FEMALE, LIMESTONE SLAG}}

{{IMG:EB1911 Egypt - Earliest Art - Heads on Ivory Tusks.jpg|HEADS ON IVORY TUSKS. 3}}

{{IMG:EB1911 Egypt - Earliest Art - Animals on Bone Combs.jpg|ANIMALS ON BONE COMBS}}

{{IMG:EB1911 Egypt - Earliest Art - Ivory Hawk.jpg|IVORY HAWK}}

{{IMG:EB1911 Egypt - Earliest Art - Ivory Dog and Gazelle.jpg|IVORY DOG AND GAZELLE}}

{{IMG:EB1911 Egypt - Earliest Art - White on Red Vases.jpg|WHITE ON RED VASES}}

{{IMG:EB1911 Egypt - Earliest Art - Limestone Lion.jpg|MEN AND ANIMALS}}

{{IMG:EB1911 Egypt - Earliest Art - Ivory Handle of Knife.jpg|LIMESTONE LION}}

{{IMG:EB1911 Egypt - Earliest Art - Ship on a Vase.jpg|SHIP ON A VASE}}

{{IMG:EB1911 Egypt - Earliest Art - Ship on a Wall Painting.jpg|SHIP ON A WALL PAINTING}}

{{IMG:EB1911 Egypt - Earliest Art - Ivory King.jpg|IVORY KING}}

{{IMG:EB1911 Egypt - Earliest Art - Archaic King's Head.jpg|ARCHAIC KING'S HEAD, STUDY IN LIMESTONE. 16}}

{{IMG:EB1911 Egypt - Earliest Art - Head of Khasekhem.jpg|HEAD OF KHASEKHEM}}

{{LEGEND:EARLIEST EGYPTIAN ART}LEGEND}

{{LEGEND:IVORY HANDLE OF KNIFE}LEGEND}
```

### Current body
```
{{IMG:EB1911 Egypt - Earliest Art - Tatooed Female.jpg|TATOOED FEMALE, LIMESTONE SLAG}}

{{IMG:EB1911 Egypt - Earliest Art - Heads on Ivory Tusks.jpg|HEADS ON IVORY TUSKS. 3}}

{{IMG:EB1911 Egypt - Earliest Art - Animals on Bone Combs.jpg|ANIMALS ON BONE COMBS}}

{{IMG:EB1911 Egypt - Earliest Art - Ivory Hawk.jpg|IVORY HAWK}}

{{IMG:EB1911 Egypt - Earliest Art - Ivory Dog and Gazelle.jpg|IVORY DOG AND GAZELLE}}

{{IMG:EB1911 Egypt - Earliest Art - White on Red Vases.jpg|WHITE ON RED VASES}}

{{IMG:EB1911 Egypt - Earliest Art - Limestone Lion.jpg|MEN AND ANIMALS}}

{{IMG:EB1911 Egypt - Earliest Art - Ivory Handle of Knife.jpg|LIMESTONE LION}}

{{IMG:EB1911 Egypt - Earliest Art - Ship on a Vase.jpg|SHIP ON A VASE}}

{{IMG:EB1911 Egypt - Earliest Art - Ship on a Wall Painting.jpg|SHIP ON A WALL PAINTING}}

{{IMG:EB1911 Egypt - Earliest Art - Ivory King.jpg|IVORY KING}}

{{IMG:EB1911 Egypt - Earliest Art - Archaic King's Head.jpg|ARCHAIC KING'S HEAD, STUDY IN LIMESTONE. 16}}

{{IMG:EB1911 Egypt - Earliest Art - Head of Khasekhem.jpg|HEAD OF KHASEKHEM}}

{{LEGEND:EARLIEST EGYPTIAN ART}LEGEND}

{{LEGEND:IVORY HANDLE OF KNIFE}LEGEND}
```

---

## EMBROIDERY, PLATE I — vol 09

**Article ID:** 4197944  
**Signature:** `html_table depth=0 wt=0 ht=1`

### Source excerpt
```
<table align=center {{Ts|sm92|lh13}}>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 Embroidery - Fig. 6.—PANEL OF PETIT-POINT EMBROIDERY.jpg]]</td></tr>
<tr><td {{Ts|ac|pl1|pr1}}>{{sc|Fig. 6.}}—PANEL OF PETIT-POINT EMBROIDERY, WITH A REPRESENTATION OF COURTLY FIGURES IN A LANDSCAPE.<br/>English work of the end of the reign of Queen Elizabeth. Scale: {{EB1911 tfrac|1|6}}th.</td></tr>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 Embroidery - Fig. 7.—Portion of the BAYEUX TAPESTRY.jpg]]</td></tr>
<tr><td {{Ts|ac|pl1|pr1}}>{{sc|Fig. 7.}}—PORTION OF THE “BAYEUX TAPESTRY,” A BAND OF EMBROIDERY WITH THE STORY OF THE<br/>NORMAN CONQUEST OF ENGLAND. In the museum at Bayeux, 11th century work. Scale: {{EB1911 tfrac|1|4}}th.</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Embroidery - Fig. 6.—PANEL OF PETIT-POINT EMBROIDERY.jpg|PANEL OF PETIT-POINT EMBROIDERY, WITH A REPRESENTATION OF COURTLY FIGURES IN A LANDSCAPE. English work of the end of the reign of Queen Elizabeth. Scale: 6th}}

{{IMG:EB1911 Embroidery - Fig. 7.—Portion of the BAYEUX TAPESTRY.jpg|PORTION OF THE “BAYEUX TAPESTRY,” A BAND OF EMBROIDERY WITH THE STORY OF THE NORMAN CONQUEST OF ENGLAND. In the museum at Bayeux, 11th century work. Scale: 4th}}
```

### Current body
```
{{IMG:EB1911 Embroidery - Fig. 6.—PANEL OF PETIT-POINT EMBROIDERY.jpg|PANEL OF PETIT-POINT EMBROIDERY, WITH A REPRESENTATION OF COURTLY FIGURES IN A LANDSCAPE. English work of the end of the reign of Queen Elizabeth. Scale: 6th}}

{{IMG:EB1911 Embroidery - Fig. 7.—Portion of the BAYEUX TAPESTRY.jpg|PORTION OF THE “BAYEUX TAPESTRY,” A BAND OF EMBROIDERY WITH THE STORY OF THE NORMAN CONQUEST OF ENGLAND. In the museum at Bayeux, 11th century work. Scale: 4th}}
```

---

## EMBROIDERY, PLATE II — vol 09

**Article ID:** 4197945  
**Signature:** `html_table depth=0 wt=0 ht=1`

### Source excerpt
```
<table align=center {{Ts|sm92|lh13}}>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 Embroidery - Fig. 8.—HANGING OF WOOLLEN CLOTH.jpg]]</td></tr>
<tr><td {{Ts|ac|pl1|pr1}}>{{sc|Fig. 8.}}—HANGING OF WOOLLEN CLOTH, EMBROIDERED WITH THE FIVE WISE AND THE FIVE FOOLISH VIRGINS.<br />German work, dated 1598. Scale: {{EB1911 tfrac|1|10}}th.</td></tr>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 Embroidery - Fig. 9.—PORTION OF THE ORPHREY OF THE 'SYON COPE'.jpg]]</td></tr>
<tr><td {{Ts|ac|pl1|pr1}}>{{sc|Fig. 9.}}—PORTION OF THE ORPHREY OF THE “SYON COPE,” EMBROIDERED WITH SHIELDS OF ARMS.<br />The cope, formerly in the monastery of Syon near Isleworth, is now in the Victoria and Albert Museum.<br />
English work of the 13th century. Scale: {{EB1911 tfrac|5|16}}ths.</td></tr>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 Embroidery - Fig. 10.—PORTION OF A BAND OF LOOSE LINEN.jpg]]</td></tr>
<tr><td {{Ts|sm92|ac|pl1|pr1}}>{{sc|Fig. 10.}}—PORTION OF A BAND OF LOOSE LINEN, EMBROIDERED IN WHITE THREAD WITH FIGURES AND ANIMALS.<br />German work of the later part of the 14th century. Scale: {{EB1911 tfrac|2|7}}ths.</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Embroidery - Fig. 8.—HANGING OF WOOLLEN CLOTH.jpg|HANGING OF WOOLLEN CLOTH, EMBROIDERED WITH THE FIVE WISE AND THE FIVE FOOLISH VIRGINS. German work, dated 1598. Scale: 10th}}

{{IMG:EB1911 Embroidery - Fig. 9.—PORTION OF THE ORPHREY OF THE 'SYON COPE'.jpg|PORTION OF THE ORPHREY OF THE “SYON COPE,” EMBROIDERED WITH SHIELDS OF ARMS. The cope, formerly in the monastery of Syon near Isleworth, is now in the Victoria and Albert Museum. English work of the 13th century. Scale: 16ths}}

{{IMG:EB1911 Embroidery - Fig. 10.—PORTION OF A BAND OF LOOSE LINEN.jpg|PORTION OF A BAND OF LOOSE LINEN, EMBROIDERED IN WHITE THREAD WITH FIGURES AND ANIMALS. German work of the later part of the 14th century. Scale: 7ths}}
```

### Current body
```
{{IMG:EB1911 Embroidery - Fig. 8.—HANGING OF WOOLLEN CLOTH.jpg|HANGING OF WOOLLEN CLOTH, EMBROIDERED WITH THE FIVE WISE AND THE FIVE FOOLISH VIRGINS. German work, dated 1598. Scale: 10th}}

{{IMG:EB1911 Embroidery - Fig. 9.—PORTION OF THE ORPHREY OF THE 'SYON COPE'.jpg|PORTION OF THE ORPHREY OF THE “SYON COPE,” EMBROIDERED WITH SHIELDS OF ARMS. The cope, formerly in the monastery of Syon near Isleworth, is now in the Victoria and Albert Museum. English work of the 13th century. Scale: 16ths}}

{{IMG:EB1911 Embroidery - Fig. 10.—PORTION OF A BAND OF LOOSE LINEN.jpg|PORTION OF A BAND OF LOOSE LINEN, EMBROIDERED IN WHITE THREAD WITH FIGURES AND ANIMALS. German work of the later part of the 14th century. Scale: 7ths}}
```

---

## EMBROIDERY, PLATE III — vol 09

**Article ID:** 4197949  
**Signature:** `html_table depth=0 wt=0 ht=1`

### Source excerpt
```
<table align=center {{Ts|sm92|lh13}}>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 Embroidery - Fig. 11.—Silk Panel with Lantern.jpg]]</td>
<td {{Ts|ac|mc|ma|pt1|pl1}}>[[File:EB1911 Embroidery - Fig. 13.—Portion of a Bed-Hanging with Trees.jpg]]</td></tr>
<tr><td {{Ts|ac|pl1|pr1}}>{{sc|Fig. 11.}}—SILK PANEL, EMBROIDERED WITH A<br />HANGING LANTERN.<br />Chinese work of the 17th or 18th century. Scale: {{EB1911 tfrac|1|4}}th.</td>
<td {{Ts|ac|pl1|pr1}}>{{sc|Fig. 13.}}—PORTION OF A BED-HANGING, EMBROIDERED<br />WITH FLOWERING TREES GROWING FROM MOUNDS.<br />English work of the later part of the 17th century. Scale: {{EB1911 tfrac|1|12}}th.</td></tr>

<tr><td {{Ts|ac|mc|ma|pt1}}><[[File:EB1911 Embroidery - Fig. 12.—Portion of a large hanging, Iceland.jpg]]</td>
<td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 Embroidery - Fig. 14.—APPAREL FOR A DALMATIC.jpg]]</td></tr>
<tr><td {{Ts|pl1|pr1}}>{{sc|Fig. 12.}}—PORTION OF A LARGE HANGING, EMBROIDERED<br />WITH FIGURES WITHIN MEDALLIONS,<br />
AND INSCRIPTIONS.<br />From a church in Iceland, probably 17th century. Scale: {{EB1911 tfrac|1|8}}th.</td>
<td {{Ts|sm92|ac|pl1|pr1}}>{{sc|Fig. 14.}}—APPAREL FOR A DALMATIC OF GREEN VELVET,<br/>EMBROIDERED WITH AN APPLIQUÉ PATTERN.<br />
Italian work of the 16th century. Scale: {{EB1911 tfrac|1|4}}th.</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Embroidery - Fig. 11.—Silk Panel with Lantern.jpg|SILK PANEL, EMBROIDERED WITH A HANGING LANTERN. Chinese work of the 17th or 18th century. Scale: 4th}}

{{IMG:EB1911 Embroidery - Fig. 13.—Portion of a Bed-Hanging with Trees.jpg|PORTION OF A BED-HANGING, EMBROIDERED WITH FLOWERING TREES GROWING FROM MOUNDS. English work of the later part of the 17th century. Scale: 12th}}

{{IMG:EB1911 Embroidery - Fig. 12.—Portion of a large hanging, Iceland.jpg|PORTION OF A LARGE HANGING, EMBROIDERED WITH FIGURES WITHIN MEDALLIONS, AND INSCRIPTIONS. From a church in Iceland, probably 17th century. Scale: 8th}}

{{IMG:EB1911 Embroidery - Fig. 14.—APPAREL FOR A DALMATIC.jpg|APPAREL FOR A DALMATIC OF GREEN VELVET, EMBROIDERED WITH AN APPLIQUÉ PATTERN. Italian work of the 16th century. Scale: 4th}}
```

### Current body
```
{{IMG:EB1911 Embroidery - Fig. 11.—Silk Panel with Lantern.jpg|SILK PANEL, EMBROIDERED WITH A HANGING LANTERN. Chinese work of the 17th or 18th century. Scale: 4th}}

{{IMG:EB1911 Embroidery - Fig. 13.—Portion of a Bed-Hanging with Trees.jpg|PORTION OF A BED-HANGING, EMBROIDERED WITH FLOWERING TREES GROWING FROM MOUNDS. English work of the later part of the 17th century. Scale: 12th}}

{{IMG:EB1911 Embroidery - Fig. 12.—Portion of a large hanging, Iceland.jpg|PORTION OF A LARGE HANGING, EMBROIDERED WITH FIGURES WITHIN MEDALLIONS, AND INSCRIPTIONS. From a church in Iceland, probably 17th century. Scale: 8th}}

{{IMG:EB1911 Embroidery - Fig. 14.—APPAREL FOR A DALMATIC.jpg|APPAREL FOR A DALMATIC OF GREEN VELVET, EMBROIDERED WITH AN APPLIQUÉ PATTERN. Italian work of the 16th century. Scale: 4th}}
```

---

## EMBROIDERY, PLATE IV — vol 09

**Article ID:** 4197950  
**Signature:** `html_table depth=0 wt=0 ht=1`

### Source excerpt
```
<table align=center  {{Ts|sm92|lh13}}>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 Embroidery - Fig. 15.—PORTION OF THE BORDER OF A LINEN COVER.jpg]]</td></tr>
<tr><td {{Ts|ac|pl1|pr1}}>{{sc|Fig. 15.}}—PORTION OF THE BORDER OF A LINEN COVER, EMBROIDERED WITH A FIGURE OF ST CATHERINE<br/>OF ALEXANDRIA AND KNEELING VOTARIES. Italian work of the 16th century. Scale: {{EB1911 tfrac|2|5}}ths.</td></tr>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 Embroidery - Fig. 16.—Linen Border, Birds & Flowers.jpg]]</td></tr>
<tr><td {{Ts|ac|pl1|pr1}}>{{sc|Fig. 16.}}—LINEN BORDER, EMBROIDERED WITH DEBASED FIGURES, BIRDS AND ANIMALS AMID FLOWERS.<br />Cretan work, dated 1762. Scale: {{EB1911 tfrac|4|9}}ths.</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Embroidery - Fig. 15.—PORTION OF THE BORDER OF A LINEN COVER.jpg|PORTION OF THE BORDER OF A LINEN COVER, EMBROIDERED WITH A FIGURE OF ST CATHERINE OF ALEXANDRIA AND KNEELING VOTARIES. Italian work of the 16th century. Scale: 5ths}}

{{IMG:EB1911 Embroidery - Fig. 16.—Linen Border, Birds & Flowers.jpg|LINEN BORDER, EMBROIDERED WITH DEBASED FIGURES, BIRDS AND ANIMALS AMID FLOWERS. Cretan work, dated 1762. Scale: 9ths}}
```

### Current body
```
{{IMG:EB1911 Embroidery - Fig. 15.—PORTION OF THE BORDER OF A LINEN COVER.jpg|PORTION OF THE BORDER OF A LINEN COVER, EMBROIDERED WITH A FIGURE OF ST CATHERINE OF ALEXANDRIA AND KNEELING VOTARIES. Italian work of the 16th century. Scale: 5ths}}

{{IMG:EB1911 Embroidery - Fig. 16.—Linen Border, Birds & Flowers.jpg|LINEN BORDER, EMBROIDERED WITH DEBASED FIGURES, BIRDS AND ANIMALS AMID FLOWERS. Cretan work, dated 1762. Scale: 9ths}}
```

---

## EMBROIDERY, PLATE V — vol 09

**Article ID:** 4197953  
**Signature:** `html_table depth=0 wt=0 ht=1`

### Source excerpt
```
<table align=center>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 Embroidery - Fig. 17.—LINEN PRAYER CARPET.jpg]]</td></tr>
<tr><td {{Ts|sm92|ac|pl1|pr1}}>{{sc|Fig. 17.}}—LINEN PRAYER CARPET, QUILTED AND EMBROIDERED IN CHAIN STITCH WITH COLOURED SILKS, CHIEFLY WHITE, YELLOW, GREEN AND RED.</td></tr>
<tr><td {{Ts|pl.5|pr.5|sm92|lh13}}>The border consists of a wide band set between two narrow ones, each with a waved continuous stem with blossoms in the wavings. Similar floral scrolling and leafy stem<br/>ornament fills the space beyond the pointed shape at the upper end, which is edged with acanthus leaf devices. The main ground below the niche or pointed shape is a blossoming<br/>plant, with balanced bunches of flowers between which are leaves, formally arranged in a pointed oval shape. Persian work, 18th century, 4 ft. 6 in. × 2 ft. 11 in. (Victoria and<br/>Albert Museum.)</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | 'The border consists of a wide band set between two narrow ones, each with a waved continuous stem with blossoms in the w' | 'The border consists of a wide band set between two narrow ones, each with a waved continuous stem with blossoms in the w' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Embroidery - Fig. 17.—LINEN PRAYER CARPET.jpg|LINEN PRAYER CARPET, QUILTED AND EMBROIDERED IN CHAIN STITCH WITH COLOURED SILKS, CHIEFLY WHITE, YELLOW, GREEN AND RED}}

The border consists of a wide band set between two narrow ones, each with a waved continuous stem with blossoms in the wavings. Similar floral scrolling and leafy stem ornament fills the space beyond the pointed shape at the upper end, which is edged with acanthus leaf devices. The main ground below the niche or pointed shape is a blossoming plant, with balanced bunches of flowers between which are leaves, formally arranged in a pointed oval shape. Persian work, 18th century, 4 ft. 6 in. × 2 ft. 11 in. (Victoria and Albert Museum.)
```

### Current body
```
{{IMG:EB1911 Embroidery - Fig. 17.—LINEN PRAYER CARPET.jpg|LINEN PRAYER CARPET, QUILTED AND EMBROIDERED IN CHAIN STITCH WITH COLOURED SILKS, CHIEFLY WHITE, YELLOW, GREEN AND RED}}

The border consists of a wide band set between two narrow ones, each with a waved continuous stem with blossoms in the wavings. Similar floral scrolling and leafy stem ornament fills the space beyond the pointed shape at the upper end, which is edged with acanthus leaf devices. The main ground below the niche or pointed shape is a blossoming plant, with balanced bunches of flowers between which are leaves, formally arranged in a pointed oval shape. Persian work, 18th century, 4 ft. 6 in. × 2 ft. 11 in. (Victoria and Albert Museum.)
```

---

## EMBROIDERY, PLATE VI — vol 09

**Article ID:** 4197954  
**Signature:** `html_table depth=0 wt=0 ht=1`

### Source excerpt
```
<table align=center {{Ts|sm92|lh13}}>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 Embroidery - Fig. 18.—PART OF A SICILIAN COVERLET.jpg|center]]</td></tr>
<tr><td {{Ts|ac|pl1|pr1}}>{{sc|Fig. 18.}}—PART OF A SICILIAN COVERLET, OF THE END OF THE 14TH CENTURY.</td></tr>
<tr><td {{Ts|pl2|sm92|pl5}}>It is of white linen, quilted and padded in wool so as to throw the design into relief. The scenes represented, taken from the<br />Story of Tristan, with inscriptions in the Sicilian dialect, are as follows:—(1) {{sc|Comu: Lu Amoroldu Fa Bandiri: Lu Osti: In<br />Cornuualgia}} (How the Morold made the host to go to Cornwall); (2) {{sc|Comu: Lu Rre: Languis: Cumanda: Chi Uaia: Lo Osti.<br />Cornuaglia}} (How King Languis ordered that the host should go to Cornwall); (3) {{sc|Comu: Lu Rre: Languis: Manda: Per Lu<br />Trabutu in Cornualia}} (How King Languis sent to Cornwall for the tribute); (4) {{sc|Comu: (li m) Issagieri: so Uinnti: Al Rre:<br />Marcu: Per Lu Tributu Di Secti Anni}} (How the ambassadors are come to King Mark for the tribute of seven years); (5)<br />{{sc|Comu: Lu Amoroldu Uai: in Cornuualgia}} (How the Morold comes to Cornwall); (6) {{sc|Comu: Lu Amoroldu: Fa Suldari:<br />La Genti}} (How the Morold made the people pay); (7) {{sc|Comu: T(ristainu): Dai: Lu Guantu Allu Amoroldu Dela<br />Bactaglia}} (How Tristan gives the glove of battle to the Morold); (8) {{sc|Comu: Lu Amoroldu: E Uinutu: in Cornuualgia:<br />Cum XXXX Galei}}: (How the Morold is come to Cornwall with f
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | 'It is of white linen, quilted and padded in wool so as to throw the design into relief. The scenes represented, taken fr' | 'It is of white linen, quilted and padded in wool so as to throw the design into relief. The scenes represented, taken fr' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Embroidery - Fig. 18.—PART OF A SICILIAN COVERLET.jpg|PART OF A SICILIAN COVERLET, OF THE END OF THE 14TH CENTURY}}

It is of white linen, quilted and padded in wool so as to throw the design into relief. The scenes represented, taken from the Story of Tristan, with inscriptions in the Sicilian dialect, are as follows:—(1) Comu: Lu Amoroldu Fa Bandiri: Lu Osti: In Cornuualgia (How the Morold made the host to go to Cornwall); (2) Comu: Lu Rre: Languis: Cumanda: Chi Uaia: Lo Osti. Cornuaglia (How King Languis ordered that the host should go to Cornwall); (3) Comu: Lu Rre: Languis: Manda: Per Lu Trabutu in Cornualia (How King Languis sent to Cornwall for the tribute); (4) Comu: (li m) Issagieri: so Uinnti: Al Rre: Marcu: Per Lu Tributu Di Secti Anni (How the ambassadors are come to King Mark for the tribute of seven years); (5) Comu: Lu Amoroldu Uai: in Cornuualgia (How the Morold comes to Cornwall); (6) Comu: Lu Amoroldu: Fa Suldari: La Genti (How the Morold made the people pay); (7) Comu: T(ristainu): Dai: Lu Guantu Allu Amoroldu Dela Bactaglia (How Tristan gives the glove of battle to the Morold); (8) Comu: Lu Amoroldu: E Uinutu: in Cornuualgia: Cum XXXX Galei: (How the Morold is come to Cornwall with forty galleys); (9) Comu Tristainu Bucta: La Uarca: Arretu: Intu: Allu Maru (How Tristan struck his boat behind him into the sea); (10) Comu: Tristainu: Aspecta: Lu Amoroldu: Alla Isola Di Lu Maru: Sansa Uintura (How Tristan awaits the Morold on the isle Sanza Ventura in the sea); (11) Comu: Tristainu Feriu Lu Amorolldu in Testa (How Tristan wounded the Morold in the head); (12) Comu: Lu Inna (?) Delu Amoroldu: Aspecttaua Lu Patrunu (How the Morold’s page (?) awaited his master); (13) Comu Lu Amorodu Feriu: Tristainu A Tradimantu (How the Morold wounded Tristan by treachery); (14) ... Sita: In Airlandia ( ... in Ireland)
```

### Current body
```
{{IMG:EB1911 Embroidery - Fig. 18.—PART OF A SICILIAN COVERLET.jpg|PART OF A SICILIAN COVERLET, OF THE END OF THE 14TH CENTURY}}

It is of white linen, quilted and padded in wool so as to throw the design into relief. The scenes represented, taken from the Story of Tristan, with inscriptions in the Sicilian dialect, are as follows:—(1) Comu: Lu Amoroldu Fa Bandiri: Lu Osti: In Cornuualgia (How the Morold made the host to go to Cornwall); (2) Comu: Lu Rre: Languis: Cumanda: Chi Uaia: Lo Osti. Cornuaglia (How King Languis ordered that the host should go to Cornwall); (3) Comu: Lu Rre: Languis: Manda: Per Lu Trabutu in Cornualia (How King Languis sent to Cornwall for the tribute); (4) Comu: (li m) Issagieri: so Uinnti: Al Rre: Marcu: Per Lu Tributu Di Secti Anni (How the ambassadors are come to King Mark for the tribute of seven years); (5) Comu: Lu Amoroldu Uai: in Cornuualgia (How the Morold comes to Cornwall); (6) Comu: Lu Amoroldu: Fa Suldari: La Genti (How the Morold made the people pay); (7) Comu: T(ristainu): Dai: Lu Guantu Allu Amoroldu Dela Bactaglia (How Tristan gives the glove of battle to the Morold); (8) Comu: Lu Amoroldu: E Uinutu: in Cornuualgia: Cum XXXX Galei: (How the Morold is come to Cornwall with forty galleys); (9) Comu Tristainu Bucta: La Uarca: Arretu: Intu: Allu Maru (How Tristan struck his boat behind him into the sea); (10) Comu: Tristainu: Aspecta: Lu Amoroldu: Alla Isola Di Lu Maru: Sansa Uintura (How Tristan awaits the Morold on the isle Sanza Ventura in the sea); (11) Comu: Tristainu Feriu Lu Amorolldu in Testa (How Tristan wounded the Morold in the head); (12) Comu: Lu Inna (?) Delu Amoroldu: Aspecttaua Lu Patrunu (How the Morold’s page (?) awaited his master); (13) Comu Lu Amorodu Feriu: Tristainu A Tradimantu (How the Morold wounded Tristan by treachery); (14) ... Sita: In Airlandia ( ... in Ireland)
```

---

## ENAMELS, PLATE I — vol 09

**Article ID:** 4197999  
**Signature:** `illustration_html depth=0 wt=0 ht=multi has_illus`

### Source excerpt
```
<table align=center {{Ts|sm92|lh13}}>
<tr><td {{Ts|ac|mc|ma|pt1}}>

<table style="clear: both;" summary="Illustration">
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 Enamel - Fig. 3.—GRAECO-BACTRIAN GOLD AMULET.jpg]]</td></tr>
<tr><td {{Ts|pl2|al}}>{{sc|Fig.}} 3.—GRAECO-BACTRIAN GOLD AMULET, SHOWING<br/>THE GOLD STRIP FOR SETTING STONES, WHICH<br/>EXEMPLIFIES THE MANNER IN WHICH THE<br/>CLOISONS ARE SOLDERED FOR CLOISONNÉ.</td></tr>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 Enamel - Fig. 6.—Box in Copper Partly Enamelled.jpg]]</td></tr>
<tr><td {{Ts|pl2|al}}>{{sc|Fig.}} 6.—BOX IN COPPER PARTLY ENAMELLED IN OPAQUE<br/>ENAMELS CHAMPLEVÉ WITH COATS OF ARMS.<br/>(13th century, English or German. South Kensington Museum.)</td></tr></table>
</td>
<td {{Ts|ac|mc|ma|pt1}}>

<table style="clear: both;" summary="Illustration">
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 Enamel - Fig. 4.—CHINESE CLOISONNÉ BOWL.jpg]]</td></tr>
<tr><td {{Ts|ac|pl1|pr1}}>{{sc|Fig.}} 4.—CHINESE CLOISONNÉ BOWL.</td></tr>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 Enamel - Fig. 5—Missal Cover.jpg]]</td></tr>
<tr><td {{Ts|ac|pl2}}>{{sc|Fig.}} 5.—MISSAL COVER, ENCRUSTED ENAMEL.<br />(French, 17th century. Debased style.)</td></tr>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 Enamel - Fig. 7.—PRAYER-BOOK COVER IN ENAMEL AND SILVER GILT.jpg]]</td></tr>
<tr><td {{Ts|al|pl4}}>{{sc|Fig.}} 7.—PRAYER-BOOK COVER IN ENAMEL AND SILVER GILT,<br/>SET WITH RUBIES AND EMERALDS, BY ALEXANDER FISHER.<br/>(Size, closed, 4 <big>×</big> 3 
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 5 | 5 |
| captioned       | 5 | 5 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **10** | **10** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Enamel - Fig. 3.—GRAECO-BACTRIAN GOLD AMULET.jpg|GRAECO-BACTRIAN GOLD AMULET, SHOWING THE GOLD STRIP FOR SETTING STONES, WHICH EXEMPLIFIES THE MANNER IN WHICH THE CLOISONS ARE SOLDERED FOR CLOISONNÉ}}

{{IMG:EB1911 Enamel - Fig. 6.—Box in Copper Partly Enamelled.jpg|BOX IN COPPER PARTLY ENAMELLED IN OPAQUE ENAMELS CHAMPLEVÉ WITH COATS OF ARMS. (13th century, English or German. South Kensington Museum.)}}

{{IMG:EB1911 Enamel - Fig. 4.—CHINESE CLOISONNÉ BOWL.jpg|CHINESE CLOISONNÉ BOWL}}

{{IMG:EB1911 Enamel - Fig. 5—Missal Cover.jpg|MISSAL COVER, ENCRUSTED ENAMEL. (French, 17th century. Debased style.)}}

{{IMG:EB1911 Enamel - Fig. 7.—PRAYER-BOOK COVER IN ENAMEL AND SILVER GILT.jpg|PRAYER-BOOK COVER IN ENAMEL AND SILVER GILT, SET WITH RUBIES AND EMERALDS, BY ALEXANDER FISHER. (Size, closed, 4 × 3 in.)}}
```

### Current body
```
{{IMG:EB1911 Enamel - Fig. 3.—GRAECO-BACTRIAN GOLD AMULET.jpg|GRAECO-BACTRIAN GOLD AMULET, SHOWING THE GOLD STRIP FOR SETTING STONES, WHICH EXEMPLIFIES THE MANNER IN WHICH THE CLOISONS ARE SOLDERED FOR CLOISONNÉ}}

{{IMG:EB1911 Enamel - Fig. 6.—Box in Copper Partly Enamelled.jpg|BOX IN COPPER PARTLY ENAMELLED IN OPAQUE ENAMELS CHAMPLEVÉ WITH COATS OF ARMS. (13th century, English or German. South Kensington Museum.)}}

{{IMG:EB1911 Enamel - Fig. 4.—CHINESE CLOISONNÉ BOWL.jpg|CHINESE CLOISONNÉ BOWL}}

{{IMG:EB1911 Enamel - Fig. 5—Missal Cover.jpg|MISSAL COVER, ENCRUSTED ENAMEL. (French, 17th century. Debased style.)}}

{{IMG:EB1911 Enamel - Fig. 7.—PRAYER-BOOK COVER IN ENAMEL AND SILVER GILT.jpg|PRAYER-BOOK COVER IN ENAMEL AND SILVER GILT, SET WITH RUBIES AND EMERALDS, BY ALEXANDER FISHER. (Size, closed, 4 × 3 in.)}}
```

---

## ENAMELS, PLATE II — vol 09

**Article ID:** 4198000  
**Signature:** `html_table depth=0 wt=0 ht=1 has_colspan`

### Source excerpt
```
<table {{Ts|sm92|lh13}} align=center>
<tr><td {{Ts|ac|mc|ma|pt1}} colspan="2">[[File:EB1911 Enamel - Fig. 8.—OVERMANTEL.jpg]]</td></tr>
<tr><td align=center colspan="2">{{sc|Fig.}} 8.—OVERMANTEL (24 × 18{{EB1911 tfrac|1|2}} in.) IN CHAMPLEVÉ ENAMEL ON SILVER. SUBJECT: THE GARDEN OF THE SOUL.<br/>BY ALEXANDER FISHER.</td></tr>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 Enamel - Fig. 9.—PAINTED ENAMEL CASKET.jpg]]</td>
<td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 Enamel - Fig. 10.—CELTIC CHAMPLEVÉ.jpg]]</td></tr>
<tr><td {{Ts|ac|vtp>{{sc|Fig.}} 9.—PAINTED ENAMEL CASKET BY JEAN PÉNICAUD. (16th century.)</td>
<td align=center>{{sc|Fig.}} 10.—CELTIC CHAMPLEVÉ ENAMELLED CROZIER.<br />(Irish, 9th century.)</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Enamel - Fig. 8.—OVERMANTEL.jpg|OVERMANTEL (24 × 182 in.) IN CHAMPLEVÉ ENAMEL ON SILVER. SUBJECT: THE GARDEN OF THE SOUL. BY ALEXANDER FISHER}}

{{IMG:EB1911 Enamel - Fig. 9.—PAINTED ENAMEL CASKET.jpg|PAINTED ENAMEL CASKET BY JEAN PÉNICAUD. (16th century.)}}

{{IMG:EB1911 Enamel - Fig. 10.—CELTIC CHAMPLEVÉ.jpg|CELTIC CHAMPLEVÉ ENAMELLED CROZIER. (Irish, 9th century.)}}
```

### Current body
```
{{IMG:EB1911 Enamel - Fig. 8.—OVERMANTEL.jpg|OVERMANTEL (24 × 182 in.) IN CHAMPLEVÉ ENAMEL ON SILVER. SUBJECT: THE GARDEN OF THE SOUL. BY ALEXANDER FISHER}}

{{IMG:EB1911 Enamel - Fig. 9.—PAINTED ENAMEL CASKET.jpg|PAINTED ENAMEL CASKET BY JEAN PÉNICAUD. (16th century.)}}

{{IMG:EB1911 Enamel - Fig. 10.—CELTIC CHAMPLEVÉ.jpg|CELTIC CHAMPLEVÉ ENAMELLED CROZIER. (Irish, 9th century.)}}
```

---

## PLATE (VOL. 9, P. 950) — vol 09

**Article ID:** 4198439  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|align="center" cellpadding="0" cellspacing="0" style="font-size: 50%"
|[[Image:EB1911 Europe - End of 10th Century.jpg|700px]]
|-
|style="height: 0.5em"|
|-
|[[Image:EB1911 Europe - End of 12th Century.jpg|700px]]
|-
|align="right"|Emery Walker sc.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 1 | 1 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **3** | **3** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Europe - End of 10th Century.jpg|Emery Walker sc}}

{{IMG:EB1911 Europe - End of 12th Century.jpg}}
```

### Current body
```
{{IMG:EB1911 Europe - End of 10th Century.jpg|Emery Walker sc}}

{{IMG:EB1911 Europe - End of 12th Century.jpg}}
```

---

## PLATE (VOL. 9, P. 955) — vol 09

**Article ID:** 4198440  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|align="center" cellpadding="0" cellspacing="0" style="font-size: 50%"
|[[Image:EB1911 Europe - Middle of 16th Century.jpg|700px]]
|-
|style="height: 0.5em"|
|-
|[[Image:EB1911 Europe - 1715.jpg|700px]]
|-
|align="right"|Emery Walker sc.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 1 | 1 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **3** | **3** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Europe - Middle of 16th Century.jpg|Emery Walker sc}}

{{IMG:EB1911 Europe - 1715.jpg}}
```

### Current body
```
{{IMG:EB1911 Europe - Middle of 16th Century.jpg|Emery Walker sc}}

{{IMG:EB1911 Europe - 1715.jpg}}
```

---

## PLATE (VOL. 9, P. 960) — vol 09

**Article ID:** 4198441  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|align="center" cellpadding="0" cellspacing="0" style="font-size: 50%"
|[[Image:EB1911 Europe - 1810.jpg|700px]]
|-
|style="height: 0.5em"|
|-
|[[Image:EB1911 Europe - 1815.jpg|700px]]
|-
|align="right"|Emery Walker sc.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 1 | 1 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **3** | **3** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Europe - 1810.jpg|Emery Walker sc}}

{{IMG:EB1911 Europe - 1815.jpg}}
```

### Current body
```
{{IMG:EB1911 Europe - 1810.jpg|Emery Walker sc}}

{{IMG:EB1911 Europe - 1815.jpg}}
```

---

## FIBRES, PLATE I — vol 10

**Article ID:** 4199001  
**Signature:** `html_table depth=0 wt=0 ht=1`

### Source excerpt
```
<table style="clear: both;" align=center>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 - Fibres - Fig. 1.jpg]]</td>
<td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 - Fibres - Fig. 2.jpg]]</td></tr>
<tr><td {{Ts|sm92|lh13|ac|pl1|pr1}}>{{sc|Fig.}} 1.—RAW SILK. ''Bombyx mori''. Filament of bave,<br/>viewed in length. × 110.</td>
<td {{Ts|sm92|lh13|ac|pl1|pr1}}>{{sc|Fig.}} 2.—RAW SILK. ''Bombyx mori''. Single fibres in transverse<br/>section showing each fibre or “bave” as dual cylinder. × 235.</td></tr>

<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 - Fibres - Fig. 3.jpg]]</td>
<td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 - Fibres - Fig. 4.jpg]]</td></tr>
<tr><td {{Ts|sm92|lh13|pl1|pr1}}>{{sc|Fig.}} 3.—ARTIFICIAL “SILK.” Lustra-cellulose viscose process,<br/>&nbsp;single fibres in transverse section × 235. Normal type—polygon<br/>&nbsp;of 5 sides—with concave sides due to contact of the<br/>&nbsp;component units of textile filament.</td>
<td {{Ts|sm92|lh13|pl1|pr1}}>{{sc|Fig.}} 4.—WOOL FIBRES. Australian merino viewed in length,<br/>&nbsp;× 235. Surface imbrications—the structural cause of true<br/>&nbsp;felting properties.</td></tr>

<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 - Fibres - Fig. 5.jpg]]</td>
<td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 - Fibres - Fig. 6.jpg]]</td></tr>
<tr><td {{Ts|sm92|lh13|ac|pl1|pr1}}>{{sc|Fig.}} 5.—FLAX STEM. ''Linum usitatissimum'', tranverse section<br/>of stem, × 235, showing bast fibres occupying central zone.</td>
<td {{Ts|sm92|lh13|ac|pl1|pr1}}>{{sc|Fig.}} 6.—RAMIE. Sec
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 6 | 6 |
| captioned       | 6 | 6 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **12** | **12** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Fibres - Fig. 1.jpg|RAW SILK. Bombyx mori. Filament of bave, viewed in length. × 110}}

{{IMG:EB1911 - Fibres - Fig. 2.jpg|RAW SILK. Bombyx mori. Single fibres in transverse section showing each fibre or “bave” as dual cylinder. × 235}}

{{IMG:EB1911 - Fibres - Fig. 3.jpg|ARTIFICIAL “SILK.” Lustra-cellulose viscose process, single fibres in transverse section × 235. Normal type—polygon of 5 sides—with concave sides due to contact of the component units of textile filament}}

{{IMG:EB1911 - Fibres - Fig. 4.jpg|WOOL FIBRES. Australian merino viewed in length, × 235. Surface imbrications—the structural cause of true felting properties}}

{{IMG:EB1911 - Fibres - Fig. 5.jpg|FLAX STEM. Linum usitatissimum, tranverse section of stem, × 235, showing bast fibres occupying central zone}}

{{IMG:EB1911 - Fibres - Fig. 6.jpg|RAMIE. Section of bast region, × 235. Showing bast fibres bundles but only slightly occurring as individuals}}
```

### Current body
```
{{IMG:EB1911 - Fibres - Fig. 1.jpg|RAW SILK. Bombyx mori. Filament of bave, viewed in length. × 110}}

{{IMG:EB1911 - Fibres - Fig. 2.jpg|RAW SILK. Bombyx mori. Single fibres in transverse section showing each fibre or “bave” as dual cylinder. × 235}}

{{IMG:EB1911 - Fibres - Fig. 3.jpg|ARTIFICIAL “SILK.” Lustra-cellulose viscose process, single fibres in transverse section × 235. Normal type—polygon of 5 sides—with concave sides due to contact of the component units of textile filament}}

{{IMG:EB1911 - Fibres - Fig. 4.jpg|WOOL FIBRES. Australian merino viewed in length, × 235. Surface imbrications—the structural cause of true felting properties}}

{{IMG:EB1911 - Fibres - Fig. 5.jpg|FLAX STEM. Linum usitatissimum, tranverse section of stem, × 235, showing bast fibres occupying central zone}}

{{IMG:EB1911 - Fibres - Fig. 6.jpg|RAMIE. Section of bast region, × 235. Showing bast fibres bundles but only slightly occurring as individuals}}
```

---

## FIBRES, PLATE II — vol 10

**Article ID:** 4199002  
**Signature:** `html_table depth=0 wt=0 ht=1`

### Source excerpt
```
<table style="clear: both;" align=center>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 - Fibres - Fig. 7.jpg]]</td>
<td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 - Fibres - Fig. 8.jpg]]</td></tr>
<tr><td {{Ts|sm92|lh13|ac|pl1|pr1}}>{{sc|Fig.}} 7.—JUTE. Bast bundles. Section of bast region, × 235,<br/>showing agglomerated bundles of bast fibre, each bundle representing<br/>a spinning unit or filament.</td>
<td {{Ts|sm92|lh13|ac|pl1|pr1}}>{{sc|Fig.}} 8.—MAIZE STEM. ''Zea mais''. Fibro-vascular bundle in<br/>section. × 110, typical of monocotyledonous structure.</td></tr>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 - Fibres - Fig. 9.jpg]]</td>
<td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 - Fibres - Fig. 10.jpg]]</td></tr>
<tr><td {{Ts|sm92|lh13|ac|pl1|pr1}}>{{sc|Fig.}} 9.—COTTON. FLAX. RAMIE. JUTE. Ultimate fibres in<br/>the length, × 110. Portions selected to show typical structural<br/>characteristics.</td>
<td {{Ts|sm92|lh13|ac|pl1|pr1}}>{{sc|Fig.}} 10.—COTTON. FLAX. RAMIE. JUTE. Ultimate fibres—transverse<br/>section, × 110. Note similarity of ramie to cotton<br/>and jute to flax.</td></tr><tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 - Fibres - Fig. 11.jpg]]</td>
<td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 - Fibres - Fig. 12.jpg]]</td></tr>
<tr><td {{Ts|sm92|lh13|ac|pl1|pr1}}>{{sc|Fig.}} 11.—ESPARTO. Cellulose. Ultimate fibres of paper making<br/>pulp. Typical fusiform bast fibres. × 65.</td>
<td {{Ts|sm92|lh13|ac|pl1|pr1}}>{{sc|Fig.}} 12.—SECTION OF HAND-MADE PAPER. × 110. Ultimate<br/>component fibres
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 6 | 6 |
| captioned       | 6 | 6 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **12** | **12** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Fibres - Fig. 7.jpg|JUTE. Bast bundles. Section of bast region, × 235, showing agglomerated bundles of bast fibre, each bundle representing a spinning unit or filament}}

{{IMG:EB1911 - Fibres - Fig. 8.jpg|MAIZE STEM. Zea mais. Fibro-vascular bundle in section. × 110, typical of monocotyledonous structure}}

{{IMG:EB1911 - Fibres - Fig. 9.jpg|COTTON. FLAX. RAMIE. JUTE. Ultimate fibres in the length, × 110. Portions selected to show typical structural characteristics}}

{{IMG:EB1911 - Fibres - Fig. 10.jpg|COTTON. FLAX. RAMIE. JUTE. Ultimate fibres—transverse section, × 110. Note similarity of ramie to cotton and jute to flax}}

{{IMG:EB1911 - Fibres - Fig. 11.jpg|ESPARTO. Cellulose. Ultimate fibres of paper making pulp. Typical fusiform bast fibres. × 65}}

{{IMG:EB1911 - Fibres - Fig. 12.jpg|SECTION OF HAND-MADE PAPER. × 110. Ultimate component fibres disposed in every plane}}
```

### Current body
```
{{IMG:EB1911 - Fibres - Fig. 7.jpg|JUTE. Bast bundles. Section of bast region, × 235, showing agglomerated bundles of bast fibre, each bundle representing a spinning unit or filament}}

{{IMG:EB1911 - Fibres - Fig. 8.jpg|MAIZE STEM. Zea mais. Fibro-vascular bundle in section. × 110, typical of monocotyledonous structure}}

{{IMG:EB1911 - Fibres - Fig. 9.jpg|COTTON. FLAX. RAMIE. JUTE. Ultimate fibres in the length, × 110. Portions selected to show typical structural characteristics}}

{{IMG:EB1911 - Fibres - Fig. 10.jpg|COTTON. FLAX. RAMIE. JUTE. Ultimate fibres—transverse section, × 110. Note similarity of ramie to cotton and jute to flax}}

{{IMG:EB1911 - Fibres - Fig. 11.jpg|ESPARTO. Cellulose. Ultimate fibres of paper making pulp. Typical fusiform bast fibres. × 65}}

{{IMG:EB1911 - Fibres - Fig. 12.jpg|SECTION OF HAND-MADE PAPER. × 110. Ultimate component fibres disposed in every plane}}
```

---

## FIR, PLATE I — vol 10

**Article ID:** 4199105  
**Signature:** `html_table depth=0 wt=0 ht=multi has_colspan`

### Source excerpt
```
<table align=center>
<tr><td>[[File:EB1911 - Fir - Plate 1-seedA.jpg]]{{em|2}}</td>
<td>{{em|2}}[[File:EB1911 - Fir - Plate 1-seedB.jpg]]{{em|2}}</td>
<td>{{em|2}}[[File:EB1911 - Fir - Plate 1-seedC.jpg]]</td></tr>
</table>
<table  align=center>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 - Fir - Plate 1-picA.jpg]]</td>
<td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 - Fir - Plate 1-picB.jpg]]</td></tr>

<tr><td {{Ts|sm92|lh13|ac}}>SILVER FIR (''Abies pectinata'').<br />''A'', Cone and foliage.</td>
<td {{Ts|sm92|lh13|ac}}>SPRUCE FIR (''Picea excelsa'').<br />''B'', Cone and foliage.</td></tr>

<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 - Fir - Plate 1-picC.jpg]]</td>
<td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 - Fir - Plate 1-picD.jpg]]</td></tr>

<tr><td {{Ts|sm92|lh13|ac}}>HEMLOCK SPRUCE (''Tsuga canadensis'')<br />''C'', Cone, seed and foliage.</td>
<td {{Ts|sm92|lh13|ac}}>DOUGLAS FIR (''Pseudo-tsuga Douglasii'').<br />''D'', Cone, seed and foliage.</td></tr>

<tr><td {{Ts|pl.5|pr.5|vtp|ar|sm92}} colspan="2">''Photos by Henry Irving''.
</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 7 | 7 |
| captioned       | 5 | 5 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **14** | **14** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | 'Photos by Henry Irving' | 'Photos by Henry Irving' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Fir - Plate 1-seedA.jpg|SILVER FIR (Abies pectinata). A, Cone and foliage}}

{{IMG:EB1911 - Fir - Plate 1-seedB.jpg|SPRUCE FIR (Picea excelsa). B, Cone and foliage}}

{{IMG:EB1911 - Fir - Plate 1-seedC.jpg|HEMLOCK SPRUCE (Tsuga canadensis) C, Cone, seed and foliage}}

{{IMG:EB1911 - Fir - Plate 1-picA.jpg|DOUGLAS FIR (Pseudo-tsuga Douglasii). D, Cone, seed and foliage}}

{{IMG:EB1911 - Fir - Plate 1-picB.jpg|Photos by Henry Irving}}

{{IMG:EB1911 - Fir - Plate 1-picC.jpg}}

{{IMG:EB1911 - Fir - Plate 1-picD.jpg}}

Photos by Henry Irving
```

### Current body
```
{{IMG:EB1911 - Fir - Plate 1-seedA.jpg|SILVER FIR (Abies pectinata). A, Cone and foliage}}

{{IMG:EB1911 - Fir - Plate 1-seedB.jpg|SPRUCE FIR (Picea excelsa). B, Cone and foliage}}

{{IMG:EB1911 - Fir - Plate 1-seedC.jpg|HEMLOCK SPRUCE (Tsuga canadensis) C, Cone, seed and foliage}}

{{IMG:EB1911 - Fir - Plate 1-picA.jpg|DOUGLAS FIR (Pseudo-tsuga Douglasii). D, Cone, seed and foliage}}

{{IMG:EB1911 - Fir - Plate 1-picB.jpg|Photos by Henry Irving}}

{{IMG:EB1911 - Fir - Plate 1-picC.jpg}}

{{IMG:EB1911 - Fir - Plate 1-picD.jpg}}

Photos by Henry Irving
```

---

## FIR, PLATE II — vol 10

**Article ID:** 4199106  
**Signature:** `html_table depth=0 wt=0 ht=1 has_colspan`

### Source excerpt
```
<table align=center>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 - Fir - Plate 2-picA.jpg]]</td>
<td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 - Fir - Plate 2-seedAB.jpg]]</td>
<td {{Ts|ac|mc|ma|pt1}}>&nbsp;[[File:EB1911 - Fir - Plate 2-picB.jpg]]</td></tr>

<tr><td {{Ts|sm92|ac|pl1|pr1}}>CYPRESS (''Cupressus sempervirens'').
''A'', Cone and branchlets.</td>
<td>&nbsp;</td>
<td {{Ts|sm92|ac|pl1|pr1}}>JUNIPER (''Juniperus communis'').
''B'', Fruit and foliage.</td></tr>

<tr><td {{Ts|ac|mc|ma|pt1}} rowspan="2">[[File:EB1911 - Fir - Plate 2-picC.jpg]]</td>
<td {{Ts|ac|mc|ma|pt1}} colspan="2">[[File:EB1911 - Fir - Plate 2-seedCD.jpg]]</td></tr>

<tr><td {{Ts|ac|mc|ma|pt1}} colspan="2">[[File:EB1911 - Fir - Plate 2-picD.jpg]]</td></tr>

<tr><td {{Ts|sm92|ac|pl1|pr1}}>ARAUCARIA (''A. imbricata'', Chile pine or monkey-puzzle).<br/>''C'', Seed-bearing cone and a single scale with seed.</td>
<td {{Ts|sm92|ac|pl1|pr1}} colspan="2">YEW (''Taxus baccata'').<br/>''D'', Seed and foliage.</td></tr>

<tr><td {{Ts|pr.5|ar|sm92}} colspan="3">''Photos by Henry Irving''.
</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 6 | 6 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **12** | **12** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | 'YEW (Taxus baccata). D, Seed and foliage. Photos by Henry Irving' | 'YEW (Taxus baccata). D, Seed and foliage. Photos by Henry Irving' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Fir - Plate 2-picA.jpg|CYPRESS (Cupressus sempervirens). A, Cone and branchlets}}

{{IMG:EB1911 - Fir - Plate 2-seedAB.jpg|JUNIPER (Juniperus communis). B, Fruit and foliage}}

{{IMG:EB1911 - Fir - Plate 2-picB.jpg|ARAUCARIA (A. imbricata, Chile pine or monkey-puzzle). C, Seed-bearing cone and a single scale with seed}}

{{IMG:EB1911 - Fir - Plate 2-picC.jpg|Photos by Henry Irving}}

{{IMG:EB1911 - Fir - Plate 2-seedCD.jpg}}

{{IMG:EB1911 - Fir - Plate 2-picD.jpg}}

YEW (Taxus baccata). D, Seed and foliage. Photos by Henry Irving
```

### Current body
```
{{IMG:EB1911 - Fir - Plate 2-picA.jpg|CYPRESS (Cupressus sempervirens). A, Cone and branchlets}}

{{IMG:EB1911 - Fir - Plate 2-seedAB.jpg|JUNIPER (Juniperus communis). B, Fruit and foliage}}

{{IMG:EB1911 - Fir - Plate 2-picB.jpg|ARAUCARIA (A. imbricata, Chile pine or monkey-puzzle). C, Seed-bearing cone and a single scale with seed}}

{{IMG:EB1911 - Fir - Plate 2-picC.jpg|Photos by Henry Irving}}

{{IMG:EB1911 - Fir - Plate 2-seedCD.jpg}}

{{IMG:EB1911 - Fir - Plate 2-picD.jpg}}

YEW (Taxus baccata). D, Seed and foliage. Photos by Henry Irving
```

---

## FLAGS, PLATE I — vol 10

**Article ID:** 4199188  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{| align=center
|[[File:EB1911 Flag Plate I.png]]
|-
|{{Ts|ar}}|<small>''Niagra Litho. Co., Buffalo, N.Y.''&nbsp;</small>
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **2** | **2** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Flag Plate I.png|Niagra Litho. Co., Buffalo, N.Y}}
```

### Current body
```
{{IMG:EB1911 Flag Plate I.png|Niagra Litho. Co., Buffalo, N.Y}}
```

---

## FLAGS, PLATE II — vol 10

**Article ID:** 4199189  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{| align=center
|[[File:EB1911 Flag Plate II.png]]
|-
|{{Ts|ar}}|<small>''Niagra Litho. Co., Buffalo, N.Y.''&nbsp;</small>
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **2** | **2** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Flag Plate II.png|Niagra Litho. Co., Buffalo, N.Y}}
```

### Current body
```
{{IMG:EB1911 Flag Plate II.png|Niagra Litho. Co., Buffalo, N.Y}}
```

---

## FLIGHT AND FLYING, PLATE I — vol 10

**Article ID:** 4199259  
**Signature:** `html_table depth=0 wt=0 ht=1`

### Source excerpt
```
<table align=center>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 - Flight - Plate1-1.png]]</td></tr>
<tr><td {{Ts|sm85|lh11|ar}}>''Photo'', ''Topical Press.''</td></tr>
<tr><td {{Ts|sm92|lh12|ac}}>{{sc|Fig.}} 1.—PAULHAN FLYING ON FARMAN BIPLANE.</td></tr>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 - Flight - Plate1-2.png]]</td></tr>
<tr><td {{Ts|sm85|lh11|ar}}>''Photo'', ''Topical Press.''</td></tr>
<tr><td {{Ts|sm92|lh12|ac}}>{{sc|Fig.}} 2.—WRIGHT BIPLANE.</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Flight - Plate1-1.png|PAULHAN FLYING ON FARMAN BIPLANE (Photo, Topical Press)}}

{{IMG:EB1911 - Flight - Plate1-2.png|WRIGHT BIPLANE (Photo, Topical Press)}}
```

### Current body
```
{{IMG:EB1911 - Flight - Plate1-1.png|PAULHAN FLYING ON FARMAN BIPLANE (Photo, Topical Press)}}

{{IMG:EB1911 - Flight - Plate1-2.png|WRIGHT BIPLANE (Photo, Topical Press)}}
```

---

## FLIGHT AND FLYING — vol 10

**Article ID:** 4199260  
**Signature:** `html_table depth=0 wt=0 ht=1`

### Source excerpt
```
<table align=center>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 - Flight - Plate2-3.png]]</td></tr>
<tr><td {{Ts|sm85|lh11|ar}}>''Photo'', ''Topical Press.''</td></tr>
<tr><td {{Ts|sm92|ac}}>{{sc|Fig.}} 3.—BLERIOT MONOPLANE.</td></tr>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 - Flight - Plate2-4.png]]</td></tr>
<tr><td {{Ts|sm85|lh11|ar}}>''Photo'', ''Topical Press.''</td></tr>
<tr><td {{Ts|sm92|ac}}>{{sc|Fig.}} 4.—A. V. ROE’S TRIPLANE.</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Flight - Plate2-3.png|BLERIOT MONOPLANE (Photo, Topical Press)}}

{{IMG:EB1911 - Flight - Plate2-4.png|A. V. ROE’S TRIPLANE (Photo, Topical Press)}}
```

### Current body
```
{{IMG:EB1911 - Flight - Plate2-3.png|BLERIOT MONOPLANE (Photo, Topical Press)}}

{{IMG:EB1911 - Flight - Plate2-4.png|A. V. ROE’S TRIPLANE (Photo, Topical Press)}}
```

---

## FORAMINIFERA — vol 10

**Article ID:** 4199412  
**Signature:** `wikitable depth=1 wt=multi ht=0`

### Source excerpt
```
{{EB1911 fine print/s}}
{|align="center"
|[[Image:EB1911 Foraminifera - Imperforata.jpg|400px]]
|-
|align="center"|{{sc|Fig.}} 22.—Imperforata.
|-
|width="400"|
''&ensp;1'', ''Spiroloculina planulata'', Lamarck, showing five “coils”; porcellanous.

''&ensp;2'', Young ditto, with shell dissolved and protoplasm stained so as to show the seven
nuclei ''n''.

''&ensp;3'', ''Spirolina'' (''Peneroplis''); a sculptured imperfectly coiled shell; porcellanous.

''&ensp;4'', ''Vertebralina'', a simple shell consisting of chambers succeeding one another in a
straight line; porcellanous.

''&ensp;5, 6'', ''Thurammina papillata'', Brady, a sandy form. 5 is broken open so as to show
an inner chamber; recent. × 25.

''&ensp;7'', ''Haplophragmium canariensis'', a sandy form; recent.

''&ensp;8'', Nucleated reproductive bodies (bud-spores) of ''Haliphysema''.

''&ensp;9'', ''Squamulina laevis'', M. Schultze; × 40; a simple porcellanous Miliolide.

''10'', Protoplasmic core removed after treatment with weak chromic acid from the shell
of ''Haliphysema tumanovitzii'', Bow. n, Vesicular nuclei, stained with haematoxylin.
(After Lankester.)

''11'', ''Haliphysema tumanovitzii''; × 25 diam.; living specimen, showing the wine-glass-shaped
shell built up of sand-grains and sponge-spicules, and the abundant protoplasm
p, issuing from the mouth of the shell and spreading partly over its projecting
constituents.

''12'', Shell of ''Astrorhiza limicola'', Sand.; × {{sm|{{sfrac|3|2}}}}; showing the branc
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 2 | 2 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Foraminifera - Imperforata.jpg|Imperforata}}

{{IMG:EB1911 Foraminifera - Perforata.jpg|Perforata}}

{{LEGEND:Mediterranean. Example of a branched adherent calcareous perforate Recticularian}LEGEND}

{{LEGEND:Tertiary, Sicily. Shell dissected so as to show the spiral arrangement of the chambers, and the copious secondary shell substance. a², a³, a4, Chambers of three successive coils in section, showing the thin primary wall (finely tubulate) of each; b, b, b, b, perforate surfaces of the primary wall of four tiers of chambers, from which the secondary shell substance has been cleared away; c′, c′, secondary or intermediate shell substance in section, showing coarse canals; d, section of secondary shell substance at right angles to c′; e, tubercles of secondary shell substance on the surface; f, f, club-like processes of secondary shell substance}LEGEND}
```

### Current body
```
{{IMG:EB1911 Foraminifera - Imperforata.jpg|Imperforata}}

{{IMG:EB1911 Foraminifera - Perforata.jpg|Perforata}}

{{LEGEND:Mediterranean. Example of a branched adherent calcareous perforate Recticularian}LEGEND}

{{LEGEND:Tertiary, Sicily. Shell dissected so as to show the spiral arrangement of the chambers, and the copious secondary shell substance. a², a³, a4, Chambers of three successive coils in section, showing the thin primary wall (finely tubulate) of each; b, b, b, b, perforate surfaces of the primary wall of four tiers of chambers, from which the secondary shell substance has been cleared away; c′, c′, secondary or intermediate shell substance in section, showing coarse canals; d, section of secondary shell substance at right angles to c′; e, tubercles of secondary shell substance on the surface; f, f, club-like processes of secondary shell substance}LEGEND}
```

---

## FURNITURE, PLATE I — vol 11

**Article ID:** 4247734  
**Signature:** `html_table depth=0 wt=0 ht=multi`

### Source excerpt
```
<table {{Ts|ma|sm92|lh12|ac}}>
<tr><td>
<table style="clear: both;">
<tr><td {{Ts|mc|ma|pt1}}>[[File:EB1911 Furniture Fig. 1.—Venetian Folding Chair, walnut, c. 1530.jpg]]</td>
<td {{Ts|mc|ma|pt1}}>[[File:EB1911 Furniture Fig. 2.—Oak Arm-chair. English, 17th century.jpg]]</td>
<td {{Ts|mc|ma|pt1}}>[[File:EB1911 Furniture Fig. 3.—Arm-chair, solid seat, cane back; about 1660.jpg]]</td>
<td {{Ts|mc|ma|pt1}}>[[File:EB1911 Furniture Fig. 4.—Arm-chair, stuffed back and seat; about 1650.jpg]]</td></tr>
<tr><td {{Ts|pl1|pr1}}>{{sc|Fig. 1.}}—Venetian Folding Chair of<br>carved and gilt walnut, leather<br>back and seat; about 1530.</td>
<td {{Ts|pl15|pr15|vtp}}>{{sc|Fig. 2.}}—Oak Arm-chair. English,<br>17th century.</td>
<td {{Ts|pl15|pr15|vtp}}>{{sc|Fig. 3.}}—Arm-chair, solid seat, cane<br>back; about 1660.</td>
<td {{Ts|pl1|pr1|vtp}}>{{sc|Fig. 4.}}—Arm-chair, stuffed back and<br>seat; about 1650.</td></tr></table></td></tr>

<tr><td>
<table style="clear: both;">
<tr><td {{Ts|mc|ma|pt1}}>[[File:EB1911 Furniture Fig. 5.—Painted and carved High-Back Chair; about 1660.jpg]]</td>
<td {{Ts|mc|ma|pt1|pl4|pr5}}>[[File:EB1911 Furniture Fig. 6.—Carved Walnut Chairs. English, early 18th century. The arm-chair is inlaid.jpg]]</td>
<td {{Ts|mc|ma|pt1|pl1}}>[[File:EB1911 Furniture Fig. 7.—Walnut Chair; about 1710.jpg]]</td></tr>
<tr><td {{Ts|pl1|pr1}}>{{sc|Fig. 5.}}—Painted and carved High-<br>Back Chair; about 1660.</td>
<td>{{sc|Fig. 6.}}—Carved Walnut Chairs. English, early 18th century.<br>The
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 15 | 15 |
| captioned       | 15 | 15 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **30** | **30** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Furniture Fig. 1.—Venetian Folding Chair, walnut, c. 1530.jpg|Venetian Folding Chair of carved and gilt walnut, leather back and seat; about 1530}}

{{IMG:EB1911 Furniture Fig. 2.—Oak Arm-chair. English, 17th century.jpg|Oak Arm-chair. English, 17th century}}

{{IMG:EB1911 Furniture Fig. 3.—Arm-chair, solid seat, cane back; about 1660.jpg|Arm-chair, solid seat, cane back; about 1660}}

{{IMG:EB1911 Furniture Fig. 4.—Arm-chair, stuffed back and seat; about 1650.jpg|Arm-chair, stuffed back and seat; about 1650}}

{{IMG:EB1911 Furniture Fig. 5.—Painted and carved High-Back Chair; about 1660.jpg|Painted and carved High- Back Chair; about 1660}}

{{IMG:EB1911 Furniture Fig. 6.—Carved Walnut Chairs. English, early 18th century. The arm-chair is inlaid.jpg|Carved Walnut Chairs. English, early 18th century. The arm-chair is inlaid}}

{{IMG:EB1911 Furniture Fig. 7.—Walnut Chair; about 1710.jpg|Walnut Chair; about 1710}}

{{IMG:EB1911 Furniture Fig. 8.—Carved Mahogany Chair in the style of Chippendale; 2nd half of 18th century.jpg|Carved Mahogany Chair in the style of Chippendale; 2nd half of 18th century}}

{{IMG:EB1911 Furniture Fig. 9.—Carved Mahogany Arm-chair, in the style of Chippendale, with ribbon pattern.jpg|Carved Mahogany Arm-chair, in the style of Chippendale, with ribbon pattern}}

{{IMG:EB1911 Furniture Fig. 10.—Carved and Inlaid Mahogany Chair, in the style of Hepplewhite; late 18th century.jpg|Carved and Inlaid Mahogany Chair, in the style of Hepplewhite; late 18th century}}

{{IMG:EB1911 Furniture Fig. 11.—Mahogany Chair in the style of Sheraton; about 1780.jpg|Mahogany Chair in the style of Sheraton; about 1780}}

{{IMG:EB1911 Furniture Fig. 12.—Painted and gilt Arm-chair with cane seat, in the style of Adam; about 1790.jpg|Painted and gilt Arm-chair with cane seat, in the style of Adam; about 1790}}

{{IMG:EB1911 Furniture Fig. 13.—Arm-chair of carved and gilt wood.jpg|Arm-chair of carved and gilt wood with stuffed back, seat and arms. French, Louis XV. style}}

{{IMG:EB1911 Furniture Fig. 14.—Mahogany Arm-chair. Empire style.jpg|Mahogany Arm-chair. Empire style, early 19th century, said to have belonged to the Bonaparte family}}

{{IMG:EB1911 Furniture Fig. 15.—Painted and gilt Beech Chair. English, about 1800.jpg|Painted and gilt Beech Chair. English, about 1800}}
```

### Current body
```
{{IMG:EB1911 Furniture Fig. 1.—Venetian Folding Chair, walnut, c. 1530.jpg|Venetian Folding Chair of carved and gilt walnut, leather back and seat; about 1530}}

{{IMG:EB1911 Furniture Fig. 2.—Oak Arm-chair. English, 17th century.jpg|Oak Arm-chair. English, 17th century}}

{{IMG:EB1911 Furniture Fig. 3.—Arm-chair, solid seat, cane back; about 1660.jpg|Arm-chair, solid seat, cane back; about 1660}}

{{IMG:EB1911 Furniture Fig. 4.—Arm-chair, stuffed back and seat; about 1650.jpg|Arm-chair, stuffed back and seat; about 1650}}

{{IMG:EB1911 Furniture Fig. 5.—Painted and carved High-Back Chair; about 1660.jpg|Painted and carved High- Back Chair; about 1660}}

{{IMG:EB1911 Furniture Fig. 6.—Carved Walnut Chairs. English, early 18th century. The arm-chair is inlaid.jpg|Carved Walnut Chairs. English, early 18th century. The arm-chair is inlaid}}

{{IMG:EB1911 Furniture Fig. 7.—Walnut Chair; about 1710.jpg|Walnut Chair; about 1710}}

{{IMG:EB1911 Furniture Fig. 8.—Carved Mahogany Chair in the style of Chippendale; 2nd half of 18th century.jpg|Carved Mahogany Chair in the style of Chippendale; 2nd half of 18th century}}

{{IMG:EB1911 Furniture Fig. 9.—Carved Mahogany Arm-chair, in the style of Chippendale, with ribbon pattern.jpg|Carved Mahogany Arm-chair, in the style of Chippendale, with ribbon pattern}}

{{IMG:EB1911 Furniture Fig. 10.—Carved and Inlaid Mahogany Chair, in the style of Hepplewhite; late 18th century.jpg|Carved and Inlaid Mahogany Chair, in the style of Hepplewhite; late 18th century}}

{{IMG:EB1911 Furniture Fig. 11.—Mahogany Chair in the style of Sheraton; about 1780.jpg|Mahogany Chair in the style of Sheraton; about 1780}}

{{IMG:EB1911 Furniture Fig. 12.—Painted and gilt Arm-chair with cane seat, in the style of Adam; about 1790.jpg|Painted and gilt Arm-chair with cane seat, in the style of Adam; about 1790}}

{{IMG:EB1911 Furniture Fig. 13.—Arm-chair of carved and gilt wood.jpg|Arm-chair of carved and gilt wood with stuffed back, seat and arms. French, Louis XV. style}}

{{IMG:EB1911 Furniture Fig. 14.—Mahogany Arm-chair. Empire style.jpg|Mahogany Arm-chair. Empire style, early 19th century, said to have belonged to the Bonaparte family}}

{{IMG:EB1911 Furniture Fig. 15.—Painted and gilt Beech Chair. English, about 1800.jpg|Painted and gilt Beech Chair. English, about 1800}}
```

---

## FURNITURE, PLATE II — vol 11

**Article ID:** 4247735  
**Signature:** `html_table depth=0 wt=0 ht=multi has_colspan`

### Source excerpt
```
<table {{Ts|ma|sm92|lh12|ac}}>
<tr><td>
<table style="clear: both;">
<tr><td {{Ts|pt1}}>[[File:EB1911 Furniture Plate II Fig. 1.—Front of Oak Coffer.jpg]]</td>
<td {{Ts|pt1|pl15}}>[[File:EB1911 Furniture Plate II Fig. 2.—English Oak Chest.jpg]]</td></tr>
<tr><td>{{sc|Fig. 1.}}—Front of Oak Coffer with wrought iron bands.<br>French, 2nd half of 13th century.</td>
<td>&emsp; {{sc|Fig. 2.}}—English Oak Chest, dated 1637.</td></tr></table></td></tr>

<tr><td>
<table>
<tr><td {{Ts|mc|ma|pt1}}>[[File:EB1911 Furniture Plate II Fig. 3.—Italian (Florentine) Coffer of Wood.jpg]]</td>
<td {{Ts|mc|ma|pt1|pl15}}>[[File:EB1911 Furniture Plate II Fig. 4.—Italian 'Cassone' or Marriage Coffer.jpg]]</td></tr>
<tr><td {{Ts|pl1|pr1}}>{{sc|Fig. 3.}}—Italian (Florentine) Coffer of Wood with gilt arabesque<br>stucco ornament, about 1480.</td>
<td>&emsp; {{sc|Fig. 4.}}—Italian “Cassone” or Marriage Coffer, 13th century.<br>Carved and gilt wood with painted front and ends.</td></tr></table></td></tr>

<tr><td>
<table>
<tr><td {{Ts|mc|ma|pt1}}>[[File:EB1911 Furniture Plate II Fig. 5.—Walnut Table with expanding leaves.jpg]]</td>
<td {{Ts|mc|ma|pt1|pl15}}>[[File:EB1911 Furniture Plate II Fig. 6.—Oak Gate-Legged Table.jpg]]</td></tr>
<tr><td>{{sc|Fig. 5.}}—Walnut Table with expanding leaves. Swiss, 17th century.</td>
<td>&emsp; {{sc|Fig. 6.}}—Oak Gate-Legged Table. English,<br>17th century.</td></tr></table></td></tr>

<tr><td>
<table>
<tr><td {{Ts|mc|ma|pt1}}>[[File:EB1911 Furniture Plate II Fig. 7.—Wr
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 8 | 8 |
| captioned       | 8 | 8 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **18** | **18** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | '(The above are in the Victoria and Albert Museum, except Fig. 8, which were in the Bethnal Green Exhibition, 1892.)' | '(The above are in the Victoria and Albert Museum, except Fig. 8, which were in the Bethnal Green Exhibition, 1892.)' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Furniture Plate II Fig. 1.—Front of Oak Coffer.jpg|Front of Oak Coffer with wrought iron bands. French, 2nd half of 13th century}}

{{IMG:EB1911 Furniture Plate II Fig. 2.—English Oak Chest.jpg|English Oak Chest, dated 1637}}

{{IMG:EB1911 Furniture Plate II Fig. 3.—Italian (Florentine) Coffer of Wood.jpg|Italian (Florentine) Coffer of Wood with gilt arabesque stucco ornament, about 1480}}

{{IMG:EB1911 Furniture Plate II Fig. 4.—Italian 'Cassone' or Marriage Coffer.jpg|Italian “Cassone” or Marriage Coffer, 13th century. Carved and gilt wood with painted front and ends}}

{{IMG:EB1911 Furniture Plate II Fig. 5.—Walnut Table with expanding leaves.jpg|Walnut Table with expanding leaves. Swiss, 17th century}}

{{IMG:EB1911 Furniture Plate II Fig. 6.—Oak Gate-Legged Table.jpg|Oak Gate-Legged Table. English, 17th century}}

{{IMG:EB1911 Furniture Plate II Fig. 7.—Writing Table. French.jpg|Writing Table. French, end of Louis XV. period. Riesener marquetry, ormolu mounts and Sèvres plaques}}

{{IMG:EB1911 Furniture Plate II Fig. 8.—Painted Satin-Wood Tables.jpg|Painted Satin-Wood Tables, in the style of Sheraton, about 1790}}

(The above are in the Victoria and Albert Museum, except Fig. 8, which were in the Bethnal Green Exhibition, 1892.)
```

### Current body
```
{{IMG:EB1911 Furniture Plate II Fig. 1.—Front of Oak Coffer.jpg|Front of Oak Coffer with wrought iron bands. French, 2nd half of 13th century}}

{{IMG:EB1911 Furniture Plate II Fig. 2.—English Oak Chest.jpg|English Oak Chest, dated 1637}}

{{IMG:EB1911 Furniture Plate II Fig. 3.—Italian (Florentine) Coffer of Wood.jpg|Italian (Florentine) Coffer of Wood with gilt arabesque stucco ornament, about 1480}}

{{IMG:EB1911 Furniture Plate II Fig. 4.—Italian 'Cassone' or Marriage Coffer.jpg|Italian “Cassone” or Marriage Coffer, 13th century. Carved and gilt wood with painted front and ends}}

{{IMG:EB1911 Furniture Plate II Fig. 5.—Walnut Table with expanding leaves.jpg|Walnut Table with expanding leaves. Swiss, 17th century}}

{{IMG:EB1911 Furniture Plate II Fig. 6.—Oak Gate-Legged Table.jpg|Oak Gate-Legged Table. English, 17th century}}

{{IMG:EB1911 Furniture Plate II Fig. 7.—Writing Table. French.jpg|Writing Table. French, end of Louis XV. period. Riesener marquetry, ormolu mounts and Sèvres plaques}}

{{IMG:EB1911 Furniture Plate II Fig. 8.—Painted Satin-Wood Tables.jpg|Painted Satin-Wood Tables, in the style of Sheraton, about 1790}}

(The above are in the Victoria and Albert Museum, except Fig. 8, which were in the Bethnal Green Exhibition, 1892.)
```

---

## FURNITURE, PLATE III — vol 11

**Article ID:** 4247736  
**Signature:** `html_table depth=0 wt=0 ht=multi`

### Source excerpt
```
<table {{Ts|ma|sm92|lh12|ac}}>
<tr><td>
<table>
<tr><td {{Ts|pt1}}>[[File:EB1911 Furniture Plate III 1. CARVED OAK SIDEBOARD.jpg]]</td>
<td {{Ts|mc|ma|pt1|pl1}}>[[File:EB1911 Furniture Plate III 2. CARVED OAK COURT CUPBOARD.jpg]]</td></tr>
<tr><td {{Ts|pl1|pr1}}>1. CARVED OAK SIDEBOARD. English,<br>17th century. Victoria and Albert Museum.</td>
<td {{Ts|pl2}}>2. CARVED OAK COURT CUPBOARD. English, early 17th<br>century. Victoria and Albert Museum.</td></tr></table></td></tr>
<tr><td>
<table>
<tr><td {{Ts|pt1}}>[[File:EB1911 Furniture Plate III 3. EBONY CARVED CABINET.jpg]]</td>
<td {{Ts|pl1|vbm}}>[[File:EB1911 Furniture Plate III 4. VENEERED CHEST OF DRAWERS.jpg]]</td></tr>
<tr><td {{Ts|al|pl.5|pr1|width:335px}}>3. EBONY CARVED CABINET. The interior decorated with inlaid ivory and coloured woods; French or Dutch, middle of 17th century. Victoria and Albert Museum.</td>
<td {{Ts|al|pl3|width:270px}}>4. VENEERED CHEST OF DRAWERS. About 1690. Lent to Bethnal Green Exhibition by Sir Spencer Ponsonby-Fane, G.C.B.</td></tr></table></td></tr>
<tr><td>
<table>
<tr><td {{Ts|mc|ma|pt1}}>[[File:EB1911 Furniture Plate III 5. EBONY ARMOIRE.jpg]]</td>
<td {{Ts|mc|ma|pt1|pl15}}>[[File:EB1911 Furniture Plate III 6. GLASS-FRONTED BOOKCASE AND CABINET.jpg]]</td></tr>
<tr><td {{Ts|pl1|al|width:290px}}>5. EBONY ARMOIRE. With tortoise-shell panels inlaid with brass and other metals, and ormolu mountings. Designed by Bérain, and executed by André Boulle. French, Louis XIV. period.<br>Victoria and 
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 6 | 6 |
| captioned       | 6 | 6 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **12** | **12** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Furniture Plate III 1. CARVED OAK SIDEBOARD.jpg|1. CARVED OAK SIDEBOARD. English, 17th century. Victoria and Albert Museum}}

{{IMG:EB1911 Furniture Plate III 2. CARVED OAK COURT CUPBOARD.jpg|2. CARVED OAK COURT CUPBOARD. English, early 17th century. Victoria and Albert Museum}}

{{IMG:EB1911 Furniture Plate III 3. EBONY CARVED CABINET.jpg|3. EBONY CARVED CABINET. The interior decorated with inlaid ivory and coloured woods; French or Dutch, middle of 17th century. Victoria and Albert Museum}}

{{IMG:EB1911 Furniture Plate III 4. VENEERED CHEST OF DRAWERS.jpg|Lent to Bethnal Green Exhibition by Sir Spencer Ponsonby-Fane, G.C.B}}

{{IMG:EB1911 Furniture Plate III 5. EBONY ARMOIRE.jpg|5. EBONY ARMOIRE. With tortoise-shell panels inlaid with brass and other metals, and ormolu mountings. Designed by Bérain, and executed by André Boulle. French, Louis XIV. period. Victoria and Albert Museum}}

{{IMG:EB1911 Furniture Plate III 6. GLASS-FRONTED BOOKCASE AND CABINET.jpg|Lent to the Bethnal Green Exhibition by the late Vincent J. Robinson, C.I.E}}
```

### Current body
```
{{IMG:EB1911 Furniture Plate III 1. CARVED OAK SIDEBOARD.jpg|1. CARVED OAK SIDEBOARD. English, 17th century. Victoria and Albert Museum}}

{{IMG:EB1911 Furniture Plate III 2. CARVED OAK COURT CUPBOARD.jpg|2. CARVED OAK COURT CUPBOARD. English, early 17th century. Victoria and Albert Museum}}

{{IMG:EB1911 Furniture Plate III 3. EBONY CARVED CABINET.jpg|3. EBONY CARVED CABINET. The interior decorated with inlaid ivory and coloured woods; French or Dutch, middle of 17th century. Victoria and Albert Museum}}

{{IMG:EB1911 Furniture Plate III 4. VENEERED CHEST OF DRAWERS.jpg|Lent to Bethnal Green Exhibition by Sir Spencer Ponsonby-Fane, G.C.B}}

{{IMG:EB1911 Furniture Plate III 5. EBONY ARMOIRE.jpg|5. EBONY ARMOIRE. With tortoise-shell panels inlaid with brass and other metals, and ormolu mountings. Designed by Bérain, and executed by André Boulle. French, Louis XIV. period. Victoria and Albert Museum}}

{{IMG:EB1911 Furniture Plate III 6. GLASS-FRONTED BOOKCASE AND CABINET.jpg|Lent to the Bethnal Green Exhibition by the late Vincent J. Robinson, C.I.E}}
```

---

## FURNITURE, PLATE IV — vol 11

**Article ID:** 4247737  
**Signature:** `html_table depth=0 wt=0 ht=multi has_colspan`

### Source excerpt
```
<table {{Ts|ma|sm92|lh12|ac}}>
<tr><td>
<table>
<tr><td {{Ts|mc|ma|pt1}}>[[File:EB1911 Furniture Plate IV 1. COMMODE OF PINE.jpg]]</td>
<td {{Ts|mc|ma|pt1|pl2}}>[[File:EB1911 Furniture Plate IV 2. COMMODE.jpg]]</td></tr>
<tr><td {{Ts|al|width:370px}}>1. COMMODE OF PINE. With marquetry of brass, ebony, tortoise-shell,
mother-of-pearl, ivory, and green-stained bone. “Boulle” work with designs in the style of Bérain. French, late period of Louis XIV.</td>
<td {{Ts|al|pl3|width:360px}}>2. COMMODE. With panels of Japanese lacquer and ormolu mountings, in the style of Caffieri. French, Louis XV. period.</td></tr></table></td></tr>

<tr><td>
<table>
<tr><td {{Ts|mc|ma|pt1|pl2}}>[[File:EB1911 Furniture Plate IV 3. TABLE OF KING AND TULIP WOODS.jpg|EB1911 Furniture Plate IV 3. TABLE OF KING AND TULIP WOODS.jpg]]</td>
<td {{Ts|mc|ma|pt1|pl5}}>[[File:EB1911 Furniture Plate IV 4. ESCRITOIRE À TOILETTE.jpg]]</td></tr>
<tr><td {{Ts|al|pl2|width:250px|vtp}}>3. TABLE OF KING AND TULIP WOODS. With ormolu mountings. Louis XV. period.</td>
<td {{Ts|pl5|al|width:340px}}>4. ESCRITOIRE À TOILETTE. Formerly belonging to Marie Antoinette. Of tulip and sycamore woods inlaid with other coloured woods, ormolu mounts. Louis XV. period.</td></tr></table></td></tr>

<tr><td>
<table>
<tr><td {{Ts|mc|ma|pt1}}>[[File:EB1911 Furniture Plate IV 5. FOUR-POST BEDSTEAD.jpg]]</td>
<td {{Ts|mc|ma|pt1|pl3}}>[[File:EB1911 Furniture Plate IV 6. CARVED AND GILT BEDSTEAD.jpg]]</td></tr>
<tr><td {{Ts|width:320px}}>5. FOU
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 6 | 6 |
| captioned       | 6 | 6 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **14** | **14** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | 'From the Victoria and Albert Museum, S. Kensington' | 'From the Victoria and Albert Museum, S. Kensington' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Furniture Plate IV 1. COMMODE OF PINE.jpg|1. COMMODE OF PINE. With marquetry of brass, ebony, tortoise-shell, mother-of-pearl, ivory, and green-stained bone. “Boulle” work with designs in the style of Bérain. French, late period of Louis XIV}}

{{IMG:EB1911 Furniture Plate IV 2. COMMODE.jpg|2. COMMODE. With panels of Japanese lacquer and ormolu mountings, in the style of Caffieri. French, Louis XV. period}}

{{IMG:EB1911 Furniture Plate IV 3. TABLE OF KING AND TULIP WOODS.jpg|3. TABLE OF KING AND TULIP WOODS. With ormolu mountings. Louis XV. period}}

{{IMG:EB1911 Furniture Plate IV 4. ESCRITOIRE À TOILETTE.jpg|4. ESCRITOIRE À TOILETTE. Formerly belonging to Marie Antoinette. Of tulip and sycamore woods inlaid with other coloured woods, ormolu mounts. Louis XV. period}}

{{IMG:EB1911 Furniture Plate IV 5. FOUR-POST BEDSTEAD.jpg|5. FOUR-POST BEDSTEAD. Of oak inlaid with bog-oak and holly, from the “Inlaid Room” at Sizergh Castle, Westmorland. Latter half of sixteenth century}}

{{IMG:EB1911 Furniture Plate IV 6. CARVED AND GILT BEDSTEAD.jpg|6. CARVED AND GILT BEDSTEAD. With blue silk damask coverings and hangings. French, late 18th century. Louis XVI. period}}

From the Victoria and Albert Museum, S. Kensington
```

### Current body
```
{{IMG:EB1911 Furniture Plate IV 1. COMMODE OF PINE.jpg|1. COMMODE OF PINE. With marquetry of brass, ebony, tortoise-shell, mother-of-pearl, ivory, and green-stained bone. “Boulle” work with designs in the style of Bérain. French, late period of Louis XIV}}

{{IMG:EB1911 Furniture Plate IV 2. COMMODE.jpg|2. COMMODE. With panels of Japanese lacquer and ormolu mountings, in the style of Caffieri. French, Louis XV. period}}

{{IMG:EB1911 Furniture Plate IV 3. TABLE OF KING AND TULIP WOODS.jpg|3. TABLE OF KING AND TULIP WOODS. With ormolu mountings. Louis XV. period}}

{{IMG:EB1911 Furniture Plate IV 4. ESCRITOIRE À TOILETTE.jpg|4. ESCRITOIRE À TOILETTE. Formerly belonging to Marie Antoinette. Of tulip and sycamore woods inlaid with other coloured woods, ormolu mounts. Louis XV. period}}

{{IMG:EB1911 Furniture Plate IV 5. FOUR-POST BEDSTEAD.jpg|5. FOUR-POST BEDSTEAD. Of oak inlaid with bog-oak and holly, from the “Inlaid Room” at Sizergh Castle, Westmorland. Latter half of sixteenth century}}

{{IMG:EB1911 Furniture Plate IV 6. CARVED AND GILT BEDSTEAD.jpg|6. CARVED AND GILT BEDSTEAD. With blue silk damask coverings and hangings. French, late 18th century. Louis XVI. period}}

From the Victoria and Albert Museum, S. Kensington
```

---

## FURNITURE, PLATE V — vol 11

**Article ID:** 4247738  
**Signature:** `html_table depth=0 wt=0 ht=1`

### Source excerpt
```
<table align=center>
<tr><td {{Ts|ac|pt1}}>[[File:EB1911 - Furniture - Plate V-1.png|584px]]</td></tr>
<tr><td {{Ts|ac|pt15}}>[[File:EB1911 - Furniture - Plate V-2.png|584px]]</td></tr>
<tr><td {{Ts|pl1|sm|lh11}}>''Photo'', ''Mansell & Co.''</td></tr>
<tr><td {{Ts|sm92|ac}}>THE “BUREAU DU ROI,” MADE FOR LOUIS XV., NOW IN THE LOUVRE. For description, see {{EB1911 article link|Desk}}.</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Furniture - Plate V-1.png|THE “BUREAU DU ROI,” MADE FOR LOUIS XV., NOW IN THE LOUVRE. For description, see Desk}}

{{IMG:EB1911 - Furniture - Plate V-2.png|Photo, Mansell & Co}}
```

### Current body
```
{{IMG:EB1911 - Furniture - Plate V-1.png|THE “BUREAU DU ROI,” MADE FOR LOUIS XV., NOW IN THE LOUVRE. For description, see Desk}}

{{IMG:EB1911 - Furniture - Plate V-2.png|Photo, Mansell & Co}}
```

---

## GEMS, PLATE I — vol 11

**Article ID:** 4248110  
**Signature:** `other depth=0 wt=0 ht=0`

### Source excerpt
```
<div align=center {{Ts|pt1}}>[[File:EB1911 Gem - Plate I.jpg]]</div>
{{EB1911 fine print/s}}
1–5.—ORIENTAL.<br />
{{gap}}1. Babylonian (late Sumerian) Cylinder of a Viceroy of Ur-Gur (or Ur-Engur), 2500 {{asc|B.C.}}<br />
{{gap}}2. Assyrian Cylinder. Woman adoring Goddess.<br />
{{gap}}3. Assyrian Cylinder. Assur worshipped by two Assyrian kings, and divine Attendants.<br />
{{gap}}4. Persian Seal of Darius (500 {{asc|B.C.}}). Lion Hunt.<br />
{{gap}}5. Graeco-Persian Scarabaeoid. Boar Hunt.
{{EB1911 fine print/e}}

6–15.—CRETAN AND MYCENAEAN INTAGLIOS.<br />
{{EB1911 fine print/s}}
{{gap}}6. Cretan Symbols.<br />
{{gap}}7. Man and Bull. Crete.<br />
{{gap}}8. Lions and Column. Ialysus.<br />
{{gap}}9. Daemon. Crete.<br />
{{gap}}10. Lioness and Deer.<br />
{{gap}}11-13. Three-sided Stone. Peloponnesus.<br />
{{gap}}14. Man and Bull. Crete.<br />
{{gap}}15. Bull and Palm. Ialysus.
{{EB1911 fine print/e}}

16–18.—GEMS OF THE ISLANDS.<br />
{{EB1911 fine print/s}}
{{em|2}}16. Goddess on Waves. Birds.<br />
{{em|2}}17. Lion and Goat.<br />
{{em|2}}18. Heracles and Nereus.<br />
{{EB1911 fine print/e}}
{{em|1.7}}19.—PHOENICIAN SEAL, inscribed.

20–26.—GRAECO-PHOENICIAN SCARABS FROM THARROS.<br />
{{EB1911 fine print/s}}
{{gap}}20. King, enthroned.<br />
{{gap}}21. Bes with Antelope and Hound.<br />
{{gap}}22. Bes with Lions.<br />
{{gap}}23. Warrior.<br />
{{gap}}24. Egyptian Device.<br />
{{gap}}25. Bes and Goats.<br />
{{gap}}26. Hawk of Horus.
{{EB1911 fine print/e}}
<div alig
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 4 | 4 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Gem - Plate I.jpg|Babylonian (late Sumerian) Cylinder of a Viceroy of Ur-Gur (or Ur-Engur), 2500 B.C. 2. Assyrian Cylinder. Woman adoring Goddess. 3. Assyrian Cylinder. Assur worshipped by two Assyrian kings, and divine Attendants. 4. Persian Seal of Darius (500 B.C.). Lion Hunt. 5. Graeco-Persian Scarabaeoid. Boar Hunt}}

{{LEGEND:Cretan Symbols. 7. Man and Bull. Crete. 8. Lions and Column. Ialysus. 9. Daemon. Crete. 10. Lioness and Deer. 11-13. Three-sided Stone. Peloponnesus. 14. Man and Bull. Crete. 15. Bull and Palm. Ialysus}LEGEND}

{{LEGEND:Goddess on Waves. Birds. 17. Lion and Goat. 18. Heracles and Nereus}LEGEND}

{{LEGEND:PHOENICIAN SEAL, inscribed}LEGEND}

{{LEGEND:King, enthroned. 21. Bes with Antelope and Hound. 22. Bes with Lions. 23. Warrior. 24. Egyptian Device. 25. Bes and Goats. 26. Hawk of Horus. All the above are in the British Museum}LEGEND}
```

### Current body
```
{{IMG:EB1911 Gem - Plate I.jpg|Babylonian (late Sumerian) Cylinder of a Viceroy of Ur-Gur (or Ur-Engur), 2500 B.C. 2. Assyrian Cylinder. Woman adoring Goddess. 3. Assyrian Cylinder. Assur worshipped by two Assyrian kings, and divine Attendants. 4. Persian Seal of Darius (500 B.C.). Lion Hunt. 5. Graeco-Persian Scarabaeoid. Boar Hunt}}

{{LEGEND:Cretan Symbols. 7. Man and Bull. Crete. 8. Lions and Column. Ialysus. 9. Daemon. Crete. 10. Lioness and Deer. 11-13. Three-sided Stone. Peloponnesus. 14. Man and Bull. Crete. 15. Bull and Palm. Ialysus}LEGEND}

{{LEGEND:Goddess on Waves. Birds. 17. Lion and Goat. 18. Heracles and Nereus}LEGEND}

{{LEGEND:PHOENICIAN SEAL, inscribed}LEGEND}

{{LEGEND:King, enthroned. 21. Bes with Antelope and Hound. 22. Bes with Lions. 23. Warrior. 24. Egyptian Device. 25. Bes and Goats. 26. Hawk of Horus. All the above are in the British Museum}LEGEND}
```

---

## GEMS, PLATE II — vol 11

**Article ID:** 4248111  
**Signature:** `html_table depth=0 wt=0 ht=1`

### Source excerpt
```
{{center|[[File:EB1911 Gem- Plate II.jpg]]}}
<table align=center {{Ts|bc}}><tr><td {{Ts|pl.5|pr.5|vtp|al}}>
<br />27–34.—EARLY GREEK SCARABS AND SCARABAEOIDS.<br />
{{EB1911 fine print/s}}
{{em|3}}27. Pluto and Persephone. (New York.)<br />
{{em|3}}28. Boreas and Oreithyia. (New York.)<br />
{{em|3}}29. Youth and Dog.<br />
{{em|3}}30. Archer feeling Arrow Tip. (Lord Southesk.)<br />
{{em|3}}31. Satyr and Wine Cup.<br />
{{em|3}}32. Archer and Dog.<br />
{{em|3}}33. Satyr with Wineskin.<br />
{{em|3}}34. Athena with Gorgon Spoils.
{{EB1911 fine print/e}}
<br />35–44.—FINEST GREEK SCARABS AND SCARABAEOIDS.<br />
{{EB1911 fine print/s}}
{{em|3}}35. Head of Young Warrior.<br />
{{em|3}}36. Lyre Player. (Cockerell Coll.)<br />
{{em|3}}37. Crane, with Deer’s Antler.<br />
{{em|3}}38. Head of Eos.<br />
{{em|3}}39. Lyre Player. (Woodhouse Coll. and B.M.)<br />
{{em|3}}40. Lyre Player, signed by Syries.<br />
{{em|3}}41. Stork and Grasshopper, signed by Dexamenos. (St. Petersburg.)<br />
{{em|3}}42. Flying Crane, signed by Dexamenos. (St. Petersburg.)<br />
{{em|3}}43. Flying Goose.<br />
{{em|3}}44. Lion and Stag.
{{EB1911 fine print/e}}
<br />45–54.—ETRUSCAN SCARABS.<br />
{{EB1911 fine print/s}}
{{em|3}}45. Achilles in Retirement.<br />
{{em|3}}46. Victory.<br />
{{em|3}}47. Capaneus struck by the Bolt.<br />
{{em|3}}48. Heracles.<br />
{{em|3}}49. Capaneus struck by the Bolt.<br />
{{em|3}}50. Achilles.<br />
{{em|3}}51. Heracles and Cycnus.<br />
{{em|3}}52. Heracles.<br />
{{e
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **5** | **5** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'center' | 'center' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
center

{{IMG:EB1911 Gem- Plate II.jpg|Pluto and Persephone. (New York.) 28. Boreas and Oreithyia. (New York.) 29. Youth and Dog. 30. Archer feeling Arrow Tip. (Lord Southesk.) 31. Satyr and Wine Cup. 32. Archer and Dog. 33. Satyr with Wineskin. 34. Athena with Gorgon Spoils. 35–44.—FINEST GREEK SCARABS AND SCARABAEOIDS. 35. Head of Young Warrior. 36. Lyre Player. (Cockerell Coll.) 37. Crane, with Deer’s Antler. 38. Head of Eos. 39. Lyre Player. (Woodhouse Coll. and B.M.) 40. Lyre Player, signed by Syries. 41. Stork and Grasshopper, signed by Dexamenos. (St. Petersburg.) 42. Flying Crane, signed by Dexamenos. (St. Petersburg.) 43. Flying Goose. 44. Lion and Stag. 45–54.—ETRUSCAN SCARABS. 45. Achilles in Retirement. 46. Victory. 47. Capaneus struck by the Bolt. 48. Heracles. 49. Capaneus struck by the Bolt. 50. Achilles. 51. Heracles and Cycnus. 52. Heracles. 53. Heracles and the Lion. 54. Machaon bandaging Philoctetes}}

{{LEGEND:Girl with Scroll and Lyre. 56. Girl with Water-Jar. 57. Head of Aristippus—Deities. 58–61.—SIGNED GEMS. 58. Asclepius of Aulos. 59. Citharist of Allion. 60. Medusa of Solon. 61. Heracles of Gnaios. 62–70.—ROMAN GEMS. 62. Portrait. 63. Head of Trajan Decius. 64. Ares and Aphrodite. 65. Jupiter of Heliopolis. 66. Artemis of Ephesus. 67. So-called Psyche. 68. So-called Psyche. 69. Minerva with Mask, Stamp for the Eye Balsam of Herophilus. 70. Helios. 71–72.—CHRISTIAN GEMS. 71. Crucifixion. 72. Good Shepherd. Jonah. 73–76.—EIGHTEENTH CENTURY GEMS. 73. Achilles of Pamphilus, copied from the antique. 74. Eros and Psyche, by Pichler. 75. Head of Athena. 76. Athena, from Townley Bust by Marchant}LEGEND}
```

### Current body
```
center

{{IMG:EB1911 Gem- Plate II.jpg|Pluto and Persephone. (New York.) 28. Boreas and Oreithyia. (New York.) 29. Youth and Dog. 30. Archer feeling Arrow Tip. (Lord Southesk.) 31. Satyr and Wine Cup. 32. Archer and Dog. 33. Satyr with Wineskin. 34. Athena with Gorgon Spoils. 35–44.—FINEST GREEK SCARABS AND SCARABAEOIDS. 35. Head of Young Warrior. 36. Lyre Player. (Cockerell Coll.) 37. Crane, with Deer’s Antler. 38. Head of Eos. 39. Lyre Player. (Woodhouse Coll. and B.M.) 40. Lyre Player, signed by Syries. 41. Stork and Grasshopper, signed by Dexamenos. (St. Petersburg.) 42. Flying Crane, signed by Dexamenos. (St. Petersburg.) 43. Flying Goose. 44. Lion and Stag. 45–54.—ETRUSCAN SCARABS. 45. Achilles in Retirement. 46. Victory. 47. Capaneus struck by the Bolt. 48. Heracles. 49. Capaneus struck by the Bolt. 50. Achilles. 51. Heracles and Cycnus. 52. Heracles. 53. Heracles and the Lion. 54. Machaon bandaging Philoctetes}}

{{LEGEND:Girl with Scroll and Lyre. 56. Girl with Water-Jar. 57. Head of Aristippus—Deities. 58–61.—SIGNED GEMS. 58. Asclepius of Aulos. 59. Citharist of Allion. 60. Medusa of Solon. 61. Heracles of Gnaios. 62–70.—ROMAN GEMS. 62. Portrait. 63. Head of Trajan Decius. 64. Ares and Aphrodite. 65. Jupiter of Heliopolis. 66. Artemis of Ephesus. 67. So-called Psyche. 68. So-called Psyche. 69. Minerva with Mask, Stamp for the Eye Balsam of Herophilus. 70. Helios. 71–72.—CHRISTIAN GEMS. 71. Crucifixion. 72. Good Shepherd. Jonah. 73–76.—EIGHTEENTH CENTURY GEMS. 73. Achilles of Pamphilus, copied from the antique. 74. Eros and Psyche, by Pichler. 75. Head of Athena. 76. Athena, from Townley Bust by Marchant}LEGEND}
```

---

## PLATE (VOL. 11, P. 857) — vol 11

**Article ID:** 4248241  
**Signature:** `wikitable depth=1 wt=1 ht=0 has_colspan`

### Source excerpt
```
{|align="center" style="font-size: 50%"
|valign="bottom"|[[Image:EB1911 Germany - The Great Duchies 887-1137.jpg|400px]]
|valign="bottom"|[[Image:EB1911 Germany - The Transition to Empire 1137-1254.jpg|400px]]
|-
|colspan="2"|[[Image:EB1911 Germany - 1254-1500.jpg|805px]]
|-
|align="right" colspan="2"|Emery Walker sc.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 0 | 0 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **5** | **5** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | 'Emery Walker sc' | 'Emery Walker sc' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Germany - The Great Duchies 887-1137.jpg}}

{{IMG:EB1911 Germany - The Transition to Empire 1137-1254.jpg}}

{{IMG:EB1911 Germany - 1254-1500.jpg}}

Emery Walker sc
```

### Current body
```
{{IMG:EB1911 Germany - The Great Duchies 887-1137.jpg}}

{{IMG:EB1911 Germany - The Transition to Empire 1137-1254.jpg}}

{{IMG:EB1911 Germany - 1254-1500.jpg}}

Emery Walker sc
```

---

## PLATE (VOL. 11, P. 880) — vol 11

**Article ID:** 4248242  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|align="center" style="font-size: 50%"
|[[Image:EB1911 Germany - at the time of the Reformation, 1547.jpg|800px]]
|-
|[[Image:EB1911 Germany - after the Peace of Westphalia, 1648.jpg|800px]]
|-
|align="right"|Emery Walker sc.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 1 | 1 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **3** | **3** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Germany - at the time of the Reformation, 1547.jpg|Emery Walker sc}}

{{IMG:EB1911 Germany - after the Peace of Westphalia, 1648.jpg}}
```

### Current body
```
{{IMG:EB1911 Germany - at the time of the Reformation, 1547.jpg|Emery Walker sc}}

{{IMG:EB1911 Germany - after the Peace of Westphalia, 1648.jpg}}
```

---

## PLATE (VOL. 12, P. 112), PLATE I — vol 12

**Article ID:** 4200718  
**Signature:** `wikitable depth=2 wt=multi ht=0`

### Source excerpt
```
{|align="center"
|-
 |align="center"|
{|
|-
 |valign="bottom"|[[Image:Britannica Glass Egyptian Amphora.png|150px]]
 |valign="bottom"|[[Image:Britannica Glass Egyptian Amphorae.png|200px]]
|-
 |align="center"|{{small-caps|Fig.}} 1.
 |align="center"|{{small-caps|Fig.}} 2.
|}


[[Image:Britannica Glass Fragments.png|375px]]

{|width="375"
|-
 |align="center"|{{small-caps|Fig.}} 3.
 |align="center"|{{small-caps|Fig.}} 4.
|}


[[Image:Britannica Glass Ancient Roman Cut Glass A.png|300px]]

{{small-caps|Fig.}} 5.
 |align="center"|
[[Image:Britannica Glass Ancient Roman Cut Glass Bowl.png|400px]]

{{small-caps|Fig.}} 6.


[[Image:Britannica Glass Verzellini Goblet.png|200px]]

{{small-caps|Fig.}} 8.


[[Image:Britannica Glass Oval Cut-Glass Waterford Bowl.png|400px]]

{{small-caps|Fig.}} 10.
|-
 |valign="bottom"|[[Image:Britannica Glass Venetian Drinking Glasses.png|400px]]
 |valign="bottom"|[[Image:Britannica Glass English 18th Century Drinking Glasses.png|400px]]
|-
 |align="center"|{{small-caps|Fig.}} 7
 |align="center"|{{small-caps|Fig.}} 9.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 9 | 9 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 1 | 1 |
| **matter**      | **15** | **15** |
| **penalty**     | **1** | **1** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | 'Fig. 7 Fig. 9' | 'Fig. 7 Fig. 9' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:Britannica Glass Egyptian Amphora.png|Fig. 5}}

{{IMG:Britannica Glass Egyptian Amphorae.png|Fig. 6}}

{{IMG:Britannica Glass Fragments.png|Fig. 8}}

{{IMG:Britannica Glass Ancient Roman Cut Glass A.png|Fig. 10}}

{{IMG:Britannica Glass Ancient Roman Cut Glass Bowl.png}}

{{IMG:Britannica Glass Verzellini Goblet.png}}

{{IMG:Britannica Glass Oval Cut-Glass Waterford Bowl.png}}

{{IMG:Britannica Glass Venetian Drinking Glasses.png}}

{{IMG:Britannica Glass English 18th Century Drinking Glasses.png}}

Fig. 7 Fig. 9
```

### Current body
```
{{IMG:Britannica Glass Egyptian Amphora.png|Fig. 5}}

{{IMG:Britannica Glass Egyptian Amphorae.png|Fig. 6}}

{{IMG:Britannica Glass Fragments.png|Fig. 8}}

{{IMG:Britannica Glass Ancient Roman Cut Glass A.png|Fig. 10}}

{{IMG:Britannica Glass Ancient Roman Cut Glass Bowl.png}}

{{IMG:Britannica Glass Verzellini Goblet.png}}

{{IMG:Britannica Glass Oval Cut-Glass Waterford Bowl.png}}

{{IMG:Britannica Glass Venetian Drinking Glasses.png}}

{{IMG:Britannica Glass English 18th Century Drinking Glasses.png}}

Fig. 7 Fig. 9
```

---

## GLASS, PLATE II — vol 12

**Article ID:** 4200719  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{{c/s}}
{|width="800"
|-
 |align="center" valign="bottom"|[[Image:Britannica Glass Jackson Table Glass.png|400px]]
 |align="center" valign="bottom"|[[Image:Britannica Glass Webb Table Glass.png|400px]]
|-
 |align="center" valign="top"|{{small-caps|Fig.}} 11. &mdash; TABLE GLASS.<br>{{small-caps|Designed by T. G. Jackson in 1870.}}
 |align="center" valign="top"|{{small-caps|Fig.}} 12. &mdash; TABLE GLASS<br>{{small-caps|Designed for Wm. Morris about 1872 by Philip Webb.}}
|}


[[Image:Britannica Glass Tiffany Glassware.png|800px]]

{{small-caps|Fig.}} 13 &mdash; TIFFANY GLASS.


[[Image:Britannica Glass Whitefriars Glassware.png|800px]]

{{small-caps|Fig.}} 14. &mdash; WHITEFRIARS GLASS, 1906.
{{c/e}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **7** | **7** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:Britannica Glass Jackson Table Glass.png|TABLE GLASS. Designed by T. G. Jackson in 1870. align="center" valign="top" Fig. 12. — TABLE GLASS Designed for Wm. Morris about 1872 by Philip Webb}}

{{IMG:Britannica Glass Webb Table Glass.png|Fig. 13 — TIFFANY GLASS}}

{{IMG:Britannica Glass Tiffany Glassware.png|WHITEFRIARS GLASS, 1906}}

{{IMG:Britannica Glass Whitefriars Glassware.png}}
```

### Current body
```
{{IMG:Britannica Glass Jackson Table Glass.png|TABLE GLASS. Designed by T. G. Jackson in 1870. align="center" valign="top" Fig. 12. — TABLE GLASS Designed for Wm. Morris about 1872 by Philip Webb}}

{{IMG:Britannica Glass Webb Table Glass.png|Fig. 13 — TIFFANY GLASS}}

{{IMG:Britannica Glass Tiffany Glassware.png|WHITEFRIARS GLASS, 1906}}

{{IMG:Britannica Glass Whitefriars Glassware.png}}
```

---

## GLASS, STAINED, PLATE I — vol 12

**Article ID:** 4200721  
**Signature:** `html_table depth=0 wt=0 ht=1 has_colspan`

### Source excerpt
```
<table align=center width=730>
<tr><td colspan=2 {{Ts|sm92|lh12}}>{{em|11}} I.{{em|17}} II.{{em|15}} III.</td></tr>
<tr><td colspan=2>[[File:EB1911 - Glass, Stained - Plate I.png]]</td></tr>
<tr><td colspan=2 {{Ts|sm92|lh13}}>{{em|4}} IV.{{em|21}} V.{{em|22}} VI.</td></tr>
<tr><td {{Ts|sm92|lh13|w050|pr.5}}>{{hanging indent|{{em|.6}}I. EARLY GLAZING. From S. Serge, Angers, Grisaille, with colour introduced in the small circles.

{{em|.3}}II. AN EARLY BORDER. From S. Kunibert, Cologne.

III. PORTION OF AN EARLY MEDALLION WINDOW. From Canterbury, showing the plan of the design and the ornamental details.}}</td>

<td {{Ts|sm92|lh13|w050|pl.5}}>{{hanging indent|IV. AN EARLY FIGURE FROM LYONS. Showing the leading of the eyes, hair, nimbus, and drapery.

{{em|.3}}V. DECORATED LIGHTS. From S. Urbain, Troyes, showing both the influence of the early period in the figures, and the beginning of the architectural canopy.

VI. TYPICAL DECORATED CANOPY. From Exeter.}}</td></tr>
<tr><td {{Ts|sm|ac|pb1}} colspan="2">Nos. I., II., III., IV., VI. are taken from illustrations in Lewis F. Day, ''Windows'', by permission of B. T. Batsford.</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 6 | 6 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **12** | **12** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **2** | **2** |
| header text     | '11' | '11' |
| footer text     | 'Nos. I., II., III., IV., VI. are taken from illustrations in Lewis F. Day, Windows, by permission of B. T. Batsford' | 'Nos. I., II., III., IV., VI. are taken from illustrations in Lewis F. Day, Windows, by permission of B. T. Batsford' |

**Verdict:** ✅ identical

### Baseline body
```
11

{{IMG:EB1911 - Glass, Stained - Plate I.png|V. VI}}

{{LEGEND:EARLY GLAZING. From S. Serge, Angers, Grisaille, with colour introduced in the small circles}LEGEND}

{{LEGEND:AN EARLY BORDER. From S. Kunibert, Cologne}LEGEND}

{{LEGEND:PORTION OF AN EARLY MEDALLION WINDOW. From Canterbury, showing the plan of the design and the ornamental details}LEGEND}

{{LEGEND:AN EARLY FIGURE FROM LYONS. Showing the leading of the eyes, hair, nimbus, and drapery}LEGEND}

{{LEGEND:DECORATED LIGHTS. From S. Urbain, Troyes, showing both the influence of the early period in the figures, and the beginning of the architectural canopy}LEGEND}

{{LEGEND:TYPICAL DECORATED CANOPY. From Exeter}LEGEND}

Nos. I., II., III., IV., VI. are taken from illustrations in Lewis F. Day, Windows, by permission of B. T. Batsford
```

### Current body
```
11

{{IMG:EB1911 - Glass, Stained - Plate I.png|V. VI}}

{{LEGEND:EARLY GLAZING. From S. Serge, Angers, Grisaille, with colour introduced in the small circles}LEGEND}

{{LEGEND:AN EARLY BORDER. From S. Kunibert, Cologne}LEGEND}

{{LEGEND:PORTION OF AN EARLY MEDALLION WINDOW. From Canterbury, showing the plan of the design and the ornamental details}LEGEND}

{{LEGEND:AN EARLY FIGURE FROM LYONS. Showing the leading of the eyes, hair, nimbus, and drapery}LEGEND}

{{LEGEND:DECORATED LIGHTS. From S. Urbain, Troyes, showing both the influence of the early period in the figures, and the beginning of the architectural canopy}LEGEND}

{{LEGEND:TYPICAL DECORATED CANOPY. From Exeter}LEGEND}

Nos. I., II., III., IV., VI. are taken from illustrations in Lewis F. Day, Windows, by permission of B. T. Batsford
```

---

## GLASS, STAINED, PLATE II — vol 12

**Article ID:** 4200722  
**Signature:** `html_table depth=0 wt=0 ht=1`

### Source excerpt
```
<table {{Ts|ma|sm92|lh12}}>
<tr><td>{{em|61}} <span style="position: relative; top: 25.05em;>I.</span></td></tr>
<tr><td {{Ts|ac|mc|ma}}>[[File:EB1911 - Glass, Stained - Plate II.png]]</td></tr>
<tr><td>{{em|9}} II.{{em|25}} III.{{em|24}} IV.</td></tr>
<tr><td {{Ts|pl.5|pr.5|al}}>{{em|.6}}I. A TYPICAL PERPENDICULAR CANOPY (from Lewis F. Day, ''Windows'', by permission of B. T. Batsford).<br />{{em|.3}}II. A WINDOW FROM AUCH. Illustrating the transition from Perpendicular to Renaissance.<br />III. A SIXTEENTH-CENTURY JESSE WINDOW. From Beauvais (source as in Fig. I.).<br />IV. PORTION OF A RENAISSANCE WINDOW. From Montmorency, showing the perfection of glass painting.</td></tr>
<tr><td {{Ts|pl.5|pr.5|ar|sm92|lh11}}>From Lutien Magne, ''Oeuvre des Peintres Verriers Français'', by permission of Firmin-Didot et C<sup>ie</sup>.</td></tr></table>
{{nop}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 2 | 2 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '61 I' | '61 I' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
61 I

{{IMG:EB1911 - Glass, Stained - Plate II.png|III. IV}}

{{LEGEND:A TYPICAL PERPENDICULAR CANOPY (from Lewis F. Day, Windows, by permission of B. T. Batsford). II. A WINDOW FROM AUCH. Illustrating the transition from Perpendicular to Renaissance. III. A SIXTEENTH-CENTURY JESSE WINDOW. From Beauvais (source as in Fig. I.). IV. PORTION OF A RENAISSANCE WINDOW. From Montmorency, showing the perfection of glass painting}LEGEND}

{{LEGEND:From Lutien Magne, Oeuvre des Peintres Verriers Français, by permission of Firmin-Didot et Cie}LEGEND}
```

### Current body
```
61 I

{{IMG:EB1911 - Glass, Stained - Plate II.png|III. IV}}

{{LEGEND:A TYPICAL PERPENDICULAR CANOPY (from Lewis F. Day, Windows, by permission of B. T. Batsford). II. A WINDOW FROM AUCH. Illustrating the transition from Perpendicular to Renaissance. III. A SIXTEENTH-CENTURY JESSE WINDOW. From Beauvais (source as in Fig. I.). IV. PORTION OF A RENAISSANCE WINDOW. From Montmorency, showing the perfection of glass painting}LEGEND}

{{LEGEND:From Lutien Magne, Oeuvre des Peintres Verriers Français, by permission of Firmin-Didot et Cie}LEGEND}
```

---

## GREEK ART, PLATE I — vol 12

**Article ID:** 4201283  
**Signature:** `wikitable depth=2 wt=multi ht=0`

### Source excerpt
```
{|align="center" cellspacing="20"
|align="center"|
{|align="center" cellspacing="0" cellpadding="0" style="font-size: 50%"
|[[Image:EB1911 Greek Art - Harmodius and Aristogiton.jpg|340px]]
|-
|&ensp;''Photo, Brogi.''
|}
{{sc|Fig. 50. HARMODIUS AND ARISTOGITON.<br />
(Nat. Mus. Naples.)}}
|align="center" valign="top"|
{|align="center" cellspacing="0" cellpadding="0" style="font-size: 50%"
|[[Image:EB1911 Greek Art - Farnese Bull.jpg|440px]]
|-
|&ensp;''Photo, Brogi.''
|}
{{sc|Fig. 51. FARNESE BULL. (Naples.)}}
|-
|valign="bottom" align="center"|
{|align="center" cellspacing="0" cellpadding="0" style="font-size: 50%"
|[[Image:EB1911 Greek Art - Laocoon Group.jpg|360px]]
|-
|&ensp;''Photo, Anderson.''
|}
{{sc|Fig. 52. LAOCOON GROUP. (Vatican.)}}
|align="center"|
{|align="center" cellspacing="0" cellpadding="0" style="font-size: 50%"
|[[Image:EB1911 Greek Art - Ganymede of Leochares.jpg|420px]]
|-
|&ensp;''Photo, Anderson.''
|}
{{sc|Fig. 53. GANYMEDE OF LEOCHARES. (Vatican.)}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Greek Art - Harmodius and Aristogiton.jpg|HARMODIUS AND ARISTOGITON. (Nat. Mus. Naples.) (Photo, Brogi)}}

{{IMG:EB1911 Greek Art - Farnese Bull.jpg|FARNESE BULL. (Naples.) (Photo, Brogi)}}

{{IMG:EB1911 Greek Art - Laocoon Group.jpg|LAOCOON GROUP. (Vatican.) (Photo, Anderson)}}

{{IMG:EB1911 Greek Art - Ganymede of Leochares.jpg|GANYMEDE OF LEOCHARES. (Vatican.) (Photo, Anderson)}}
```

### Current body
```
{{IMG:EB1911 Greek Art - Harmodius and Aristogiton.jpg|HARMODIUS AND ARISTOGITON. (Nat. Mus. Naples.) (Photo, Brogi)}}

{{IMG:EB1911 Greek Art - Farnese Bull.jpg|FARNESE BULL. (Naples.) (Photo, Brogi)}}

{{IMG:EB1911 Greek Art - Laocoon Group.jpg|LAOCOON GROUP. (Vatican.) (Photo, Anderson)}}

{{IMG:EB1911 Greek Art - Ganymede of Leochares.jpg|GANYMEDE OF LEOCHARES. (Vatican.) (Photo, Anderson)}}
```

---

## GREEK ART, PLATE II — vol 12

**Article ID:** 4201284  
**Signature:** `wikitable depth=2 wt=multi ht=0`

### Source excerpt
```
{|align="center" cellspacing="20"
|align="center" width="150" valign="top"|
{|align="center" cellspacing="0" cellpadding="0" style="font-size: 50%"
|[[Image:EB1911 Greek Art - Flaying of Marsyas.jpg|150px]]
|-
|&ensp;''Photo, Anderson.''
|}
{{EB1911 fine print|{{sc|Fig. 54.—FLAYING OF MARSYAS. (Villa Albani, Rome.)}}}}


[[Image:Greek Art - Theseus and Amazon.jpg|150px]]
{{EB1911 fine print|{{sc|Fig. 58.—THESEUS AND AMAZON (ERETRIA).}}}}
|align="center" width="450" valign="top"|
{|align="center" cellspacing="0" cellpadding="0" style="font-size: 50%"
|[[Image:EB1911 Greek Art - Apollo of the Belvidere.jpg|450px]]
|-
|&ensp;''Photo, Anderson.''
|}
{{EB1911 fine print|{{sc|Fig. 55.—APOLLO OF THE BELVIDERE. (Vatican.)}}}}


{|align="center" cellspacing="0" cellpadding="0" style="font-size: 50%"
|[[Image:EB1911 Greek Art - Drum of column from Ephesus.jpg|350px]]
|-
|&ensp;''Photo, Mansell.''
|}
{{EB1911 fine print|{{sc|Fig. 59.—DRUM OF COLUMN FROM EPHESUS. (Brit. Mus.)}}}}
|align="center" width="200" valign="top"|[[Image:EB1911 Greek Art - Head of young Alexander.jpg|200px]]
{{EB1911 fine print|{{sc|Fig. 56.—HEAD OF YOUNG ALEXANDER. (Brit. Mus.)}}}}

{|align="center" cellspacing="0" cellpadding="0" style="font-size: 50%"
|[[Image:EB1911 Greek Art - Hermes of Alcamenes.jpg|200px]]
|-
|&ensp;''Photo, Seebah.''
|}
{{EB1911 fine print|{{sc|Fig. 57.—HERMES OF ALCAMENES. (Constantinople.)}}}}

{|align="center" cellspacing="0" cellpadding="0" style="font-size: 50%"
|[[Image:EB1911 Greek 
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 7 | 7 |
| captioned       | 7 | 7 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **14** | **14** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Greek Art - Flaying of Marsyas.jpg|FLAYING OF MARSYAS. (Villa Albani, Rome.)}}

{{IMG:Greek Art - Theseus and Amazon.jpg|THESEUS AND AMAZON (ERETRIA)}}

{{IMG:EB1911 Greek Art - Apollo of the Belvidere.jpg|APOLLO OF THE BELVIDERE. (Vatican.)}}

{{IMG:EB1911 Greek Art - Drum of column from Ephesus.jpg|DRUM OF COLUMN FROM EPHESUS. (Brit. Mus.)}}

{{IMG:EB1911 Greek Art - Head of young Alexander.jpg|HEAD OF YOUNG ALEXANDER. (Brit. Mus.)}}

{{IMG:EB1911 Greek Art - Hermes of Alcamenes.jpg|HERMES OF ALCAMENES. (Constantinople.)}}

{{IMG:EB1911 Greek Art - young Hermes.jpg|YOUNG HERMES. (Mus. of Fine Arts, Boston.)}}
```

### Current body
```
{{IMG:EB1911 Greek Art - Flaying of Marsyas.jpg|FLAYING OF MARSYAS. (Villa Albani, Rome.)}}

{{IMG:Greek Art - Theseus and Amazon.jpg|THESEUS AND AMAZON (ERETRIA)}}

{{IMG:EB1911 Greek Art - Apollo of the Belvidere.jpg|APOLLO OF THE BELVIDERE. (Vatican.)}}

{{IMG:EB1911 Greek Art - Drum of column from Ephesus.jpg|DRUM OF COLUMN FROM EPHESUS. (Brit. Mus.)}}

{{IMG:EB1911 Greek Art - Head of young Alexander.jpg|HEAD OF YOUNG ALEXANDER. (Brit. Mus.)}}

{{IMG:EB1911 Greek Art - Hermes of Alcamenes.jpg|HERMES OF ALCAMENES. (Constantinople.)}}

{{IMG:EB1911 Greek Art - young Hermes.jpg|YOUNG HERMES. (Mus. of Fine Arts, Boston.)}}
```

---

## GREEK ART, PLATE III — vol 12

**Article ID:** 4201285  
**Signature:** `wikitable depth=2 wt=multi ht=0 has_colspan`

### Source excerpt
```
{|align="center" cellspacing="20"
|align="center" width="150" valign="top"|
{|align="center" cellspacing="0" cellpadding="0" style="font-size: 50%"
|[[Image:EB1911 Greek Art - Winged Victory of Samothrace.jpg|150px]]
|-
|&ensp;''Photo, Giraudon.''
|}
{{EB1911 fine print|{{sc|Fig. 61.—WINGED VICTORY OF SAMOTHRACE. (Louvre.)}}}}


[[Image:EB1911 Greek Art - Head of Warrior.jpg|150px]]
{{EB1911 fine print|{{sc|Fig. 63. HEAD OF WARRIOR, RESTORED, FROM TEGEA.}}}}
|align="center" width="225" valign="top"|
{|align="center" cellspacing="0" cellpadding="0" style="font-size: 50%"
|[[Image:EB1911 Greek Art - Winged Victory of Samothrace (front).jpg|225px]]
|-
|&ensp;''Photo, Giraudon.''
|}
{{EB1911 fine print|{{sc|Fig. 62.—WINGED VICTORY OF SAMOTHRACE. (Louvre.)}}}}
|align="center" width="300" valign="top"|
{|align="center" cellspacing="0" cellpadding="0" style="font-size: 50%"
|[[Image:EB1911 Greek Art - Marsyas of Myron.jpg|300px]]
|-
|&ensp;''Photo, Anderson.''
|}
{{EB1911 fine print|{{sc|Fig. 64.—MARSYAS OF MYRON. (Lateran Mus.)}}}}
|-
|colspan="3" align="center"|[[Image:EB1911 Greek Art - East Pediment of the Parthenon (left).jpg|700px]]
|-
|colspan="3" align="center"|
{|align="center" cellspacing="0" cellpadding="0" style="font-size: 50%"
|[[Image:EB1911 Greek Art - East Pediment of the Parthenon (right).jpg|700px]]
|-
|&ensp;''Photo, Mansell.''
|}
{{EB1911 fine print|{{sc|Fig. 65.—EAST PEDIMENT OF THE PARTHENON; LEFT AND RIGHT ENDS. (Brit. Mus.)}}}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 6 | 6 |
| captioned       | 6 | 6 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **12** | **12** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Greek Art - Winged Victory of Samothrace.jpg|WINGED VICTORY OF SAMOTHRACE. (Louvre.)}}

{{IMG:EB1911 Greek Art - Head of Warrior.jpg|HEAD OF WARRIOR, RESTORED, FROM TEGEA}}

{{IMG:EB1911 Greek Art - Winged Victory of Samothrace (front).jpg|WINGED VICTORY OF SAMOTHRACE. (Louvre.)}}

{{IMG:EB1911 Greek Art - Marsyas of Myron.jpg|MARSYAS OF MYRON. (Lateran Mus.)}}

{{IMG:EB1911 Greek Art - East Pediment of the Parthenon (left).jpg|EAST PEDIMENT OF THE PARTHENON; LEFT AND RIGHT ENDS. (Brit. Mus.)}}

{{IMG:EB1911 Greek Art - East Pediment of the Parthenon (right).jpg|Photo, Mansell}}
```

### Current body
```
{{IMG:EB1911 Greek Art - Winged Victory of Samothrace.jpg|WINGED VICTORY OF SAMOTHRACE. (Louvre.)}}

{{IMG:EB1911 Greek Art - Head of Warrior.jpg|HEAD OF WARRIOR, RESTORED, FROM TEGEA}}

{{IMG:EB1911 Greek Art - Winged Victory of Samothrace (front).jpg|WINGED VICTORY OF SAMOTHRACE. (Louvre.)}}

{{IMG:EB1911 Greek Art - Marsyas of Myron.jpg|MARSYAS OF MYRON. (Lateran Mus.)}}

{{IMG:EB1911 Greek Art - East Pediment of the Parthenon (left).jpg|EAST PEDIMENT OF THE PARTHENON; LEFT AND RIGHT ENDS. (Brit. Mus.)}}

{{IMG:EB1911 Greek Art - East Pediment of the Parthenon (right).jpg|Photo, Mansell}}
```

---

## GREEK ART, PLATE IV — vol 12

**Article ID:** 4201286  
**Signature:** `wikitable depth=2 wt=multi ht=0 has_colspan`

### Source excerpt
```
{|align="center" cellspacing="20"
|align="center" width="370" valign="top"|[[Image:EB1911 Greek Art - Metope of the Treasury of Sicyon at Delphi.jpg|370px]]
{{EB1911 fine print|{{sc|Fig. 66.—METOPE OF THE TREASURY OF SICYON AT DELPHI.}}}}<br />
{{fs|70%|(From ''Fouilles de Delphes'', by permission of A. Fontemoing.)}}


{|align="center" cellspacing="0" cellpadding="0" style="font-size: 70%"
|[[Image:EB1911 Greek Art - Discobolus of Myron.jpg|370px]]
|-
|&ensp;''Photo, F. Bruckmann.''
|}
{{EB1911 fine print|{{sc|Fig. 68.—DISCOBOLUS OF MYRON, RESTORED BY
PROF. FURTWÄNGLER.}}}}

|align="center" width="420" valign="top"|[[Image:EB1911 Greek Art - .jpg|420px]]
{{EB1911 fine print|{{sc|Fig. 67.—GREEK PAINTING OF WOMAN’S HEAD.}}}}<br />
{{fs|70%|(From ''Comptes Rendus'' of St. Petersburg, 1865. Pl. I.)}}


{|align="center" cellspacing="0" cellpadding="0" style="font-size: 70%"
|[[Image:EB1911 Greek Art - Fighter of Agasias.jpg|420px]]
|-
|&ensp;''Photo, Giraudon.''
|}
{{EB1911 fine print|{{sc|Fig. 69.—FIGHTER OF AGASIAS. (Louvre.)}}}}
|-
|align="center" width="750" colspan="2"|
{|align="center" cellspacing="0" cellpadding="0" style="font-size: 70%"
|[[Image:EB1911 Greek Art - Portion of frieze of mausoleum.jpg|750px]]
|-
|&ensp;''Photo, Mansell.''
|}
{{EB1911 fine print|{{sc|Fig. 70.—PORTION OF FRIEZE OF MAUSOLEUM. (Brit. Mus.)}}}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 5 | 5 |
| captioned       | 5 | 5 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **10** | **10** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Greek Art - Metope of the Treasury of Sicyon at Delphi.jpg|METOPE OF THE TREASURY OF SICYON AT DELPHI. (From Fouilles de Delphes, by permission of A. Fontemoing.)}}

{{IMG:EB1911 Greek Art - Discobolus of Myron.jpg|DISCOBOLUS OF MYRON, RESTORED BY PROF. FURTWÄNGLER}}

{{IMG:EB1911 Greek Art - .jpg|GREEK PAINTING OF WOMAN’S HEAD. (From Comptes Rendus of St. Petersburg, 1865. Pl. I.)}}

{{IMG:EB1911 Greek Art - Fighter of Agasias.jpg|FIGHTER OF AGASIAS. (Louvre.)}}

{{IMG:EB1911 Greek Art - Portion of frieze of mausoleum.jpg|PORTION OF FRIEZE OF MAUSOLEUM. (Brit. Mus.)}}
```

### Current body
```
{{IMG:EB1911 Greek Art - Metope of the Treasury of Sicyon at Delphi.jpg|METOPE OF THE TREASURY OF SICYON AT DELPHI. (From Fouilles de Delphes, by permission of A. Fontemoing.)}}

{{IMG:EB1911 Greek Art - Discobolus of Myron.jpg|DISCOBOLUS OF MYRON, RESTORED BY PROF. FURTWÄNGLER}}

{{IMG:EB1911 Greek Art - .jpg|GREEK PAINTING OF WOMAN’S HEAD. (From Comptes Rendus of St. Petersburg, 1865. Pl. I.)}}

{{IMG:EB1911 Greek Art - Fighter of Agasias.jpg|FIGHTER OF AGASIAS. (Louvre.)}}

{{IMG:EB1911 Greek Art - Portion of frieze of mausoleum.jpg|PORTION OF FRIEZE OF MAUSOLEUM. (Brit. Mus.)}}
```

---

## GREEK ART, PLATE V — vol 12

**Article ID:** 4201287  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|align="center" cellspacing="20"
|align="center" width="200" valign="top"|[[Image:EB1911 Greek Art - Aphrodite of Cnidus.jpg|x550px]]
{{left|{{fs|70%|''From a Cast.''}}}}
{{EB1911 fine print|{{sc|Fig. 71.—APHRODITE OF CNIDUS. (Vatican.)}}}}
|align="center" width="400" valign="top"|[[Image:EB1911 Greek Art - Bronze Boxer of Terme.jpg|x550px]]
{{left|{{fs|70%|''Photo, Anderson.''}}}}
{{EB1911 fine print|{{sc|Fig. 72.—BRONZE BOXER OF TERME. (Rome.)}}}}
|align="center" width="200" valign="top"|[[Image:EB1911 Greek Art - Bronze of Cerigotto.jpg|x550px]]
{{EB1911 fine print|{{sc|Fig. 73.—BRONZE OF CERIGOTTO. (Athens.)}} Found in the sea near Cythera.}}
|-
|align="center" valign="top"|[[Image:EB1911 Greek Art - Agias at Delphi.jpg|x500px]]
{{EB1911 fine print|{{sc|Fig. 74.—AGIAS AT DELPHI.}}}}<br>
{{fs|70%|(From ''Fouilles de Delphes'', by permission of A. Fontemoing.)}}
|align="center" valign="top"|[[Image:EB1911 Greek Art - Cora of Erechtheum.jpg|x500px]]
{{EB1911 fine print|{{sc|Fig. 75.—CORA (KORÉ) OF ERECHTHEUM. (Athens.)}}}}
|align="center" valign="top"|[[Image:EB1911 Greek Art - Apollo at Delphi.jpg|x500px]]
{{EB1911 fine print|{{sc|Fig. 76.—APOLLO AT DELPHI.}}}}<br>
{{fs|70%|(From ''Fouilles de Delphes'', by permission of A. Fontemoing.)}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 6 | 6 |
| captioned       | 6 | 6 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **12** | **12** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Greek Art - Aphrodite of Cnidus.jpg|APHRODITE OF CNIDUS. (Vatican.)}}

{{IMG:EB1911 Greek Art - Bronze Boxer of Terme.jpg|BRONZE BOXER OF TERME. (Rome.)}}

{{IMG:EB1911 Greek Art - Bronze of Cerigotto.jpg|BRONZE OF CERIGOTTO. (Athens.) Found in the sea near Cythera}}

{{IMG:EB1911 Greek Art - Agias at Delphi.jpg|AGIAS AT DELPHI. (From Fouilles de Delphes, by permission of A. Fontemoing.)}}

{{IMG:EB1911 Greek Art - Cora of Erechtheum.jpg|CORA (KORÉ) OF ERECHTHEUM. (Athens.)}}

{{IMG:EB1911 Greek Art - Apollo at Delphi.jpg|APOLLO AT DELPHI. (From Fouilles de Delphes, by permission of A. Fontemoing.)}}
```

### Current body
```
{{IMG:EB1911 Greek Art - Aphrodite of Cnidus.jpg|APHRODITE OF CNIDUS. (Vatican.)}}

{{IMG:EB1911 Greek Art - Bronze Boxer of Terme.jpg|BRONZE BOXER OF TERME. (Rome.)}}

{{IMG:EB1911 Greek Art - Bronze of Cerigotto.jpg|BRONZE OF CERIGOTTO. (Athens.) Found in the sea near Cythera}}

{{IMG:EB1911 Greek Art - Agias at Delphi.jpg|AGIAS AT DELPHI. (From Fouilles de Delphes, by permission of A. Fontemoing.)}}

{{IMG:EB1911 Greek Art - Cora of Erechtheum.jpg|CORA (KORÉ) OF ERECHTHEUM. (Athens.)}}

{{IMG:EB1911 Greek Art - Apollo at Delphi.jpg|APOLLO AT DELPHI. (From Fouilles de Delphes, by permission of A. Fontemoing.)}}
```

---

## GREEK ART, PLATE VI — vol 12

**Article ID:** 4201288  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|align="center" cellspacing="20"
|align="center" width="200" valign="top"|[[Image:EB1911 Greek Art - Aphrodite of Melos.jpg|x550px]]
{{left|{{fs|70%|''Photo, Giraudon.''}}}}
{{EB1911 fine print|{{sc|Fig. 77.—APHRODITE OF MELOS. (Louvre.)}}}}
|align="center" width="400" valign="top"|[[Image:EB1911 Greek Art - Niobe and her Youngest Daughter.jpg|x550px]]
{{left|{{fs|70%|''Photo, Alinari.''}}}}
{{EB1911 fine print|{{sc|Fig. 78.—NIOBE AND HER YOUNGEST DAUGHTER. (Florence.)}}}}
|align="center" width="250" valign="top"|[[Image:EB1911 Greek Art - Apoxyomenus.jpg|x550px]]
{{left|{{fs|70%|''Photo, Anderson.''}}}}
{{EB1911 fine print|{{sc|Fig. 79.—APOXYOMENUS. (Vatican.)}}}}
|-
|align="center" valign="top"|[[Image:EB1911 Greek Art - Doryphorus of Polyclitus.jpg|x550px]]
{{left|{{fs|70%|''Photo, Brogi.''}}}}
{{EB1911 fine print|{{sc|Fig. 80.—DORYPHORUS OF POLYCLITUS. (Nat. Mus., Naples.)}}}}
|align="center" valign="top"|[[Image:EB1911 Greek Art - Antioch Seated on a Rock.jpg|x550px]]
{{left|{{fs|70%|''Photo, Alinari.''}}}}
{{EB1911 fine print|{{sc|Fig. 81.—ANTIOCH SEATED ON A ROCK. (Vatican.)}}}}
|align="center" valign="top"|[[Image:EB1911 Greek Art - Hermes of Praxiteles (2).jpg|x550px]]
{{left|{{fs|70%|''English Photographic Co.''}}}}
{{EB1911 fine print|{{sc|Fig. 82.—HERMES OF PRAXITELES. (Olympia.)}}}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 6 | 6 |
| captioned       | 6 | 6 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **12** | **12** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Greek Art - Aphrodite of Melos.jpg|APHRODITE OF MELOS. (Louvre.)}}

{{IMG:EB1911 Greek Art - Niobe and her Youngest Daughter.jpg|NIOBE AND HER YOUNGEST DAUGHTER. (Florence.)}}

{{IMG:EB1911 Greek Art - Apoxyomenus.jpg|APOXYOMENUS. (Vatican.)}}

{{IMG:EB1911 Greek Art - Doryphorus of Polyclitus.jpg|DORYPHORUS OF POLYCLITUS. (Nat. Mus., Naples.)}}

{{IMG:EB1911 Greek Art - Antioch Seated on a Rock.jpg|ANTIOCH SEATED ON A ROCK. (Vatican.)}}

{{IMG:EB1911 Greek Art - Hermes of Praxiteles (2).jpg|HERMES OF PRAXITELES. (Olympia.)}}
```

### Current body
```
{{IMG:EB1911 Greek Art - Aphrodite of Melos.jpg|APHRODITE OF MELOS. (Louvre.)}}

{{IMG:EB1911 Greek Art - Niobe and her Youngest Daughter.jpg|NIOBE AND HER YOUNGEST DAUGHTER. (Florence.)}}

{{IMG:EB1911 Greek Art - Apoxyomenus.jpg|APOXYOMENUS. (Vatican.)}}

{{IMG:EB1911 Greek Art - Doryphorus of Polyclitus.jpg|DORYPHORUS OF POLYCLITUS. (Nat. Mus., Naples.)}}

{{IMG:EB1911 Greek Art - Antioch Seated on a Rock.jpg|ANTIOCH SEATED ON A ROCK. (Vatican.)}}

{{IMG:EB1911 Greek Art - Hermes of Praxiteles (2).jpg|HERMES OF PRAXITELES. (Olympia.)}}
```

---

## HERALDRY, PLATE I — vol 13

**Article ID:** 4202629  
**Signature:** `html_table depth=0 wt=0 ht=1`

### Source excerpt
```
<table align=center>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 Heraldry - Plate I.jpg]]</td></tr>
<tr><td {{Ts|sm92|lh13|ac|pl1|pr1}}>PART OF A ROLL OF ARMS PAINTED IN ENGLAND AT THE BEGINNING OF THE 14TH CENTURY. THE NAMES HAVE BEEN ADDED BY A<br />SOMEWHAT LATER HAND, AND ARE IN MANY CASES MISTAKEN AND MIS-SPELLED.</td></tr>
<tr><td {{Ts|sm80|lh12|ac}}>''Drawn by William Gibb for the'' ENCYCLOPAEDIA BRITANNICA.</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **3** | **3** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Heraldry - Plate I.jpg|PART OF A ROLL OF ARMS PAINTED IN ENGLAND AT THE BEGINNING OF THE 14TH CENTURY. THE NAMES HAVE BEEN ADDED BY A SOMEWHAT LATER HAND, AND ARE IN MANY CASES MISTAKEN AND MIS-SPELLED}}

{{LEGEND:Drawn by William Gibb for the ENCYCLOPAEDIA BRITANNICA}LEGEND}
```

### Current body
```
{{IMG:EB1911 Heraldry - Plate I.jpg|PART OF A ROLL OF ARMS PAINTED IN ENGLAND AT THE BEGINNING OF THE 14TH CENTURY. THE NAMES HAVE BEEN ADDED BY A SOMEWHAT LATER HAND, AND ARE IN MANY CASES MISTAKEN AND MIS-SPELLED}}

{{LEGEND:Drawn by William Gibb for the ENCYCLOPAEDIA BRITANNICA}LEGEND}
```

---

## HERALDRY, PLATE II — vol 13

**Article ID:** 4202630  
**Signature:** `html_table depth=0 wt=0 ht=1 has_colspan`

### Source excerpt
```
<table align=center>
<tr><td {{Ts|ac|mc|ma|pt1}} colspan="2">[[File:EB1911 Heraldry - Plate II.jpg]]</td></tr>
<tr><td {{Ts|sm92|lh13|ac|pl1|pr1}} colspan="2">SIXTEEN SHIELDS FROM A ROLL OF ARMS OF ENGLISH KNIGHTS AND BARONS MADE BY AN ENGLISH<br/>PAINTER EARLY IN THE REIGN OF EDWARD III.</td></tr>
<tr><td {{Ts|pl.5|pr.5|vtp|al|sm|lh12}}>''Drawn by William Gibb.''</td>
<td {{Ts|pl.5|pr.5|vtp|ar|sm85|lh12}}>''Niagara Litho. Co., Buffalo, N. Y.''</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **3** | **3** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Heraldry - Plate II.jpg|Drawn by William Gibb}}

{{LEGEND:Niagara Litho. Co., Buffalo, N. Y}LEGEND}
```

### Current body
```
{{IMG:EB1911 Heraldry - Plate II.jpg|Drawn by William Gibb}}

{{LEGEND:Niagara Litho. Co., Buffalo, N. Y}LEGEND}
```

---

## HERALDY, PLATE IV — vol 13

**Article ID:** 4202631  
**Signature:** `html_table depth=0 wt=0 ht=1 has_colspan`

### Source excerpt
```
<table align=center width=850>
<tr><td {{Ts|ac|mc|ma|pt1}} colspan="2">[[File:EB1911 Heraldry - Plate IV.jpg]]</td></tr>
<tr><td {{Ts|sm92|lh13|ac|pl1|pr1}} colspan="2">THE BEGINNING OF A ROLL OF THE ARMS OF THOSE JOUSTING IN A TOURNAMENT HELD ON THE FIELD OF THE CLOTH OF GOLD. BESIDES THE ARMS OF THE KINGS OF FRANCE AND ENGLAND ARE TWO COLUMNS OF “CHEQUES,” MARKED WITH THE NAMES AND SCORING POINTS OF THE JOUSTERS.</td></tr>
<tr><td {{Ts|pl.5|pr.5|vtp|al|sm}}>''Drawn by William Gibb.''</td>
<td {{Ts|pl.5|pr.5|vtp|ar|sm85}}>''Niagara Litho. Co., Buffalo, N. Y.''</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **3** | **3** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Heraldry - Plate IV.jpg|Drawn by William Gibb}}

{{LEGEND:Niagara Litho. Co., Buffalo, N. Y}LEGEND}
```

### Current body
```
{{IMG:EB1911 Heraldry - Plate IV.jpg|Drawn by William Gibb}}

{{LEGEND:Niagara Litho. Co., Buffalo, N. Y}LEGEND}
```

---

## HORSE — vol 13

**Article ID:** 4203241  
**Signature:** `wikitable depth=2 wt=multi ht=0 has_colspan`

### Source excerpt
```
{{right|{{sc|Plate I.}}}}

{|align="center"
|-valign="bottom"
|
{|cellpadding="0" border="1"
|[[Image:EB1911 Horse - shire stallion.jpg|390px]]
|}
|{{gap}}
|
{|cellpadding="0" border="1"
|[[Image:EB1911 Horse - suffolk stallion.jpg|390px]]
|}
|-
|align="center"|SHIRE STALLION.
|
|align="center"|SUFFOLK STALLION.
|-
|&nbsp;
|-valign="bottom"
|
{|cellpadding="0" border="1"
|[[Image:EB1911 Horse - clydesdale stallion.jpg|390px]]
|}
|
|
{|cellpadding="0" border="1"
|[[Image:EB1911 Horse - hackney stallion.jpg|390px]]
|}
|-
|align="center"|CLYDESDALE STALLION.
|
|align="center"|HACKNEY STALLION.
|-
|align="center" colspan="3"|BREEDS OF HORSES. (''From Photographs by F. Babbage.'')
|-
|align="center" colspan="3"|{{EB1911 fine print|The comparative sizes of the horses are shown.}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **12** | **12** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **2** | **2** |
| header text     | 'Plate I.' | 'Plate I.' |
| footer text     | 'BREEDS OF HORSES. (From Photographs by F. Babbage.) The comparative sizes of the horses are shown' | 'BREEDS OF HORSES. (From Photographs by F. Babbage.) The comparative sizes of the horses are shown' |

**Verdict:** ✅ identical

### Baseline body
```
Plate I.

{{IMG:EB1911 Horse - shire stallion.jpg|SHIRE STALLION}}

{{IMG:EB1911 Horse - suffolk stallion.jpg|SUFFOLK STALLION}}

{{IMG:EB1911 Horse - clydesdale stallion.jpg|CLYDESDALE STALLION}}

{{IMG:EB1911 Horse - hackney stallion.jpg|HACKNEY STALLION}}

BREEDS OF HORSES. (From Photographs by F. Babbage.) The comparative sizes of the horses are shown
```

### Current body
```
Plate I.

{{IMG:EB1911 Horse - shire stallion.jpg|SHIRE STALLION}}

{{IMG:EB1911 Horse - suffolk stallion.jpg|SUFFOLK STALLION}}

{{IMG:EB1911 Horse - clydesdale stallion.jpg|CLYDESDALE STALLION}}

{{IMG:EB1911 Horse - hackney stallion.jpg|HACKNEY STALLION}}

BREEDS OF HORSES. (From Photographs by F. Babbage.) The comparative sizes of the horses are shown
```

---

## HORSE — vol 13

**Article ID:** 4203242  
**Signature:** `wikitable depth=2 wt=multi ht=0 has_colspan`

### Source excerpt
```
{{right|{{sc|Plate II.}}}}

{|align="center"
|-valign="bottom"
|
{|cellpadding="0" border="1"
|[[Image:EB1911 Horse - thoroughbred stallion.jpg|390px]]
|}
|{{gap}}
|
{|cellpadding="0" border="1"
|[[Image:EB1911 Horse - shetland pony stallion.jpg|390px]]
|}
|-
|align="center"|THOROUGHBRED STALLION.
|
|align="center"|SHETLAND PONY STALLION.
|-
|&nbsp;
|-valign="bottom"
|
{|cellpadding="0" border="1"
|[[Image:EB1911 Horse - coaching stallion.jpg|390px]]
|}
|
|
{|cellpadding="0" border="1"
|[[Image:EB1911 Horse - polo pony stallion.jpg|390px]]
|}
|-
|align="center"|COACHING STALLION.
|
|align="center"|POLO PONY STALLION.
|-
|align="center" colspan="3"|BREEDS OF HORSES. (''From Photographs by F. Babbage.'')
|-
|align="center" colspan="3"|{{EB1911 fine print|The comparative sizes of the horses are shown.}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **12** | **12** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **2** | **2** |
| header text     | 'Plate II.' | 'Plate II.' |
| footer text     | 'BREEDS OF HORSES. (From Photographs by F. Babbage.) The comparative sizes of the horses are shown' | 'BREEDS OF HORSES. (From Photographs by F. Babbage.) The comparative sizes of the horses are shown' |

**Verdict:** ✅ identical

### Baseline body
```
Plate II.

{{IMG:EB1911 Horse - thoroughbred stallion.jpg|THOROUGHBRED STALLION}}

{{IMG:EB1911 Horse - shetland pony stallion.jpg|SHETLAND PONY STALLION}}

{{IMG:EB1911 Horse - coaching stallion.jpg|COACHING STALLION}}

{{IMG:EB1911 Horse - polo pony stallion.jpg|POLO PONY STALLION}}

BREEDS OF HORSES. (From Photographs by F. Babbage.) The comparative sizes of the horses are shown
```

### Current body
```
Plate II.

{{IMG:EB1911 Horse - thoroughbred stallion.jpg|THOROUGHBRED STALLION}}

{{IMG:EB1911 Horse - shetland pony stallion.jpg|SHETLAND PONY STALLION}}

{{IMG:EB1911 Horse - coaching stallion.jpg|COACHING STALLION}}

{{IMG:EB1911 Horse - polo pony stallion.jpg|POLO PONY STALLION}}

BREEDS OF HORSES. (From Photographs by F. Babbage.) The comparative sizes of the horses are shown
```

---

## HOUSE, PLATE I — vol 13

**Article ID:** 4203320  
**Signature:** `html_table depth=0 wt=0 ht=multi`

### Source excerpt
```
<table align=center>
<tr><td>[[File:EB1911 - House Fig. 4.—Musician's House, Reims.jpg]]</td>
<td>[[File:EB1911 - House Fig. 5.—Jew's House, Lincoln.jpg]]</td></tr>
<tr><td {{Ts|pl1|sm|lh11}}>''Photo, Neurdein.''</td>
<td {{Ts|pl15|sm|lh11}}>''Photo, F. Frith & Co.''</td></tr>
<tr><td {{Ts|sm92|lh12|ac}}>{{sc|Fig. 4.}}—MUSICIAN’S HOUSE, REIMS.</td>
<td {{Ts|sm92|lh12|ac}}>{{sc|Fig. 5.}}—JEW’S HOUSE, LINCOLN.</td></tr></table>


<table align=center>
<tr><td>[[File:EB1911 - House Fig. 6.—Hôtel De Cluny, Paris.jpg]]</td></tr>
<tr><td {{Ts|pl1|sm|lh11}}>''Photo, Neurdein.''</td></tr>
<tr><td {{Ts|sm92|lh12|ac}}>{{sc|Fig. 6.}}—HÔTEL DE CLUNY, PARIS.</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - House Fig. 4.—Musician's House, Reims.jpg|MUSICIAN’S HOUSE, REIMS (Photo, Neurdein)}}

{{IMG:EB1911 - House Fig. 5.—Jew's House, Lincoln.jpg|JEW’S HOUSE, LINCOLN (Photo, F. Frith & Co)}}

{{IMG:EB1911 - House Fig. 6.—Hôtel De Cluny, Paris.jpg|HÔTEL DE CLUNY, PARIS (Photo, Neurdein)}}
```

### Current body
```
{{IMG:EB1911 - House Fig. 4.—Musician's House, Reims.jpg|MUSICIAN’S HOUSE, REIMS (Photo, Neurdein)}}

{{IMG:EB1911 - House Fig. 5.—Jew's House, Lincoln.jpg|JEW’S HOUSE, LINCOLN (Photo, F. Frith & Co)}}

{{IMG:EB1911 - House Fig. 6.—Hôtel De Cluny, Paris.jpg|HÔTEL DE CLUNY, PARIS (Photo, Neurdein)}}
```

---

## HOUSE, PLATE II — vol 13

**Article ID:** 4203321  
**Signature:** `html_table depth=0 wt=0 ht=multi`

### Source excerpt
```
<table align=center>
<tr><td {{Ts|pt2}}>[[File:EB1911 - House Fig. 7.—Hôtel de Jacques Cœur, Bourges, Façade.jpg]]</td></tr>
<tr><td {{Ts|pl1|al|sm|lh10}}>''Photo, Neurdein.''</td></tr>
<tr><td {{Ts|sm92|lh11|ac}}>{{sc|Fig. 7.}}—HÔTEL DE JACQUES CŒUR, BOURGES. FAÇADE.</td></tr></table>

<table align=center>
<tr><td {{Ts|ac|pt2|pr2}}>[[File:EB1911 - House Fig. 8.—Half-Timbered House at Hildesheim.jpg]]</td>
<td {{Ts|ac|mc|ma|vbm|pl2}}>[[File:EB1911 - House Fig. 9.—House of John Harvard's Mother, Stratford-On-Avon.jpg]]</td></tr>
<tr><td></td>
<td {{Ts|pl3|vtp|al|sm|lh11}}>''Photo'', ''F. Frith & Co.''</td></tr>
<tr><td {{Ts|sm92|lh12|ac|vtp}}>{{sc|Fig. 8.}}—HALF-TIMBERED HOUSE AT HILDESHEIM.</td>
<td {{Ts|sm92|lh11|ac|pl2}}>{{sc|Fig. 9.}}—HOUSE OF JOHN HARVARD’S MOTHER,<br />STRATFORD-ON-AVON.</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - House Fig. 7.—Hôtel de Jacques Cœur, Bourges, Façade.jpg|HÔTEL DE JACQUES CŒUR, BOURGES. FAÇADE}}

{{IMG:EB1911 - House Fig. 8.—Half-Timbered House at Hildesheim.jpg|HALF-TIMBERED HOUSE AT HILDESHEIM}}

{{IMG:EB1911 - House Fig. 9.—House of John Harvard's Mother, Stratford-On-Avon.jpg|HOUSE OF JOHN HARVARD’S MOTHER, STRATFORD-ON-AVON}}
```

### Current body
```
{{IMG:EB1911 - House Fig. 7.—Hôtel de Jacques Cœur, Bourges, Façade.jpg|HÔTEL DE JACQUES CŒUR, BOURGES. FAÇADE}}

{{IMG:EB1911 - House Fig. 8.—Half-Timbered House at Hildesheim.jpg|HALF-TIMBERED HOUSE AT HILDESHEIM}}

{{IMG:EB1911 - House Fig. 9.—House of John Harvard's Mother, Stratford-On-Avon.jpg|HOUSE OF JOHN HARVARD’S MOTHER, STRATFORD-ON-AVON}}
```

---

## HOUSE, PLATE III — vol 13

**Article ID:** 4203322  
**Signature:** `html_table depth=0 wt=0 ht=multi`

### Source excerpt
```
<table align=center>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 - House Fig. 10.—Speke Hall, near Liverpool.jpg]]</td></tr>
<tr><td {{Ts|pl1|sm|lh11}}>''Photo'', ''Frith & Co.''</td></tr>
<tr><td {{Ts|sm92|lh12|ac}}>{{sc|Fig. 10.}}—SPEKE HALL, NEAR LIVERPOOL.</td></tr></table>

<table align=center>
<tr><td {{Ts|ac|mc|ma|pt15}}>[[File:EB1911 - House Fig. 11.—Moreton old hall, near Congleton, Cheshire.jpg]]</td></tr>
<tr><td {{Ts|pl1|sm|lh11}}>''Photo'', ''F. Frith & Co.''</td></tr>
<tr><td {{Ts|sm92|lh12|ac}}>{{sc|Fig. 11.}}—MORETON OLD HALL, NEAR CONGLETON, CHESHIRE.</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - House Fig. 10.—Speke Hall, near Liverpool.jpg|SPEKE HALL, NEAR LIVERPOOL (Photo, Frith & Co)}}

{{IMG:EB1911 - House Fig. 11.—Moreton old hall, near Congleton, Cheshire.jpg|MORETON OLD HALL, NEAR CONGLETON, CHESHIRE (Photo, F. Frith & Co)}}
```

### Current body
```
{{IMG:EB1911 - House Fig. 10.—Speke Hall, near Liverpool.jpg|SPEKE HALL, NEAR LIVERPOOL (Photo, Frith & Co)}}

{{IMG:EB1911 - House Fig. 11.—Moreton old hall, near Congleton, Cheshire.jpg|MORETON OLD HALL, NEAR CONGLETON, CHESHIRE (Photo, F. Frith & Co)}}
```

---

## HOUSE, PLATE IV — vol 13

**Article ID:** 4203323  
**Signature:** `html_table depth=0 wt=0 ht=multi`

### Source excerpt
```
<table align=center>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 - House Fig. 12.—South court of Sutton Place, Surrey, 1525.jpg]]</td></tr>
<tr><td {{Ts|pl1|sm|lh11}}>From Garner and Stratton, ''Domestic Architecture of England during the Tudor Period'', 1910. By permission of B. T. Batsford.</td></tr>
<tr><td {{Ts|sm92|lh12|ac}}>{{sc|Fig. 12.}}—SOUTH COURT OF SUTTON PLACE, SURREY, 1525.</td></tr></table>

<table align=center>
<tr><td {{Ts|ac|mc|ma|pt15}}>[[File:EB1911 - House Fig. 13.—Moyns park, Essex, 1580.jpg]]</td></tr>
<tr><td {{Ts|pl1|sm|lh11}}>From ''Gotch'', ''Architecture of the Renaissance in England'', 1894. By permission of B. T. Batsford.</td></tr>
<tr><td {{Ts|sm92|lh12|ac}}>{{sc|Fig. 13.}}—MOYNS PARK, ESSEX, 1580.</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - House Fig. 12.—South court of Sutton Place, Surrey, 1525.jpg|SOUTH COURT OF SUTTON PLACE, SURREY, 1525 (By permission of B. T. Batsford)}}

{{IMG:EB1911 - House Fig. 13.—Moyns park, Essex, 1580.jpg|MOYNS PARK, ESSEX, 1580 (By permission of B. T. Batsford)}}
```

### Current body
```
{{IMG:EB1911 - House Fig. 12.—South court of Sutton Place, Surrey, 1525.jpg|SOUTH COURT OF SUTTON PLACE, SURREY, 1525 (By permission of B. T. Batsford)}}

{{IMG:EB1911 - House Fig. 13.—Moyns park, Essex, 1580.jpg|MOYNS PARK, ESSEX, 1580 (By permission of B. T. Batsford)}}
```

---

## HOUSE, PLATE V — vol 13

**Article ID:** 4203328  
**Signature:** `html_table depth=0 wt=0 ht=multi`

### Source excerpt
```
<table align=center>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 - House Fig. 14.—Ham house, Petersham, 1610.jpg]]</td></tr>
<tr><td {{Ts|pl1|sm|lh11}}>From Belcher and Macartney, ''Later Renaissance Architecture in England'', 1901. By permission of B. T. Batsford.</td></tr>
<tr><td {{Ts|sm92|lh12|ac}}>{{sc|Fig. 14.}}—HAM HOUSE, PETERSHAM, 1610.</td></tr></table>

<table align=center>
<tr><td {{Ts|ac|mc|ma|pt15}}>[[File:EB1911 - House Fig. 15.—Bramshill, Hampshire, 1612.jpg]]</td></tr>
<tr><td {{Ts|pl1|sm|lh11}}>From Gotch, ''Architecture of the Renaissance in England'', 1894. By permission of B. T. Batsford.</td></tr>
<tr><td {{Ts|sm92|lh12|ac}}>{{sc|Fig. 15.}}—BRAMSHILL, HAMPSHIRE, 1612.</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - House Fig. 14.—Ham house, Petersham, 1610.jpg|HAM HOUSE, PETERSHAM, 1610 (By permission of B. T. Batsford)}}

{{IMG:EB1911 - House Fig. 15.—Bramshill, Hampshire, 1612.jpg|BRAMSHILL, HAMPSHIRE, 1612 (By permission of B. T. Batsford)}}
```

### Current body
```
{{IMG:EB1911 - House Fig. 14.—Ham house, Petersham, 1610.jpg|HAM HOUSE, PETERSHAM, 1610 (By permission of B. T. Batsford)}}

{{IMG:EB1911 - House Fig. 15.—Bramshill, Hampshire, 1612.jpg|BRAMSHILL, HAMPSHIRE, 1612 (By permission of B. T. Batsford)}}
```

---

## HOUSE, PLATE VI — vol 13

**Article ID:** 4203329  
**Signature:** `html_table depth=0 wt=0 ht=multi`

### Source excerpt
```
<table align=center>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 - House Fig. 16.—The earl of Burlington’s villa, Chiswick. 18th century.jpg]]</td></tr>
<tr><td {{Ts|pl.5|sm|lh11}}>From Belcher and Macartney, ''Later Renaissance Architecture in England'', By permission of B. T. Batsford.</td></tr>
<tr><td {{Ts|sm92|lh12|ac}}>{{sc|Fig. 16.}}—THE EARL OF BURLINGTON’S VILLA, CHISWICK. EIGHTEENTH CENTURY.</td></tr></table>

<table align=center>
<tr><td {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 - House Fig. 17.—Houses in Cavendish square, London. 18th century.jpg]]</td></tr>
<tr><td {{Ts|pl.5|sm|lh11}}>From the same source as above.</td></tr>
<tr><td {{Ts|sm92|lh12|ac}}>{{sc|Fig. 17.}}—HOUSES IN CAVENDISH SQUARE, LONDON. EIGHTEENTH CENTURY.</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 2 | 2 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - House Fig. 16.—The earl of Burlington’s villa, Chiswick. 18th century.jpg|From Belcher and Macartney, Later Renaissance Architecture in England, By permission of B. T. Batsford}}

{{IMG:EB1911 - House Fig. 17.—Houses in Cavendish square, London. 18th century.jpg|From the same source as above}}

{{LEGEND:THE EARL OF BURLINGTON’S VILLA, CHISWICK. EIGHTEENTH CENTURY}LEGEND}

{{LEGEND:HOUSES IN CAVENDISH SQUARE, LONDON. EIGHTEENTH CENTURY}LEGEND}
```

### Current body
```
{{IMG:EB1911 - House Fig. 16.—The earl of Burlington’s villa, Chiswick. 18th century.jpg|From Belcher and Macartney, Later Renaissance Architecture in England, By permission of B. T. Batsford}}

{{IMG:EB1911 - House Fig. 17.—Houses in Cavendish square, London. 18th century.jpg|From the same source as above}}

{{LEGEND:THE EARL OF BURLINGTON’S VILLA, CHISWICK. EIGHTEENTH CENTURY}LEGEND}

{{LEGEND:HOUSES IN CAVENDISH SQUARE, LONDON. EIGHTEENTH CENTURY}LEGEND}
```

---

## ILLUMINATED MANUSCRIPTS, PLATE II — vol 14

**Article ID:** 4203774  
**Signature:** `other depth=0 wt=0 ht=1`

### Source excerpt
```
<section begin="Plate2" /><table align=center>
<tr><td>[[File:EB1911 ILLUMINATED MSS. — Psalter of Westminster Abbey.—late 12th century.jpg]]</td></tr>
<tr><td {{Ts|sm92|lh13|ac}}>PSALTER OF WESTMINSTER ABBEY.—LATE TWELFTH CENTURY.<br />(British Museum. ''Royal MS.'' 2A. xxii.)</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **2** | **2** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 ILLUMINATED MSS. — Psalter of Westminster Abbey.—late 12th century.jpg|PSALTER OF WESTMINSTER ABBEY.—LATE TWELFTH CENTURY. (British Museum. Royal MS. 2A. xxii.)}}
```

### Current body
```
{{IMG:EB1911 ILLUMINATED MSS. — Psalter of Westminster Abbey.—late 12th century.jpg|PSALTER OF WESTMINSTER ABBEY.—LATE TWELFTH CENTURY. (British Museum. Royal MS. 2A. xxii.)}}
```

---

## ILLUMINATED MANUSCRIPTS, PLATE III — vol 14

**Article ID:** 4203775  
**Signature:** `html_table depth=0 wt=0 ht=1`

### Source excerpt
```
<table align=center>
<tr><td>[[File:EB1911 ILLUMINATED MSS. —Lectionary, of the use of Paris.—late 13th century.jpg]]</td></tr>
<tr><td {{Ts|sm92|lh13|ac}}>LECTIONARY, OF THE USE OF PARIS. LATE THIRTEENTH CENTURY. (British Museum. Add. M.S. 17,341.)</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **2** | **2** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 ILLUMINATED MSS. —Lectionary, of the use of Paris.—late 13th century.jpg|LECTIONARY, OF THE USE OF PARIS. LATE THIRTEENTH CENTURY. (British Museum. Add. M.S. 17,341.)}}
```

### Current body
```
{{IMG:EB1911 ILLUMINATED MSS. —Lectionary, of the use of Paris.—late 13th century.jpg|LECTIONARY, OF THE USE OF PARIS. LATE THIRTEENTH CENTURY. (British Museum. Add. M.S. 17,341.)}}
```

---

## ILLUMINATED MANUSCRIPTS, PLATE IV — vol 14

**Article ID:** 4203776  
**Signature:** `other depth=0 wt=0 ht=1`

### Source excerpt
```
<section begin="Plate4" /><table align=center>
<tr><td>[[File:EB1911 ILLUMINATED MSS. — Durandus. De divinis officiis. 14th century. Italian school.jpg]]</td></tr>
<tr><td {{Ts|sm92|ac}}>DURANDUS. DE DIVINIS OFFICIIS. FOURTEENTH CENTURY. Italian School. (British Museum. Add. MS. 31,032.)</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **2** | **2** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 ILLUMINATED MSS. — Durandus. De divinis officiis. 14th century. Italian school.jpg|DURANDUS. DE DIVINIS OFFICIIS. FOURTEENTH CENTURY. Italian School. (British Museum. Add. MS. 31,032.)}}
```

### Current body
```
{{IMG:EB1911 ILLUMINATED MSS. — Durandus. De divinis officiis. 14th century. Italian school.jpg|DURANDUS. DE DIVINIS OFFICIIS. FOURTEENTH CENTURY. Italian School. (British Museum. Add. MS. 31,032.)}}
```

---

## ILLUMINATED MANUSCRIPTS, PLATE V — vol 14

**Article ID:** 4203777  
**Signature:** `html_table depth=0 wt=0 ht=1`

### Source excerpt
```
<table align=center>
<tr><td>[[File:EB1911 ILLUMINATED MSS. — Valerius maximus. About A.D. 1475. Executed for Philippe de Comines.jpg]]</td></tr>
<tr><td {{Ts|sm92|ac}}>VALERIUS MAXIMUS. ABOUT A.D. 1475. Executed for Philippe de Comines. (British Museum. ''Harley M.S.'' 4374.)</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **2** | **2** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 ILLUMINATED MSS. — Valerius maximus. About A.D. 1475. Executed for Philippe de Comines.jpg|Executed for Philippe de Comines. (British Museum. Harley M.S. 4374.)}}
```

### Current body
```
{{IMG:EB1911 ILLUMINATED MSS. — Valerius maximus. About A.D. 1475. Executed for Philippe de Comines.jpg|Executed for Philippe de Comines. (British Museum. Harley M.S. 4374.)}}
```

---

## INDIAN ARCHITECTURE — vol 14

**Article ID:** 4203858  
**Signature:** `wikitable depth=2 wt=multi ht=0 has_colspan`

### Source excerpt
```
{{right|{{sc|Plate I.}}}}
{|{{ts|mc|border-spacing:0}}
|{{ts|p0}}|
{| {{ts|border-spacing:0}}
|{{ts|ba|padding:1px;}}|[[Image:EB1911 Indian Architecture - Sānchi North Gateway.jpg|x600px]]
|}
|{{ts|p0}}|&emsp;
|{{ts|p0}}|
{| {{ts|border-spacing:0}}
|{{ts|ba|padding:1px;}}|[[Image:EB1911 Indian Architecture - Kutb Minâr near Delhi.jpg|x600px]]
|}
|-
|{{ts|p0|ac}} rowspan="2"|{{sc|Fig. 8.}}—SĀNCHI NORTH GATEWAY.
|{{ts|p0}}|
|{{ts|p0}}|{{x-smaller|&ensp;''Photo, F. Frith & Co.''}}
|-
|{{ts|p0}}|
|{{ts|p0|ac}}|{{sc|Fig. 9.}}—THE KUTB MINÂR NEAR DELHI.
|-
|{{ts|p0}}|&nbsp;
|-
|{{ts|p0}} colspan="3"|
{| {{ts|border-spacing:0}}
|{{ts|ba|padding:1px;}}|[[Image:EB1911 Indian Architecture - Sher Shah's Mosque at Delhi.jpg|x350px]]
|}
|-
|{{ts|p0}} colspan="3"|{{x-smaller|&ensp;''Photo lent by the India Office.''}}
|-
|{{ts|p0|ac}} colspan="3" |{{sc|Fig. 10.}}—SHER SHAH’S MOSQUE AT DELHI.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'Plate I' | 'Plate I' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
Plate I

{{IMG:EB1911 Indian Architecture - Sānchi North Gateway.jpg|SĀNCHI NORTH GATEWAY}}

{{IMG:EB1911 Indian Architecture - Kutb Minâr near Delhi.jpg|THE KUTB MINÂR NEAR DELHI}}

{{IMG:EB1911 Indian Architecture - Sher Shah's Mosque at Delhi.jpg|SHER SHAH’S MOSQUE AT DELHI}}
```

### Current body
```
Plate I

{{IMG:EB1911 Indian Architecture - Sānchi North Gateway.jpg|SĀNCHI NORTH GATEWAY}}

{{IMG:EB1911 Indian Architecture - Kutb Minâr near Delhi.jpg|THE KUTB MINÂR NEAR DELHI}}

{{IMG:EB1911 Indian Architecture - Sher Shah's Mosque at Delhi.jpg|SHER SHAH’S MOSQUE AT DELHI}}
```

---

## INDIAN ARCHITECTURE — vol 14

**Article ID:** 4203859  
**Signature:** `wikitable depth=2 wt=multi ht=0`

### Source excerpt
```
{{sc|Plate II.}}
{|{{ts|mc}}
|
{|
|{{ts|ba|padding:1px;}}|[[Image:EB1911 Indian Architecture - Great Temple at Halebid.jpg|700px]]
|}
|-
|{{ts|ac}}|{{sc|Fig. 11.}}—GREAT TEMPLE AT HALEBID.
|-
|
{|
|{{ts|ba|padding:1px;}}|[[Image:EB1911 Indian Architecture - Roof of Dome of Vimala's Temple on Mount Abu.jpg|700px]]
|}
|-
|{{ts|ac}}|{{sc|Fig. 12.}}—ROOF OF DOME OF VIMALA’S TEMPLE ON MOUNT ABU.
|-
|{{ts|ac}}|{{x-smaller|(''From Photographs kindly lent by the India Office.'')}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **7** | **7** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'Plate II' | 'Plate II' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
Plate II

{{IMG:EB1911 Indian Architecture - Great Temple at Halebid.jpg|GREAT TEMPLE AT HALEBID}}

{{IMG:EB1911 Indian Architecture - Roof of Dome of Vimala's Temple on Mount Abu.jpg|ROOF OF DOME OF VIMALA’S TEMPLE ON MOUNT ABU}}

{{LEGEND:(From Photographs kindly lent by the India Office.)}LEGEND}
```

### Current body
```
Plate II

{{IMG:EB1911 Indian Architecture - Great Temple at Halebid.jpg|GREAT TEMPLE AT HALEBID}}

{{IMG:EB1911 Indian Architecture - Roof of Dome of Vimala's Temple on Mount Abu.jpg|ROOF OF DOME OF VIMALA’S TEMPLE ON MOUNT ABU}}

{{LEGEND:(From Photographs kindly lent by the India Office.)}LEGEND}
```

---

## INDIAN ARCHITECTURE — vol 14

**Article ID:** 4203860  
**Signature:** `wikitable depth=1 wt=1 ht=0 has_colspan`

### Source excerpt
```
{{right|{{sc|Plate III.}}}}
{|align="center" cellpadding="0" cellspacing="0" width="800"
|[[Image:EB1911 Indian Architecture - Kanārak Temple of Sūrya.jpg|x440px]]
|&emsp;
|[[Image:EB1911 Indian Architecture - Tomb of Mahommed Adil Shāh.jpg|x440px]]
|-valign="top"
|align="center"|
{{sc|Fig. 13.}}—KANĀRAK TEMPLE OF SŪRYA, OR BLACK
PAGODA, FROM THE EAST.
|
|align="center"|
{{sc|Fig. 14.}}—TOMB OF MAHOMMED ADIL SHĀH,
BIJAPUR.
|-
|&nbsp;
|-
|colspan="3"|[[Image:EB1911 Indian Architecture - Jama Masjid at Ahmedābad.jpg|x650px]]
|-
|colspan="3" align="center"|{{sc|Fig. 15.}}—JAMA MASJID AT AHMEDĀBAD.
|-
|colspan="3" align="center"|{{x-smaller|''From Photographs kindly lent by the India Office.''}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **10** | **10** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **2** | **2** |
| header text     | 'Plate III' | 'Plate III' |
| footer text     | 'From Photographs kindly lent by the India Office' | 'From Photographs kindly lent by the India Office' |

**Verdict:** ✅ identical

### Baseline body
```
Plate III

{{IMG:EB1911 Indian Architecture - Kanārak Temple of Sūrya.jpg|KANĀRAK TEMPLE OF SŪRYA, OR BLACK PAGODA, FROM THE EAST}}

{{IMG:EB1911 Indian Architecture - Tomb of Mahommed Adil Shāh.jpg|TOMB OF MAHOMMED ADIL SHĀH, BIJAPUR}}

{{IMG:EB1911 Indian Architecture - Jama Masjid at Ahmedābad.jpg|JAMA MASJID AT AHMEDĀBAD}}

From Photographs kindly lent by the India Office
```

### Current body
```
Plate III

{{IMG:EB1911 Indian Architecture - Kanārak Temple of Sūrya.jpg|KANĀRAK TEMPLE OF SŪRYA, OR BLACK PAGODA, FROM THE EAST}}

{{IMG:EB1911 Indian Architecture - Tomb of Mahommed Adil Shāh.jpg|TOMB OF MAHOMMED ADIL SHĀH, BIJAPUR}}

{{IMG:EB1911 Indian Architecture - Jama Masjid at Ahmedābad.jpg|JAMA MASJID AT AHMEDĀBAD}}

From Photographs kindly lent by the India Office
```

---

## INDIAN ARCHITECTURE — vol 14

**Article ID:** 4203861  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{{sc|Plate IV.}}
{|align="center"
|[[Image:EB1911 Indian Architecture - Tomb of Itimad-ud-Daula.jpg|700px]]
|-style="font-size: 70%"
|&ensp;''Photo, F. Frith & Co.''
|-
|align="center"|{{sc|Fig. 16.}}—TOMB OF PRINCE ITIMAD-UD-DAULA, AGRA.
|-
|[[Image:EB1911 Indian Architecture - Taj Mahal.jpg|700px]]
|-style="font-size: 70%"
|&ensp;''Photo, Johnston & Hoffmann.''
|-
|align="center"|{{sc|Fig. 17.}}—THE TAJ MAHAL, AGRA.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'Plate IV' | 'Plate IV' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
Plate IV

{{IMG:EB1911 Indian Architecture - Tomb of Itimad-ud-Daula.jpg|TOMB OF PRINCE ITIMAD-UD-DAULA, AGRA (Photo, F. Frith & Co)}}

{{IMG:EB1911 Indian Architecture - Taj Mahal.jpg|THE TAJ MAHAL, AGRA (Photo, Johnston & Hoffmann)}}
```

### Current body
```
Plate IV

{{IMG:EB1911 Indian Architecture - Tomb of Itimad-ud-Daula.jpg|TOMB OF PRINCE ITIMAD-UD-DAULA, AGRA (Photo, F. Frith & Co)}}

{{IMG:EB1911 Indian Architecture - Taj Mahal.jpg|THE TAJ MAHAL, AGRA (Photo, Johnston & Hoffmann)}}
```

---

## INFANTRY, PLATE I — vol 14

**Article ID:** 4203905  
**Signature:** `html_table depth=0 wt=0 ht=multi has_colspan`

### Source excerpt
```
<table align=center>
<tr><td colspan=3 {{Ts|ac|mc|ma|pt1}}>[[File:EB1911 Infantry Plate I - Dreux.jpg]]</td></tr>
<tr><td>{{em|24}}</td><td {{Ts|sm92|lh12|ac|pl5|pr5}}>DREUX—1562.</td><td {{Ts|pl.5|pr.5|vtp|ar|sm85}}>(''From Hardÿ de Périni’s Batailles Françaises, by permission.'')</td></tr>
</table>

<table align=center {{Ts|pt1}}>
<tr><td align=center>[[File:EB1911 Infantry Plate I - Lutzen.jpg]]</td></tr>
<tr><td {{Ts|sm92|lh12|ac}}>LÜTZEN—1632.</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **5** | **5** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Infantry Plate I - Dreux.jpg|DREUX—1562}}

{{IMG:EB1911 Infantry Plate I - Lutzen.jpg|LÜTZEN—1632}}

{{LEGEND:(From Hardÿ de Périni’s Batailles Françaises, by permission.)}LEGEND}
```

### Current body
```
{{IMG:EB1911 Infantry Plate I - Dreux.jpg|DREUX—1562}}

{{IMG:EB1911 Infantry Plate I - Lutzen.jpg|LÜTZEN—1632}}

{{LEGEND:(From Hardÿ de Périni’s Batailles Françaises, by permission.)}LEGEND}
```

---

## INFANTRY, PLATE II — vol 14

**Article ID:** 4203906  
**Signature:** `html_table depth=0 wt=0 ht=multi`

### Source excerpt
```
{{center|[[File:EB1911 Infantry Plate II - Evolutions of the Column and Skirmishers.jpg]]}}

<table align=center>
<tr><td {{Ts|ac|pt2}}>[[File:EB1911 Infantry Plate II - De Cissey's Counter-attack.jpg]]</td></tr>
<tr><td {{Ts|sm92|lh12|ac}}>VIONVILLE DE CISSEY’S COUNTER-ATTACK (SEEN FROM REAR OF PRUSSIAN 38th BRIGADE).</td></tr></table>

<table align=center>
<tr><td {{Ts|ac|pt15}}>[[File:EB1911 Infantry Plate II - March under artillery fire.jpg]]</td></tr>
<tr><td {{Ts|vtp|ar|sm85|lh10}}>(''From Revue d’Infanterie'', 1909.)</td></tr>
<tr><td {{Ts|sm92|lh11|ac}}>APPROACH-MARCH UNDER ARTILLERY FIRE, FRENCH PRINCIPLES (FROM ENEMY’S ARTILLERY POSITION).</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'center' | 'center' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
center

{{IMG:EB1911 Infantry Plate II - Evolutions of the Column and Skirmishers.jpg|VIONVILLE DE CISSEY’S COUNTER-ATTACK (SEEN FROM REAR OF PRUSSIAN 38th BRIGADE)}}

{{IMG:EB1911 Infantry Plate II - De Cissey's Counter-attack.jpg|(From Revue d’Infanterie, 1909.)}}

{{IMG:EB1911 Infantry Plate II - March under artillery fire.jpg|APPROACH-MARCH UNDER ARTILLERY FIRE, FRENCH PRINCIPLES (FROM ENEMY’S ARTILLERY POSITION)}}
```

### Current body
```
center

{{IMG:EB1911 Infantry Plate II - Evolutions of the Column and Skirmishers.jpg|VIONVILLE DE CISSEY’S COUNTER-ATTACK (SEEN FROM REAR OF PRUSSIAN 38th BRIGADE)}}

{{IMG:EB1911 Infantry Plate II - De Cissey's Counter-attack.jpg|(From Revue d’Infanterie, 1909.)}}

{{IMG:EB1911 Infantry Plate II - March under artillery fire.jpg|APPROACH-MARCH UNDER ARTILLERY FIRE, FRENCH PRINCIPLES (FROM ENEMY’S ARTILLERY POSITION)}}
```

---

## JAPAN, PLATE I — vol 15

**Article ID:** 4204360  
**Signature:** `html_table depth=0 wt=0 ht=1 toplegend`

### Source excerpt
```
{{c|{{larger|PAINTING}}

{{EB1911 Fine Print|(''These illustrations are reproduced by permission of the Kokka Company'', ''Tokyo'', ''Japan''.)}}}}


<table align="center" cellpadding="0" cellspacing="0">
<tr valign="bottom">
<td>[[Image:EB1911 Japan - Manjusri, Deity of Wisdom.jpg|315px]]</td>
<td>&emsp;[[Image:EB1911 Japan - Waterfall of Nachi.jpg|263px]]&emsp;
<td>[[Image:EB1911 Japan - Priest Daito-Kokushi.jpg|330px]]</td>
</tr>
<tr style="line-height:130%; vertical-align:top;">
<td width=320 align="center">{{sc|Fig. 1.}}—MANJUSRI, DEITY OF WISDOM. Kosé School (13th century).</td>
<td width=295 align="center">{{sc|Fig. 2.}}—WATERFALL OF NACHI.<br />Attributed to Kanaoka (9th century).</td>
<td width=335 align="center">{{sc|Fig. 3.}}—PORTRAIT OF THE PRIEST DAITO-KOKUSHI.&emsp;Tosa School (14th century).</td>
</tr>
</table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'PAINTING (These illustrations are reproduced by permission of the Kokka Company, Tokyo, Japan.)' | 'PAINTING (These illustrations are reproduced by permission of the Kokka Company, Tokyo, Japan.)' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
PAINTING (These illustrations are reproduced by permission of the Kokka Company, Tokyo, Japan.)

{{IMG:EB1911 Japan - Manjusri, Deity of Wisdom.jpg|MANJUSRI, DEITY OF WISDOM. Kosé School (13th century)}}

{{IMG:EB1911 Japan - Waterfall of Nachi.jpg|WATERFALL OF NACHI. Attributed to Kanaoka (9th century)}}

{{IMG:EB1911 Japan - Priest Daito-Kokushi.jpg|PORTRAIT OF THE PRIEST DAITO-KOKUSHI. Tosa School (14th century)}}
```

### Current body
```
PAINTING (These illustrations are reproduced by permission of the Kokka Company, Tokyo, Japan.)

{{IMG:EB1911 Japan - Manjusri, Deity of Wisdom.jpg|MANJUSRI, DEITY OF WISDOM. Kosé School (13th century)}}

{{IMG:EB1911 Japan - Waterfall of Nachi.jpg|WATERFALL OF NACHI. Attributed to Kanaoka (9th century)}}

{{IMG:EB1911 Japan - Priest Daito-Kokushi.jpg|PORTRAIT OF THE PRIEST DAITO-KOKUSHI. Tosa School (14th century)}}
```

---

## JAPAN, PLATE II — vol 15

**Article ID:** 4204361  
**Signature:** `html_table depth=0 wt=0 ht=1 toplegend`

### Source excerpt
```
{{c|{{larger|PAINTING}}}}

<table {{Ts|ma|ac|width:800px}}>
<tr><td>[[Image:EB1911 Japan - Priests caricatured by Toba Sojo.jpg|800px]]</td></tr>
<tr><td>{{sc|Fig. 4.}}—PRIESTS CARICATURED BY ANIMALS. By Toba Sojo (1053–1140).</td></tr>
<tr><td>&nbsp;</td></tr>
<tr><td>[[Image:EB1911 Japan - Escape of the emperor by Keion.jpg|800px]]</td></tr>
<tr><td>{{sc|Fig. 5.}}—ESCAPE OF THE EMPEROR DISGUISED AS A WOMAN. Scene from the Civil War. By Keion (13th century).</td></tr>
</table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Japan - Priests caricatured by Toba Sojo.jpg|PRIESTS CARICATURED BY ANIMALS. By Toba Sojo (1053–1140)}}

{{IMG:EB1911 Japan - Escape of the emperor by Keion.jpg|ESCAPE OF THE EMPEROR DISGUISED AS A WOMAN. Scene from the Civil War. By Keion (13th century)}}
```

### Current body
```
{{IMG:EB1911 Japan - Priests caricatured by Toba Sojo.jpg|PRIESTS CARICATURED BY ANIMALS. By Toba Sojo (1053–1140)}}

{{IMG:EB1911 Japan - Escape of the emperor by Keion.jpg|ESCAPE OF THE EMPEROR DISGUISED AS A WOMAN. Scene from the Civil War. By Keion (13th century)}}
```

---

## JAPAN, PLATE III — vol 15

**Article ID:** 4204362  
**Signature:** `html_table depth=0 wt=0 ht=1 toplegend`

### Source excerpt
```
{{c|{{larger|PAINTING}}}}

<table align="center" cellpadding="0" cellspacing="0">
<tr valign="bottom">
<td>[[Image:EB1911 Japan - Kwannon.jpg|295px]]</td>
<td>&nbsp;</td>
<td>[[Image:EB1911 Japan - Landscape in snow.jpg|323px]]
<td>&nbsp;</td>
<td>[[Image:EB1911 Japan - Jurojin.jpg|298px]]</td>
</tr>
<tr style="line-height:130%; vertical-align:top;">
<td width="295" align="center">{{sc|Fig. 6.}}—KWANNON, GODDESS OF MERCY. By Mincho or Cho Densu (1352–1431).</td>
<td></td>
<td width="323" align="center">{{sc|Fig. 7.}}—LANDSCAPE IN SNOW. By Kano Motonobu (1476–1559).</td>
<td></td>
<td width="298" align="center">{{sc|Fig. 8.}}—JUROJIN. By Sesshiu (1420–1506).</td>
</tr>
</table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Japan - Kwannon.jpg|KWANNON, GODDESS OF MERCY. By Mincho or Cho Densu (1352–1431)}}

{{IMG:EB1911 Japan - Landscape in snow.jpg|LANDSCAPE IN SNOW. By Kano Motonobu (1476–1559)}}

{{IMG:EB1911 Japan - Jurojin.jpg|JUROJIN. By Sesshiu (1420–1506)}}
```

### Current body
```
{{IMG:EB1911 Japan - Kwannon.jpg|KWANNON, GODDESS OF MERCY. By Mincho or Cho Densu (1352–1431)}}

{{IMG:EB1911 Japan - Landscape in snow.jpg|LANDSCAPE IN SNOW. By Kano Motonobu (1476–1559)}}

{{IMG:EB1911 Japan - Jurojin.jpg|JUROJIN. By Sesshiu (1420–1506)}}
```

---

## JAPAN, PLATE IV — vol 15

**Article ID:** 4204363  
**Signature:** `c_centered depth=0 wt=0 ht=0 toplegend`

### Source excerpt
```
{{c|{{larger|PAINTING}}

[[Image:EB1911 Japan - Plum Trees and Stream.jpg|566px]]

{{sc|Fig. 9.}}—PLUM TREES AND STREAM—SCREEN ON GOLD GROUND. By Korin (1661–1716).


[[Image:EB1911 Japan - Peacocks.jpg|525px]]

{{sc|Fig. 10.}}—PEACOCKS. By Ganku (1749–1838).}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'c PAINTING' | 'c PAINTING' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
c PAINTING

{{IMG:EB1911 Japan - Plum Trees and Stream.jpg|PLUM TREES AND STREAM—SCREEN ON GOLD GROUND. By Korin (1661–1716)}}

{{IMG:EB1911 Japan - Peacocks.jpg|PEACOCKS. By Ganku (1749–1838)}}
```

### Current body
```
c PAINTING

{{IMG:EB1911 Japan - Plum Trees and Stream.jpg|PLUM TREES AND STREAM—SCREEN ON GOLD GROUND. By Korin (1661–1716)}}

{{IMG:EB1911 Japan - Peacocks.jpg|PEACOCKS. By Ganku (1749–1838)}}
```

---

## JAPAN, PLATE V — vol 15

**Article ID:** 4204364  
**Signature:** `html_table depth=0 wt=0 ht=1 has_colspan toplegend`

### Source excerpt
```
{{c|{{larger|SCULPTURE}}}}

<table align="center" cellpadding="0" cellspacing="0">
<tr valign="bottom">
<td>[[Image:EB1911 Japan - Vajra Malla.jpg|371px]]</td>
<td>{{gap|2.5em}}</td>
<td>[[Image:EB1911 Japan - Statue of Asanga.jpg|438px]]</td>
</tr>
<tr valign="top">
<td align="center">{{sc|Fig. 11.}}—VAJRA MALLA. By Unkei (13th century).</td>
<td></td>
<td align="center">{{sc|Fig. 12.}}—STATUE OF ASANGA (12th century, artist unknown).</td>
</tr>
<tr><td colspan="3" align="center">
[[Image:EB1911 Japan - Statues of Buddha Ami’tabha and Two Bodhisattvas.jpg|553px]]
</td></tr>
<tr><td colspan="3" align="center">
{{sc|Fig. 13.}}—STATUES OF BUDDHA AMI’TABHA AND TWO BODHISATTVAS (7th century).
</td></tr>
</table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Japan - Vajra Malla.jpg|VAJRA MALLA. By Unkei (13th century)}}

{{IMG:EB1911 Japan - Statue of Asanga.jpg|STATUE OF ASANGA (12th century, artist unknown)}}

{{IMG:EB1911 Japan - Statues of Buddha Ami’tabha and Two Bodhisattvas.jpg|STATUES OF BUDDHA AMI’TABHA AND TWO BODHISATTVAS (7th century)}}
```

### Current body
```
{{IMG:EB1911 Japan - Vajra Malla.jpg|VAJRA MALLA. By Unkei (13th century)}}

{{IMG:EB1911 Japan - Statue of Asanga.jpg|STATUE OF ASANGA (12th century, artist unknown)}}

{{IMG:EB1911 Japan - Statues of Buddha Ami’tabha and Two Bodhisattvas.jpg|STATUES OF BUDDHA AMI’TABHA AND TWO BODHISATTVAS (7th century)}}
```

---

## JAPAN, PLATE VI — vol 15

**Article ID:** 4204365  
**Signature:** `html_table depth=0 wt=0 ht=1 has_colspan toplegend`

### Source excerpt
```
{{c|{{larger|METAL WORK AND LACQUER}}}}

<table {{Ts|ma}}>
<tr valign="bottom">
<td rowspan="5">[[Image:EB1911 Japan - Door of Bronze Lantern.jpg|384px]]</td>
<td rowspan="6">&emsp;</td>
<td rowspan="3">[[Image:EB1911 Japan - Bronze Duck Incense Burner.jpg|332px]]</td>
<td rowspan="3">{{gap|2em}}</td>
<td>[[Image:EB1911 Japan - Bronze Mirror.jpg|442px]]</td>
</tr>
<tr><td width="442px" align="center">{{sc|Fig. 15.}}—BRONZE DUCK INCENSE BURNER (15th century). British Museum.</td></tr>
<tr><td width="442px">{{sc|Fig. 16.}}—BRONZE MIRROR (12th to 13th century).</td></tr>
<tr><td>&nbsp;</td></tr>
<tr><td colspan="3" align="center">[[Image:EB1911 Japan - Inkstone Box in Lacquer.jpg|786px]]</td>
<tr>
<td width="384px" align="center">{{sc|Fig 14.}}—DOOR OF BRONZE LANTERN IN THE TODAI TEMPLE (8th century).</td>
<td colspan="3" align="center">{{sc|Fig. 17.}}—INKSTONE BOX IN LACQUER. By Koyetsu (1557–1637).</td>
</tr>
</table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **9** | **9** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Japan - Door of Bronze Lantern.jpg|BRONZE DUCK INCENSE BURNER (15th century). British Museum}}

{{IMG:EB1911 Japan - Bronze Duck Incense Burner.jpg|BRONZE MIRROR (12th to 13th century)}}

{{IMG:EB1911 Japan - Bronze Mirror.jpg|DOOR OF BRONZE LANTERN IN THE TODAI TEMPLE (8th century)}}

{{IMG:EB1911 Japan - Inkstone Box in Lacquer.jpg|INKSTONE BOX IN LACQUER. By Koyetsu (1557–1637)}}

{{LEGEND:METAL WORK AND LACQUER}LEGEND}
```

### Current body
```
{{IMG:EB1911 Japan - Door of Bronze Lantern.jpg|BRONZE DUCK INCENSE BURNER (15th century). British Museum}}

{{IMG:EB1911 Japan - Bronze Duck Incense Burner.jpg|BRONZE MIRROR (12th to 13th century)}}

{{IMG:EB1911 Japan - Bronze Mirror.jpg|DOOR OF BRONZE LANTERN IN THE TODAI TEMPLE (8th century)}}

{{IMG:EB1911 Japan - Inkstone Box in Lacquer.jpg|INKSTONE BOX IN LACQUER. By Koyetsu (1557–1637)}}

{{LEGEND:METAL WORK AND LACQUER}LEGEND}
```

---

## JAPAN, PLATE VII — vol 15

**Article ID:** 4204366  
**Signature:** `html_table depth=0 wt=0 ht=multi has_colspan toplegend`

### Source excerpt
```
{{c|{{larger|LACQUER}}}}

<table {{Ts|ma}}>
<tr valign="bottom">
<td>[[Image:EB1911 Japan - Lid of Box.jpg|371px]]</td>
<td>{{gap|2em}}</td>
<td>[[Image:EB1911 Japan - Case for Head of a Skakujo.jpg|362px]]</td>
<td>{{gap|3em}}</td>
<td>[[Image:EB1911 Japan - Owl on a Branch.jpg|403px]]</td>
</tr>
<tr valign="top">
<td align="center" width="371">{{sc|Fig. 18.}}—LID OF BOX. By Korin.</td>
<td></td>
<td align="center" width="362">{{sc|Fig. 19.}}—CASE FOR HEAD OF A SKAKUJO.</td>
<td></td>
<td align="center" width="403">{{sc|Fig. 20.}}—OWL ON A BRANCH. By Ritsuo.</td>
</tr>
<tr><td colspan="5">
<table width="100%">
<tr valign="bottom">
<td align="center">[[Image:EB1911 Japan - Box with Butterflies and Flowers.jpg|474px]]</td>
<td align="center">[[Image:EB1911 Japan - Lacquered Boxes.jpg|587px]]</td>
</tr>
<tr valign="top">
<td align="center">{{sc|Fig. 21.}}—BOX WITH BUTTERFLIES AND FLOWERS IN GOLD (12th century).</td>
<td align="center">{{sc|Fig. 22.}}—LACQUERED BOXES. By Kôami (1598–1651).</td>
</tr>
</table>
</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 5 | 5 |
| captioned       | 5 | 5 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **10** | **10** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Japan - Lid of Box.jpg|LID OF BOX. By Korin}}

{{IMG:EB1911 Japan - Case for Head of a Skakujo.jpg|CASE FOR HEAD OF A SKAKUJO}}

{{IMG:EB1911 Japan - Owl on a Branch.jpg|OWL ON A BRANCH. By Ritsuo}}

{{IMG:EB1911 Japan - Box with Butterflies and Flowers.jpg|BOX WITH BUTTERFLIES AND FLOWERS IN GOLD (12th century)}}

{{IMG:EB1911 Japan - Lacquered Boxes.jpg|LACQUERED BOXES. By Kôami (1598–1651)}}
```

### Current body
```
{{IMG:EB1911 Japan - Lid of Box.jpg|LID OF BOX. By Korin}}

{{IMG:EB1911 Japan - Case for Head of a Skakujo.jpg|CASE FOR HEAD OF A SKAKUJO}}

{{IMG:EB1911 Japan - Owl on a Branch.jpg|OWL ON A BRANCH. By Ritsuo}}

{{IMG:EB1911 Japan - Box with Butterflies and Flowers.jpg|BOX WITH BUTTERFLIES AND FLOWERS IN GOLD (12th century)}}

{{IMG:EB1911 Japan - Lacquered Boxes.jpg|LACQUERED BOXES. By Kôami (1598–1651)}}
```

---

## JAPAN, PLATE VIII — vol 15

**Article ID:** 4204367  
**Signature:** `html_table depth=0 wt=0 ht=multi toplegend`

### Source excerpt
```
{{c|{{larger|POTTERY AND PORCELAIN}}}}

<table align="center">
<tr valign="top">
<td align="center">[[Image:EB1911 Japan - Tea Bowl.jpg|305px]]<br/>{{sc|Fig. 23.}}—TEA BOWL. By Kenzan.</td>
<td>{{gap|1.5em}}</td>
<td align="center">[[Image:EB1911 Japan - Tea Jar.jpg|319px]]<br/>{{sc|Fig. 24.}}—TEA JAR. By Ninsei.</td>
<td>{{gap|1.5em}}</td>
<td align="center">[[Image:EB1911 Japan - Figure.jpg|186px]]<br/>{{sc|Fig. 25.}}—FIGURE. By Kakiemon.<br/>Arita porcelain.</td>
<td>{{gap|1.5em}}</td>
<td align="center">[[Image:EB1911 Japan - Lion.jpg|318px]]<br/>{{sc|Fig. 26.}}—LION. By Chojiro Raku.</td>
</tr>
</table>

<table align="center">
<tr valign="bottom">
<td align="center">[[Image:EB1911 Japan - Censer.jpg|314px]]</td>
<td>{{gap|1.5em}}</td>
<td align="center">[[Image:EB1911 Japan - Tea Jar(2).jpg|257px]]</td>
<td>{{gap|1.5em}}</td>
<td align="center">[[Image:EB1911 Japan - Bizen Ware.jpg|262px]]</td>
<td>{{gap|1.5em}}</td>
<td align="center">[[Image:EB1911 Japan - Censer(2).jpg|284px]]</td>
</tr>
<tr valign="top">
<tr>
<td align="center">{{sc|Fig. 27.}}—CENSER, WITH KOCHI GLAZE.<br/>By Eisen.</td>
<td></td>
<td class="caption">{{sc|Fig. 28.}}—TEA JAR. By Ninsei.</td>
<td></td>
<td class="caption">{{sc|Fig. 29.}}—BIZEN WARE. Samantabhadra.</td>
<td></td>
<td class="caption">{{sc|Fig. 30.}}—CENSER. By Kenzan.</td>
</tr>
</table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 8 | 8 |
| captioned       | 8 | 8 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **17** | **17** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Japan - Tea Bowl.jpg|TEA BOWL. By Kenzan}}

{{IMG:EB1911 Japan - Tea Jar.jpg|TEA JAR. By Ninsei}}

{{IMG:EB1911 Japan - Figure.jpg|FIGURE. By Kakiemon. Arita porcelain}}

{{IMG:EB1911 Japan - Lion.jpg|LION. By Chojiro Raku}}

{{IMG:EB1911 Japan - Censer.jpg|CENSER, WITH KOCHI GLAZE. By Eisen}}

{{IMG:EB1911 Japan - Tea Jar(2).jpg|TEA JAR. By Ninsei}}

{{IMG:EB1911 Japan - Bizen Ware.jpg|BIZEN WARE. Samantabhadra}}

{{IMG:EB1911 Japan - Censer(2).jpg|CENSER. By Kenzan}}

{{LEGEND:POTTERY AND PORCELAIN}LEGEND}
```

### Current body
```
{{IMG:EB1911 Japan - Tea Bowl.jpg|TEA BOWL. By Kenzan}}

{{IMG:EB1911 Japan - Tea Jar.jpg|TEA JAR. By Ninsei}}

{{IMG:EB1911 Japan - Figure.jpg|FIGURE. By Kakiemon. Arita porcelain}}

{{IMG:EB1911 Japan - Lion.jpg|LION. By Chojiro Raku}}

{{IMG:EB1911 Japan - Censer.jpg|CENSER, WITH KOCHI GLAZE. By Eisen}}

{{IMG:EB1911 Japan - Tea Jar(2).jpg|TEA JAR. By Ninsei}}

{{IMG:EB1911 Japan - Bizen Ware.jpg|BIZEN WARE. Samantabhadra}}

{{IMG:EB1911 Japan - Censer(2).jpg|CENSER. By Kenzan}}

{{LEGEND:POTTERY AND PORCELAIN}LEGEND}
```

---

## JEWELRY, PLATE I — vol 15

**Article ID:** 4204501  
**Signature:** `wikitable depth=2 wt=multi ht=0 has_colspan`

### Source excerpt
```
{|align="center" cellspacing="10"<includeonly>
|&nbsp;
|-
|colspan="2" align="center"|{{sc|Plate I.}}
|-
</includeonly>
|colspan="2"|
{|border="1"
|[[Image:EB1911 Jewelry - Egypt XIIth Dynasty - two crowns and plume.jpg|600px]]
|}
|-
|
{|border="1"
|[[Image:EB1911 Jewelry - Egypt XIIth Dynasty pectoral (2).jpg|x200px]]
|}
|align="right"|
{|border="1"
|[[Image:EB1911 Jewelry - Egypt XIIth Dynasty pectoral (3).jpg|x200px]]
|}
|-
|colspan="2" align="center"|EARLY EGYPTIAN.
|-
|valign="bottom"|
{|border="1"
|[[Image:EB1911 Jewelry - Mycenaean from Enkomi.jpg|x375px]]
|}
|align="right"|
{|border="1"
|[[Image:EB1911 Jewelry - Late Mycenaean from the Greek islands.jpg|x380px]]
|}
|-
|align="center"|({{sc|From Enkomi.}})
|align="center"|({{sc|From the Greek Islands.}})
|-
|colspan="2" align="center"|LATE MYCENAEAN.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 5 | 5 |
| captioned       | 2 | 2 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **12** | **12** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **2** | **2** |
| header text     | 'Plate I.' | 'Plate I.' |
| footer text     | 'LATE MYCENAEAN' | 'LATE MYCENAEAN' |

**Verdict:** ✅ identical

### Baseline body
```
Plate I.

{{IMG:EB1911 Jewelry - Egypt XIIth Dynasty - two crowns and plume.jpg|(From Enkomi. )}}

{{IMG:EB1911 Jewelry - Egypt XIIth Dynasty pectoral (2).jpg|(From the Greek Islands. )}}

{{IMG:EB1911 Jewelry - Egypt XIIth Dynasty pectoral (3).jpg}}

{{IMG:EB1911 Jewelry - Mycenaean from Enkomi.jpg}}

{{IMG:EB1911 Jewelry - Late Mycenaean from the Greek islands.jpg}}

{{LEGEND:EARLY EGYPTIAN}LEGEND}

LATE MYCENAEAN
```

### Current body
```
Plate I.

{{IMG:EB1911 Jewelry - Egypt XIIth Dynasty - two crowns and plume.jpg|(From Enkomi. )}}

{{IMG:EB1911 Jewelry - Egypt XIIth Dynasty pectoral (2).jpg|(From the Greek Islands. )}}

{{IMG:EB1911 Jewelry - Egypt XIIth Dynasty pectoral (3).jpg}}

{{IMG:EB1911 Jewelry - Mycenaean from Enkomi.jpg}}

{{IMG:EB1911 Jewelry - Late Mycenaean from the Greek islands.jpg}}

{{LEGEND:EARLY EGYPTIAN}LEGEND}

LATE MYCENAEAN
```

---

## JEWELRY, PLATE II — vol 15

**Article ID:** 4204502  
**Signature:** `wikitable depth=2 wt=multi ht=0 has_colspan`

### Source excerpt
```
{|align="center" cellspacing="10"<includeonly>
|&nbsp;
|-
|colspan="2" align="center"|{{sc|Plate II.}}
|-
</includeonly>
|colspan="2"|
{|border="1"
|[[Image:EB1911 Jewelry - Greek.jpg|600px]]
|}
|-
|colspan="2" align="center"|GREEK
|-
|
{|border="1"
|[[Image:EB1911 Jewelry - Etruscan.jpg|x375px]]
|}
|align="right"|
{|border="1"
|[[Image:EB1911 Jewelry - Roman.jpg|x375px]]
|}
|-
|align="center"|ETRUSCAN.
|align="center"|ROMAN.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 2 | 2 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'Plate II.' | 'Plate II.' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
Plate II.

{{IMG:EB1911 Jewelry - Greek.jpg|ETRUSCAN}}

{{IMG:EB1911 Jewelry - Etruscan.jpg|ROMAN}}

{{IMG:EB1911 Jewelry - Roman.jpg}}

{{LEGEND:GREEK}LEGEND}
```

### Current body
```
Plate II.

{{IMG:EB1911 Jewelry - Greek.jpg|ETRUSCAN}}

{{IMG:EB1911 Jewelry - Etruscan.jpg|ROMAN}}

{{IMG:EB1911 Jewelry - Roman.jpg}}

{{LEGEND:GREEK}LEGEND}
```

---

## KNIGHTHOOD AND CHIVALRY, PLATE I — vol 15

**Article ID:** 4205500  
**Signature:** `html_table depth=0 wt=0 ht=1 has_colspan`

### Source excerpt
```
<table align=center>
<tr><td {{Ts|pl.5|pr.5|vtp|ac}} colspan="2">INSIGNIA OF SOME OF THE PRINCIPAL ORDERS OF KNIGHTHOOD,<br/>DRAWN BY GRACIOUS PERMISSION FROM THOSE IN THE POSSESSION<br/>OF HIS LATE MAJESTY KING EDWARD VII AND ARRANGED<br/>IN ACCORDANCE WITH HIS MAJESTY’S WISHES AND COMMAND.</td></tr>
<tr><td {{Ts|ac|mc|ma|pt1}} colspan="2">[[File:EB1911 - Knighthood - Plate I. - Order of the Garter.jpg]]</td></tr>
<tr><td {{Ts|sm92|ac|pl1|pr1}} colspan="2">THE ORDER OF THE GARTER.<br />
(i.) {{sc|The Garter}}; (ii) {{sc|The Collar and George}}; (iii.) {{sc|The Lesser George and Ribbon}}; (iv.) {{sc|Star}}.</td></tr>
<tr><td {{Ts|pl.5|pr.5|vtp|al|sm92}}>''Drawn by William Gibb.''</td>
<td {{Ts|pl.5|pr.5|vtp|ar|sm92}}>''Niagara Litho. Co., Buffalo, N. Y.''</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **5** | **5** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'INSIGNIA OF SOME OF THE PRINCIPAL ORDERS OF KNIGHTHOOD, DRAWN BY GRACIOUS PERMISSION FROM THOSE IN THE POSSESSION OF HIS' | 'INSIGNIA OF SOME OF THE PRINCIPAL ORDERS OF KNIGHTHOOD, DRAWN BY GRACIOUS PERMISSION FROM THOSE IN THE POSSESSION OF HIS' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
INSIGNIA OF SOME OF THE PRINCIPAL ORDERS OF KNIGHTHOOD, DRAWN BY GRACIOUS PERMISSION FROM THOSE IN THE POSSESSION OF HIS LATE MAJESTY KING EDWARD VII AND ARRANGED IN ACCORDANCE WITH HIS MAJESTY’S WISHES AND COMMAND

{{IMG:EB1911 - Knighthood - Plate I. - Order of the Garter.jpg|Drawn by William Gibb}}

{{LEGEND:Niagara Litho. Co., Buffalo, N. Y}LEGEND}
```

### Current body
```
INSIGNIA OF SOME OF THE PRINCIPAL ORDERS OF KNIGHTHOOD, DRAWN BY GRACIOUS PERMISSION FROM THOSE IN THE POSSESSION OF HIS LATE MAJESTY KING EDWARD VII AND ARRANGED IN ACCORDANCE WITH HIS MAJESTY’S WISHES AND COMMAND

{{IMG:EB1911 - Knighthood - Plate I. - Order of the Garter.jpg|Drawn by William Gibb}}

{{LEGEND:Niagara Litho. Co., Buffalo, N. Y}LEGEND}
```

---

## KNIGHTHOOD AND CHIVALRY, PLATE II — vol 15

**Article ID:** 4205501  
**Signature:** `html_table depth=0 wt=0 ht=1 has_colspan`

### Source excerpt
```
<table align=center>
<tr align=center><td {{Ts|pl.5|pr.5|vtp}} colspan="2">INSIGNIA OF SOME OF THE PRINCIPAL ORDERS OF KNIGHTHOOD,<br/>DRAWN BY GRACIOUS PERMISSION FROM THOSE IN THE POSSESSION<br/>OF HIS LATE MAJESTY KING EDWARD VII AND ARRANGED<br/>IN ACCORDANCE WITH HIS MAJESTY’S WISHES AND COMMAND.</td></tr>
<tr><td {{Ts|ac|mc|ma|pt1}} colspan="2">[[File:EB1911 - Knighthood - Plate II. - Orders of the Bath; Thistle; St. Patrick; St. Michael and St. George.jpg]]</td></tr>
<tr><td {{Ts|sm92|lh13|ac|pl1|pr1}} colspan="2">THE BATH. (i) {{sc|Star}}; (ii.) {{sc|Grand Cross}} (Mil.); (iii) {{sc|Star}}; (iv.) {{sc|Grand Cross}} (Civ.); THE THISTLE. (v.) {{sc|Star}}; (vi.) {{sc|Badge}}. THE ST. PATRICK.<br/>(vii.) {{sc|Badge}}; (viii.) {{sc|Star}}. THE ST. MICHAEL AND ST. GEORGE. (ix.) {{sc|Star}}; (x.) {{sc|Grand Cross}}.</td></tr>
<tr><td {{Ts|pl.5|pr.5|vtp|al|sm92}}>''Drawn by William Gibb.''</td>
<td {{Ts|pl.5|pr.5|vtp|ar|sm92}}>''Niagara Litho. Co., Buffalo, N. Y.''</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **5** | **5** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'INSIGNIA OF SOME OF THE PRINCIPAL ORDERS OF KNIGHTHOOD, DRAWN BY GRACIOUS PERMISSION FROM THOSE IN THE POSSESSION OF HIS' | 'INSIGNIA OF SOME OF THE PRINCIPAL ORDERS OF KNIGHTHOOD, DRAWN BY GRACIOUS PERMISSION FROM THOSE IN THE POSSESSION OF HIS' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
INSIGNIA OF SOME OF THE PRINCIPAL ORDERS OF KNIGHTHOOD, DRAWN BY GRACIOUS PERMISSION FROM THOSE IN THE POSSESSION OF HIS LATE MAJESTY KING EDWARD VII AND ARRANGED IN ACCORDANCE WITH HIS MAJESTY’S WISHES AND COMMAND

{{IMG:EB1911 - Knighthood - Plate II. - Orders of the Bath; Thistle; St. Patrick; St. Michael and St. George.jpg|Drawn by William Gibb}}

{{LEGEND:Niagara Litho. Co., Buffalo, N. Y}LEGEND}
```

### Current body
```
INSIGNIA OF SOME OF THE PRINCIPAL ORDERS OF KNIGHTHOOD, DRAWN BY GRACIOUS PERMISSION FROM THOSE IN THE POSSESSION OF HIS LATE MAJESTY KING EDWARD VII AND ARRANGED IN ACCORDANCE WITH HIS MAJESTY’S WISHES AND COMMAND

{{IMG:EB1911 - Knighthood - Plate II. - Orders of the Bath; Thistle; St. Patrick; St. Michael and St. George.jpg|Drawn by William Gibb}}

{{LEGEND:Niagara Litho. Co., Buffalo, N. Y}LEGEND}
```

---

## KNIGHTHOOD AND CHIVALRY, PLATE III — vol 15

**Article ID:** 4205502  
**Signature:** `html_table depth=0 wt=0 ht=1 has_colspan`

### Source excerpt
```
<table align=center>
<tr><td {{Ts|pl.5|pr.5|vtp|ac}} colspan="2">INSIGNIA OF SOME OF THE PRINCIPAL ORDERS OF KNIGHTHOOD,<br/>DRAWN BY GRACIOUS PERMISSION FROM THOSE IN THE POSSESSION<br/>OF HIS LATE MAJESTY KING EDWARD VII AND ARRANGED<br/>IN ACCORDANCE WITH HIS MAJESTY’S WISHES AND COMMAND.</td></tr>
<tr><td {{Ts|ac|mc|ma|pt1}} colspan="2">[[File:EB1911 - Knighthood - Plate III. - Royal Victorian Order; Order of the Indian Empire; Star of India.jpg]]</td></tr>
<tr><td {{Ts|sm92|lh13|ac}} colspan="2">ROYAL VICTORIAN ORDER. (i.) {{sc|Grand Cross}}; (ii.) {{sc|Star}}. ORDER OF THE INDIAN EMPIRE. (iii.) {{sc|Badge Of Knight}}<br/>{{sc|Grand Commander}}; (iv.) {{sc|Star}}. THE STAR OF INDIA. (v.) {{sc|Star}}; (vi.) {{sc|Badge of Knight Grand Commander}}.</td></tr>
<tr><td {{Ts|pl1|vtp|al|sm92}}>''Drawn by William Gibb.''</td>
<td {{Ts|pr1|vtp|ar|sm92}}>''Niagara Litho. Co., Buffalo, N. Y.''</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **5** | **5** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'INSIGNIA OF SOME OF THE PRINCIPAL ORDERS OF KNIGHTHOOD, DRAWN BY GRACIOUS PERMISSION FROM THOSE IN THE POSSESSION OF HIS' | 'INSIGNIA OF SOME OF THE PRINCIPAL ORDERS OF KNIGHTHOOD, DRAWN BY GRACIOUS PERMISSION FROM THOSE IN THE POSSESSION OF HIS' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
INSIGNIA OF SOME OF THE PRINCIPAL ORDERS OF KNIGHTHOOD, DRAWN BY GRACIOUS PERMISSION FROM THOSE IN THE POSSESSION OF HIS LATE MAJESTY KING EDWARD VII AND ARRANGED IN ACCORDANCE WITH HIS MAJESTY’S WISHES AND COMMAND

{{IMG:EB1911 - Knighthood - Plate III. - Royal Victorian Order; Order of the Indian Empire; Star of India.jpg|Drawn by William Gibb}}

{{LEGEND:Niagara Litho. Co., Buffalo, N. Y}LEGEND}
```

### Current body
```
INSIGNIA OF SOME OF THE PRINCIPAL ORDERS OF KNIGHTHOOD, DRAWN BY GRACIOUS PERMISSION FROM THOSE IN THE POSSESSION OF HIS LATE MAJESTY KING EDWARD VII AND ARRANGED IN ACCORDANCE WITH HIS MAJESTY’S WISHES AND COMMAND

{{IMG:EB1911 - Knighthood - Plate III. - Royal Victorian Order; Order of the Indian Empire; Star of India.jpg|Drawn by William Gibb}}

{{LEGEND:Niagara Litho. Co., Buffalo, N. Y}LEGEND}
```

---

## KNIGHTHOOD AND CHIVALRY, PLATE IV — vol 15

**Article ID:** 4205503  
**Signature:** `html_table depth=0 wt=0 ht=1 has_colspan`

### Source excerpt
```
<table align=center>
<tr><td {{Ts|pl.5|pr.5|vtp|ac}} colspan="2">INSIGNIA OF SOME OF THE PRINCIPAL ORDERS OF KNIGHTHOOD,<br/>DRAWN BY GRACIOUS PERMISSION FROM THOSE IN THE POSSESSION<br/>OF HIS LATE MAJESTY KING EDWARD VII AND ARRANGED<br/>IN ACCORDANCE WITH HIS MAJESTY’S WISHES AND COMMAND.<br/><br/></td></tr>
<tr align=center><td colspan="2">[[File:EB1911 - Knighthood - Plate IV. - Various European honours.jpg]]</td></tr>
<tr align=center><td {{Ts|sm92|lh13}} colspan="2">(i.) {{sc|The St. Andrew}} (Russia). (ii.) {{sc|The Golden Fleece}} (Spain). (iii.) {{sc|The Black Eagle}} (Prussia). (iv.) {{sc|The Tower and Sword}} (Portugal). <br/>(v.) {{sc|The Elephant}} (Denmark). (vi.) {{sc|The Legion of Honour}} (France-Napoleonic). (vii.) {{sc|The Annunziata}} (Italy).</td></tr>
<tr><td {{Ts|pl1|al|sm92}}>''Drawn by William Gibb.''</td>
<td {{Ts|pr1|ar|sm92}}>''Niagara Litho. Co., Buffalo, N. Y.''</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **5** | **5** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'INSIGNIA OF SOME OF THE PRINCIPAL ORDERS OF KNIGHTHOOD, DRAWN BY GRACIOUS PERMISSION FROM THOSE IN THE POSSESSION OF HIS' | 'INSIGNIA OF SOME OF THE PRINCIPAL ORDERS OF KNIGHTHOOD, DRAWN BY GRACIOUS PERMISSION FROM THOSE IN THE POSSESSION OF HIS' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
INSIGNIA OF SOME OF THE PRINCIPAL ORDERS OF KNIGHTHOOD, DRAWN BY GRACIOUS PERMISSION FROM THOSE IN THE POSSESSION OF HIS LATE MAJESTY KING EDWARD VII AND ARRANGED IN ACCORDANCE WITH HIS MAJESTY’S WISHES AND COMMAND

{{IMG:EB1911 - Knighthood - Plate IV. - Various European honours.jpg|Drawn by William Gibb}}

{{LEGEND:Niagara Litho. Co., Buffalo, N. Y}LEGEND}
```

### Current body
```
INSIGNIA OF SOME OF THE PRINCIPAL ORDERS OF KNIGHTHOOD, DRAWN BY GRACIOUS PERMISSION FROM THOSE IN THE POSSESSION OF HIS LATE MAJESTY KING EDWARD VII AND ARRANGED IN ACCORDANCE WITH HIS MAJESTY’S WISHES AND COMMAND

{{IMG:EB1911 - Knighthood - Plate IV. - Various European honours.jpg|Drawn by William Gibb}}

{{LEGEND:Niagara Litho. Co., Buffalo, N. Y}LEGEND}
```

---

## KNIGHTHOOD AND CHIVALRY, PLATE V — vol 15

**Article ID:** 4205504  
**Signature:** `html_table depth=0 wt=0 ht=1 has_colspan`

### Source excerpt
```
<table align=center>
<tr align=center><td colspan=2>INSIGNIA OF SOME OF THE PRINCIPAL ORDERS OF KNIGHTHOOD,<br/>DRAWN BY GRACIOUS PERMISSION FROM THOSE IN THE POSSESSION<br/>OF HIS LATE MAJESTY KING EDWARD VII AND ARRANGED<br/>IN ACCORDANCE WITH HIS MAJESTY’S WISHES AND COMMAND.<br/><br/></td></tr>
<tr align=center><td colspan=2>[[File:EB1911 - Knighthood - Plate V. - Various European honours.jpg]]</td></tr>
<tr align=center><td {{Ts|sm92|lh13}} colspan="2">(i) {{sc|The Redeemer}} (Greece). (ii) {{sc|The Order of the Knights of St. John
of Jerusalem}} (English Branch, Badge of the Sovereign and<br/>Patron). (iii) {{sc|The St. Hubert}} (Bavaria). (iv) {{sc|The St. Stephen}} (Hungary). (v). {{sc|The St. Olaf}} (Norway). (vi). {{sc|The Seraphim}} (Sweden).</td></tr>
<tr><td {{Ts|pl1|al|sm92}}>''Drawn by William Gibb.''</td>
<td {{Ts|pr1|ar|sm92}}>''Niagara Litho. Co., Buffalo, N. Y.''</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **5** | **5** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'INSIGNIA OF SOME OF THE PRINCIPAL ORDERS OF KNIGHTHOOD, DRAWN BY GRACIOUS PERMISSION FROM THOSE IN THE POSSESSION OF HIS' | 'INSIGNIA OF SOME OF THE PRINCIPAL ORDERS OF KNIGHTHOOD, DRAWN BY GRACIOUS PERMISSION FROM THOSE IN THE POSSESSION OF HIS' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
INSIGNIA OF SOME OF THE PRINCIPAL ORDERS OF KNIGHTHOOD, DRAWN BY GRACIOUS PERMISSION FROM THOSE IN THE POSSESSION OF HIS LATE MAJESTY KING EDWARD VII AND ARRANGED IN ACCORDANCE WITH HIS MAJESTY’S WISHES AND COMMAND

{{IMG:EB1911 - Knighthood - Plate V. - Various European honours.jpg|Drawn by William Gibb}}

{{LEGEND:Niagara Litho. Co., Buffalo, N. Y}LEGEND}
```

### Current body
```
INSIGNIA OF SOME OF THE PRINCIPAL ORDERS OF KNIGHTHOOD, DRAWN BY GRACIOUS PERMISSION FROM THOSE IN THE POSSESSION OF HIS LATE MAJESTY KING EDWARD VII AND ARRANGED IN ACCORDANCE WITH HIS MAJESTY’S WISHES AND COMMAND

{{IMG:EB1911 - Knighthood - Plate V. - Various European honours.jpg|Drawn by William Gibb}}

{{LEGEND:Niagara Litho. Co., Buffalo, N. Y}LEGEND}
```

---

## LACE, PLATE I — vol 16

**Article ID:** 4205826  
**Signature:** `center_template depth=0 wt=0 ht=0 toplegend`

### Source excerpt
```
[[File:1911 Britannica - Lace 1.jpg|center|800px|]]
{{center|{{EB1911 Fine Print|{{sc|Fig.}} 1.—PORTION OF A COVERLET COMPOSED OF SQUARES OF “LACIS” OR DARNED NETTING, DIVIDED BY LINEN CUT-WORK BANDS.<br />{{EB1911 Fine Print|The squares are worked with groups representing the twelve months, and with scenes from the old Spanish dramatic story “Celestina.” Spanish or Portuguese.<br />16th century. (Victoria and Albert Museum.)}}}}}}


[[File:1911 Britannica - Lace 2.jpg|center|800px|]]
{{center|{{EB1911 Fine Print|{{sc|Fig.}} 2.—CORNER OF A BED-COVER OF PILLOW-MADE LACE OF A TAPE-LIKE TEXTURE WITH CHARACTERISTICS IN THE TWISTED AND<br />PLAITED THREADS RELATING THE WORK TO ITALIAN “MERLETTI A PIOMBINI” OR EARLY ENGLISH “BONE LACE.”<br />{{EB1911 Fine Print|Possibly made in Flanders or Italy during the early part of the 17th or at the end of the 16th century. The design includes the Imperial double-headed eagle<br /> of Austria with the ancient crown of the German Empire. (Victoria and Albert Museum.)}}}}}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica - Lace 1.jpg|PORTION OF A COVERLET COMPOSED OF SQUARES OF “LACIS” OR DARNED NETTING, DIVIDED BY LINEN CUT-WORK BANDS. The squares are worked with groups representing the twelve months, and with scenes from the old Spanish dramatic story “Celestina.” Spanish or Portuguese. 16th century. (Victoria and Albert Museum.)}}

{{IMG:1911 Britannica - Lace 2.jpg|CORNER OF A BED-COVER OF PILLOW-MADE LACE OF A TAPE-LIKE TEXTURE WITH CHARACTERISTICS IN THE TWISTED AND PLAITED THREADS RELATING THE WORK TO ITALIAN “MERLETTI A PIOMBINI” OR EARLY ENGLISH “BONE LACE.” Possibly made in Flanders or Italy during the early part of the 17th or at the end of the 16th century. The design includes the Imperial double-headed eagle of Austria with the ancient crown of the German Empire. (Victoria and Albert Museum.)}}
```

### Current body
```
{{IMG:1911 Britannica - Lace 1.jpg|PORTION OF A COVERLET COMPOSED OF SQUARES OF “LACIS” OR DARNED NETTING, DIVIDED BY LINEN CUT-WORK BANDS. The squares are worked with groups representing the twelve months, and with scenes from the old Spanish dramatic story “Celestina.” Spanish or Portuguese. 16th century. (Victoria and Albert Museum.)}}

{{IMG:1911 Britannica - Lace 2.jpg|CORNER OF A BED-COVER OF PILLOW-MADE LACE OF A TAPE-LIKE TEXTURE WITH CHARACTERISTICS IN THE TWISTED AND PLAITED THREADS RELATING THE WORK TO ITALIAN “MERLETTI A PIOMBINI” OR EARLY ENGLISH “BONE LACE.” Possibly made in Flanders or Italy during the early part of the 17th or at the end of the 16th century. The design includes the Imperial double-headed eagle of Austria with the ancient crown of the German Empire. (Victoria and Albert Museum.)}}
```

---

## LACE, PLATE II — vol 16

**Article ID:** 4205827  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{| {{ts|mc|width:850px}}
|-
| {{ts|pr1|vtp|width:50%}} |
[[File:1911 Britannica - Lace 3.jpg|center|400px|]]
{{EB1911 Fine Print|{{sc|Fig.}} 3.—THREE VANDYKE OR DENTATED BORDERS OF ITALIAN LACE OF THE LATE 16th CENTURY.<br />{{EB1911 Fine Print|Style usually called “Reticella” on account of the patterns being based on repeated squares or reticulations. The two first borders are of needlepoint work; the lower border is of such pillow lace as was known in Italy as “merletti a piombini.”}}}}

[[File:1911 Britannica - Lace 7.jpg|center|400px|]]
{{EB1911 Fine Print|{{sc|Fig.}} 7.—BORDER OF FLAT NEEDLEPOINT LACE OF FULLER TEXTURE THAN THAT OF FIG. 3, AND FROM A FREER STYLE OF DESIGN IN WHICH CONVENTIONALIZED FLORAL FORMS HELD TOGETHER BY SMALL BARS OR TYES ARE USED.<br />{{EB1911 Fine Print|Style called “Punto in Aria,” chiefly on account of its independence of squares or reticulations.&emsp;Italian.&emsp;Early 17th century.}}}}

[[File:1911 Britannica - Lace 5.jpg|center|400px|]]
{{EB1911 Fine Print|{{sc|Fig.}} 5.—CORNER OF A NAPKIN OR HANDKERCHIEF BORDERED WITH “RETICELLA” NEEDLEPOINT LACE IN THE DESIGN OF WHICH ACORNS AND CARNATIONS ARE MINGLED WITH GEOMETRIC RADIATIONS.&emsp;{{Fs|92%|Probably of English early 17th century.}}}}

| {{ts|vtp|pl1|width:50%}} |
[[File:1911 Britannica - Lace 4.jpg|center|400px|]]
{{EB1911 Fine Print|{{sc|Fig.}} 4.—CATHERINE DE MEDICI, WEARING A LINEN UPTURNED COLLAR OF CUT WORK AND NEEDLEPOINT LACE.&emsp;Louvre.&emsp;About 1540.}}

[[File:1911 Britan
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 5 | 5 |
| captioned       | 5 | 5 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **10** | **10** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica - Lace 3.jpg|THREE VANDYKE OR DENTATED BORDERS OF ITALIAN LACE OF THE LATE 16th CENTURY. Style usually called “Reticella” on account of the patterns being based on repeated squares or reticulations. The two first borders are of needlepoint work; the lower border is of such pillow lace as was known in Italy as “merletti a piombini.”}}

{{IMG:1911 Britannica - Lace 7.jpg|BORDER OF FLAT NEEDLEPOINT LACE OF FULLER TEXTURE THAN THAT OF FIG. 3, AND FROM A FREER STYLE OF DESIGN IN WHICH CONVENTIONALIZED FLORAL FORMS HELD TOGETHER BY SMALL BARS OR TYES ARE USED. Style called “Punto in Aria,” chiefly on account of its independence of squares or reticulations. Italian. Early 17th century}}

{{IMG:1911 Britannica - Lace 5.jpg|CORNER OF A NAPKIN OR HANDKERCHIEF BORDERED WITH “RETICELLA” NEEDLEPOINT LACE IN THE DESIGN OF WHICH ACORNS AND CARNATIONS ARE MINGLED WITH GEOMETRIC RADIATIONS. Probably of English early 17th century}}

{{IMG:1911 Britannica - Lace 4.jpg|CATHERINE DE MEDICI, WEARING A LINEN UPTURNED COLLAR OF CUT WORK AND NEEDLEPOINT LACE. Louvre. About 1540}}

{{IMG:1911 Britannica - Lace 6.jpg|AMELIE ELISABETH, COMTESSE DE HAINAULT, WEARING A RUFF OF NEEDLEPOINT RETICELLA LACE. By Morcelse. The Hague. About 1600. (Figs. 4 and 6 by permission of Messrs Braun, Clement & Co., Dornach (Alsace), and Paris.)}}
```

### Current body
```
{{IMG:1911 Britannica - Lace 3.jpg|THREE VANDYKE OR DENTATED BORDERS OF ITALIAN LACE OF THE LATE 16th CENTURY. Style usually called “Reticella” on account of the patterns being based on repeated squares or reticulations. The two first borders are of needlepoint work; the lower border is of such pillow lace as was known in Italy as “merletti a piombini.”}}

{{IMG:1911 Britannica - Lace 7.jpg|BORDER OF FLAT NEEDLEPOINT LACE OF FULLER TEXTURE THAN THAT OF FIG. 3, AND FROM A FREER STYLE OF DESIGN IN WHICH CONVENTIONALIZED FLORAL FORMS HELD TOGETHER BY SMALL BARS OR TYES ARE USED. Style called “Punto in Aria,” chiefly on account of its independence of squares or reticulations. Italian. Early 17th century}}

{{IMG:1911 Britannica - Lace 5.jpg|CORNER OF A NAPKIN OR HANDKERCHIEF BORDERED WITH “RETICELLA” NEEDLEPOINT LACE IN THE DESIGN OF WHICH ACORNS AND CARNATIONS ARE MINGLED WITH GEOMETRIC RADIATIONS. Probably of English early 17th century}}

{{IMG:1911 Britannica - Lace 4.jpg|CATHERINE DE MEDICI, WEARING A LINEN UPTURNED COLLAR OF CUT WORK AND NEEDLEPOINT LACE. Louvre. About 1540}}

{{IMG:1911 Britannica - Lace 6.jpg|AMELIE ELISABETH, COMTESSE DE HAINAULT, WEARING A RUFF OF NEEDLEPOINT RETICELLA LACE. By Morcelse. The Hague. About 1600. (Figs. 4 and 6 by permission of Messrs Braun, Clement & Co., Dornach (Alsace), and Paris.)}}
```

---

## LACE, PLATE III — vol 16

**Article ID:** 4205828  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{| {{ts|mc|width:850px}}
|-
| {{ts|pr1|vtp|w50|ac}} |
[[File:1911 Britannica - Lace 8.jpg|center|400px|]]
{{EB1911 Fine Print|{{sc|Fig.}} 8.—MARY, COUNTESS OF PEMBROKE, WEARING<br />A COIF AND CUFFS OF RETICELLA LACE.<br />{{EB1911 Fine Print|National Portrait Gallery. Dated 1614.}}}}
{{lh|75%|
}}
[[File:1911 Britannica - Lace 11.jpg|center|400px|]]
{{EB1911 Fine Print|{{sc|Fig.}} 11.—JAMES II. WEARING A JABOT AND CUFFS<br />OF RAISED NEEDLEPOINT LACE.<br />{{EB1911 Fine Print|By {{sc|Riley}}. National Portrait Gallery. About 1685<br />(''Figs. 8 and 11'', ''photo by Emery Walker.'')}}}}
| {{ts|pl1|vtp|w50|ac}} |
[[File:1911 Britannica - Lace 9.jpg|center|400px|]]
{{EB1911 Fine Print|{{sc|Fig.}} 9.—HENRI II., DUC DE MONTMORENCY, WEARING A<br />FALLING LACE COLLAR. By {{sc|Le Nain}}. Louvre. About 1628.<br />{{EB1911 Fine Print|(''By permission of Messrs Braun, Clement & Co''.,<br />''Dornach'' (''Alsace''), ''and Paris.'')}}}}

[[File:1911 Britannica - Lace 10.jpg|center|400px|]]
{{EB1911 Fine Print|{{sc|Fig.}} 10.—SCALLOPPED COLLAR OF TAPE-LIKE<br /> PILLOW-MADE LACE.<br />{{EB1911 Fine Print|Possibly of English early 17th-century work. Its texture is<br />&emsp; typical of a development in pillow-lace-making later than that<br />of the lower edge of “merletti a piombini” in Pl. II. fig. 3. &emsp;}}}}

[[File:1911 Britannica - Lace 12.jpg|center|400px|]]
{{EB1911 Fine Print|{{sc|Fig.}} 12.—JABOT OF NEEDLEPOINT LACE WORKED<br />PARTLY IN RELIEF, AND USUALLY KNOWN AS<br />“GRO
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 5 | 5 |
| captioned       | 5 | 5 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **10** | **10** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica - Lace 8.jpg|MARY, COUNTESS OF PEMBROKE, WEARING A COIF AND CUFFS OF RETICELLA LACE. National Portrait Gallery. Dated 1614}}

{{IMG:1911 Britannica - Lace 11.jpg|JAMES II. WEARING A JABOT AND CUFFS OF RAISED NEEDLEPOINT LACE. By Riley . National Portrait Gallery. About 1685 (Figs. 8 and 11, photo by Emery Walker.)}}

{{IMG:1911 Britannica - Lace 9.jpg|HENRI II., DUC DE MONTMORENCY, WEARING A FALLING LACE COLLAR. By Le Nain . Louvre. About 1628. (By permission of Messrs Braun, Clement & Co., Dornach (Alsace), and Paris.)}}

{{IMG:1911 Britannica - Lace 10.jpg|SCALLOPPED COLLAR OF TAPE-LIKE PILLOW-MADE LACE. Possibly of English early 17th-century work. Its texture is typical of a development in pillow-lace-making later than that of the lower edge of “merletti a piombini” in Pl. II. fig. 3}}

{{IMG:1911 Britannica - Lace 12.jpg|JABOT OF NEEDLEPOINT LACE WORKED PARTLY IN RELIEF, AND USUALLY KNOWN AS “GROS POINT DE VENISE.” Middle of 17th century. Conventional scrolling stems with off- shooting pseudo-blossoms and leafs are specially characteristic}}
```

### Current body
```
{{IMG:1911 Britannica - Lace 8.jpg|MARY, COUNTESS OF PEMBROKE, WEARING A COIF AND CUFFS OF RETICELLA LACE. National Portrait Gallery. Dated 1614}}

{{IMG:1911 Britannica - Lace 11.jpg|JAMES II. WEARING A JABOT AND CUFFS OF RAISED NEEDLEPOINT LACE. By Riley . National Portrait Gallery. About 1685 (Figs. 8 and 11, photo by Emery Walker.)}}

{{IMG:1911 Britannica - Lace 9.jpg|HENRI II., DUC DE MONTMORENCY, WEARING A FALLING LACE COLLAR. By Le Nain . Louvre. About 1628. (By permission of Messrs Braun, Clement & Co., Dornach (Alsace), and Paris.)}}

{{IMG:1911 Britannica - Lace 10.jpg|SCALLOPPED COLLAR OF TAPE-LIKE PILLOW-MADE LACE. Possibly of English early 17th-century work. Its texture is typical of a development in pillow-lace-making later than that of the lower edge of “merletti a piombini” in Pl. II. fig. 3}}

{{IMG:1911 Britannica - Lace 12.jpg|JABOT OF NEEDLEPOINT LACE WORKED PARTLY IN RELIEF, AND USUALLY KNOWN AS “GROS POINT DE VENISE.” Middle of 17th century. Conventional scrolling stems with off- shooting pseudo-blossoms and leafs are specially characteristic}}
```

---

## LACE, PLATE IV — vol 16

**Article ID:** 4205829  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{| {{ts|mc|width:850px}}
|-
| {{ts|pr1|vtp|width:50%}} |
[[File:1911 Britannica - Lace 13.jpg|center|400px|]]
{{center|{{EB1911 Fine Print|{{sc|Fig.}} 13.—MME VERBIEST, WEARING PILLOW-MADE<br />LACE À RÉSEAU.<br />{{EB1911 Fine Print|From the family group by {{sc|Gonzales Coquer}}. Buckingham Palace.<br />About 1664.<br />(''By permission of Messrs Braun, Clement & Co.,<br />Dornach'' (''Alsace''), ''and Paris.'')}}}}}}
 
[[File:1911 Britannica - Lace 14.jpg|center|400px|]]
{{center|{{EB1911 Fine Print|{{sc|Fig.}} 14.—PIECE OF PILLOW-MADE LACE USUALLY KNOWN AS “POINT DE FLANDRES À BRIDES.”<br />{{EB1911 Fine Print|Of the middle of the 17th century, the designs for which were<br />often adaptations from those made for such needlepoint lace<br />as that of the Jabot in fig. 12.}}}}}}
| {{ts|pl1|vtp|width:50%}} |
[[File:1911 Britannica - Lace 15.jpg|center|400px|]]
{{center|{{EB1911 Fine Print|{{sc|Fig.}} 15.—PRINCESS MARIA TERESA STUART, WEARING<br />A FLOUNCE OR TABLIER OF LACE SIMILAR TO<br />THAT IN FIG. 17.&emsp;{{Fs|92%|Dated 1695.}}<br />{{EB1911 Fine Print|From a group by {{sc|Largilliere}}. National Portrait Gallery.<br />(''Photo by Emery Walker''.)}}}}}}

[[File:1911 Britannica - Lace 16.jpg|center|400px|]]
{{center|{{EB1911 Fine Print|{{sc|Fig.}} 16.—FLOUNCE OF PILLOW-MADE LACE ''À RÉSEAU''.<br />{{EB1911 Fine Print|Flemish, of the middle of the 17th century. This lace is<br />usually thought to be the earliest type of “Point d’Angleterre”<br />in contradistinction t
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 5 | 5 |
| captioned       | 5 | 5 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **10** | **10** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica - Lace 13.jpg|MME VERBIEST, WEARING PILLOW-MADE LACE À RÉSEAU. From the family group by Gonzales Coquer . Buckingham Palace. About 1664. (By permission of Messrs Braun, Clement & Co., Dornach (Alsace), and Paris.)}}

{{IMG:1911 Britannica - Lace 14.jpg|PIECE OF PILLOW-MADE LACE USUALLY KNOWN AS “POINT DE FLANDRES À BRIDES.” Of the middle of the 17th century, the designs for which were often adaptations from those made for such needlepoint lace as that of the Jabot in fig. 12}}

{{IMG:1911 Britannica - Lace 15.jpg|PRINCESS MARIA TERESA STUART, WEARING A FLOUNCE OR TABLIER OF LACE SIMILAR TO THAT IN FIG. 17. Dated 1695. From a group by Largilliere . National Portrait Gallery. (Photo by Emery Walker.)}}

{{IMG:1911 Britannica - Lace 16.jpg|FLOUNCE OF PILLOW-MADE LACE À RÉSEAU. Flemish, of the middle of the 17th century. This lace is usually thought to be the earliest type of “Point d’Angleterre” in contradistinction to the “Point de Flandres” (fig. 14)}}

{{IMG:1911 Britannica - Lace 17.jpg|VERY DELICATE NEEDLEPOINT LACE WITH CLUSTERS OF SMALL RELIEF WORK. Venetian, middle of the 17th century, and often called “rose- point lace,” and sometimes “Point de Neige.”}}
```

### Current body
```
{{IMG:1911 Britannica - Lace 13.jpg|MME VERBIEST, WEARING PILLOW-MADE LACE À RÉSEAU. From the family group by Gonzales Coquer . Buckingham Palace. About 1664. (By permission of Messrs Braun, Clement & Co., Dornach (Alsace), and Paris.)}}

{{IMG:1911 Britannica - Lace 14.jpg|PIECE OF PILLOW-MADE LACE USUALLY KNOWN AS “POINT DE FLANDRES À BRIDES.” Of the middle of the 17th century, the designs for which were often adaptations from those made for such needlepoint lace as that of the Jabot in fig. 12}}

{{IMG:1911 Britannica - Lace 15.jpg|PRINCESS MARIA TERESA STUART, WEARING A FLOUNCE OR TABLIER OF LACE SIMILAR TO THAT IN FIG. 17. Dated 1695. From a group by Largilliere . National Portrait Gallery. (Photo by Emery Walker.)}}

{{IMG:1911 Britannica - Lace 16.jpg|FLOUNCE OF PILLOW-MADE LACE À RÉSEAU. Flemish, of the middle of the 17th century. This lace is usually thought to be the earliest type of “Point d’Angleterre” in contradistinction to the “Point de Flandres” (fig. 14)}}

{{IMG:1911 Britannica - Lace 17.jpg|VERY DELICATE NEEDLEPOINT LACE WITH CLUSTERS OF SMALL RELIEF WORK. Venetian, middle of the 17th century, and often called “rose- point lace,” and sometimes “Point de Neige.”}}
```

---

## LACE, PLATE V — vol 16

**Article ID:** 4205830  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{| {{ts|mc|width:850px}}
|-
| {{ts|pr1|vtp|width:50%}} |
[[File:1911 Britannica - Lace 18.jpg|center|400px|]]
{{EB1911 Fine Print|&emsp;{{sc|Fig.}} 18.—CHARLES GASPARD GUILLAUME DE VINTIMILLE,<br />&emsp;WEARING LACE SIMILAR IN STYLE OF DESIGN SHOWN IN<br />&emsp;FIG. 19. About 1730.}}

[[File:1911 Britannica - Lace 19.jpg|center|400px|]]
{{EB1911 Fine Print|{{sc|Fig.}} 19.—PORTION OF FLOUNCE, NEEDLEPOINT LACE COPIED AT THE BURANO LACE SCHOOL FROM THE ORIGINAL OF THE SO-CALLED “POINT DE VENISE À BRIDES PICOTÉES.”<br />17th century. Formerly belonging to Pope Clement XIII., but now the property of the queen of Italy. The design and work, however, are indistinguishable from those of important flounces of “Point de France.” The pattern consists of repetitions of two vertically-arranged groups of fantastic pine-apples and vases with flowers, intermixed with bold rococo bands and large leaf devices. The hexagonal meshes of the ground, although similar to the Venetian “brides picotées,” are much akin to the button-hole stitched ground of “Point d’Argentan.” (Victoria and Albert Museum.)}}
| {{ts|pl1|vtp|width:50%}} |
[[File:1911 Britannica - Lace 20.jpg|center|400px|]]
{{c|{{smaller|A{{gap|7em}}{{sc|Fig.}} 20.{{gap|7em}}B}}}}

{{EB1911 Fine Print|{{sc|a.}}—A LAPPET OF “POINT DE VENISE À RÉSEAU.”  The conventional character of the pseudo-leaf and floral forms contrasts with that of the realistic designs of contemporary French laces. Italian. Early 18th century.}}

{{EB1911 Fine Prin
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica - Lace 18.jpg|CHARLES GASPARD GUILLAUME DE VINTIMILLE, WEARING LACE SIMILAR IN STYLE OF DESIGN SHOWN IN FIG. 19. About 1730}}

{{IMG:1911 Britannica - Lace 19.jpg|PORTION OF FLOUNCE, NEEDLEPOINT LACE COPIED AT THE BURANO LACE SCHOOL FROM THE ORIGINAL OF THE SO-CALLED “POINT DE VENISE À BRIDES PICOTÉES.” 17th century. Formerly belonging to Pope Clement XIII., but now the property of the queen of Italy. The design and work, however, are indistinguishable from those of important flounces of “Point de France.” The pattern consists of repetitions of two vertically-arranged groups of fantastic pine-apples and vases with flowers, intermixed with bold rococo bands and large leaf devices. The hexagonal meshes of the ground, although similar to the Venetian “brides picotées,” are much akin to the button-hole stitched ground of “Point d’Argentan.” (Victoria and Albert Museum.)}}

{{IMG:1911 Britannica - Lace 20.jpg|A Fig. 20. B}}

{{IMG:1911 Britannica - Lace 21.jpg|BORDER OF FRENCH NEEDLEPOINT LACE, WITH GROUND OF “RÉSEAU ROSACÉ.” 18th century}}
```

### Current body
```
{{IMG:1911 Britannica - Lace 18.jpg|CHARLES GASPARD GUILLAUME DE VINTIMILLE, WEARING LACE SIMILAR IN STYLE OF DESIGN SHOWN IN FIG. 19. About 1730}}

{{IMG:1911 Britannica - Lace 19.jpg|PORTION OF FLOUNCE, NEEDLEPOINT LACE COPIED AT THE BURANO LACE SCHOOL FROM THE ORIGINAL OF THE SO-CALLED “POINT DE VENISE À BRIDES PICOTÉES.” 17th century. Formerly belonging to Pope Clement XIII., but now the property of the queen of Italy. The design and work, however, are indistinguishable from those of important flounces of “Point de France.” The pattern consists of repetitions of two vertically-arranged groups of fantastic pine-apples and vases with flowers, intermixed with bold rococo bands and large leaf devices. The hexagonal meshes of the ground, although similar to the Venetian “brides picotées,” are much akin to the button-hole stitched ground of “Point d’Argentan.” (Victoria and Albert Museum.)}}

{{IMG:1911 Britannica - Lace 20.jpg|A Fig. 20. B}}

{{IMG:1911 Britannica - Lace 21.jpg|BORDER OF FRENCH NEEDLEPOINT LACE, WITH GROUND OF “RÉSEAU ROSACÉ.” 18th century}}
```

---

## LACE, PLATE VI — vol 16

**Article ID:** 4205831  
**Signature:** `c_centered depth=0 wt=0 ht=0 toplegend`

### Source excerpt
```
[[File:1911 Britannica - Lace 22.jpg|center|800px|]]
{{c|{{EB1911 Fine Print|{{sc|Fig.}} 22.—JABOT OR CRAVAT OF PILLOW-MADE LACE. Brussels. Late 17th century. (Victoria and Albert Museum.)}}}}


[[File:1911 Britannica - Lace 23.jpg|center|800px|]]
{{c|{{EB1911 Fine Print|{{sc|Fig.}} 23.—JABOT OR CRAVAT OF PILLOW-MADE LACE OF FANTASTIC FLORAL DESIGN, THE GROUND OF WHICH IS<br />COMPOSED OF LITTLE FLOWERS AND LEAVES ARRANGED WITHIN SMALL OPENWORK VERTICAL STRIPS.<br />Brussels. 18th century. (Victoria and Albert Museum.)}}}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:1911 Britannica - Lace 22.jpg|JABOT OR CRAVAT OF PILLOW-MADE LACE. Brussels. Late 17th century. (Victoria and Albert Museum.)}}

{{IMG:1911 Britannica - Lace 23.jpg|JABOT OR CRAVAT OF PILLOW-MADE LACE OF FANTASTIC FLORAL DESIGN, THE GROUND OF WHICH IS COMPOSED OF LITTLE FLOWERS AND LEAVES ARRANGED WITHIN SMALL OPENWORK VERTICAL STRIPS. Brussels. 18th century. (Victoria and Albert Museum.)}}
```

### Current body
```
{{IMG:1911 Britannica - Lace 22.jpg|JABOT OR CRAVAT OF PILLOW-MADE LACE. Brussels. Late 17th century. (Victoria and Albert Museum.)}}

{{IMG:1911 Britannica - Lace 23.jpg|JABOT OR CRAVAT OF PILLOW-MADE LACE OF FANTASTIC FLORAL DESIGN, THE GROUND OF WHICH IS COMPOSED OF LITTLE FLOWERS AND LEAVES ARRANGED WITHIN SMALL OPENWORK VERTICAL STRIPS. Brussels. 18th century. (Victoria and Albert Museum.)}}
```

---

## LIGHTHOUSE, PLATE I — vol 16

**Article ID:** 4206793  
**Signature:** `html_table depth=0 wt=0 ht=1`

### Source excerpt
```
<table style="clear: both;" align=center>
<tr><td>[[File:EB1911 - Lighthouse - Fig. 54.—Fastnet Lighthouse—First order single-flashing biform apparatus.jpg]]</td>
<td>&emsp;[[File:EB1911 - Lighthouse - Fig. 55.—Pachena Point Lighthouse, B.C.—First order double-flashing apparatus.jpg]]</td></tr>
<tr align=center><td {{Ts|sm92|lh13|pl1|pr1}}>{{sc|Fig. 54.}}—FASTNET LIGHTHOUSE—FIRST ORDER<br />SINGLE-FLASHING BIFORM APPARATUS.</td>
<td {{Ts|sm92|lh13|pl2}}>{{sc|Fig. 55.}}—PACHENA POINT LIGHTHOUSE, B.C.—FIRST<br />ORDER DOUBLE-FLASHING APPARATUS.</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Lighthouse - Fig. 54.—Fastnet Lighthouse—First order single-flashing biform apparatus.jpg|FASTNET LIGHTHOUSE—FIRST ORDER SINGLE-FLASHING BIFORM APPARATUS}}

{{IMG:EB1911 - Lighthouse - Fig. 55.—Pachena Point Lighthouse, B.C.—First order double-flashing apparatus.jpg|PACHENA POINT LIGHTHOUSE, B.C.—FIRST ORDER DOUBLE-FLASHING APPARATUS}}
```

### Current body
```
{{IMG:EB1911 - Lighthouse - Fig. 54.—Fastnet Lighthouse—First order single-flashing biform apparatus.jpg|FASTNET LIGHTHOUSE—FIRST ORDER SINGLE-FLASHING BIFORM APPARATUS}}

{{IMG:EB1911 - Lighthouse - Fig. 55.—Pachena Point Lighthouse, B.C.—First order double-flashing apparatus.jpg|PACHENA POINT LIGHTHOUSE, B.C.—FIRST ORDER DOUBLE-FLASHING APPARATUS}}
```

---

## LIGHTHOUSE, PLATE II — vol 16

**Article ID:** 4206794  
**Signature:** `html_table depth=0 wt=0 ht=1`

### Source excerpt
```
<table style="clear: both;" align=center>
<tr><td>[[File:EB1911 - Lighthouse - Fig. 56.—Old Eddystone Lighthouse.jpg]]&ensp;</td>
<td>&ensp;[[File:EB1911 - Lighthouse - Fig. 57.—Eddystone Lighthouse.jpg]]</td></tr>
<tr><td {{Ts|sm92|ac}}>{{sc|Fig. 56.}}—OLD EDDYSTONE LIGHTHOUSE.</td>
<td {{Ts|sm92|ac}}>{{sc|Fig. 57.}}—EDDYSTONE LIGHTHOUSE.</td></tr>

<tr><td><br />[[File:EB1911 - Lighthouse - Fig. 58.—Ile Vierge Lighthouse.jpg]]&ensp;</td>
<td><br />&ensp;[[File:EB1911 - Lighthouse - Fig. 59.—Minot's Ledge Lighthouse.jpg]]</td></tr>
<tr><td {{Ts|sm92|ac}}>{{sc|Fig. 58.}}—ILE VIERGE LIGHTHOUSE.</td>
<td {{Ts|sm92|ac}}>{{sc|Fig. 59.}}—MINOT’S LEDGE LIGHTHOUSE.</td></tr></table>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Lighthouse - Fig. 56.—Old Eddystone Lighthouse.jpg|OLD EDDYSTONE LIGHTHOUSE}}

{{IMG:EB1911 - Lighthouse - Fig. 57.—Eddystone Lighthouse.jpg|EDDYSTONE LIGHTHOUSE}}

{{IMG:EB1911 - Lighthouse - Fig. 58.—Ile Vierge Lighthouse.jpg|ILE VIERGE LIGHTHOUSE}}

{{IMG:EB1911 - Lighthouse - Fig. 59.—Minot's Ledge Lighthouse.jpg|MINOT’S LEDGE LIGHTHOUSE}}
```

### Current body
```
{{IMG:EB1911 - Lighthouse - Fig. 56.—Old Eddystone Lighthouse.jpg|OLD EDDYSTONE LIGHTHOUSE}}

{{IMG:EB1911 - Lighthouse - Fig. 57.—Eddystone Lighthouse.jpg|EDDYSTONE LIGHTHOUSE}}

{{IMG:EB1911 - Lighthouse - Fig. 58.—Ile Vierge Lighthouse.jpg|ILE VIERGE LIGHTHOUSE}}

{{IMG:EB1911 - Lighthouse - Fig. 59.—Minot's Ledge Lighthouse.jpg|MINOT’S LEDGE LIGHTHOUSE}}
```

---

## MICROSCOPE, PLATE I — vol 18

**Article ID:** 4209118  
**Signature:** `wikitable depth=1 wt=1 ht=0 has_colspan`

### Source excerpt
```
{|{{Ts|ma|ac|lh120}}
|colspan=3|[[File:EB1911 - Microscope - Fig. 57.png|570px]]
|-
|colspan=3|{{sc|Fig}}. 57.—LARGE DISSECTING STAND (ZEISS).
|-
|<br><br>
|-
|[[File:EB1911 - Microscope - Fig. 58.png|420px]]||{{gap}}||[[File:EB1911 - Microscope - Fig. 60.png|315px]]
|-
|{{sc|Fig}}. 58.—STEPHENSON’S BINOCULAR MICROSCOPE<br>(SWIFT).|||| {{sc|Fig}}. 60.—THE DEMONSTRATION MICROSCOPE<br>(BAKER).
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **5** | **5** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Microscope - Fig. 57.png|LARGE DISSECTING STAND (ZEISS)}}

{{IMG:EB1911 - Microscope - Fig. 58.png|STEPHENSON’S BINOCULAR MICROSCOPE (SWIFT). Fig . 60.—THE DEMONSTRATION MICROSCOPE (BAKER)}}

{{IMG:EB1911 - Microscope - Fig. 60.png}}
```

### Current body
```
{{IMG:EB1911 - Microscope - Fig. 57.png|LARGE DISSECTING STAND (ZEISS)}}

{{IMG:EB1911 - Microscope - Fig. 58.png|STEPHENSON’S BINOCULAR MICROSCOPE (SWIFT). Fig . 60.—THE DEMONSTRATION MICROSCOPE (BAKER)}}

{{IMG:EB1911 - Microscope - Fig. 60.png}}
```

---

## MICROSCOPE, PLATE II — vol 18

**Article ID:** 4209119  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|{{Ts|ma|ac}}
|[[File:EB1911 - Microscope - Fig. 59.png|550px]]<br>
{{sc|Fig.}} 59.—GREENOUGH’S BINOCULAR MICROSCOPE (ZEISS).
|-
|{{dhr|60%}}
|-
|[[File:EB1911 - Microscope - Fig. 61.png|420px]]<br> 
{{sc|Fig.}} 61.—PETROGRAPHICAL MICROSCOPE (ZEISS).
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Microscope - Fig. 59.png|GREENOUGH’S BINOCULAR MICROSCOPE (ZEISS)}}

{{IMG:EB1911 - Microscope - Fig. 61.png|PETROGRAPHICAL MICROSCOPE (ZEISS)}}
```

### Current body
```
{{IMG:EB1911 - Microscope - Fig. 59.png|GREENOUGH’S BINOCULAR MICROSCOPE (ZEISS)}}

{{IMG:EB1911 - Microscope - Fig. 61.png|PETROGRAPHICAL MICROSCOPE (ZEISS)}}
```

---

## MITRE — vol 18

**Article ID:** 4209354  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|{{Ts|ma|sm92|lh12}}
|rowspan=2 {{Ts|pr2|vtp|width:350px}}|[[File:EB1911-Mitre-Fig. 5.jpg|center|350px]]<br>{{smaller|''From a photograph by Father Joseph Braun. S. J.'', ''by kind permission''.}}<br>
{{sc|Fig}}. 5.—German Mitre, of red velvet embroidered with pearls and silver gilt plaques. 15th century. In the cathedral at 
Halberstadt. 
|width=336px|[[File:EB1911-Mitre-Fig. 6.jpg|center|336px]]<br>{{sc|Fig}}. 6.—Mitre (restored) of William of Wykeham, Bishop of Winchester (d. 1404), preserved at New College, Oxford.<br><br>
|-
|width=330px|[[File:EB1911-Mitre-Fig. 7.jpg|center|330px]]<br>{{sc|Fig}}. 7.—Flemish Mitre, embroidered in gold thread, and the panels in colours, with figures of the Virgin and St. Augustine. The other side is similar, with figures of St. Leonard and St. Mary Magdalene. It is dated 1592, repaired in 1766.
{{center|{{smaller|In the Victoria and Albert Museum.}}}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911-Mitre-Fig. 5.jpg|German Mitre, of red velvet embroidered with pearls and silver gilt plaques. 15th century. In the cathedral at Halberstadt}}

{{IMG:EB1911-Mitre-Fig. 6.jpg|Mitre (restored) of William of Wykeham, Bishop of Winchester (d. 1404), preserved at New College, Oxford}}

{{IMG:EB1911-Mitre-Fig. 7.jpg|Flemish Mitre, embroidered in gold thread, and the panels in colours, with figures of the Virgin and St. Augustine. The other side is similar, with figures of St. Leonard and St. Mary Magdalene. It is dated 1592, repaired in 1766. In the Victoria and Albert Museum}}
```

### Current body
```
{{IMG:EB1911-Mitre-Fig. 5.jpg|German Mitre, of red velvet embroidered with pearls and silver gilt plaques. 15th century. In the cathedral at Halberstadt}}

{{IMG:EB1911-Mitre-Fig. 6.jpg|Mitre (restored) of William of Wykeham, Bishop of Winchester (d. 1404), preserved at New College, Oxford}}

{{IMG:EB1911-Mitre-Fig. 7.jpg|Flemish Mitre, embroidered in gold thread, and the panels in colours, with figures of the Virgin and St. Augustine. The other side is similar, with figures of St. Leonard and St. Mary Magdalene. It is dated 1592, repaired in 1766. In the Victoria and Albert Museum}}
```

---

## MOON, PLATE I — vol 18

**Article ID:** 4209684  
**Signature:** `bare_image depth=0 wt=0 ht=0`

### Source excerpt
```
[[File:EB1911 - Moon - Photo.jpg|800px|Photograph of Full Moon|center]]
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 0 | 0 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **1** | **1** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Moon - Photo.jpg}}
```

### Current body
```
{{IMG:EB1911 - Moon - Photo.jpg}}
```

---

## MOON, PLATE II — vol 18

**Article ID:** 4209685  
**Signature:** `bare_image depth=0 wt=0 ht=0`

### Source excerpt
```
[[File:EB1911 Moon - Plate II.jpg|center|800px]]
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 0 | 0 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **1** | **1** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Moon - Plate II.jpg}}
```

### Current body
```
{{IMG:EB1911 Moon - Plate II.jpg}}
```

---

## NEBULA — vol 19

**Article ID:** 4210436  
**Signature:** `wikitable depth=1 wt=1 ht=0 has_colspan`

### Source excerpt
```
{|{{Ts|ma|ac}}
|{{Ts|ar}} colspan=3|{{sc|Plate}} I.
|-
|[[File:EB1911 - Nebula Plate I - 1 Orion.jpg|492px]]||{{gap}}||[[File:EB1911 - Nebula Plate I - 2 - Andromeda.jpg|500px]]
|-
|(1) GREAT NEBULA IN ORION, 1901, OCTOBER 19.|| ||(2) NEBULA IN ANDROMEDA, 1901, SEPTEMBER 18.
|-{{Ts|ar|sm92|lh12}}
|By permission of Yerkes Observatory.|| ||By permission of Yerkes Observatory.
|}
{{nop}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | 'By permission of Yerkes Observatory' | 'By permission of Yerkes Observatory' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Nebula Plate I - 1 Orion.jpg|(1) GREAT NEBULA IN ORION, 1901, OCTOBER 19}}

{{IMG:EB1911 - Nebula Plate I - 2 - Andromeda.jpg|(2) NEBULA IN ANDROMEDA, 1901, SEPTEMBER 18}}

By permission of Yerkes Observatory
```

### Current body
```
{{IMG:EB1911 - Nebula Plate I - 1 Orion.jpg|(1) GREAT NEBULA IN ORION, 1901, OCTOBER 19}}

{{IMG:EB1911 - Nebula Plate I - 2 - Andromeda.jpg|(2) NEBULA IN ANDROMEDA, 1901, SEPTEMBER 18}}

By permission of Yerkes Observatory
```

---

## NEBULA — vol 19

**Article ID:** 4210437  
**Signature:** `wikitable depth=1 wt=1 ht=0 has_colspan`

### Source excerpt
```
{|{{Ts|ma|ac}}
|{{Ts|ar}} colspan=3|{{sc|Plate}} II.
|-
|[[File:EB1911 - Nebula Plate II - 1 Lyra.jpg|500px]]||{{em|3}}||[[File:EB1911 - Nebula Plate II - 2 Canes Venatici.jpg|464px]]
|-
|(1) ANNULAR NEBULA, ''LYRA'', 1899, JULY 14.|| ||(2) SPIRAL NEBULA, ''CANES VENATICI'', 1899, MAY 10.
|-{{Ts|ar|sm92|lh12}}
|By permission of Lick Observatory.|| ||By permission of Lick Observatory.
|}
{{nop}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | 'By permission of Lick Observatory' | 'By permission of Lick Observatory' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Nebula Plate II - 1 Lyra.jpg|(1) ANNULAR NEBULA, LYRA, 1899, JULY 14}}

{{IMG:EB1911 - Nebula Plate II - 2 Canes Venatici.jpg|(2) SPIRAL NEBULA, CANES VENATICI, 1899, MAY 10}}

By permission of Lick Observatory
```

### Current body
```
{{IMG:EB1911 - Nebula Plate II - 1 Lyra.jpg|(1) ANNULAR NEBULA, LYRA, 1899, JULY 14}}

{{IMG:EB1911 - Nebula Plate II - 2 Canes Venatici.jpg|(2) SPIRAL NEBULA, CANES VENATICI, 1899, MAY 10}}

By permission of Lick Observatory
```

---

## ORDNANCE, PLATE I — vol 20

**Article ID:** 4211514  
**Signature:** `center_template depth=0 wt=0 ht=0 toplegend`

### Source excerpt
```
{{center|[[File:EB1911 - Ordnance - Fig. 15 - Forging Process.jpg|900px]]<br>
{{sc|Fig}}. 15.—FORGING PROCESS.}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'center' | 'center' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
center

{{IMG:EB1911 - Ordnance - Fig. 15 - Forging Process.jpg|FORGING PROCESS}}
```

### Current body
```
center

{{IMG:EB1911 - Ordnance - Fig. 15 - Forging Process.jpg|FORGING PROCESS}}
```

---

## ORDNANCE, PLATE II — vol 20

**Article ID:** 4211515  
**Signature:** `center_template depth=0 wt=0 ht=0 toplegend`

### Source excerpt
```
[[File:EB1911 - Ordnance - Fig. 18 - Shrinking-on Process.jpg|center|400px|SHRINKING-ON PROCESS.]]
{{center|{{sc|Fig}}. 18.—SHRINKING-ON PROCESS.}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **2** | **2** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Ordnance - Fig. 18 - Shrinking-on Process.jpg|SHRINKING-ON PROCESS}}
```

### Current body
```
{{IMG:EB1911 - Ordnance - Fig. 18 - Shrinking-on Process.jpg|SHRINKING-ON PROCESS}}
```

---

## ORDNANCE — vol 20

**Article ID:** 4211516  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|style="margin:auto; text-align:center"
|style=text-align:right|{{sc|Plate}} III.
|-
|[[File:EB1911 - Ordnance Fig 60.jpg|796px]]
|-
|{{sc|Fig}}. 60.—BRITISH 18-PR. QUICK-FIRING GUN.<br><br>
|-
|[[File:EB1911 - Ordnance Fig 61.jpg|800px]]
|-
|{{sc|Fig}}. 61.—BRITISH 18-PR. QUICK-FIRING GUN AND LIMBER.<br><br>
|-
|[[File:EB1911 - Ordnance Fig 62.jpg|800px]]
|-
|{{sc|Fig}}. 62.—FRENCH 75-MM. QUICK-FIRING GUN AND WAGON BODY IN ACTION.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Ordnance Fig 60.jpg|BRITISH 18-PR. QUICK-FIRING GUN}}

{{IMG:EB1911 - Ordnance Fig 61.jpg|BRITISH 18-PR. QUICK-FIRING GUN AND LIMBER}}

{{IMG:EB1911 - Ordnance Fig 62.jpg|FRENCH 75-MM. QUICK-FIRING GUN AND WAGON BODY IN ACTION}}
```

### Current body
```
{{IMG:EB1911 - Ordnance Fig 60.jpg|BRITISH 18-PR. QUICK-FIRING GUN}}

{{IMG:EB1911 - Ordnance Fig 61.jpg|BRITISH 18-PR. QUICK-FIRING GUN AND LIMBER}}

{{IMG:EB1911 - Ordnance Fig 62.jpg|FRENCH 75-MM. QUICK-FIRING GUN AND WAGON BODY IN ACTION}}
```

---

## ORDNANCE — vol 20

**Article ID:** 4211517  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|style="margin:auto; text-align:center"
|style=text-align:right|{{sc|Plate}} IV.
|-
|[[File:EB1911 - Ordnance Fig 64.jpg|796px]]
|-
|{{sc|Fig}}. 64.–DANISH (KRUPP) 7·5-CM. QUICK-FIRING FIELD GUN AND WAGON BODY IN ACTION.<br><br>
|-
|[[File:EB1911 - Ordnance Fig 67.jpg|800px]]
|-
|{{sc|Fig}}. 67.–EHRHARDT 4·7-IN. QUICK-FIRING FIELD HOWITZER (CONTROLLED RECOIL).<br><br>
|-
|[[File:EB1911 - Ordnance Fig 68.jpg|800px]]
|-
|{{sc|Fig}}. 68.–KRUPP 7·5-CM. MOUNTAIN GUN.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Ordnance Fig 64.jpg|DANISH (KRUPP) 7·5-CM. QUICK-FIRING FIELD GUN AND WAGON BODY IN ACTION}}

{{IMG:EB1911 - Ordnance Fig 67.jpg|EHRHARDT 4·7-IN. QUICK-FIRING FIELD HOWITZER (CONTROLLED RECOIL)}}

{{IMG:EB1911 - Ordnance Fig 68.jpg|KRUPP 7·5-CM. MOUNTAIN GUN}}
```

### Current body
```
{{IMG:EB1911 - Ordnance Fig 64.jpg|DANISH (KRUPP) 7·5-CM. QUICK-FIRING FIELD GUN AND WAGON BODY IN ACTION}}

{{IMG:EB1911 - Ordnance Fig 67.jpg|EHRHARDT 4·7-IN. QUICK-FIRING FIELD HOWITZER (CONTROLLED RECOIL)}}

{{IMG:EB1911 - Ordnance Fig 68.jpg|KRUPP 7·5-CM. MOUNTAIN GUN}}
```

---

## ORDNANCE — vol 20

**Article ID:** 4211518  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|{{Ts|ma}}
|style=text-align:right|{{sc|Plate V.}}
|-
|[[File:EB1911 Ordnance - Fig. 69.png|800px]]
|-
|{{Fs|83%|From Lieut.-Col. Ormond M. Lissak’s ''Ordnance and Gunnery''.}}
|-style=text-align:center
|{{sc|Fig}}. 69.—4·7-IN. SIEGE GUN, TRAVELLING POSITION (U.S.A.).
|-
|&nbsp;
|-
|[[File:EB1911 Ordnance - Fig. 70.png|800px]]
|-
|{{Fs|83%|From Lieut.-Col. Ormond M. Lissak’s ''Ordnance and Gunnery''.}}
|-style=text-align:center
|{{sc|Fig}}. 70.—4·7-IN. SIEGE GUN, IN ACTION (U.S.A.).
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 2 | 2 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Ordnance - Fig. 69.png|From Lieut.-Col. Ormond M. Lissak’s Ordnance and Gunnery}}

{{IMG:EB1911 Ordnance - Fig. 70.png|From Lieut.-Col. Ormond M. Lissak’s Ordnance and Gunnery}}

{{LEGEND:Fig . 69.—4·7-IN. SIEGE GUN, TRAVELLING POSITION (U.S.A.)}LEGEND}

{{LEGEND:Fig . 70.—4·7-IN. SIEGE GUN, IN ACTION (U.S.A.)}LEGEND}
```

### Current body
```
{{IMG:EB1911 Ordnance - Fig. 69.png|From Lieut.-Col. Ormond M. Lissak’s Ordnance and Gunnery}}

{{IMG:EB1911 Ordnance - Fig. 70.png|From Lieut.-Col. Ormond M. Lissak’s Ordnance and Gunnery}}

{{LEGEND:Fig . 69.—4·7-IN. SIEGE GUN, TRAVELLING POSITION (U.S.A.)}LEGEND}

{{LEGEND:Fig . 70.—4·7-IN. SIEGE GUN, IN ACTION (U.S.A.)}LEGEND}
```

---

## ORDNANCE — vol 20

**Article ID:** 4211519  
**Signature:** `wikitable depth=1 wt=1 ht=0 has_colspan`

### Source excerpt
```
{|style="margin:auto; text-align:center"
|colspan=2 style=text-align:right|{{sc|Plate}} VI.
|-
|colspan=2|[[File:EB1911 - Ordnance Fig 83.jpg|800px]]
|-
|colspan=2|{{sc|Fig}}. 83.—KRUPP 11·2-IN. HOWITZER AND SHIELD.<br><br>
|-
|[[File:EB1911 - Ordnance Fig 76.jpg|520px]]||[[File:EB1911 - Ordnance Fig 77.jpg|290px]]
|-{{Ts|vtp|lh110}}
|{{sc|Fig}}. 76.—KRUPP 8·26-IN. MORTAR, TRAVELLING.||{{sc|Fig}}. 77.—KRUPP 8·26-IN. MORTAR,<br>FIRING POSITION.
|-
|colspan=2|[[File:EB1911 - Ordnance Fig 88.jpg|800px]]
|-
|colspan=2|{{sc|Fig}}. 88.—KRUPP 3·4-IN. AUTOMATIC GUN.
|-
|colspan=2 style=text-align:right|{{smaller|From photographs by Friedrich Krupp A. G., Essen/Ruhr.}}
|}
{{nop}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Ordnance Fig 83.jpg|KRUPP 11·2-IN. HOWITZER AND SHIELD}}

{{IMG:EB1911 - Ordnance Fig 76.jpg|KRUPP 8·26-IN. MORTAR, TRAVELLING. Fig . 77.—KRUPP 8·26-IN. MORTAR, FIRING POSITION}}

{{IMG:EB1911 - Ordnance Fig 77.jpg|From photographs by Friedrich Krupp A. G., Essen/Ruhr}}

{{IMG:EB1911 - Ordnance Fig 88.jpg|KRUPP 3·4-IN. AUTOMATIC GUN}}
```

### Current body
```
{{IMG:EB1911 - Ordnance Fig 83.jpg|KRUPP 11·2-IN. HOWITZER AND SHIELD}}

{{IMG:EB1911 - Ordnance Fig 76.jpg|KRUPP 8·26-IN. MORTAR, TRAVELLING. Fig . 77.—KRUPP 8·26-IN. MORTAR, FIRING POSITION}}

{{IMG:EB1911 - Ordnance Fig 77.jpg|From photographs by Friedrich Krupp A. G., Essen/Ruhr}}

{{IMG:EB1911 - Ordnance Fig 88.jpg|KRUPP 3·4-IN. AUTOMATIC GUN}}
```

---

## PAINTING — vol 20

**Article ID:** 4211895  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|{{Ts|ma|ac}}
|{{Ts|ar}}|{{sc|Plate I.}}
|-
|[[File:EB1911 - Painting - Figs 1, 2. Heads of Chamois.png|780px]]<br>
{{sc|Figs}}. 1, 2.—HEADS OF CHAMOIS, &c., ENGRAVED ON THE TINES OF AN ANTLER.<br>
({{sc|From the Cave of Gourdan, Haute-Garonne, France.}})
|-
|[[File:EB1911 - Painting - Fig 3. Stags and Salmon.png|760px]]<br>
{{sc|Fig}}. 3.—STAGS AND SALMON. THE ORIGINALS ARE ENGRAVED ROUND AN ANTLER ABOUT AN INCH<br>
IN DIAMETER. ({{sc|From the Grotto of Lortet, Hautes-Pyrénées, France}}.)

PREHISTORIC INCISED DRAWINGS OF ANIMALS.<br>
{{em|10}}{{fs|72%|Reproduced from Édouard Piette’s ''L’art pendant l’age du renne'' (Paris, 1907).&emsp;By permission.}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **9** | **9** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **2** | **2** |
| header text     | 'Plate I.' | 'Plate I.' |
| footer text     | '1072% Reproduced from Édouard Piette’s L’art pendant l’age du renne (Paris, 1907). By permission' | '1072% Reproduced from Édouard Piette’s L’art pendant l’age du renne (Paris, 1907). By permission' |

**Verdict:** ✅ identical

### Baseline body
```
Plate I.

{{IMG:EB1911 - Painting - Figs 1, 2. Heads of Chamois.png|HEADS OF CHAMOIS, &c., ENGRAVED ON THE TINES OF AN ANTLER. (From the Cave of Gourdan, Haute-Garonne, France. )}}

{{IMG:EB1911 - Painting - Fig 3. Stags and Salmon.png|STAGS AND SALMON. THE ORIGINALS ARE ENGRAVED ROUND AN ANTLER ABOUT AN INCH IN DIAMETER. (From the Grotto of Lortet, Hautes-Pyrénées, France .)}}

{{LEGEND:PREHISTORIC INCISED DRAWINGS OF ANIMALS}LEGEND}

1072% Reproduced from Édouard Piette’s L’art pendant l’age du renne (Paris, 1907). By permission
```

### Current body
```
Plate I.

{{IMG:EB1911 - Painting - Figs 1, 2. Heads of Chamois.png|HEADS OF CHAMOIS, &c., ENGRAVED ON THE TINES OF AN ANTLER. (From the Cave of Gourdan, Haute-Garonne, France. )}}

{{IMG:EB1911 - Painting - Fig 3. Stags and Salmon.png|STAGS AND SALMON. THE ORIGINALS ARE ENGRAVED ROUND AN ANTLER ABOUT AN INCH IN DIAMETER. (From the Grotto of Lortet, Hautes-Pyrénées, France .)}}

{{LEGEND:PREHISTORIC INCISED DRAWINGS OF ANIMALS}LEGEND}

1072% Reproduced from Édouard Piette’s L’art pendant l’age du renne (Paris, 1907). By permission
```

---

## PAINTING — vol 20

**Article ID:** 4211896  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|{{Ts|ma|ac}}
|{{Ts|ar}}|{{sc|Plate II.}}
|-
|[[File:EB1911 - Painting - Plate II - Fig. 4.jpg|780px|center]]<br>
{{csc|Fig. 4. Wild Boar in a Galloping and in Standing Position.}}
|-
|[[File:EB1911 - Painting - Plate II - Fig. 5.jpg|782px]]<br>
{{csc|Fig. 5. The Finest Example of a Bison.}}
{{center|''Reproduced by kind permission of the authors and publishers of'' “''La Caverne d’Altamira''.”

REDUCED FACSIMILES OF PAINTINGS OF THE PALAEOLITHIC AGE FROM THE CAVE OF ALTAMIRA IN SPAIN}}
|}
<br>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'Plate II.' | 'Plate II.' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
Plate II.

{{IMG:EB1911 - Painting - Plate II - Fig. 4.jpg|Wild Boar in a Galloping and in Standing Position}}

{{IMG:EB1911 - Painting - Plate II - Fig. 5.jpg|The Finest Example of a Bison. Reproduced by kind permission of the authors and publishers of “La Caverne d’Altamira.” REDUCED FACSIMILES OF PAINTINGS OF THE PALAEOLITHIC AGE FROM THE CAVE OF ALTAMIRA IN SPAIN}}
```

### Current body
```
Plate II.

{{IMG:EB1911 - Painting - Plate II - Fig. 4.jpg|Wild Boar in a Galloping and in Standing Position}}

{{IMG:EB1911 - Painting - Plate II - Fig. 5.jpg|The Finest Example of a Bison. Reproduced by kind permission of the authors and publishers of “La Caverne d’Altamira.” REDUCED FACSIMILES OF PAINTINGS OF THE PALAEOLITHIC AGE FROM THE CAVE OF ALTAMIRA IN SPAIN}}
```

---

## PAINTING — vol 20

**Article ID:** 4211897  
**Signature:** `wikitable depth=1 wt=1 ht=0 has_colspan`

### Source excerpt
```
{|{{ts|ma}}
|colspan=3 style=text-align:right|{{sc|Plate III.}}
|-
|[[File:EB1911 - Painting - Plate III - Fig. 6.jpg|400px]]<br>
  {{sc|Fig}}. 6.—PREHISTORIC DRAWING OF A MAMMOTH.{{dhr|60%}}
[[File:EB1911 - Painting - Plate III - Fig. 10.jpg|400px]]<br>
{{smaller|''Photo'', ''Alinari''.}}<br>
{{sc|Fig}}. 10.— ZEUS AND HERA.&emsp;POMPEIAN WALL PAINTING.
|{{gap}}
|[[File:EB1911 - Painting - Plate III - Fig. 7.jpg|400px]]<br>
{{smaller|''Photo'', ''W. A. Mansell & Co''.}}<br>{{em|4}}{{sc|Fig}}. 7.—EGYPTIAN FOWLING IN THE DELTA.<br>
[[File:EB1911 - Painting - Plate III - Fig. 8.jpg|360px|right]]<br>
{{em|4}}{{smaller|''Photo'', ''Alinari''.}}<br>
{{em|8}}{{sc|Fig}}. 8.— FRANÇOIS VASE. Florence.
|-
|colspan=3|[[File:EB1911 - Painting - Plate III - Fig. 11.jpg|700px|center]]
{{em|6}}{{smaller|''Photo'', ''W. A. Mansell & Co''.}}<br>
{{em|9}}{{sc|Fig}}. 11.— HEROD’S BIRTHDAY FEAST.&emsp;WALL PAINTING IN CATHEDRAL AT BRUNSWICK.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 5 | 5 |
| captioned       | 5 | 5 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **10** | **10** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Painting - Plate III - Fig. 6.jpg|PREHISTORIC DRAWING OF A MAMMOTH}}

{{IMG:EB1911 - Painting - Plate III - Fig. 10.jpg|ZEUS AND HERA. POMPEIAN WALL PAINTING}}

{{IMG:EB1911 - Painting - Plate III - Fig. 7.jpg|EGYPTIAN FOWLING IN THE DELTA}}

{{IMG:EB1911 - Painting - Plate III - Fig. 8.jpg|FRANÇOIS VASE. Florence}}

{{IMG:EB1911 - Painting - Plate III - Fig. 11.jpg|HEROD’S BIRTHDAY FEAST. WALL PAINTING IN CATHEDRAL AT BRUNSWICK}}
```

### Current body
```
{{IMG:EB1911 - Painting - Plate III - Fig. 6.jpg|PREHISTORIC DRAWING OF A MAMMOTH}}

{{IMG:EB1911 - Painting - Plate III - Fig. 10.jpg|ZEUS AND HERA. POMPEIAN WALL PAINTING}}

{{IMG:EB1911 - Painting - Plate III - Fig. 7.jpg|EGYPTIAN FOWLING IN THE DELTA}}

{{IMG:EB1911 - Painting - Plate III - Fig. 8.jpg|FRANÇOIS VASE. Florence}}

{{IMG:EB1911 - Painting - Plate III - Fig. 11.jpg|HEROD’S BIRTHDAY FEAST. WALL PAINTING IN CATHEDRAL AT BRUNSWICK}}
```

---

## PAINTING — vol 20

**Article ID:** 4211898  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|{{ts|ma}}
|{{Ts|ar}}|{{sc|Plate IV.}}
|-
|[[File:EB1911 - Painting - Plate IV - Fig. 12.jpg|730px|center]]
|-
|{{Ts|sm85|lh90}}|{{em|4}}''By permission of Braun'', ''Clément & Co''., ''Dornach'' (''Alsace'') ''and Paris''.
|-
|{{Ts|ac|pb.5}}|{{sc|Fig}}. 12.—THE MARIES AT THE SEPULCHRE, HUBERT VAN EYCK (?). (28 ✕ 35.)
|-
|[[File:EB1911 - Painting - Plate IV - Fig. 13.jpg|800px]]
|-
|{{Ts|sm85|lh90}}| ''Photo'', ''Alinari''.
|-
|{{Ts|ac}}|{{sc|Fig}}. 13.—HEROD’S BIRTHDAY FEAST, GIOTTO.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Painting - Plate IV - Fig. 12.jpg|THE MARIES AT THE SEPULCHRE, HUBERT VAN EYCK (?). (28 ✕ 35.) (By permission of Braun, Clément & Co., Dornach (Alsace) and Paris)}}

{{IMG:EB1911 - Painting - Plate IV - Fig. 13.jpg|HEROD’S BIRTHDAY FEAST, GIOTTO (Photo, Alinari)}}
```

### Current body
```
{{IMG:EB1911 - Painting - Plate IV - Fig. 12.jpg|THE MARIES AT THE SEPULCHRE, HUBERT VAN EYCK (?). (28 ✕ 35.) (By permission of Braun, Clément & Co., Dornach (Alsace) and Paris)}}

{{IMG:EB1911 - Painting - Plate IV - Fig. 13.jpg|HEROD’S BIRTHDAY FEAST, GIOTTO (Photo, Alinari)}}
```

---

## PALAEOBOTANY — vol 20

**Article ID:** 4211915  
**Signature:** `wikitable depth=2 wt=multi ht=0 has_colspan`

### Source excerpt
```
<!-- -->
{|{{Ts|ma}}
|-
|
{|
|[[Image:EB1911 Paleobotany - Calamites - young stem.jpg|300px]]
|-
|width=300px|
{{sc|Fig.}} 1.—''Calamites''. Part of transverse section of a young 
stem, showing pith, vascular bundles with secondary wood, 
and cortex. (× about 40.) ''From a photograph'' (''Scott'', “''Studies''”). 
|}
|rowspan="4"|&emsp;
|rowspan="4"|
{|
|[[Image:EB1911 Paleobotany - Palaeostachya pedunculata - fertile shoot.jpg|150px]]
|-
|width=150px|
{{sc|Fig.}} 4.—''Palaeostachya pedunculata''.
Fertile shoot, bearing
numerous cones and a few 
leaves. ''After Williamson'' (''Scott'', 
“''Studies''”). 
|}
|rowspan="4"|&emsp;
|colspan=3 width=350px|
{|
|{{Ts|ar}}|{{sc|Plate.}}
|-
|[[Image:EB1911 Paleobotany - Lyginodendron oldhamium - stem.jpg|350px]]
|-
|
{{sc|Fig.}} 22.—''Lyginodendron oldhamium''. Transverse section of stem, 
showing the pith containing groups of sclerotic cells, the primary 
xylem-strands, secondary wood and phloem, pericycle and cortex. 
𝑙𝑡<sup>1</sup>-𝑙𝑡<sup>5</sup>, leaf-traces, numbered according to the phyllotaxis, 𝑙𝑡<sup>5</sup>
belonging to the lowest leaf of the five; 𝑝ℎ, a group of primary 
phloem; 𝑝𝑑, periderm, formed from pericycle. (×&nbsp;3.)
|}
|-
|rowspan=3 width=350px|
{|
|[[Image:EB1911 Paleobotany - Sphenophyllum insigne - stem.jpg|350px]]
|-
|width=350px|
{{sc|Fig.}} 5.—''Sphenophyllum insigne''. Transverse section of stem, showing
triangular primary wood, secondary wood, remains of phloem, 
and primary cortex. (×&nbsp;about&nbsp;30.) '
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 6 | 6 |
| captioned       | 6 | 6 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **12** | **12** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Paleobotany - Calamites - young stem.jpg|Calamites. Part of transverse section of a young stem, showing pith, vascular bundles with secondary wood, and cortex. (× about 40.) From a photograph (Scott, “Studies”)}}

{{IMG:EB1911 Paleobotany - Palaeostachya pedunculata - fertile shoot.jpg|Palaeostachya pedunculata. Fertile shoot, bearing numerous cones and a few leaves. After Williamson (Scott, “Studies”)}}

{{IMG:EB1911 Paleobotany - Lyginodendron oldhamium - stem.jpg|Lyginodendron oldhamium. Transverse section of stem, showing the pith containing groups of sclerotic cells, the primary xylem-strands, secondary wood and phloem, pericycle and cortex. 𝑙𝑡1-𝑙𝑡5, leaf-traces, numbered according to the phyllotaxis, 𝑙𝑡5 belonging to the lowest leaf of the five; 𝑝ℎ, a group of primary phloem; 𝑝𝑑, periderm, formed from pericycle. (× 3.)}}

{{IMG:EB1911 Paleobotany - Sphenophyllum insigne - stem.jpg|Sphenophyllum insigne. Transverse section of stem, showing triangular primary wood, secondary wood, remains of phloem, and primary cortex. (× about 30.) From a photograph (Scott, “Studies”)}}

{{IMG:EB1911 Paleobotany - Cordaianthus Penjoni - male catkin.jpg|Cordaianthus Penjoni. A, Male catkin in longitudinal section: 𝑎, axis; 𝑏, bracts; 𝑐, 𝑑, filaments of stamens, hearing the pollen-sacs (𝑒 and 𝑓) at the top; 𝑣, apex of axis. (× 62.) B, Stamens more highly magnified: 𝑔, vascular bundle of filament; 𝑒, pollen-sac after dehiscence. (× 23.) After Renault (Scott, “Studies”)}}

{{IMG:EB1911 Paleobotany - Cordaianthus Penjoni - stamens.jpg|Plate}}
```

### Current body
```
{{IMG:EB1911 Paleobotany - Calamites - young stem.jpg|Calamites. Part of transverse section of a young stem, showing pith, vascular bundles with secondary wood, and cortex. (× about 40.) From a photograph (Scott, “Studies”)}}

{{IMG:EB1911 Paleobotany - Palaeostachya pedunculata - fertile shoot.jpg|Palaeostachya pedunculata. Fertile shoot, bearing numerous cones and a few leaves. After Williamson (Scott, “Studies”)}}

{{IMG:EB1911 Paleobotany - Lyginodendron oldhamium - stem.jpg|Lyginodendron oldhamium. Transverse section of stem, showing the pith containing groups of sclerotic cells, the primary xylem-strands, secondary wood and phloem, pericycle and cortex. 𝑙𝑡1-𝑙𝑡5, leaf-traces, numbered according to the phyllotaxis, 𝑙𝑡5 belonging to the lowest leaf of the five; 𝑝ℎ, a group of primary phloem; 𝑝𝑑, periderm, formed from pericycle. (× 3.)}}

{{IMG:EB1911 Paleobotany - Sphenophyllum insigne - stem.jpg|Sphenophyllum insigne. Transverse section of stem, showing triangular primary wood, secondary wood, remains of phloem, and primary cortex. (× about 30.) From a photograph (Scott, “Studies”)}}

{{IMG:EB1911 Paleobotany - Cordaianthus Penjoni - male catkin.jpg|Cordaianthus Penjoni. A, Male catkin in longitudinal section: 𝑎, axis; 𝑏, bracts; 𝑐, 𝑑, filaments of stamens, hearing the pollen-sacs (𝑒 and 𝑓) at the top; 𝑣, apex of axis. (× 62.) B, Stamens more highly magnified: 𝑔, vascular bundle of filament; 𝑒, pollen-sac after dehiscence. (× 23.) After Renault (Scott, “Studies”)}}

{{IMG:EB1911 Paleobotany - Cordaianthus Penjoni - stamens.jpg|Plate}}
```

---

## PALAEONTOLOGY — vol 20

**Article ID:** 4211920  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|style="margin:auto; width:780px"
|-
|{{right|{{sc|Plate II.}}}}
|-
|[[Image:EB1911 Palaeontology - skeleton of allosaurus.jpg|780px]]
|-
|{{Ts|ac|lh100}}|{{sc|Fig.}} 4.—SKELETON OF ALLOSAURUS.<br><br>
|-
|[[Image:EB1911 Palaeontology - restoration of allosaurus.jpg|780px]]
|-
|{{Ts|ac|lh100}}|{{sc|Fig.}} 5.—RESTORATION OF ALLOSAURUS.
|-
|{{fine block|''Materials for the Restoration of Dinosaurs''.—Carnivorous dinosaur (''Allosaurus'') of the Upper Jurassic period of North America, an animal
closely related to the ''Megalosaurus'' type of England. The skeleton (fig.&nbsp;4) was found nearly complete in the beds of the Morrison
formation, Upper Jurassic of central Wyoming. U.S.A. Near it was discovered the posterior portion of the skeleton of a giant herbivorous
dinosaur (''Brontosaurus Marsh''). It was observed that ten of the caudal vertebrae of the latter skeleton bore tooth marks and grooves
corresponding exactly with the sharp pointed teeth in the jaw of the carnivorous dinosaur. This proved that the great herbivorous
dinosaur had been preyed upon by its smaller carnivorous contemporary. Teeth of the carnivorous dinosaur scattered among the bones
of the herbivorous dinosaur completed the line of circumstantial evidence. Upon this testimony the restoration (fig.&nbsp;5) of the Megalosaur
has been drawn by Charles R. Knight under the direction of Professor Osborn.}}
|-
|style="text-align:center; font-size:92%; line-height:100%"|(''Originals reproduced by permission of the 
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **5** | **5** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Palaeontology - skeleton of allosaurus.jpg|SKELETON OF ALLOSAURUS}}

{{IMG:EB1911 Palaeontology - restoration of allosaurus.jpg|RESTORATION OF ALLOSAURUS}}

{{LEGEND:(Originals reproduced by permission of the American Museum of Natural History.)}LEGEND}
```

### Current body
```
{{IMG:EB1911 Palaeontology - skeleton of allosaurus.jpg|SKELETON OF ALLOSAURUS}}

{{IMG:EB1911 Palaeontology - restoration of allosaurus.jpg|RESTORATION OF ALLOSAURUS}}

{{LEGEND:(Originals reproduced by permission of the American Museum of Natural History.)}LEGEND}
```

---

## PALAEONTOLOGY — vol 20

**Article ID:** 4211921  
**Signature:** `wikitable depth=2 wt=multi ht=0 has_colspan`

### Source excerpt
```
{{EB1911 fine print/s}}
{|style="margin:auto; width:1060px"
| || ||{{right|{{sc|Plate IV.}}}}
|-
|[[Image:EB1911 Palaeontology - hypohippus.jpg|x600px|center]]
|&emsp;
|[[Image:EB1911 Palaeontology - neohipparion.jpg|x600px|center]]
|-
|colspan="3"|
{|width="100%"
|-valign="top"
|width="30%" style="padding-right: 1em"|
{{sc|Fig.}} 12.—''Hypohippus'', a forest-living
horse, rear view, showing
large lateral digits on the fore and hind feet, adapted
to prevent the animal from sinking into the soft soil.
|align="center"|
{{sc|Fig.}} 13.—''Neohipparion'', a plains-living horse with very slender limbs and lateral digits small and well raised from the ground,<br>adapted to a dry, hard soil.
|}
|-
|colspan="3"|
{|width="100%"
|-valign="bottom"
|[[Image:EB1911 Palaeontology - hypohippus restoration.jpg|x225px|center]]
|rowspan=2 valign="top" style="padding-left: 1em; padding-right: 1em"|
Laws of Local Adaptive
Radiation and Polyphyletic
Evolution, illustrated
by two Upper Miocene
Horses of the Plains Region
of North America.  These
horses are of the same
geologic age (Upper
Miocene) and were found in
the same geographic region
(South Dakota, U.S.A.).
One is supposed to have
lived in the forests along
the stream borders, and the
other in the open plains.

(''Illustrations reproduced by''
''permission of the American''
''Museum of Natural''
''History, New York.'')
|[[Image:EB1911 Palaeontology - neohipparion restoration.jpg|x225px|center]]
|-valign="top"
|align="center"|
{{sc|Fig.}} 14.
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Palaeontology - hypohippus.jpg|Hypohippus, a forest-living horse, rear view, showing large lateral digits on the fore and hind feet, adapted to prevent the animal from sinking into the soft soil}}

{{IMG:EB1911 Palaeontology - neohipparion.jpg|Neohipparion, a plains-living horse with very slender limbs and lateral digits small and well raised from the ground, adapted to a dry, hard soil}}

{{IMG:EB1911 Palaeontology - hypohippus restoration.jpg|Restoration of Hypohippus. (From a drawing by Charles R. Knight, made under the direction of Professor Osborn.)}}

{{IMG:EB1911 Palaeontology - neohipparion restoration.jpg|Restoration of Neohipparion. (From a drawing by Charles R. Knight, made under the direction of Professor Osborn.)}}
```

### Current body
```
{{IMG:EB1911 Palaeontology - hypohippus.jpg|Hypohippus, a forest-living horse, rear view, showing large lateral digits on the fore and hind feet, adapted to prevent the animal from sinking into the soft soil}}

{{IMG:EB1911 Palaeontology - neohipparion.jpg|Neohipparion, a plains-living horse with very slender limbs and lateral digits small and well raised from the ground, adapted to a dry, hard soil}}

{{IMG:EB1911 Palaeontology - hypohippus restoration.jpg|Restoration of Hypohippus. (From a drawing by Charles R. Knight, made under the direction of Professor Osborn.)}}

{{IMG:EB1911 Palaeontology - neohipparion restoration.jpg|Restoration of Neohipparion. (From a drawing by Charles R. Knight, made under the direction of Professor Osborn.)}}
```

---

## PATHOLOGY, PLATE V — vol 20

**Article ID:** 4212309  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|{{Ts|ma|width:800px}}
|{{Ts|ar}}|{{sc|Plate}} V.&emsp;
|-
|[[File:EB1911 - Pathology - Plate V.png|800px]]
|}

<!-- Fig. 44.—Thyroid gland—cystic goitre. The gland
spaces vary in size and many may show marked
cystic formation. These vesicles are filled with
the colloid material (× 90 diam.)

Fig. 45.—Liver. Fatty Infiltration. The liver cells
are seen to contain a large globule of fat which
pushes the cell nucleus to one side— giving the
signet-ring appearance. (× 250 diam.)

Fig. 50.—Phagocytic cells (in sputum)
which have taken into their proto-
plasm particles of carbon pigment.
(× 500 diam.)

Fig. 47.—Pudic artery showing calcified areas
in the muscular coat of the vessel. These
degenerated parts are darkly stained owing
to the calcareous particles having a strong
affinity for the haemotoxylin stain. (× 35
diam.) 

Fig. 46.—Heart. Fatty Infiltration. The fat
cells are increased and infiltrate the connective
tissue between the bundles of
muscle fibres. These are pressed upon and
become atrophied, and may ultimately be
replaced by adipose tissue. (× 40 diam.)

Fig. 49.—Melanotic sarcoma. Many of these
malignant cells develop and accumulate
in their protoplasm granules of melanin
pigment. (× 300 diam.)

Fig. 48.—Brown atrophy of heart. The
muscle fibres show the pigment
granules, which are of a light yellow
colour, situated specially at the poles
of the fibre nucleus and extending
short distance in the long axis of the
fibre. (× 400 diam.)

Fig. 51. Liver, waxy. The swolle
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **2** | **2** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Pathology - Plate V.png|Plate V}}
```

### Current body
```
{{IMG:EB1911 - Pathology - Plate V.png|Plate V}}
```

---

## PERGAMUM — vol 21

**Article ID:** 4212624  
**Signature:** `wikitable depth=2 wt=multi ht=0 has_colspan`

### Source excerpt
```
{{right|{{sc|Plate I.}}}}
{|align="center"
|
{|border="1"
|[[Image:EB1911 Pergamum - Great Altar of Zeus (North Wing).jpg|x475px]]
|}
|&emsp;
|
{|border="1"
|[[Image:EB1911 Pergamum - Great Altar of Zeus (South Wing).jpg|x475px]]
|}
|-
|align="center"|THE NORTH WING, WEST AND SOUTH SIDES.
|
|align="center"|THE SOUTH WING, WEST AND SOUTH SIDES.
|-
|colspan="3"|
{|border="1"
|colspan="3"|[[Image:EB1911 Pergamum - Great Altar of Zeus.jpg|800px]]
|}
|-
|colspan="3" align="center"|THE GREAT ALTAR OF ZEUS, FROM THE NORTH-WEST, AS SET UP IN THE KAISER FRIEDRICH MUSEUM, BERLIN.
|-style="font-size: 70%"
|colspan="3" align="right"|From photographs by W. Titzenthaler, Berlin.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **9** | **9** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **2** | **2** |
| header text     | 'Plate I' | 'Plate I' |
| footer text     | 'THE GREAT ALTAR OF ZEUS, FROM THE NORTH-WEST, AS SET UP IN THE KAISER FRIEDRICH MUSEUM, BERLIN. From photographs by W. T' | 'THE GREAT ALTAR OF ZEUS, FROM THE NORTH-WEST, AS SET UP IN THE KAISER FRIEDRICH MUSEUM, BERLIN. From photographs by W. T' |

**Verdict:** ✅ identical

### Baseline body
```
Plate I

{{IMG:EB1911 Pergamum - Great Altar of Zeus (North Wing).jpg|THE NORTH WING, WEST AND SOUTH SIDES}}

{{IMG:EB1911 Pergamum - Great Altar of Zeus (South Wing).jpg|THE SOUTH WING, WEST AND SOUTH SIDES}}

{{IMG:EB1911 Pergamum - Great Altar of Zeus.jpg}}

THE GREAT ALTAR OF ZEUS, FROM THE NORTH-WEST, AS SET UP IN THE KAISER FRIEDRICH MUSEUM, BERLIN. From photographs by W. Titzenthaler, Berlin
```

### Current body
```
Plate I

{{IMG:EB1911 Pergamum - Great Altar of Zeus (North Wing).jpg|THE NORTH WING, WEST AND SOUTH SIDES}}

{{IMG:EB1911 Pergamum - Great Altar of Zeus (South Wing).jpg|THE SOUTH WING, WEST AND SOUTH SIDES}}

{{IMG:EB1911 Pergamum - Great Altar of Zeus.jpg}}

THE GREAT ALTAR OF ZEUS, FROM THE NORTH-WEST, AS SET UP IN THE KAISER FRIEDRICH MUSEUM, BERLIN. From photographs by W. Titzenthaler, Berlin
```

---

## PERGAMUM — vol 21

**Article ID:** 4212625  
**Signature:** `wikitable depth=2 wt=multi ht=0`

### Source excerpt
```
{{sc|Plate II.}}
{|align="center"
|
{|border="1"
|[[Image:EB1911 Pergamum - Great Altar of Zeus (North Side).jpg|800px]]
|}
|-
|
{|border="1"
|[[Image:EB1911 Pergamum - Great Altar of Zeus (South Side).jpg|800px]]
|}
|-
|
{|border="1"
|[[Image:EB1911 Pergamum - Great Altar of Zeus (East Side).jpg|800px]]
|}
|-
|
{|border="1"
|[[Image:EB1911 Pergamum - Great Altar of Zeus (West Side).jpg|800px]]
|}
|-
|align="center"|NORTH, SOUTH, EAST, AND WEST SIDES OF THE GREAT ALTAR OF ZEUS.
|-style="font-size: 70%"
|align="right"|From photographs by W. Titzenthaler, Berlin.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'Plate II' | 'Plate II' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
Plate II

{{IMG:EB1911 Pergamum - Great Altar of Zeus (North Side).jpg|NORTH, SOUTH, EAST, AND WEST SIDES OF THE GREAT ALTAR OF ZEUS}}

{{IMG:EB1911 Pergamum - Great Altar of Zeus (South Side).jpg|From photographs by W. Titzenthaler, Berlin}}

{{IMG:EB1911 Pergamum - Great Altar of Zeus (East Side).jpg}}

{{IMG:EB1911 Pergamum - Great Altar of Zeus (West Side).jpg}}
```

### Current body
```
Plate II

{{IMG:EB1911 Pergamum - Great Altar of Zeus (North Side).jpg|NORTH, SOUTH, EAST, AND WEST SIDES OF THE GREAT ALTAR OF ZEUS}}

{{IMG:EB1911 Pergamum - Great Altar of Zeus (South Side).jpg|From photographs by W. Titzenthaler, Berlin}}

{{IMG:EB1911 Pergamum - Great Altar of Zeus (East Side).jpg}}

{{IMG:EB1911 Pergamum - Great Altar of Zeus (West Side).jpg}}
```

---

## PETROLOGY, PLATE I — vol 21

**Article ID:** 4212793  
**Signature:** `center_template depth=0 wt=0 ht=0`

### Source excerpt
```
{{center|[[File:EB1911 Petrology - Plate I.jpg]]}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 0 | 0 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **3** | **3** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'center' | 'center' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
center

{{IMG:EB1911 Petrology - Plate I.jpg}}
```

### Current body
```
center

{{IMG:EB1911 Petrology - Plate I.jpg}}
```

---

## PETROLOGY, PLATE II — vol 21

**Article ID:** 4212794  
**Signature:** `center_template depth=0 wt=0 ht=0`

### Source excerpt
```
{{center|[[File:EB1911 Petrology - Plate II.jpg]]}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 0 | 0 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **3** | **3** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'center' | 'center' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
center

{{IMG:EB1911 Petrology - Plate II.jpg}}
```

### Current body
```
center

{{IMG:EB1911 Petrology - Plate II.jpg}}
```

---

## PETROLOGY, PLATE III — vol 21

**Article ID:** 4212795  
**Signature:** `center_template depth=0 wt=0 ht=0`

### Source excerpt
```
{{center|[[File:EB1911 Petrology - Plate III.jpg]]}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 0 | 0 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **3** | **3** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'center' | 'center' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
center

{{IMG:EB1911 Petrology - Plate III.jpg}}
```

### Current body
```
center

{{IMG:EB1911 Petrology - Plate III.jpg}}
```

---

## PETROLOGY, PLATE IV — vol 21

**Article ID:** 4212796  
**Signature:** `center_template depth=0 wt=0 ht=0`

### Source excerpt
```
{{center|[[File:EB1911 Petrology - Plate IV.jpg]]}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 0 | 0 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **3** | **3** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'center' | 'center' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
center

{{IMG:EB1911 Petrology - Plate IV.jpg}}
```

### Current body
```
center

{{IMG:EB1911 Petrology - Plate IV.jpg}}
```

---

## PHOTOGRAPHY — vol 21

**Article ID:** 4212988  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|{{Ts|ma|width:1000px}}
| || ||{{Ts|ar}}|{{sc|Plate II.}}&numsp;
|-
|[[File:EB1911 - Photography - Plate II a.jpg|509px]]||{{em|2.2}}
|[[File:EB1911 - Photography - Plate II b.jpg|451px]]
|-{{Ts|ac}}
|PORTRAIT STUDY.&emsp;By {{sc|James Craig Annan}}.|| 
|PORTRAIT.&emsp;By {{sc|David Octavius Hill, R.S.A.}}
|}
<br><br>
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Photography - Plate II a.jpg|PORTRAIT STUDY. By James Craig Annan}}

{{IMG:EB1911 - Photography - Plate II b.jpg|PORTRAIT. By David Octavius Hill, R.S.A}}
```

### Current body
```
{{IMG:EB1911 - Photography - Plate II a.jpg|PORTRAIT STUDY. By James Craig Annan}}

{{IMG:EB1911 - Photography - Plate II b.jpg|PORTRAIT. By David Octavius Hill, R.S.A}}
```

---

## Pig, PLATE — vol 21

**Article ID:** 4213078  
**Signature:** `center_template depth=0 wt=0 ht=0 toplegend`

### Source excerpt
```
{{flex wrap centre
 |[[File:EB1911 Pig - Berkshire boar.jpg|x300px]]<br>
BERKSHIRE BOAR
 |[[File:EB1911 Pig - Large white sow.jpg|x300px]]<br>
LARGE WHITE SOW.
}}

{{flex wrap centre
 |[[File:EB1911 Pig - Middle white boar.jpg|x300px]]<br>
MIDDLE WHITE BOAR
 |[[File:EB1911 Pig - Small white boar.jpg|x300px]]<br>
SMALL WHITE BOAR.
}}

{{flex wrap centre
 |[[File:EB1911 Pig - Large black sow.jpg|x300px]]<br>
LARGE BLACK SOW.
 |[[File:EB1911 Pig - Tamworth boar.jpg|x300px]]<br>
TAMWORTH BOAR.
}}

{{center|ENGLISH BREEDS OF PIG, from photographs of F. Babbage. The comparative sizes of the animals are indicated by the scale of reproduction of the photographs.}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 6 | 6 |
| captioned       | 6 | 6 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **16** | **16** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **2** | **2** |
| header text     | 'flex wrap centre' | 'flex wrap centre' |
| footer text     | 'ENGLISH BREEDS OF PIG, from photographs of F. Babbage. The comparative sizes of the animals are indicated by the scale o' | 'ENGLISH BREEDS OF PIG, from photographs of F. Babbage. The comparative sizes of the animals are indicated by the scale o' |

**Verdict:** ✅ identical

### Baseline body
```
flex wrap centre

{{IMG:EB1911 Pig - Berkshire boar.jpg|BERKSHIRE BOAR}}

{{IMG:EB1911 Pig - Large white sow.jpg|LARGE WHITE SOW}}

{{IMG:EB1911 Pig - Middle white boar.jpg|MIDDLE WHITE BOAR}}

{{IMG:EB1911 Pig - Small white boar.jpg|SMALL WHITE BOAR}}

{{IMG:EB1911 Pig - Large black sow.jpg|LARGE BLACK SOW}}

{{IMG:EB1911 Pig - Tamworth boar.jpg|TAMWORTH BOAR}}

ENGLISH BREEDS OF PIG, from photographs of F. Babbage. The comparative sizes of the animals are indicated by the scale of reproduction of the photographs
```

### Current body
```
flex wrap centre

{{IMG:EB1911 Pig - Berkshire boar.jpg|BERKSHIRE BOAR}}

{{IMG:EB1911 Pig - Large white sow.jpg|LARGE WHITE SOW}}

{{IMG:EB1911 Pig - Middle white boar.jpg|MIDDLE WHITE BOAR}}

{{IMG:EB1911 Pig - Small white boar.jpg|SMALL WHITE BOAR}}

{{IMG:EB1911 Pig - Large black sow.jpg|LARGE BLACK SOW}}

{{IMG:EB1911 Pig - Tamworth boar.jpg|TAMWORTH BOAR}}

ENGLISH BREEDS OF PIG, from photographs of F. Babbage. The comparative sizes of the animals are indicated by the scale of reproduction of the photographs
```

---

## PLATE, PLATE I — vol 21

**Article ID:** 4213285  
**Signature:** `wikitable depth=2 wt=multi ht=0 has_colspan`

### Source excerpt
```
{|align="center" cellpadding="0" cellspacing="0"
|21
|rowspan="3"|
{|border="1"
|[[Image:EB1911 Plate - Greek Plate (Bronze Age).jpg|600px]]
|}
|22
|-
|23
|-
|24
|25
|-
|
|
{|width="600" cellpadding="0" cellspacing="0"
|valign="top"|{{small-caps|Fig}}. 21.—
|Golden {{Greek|Δέπας ἀμφικύπελλον}} from Mycenae (Late Minoan i.; about 1600 {{asc|B.C.}})
|-
|valign="top"|{{nowrap|{{small-caps|Fig}}. 22.—}}
|Fragment of a Silver Vase with Relief Design, showing the Defence of a City, from Mycenae (Late Minoan i.).
|-
|valign="top"|{{small-caps|Fig}}. 23.—
|Golden Cup from Troy (Early Minoan iii.; 2500 {{asc|B.C.}} or earlier).
|-
|valign="top" colspan="2"|{{small-caps|Fig}}. 24, 25.—Gold Cups of Vaphio (Late Minoan i.). 
|}
|-
|colspan="3" align="center"|GREEK PLATE OF THE BRONZE AGE (PREHISTORIC PERIOD)
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **2** | **2** |
| header text     | '21' | '21' |
| footer text     | 'GREEK PLATE OF THE BRONZE AGE (PREHISTORIC PERIOD)' | 'GREEK PLATE OF THE BRONZE AGE (PREHISTORIC PERIOD)' |

**Verdict:** ✅ identical

### Baseline body
```
21

{{IMG:EB1911 Plate - Greek Plate (Bronze Age).jpg|Gold Cups of Vaphio (Late Minoan i.)}}

GREEK PLATE OF THE BRONZE AGE (PREHISTORIC PERIOD)
```

### Current body
```
21

{{IMG:EB1911 Plate - Greek Plate (Bronze Age).jpg|Gold Cups of Vaphio (Late Minoan i.)}}

GREEK PLATE OF THE BRONZE AGE (PREHISTORIC PERIOD)
```

---

## PLATE — vol 21

**Article ID:** 4213286  
**Signature:** `wikitable depth=2 wt=multi ht=0 has_colspan`

### Source excerpt
```
{|{{Ts|ma|lh110}}
|colspan=3 {{Ts|ar}}|{{sc|Plate II.}}
|-
|valign="top"|
{|border="1"
|[[Image:EB1911 Plate - Gold Chalice and Paten of Bishop Foxe.jpg|390px]]
|}
{{sm|''Photo, Hills & Saunders, by permission of Corpus Cristi College''.}}

{{csc|Fig. 26—GOLD CHALICE AND PATEN OF BISHOP FOXE.}}
<br>
{|border="1"
|[[Image:EB1911 Plate - Salt of the Vintners' Co.jpg|390px]]
|}
{{sm|''Photo, Southwark Photo Eng. Co.''}}

{{csc|Fig. 27—SALT OF THE VINTNERS’ COMPANY (ELIZABETHAN).}}
<br>
{|border="1"
|[[Image:EB1911 Plate - Braikenbridge Mazer Bowl.jpg|390px]]
|}
{{sm|''By permission of Crichton Bros.''}}

{{csc|Fig. 28—BRAIKENBRIDGE MAZER BOWL.}}
|&emsp;
|valign="top"|
{|border="1"
|[[Image:EB1911 Plate - Gold Cup and Cover, Charles II.jpg|390px]]
|}
{{sm|From Jackson, ''History of English Plate'', by permission of C. J. Jackson, F.S.A.}}

{{c|{{sc|Fig}}. 29—GOLD CUP AND COVER, CHARLES II.}}
<br>
{|border="1"
|[[Image:EB1911 Plate - Tudor Cup.jpg|390px]]
|}
{{sm|From Gardner, ''Old Silverwork'', by permission of B. T. Batsford.}}

{{csc|Fig. 30—TUDOR CUP.}}
<br>
{|border="1"
|[[Image:EB1911 Plate - Ardagh Chalice.jpg|390px]]
|}
{{sm|''By permission of the Royal Irish Academy.''}}

{{csc|Fig. 31—ARDAGH CHALICE.}}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 6 | 6 |
| captioned       | 6 | 6 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **12** | **12** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Plate - Gold Chalice and Paten of Bishop Foxe.jpg|Fig. 26—GOLD CHALICE AND PATEN OF BISHOP FOXE}}

{{IMG:EB1911 Plate - Salt of the Vintners' Co.jpg|Fig. 27—SALT OF THE VINTNERS’ COMPANY (ELIZABETHAN)}}

{{IMG:EB1911 Plate - Braikenbridge Mazer Bowl.jpg|Fig. 28—BRAIKENBRIDGE MAZER BOWL}}

{{IMG:EB1911 Plate - Gold Cup and Cover, Charles II.jpg|Fig . 29—GOLD CUP AND COVER, CHARLES II}}

{{IMG:EB1911 Plate - Tudor Cup.jpg|Fig. 30—TUDOR CUP}}

{{IMG:EB1911 Plate - Ardagh Chalice.jpg|Fig. 31—ARDAGH CHALICE}}
```

### Current body
```
{{IMG:EB1911 Plate - Gold Chalice and Paten of Bishop Foxe.jpg|Fig. 26—GOLD CHALICE AND PATEN OF BISHOP FOXE}}

{{IMG:EB1911 Plate - Salt of the Vintners' Co.jpg|Fig. 27—SALT OF THE VINTNERS’ COMPANY (ELIZABETHAN)}}

{{IMG:EB1911 Plate - Braikenbridge Mazer Bowl.jpg|Fig. 28—BRAIKENBRIDGE MAZER BOWL}}

{{IMG:EB1911 Plate - Gold Cup and Cover, Charles II.jpg|Fig . 29—GOLD CUP AND COVER, CHARLES II}}

{{IMG:EB1911 Plate - Tudor Cup.jpg|Fig. 30—TUDOR CUP}}

{{IMG:EB1911 Plate - Ardagh Chalice.jpg|Fig. 31—ARDAGH CHALICE}}
```

---

## PROCESS — vol 22

**Article ID:** 4213989  
**Signature:** `wikitable depth=1 wt=1 ht=0 has_colspan`

### Source excerpt
```
{|align="center" style="text-align: center"
|style="height: 0px; width: 180px"|
|style="height: 0px; width:  40px"|
|style="height: 0px; width: 180px"|
|style="height: 0px; width:  40px"|
|style="height: 0px; width: 180px"|
|style="height: 0px; width:  40px"|
|style="height: 0px; width: 180px"|
|-
|colspan="3"|[[File:EB1911 Process (printing) - color separation - yellow.jpg|400px]]
|
|colspan="3"|[[File:EB1911 Process (printing) - color separation - red.jpg|400px]]
|-
|
|A.
|colspan="3"|GALLIREX JOHNSTONI.
|B.
|-style="font-size: 90%"
|colspan="7"|The Turaco of Ruwenzori.
|-style="font-size: 81%"
|colspan="7"|''From a Drawing by Sir Harry Johnston, from'' “''The Uganda Protectorate'',” ''by Permission of Hutchinson & Co.''
|-
|&nbsp;
|-
|colspan="3"|[[File:EB1911 Process (printing) - color separation - blue.jpg|400px]]
|
|colspan="3"|[[File:EB1911 Process (printing) - color separation - result.jpg|400px]]
|-
|style="font-size: 81%" align="left"|''&emsp;Three-Colour Process.''<br />&nbsp;
|C.
|colspan="3"|
|D.
|style="font-size: 81%" align="center"|''Andre & Sleigh, Ltd., Engravers,''<br />''Bushey, Herts.''
|-
|colspan="7"|<div style="width: 650px; margin-left: auto; margin-right: auto">
SHOWING THE SEPARATE COLOURS EMPLOYED IN PHOTO-REPRODUCTION
BY THE THREE-COLOUR PROCESS
</div>
|-
|colspan="7" style="font-size: 81%"|<div style="width: 650px; margin-left: auto; margin-right: auto">
The three primary colours are separated out by photography, each colour sensation is etched o
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 6 | 6 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **16** | **16** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | 'The three primary colours are separated out by photography, each colour sensation is etched on copper, and when the Bloc' | 'The three primary colours are separated out by photography, each colour sensation is etched on copper, and when the Bloc' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Process (printing) - color separation - yellow.jpg|Three-Colour Process}}

{{IMG:EB1911 Process (printing) - color separation - red.jpg|Andre & Sleigh, Ltd., Engravers, Bushey, Herts}}

{{IMG:EB1911 Process (printing) - color separation - blue.jpg|SHOWING THE SEPARATE COLOURS EMPLOYED IN PHOTO-REPRODUCTION}}

{{IMG:EB1911 Process (printing) - color separation - result.jpg|BY THE THREE-COLOUR PROCESS}}

{{LEGEND:style="height: 0px; width: 40px"}LEGEND}

{{LEGEND:style="height: 0px; width: 40px"}LEGEND}

{{LEGEND:style="height: 0px; width: 40px"}LEGEND}

{{LEGEND:GALLIREX JOHNSTONI}LEGEND}

{{LEGEND:The Turaco of Ruwenzori}LEGEND}

{{LEGEND:From a Drawing by Sir Harry Johnston, from “The Uganda Protectorate,” by Permission of Hutchinson & Co}LEGEND}

The three primary colours are separated out by photography, each colour sensation is etched on copper, and when the Blocks representing Yellow (A), Red (B), and Blue (C), as illustrated above, are superimposed in the printing press, the result (D) is a reproduction of the original in all its combinations of colour
```

### Current body
```
{{IMG:EB1911 Process (printing) - color separation - yellow.jpg|Three-Colour Process}}

{{IMG:EB1911 Process (printing) - color separation - red.jpg|Andre & Sleigh, Ltd., Engravers, Bushey, Herts}}

{{IMG:EB1911 Process (printing) - color separation - blue.jpg|SHOWING THE SEPARATE COLOURS EMPLOYED IN PHOTO-REPRODUCTION}}

{{IMG:EB1911 Process (printing) - color separation - result.jpg|BY THE THREE-COLOUR PROCESS}}

{{LEGEND:style="height: 0px; width: 40px"}LEGEND}

{{LEGEND:style="height: 0px; width: 40px"}LEGEND}

{{LEGEND:style="height: 0px; width: 40px"}LEGEND}

{{LEGEND:GALLIREX JOHNSTONI}LEGEND}

{{LEGEND:The Turaco of Ruwenzori}LEGEND}

{{LEGEND:From a Drawing by Sir Harry Johnston, from “The Uganda Protectorate,” by Permission of Hutchinson & Co}LEGEND}

The three primary colours are separated out by photography, each colour sensation is etched on copper, and when the Blocks representing Yellow (A), Red (B), and Blue (C), as illustrated above, are superimposed in the printing press, the result (D) is a reproduction of the original in all its combinations of colour
```

---

## REGALIA — vol 23

**Article ID:** 4241893  
**Signature:** `wikitable depth=3 wt=multi ht=0 has_colspan`

### Source excerpt
```
{| {{ts|mc|fs085|lh110}} width=815px
| {{ts|ar}} colspan="3" | {{sc|Plate}} I.
|-
|
{| width="100%"
|- {{ts|vtp}}
| {{ts|ac}} |
{| {{ts|ba|bc}}
|{{ts|padding:1px}}| [[Image:EB1911 Regalia, Plate I, 1.jpg|380px]]
|}
1.—{{sc|St EDWARD’S CROWN}}. The ancient crown was destroyed at the Commonwealth, and a model made for Charles II’s coronation.
| &emsp; || {{ts|ac}}|
{| {{ts|ba|bc}}
|{{ts|padding:1px}}| [[Image:EB1911 Regalia, Plate I, 2.jpg|380px]]
|}
2.—THE IMPERIAL STATE CROWN, as worn by Queen Victoria. The Black Prince’s ruby is in the centre. Modifications in the cap were made for the coronation of King Edward VII. and the smaller “Cullinan” diamond substituted for the sapphire below the ruby.
|}
|-
|
{| width="100%"
|- {{ts|vbm}}
|
{| {{ts|ba|bc}}
|{{ts|padding:1px}}| [[Image:EB1911 Regalia, Plate I, 3.jpg|380px]]
|}
| &emsp; || {{ts|ar}} |
{| {{ts|ba|bc}}
|{{ts|padding:1px}}| [[Image:EB1911 Regalia, Plate I, 4.jpg|380px]]
|}
|- {{ts|vbtp}}
| {{ts|ac}} | 3.—QUEEN ALEXANDRA’S CORONATION CROWN, with the<br>Koh-i-Noor in centre. ||
| {{ts|ac}} | 4.—THE CORONET OF THE PRINCE OF WALES.
|}
|-
| colspan="3" | &nbsp;
|-
|
{| {{ts|mc}} width=705px
|-
| {{ts|ac}} |
{| {{ts|ba|bc}}
|{{ts|padding:1px}}| [[Image:EB1911 Regalia, Plate I, 5.jpg|254px]]
|}
5.—THE LARGER OR KING’S ORB.
| {{ts|pl15|pr15}} | The illustrations on these plates are, except where otherwise stated, repro&shy;duced by permission from the unique collection of photographs in the pos&shy;session of {{sc|Sir Benjamin 
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 6 | 6 |
| captioned       | 6 | 6 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **15** | **15** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'Plate I.' | 'Plate I.' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
Plate I.

{{IMG:EB1911 Regalia, Plate I, 1.jpg|St EDWARD’S CROWN . The ancient crown was destroyed at the Commonwealth, and a model made for Charles II’s coronation}}

{{IMG:EB1911 Regalia, Plate I, 2.jpg|THE IMPERIAL STATE CROWN, as worn by Queen Victoria. The Black Prince’s ruby is in the centre. Modifications in the cap were made for the coronation of King Edward VII. and the smaller “Cullinan” diamond substituted for the sapphire below the ruby}}

{{IMG:EB1911 Regalia, Plate I, 3.jpg|QUEEN ALEXANDRA’S CORONATION CROWN, with the Koh-i-Noor in centre}}

{{IMG:EB1911 Regalia, Plate I, 4.jpg|THE CORONET OF THE PRINCE OF WALES}}

{{IMG:EB1911 Regalia, Plate I, 5.jpg|THE LARGER OR KING’S ORB}}

{{IMG:EB1911 Regalia, Plate I, 6.jpg|THE LESSER OR QUEEN’S ORB}}

{{LEGEND:The illustrations on these plates are, except where otherwise stated, reproduced by permission from the unique collection of photographs in the possession of Sir Benjamin Stone , formerly M. P. for East Birmingham}LEGEND}
```

### Current body
```
Plate I.

{{IMG:EB1911 Regalia, Plate I, 1.jpg|St EDWARD’S CROWN . The ancient crown was destroyed at the Commonwealth, and a model made for Charles II’s coronation}}

{{IMG:EB1911 Regalia, Plate I, 2.jpg|THE IMPERIAL STATE CROWN, as worn by Queen Victoria. The Black Prince’s ruby is in the centre. Modifications in the cap were made for the coronation of King Edward VII. and the smaller “Cullinan” diamond substituted for the sapphire below the ruby}}

{{IMG:EB1911 Regalia, Plate I, 3.jpg|QUEEN ALEXANDRA’S CORONATION CROWN, with the Koh-i-Noor in centre}}

{{IMG:EB1911 Regalia, Plate I, 4.jpg|THE CORONET OF THE PRINCE OF WALES}}

{{IMG:EB1911 Regalia, Plate I, 5.jpg|THE LARGER OR KING’S ORB}}

{{IMG:EB1911 Regalia, Plate I, 6.jpg|THE LESSER OR QUEEN’S ORB}}

{{LEGEND:The illustrations on these plates are, except where otherwise stated, reproduced by permission from the unique collection of photographs in the possession of Sir Benjamin Stone , formerly M. P. for East Birmingham}LEGEND}
```

---

## REGALIA — vol 23

**Article ID:** 4241894  
**Signature:** `wikitable depth=3 wt=multi ht=0 has_colspan`

### Source excerpt
```
{| {{ts|mc|fs085|lh110}} width=815px
| colspan="3" | {{right|{{sc|Plate}} II.}}
|- {{ts|vtp}}
| {{ts|ac}} width="1%" |
{|
| {{ts|ac}} |
{| {{ts|border-spacing:0}}
|{{ts|ba|padding:1px;}}|[[Image:EB1911 Regalia, Plate II, 1.jpg|300px]]
|}
{| {{ts|mc|ac|width: 100%;}}
| ''a'' || ''b'' || ''c'' || ''d'' || ''e''
|}
|-
| 1.—THE SCEPTRES: (''a'') The Scepter with the Dove; (''b'') The Royal Sceptre with the Cross (''Cf''. Fig. 3); (''c'') The Queen’s Sceptre with the Cross; (''d'') The Queen’s Ivory Rod; (''e'') The Queen’s Sceptre with the Dove.
|-
| &nbsp;
|-
|
{| {{ts|border-spacing:0}}
|{{ts|ba|padding:1px;}}|[[Image:EB1911 Regalia, Plate II, 6.jpg|300px]]
|}
|-
| {{ts|ac}} | 6.—THE AMPULLA.
|}
| &nbsp; || {{ts|ac}} |
{|
| {{ts|ac}} |
{| {{ts|border-spacing:0}}
|{{gap}}[[Image:EB1911 Regalia, Plate II, 2.jpg|110px]]{{gap}}
|}
2.—{{uc|The Coronation Spoon.}}
{| {{ts|border-spacing:0}}
|{{ts|ba|padding:20px;}}| [[Image:EB1911 Regalia, Plate II, 3.jpg|140px]]
|}
3.—THE HEAD OF THE ROYAL SCEPTRE with the largest of the “Star of Africa” (Cullinan) Diamonds. &emsp; ''Photo'', ''W. E. Gray.''
| &nbsp; || {{ts|ac}} |
{| {{ts|border-spacing:0}}
|{{ts|ba|padding:1px;}}| [[Image:EB1911 Regalia, Plate II, 4.jpg|300px]]
|}
{| {{ts|ac|mc|width: 100%}}
| ''a'' || ''b'' || ''c''
|}
4.—THE SWORDS: (''a'') The Spiritual Sword of Justice; (''b'') The Sword of State; (''c'') The Temporal Sword of Justice. {{right|{{smaller|''Photo'', ''W. E. Gray.''}}}}
{| {{ts|border-spacing:0}}
|{{ts|ba|padding
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 7 | 7 |
| captioned       | 7 | 7 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **16** | **16** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'Plate II.' | 'Plate II.' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
Plate II.

{{IMG:EB1911 Regalia, Plate II, 1.jpg|THE SCEPTRES: (a) The Scepter with the Dove; (b) The Royal Sceptre with the Cross (Cf. Fig. 3); (c) The Queen’s Sceptre with the Cross; (d) The Queen’s Ivory Rod; (e) The Queen’s Sceptre with the Dove}}

{{IMG:EB1911 Regalia, Plate II, 6.jpg|THE AMPULLA}}

{{IMG:EB1911 Regalia, Plate II, 2.jpg|THE CORONATION SPOON}}

{{IMG:EB1911 Regalia, Plate II, 3.jpg|THE HEAD OF THE ROYAL SCEPTRE with the largest of the “Star of Africa” (Cullinan) Diamonds. Photo, W. E. Gray}}

{{IMG:EB1911 Regalia, Plate II, 4.jpg|THE SWORDS: (a) The Spiritual Sword of Justice; (b) The Sword of State; (c) The Temporal Sword of Justice. Photo, W. E. Gray}}

{{IMG:EB1911 Regalia, Plate II, 5.jpg|THE BRACELETS}}

{{IMG:EB1911 Regalia, Plate II, 7.jpg|THE St GEORGE’S SPURS}}
```

### Current body
```
Plate II.

{{IMG:EB1911 Regalia, Plate II, 1.jpg|THE SCEPTRES: (a) The Scepter with the Dove; (b) The Royal Sceptre with the Cross (Cf. Fig. 3); (c) The Queen’s Sceptre with the Cross; (d) The Queen’s Ivory Rod; (e) The Queen’s Sceptre with the Dove}}

{{IMG:EB1911 Regalia, Plate II, 6.jpg|THE AMPULLA}}

{{IMG:EB1911 Regalia, Plate II, 2.jpg|THE CORONATION SPOON}}

{{IMG:EB1911 Regalia, Plate II, 3.jpg|THE HEAD OF THE ROYAL SCEPTRE with the largest of the “Star of Africa” (Cullinan) Diamonds. Photo, W. E. Gray}}

{{IMG:EB1911 Regalia, Plate II, 4.jpg|THE SWORDS: (a) The Spiritual Sword of Justice; (b) The Sword of State; (c) The Temporal Sword of Justice. Photo, W. E. Gray}}

{{IMG:EB1911 Regalia, Plate II, 5.jpg|THE BRACELETS}}

{{IMG:EB1911 Regalia, Plate II, 7.jpg|THE St GEORGE’S SPURS}}
```

---

## REGALIA — vol 23

**Article ID:** 4241895  
**Signature:** `wikitable depth=3 wt=multi ht=0 has_colspan`

### Source excerpt
```
{| {{ts|mc|fs085|lh110}} width=815px
| {{ts|ar}} colspan="3" | {{sc|Plate}} III.
|-
| {{ts|ac}} |
{|
|-
| {{ts|ac}} |
{| {{ts|ba|bc}}
|{{ts|padding:1px}}| [[Image:EB1911 Regalia, Plate III, 1.jpg|350px]]
|}
|-
| {{ts|ac}} | 1.—{{uc|The Silver-Gilt Christening Font}}, made for Charles II.
|-
| &nbsp;
|-
|
{| {{ts|ba|bc}}
|{{ts|ac|padding:1px}}| [[Image:EB1911 Regalia, Plate III, 3.jpg|350px]]
|}
|-
| {{ts|ac}} | 3.—{{uc|Silver-Gilt Altar Dish}}, used at Christmas and Easter in the Chapel of Peter ad Vincula, Tower of London. ||
|}
| &emsp; || {{ts|ac}} |
{|
|- {{ts|vtp}}
| {{ts|ac}} |
{| {{ts|mc|ba|bc}}
|{{ts|ac|padding:1px}}| [[Image:EB1911 Regalia, Plate III, 2.jpg|250px]]
|}
|-
| {{ts|ac}} | 2.—{{uc|Queen Elizabeth’s Salt-Cellar.}}
|-
| &nbsp;
|-
| {{ts|ac}} |
{| {{ts|ba|bc}}
|{{ts|padding:1px}}| [[Image:EB1911 Regalia, Plate III, 4.jpg|410px]]
|}
|- {{ts|vtp}}
| {{ts|ac}} | 4.—THE GOLD SALT-CELLAR presented to the Crown by the City of Exeter.
|}
|-
| colspan="3" | &nbsp;
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **10** | **10** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'Plate III.' | 'Plate III.' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
Plate III.

{{IMG:EB1911 Regalia, Plate III, 1.jpg|THE SILVER-GILT CHRISTENING FONT , made for Charles II}}

{{IMG:EB1911 Regalia, Plate III, 3.jpg|SILVER-GILT ALTAR DISH , used at Christmas and Easter in the Chapel of Peter ad Vincula, Tower of London}}

{{IMG:EB1911 Regalia, Plate III, 2.jpg|QUEEN ELIZABETH’S SALT-CELLAR}}

{{IMG:EB1911 Regalia, Plate III, 4.jpg|THE GOLD SALT-CELLAR presented to the Crown by the City of Exeter}}
```

### Current body
```
Plate III.

{{IMG:EB1911 Regalia, Plate III, 1.jpg|THE SILVER-GILT CHRISTENING FONT , made for Charles II}}

{{IMG:EB1911 Regalia, Plate III, 3.jpg|SILVER-GILT ALTAR DISH , used at Christmas and Easter in the Chapel of Peter ad Vincula, Tower of London}}

{{IMG:EB1911 Regalia, Plate III, 2.jpg|QUEEN ELIZABETH’S SALT-CELLAR}}

{{IMG:EB1911 Regalia, Plate III, 4.jpg|THE GOLD SALT-CELLAR presented to the Crown by the City of Exeter}}
```

---

## REGALIA — vol 23

**Article ID:** 4241896  
**Signature:** `wikitable depth=1 wt=1 ht=0 has_colspan`

### Source excerpt
```
{| {{ts|mc|fs083|lh110}}
| colspan=3 {{Ts|ar}}|{{sc|Plate IV.}}
|-
|[[Image:EB1911 Regalia, Plate IV, 1.jpg|520px]] || {{gap}}
|[[Image:EB1911 Regalia, Plate IV, 2.jpg|525px]]
|-
| {{ts|ac}} |1.—{{uc|Silver-Gilt Altar Dish}} dated 1660, with representation of the Last Supper; it forms part of<br>the Altar plate at the Coronation and is in the custody of the Chapels Royal. ||
| {{ts|ac}}|2.—{{uc|The Wine Fountain State Crown}}, presented to Charles II. by the Corporation of Plymouth.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Regalia, Plate IV, 1.jpg|SILVER-GILT ALTAR DISH dated 1660, with representation of the Last Supper; it forms part of the Altar plate at the Coronation and is in the custody of the Chapels Royal}}

{{IMG:EB1911 Regalia, Plate IV, 2.jpg|THE WINE FOUNTAIN STATE CROWN , presented to Charles II. by the Corporation of Plymouth}}
```

### Current body
```
{{IMG:EB1911 Regalia, Plate IV, 1.jpg|SILVER-GILT ALTAR DISH dated 1660, with representation of the Last Supper; it forms part of the Altar plate at the Coronation and is in the custody of the Chapels Royal}}

{{IMG:EB1911 Regalia, Plate IV, 2.jpg|THE WINE FOUNTAIN STATE CROWN , presented to Charles II. by the Corporation of Plymouth}}
```

---

## ROMAN ART — vol 23

**Article ID:** 4242514  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{{right|{{sc|Plate I.}}}}{{EB1911 fine print/s}}
{|align="center" cellpadding="0" cellspacing="0"
|[[Image:EB1911 Roman Art - Domitius Ahenobarbus.jpg|x300px]]
|{{gap}}
|[[Image:EB1911 Roman Art - Scipio Africanus.jpg|x300px]]
|{{gap}}
|[[Image:EB1911 Roman Art - Unknown Woman.jpg|x300px]]
|-style="font-size: 80%"
|''Photo, Alinari.''
|
|''Photo, Anderson.''
|
|''Photo, Alinari.''
|-valign="top"
|align="center"|{{nowrap|{{sc|Fig.}} 1.—DOMITIUS AHENOBARBUS}}<br>(SO CALLED).
|
|align="center"|{{sc|Fig.}} 2.—SCIPIO AFRICANUS<br>(SO CALLED).
|
|align="center"|{{nowrap|{{sc|Fig.}} 3.—UNKNOWN WOMAN.}}
|-
|&nbsp;
|-
|[[Image:EB1911 Roman Art - Vespasian.jpg|x300px]]
|
|[[Image:EB1911 Roman Art - Unknown Physician.jpg|x300px]]
|
|[[Image:EB1911 Roman Art - Antinoüs.jpg|x300px]]
|-style="font-size: 80%"
|''Photo, Alinari.''
|
|''Photo, F. Bruckmann, Munich.''
|
|''Photo, Giraudon.''
|-valign="top"
|align="center"|{{sc|Fig.}} 4.—VESPASIAN.
|
|align="center"|{{nowrap|{{sc|Fig.}} 5.—UNKNOWN PHYSICIAN.}}
|
|align="center"|{{sc|Fig.}} 6.—ANTINOÜS.
|-
|&nbsp;
|-
|[[Image:EB1911 Roman Art - Unknown Roman.jpg|x300px]]
|
|[[Image:EB1911 Roman Art - Gallienus.jpg|x300px]]
|
|[[Image:EB1911 Roman Art - Unknown Man (4th Century).jpg|x300px]]
|-style="font-size: 80%"
|''Photo, F. Bruckmann, Munich.''
|
|''Photo, Giraudon.''
|
|''Photo, F. Bruckmann, Munich.''
|-valign="top"
|align="center"|{{sc|Fig.}} 7.—UNKNOWN ROMAN.
|
|align="center"|{{sc|Fig.}} 8.—GALLIENUS.
|
|align="center"|{{sc|Fig.}} 9.—UN
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 9 | 9 |
| captioned       | 9 | 9 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **20** | **20** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'Plate I' | 'Plate I' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
Plate I

{{IMG:EB1911 Roman Art - Domitius Ahenobarbus.jpg|DOMITIUS AHENOBARBUS (SO CALLED) (Photo, Alinari)}}

{{IMG:EB1911 Roman Art - Scipio Africanus.jpg|SCIPIO AFRICANUS (SO CALLED) (Photo, Anderson)}}

{{IMG:EB1911 Roman Art - Unknown Woman.jpg|UNKNOWN WOMAN (Photo, Alinari)}}

{{IMG:EB1911 Roman Art - Vespasian.jpg|VESPASIAN (Photo, Alinari)}}

{{IMG:EB1911 Roman Art - Unknown Physician.jpg|UNKNOWN PHYSICIAN (Photo, F. Bruckmann, Munich)}}

{{IMG:EB1911 Roman Art - Antinoüs.jpg|ANTINOÜS (Photo, Giraudon)}}

{{IMG:EB1911 Roman Art - Unknown Roman.jpg|UNKNOWN ROMAN (Photo, F. Bruckmann, Munich)}}

{{IMG:EB1911 Roman Art - Gallienus.jpg|GALLIENUS (Photo, Giraudon)}}

{{IMG:EB1911 Roman Art - Unknown Man (4th Century).jpg|UNKNOWN MAN (4th Century ) (Photo, F. Bruckmann, Munich)}}
```

### Current body
```
Plate I

{{IMG:EB1911 Roman Art - Domitius Ahenobarbus.jpg|DOMITIUS AHENOBARBUS (SO CALLED) (Photo, Alinari)}}

{{IMG:EB1911 Roman Art - Scipio Africanus.jpg|SCIPIO AFRICANUS (SO CALLED) (Photo, Anderson)}}

{{IMG:EB1911 Roman Art - Unknown Woman.jpg|UNKNOWN WOMAN (Photo, Alinari)}}

{{IMG:EB1911 Roman Art - Vespasian.jpg|VESPASIAN (Photo, Alinari)}}

{{IMG:EB1911 Roman Art - Unknown Physician.jpg|UNKNOWN PHYSICIAN (Photo, F. Bruckmann, Munich)}}

{{IMG:EB1911 Roman Art - Antinoüs.jpg|ANTINOÜS (Photo, Giraudon)}}

{{IMG:EB1911 Roman Art - Unknown Roman.jpg|UNKNOWN ROMAN (Photo, F. Bruckmann, Munich)}}

{{IMG:EB1911 Roman Art - Gallienus.jpg|GALLIENUS (Photo, Giraudon)}}

{{IMG:EB1911 Roman Art - Unknown Man (4th Century).jpg|UNKNOWN MAN (4th Century ) (Photo, F. Bruckmann, Munich)}}
```

---

## ROMAN ART — vol 23

**Article ID:** 4242515  
**Signature:** `wikitable depth=2 wt=multi ht=0 has_colspan`

### Source excerpt
```
{{right|{{sc|Plate II.}}}}{{EB1911 fine print/s}}
{|align="center" cellpadding="0" cellspacing="0"
|
{|align="center" cellpadding="0" cellspacing="0"
|[[Image:EB1911 Roman Art - Altar of Domitius Ahenobarbus.jpg|x260px]]
|-style="font-size: 80%"
|''Photo, Giraudon.''
|-
|align="center"|{{sc|Fig.}} 10.—ALTAR OF DOMITIUS AHENOBARBUS.
|}
|-
|&nbsp;
|-
|
{|align="center" cellpadding="0" cellspacing="0"
|[[Image:EB1911 Roman Art - Augustus and the Royal Family.jpg|x390px]]
|{{gap}}
|[[Image:EB1911 Roman Art - Claudius and Family.jpg|x390px]]
|{{gap}}
|[[Image:EB1911 Roman Art - Earth Goddess and the Spirits of Air and Water.jpg|x390px]]
|-
|align="center"|AUGUSTUS AND THE ROYAL FAMILY.
|
|align="center"|CLAUDIUS AND FAMILY.
|
|align="center"|THE EARTH GODDESS AND THE SPIRITS OF AIR AND WATER.
|-
|align="center" colspan="5"|{{sc|Figs.}} 11-13.—PORTIONS OF THE DECORATION OF THE ARA PACIS AUGUSTAE.
|-style="font-size: 80%"
|align="center" colspan="5"|''By permission of the Italian Ministry of Public Instruction.''
|}
|-
|&nbsp;
|-
|
{|align="center" cellpadding="0" cellspacing="0"
|[[Image:EB1911 Roman Art - Relief from the Arch of Titus.jpg|x390px]]
|{{gap}}
|[[Image:EB1911 Roman Art - Pilaster.jpg|x390px|center]]
|{{gap}}
|[[Image:EB1911 Roman Art - Relief from the Arch of Constantine.jpg|x390px]]
|-style="font-size: 80%"
|''By permission of the Italian Ministry of Public Instruction.''
|
|''Photo, Moscioni.''
|
|''By permission of the Italian Ministry of Public Instruction.''
|-va
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 7 | 7 |
| captioned       | 7 | 7 |
| legends         | 2 | 2 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **18** | **18** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'Plate II' | 'Plate II' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
Plate II

{{IMG:EB1911 Roman Art - Altar of Domitius Ahenobarbus.jpg|ALTAR OF DOMITIUS AHENOBARBUS}}

{{IMG:EB1911 Roman Art - Augustus and the Royal Family.jpg|AUGUSTUS AND THE ROYAL FAMILY}}

{{IMG:EB1911 Roman Art - Claudius and Family.jpg|CLAUDIUS AND FAMILY}}

{{IMG:EB1911 Roman Art - Earth Goddess and the Spirits of Air and Water.jpg|THE EARTH GODDESS AND THE SPIRITS OF AIR AND WATER}}

{{IMG:EB1911 Roman Art - Relief from the Arch of Titus.jpg|RELIEF FROM THE ARCH OF TITUS: TRIUMPH OF TITUS AND THE SPOILS OF JERUSALEM}}

{{IMG:EB1911 Roman Art - Pilaster.jpg|PILASTER}}

{{IMG:EB1911 Roman Art - Relief from the Arch of Constantine.jpg|RELIEF FROM THE ARCH OF CONSTANTINE: ROMAN CAVALRY CHARGE}}

{{LEGEND:Figs. 11-13.—PORTIONS OF THE DECORATION OF THE ARA PACIS AUGUSTAE}LEGEND}

{{LEGEND:By permission of the Italian Ministry of Public Instruction}LEGEND}
```

### Current body
```
Plate II

{{IMG:EB1911 Roman Art - Altar of Domitius Ahenobarbus.jpg|ALTAR OF DOMITIUS AHENOBARBUS}}

{{IMG:EB1911 Roman Art - Augustus and the Royal Family.jpg|AUGUSTUS AND THE ROYAL FAMILY}}

{{IMG:EB1911 Roman Art - Claudius and Family.jpg|CLAUDIUS AND FAMILY}}

{{IMG:EB1911 Roman Art - Earth Goddess and the Spirits of Air and Water.jpg|THE EARTH GODDESS AND THE SPIRITS OF AIR AND WATER}}

{{IMG:EB1911 Roman Art - Relief from the Arch of Titus.jpg|RELIEF FROM THE ARCH OF TITUS: TRIUMPH OF TITUS AND THE SPOILS OF JERUSALEM}}

{{IMG:EB1911 Roman Art - Pilaster.jpg|PILASTER}}

{{IMG:EB1911 Roman Art - Relief from the Arch of Constantine.jpg|RELIEF FROM THE ARCH OF CONSTANTINE: ROMAN CAVALRY CHARGE}}

{{LEGEND:Figs. 11-13.—PORTIONS OF THE DECORATION OF THE ARA PACIS AUGUSTAE}LEGEND}

{{LEGEND:By permission of the Italian Ministry of Public Instruction}LEGEND}
```

---

## ROMAN ART — vol 23

**Article ID:** 4242516  
**Signature:** `wikitable depth=1 wt=1 ht=0 has_colspan`

### Source excerpt
```
{{sc|Plate III.}}{{EB1911 fine print/s}}
{|align="center" cellpadding="0" cellspacing="0"
|[[Image:EB1911 Roman Art - Caesar Augustus.jpg|x600px]]
|{{gap}}
|[[Image:EB1911 Roman Art - Medallion, Arch of Constantine.jpg|x600px]]
|-style="font-size: 80%"
|''Photo, Anderson.''
|
|''Photo, Anderson.''
|-valign="top"
|align="center"|{{sc|Fig.}} 17.—CAESAR AUGUSTUS.
|
|align="center"|{{sc|Fig.}} 18.—MEDALLION, ARCH OF CONSTANTINE.
|-
|&nbsp;
|-
|colspan="3"|[[Image:EB1911 Roman Art - Constantine Distributing a Dole.jpg|x265px]]
|-style="font-size: 80%"
|''Photo, Anderson.''
|-
|colspan="3" align="center"|CONSTANTINE DISTRIBUTING A DOLE.
|-
|&nbsp;
|-
|colspan="3"|[[Image:EB1911 Roman Art - Constantine on the Rostrum.jpg|x265px]]
|-style="font-size: 80%"
|''Photo, Anderson.''
|-
|colspan="3" align="center"|CONSTANTINE ON THE ROSTRUM.
|-
|colspan="3" align="center"|{{sc|Fig.}} 19.—BAS-RELIEFS ON THE ARCH OF CONSTANTINE.
|}
{{EB1911 fine print/e}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **11** | **11** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'Plate III' | 'Plate III' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
Plate III

{{IMG:EB1911 Roman Art - Caesar Augustus.jpg|CAESAR AUGUSTUS}}

{{IMG:EB1911 Roman Art - Medallion, Arch of Constantine.jpg|MEDALLION, ARCH OF CONSTANTINE}}

{{IMG:EB1911 Roman Art - Constantine Distributing a Dole.jpg|BAS-RELIEFS ON THE ARCH OF CONSTANTINE}}

{{IMG:EB1911 Roman Art - Constantine on the Rostrum.jpg|Photo, Anderson}}

{{LEGEND:CONSTANTINE DISTRIBUTING A DOLE}LEGEND}
```

### Current body
```
Plate III

{{IMG:EB1911 Roman Art - Caesar Augustus.jpg|CAESAR AUGUSTUS}}

{{IMG:EB1911 Roman Art - Medallion, Arch of Constantine.jpg|MEDALLION, ARCH OF CONSTANTINE}}

{{IMG:EB1911 Roman Art - Constantine Distributing a Dole.jpg|BAS-RELIEFS ON THE ARCH OF CONSTANTINE}}

{{IMG:EB1911 Roman Art - Constantine on the Rostrum.jpg|Photo, Anderson}}

{{LEGEND:CONSTANTINE DISTRIBUTING A DOLE}LEGEND}
```

---

## ROMAN ART — vol 23

**Article ID:** 4242517  
**Signature:** `wikitable depth=2 wt=multi ht=0`

### Source excerpt
```
{{right|{{sc|Plate IV.}}}}
{{EB1911 fine print/s}}
{|align="center" cellpadding="0" cellspacing="0"
|align="center"|
{|cellpadding="0" cellspacing="0"
|[[Image:EB1911 Roman Art - Presentation of Caracalla.jpg|x450px]]
|-style="font-size: 80%"
|''By permission of the British School of Rome.''
|-
|align="center"|{{sc|Fig.}} 20.—PRESENTATION OF CARACALLA TO THE SENATE.
|}
|-
|&nbsp;
|-
|align="center"|
{|cellpadding="0" cellspacing="0"
|[[Image:EB1911 Roman Art - Base of Column of Antoninus (1).jpg|x300px]]
|{{gap}}
|[[Image:EB1911 Roman Art - Base of Column of Antoninus (2).jpg|x300px]]
|-style="font-size: 80%"
|''Photo, Moscioni.''
|
|''Photo, Moscioni.''
|-
|align="center"|{{sc|Fig.}} 21.—BASE OF COLUMN OF ANTONINUS.
|
|align="center"|{{sc|Fig.}} 22.—BASE OF COLUMN OF ANTONINUS.
|}
|-
|&nbsp;
|-
|align="center"|
{|cellpadding="0" cellspacing="0"
|[[Image:EB1911 Roman Art - Mêlée of Romans and Orientals.jpg|x300px]]
|{{gap}}
|[[Image:EB1911 Roman Art - Detail of the Column of Antoninus.jpg|x300px]]
|-style="font-size: 80%"
|''By permission of the Italian Ministry of Public Instruction.''
|
|''Photo, Anderson.''
|-
|align="center"|{{sc|Fig.}} 23.—MÊLÉE OF ROMANS AND ORIENTALS,<br>FROM A SARCOPHAGUS.
|
|align="center"|{{sc|Fig.}} 24.—DETAIL OF THE<br>COLUMN OF ANTONINUS.
|}
|}
{{EB1911 fine print/e}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 5 | 5 |
| captioned       | 5 | 5 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **12** | **12** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'Plate IV.' | 'Plate IV.' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
Plate IV.

{{IMG:EB1911 Roman Art - Presentation of Caracalla.jpg|PRESENTATION OF CARACALLA TO THE SENATE (By permission of the British School of Rome)}}

{{IMG:EB1911 Roman Art - Base of Column of Antoninus (1).jpg|BASE OF COLUMN OF ANTONINUS (Photo, Moscioni)}}

{{IMG:EB1911 Roman Art - Base of Column of Antoninus (2).jpg|BASE OF COLUMN OF ANTONINUS (Photo, Moscioni)}}

{{IMG:EB1911 Roman Art - Mêlée of Romans and Orientals.jpg|MÊLÉE OF ROMANS AND ORIENTALS, FROM A SARCOPHAGUS (By permission of the Italian Ministry of Public Instruction)}}

{{IMG:EB1911 Roman Art - Detail of the Column of Antoninus.jpg|DETAIL OF THE COLUMN OF ANTONINUS (Photo, Anderson)}}
```

### Current body
```
Plate IV.

{{IMG:EB1911 Roman Art - Presentation of Caracalla.jpg|PRESENTATION OF CARACALLA TO THE SENATE (By permission of the British School of Rome)}}

{{IMG:EB1911 Roman Art - Base of Column of Antoninus (1).jpg|BASE OF COLUMN OF ANTONINUS (Photo, Moscioni)}}

{{IMG:EB1911 Roman Art - Base of Column of Antoninus (2).jpg|BASE OF COLUMN OF ANTONINUS (Photo, Moscioni)}}

{{IMG:EB1911 Roman Art - Mêlée of Romans and Orientals.jpg|MÊLÉE OF ROMANS AND ORIENTALS, FROM A SARCOPHAGUS (By permission of the Italian Ministry of Public Instruction)}}

{{IMG:EB1911 Roman Art - Detail of the Column of Antoninus.jpg|DETAIL OF THE COLUMN OF ANTONINUS (Photo, Anderson)}}
```

---

## ROMAN ART — vol 23

**Article ID:** 4242518  
**Signature:** `wikitable depth=2 wt=multi ht=0`

### Source excerpt
```
{{sc|Plate V.}}{{EB1911 fine print/s}}
{|align="center" cellpadding="0" cellspacing="0"
|align="center"|
{|cellpadding="0" cellspacing="0"
|[[Image:EB1911 Roman Art - Mosaic showing cloud and sky effects.jpg|x250px]]
|-style="font-size: 80%"
|From Richer & Taylor's ''Golden Age of Classic Christian Art'', by permission of the authors and Duckworth & Co.
|-
|align="center"|{{sc|Fig.}} 25.—MOSAIC, SHOWING CLOUD AND SKY EFFECTS.
|}
|-
|&nbsp;
|-
|align="center"|
{|cellpadding="0" cellspacing="0"
|[[Image:EB1911 Roman Art - Odysseus among the Shades.jpg|x450px]]
|{{gap}}
|[[Image:EB1911 Roman Art - Evening Benediction (fresco).jpg|x450px]]
|-style="font-size: 80%"
|''Photo, Sansaini.''
|
|''Photo, Brogi.''
|-
|align="center"|{{sc|Fig.}} 26.—FRESCO: ODYSSEUS AMONG<br>THE SHADES.
|
|align="center"|{{sc|Fig.}} 27.—FRESCO FROM POMPEII:  EVENING BENEDICTION<br>IN FRONT OF THE TEMPLE OF ISIS.
|}
|-
|&nbsp;
|-
|align="center"|
{|cellpadding="0" cellspacing="0"
|[[Image:EB1911 Roman Art - Marriage of Aldobrandini (fresco).jpg|x225px]]
|-style="font-size: 80%"
|''Photo, Anderson.''
|-
|align="center"|{{sc|Fig.}} 28.—FRESCO:  THE MARRIAGE OF ALDOBRANDINI.
|}
|}
{{EB1911 fine print/e}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **11** | **11** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'Plate V.' | 'Plate V.' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
Plate V.

{{IMG:EB1911 Roman Art - Mosaic showing cloud and sky effects.jpg|From Richer & Taylor's Golden Age of Classic Christian Art, by permission of the authors and Duckworth & Co}}

{{IMG:EB1911 Roman Art - Odysseus among the Shades.jpg|FRESCO: ODYSSEUS AMONG THE SHADES}}

{{IMG:EB1911 Roman Art - Evening Benediction (fresco).jpg|FRESCO FROM POMPEII: EVENING BENEDICTION IN FRONT OF THE TEMPLE OF ISIS}}

{{IMG:EB1911 Roman Art - Marriage of Aldobrandini (fresco).jpg|FRESCO: THE MARRIAGE OF ALDOBRANDINI}}

{{LEGEND:MOSAIC, SHOWING CLOUD AND SKY EFFECTS}LEGEND}
```

### Current body
```
Plate V.

{{IMG:EB1911 Roman Art - Mosaic showing cloud and sky effects.jpg|From Richer & Taylor's Golden Age of Classic Christian Art, by permission of the authors and Duckworth & Co}}

{{IMG:EB1911 Roman Art - Odysseus among the Shades.jpg|FRESCO: ODYSSEUS AMONG THE SHADES}}

{{IMG:EB1911 Roman Art - Evening Benediction (fresco).jpg|FRESCO FROM POMPEII: EVENING BENEDICTION IN FRONT OF THE TEMPLE OF ISIS}}

{{IMG:EB1911 Roman Art - Marriage of Aldobrandini (fresco).jpg|FRESCO: THE MARRIAGE OF ALDOBRANDINI}}

{{LEGEND:MOSAIC, SHOWING CLOUD AND SKY EFFECTS}LEGEND}
```

---

## ROMAN ART — vol 23

**Article ID:** 4242519  
**Signature:** `wikitable depth=2 wt=multi ht=0 has_colspan`

### Source excerpt
```
{{right|{{sc|Plate VI.}}}}
{{EB1911 fine print/s}}
{|align="center" cellpadding="0" cellspacing="0"
|colspan="3" align="center"|
{|cellpadding="0" cellspacing="0"
|[[Image:EB1911 Roman Art - Mosaic Pavement.jpg|x600px]]
|-style="font-size: 80%"
|''By permission of the Italian Ministry of Public Instruction.''
|-
|align="center"|{{sc|Fig.}} 29.—MOSAIC PAVEMENT (MUSEO DELLE TERME).
|}
|-
|&nbsp;
|-valign="bottom"
|[[Image:EB1911 Roman Art - Medea.jpg|x490px]]
|{{gap|4em}}
|[[Image:EB1911 Roman Art - Virgil Mosaic.jpg|x500px]]
|-style="font-size: 80%"
|''Photo, Brogi.''
|
|From Piot's ''Monuments'', by permission of Ernest Leroux
|-
|align="center"|{{sc|Fig.}} 30.—MEDEA.
|
|align="center"|{{sc|Fig.}} 31.—THE VIRGIL MOSAIC.
|}
{{EB1911 fine print/e}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'Plate VI.' | 'Plate VI.' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
Plate VI.

{{IMG:EB1911 Roman Art - Mosaic Pavement.jpg|MOSAIC PAVEMENT (MUSEO DELLE TERME)}}

{{IMG:EB1911 Roman Art - Medea.jpg|From Piot's Monuments, by permission of Ernest Leroux}}

{{IMG:EB1911 Roman Art - Virgil Mosaic.jpg|MEDEA}}
```

### Current body
```
Plate VI.

{{IMG:EB1911 Roman Art - Mosaic Pavement.jpg|MOSAIC PAVEMENT (MUSEO DELLE TERME)}}

{{IMG:EB1911 Roman Art - Medea.jpg|From Piot's Monuments, by permission of Ernest Leroux}}

{{IMG:EB1911 Roman Art - Virgil Mosaic.jpg|MEDEA}}
```

---

## ROMAN ART — vol 23

**Article ID:** 4242520  
**Signature:** `wikitable depth=2 wt=multi ht=0 has_colspan`

### Source excerpt
```
{{sc|Plate VII.}}{{EB1911 fine print/s}}
{|align="center"
|[[Image:EB1911 Roman Art - Baron Rothschild Cup (1).jpg|x600px]]
|rowspan="2"|
{|align="center" cellpadding="0" cellspacing="0"
|[[Image:EB1911 Roman Art - Cup Decorated with Sprays of Olive.jpg|x225px]]
|-style="font-size: 80%"
|''Photo, Giraudon.''
|-
|align="center"|{{sc|Fig.}} 32.—CUP DECORATED<br>WITH SPRAYS OF OLIVE.
|}
|[[Image:EB1911 Roman Art - Baron Rothschild Cup (2).jpg|x600px]]
|-
|align="center"|{{sc|Fig.}} 33.—CUP IN THE BARON<br>ROTHSCHILD COLLECTION.
|align="center"|{{sc|Fig.}} 34.—CUP IN THE BARON<br>ROTHSCHILD COLLECTION.
|-
|align="center" valign="bottom" style="font-size: 80%"|''Photo'',<br>''Giraudon''.
|rowspan="2"|[[Image:EB1911 Roman Art - Silver Bowl (Louvre).jpg|x500px]]
|rowspan="2" align="center"|''EMBLEMA'', IN HIGH<br>RELIEF, PERSONIFICATION<br>OF THE PROVINCE OF AFRICA.
|-
|align="center" valign="top"|{{sc|Fig.}} 35.—SILVER<br>BOWL (LOUVRE).
|-
|align="center" colspan="3"|
{|
|[[Image:EB1911 Roman Art - Gemma Augustea.jpg|x600px]]
|[[Image:EB1911 Roman Art - Grand Camée de France.jpg|x600px]]
|-
|align="center"|{{sc|Fig.}} 36.—THE “GEMMA AUGUSTEA.”
|align="center"|{{sc|Fig.}} 37.—THE “GRAND CAMÉE DE FRANCE.”
|-style="font-size: 80%"
|
|From Furtwängler, ''Die Antiken Gemmen'', by permission of Gieseke and Devrient.
|}
|}
{{EB1911 fine print/e}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 6 | 6 |
| captioned       | 6 | 6 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **15** | **15** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'Plate VII' | 'Plate VII' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
Plate VII

{{IMG:EB1911 Roman Art - Baron Rothschild Cup (1).jpg|CUP DECORATED WITH SPRAYS OF OLIVE}}

{{IMG:EB1911 Roman Art - Cup Decorated with Sprays of Olive.jpg|CUP IN THE BARON ROTHSCHILD COLLECTION}}

{{IMG:EB1911 Roman Art - Baron Rothschild Cup (2).jpg|CUP IN THE BARON ROTHSCHILD COLLECTION}}

{{IMG:EB1911 Roman Art - Silver Bowl (Louvre).jpg|EMBLEMA, IN HIGH RELIEF, PERSONIFICATION OF THE PROVINCE OF AFRICA}}

{{IMG:EB1911 Roman Art - Gemma Augustea.jpg|THE “GEMMA AUGUSTEA.”}}

{{IMG:EB1911 Roman Art - Grand Camée de France.jpg|THE “GRAND CAMÉE DE FRANCE.”}}

{{LEGEND:From Furtwängler, Die Antiken Gemmen, by permission of Gieseke and Devrient}LEGEND}
```

### Current body
```
Plate VII

{{IMG:EB1911 Roman Art - Baron Rothschild Cup (1).jpg|CUP DECORATED WITH SPRAYS OF OLIVE}}

{{IMG:EB1911 Roman Art - Cup Decorated with Sprays of Olive.jpg|CUP IN THE BARON ROTHSCHILD COLLECTION}}

{{IMG:EB1911 Roman Art - Baron Rothschild Cup (2).jpg|CUP IN THE BARON ROTHSCHILD COLLECTION}}

{{IMG:EB1911 Roman Art - Silver Bowl (Louvre).jpg|EMBLEMA, IN HIGH RELIEF, PERSONIFICATION OF THE PROVINCE OF AFRICA}}

{{IMG:EB1911 Roman Art - Gemma Augustea.jpg|THE “GEMMA AUGUSTEA.”}}

{{IMG:EB1911 Roman Art - Grand Camée de France.jpg|THE “GRAND CAMÉE DE FRANCE.”}}

{{LEGEND:From Furtwängler, Die Antiken Gemmen, by permission of Gieseke and Devrient}LEGEND}
```

---

## ROPE AND ROPE-MAKING — vol 23

**Article ID:** 4242576  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{{nop}}
{{EB1911 fine print/s}}

{| align="center" cellpadding="0" cellspacing="0"
| align="right" | {{sc|Plate I.}}
|-
| [[Image:EB1911 Rope and Rope-making, 9.jpg|600px]]
|-
| &nbsp;
|- style="font-size: 90%"
| align="center" | {{sc|Fig.}} 9.—{{uc|Rope-making, Pottinger Mill.}}
|-
| <br />&nbsp;
|-
| [[Image:EB1911 Rope and Rope-making, 10.jpg|600px]]
|-
| &nbsp;
|- style="font-size: 90%"
| align="center" | {{sc|Fig.}} 10.—{{uc|Manila rope yarn preparing, Pottinger Mill, of the Belfast Ropework Co. Ltd.}}
|}


{{EB1911 fine print/e}}
{{nop}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 2 | 2 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Rope and Rope-making, 9.jpg|ROPE-MAKING, POTTINGER MILL}}

{{IMG:EB1911 Rope and Rope-making, 10.jpg|MANILA ROPE YARN PREPARING, POTTINGER MILL, OF THE BELFAST ROPEWORK CO. LTD}}

{{LEGEND:- style="font-size: 90%"}LEGEND}

{{LEGEND:- style="font-size: 90%"}LEGEND}
```

### Current body
```
{{IMG:EB1911 Rope and Rope-making, 9.jpg|ROPE-MAKING, POTTINGER MILL}}

{{IMG:EB1911 Rope and Rope-making, 10.jpg|MANILA ROPE YARN PREPARING, POTTINGER MILL, OF THE BELFAST ROPEWORK CO. LTD}}

{{LEGEND:- style="font-size: 90%"}LEGEND}

{{LEGEND:- style="font-size: 90%"}LEGEND}
```

---

## ROPE AND ROPE-MAKING — vol 23

**Article ID:** 4242577  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{{nop}}
{{EB1911 fine print/s}}

{| align="center" cellpadding="0" cellspacing="0"
| {{sc|Plate II.}}
|-
| [[Image:EB1911 Rope and Rope-making, 11.jpg|600px]]
|- style="font-size: 90%"
| align="center" | {{sc|Fig.}} 11.—GOOD'S HACKLING AND SPREADING MACHINE.
|-
| &nbsp;
|-
| [[Image:EB1911 Rope and Rope-making, 12.jpg|600px]]
|- style="font-size: 90%"
| align="center" | {{sc|Fig.}} 12.—HEAVY SPIRAL OR SCREW-GILL DRAWING FRAME; ONE HEAD, SIX GILLS.
|-
| &nbsp;
|-
| [[Image:EB1911 Rope and Rope-making, 13.jpg|600px]]
|- style="font-size: 90%"
| align="center" | {{sc|Fig.}} 13.—SPINNER OR JENNY.
|}


{{EB1911 fine print/e}}
{{nop}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Rope and Rope-making, 11.jpg|GOOD'S HACKLING AND SPREADING MACHINE}}

{{IMG:EB1911 Rope and Rope-making, 12.jpg|HEAVY SPIRAL OR SCREW-GILL DRAWING FRAME; ONE HEAD, SIX GILLS}}

{{IMG:EB1911 Rope and Rope-making, 13.jpg|SPINNER OR JENNY}}
```

### Current body
```
{{IMG:EB1911 Rope and Rope-making, 11.jpg|GOOD'S HACKLING AND SPREADING MACHINE}}

{{IMG:EB1911 Rope and Rope-making, 12.jpg|HEAVY SPIRAL OR SCREW-GILL DRAWING FRAME; ONE HEAD, SIX GILLS}}

{{IMG:EB1911 Rope and Rope-making, 13.jpg|SPINNER OR JENNY}}
```

---

## ROPE AND ROPE-MAKING — vol 23

**Article ID:** 4242578  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{{nop}}
{{EB1911 fine print/s}}

{| align="center" cellpadding="0" cellspacing="0"
| align="right" | {{sc|Plate III.}}
|-
| [[Image:EB1911 Rope and Rope-making, 14.jpg|600px|frameless]]
|-
| &nbsp;
|- style="font-size: 90%"
| align="center" | {{sc|Fig.}} 14.—{{uc|Binder twine preparing, Connswater Mill, of the Belfast Ropework Co. Ltd.}}
|-
| &nbsp;
|-
| [[Image:EB1911 Rope and Rope-making, 15.jpg|600px|frameless]]
|-
| &nbsp;
|- style="font-size: 90%"
| align="center" | {{sc|Fig.}} 15.—{{uc|Binder twine spinning, Connswater Mill.}}
|}


{{EB1911 fine print/e}}
{{nop}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 2 | 2 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Rope and Rope-making, 14.jpg|BINDER TWINE PREPARING, CONNSWATER MILL, OF THE BELFAST ROPEWORK CO. LTD}}

{{IMG:EB1911 Rope and Rope-making, 15.jpg|BINDER TWINE SPINNING, CONNSWATER MILL}}

{{LEGEND:- style="font-size: 90%"}LEGEND}

{{LEGEND:- style="font-size: 90%"}LEGEND}
```

### Current body
```
{{IMG:EB1911 Rope and Rope-making, 14.jpg|BINDER TWINE PREPARING, CONNSWATER MILL, OF THE BELFAST ROPEWORK CO. LTD}}

{{IMG:EB1911 Rope and Rope-making, 15.jpg|BINDER TWINE SPINNING, CONNSWATER MILL}}

{{LEGEND:- style="font-size: 90%"}LEGEND}

{{LEGEND:- style="font-size: 90%"}LEGEND}
```

---

## ROPE AND ROPE-MAKING — vol 23

**Article ID:** 4242579  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{{nop}}
{{EB1911 fine print/s}}

{| align="center" cellpadding="0" cellspacing="0"
| {{sc|Plate IV.}}
|- valign="bottom"
| [[Image:EB1911 Rope and Rope-making, 16.jpg|325px]]
| align="center" rowspan="3" | [[Image:EB1911 Rope and Rope-making, 18.jpg|250px]]
|- style="font-size: 80%"
| align="center" | {{sc|Fig.}} 16.—HASKELL DAWES HORIZONTAL ROPE MACHINE.
|- valign="bottom"
| [[Image:EB1911 Rope and Rope-making, 17.jpg|325px]]
|- style="font-size: 80%"
| align="center" | {{sc|Fig.}} 17.—EIGHTING THREAD ROPE-MAKING MACHINE.
| align="center" | {{nowrap|{{sc|Fig.}} 18.—HASKELL DAWES VERTICAL ROPE MACHINE.}}
|}


{{EB1911 fine print/e}}
{{nop}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Rope and Rope-making, 16.jpg|HASKELL DAWES HORIZONTAL ROPE MACHINE}}

{{IMG:EB1911 Rope and Rope-making, 18.jpg|HASKELL DAWES VERTICAL ROPE MACHINE}}

{{IMG:EB1911 Rope and Rope-making, 17.jpg|EIGHTING THREAD ROPE-MAKING MACHINE}}
```

### Current body
```
{{IMG:EB1911 Rope and Rope-making, 16.jpg|HASKELL DAWES HORIZONTAL ROPE MACHINE}}

{{IMG:EB1911 Rope and Rope-making, 18.jpg|HASKELL DAWES VERTICAL ROPE MACHINE}}

{{IMG:EB1911 Rope and Rope-making, 17.jpg|EIGHTING THREAD ROPE-MAKING MACHINE}}
```

---

## RUBBER — vol 23

**Article ID:** 4242745  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|{{Ts|mc|ac|lh110}}
|{{Ts|ar}}|{{sc|Plate I.}}
|-
|[[File:RB1911 - Rubber - Plate 1 - Fig 11.jpg|center|810px]]
|-
|{{sc|Fig}}. 11.—PARA RUBBER PLANTATION, CEYLON.<br><br>
|-
|[[File:RB1911 - Rubber - Plate 1 - Fig 12.jpg|center|810px]]
|-
|{{sc|Fig}}. 12.—PARA RUBBER TREES, TAPPED—CEYLON.<br>(Spiral and V Systems.)
|-{{Ts|ar|fs080}}
|''From Photographs in the Collection of the Imperial Institute''.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **5** | **5** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:RB1911 - Rubber - Plate 1 - Fig 11.jpg|PARA RUBBER PLANTATION, CEYLON}}

{{IMG:RB1911 - Rubber - Plate 1 - Fig 12.jpg|PARA RUBBER TREES, TAPPED—CEYLON. (Spiral and V Systems.)}}

{{LEGEND:From Photographs in the Collection of the Imperial Institute}LEGEND}
```

### Current body
```
{{IMG:RB1911 - Rubber - Plate 1 - Fig 11.jpg|PARA RUBBER PLANTATION, CEYLON}}

{{IMG:RB1911 - Rubber - Plate 1 - Fig 12.jpg|PARA RUBBER TREES, TAPPED—CEYLON. (Spiral and V Systems.)}}

{{LEGEND:From Photographs in the Collection of the Imperial Institute}LEGEND}
```

---

## RUBBER — vol 23

**Article ID:** 4242746  
**Signature:** `wikitable depth=1 wt=1 ht=0 has_colspan`

### Source excerpt
```
{|{{Ts|mc|ac|lh110}}
|colspan=5 {{Ts|ar}}|{{sc|Plate II.}}
|-
|[[File:RB1911 - Rubber - Plate 2 - Fig 13.jpg|400px]]|| &emsp; ||[[File:RB1911 - Rubber - Plate 2 - Fig 14.jpg|400px]]
|-
|{{sc|Fig}}. 13.—CEARA RUBBER TREE. || || {{sc|Fig}}. 14.—CASTILLOA RUBBER TREES.
|-style=line-height:40%
|&nbsp;
|-
|[[File:RB1911 - Rubber - Plate 2 - Fig 15.jpg|397px]] || ||[[File:RB1911 - Rubber - Plate 2 - Fig 16.jpg|400px]]
|-
|{{sc|Fig}}. 15.—''FICUS ELASTICA''. || ||{{sc|Fig}}. 16.—''FUNTUMIA ELASTICA''.
|-
|colspan=5 {{Ts|fs080|ar}}|''From Photographs in the Collection of the Imperial Institute.''
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:RB1911 - Rubber - Plate 2 - Fig 13.jpg|CEARA RUBBER TREE. Fig . 14.—CASTILLOA RUBBER TREES}}

{{IMG:RB1911 - Rubber - Plate 2 - Fig 14.jpg|From Photographs in the Collection of the Imperial Institute}}

{{IMG:RB1911 - Rubber - Plate 2 - Fig 15.jpg|FICUS ELASTICA. Fig . 16.—FUNTUMIA ELASTICA}}

{{IMG:RB1911 - Rubber - Plate 2 - Fig 16.jpg|Plate II}}
```

### Current body
```
{{IMG:RB1911 - Rubber - Plate 2 - Fig 13.jpg|CEARA RUBBER TREE. Fig . 14.—CASTILLOA RUBBER TREES}}

{{IMG:RB1911 - Rubber - Plate 2 - Fig 14.jpg|From Photographs in the Collection of the Imperial Institute}}

{{IMG:RB1911 - Rubber - Plate 2 - Fig 15.jpg|FICUS ELASTICA. Fig . 16.—FUNTUMIA ELASTICA}}

{{IMG:RB1911 - Rubber - Plate 2 - Fig 16.jpg|Plate II}}
```

---

## PLATE (VOL. 23, P. 919) — vol 23

**Article ID:** 4242844  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|align="center" cellspacing="8"
|[[Image:EB1911 Russia - Southern Russia.jpg|800px]]
|-
|[[Image:EB1911 Russia - Caucasia.jpg|808px]]
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 0 | 0 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **2** | **2** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Russia - Southern Russia.jpg}}

{{IMG:EB1911 Russia - Caucasia.jpg}}
```

### Current body
```
{{IMG:EB1911 Russia - Southern Russia.jpg}}

{{IMG:EB1911 Russia - Caucasia.jpg}}
```

---

## SARDINIA, PLATE — vol 24

**Article ID:** 4246357  
**Signature:** `wikitable depth=1 wt=1 ht=0 toplegend`

### Source excerpt
```
[[File:EB1911 Sardinia Plate Fig 1.jpg|center|740px|Fig. 1.—NURAGHE MELAS, NEAR GUSPINI.]]
{{center|{{smaller|{{sc|Fig}}. 1.—NURAGHE MELAS, NEAR GUSPINI.}}}}


[[File:EB1911 Sardinia Plate Fig 2.jpg|center|740px|Fig. 2.—NURAGHE LOSA, NEAR ABBASANTA.]]
{{center|{{smaller|{{sc|Fig}}. 2.—NURAGHE LOSA, NEAR ABBASANTA.}}}}


{|{{ts|mc|ac|sm}}
|-
|[[File:EB1911 Sardinia Plate Fig 3.jpg|center|390px|Fig. 3.—NURAGHE MADRONE, NEAR SILANUS.]] || [[File:EB1911 Sardinia Plate Fig 4.jpg|center|390px|Fig. 4.—NURAGHE OROLO, NEAR BORDIGHALL.]]
|-
|{{sc|Fig}}. 3.—NURAGHE MADRONE, NEAR SILANUS.||{{sc|Fig}}. 4.—NURAGHE OROLO, NEAR BORDIGHALL.
|}

{{right|{{smaller|''Photos by Dr T. Ashby''.}}}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **9** | **9** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | 'Photos by Dr T. Ashby' | 'Photos by Dr T. Ashby' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Sardinia Plate Fig 1.jpg|NURAGHE MELAS, NEAR GUSPINI}}

{{IMG:EB1911 Sardinia Plate Fig 2.jpg|NURAGHE LOSA, NEAR ABBASANTA}}

{{IMG:EB1911 Sardinia Plate Fig 3.jpg|NURAGHE MADRONE, NEAR SILANUS. Fig . 4.—NURAGHE OROLO, NEAR BORDIGHALL}}

{{IMG:EB1911 Sardinia Plate Fig 4.jpg}}

Photos by Dr T. Ashby
```

### Current body
```
{{IMG:EB1911 Sardinia Plate Fig 1.jpg|NURAGHE MELAS, NEAR GUSPINI}}

{{IMG:EB1911 Sardinia Plate Fig 2.jpg|NURAGHE LOSA, NEAR ABBASANTA}}

{{IMG:EB1911 Sardinia Plate Fig 3.jpg|NURAGHE MADRONE, NEAR SILANUS. Fig . 4.—NURAGHE OROLO, NEAR BORDIGHALL}}

{{IMG:EB1911 Sardinia Plate Fig 4.jpg}}

Photos by Dr T. Ashby
```

---

## SCANDINAVIAN CIVILIZATION, PLATE I — vol 24

**Article ID:** 4246502  
**Signature:** `wikitable depth=3 wt=multi ht=0`

### Source excerpt
```
{|align="center"
|
{|width="100%"
|valign="bottom"|
{|
|[[Image:EB1911 Scandinavian Civilization - stone axe.jpg|border|220px]]
|-
|align="center" width="220"|{{EB1911 Fine Print|1.—STONE AXE, Later Stone Age, Sweden.}}
|}
|&nbsp;
|
{|
|[[Image:Scandinavian Civilization - women's ornaments.jpg|border|250px]]
|-
|align="center" width="250"|{{EB1911 Fine Print|2.—WOMEN'S ORNAMENTS. Early Bronze Age.}}
|-
|&nbsp;
|-
|[[Image:EB1911 Scandinavian Civilization - belt ornament.jpg|border|250px]]
|-
|align="center" width="250"|{{EB1911 Fine Print|3.—BELT ORNAMENT. Latter part of earlier Bronze Age.}}
|}
|&nbsp;
|
{|
|[[Image:Scandinavian Civilization - sun chariot.jpg|border|300px]]
|-
|align="center" width="300"|{{EB1911 Fine Print|4.—SUN CHARIOT. Older Bronze Age, Denmark.}}
|-
|&nbsp;
|-
|[[Image:Scandinavian Civilization - sword.jpg|border|300px]]
|-
|align="center" width="300"|{{EB1911 Fine Print|5.—SWORD. Second period of earlier Bronze Age.}}
|}
|}
|-
|
{|width="100%"
|
{|
|[[Image:Scandinavian Civilization - bronze casket top.jpg|border|150px]]
|-
|align="center" width="150"|{{EB1911 Fine Print|6.—TOP OF A SMALL BRONZE CASKET. Latter part of earlier Bronze Age.}}
|}
|&nbsp;
|
{|
|[[Image:Scandinavian Civilization - fibulæ.jpg|border|300px]]
|-
|align="center" width="300"|{{EB1911 Fine Print|7.—FIBULÆ. Earlier and later forms, Bronze Age, Norway.}}
|}
|&nbsp;
|
{|
|[[Image:Scandinavian Civilization - bronze knives or razors.jpg|border|250px]]
|-
|align="center" width="250"|{{E
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 12 | 12 |
| captioned       | 12 | 12 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 1 | 1 |
| **matter**      | **26** | **26** |
| **penalty**     | **1** | **1** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | 'Fig. 1 from O. Montelius, Civilization of Sweden; Figs. 2-6, 10, 11 from S. Müller, Vor Oldtid and Urgeschichte Europas;' | 'Fig. 1 from O. Montelius, Civilization of Sweden; Figs. 2-6, 10, 11 from S. Müller, Vor Oldtid and Urgeschichte Europas;' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Scandinavian Civilization - stone axe.jpg|STONE AXE, Later Stone Age, Sweden}}

{{IMG:Scandinavian Civilization - women's ornaments.jpg|WOMEN'S ORNAMENTS. Early Bronze Age}}

{{IMG:EB1911 Scandinavian Civilization - belt ornament.jpg|BELT ORNAMENT. Latter part of earlier Bronze Age}}

{{IMG:Scandinavian Civilization - sun chariot.jpg|SUN CHARIOT. Older Bronze Age, Denmark}}

{{IMG:Scandinavian Civilization - sword.jpg|SWORD. Second period of earlier Bronze Age}}

{{IMG:Scandinavian Civilization - bronze casket top.jpg|TOP OF A SMALL BRONZE CASKET. Latter part of earlier Bronze Age}}

{{IMG:Scandinavian Civilization - fibulæ.jpg|FIBULÆ. Earlier and later forms, Bronze Age, Norway}}

{{IMG:Scandinavian Civilization - bronze knives or razors.jpg|BRONZE KNIVES OR RAZORS. Later Bronze Age, earlier and later forms}}

{{IMG:Scandinavian Civilization - part of a rock carving.jpg|PART OF A ROCK CARVING (the grooves are filled in with chalk). Bronze Age}}

{{IMG:Scandinavian Civilization - part of a rock carving (man ploughing).jpg|PART OF A ROCK CARVING. showing man ploughing}}

{{IMG:Scandinavian Civilization - rock carvings.jpg|ROCK CARVINGS. Sweden, Later Bronze Age}}

{{IMG:Scandinavian Civilization - bronze clasp.jpg|BRONZE CLASP, Later Bronze Age, Norway}}

Fig. 1 from O. Montelius, Civilization of Sweden; Figs. 2-6, 10, 11 from S. Müller, Vor Oldtid and Urgeschichte Europas; Figs. 7, 8, 12 from G. Gustafson, Norges Oldtid
```

### Current body
```
{{IMG:EB1911 Scandinavian Civilization - stone axe.jpg|STONE AXE, Later Stone Age, Sweden}}

{{IMG:Scandinavian Civilization - women's ornaments.jpg|WOMEN'S ORNAMENTS. Early Bronze Age}}

{{IMG:EB1911 Scandinavian Civilization - belt ornament.jpg|BELT ORNAMENT. Latter part of earlier Bronze Age}}

{{IMG:Scandinavian Civilization - sun chariot.jpg|SUN CHARIOT. Older Bronze Age, Denmark}}

{{IMG:Scandinavian Civilization - sword.jpg|SWORD. Second period of earlier Bronze Age}}

{{IMG:Scandinavian Civilization - bronze casket top.jpg|TOP OF A SMALL BRONZE CASKET. Latter part of earlier Bronze Age}}

{{IMG:Scandinavian Civilization - fibulæ.jpg|FIBULÆ. Earlier and later forms, Bronze Age, Norway}}

{{IMG:Scandinavian Civilization - bronze knives or razors.jpg|BRONZE KNIVES OR RAZORS. Later Bronze Age, earlier and later forms}}

{{IMG:Scandinavian Civilization - part of a rock carving.jpg|PART OF A ROCK CARVING (the grooves are filled in with chalk). Bronze Age}}

{{IMG:Scandinavian Civilization - part of a rock carving (man ploughing).jpg|PART OF A ROCK CARVING. showing man ploughing}}

{{IMG:Scandinavian Civilization - rock carvings.jpg|ROCK CARVINGS. Sweden, Later Bronze Age}}

{{IMG:Scandinavian Civilization - bronze clasp.jpg|BRONZE CLASP, Later Bronze Age, Norway}}

Fig. 1 from O. Montelius, Civilization of Sweden; Figs. 2-6, 10, 11 from S. Müller, Vor Oldtid and Urgeschichte Europas; Figs. 7, 8, 12 from G. Gustafson, Norges Oldtid
```

---

## SCANDINAVIAN CIVILIZATION, PLATE II — vol 24

**Article ID:** 4246503  
**Signature:** `wikitable depth=3 wt=multi ht=0 has_colspan`

### Source excerpt
```
{|align="center"
|
{|
|valign="bottom"|[[Image:EB1911 Scandinavian Civilization - bronze trumpet.jpg|border|200px]]
|valign="bottom"|[[Image:EB1911 Scandinavian Civilization - bronze hanging vessel.jpg|border|420px]]
|-
|align="center" width="200" valign="top"|{{EB1911 Fine Print|1.—BRONZE TRUMPET. Denmark, Later Bronze Age.}}
|align="center" width="420" valign="top"|{{EB1911 Fine Print|2.—BRONZE HANGING VESSEL. Later Bronze Age.}}
|}
|rowspan="2"|
{|
|align="center"|[[Image:EB1911 Scandinavian Civilization - torque.jpg|border|100px]]
|-
|align="center"|{{EB1911 Fine Print|3.—TORQUE. Denmark, Later Bronze Age.}}
|-
|[[Image:EB1911 Scandinavian Civilization - iron pins.jpg|border|120px]]
|-
|align="center" width="120"|{{EB1911 Fine Print|6.—IRON PINS. Pre-Roman Period, Denmark.}}
|}
|-
|
{|
|valign="bottom"|[[Image:EB1911 Scandinavian Civilization - fibula.jpg|border|230px]]
|valign="bottom"|[[Image:EB1911 Scandinavian Civilization - fibulæ.jpg|border|350px]]
|-
|align="center" width="230" valign="top"|{{EB1911 Fine Print|4.—FIBULA. Roman Period.}}
|align="center" width="350" valign="top"|{{EB1911 Fine Print|5.—FIBULÆ. Period of National Migrations, Denmark.}}
|}
|-
|colspan="2" align="center"|[[Image:EB1911 Scandinavian Civilization - gold collar.jpg|border|550px]]
|-
|colspan="2" align="center"|{{EB1911 Fine Print|7.—GOLD COLLAR. First period of Later Iron Age.}}
|-
|colspan="2"|
{|
|
{|
|[[Image:EB1911 Scandinavian Civilization - brooch.jpg|border|200px]]
|-
|align="center"
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 12 | 12 |
| captioned       | 12 | 12 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **26** | **26** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | 'Figs. 1, 3-6, 8, 9, 11 from S. Müller, Vor Oldtid; Figs. 2, 7, 12 from O. Montelius, Civ. Sweden; Fig. 10 from G. Gustaf' | 'Figs. 1, 3-6, 8, 9, 11 from S. Müller, Vor Oldtid; Figs. 2, 7, 12 from O. Montelius, Civ. Sweden; Fig. 10 from G. Gustaf' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Scandinavian Civilization - bronze trumpet.jpg|BRONZE TRUMPET. Denmark, Later Bronze Age}}

{{IMG:EB1911 Scandinavian Civilization - bronze hanging vessel.jpg|BRONZE HANGING VESSEL. Later Bronze Age}}

{{IMG:EB1911 Scandinavian Civilization - torque.jpg|TORQUE. Denmark, Later Bronze Age}}

{{IMG:EB1911 Scandinavian Civilization - iron pins.jpg|IRON PINS. Pre-Roman Period, Denmark}}

{{IMG:EB1911 Scandinavian Civilization - fibula.jpg|FIBULA. Roman Period}}

{{IMG:EB1911 Scandinavian Civilization - fibulæ.jpg|FIBULÆ. Period of National Migrations, Denmark}}

{{IMG:EB1911 Scandinavian Civilization - gold collar.jpg|GOLD COLLAR. First period of Later Iron Age}}

{{IMG:EB1911 Scandinavian Civilization - brooch.jpg|BROOCH. Post-Roman Period, Denmark}}

{{IMG:EB1911 Scandinavian Civilization - silver gilt brooch.jpg|SILVER GILT BROOCH (length over 9 inches). Period of National Migrations, Norway}}

{{IMG:EB1911 Scandinavian Civilization - bronze plate for a belt.jpg|BRONZE PLATE FOR A BELT, showing Animal Figures. Post-Roman Period}}

{{IMG:EB1911 Scandinavian Civilization - brooch set with garnets.jpg|BROOCH SET WITH GARNETS. Post-Roman Period, Denmark}}

{{IMG:EB1911 Scandinavian Civilization - gold bracteate.jpg|GOLD BRACTEATE, “barbarian” imitation of a Roman Coin. First period of Later Iron Age, Sweden}}

Figs. 1, 3-6, 8, 9, 11 from S. Müller, Vor Oldtid; Figs. 2, 7, 12 from O. Montelius, Civ. Sweden; Fig. 10 from G. Gustafson, Norges Oldtid
```

### Current body
```
{{IMG:EB1911 Scandinavian Civilization - bronze trumpet.jpg|BRONZE TRUMPET. Denmark, Later Bronze Age}}

{{IMG:EB1911 Scandinavian Civilization - bronze hanging vessel.jpg|BRONZE HANGING VESSEL. Later Bronze Age}}

{{IMG:EB1911 Scandinavian Civilization - torque.jpg|TORQUE. Denmark, Later Bronze Age}}

{{IMG:EB1911 Scandinavian Civilization - iron pins.jpg|IRON PINS. Pre-Roman Period, Denmark}}

{{IMG:EB1911 Scandinavian Civilization - fibula.jpg|FIBULA. Roman Period}}

{{IMG:EB1911 Scandinavian Civilization - fibulæ.jpg|FIBULÆ. Period of National Migrations, Denmark}}

{{IMG:EB1911 Scandinavian Civilization - gold collar.jpg|GOLD COLLAR. First period of Later Iron Age}}

{{IMG:EB1911 Scandinavian Civilization - brooch.jpg|BROOCH. Post-Roman Period, Denmark}}

{{IMG:EB1911 Scandinavian Civilization - silver gilt brooch.jpg|SILVER GILT BROOCH (length over 9 inches). Period of National Migrations, Norway}}

{{IMG:EB1911 Scandinavian Civilization - bronze plate for a belt.jpg|BRONZE PLATE FOR A BELT, showing Animal Figures. Post-Roman Period}}

{{IMG:EB1911 Scandinavian Civilization - brooch set with garnets.jpg|BROOCH SET WITH GARNETS. Post-Roman Period, Denmark}}

{{IMG:EB1911 Scandinavian Civilization - gold bracteate.jpg|GOLD BRACTEATE, “barbarian” imitation of a Roman Coin. First period of Later Iron Age, Sweden}}

Figs. 1, 3-6, 8, 9, 11 from S. Müller, Vor Oldtid; Figs. 2, 7, 12 from O. Montelius, Civ. Sweden; Fig. 10 from G. Gustafson, Norges Oldtid
```

---

## SCANDINAVIAN CIVILIZATION, PLATE III — vol 24

**Article ID:** 4246504  
**Signature:** `wikitable depth=3 wt=multi ht=0 has_colspan`

### Source excerpt
```
{|align="center"
|align="center"|
{|
|valign="bottom"|
{|
|align="center"|[[Image:EB1911 Scandinavian Civilization - axe inlaid with silver.jpg|border|200px]]
|-
|align="center" width="220"|{{EB1911 Fine Print|1.—AXE INLAID WITH SILVER. Viking Age, Denmark.}}
|-
|align="center"|[[Image:EB1911 Scandinavian Civilization - bronze clasp.jpg|border|220px]]
|-
|align="center" width="220"|{{EB1911 Fine Print|2.—TYPICAL MOTIF, ANIMAL FORM AND SNAKE, from bronze clasp, Viking Age, Denmark.}}
|}
|valign="bottom"|
{|
|[[Image:EB1911 Scandinavian Civilization - part of the Oseberg Viking ship.jpg|border|350px]]
|-
|align="center" width="350"|{{EB1911 Fine Print|3.—PART OF THE OSEBERG VIKING SHIP. Norway.}}<br>{{fsx|75%|''Photo lent by Prof. G. H. Gustafson.''}}
|}
|valign="bottom"|
{|
|align="center"|[[Image:EB1911 Scandinavian Civilization - oak carving from the Gokstad ship.jpg|border|200px]]
|-
|align="center" width="250"|{{EB1911 Fine Print|4.—OAK CARVING FROM THE GOKSTAD SHIP. Viking Age, Norway.}}
|-
|[[Image:EB1911 Scandinavian Civilization - gold spur.jpg|border|250px]]
|-
|align="center" width="250"|{{EB1911 Fine Print|5.—GOLD SPUR. Viking Age, Norway.}}
|}
|}
|-
|align="center"|
{|
|
{|
|colspan="3"|[[Image:EB1911 Scandinavian Civilization - playing piece and knob for harness.jpg|border|250px]]
|-
|align="center" width="75"|{{EB1911 Fine Print|6.—BONE PLAYING PIECE.}}
|width="15"|&nbsp;
|align="center" width="160"|{{EB1911 Fine Print|GILT BRONZE KNOB FOR HARNESS. Viking Age, No
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 11 | 11 |
| captioned       | 11 | 11 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **23** | **23** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Scandinavian Civilization - axe inlaid with silver.jpg|AXE INLAID WITH SILVER. Viking Age, Denmark}}

{{IMG:EB1911 Scandinavian Civilization - bronze clasp.jpg|TYPICAL MOTIF, ANIMAL FORM AND SNAKE, from bronze clasp, Viking Age, Denmark}}

{{IMG:EB1911 Scandinavian Civilization - part of the Oseberg Viking ship.jpg|PART OF THE OSEBERG VIKING SHIP. Norway. Photo lent by Prof. G. H. Gustafson}}

{{IMG:EB1911 Scandinavian Civilization - oak carving from the Gokstad ship.jpg|OAK CARVING FROM THE GOKSTAD SHIP. Viking Age, Norway}}

{{IMG:EB1911 Scandinavian Civilization - gold spur.jpg|GOLD SPUR. Viking Age, Norway}}

{{IMG:EB1911 Scandinavian Civilization - playing piece and knob for harness.jpg|BONE PLAYING PIECE}}

{{IMG:EB1911 Scandinavian Civilization - scenes from the life of Sigurd and runic inscription.jpg|SCENES FROM THE LIFE OF SIGURD AND RUNIC INSCRIPTION. Viking Age, Sweden}}

{{IMG:EB1911 Scandinavian Civilization - runic stone.jpg|RUNIC STONE, from Jellinge, Jutland, showing Christian influence}}

{{IMG:EB1911 Scandinavian Civilization - silver “Thor's Hammer”.jpg|SILVER “THOR'S HAMMER.” Viking Age, Sweden}}

{{IMG:EB1911 Scandinavian Civilization - brooch (face view).jpg|BROOCH. Viking Age, Norway}}

{{IMG:EB1911 Scandinavian Civilization - brooch (side view).jpg|Figs. 1, 2, 8, from S. Müller, Vor Oldtid; Figs. 3, 4, 5, 6, 10 from G. Gustafson, Norges Oldtid; Fig; 7, 9 from O. Montelius, Civ. Swed}}

{{LEGEND:align="center" width="160" GILT BRONZE KNOB FOR HARNESS. Viking Age, Norway}LEGEND}
```

### Current body
```
{{IMG:EB1911 Scandinavian Civilization - axe inlaid with silver.jpg|AXE INLAID WITH SILVER. Viking Age, Denmark}}

{{IMG:EB1911 Scandinavian Civilization - bronze clasp.jpg|TYPICAL MOTIF, ANIMAL FORM AND SNAKE, from bronze clasp, Viking Age, Denmark}}

{{IMG:EB1911 Scandinavian Civilization - part of the Oseberg Viking ship.jpg|PART OF THE OSEBERG VIKING SHIP. Norway. Photo lent by Prof. G. H. Gustafson}}

{{IMG:EB1911 Scandinavian Civilization - oak carving from the Gokstad ship.jpg|OAK CARVING FROM THE GOKSTAD SHIP. Viking Age, Norway}}

{{IMG:EB1911 Scandinavian Civilization - gold spur.jpg|GOLD SPUR. Viking Age, Norway}}

{{IMG:EB1911 Scandinavian Civilization - playing piece and knob for harness.jpg|BONE PLAYING PIECE}}

{{IMG:EB1911 Scandinavian Civilization - scenes from the life of Sigurd and runic inscription.jpg|SCENES FROM THE LIFE OF SIGURD AND RUNIC INSCRIPTION. Viking Age, Sweden}}

{{IMG:EB1911 Scandinavian Civilization - runic stone.jpg|RUNIC STONE, from Jellinge, Jutland, showing Christian influence}}

{{IMG:EB1911 Scandinavian Civilization - silver “Thor's Hammer”.jpg|SILVER “THOR'S HAMMER.” Viking Age, Sweden}}

{{IMG:EB1911 Scandinavian Civilization - brooch (face view).jpg|BROOCH. Viking Age, Norway}}

{{IMG:EB1911 Scandinavian Civilization - brooch (side view).jpg|Figs. 1, 2, 8, from S. Müller, Vor Oldtid; Figs. 3, 4, 5, 6, 10 from G. Gustafson, Norges Oldtid; Fig; 7, 9 from O. Montelius, Civ. Swed}}

{{LEGEND:align="center" width="160" GILT BRONZE KNOB FOR HARNESS. Viking Age, Norway}LEGEND}
```

---

## SCULPTURE, PLATE I — vol 24

**Article ID:** 4246765  
**Signature:** `wikitable depth=1 wt=multi ht=0`

### Source excerpt
```
{| width="100%" align="center" style="text-align: center"
|-
| [[File:EB1911 Plate I. 24, Fig 1.jpg|560px]]
| [[File:EB1911 Plate I. 24, Fig 2.jpg|500px]]
|-
| align="right" | {{smaller|(''Photo'', ''Brogi''.)}}
| align="right" | {{smaller|(''Photo'', ''Anderson''.)}}
|-
| JACOPO DELLA QUERCIA—Tomb, Ilaria del Carretto, Lucca.
| DONATELLO—Equestrian Statue, General Gattamelata, Padua.
|}
{| width="100%" align="center" style="text-align: center"
|-
| [[File:EB1911 Plate I. 24, Fig 3.jpg|420px]]
| [[File:EB1911 Plate I. 24, Fig 4.jpg|240px]]
| [[File:EB1911 Plate I. 24, Fig 5.jpg|425px]]
|-
| align="right" | {{smaller|(''Photo'', ''Alinari''.)}}
| align="right" | {{smaller|(''Photo'', ''Alinari''.)}}
| align="right" | {{smaller|(''Photo'', ''Anderson''.)}}
|-
| ANDREA PISANO—The first bronze door of the Baptistery,<br />Florence.
| DONATELLO—Statue of St George,<br />Florence.
| MICHELANGELO—Head of Colossal David, Florence.<br />&nbsp;
|}
{| width="100%" align="center" style="text-align: center"
|-
| [[File:EB1911 Plate I. 24, Fig 6.jpg|505px]]
| [[File:EB1911 Plate I. 24, Fig 7.jpg|420px]]
|-
| {{em|28.5}}{{smaller|(''Photo'', ''Anderson''.)}}
| {{em|22.2}}{{smaller|(''Photo'', ''Anderson''.)}}
|-
| VERROCCHIO & LEOPARDI—Bronze Colossal Statue of Bartolommeo<br />Colleoni, Venice.
| LUCA DELLA ROBBIA—Girls and boys playing on musical<br />instruments and dancing (Museo dell' Opera, Florence).
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 7 | 7 |
| captioned       | 7 | 7 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **14** | **14** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Plate I. 24, Fig 1.jpg|JACOPO DELLA QUERCIA—Tomb, Ilaria del Carretto, Lucca (Photo, Brogi.)}}

{{IMG:EB1911 Plate I. 24, Fig 2.jpg|DONATELLO—Equestrian Statue, General Gattamelata, Padua (Photo, Anderson.)}}

{{IMG:EB1911 Plate I. 24, Fig 3.jpg|ANDREA PISANO—The first bronze door of the Baptistery, Florence (Photo, Alinari.)}}

{{IMG:EB1911 Plate I. 24, Fig 4.jpg|DONATELLO—Statue of St George, Florence (Photo, Alinari.)}}

{{IMG:EB1911 Plate I. 24, Fig 5.jpg|MICHELANGELO—Head of Colossal David, Florence (Photo, Anderson.)}}

{{IMG:EB1911 Plate I. 24, Fig 6.jpg|VERROCCHIO & LEOPARDI—Bronze Colossal Statue of Bartolommeo Colleoni, Venice (Photo, Anderson.)}}

{{IMG:EB1911 Plate I. 24, Fig 7.jpg|LUCA DELLA ROBBIA—Girls and boys playing on musical instruments and dancing (Museo dell' Opera, Florence) (Photo, Anderson.)}}
```

### Current body
```
{{IMG:EB1911 Plate I. 24, Fig 1.jpg|JACOPO DELLA QUERCIA—Tomb, Ilaria del Carretto, Lucca (Photo, Brogi.)}}

{{IMG:EB1911 Plate I. 24, Fig 2.jpg|DONATELLO—Equestrian Statue, General Gattamelata, Padua (Photo, Anderson.)}}

{{IMG:EB1911 Plate I. 24, Fig 3.jpg|ANDREA PISANO—The first bronze door of the Baptistery, Florence (Photo, Alinari.)}}

{{IMG:EB1911 Plate I. 24, Fig 4.jpg|DONATELLO—Statue of St George, Florence (Photo, Alinari.)}}

{{IMG:EB1911 Plate I. 24, Fig 5.jpg|MICHELANGELO—Head of Colossal David, Florence (Photo, Anderson.)}}

{{IMG:EB1911 Plate I. 24, Fig 6.jpg|VERROCCHIO & LEOPARDI—Bronze Colossal Statue of Bartolommeo Colleoni, Venice (Photo, Anderson.)}}

{{IMG:EB1911 Plate I. 24, Fig 7.jpg|LUCA DELLA ROBBIA—Girls and boys playing on musical instruments and dancing (Museo dell' Opera, Florence) (Photo, Anderson.)}}
```

---

## SCULPTURE, PLATE II — vol 24

**Article ID:** 4246766  
**Signature:** `wikitable depth=1 wt=multi ht=0`

### Source excerpt
```
{| width="100%" align="center" style="text-align: center"
|-
| [[File:EB1911 Plate II. 24, Fig 1.jpg|350px]]
| [[File:EB1911 Plate II. 24, Fig 2.jpg|260px]]
| [[File:EB1911 Plate II. 24, Fig 3.jpg|330px]]
|-
| align="right" | {{smaller|(''Photo'', ''Alinari''.)}}
| align="right" | {{smaller|(''Photo'', ''Wurthle & Sohn''.)}}
| align="right" | {{smaller|(''Photo'', ''Anderson''.)}}
|-
| BENVENUTO CELLINI—Bronze Statue of Perseus<br />and Medusa, in the Loggia dei Lanzi, Florence.
| PETER VISCHER—Gilt Bronze Statue of<br />King Arthur, Florence.
| BERNINI—Apollo and Daphne (Borghese Gallery).<br />
|}
{| width="100%" align="center" style="text-align: center"
|-
| [[File:EB1911 Plate II. 24, Fig 4.jpg|520px]]
| [[File:EB1911 Plate II. 24, Fig 5.jpg|470px]]
|-
| align="right" | {{smaller|(''Photo'', ''Giraudon''.)}}
| align="right" | {{smaller|(''Photo'', ''Löwy''.)}}
|-
| JEAN GOUJON—Diane de Poitiers (as Huntress), in the Louvre.
| CANOVA—Colossal Marble Group of Theseus and Centaur, Vienna.
|}
{| width="100%" align="center" style="text-align: center"
|-
| [[File:EB1911 Plate II. 24, Fig 6.jpg|360px]]
| [[File:EB1911 Plate II. 24, Fig 7.jpg|400px]]
|-
| align="right" | {{smaller|(''Photo'', ''Giraudon''.)}}
| align="right" | {{smaller|(''Photo'', ''Giraudon''.)}}
|-
| HOUDON—Voltaire (Théàtre Français, Paris).
| COYSEVOX—Bust of himself, in the Louvre.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 7 | 7 |
| captioned       | 7 | 7 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **14** | **14** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Plate II. 24, Fig 1.jpg|BENVENUTO CELLINI—Bronze Statue of Perseus and Medusa, in the Loggia dei Lanzi, Florence (Photo, Alinari.)}}

{{IMG:EB1911 Plate II. 24, Fig 2.jpg|PETER VISCHER—Gilt Bronze Statue of King Arthur, Florence (Photo, Wurthle & Sohn.)}}

{{IMG:EB1911 Plate II. 24, Fig 3.jpg|BERNINI—Apollo and Daphne (Borghese Gallery) (Photo, Anderson.)}}

{{IMG:EB1911 Plate II. 24, Fig 4.jpg|JEAN GOUJON—Diane de Poitiers (as Huntress), in the Louvre (Photo, Giraudon.)}}

{{IMG:EB1911 Plate II. 24, Fig 5.jpg|CANOVA—Colossal Marble Group of Theseus and Centaur, Vienna (Photo, Löwy.)}}

{{IMG:EB1911 Plate II. 24, Fig 6.jpg|HOUDON—Voltaire (Théàtre Français, Paris) (Photo, Giraudon.)}}

{{IMG:EB1911 Plate II. 24, Fig 7.jpg|COYSEVOX—Bust of himself, in the Louvre (Photo, Giraudon.)}}
```

### Current body
```
{{IMG:EB1911 Plate II. 24, Fig 1.jpg|BENVENUTO CELLINI—Bronze Statue of Perseus and Medusa, in the Loggia dei Lanzi, Florence (Photo, Alinari.)}}

{{IMG:EB1911 Plate II. 24, Fig 2.jpg|PETER VISCHER—Gilt Bronze Statue of King Arthur, Florence (Photo, Wurthle & Sohn.)}}

{{IMG:EB1911 Plate II. 24, Fig 3.jpg|BERNINI—Apollo and Daphne (Borghese Gallery) (Photo, Anderson.)}}

{{IMG:EB1911 Plate II. 24, Fig 4.jpg|JEAN GOUJON—Diane de Poitiers (as Huntress), in the Louvre (Photo, Giraudon.)}}

{{IMG:EB1911 Plate II. 24, Fig 5.jpg|CANOVA—Colossal Marble Group of Theseus and Centaur, Vienna (Photo, Löwy.)}}

{{IMG:EB1911 Plate II. 24, Fig 6.jpg|HOUDON—Voltaire (Théàtre Français, Paris) (Photo, Giraudon.)}}

{{IMG:EB1911 Plate II. 24, Fig 7.jpg|COYSEVOX—Bust of himself, in the Louvre (Photo, Giraudon.)}}
```

---

## SCULPTURE—, PLATE III — vol 24

**Article ID:** 4246767  
**Signature:** `wikitable depth=1 wt=1 ht=0 has_colspan`

### Source excerpt
```
{| width="100%" align="center" style="text-align: center"
|- valign="bottom"
| [[File:EB1911 Plate III. v24, pg.504, Fig 1.jpg|295px]]
| [[File:EB1911 Plate III. v24, pg.504, Fig 2.jpg|360px]]
| [[File:EB1911 Plate III. v24, pg.504, Fig 3.jpg|300px]]
|- valign="top"
| {{smaller|(''Photo'', ''London Stereoscopic Co''.)}}
| {{smaller|&nbsp;}}
| {{smaller|(''Photo'', ''Mansell & Co''.)}}
|- valign="top"
| ALFRED STEVENS—The Wellington<br />Monument, St Paul's Cathedral, London.
| SIR GEORGE FRAMPTON, R.A.—<br />The Dr Barnardo Memorial.
| LORD LEIGHTON, P.R.A.—The Sluggard.<br />
|-
| colspan="3" | <br />[[File:EB1911 Plate III. v24, pg.504, Fig 4.jpg|720px]]
|-
| colspan="3" | {{smaller|(''Photo'', ''Frederick Hollyer''.)}}<br />HARRY BATES, A.R.A.—Homer.
|- valign="bottom"
| [[File:EB1911 Plate III. v24, pg.504, Fig 5.jpg|290px]]
| [[File:EB1911 Plate III. v24, pg.504, Fig 6.jpg|420px]]
| [[File:EB1911 Plate III. v24, pg.504, Fig 7.jpg|280px]]
|-
| H. H. ARMSTEAD, R.A.—Lieutenant Waghorn.
| G. F. WATTS, R.A.—Hugh Lupus.
| A. GILBERT—Icarus.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 7 | 7 |
| captioned       | 7 | 7 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **15** | **15** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Plate III. v24, pg.504, Fig 1.jpg|ALFRED STEVENS—The Wellington Monument, St Paul's Cathedral, London}}

{{IMG:EB1911 Plate III. v24, pg.504, Fig 2.jpg|SIR GEORGE FRAMPTON, R.A.— The Dr Barnardo Memorial}}

{{IMG:EB1911 Plate III. v24, pg.504, Fig 3.jpg|LORD LEIGHTON, P.R.A.—The Sluggard}}

{{IMG:EB1911 Plate III. v24, pg.504, Fig 4.jpg|H. H. ARMSTEAD, R.A.—Lieutenant Waghorn}}

{{IMG:EB1911 Plate III. v24, pg.504, Fig 5.jpg|G. F. WATTS, R.A.—Hugh Lupus}}

{{IMG:EB1911 Plate III. v24, pg.504, Fig 6.jpg|A. GILBERT—Icarus}}

{{IMG:EB1911 Plate III. v24, pg.504, Fig 7.jpg|(Photo, Frederick Hollyer.) HARRY BATES, A.R.A.—Homer}}

{{LEGEND:(Photo, Frederick Hollyer.) HARRY BATES, A.R.A.—Homer}LEGEND}
```

### Current body
```
{{IMG:EB1911 Plate III. v24, pg.504, Fig 1.jpg|ALFRED STEVENS—The Wellington Monument, St Paul's Cathedral, London}}

{{IMG:EB1911 Plate III. v24, pg.504, Fig 2.jpg|SIR GEORGE FRAMPTON, R.A.— The Dr Barnardo Memorial}}

{{IMG:EB1911 Plate III. v24, pg.504, Fig 3.jpg|LORD LEIGHTON, P.R.A.—The Sluggard}}

{{IMG:EB1911 Plate III. v24, pg.504, Fig 4.jpg|H. H. ARMSTEAD, R.A.—Lieutenant Waghorn}}

{{IMG:EB1911 Plate III. v24, pg.504, Fig 5.jpg|G. F. WATTS, R.A.—Hugh Lupus}}

{{IMG:EB1911 Plate III. v24, pg.504, Fig 6.jpg|A. GILBERT—Icarus}}

{{IMG:EB1911 Plate III. v24, pg.504, Fig 7.jpg|(Photo, Frederick Hollyer.) HARRY BATES, A.R.A.—Homer}}

{{LEGEND:(Photo, Frederick Hollyer.) HARRY BATES, A.R.A.—Homer}LEGEND}
```

---

## Plate IV, PLATE IV — vol 24

**Article ID:** 4246768  
**Signature:** `wikitable depth=2 wt=multi ht=0`

### Source excerpt
```
{| width="100%" align="center"
|-
|
{| width="100%" align="center" style="text-align: center"
|- valign="bottom"
| [[File:EB1911 Plate IV. v24, pg.505, Fig 1.jpg|280px]]
| [[File:EB1911 Plate IV. v24, pg.505, Fig 2.jpg|425px]]
| [[File:EB1911 Plate IV. v24, pg.505, Fig 3.jpg|280px]]
|- valign="top"
| F. W. POMEROY, A.R.A.—The Spearman.
| E. ONSLOW FORD, R.A.—Shelley Memorial.
| W. HAMO THORNYCROFT, R.A.—<br />Teucer.
|}
|-
|
{| width="100%" align="center" style="text-align: center"
|- valign="bottom"
| [[File:EB1911 Plate IV. v24, pg.505, Fig 4.jpg|270px]]
| [[File:EB1911 Plate IV. v24, pg.505, Fig 5.jpg|220px]]
| [[File:EB1911 Plate IV. v24, pg.505, Fig 6.jpg|225px]]
| [[File:EB1911 Plate IV. v24, pg.505, Fig 7.jpg|340px]]
|- valign="top"
| ALFRED DRURY, A.R.A.—<br />Innocence.
| F. DERWENT WOOD, A.R.A.—<br />Psyche.
| BERTRAM MACKENNAL, A.R.A.—<br />Diana Wounded.
| ALBERT TOFT—<br />Antigone.
|}
|-
|
{| width="100%" align="center" style="text-align: center"
|- valign="bottom"
| [[File:EB1911 Plate IV. v24, pg.505, Fig 8.jpg|275px]]
| [[File:EB1911 Plate IV. v24, pg.505, Fig 9.jpg|430px]]
| [[File:EB1911 Plate IV. v24, pg.505, Fig 10.jpg|275px]]
|- valign="top"
| HAVARD THOMAS—Lycidas.
| W. HAMO THORNYCROFT, R.A.—Dean Colet.
| W. GOSCOMBE JOHN, R.A.—<br />St John the Baptist.
|}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 10 | 10 |
| captioned       | 10 | 10 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **20** | **20** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Plate IV. v24, pg.505, Fig 1.jpg|F. W. POMEROY, A.R.A.—The Spearman}}

{{IMG:EB1911 Plate IV. v24, pg.505, Fig 2.jpg|E. ONSLOW FORD, R.A.—Shelley Memorial}}

{{IMG:EB1911 Plate IV. v24, pg.505, Fig 3.jpg|W. HAMO THORNYCROFT, R.A.— Teucer}}

{{IMG:EB1911 Plate IV. v24, pg.505, Fig 4.jpg|ALFRED DRURY, A.R.A.— Innocence}}

{{IMG:EB1911 Plate IV. v24, pg.505, Fig 5.jpg|F. DERWENT WOOD, A.R.A.— Psyche}}

{{IMG:EB1911 Plate IV. v24, pg.505, Fig 6.jpg|BERTRAM MACKENNAL, A.R.A.— Diana Wounded}}

{{IMG:EB1911 Plate IV. v24, pg.505, Fig 7.jpg|ALBERT TOFT— Antigone}}

{{IMG:EB1911 Plate IV. v24, pg.505, Fig 8.jpg|HAVARD THOMAS—Lycidas}}

{{IMG:EB1911 Plate IV. v24, pg.505, Fig 9.jpg|W. HAMO THORNYCROFT, R.A.—Dean Colet}}

{{IMG:EB1911 Plate IV. v24, pg.505, Fig 10.jpg|W. GOSCOMBE JOHN, R.A.— St John the Baptist}}
```

### Current body
```
{{IMG:EB1911 Plate IV. v24, pg.505, Fig 1.jpg|F. W. POMEROY, A.R.A.—The Spearman}}

{{IMG:EB1911 Plate IV. v24, pg.505, Fig 2.jpg|E. ONSLOW FORD, R.A.—Shelley Memorial}}

{{IMG:EB1911 Plate IV. v24, pg.505, Fig 3.jpg|W. HAMO THORNYCROFT, R.A.— Teucer}}

{{IMG:EB1911 Plate IV. v24, pg.505, Fig 4.jpg|ALFRED DRURY, A.R.A.— Innocence}}

{{IMG:EB1911 Plate IV. v24, pg.505, Fig 5.jpg|F. DERWENT WOOD, A.R.A.— Psyche}}

{{IMG:EB1911 Plate IV. v24, pg.505, Fig 6.jpg|BERTRAM MACKENNAL, A.R.A.— Diana Wounded}}

{{IMG:EB1911 Plate IV. v24, pg.505, Fig 7.jpg|ALBERT TOFT— Antigone}}

{{IMG:EB1911 Plate IV. v24, pg.505, Fig 8.jpg|HAVARD THOMAS—Lycidas}}

{{IMG:EB1911 Plate IV. v24, pg.505, Fig 9.jpg|W. HAMO THORNYCROFT, R.A.—Dean Colet}}

{{IMG:EB1911 Plate IV. v24, pg.505, Fig 10.jpg|W. GOSCOMBE JOHN, R.A.— St John the Baptist}}
```

---

## SCULPTURE—, PLATE V — vol 24

**Article ID:** 4246769  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{| width="100%" align="center" style="text-align: center"
|- valign="bottom"
| [[File:EB1911 Plate V. v24, pg.506, Fig 1.jpg|280px]]
| [[File:EB1911 Plate V. v24, pg.506, Fig 2.jpg|430px]]
| [[File:EB1911 Plate V. v24, pg.506, Fig 3.jpg|280px]]
|- valign="top"
| W. R. COLTON, A.R.A.—Maharajah<br />of Mysore.
| SIR CHARLES LAWES-WITTEWRONGE—<br />The Punishment of Dirce.
| G. F. WATTS, R.A.—Clytie.
|- valign="bottom"
| [[File:EB1911 Plate V. v24, pg.506, Fig 4.jpg|280px]]
| [[File:EB1911 Plate V. v24, pg.506, Fig 5.jpg|430px]]
| [[File:EB1911 Plate V. v24, pg.506, Fig 6.jpg|270px]]
|- valign="top"
| SIR J. EDGAR BOEHM, R.A.—Carlyle.
| W. R. COLTON, A.R.A.—The Crown of Love.
| THOMAS BROCK, R.A.—The Genius<br />of Poetry.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 6 | 6 |
| captioned       | 6 | 6 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **12** | **12** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Plate V. v24, pg.506, Fig 1.jpg|W. R. COLTON, A.R.A.—Maharajah of Mysore}}

{{IMG:EB1911 Plate V. v24, pg.506, Fig 2.jpg|SIR CHARLES LAWES-WITTEWRONGE— The Punishment of Dirce}}

{{IMG:EB1911 Plate V. v24, pg.506, Fig 3.jpg|G. F. WATTS, R.A.—Clytie}}

{{IMG:EB1911 Plate V. v24, pg.506, Fig 4.jpg|SIR J. EDGAR BOEHM, R.A.—Carlyle}}

{{IMG:EB1911 Plate V. v24, pg.506, Fig 5.jpg|W. R. COLTON, A.R.A.—The Crown of Love}}

{{IMG:EB1911 Plate V. v24, pg.506, Fig 6.jpg|THOMAS BROCK, R.A.—The Genius of Poetry}}
```

### Current body
```
{{IMG:EB1911 Plate V. v24, pg.506, Fig 1.jpg|W. R. COLTON, A.R.A.—Maharajah of Mysore}}

{{IMG:EB1911 Plate V. v24, pg.506, Fig 2.jpg|SIR CHARLES LAWES-WITTEWRONGE— The Punishment of Dirce}}

{{IMG:EB1911 Plate V. v24, pg.506, Fig 3.jpg|G. F. WATTS, R.A.—Clytie}}

{{IMG:EB1911 Plate V. v24, pg.506, Fig 4.jpg|SIR J. EDGAR BOEHM, R.A.—Carlyle}}

{{IMG:EB1911 Plate V. v24, pg.506, Fig 5.jpg|W. R. COLTON, A.R.A.—The Crown of Love}}

{{IMG:EB1911 Plate V. v24, pg.506, Fig 6.jpg|THOMAS BROCK, R.A.—The Genius of Poetry}}
```

---

## Plate VI, PLATE VI — vol 24

**Article ID:** 4246770  
**Signature:** `wikitable depth=2 wt=multi ht=0 has_colspan`

### Source excerpt
```
{| width="100%" align="center"
|-
|
{| width="100%" align="center" style="text-align: center"
|- valign="bottom"
| [[File:EB1911 Plate VI. v24, pg.507, Fig 1.jpg|330px]]
| [[File:EB1911 Plate VI. v24, pg.507, Fig 2.jpg|570px]]
|- valign="top"
| J. Q. A. WARD—George Washington.
| D. C. FRENCH—Indian Corn; Bull by E. C. POTTER.
|-
| colspan="2" | &nbsp;
|}
|-
|
{| width="100%" align="center" style="text-align: center"
|- valign="bottom"
| [[File:EB1911 Plate VI. v24, pg.507, Fig 3.jpg|620px]]
| [[File:EB1911 Plate VI. v24, pg.507, Fig 4.jpg|280px]]
|- valign="top"
| AUGUSTUS ST GAUDENS—Memorial to Robert Gould Shaw.
| {{sc|FREDERICK MacMONNIES}}—Nathan Hale.<br />(''By permission of Theodore B. Starr, New York.''<br />''Copyrighted by Frederick MacMonnies.'')
|}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Plate VI. v24, pg.507, Fig 1.jpg|J. Q. A. WARD—George Washington}}

{{IMG:EB1911 Plate VI. v24, pg.507, Fig 2.jpg|D. C. FRENCH—Indian Corn; Bull by E. C. POTTER}}

{{IMG:EB1911 Plate VI. v24, pg.507, Fig 3.jpg|AUGUSTUS ST GAUDENS—Memorial to Robert Gould Shaw}}

{{IMG:EB1911 Plate VI. v24, pg.507, Fig 4.jpg|FREDERICK MacMONNIES —Nathan Hale. (By permission of Theodore B. Starr, New York. Copyrighted by Frederick MacMonnies.)}}
```

### Current body
```
{{IMG:EB1911 Plate VI. v24, pg.507, Fig 1.jpg|J. Q. A. WARD—George Washington}}

{{IMG:EB1911 Plate VI. v24, pg.507, Fig 2.jpg|D. C. FRENCH—Indian Corn; Bull by E. C. POTTER}}

{{IMG:EB1911 Plate VI. v24, pg.507, Fig 3.jpg|AUGUSTUS ST GAUDENS—Memorial to Robert Gould Shaw}}

{{IMG:EB1911 Plate VI. v24, pg.507, Fig 4.jpg|FREDERICK MacMONNIES —Nathan Hale. (By permission of Theodore B. Starr, New York. Copyrighted by Frederick MacMonnies.)}}
```

---

## SCULPTURE—, PLATE VII — vol 24

**Article ID:** 4246771  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{| width="100%" align="center" style="text-align: center"
|- valign="bottom"
| [[File:EB1911 Plate VII. v24, pg.508, Fig 1.jpg|250px|center]]
| [[File:EB1911 Plate VII. v24, pg.508, Fig 2.jpg|380px|center]]
| [[File:EB1911 Plate VII. v24, pg.508, Fig 3.jpg|250px|center]]
|- valign="top"
| A. FALGUIĖRE—St Vincent<br />de Paul.
| E. BARRIAS—The First Funeral.
| E. DELAPLANCHE—The Virgin<br />with the Lily.
|- valign="bottom"
| rowspan="4" | [[File:EB1911 Plate VII. v24, pg.508, Fig 4.jpg|center|200px]]
| [[File:EB1911 Plate VII. v24, pg.508, Fig 5.jpg|center|480px]]
| rowspan="4" | [[File:EB1911 Plate VII. v24, pg.508, Fig 7.jpg|center|200px]]
|- valign="top"
| A. IDRAC—Mercury inventing the Caduceus.
|-
| &nbsp;
|- valign="bottom"
| [[File:EB1911 Plate VII. v24, pg.508, Fig 6.jpg|center|480px]]
|- valign="top"
| JUSTE BECQUER—St Sebastian.
| L. GÉRÔME—Bonaparte at Cairo.
| L. MARQUESTE—Galatea.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 7 | 7 |
| captioned       | 7 | 7 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **14** | **14** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Plate VII. v24, pg.508, Fig 1.jpg|A. FALGUIĖRE—St Vincent de Paul}}

{{IMG:EB1911 Plate VII. v24, pg.508, Fig 2.jpg|E. BARRIAS—The First Funeral}}

{{IMG:EB1911 Plate VII. v24, pg.508, Fig 3.jpg|E. DELAPLANCHE—The Virgin with the Lily}}

{{IMG:EB1911 Plate VII. v24, pg.508, Fig 4.jpg|A. IDRAC—Mercury inventing the Caduceus}}

{{IMG:EB1911 Plate VII. v24, pg.508, Fig 5.jpg|JUSTE BECQUER—St Sebastian}}

{{IMG:EB1911 Plate VII. v24, pg.508, Fig 7.jpg|L. GÉRÔME—Bonaparte at Cairo}}

{{IMG:EB1911 Plate VII. v24, pg.508, Fig 6.jpg|L. MARQUESTE—Galatea}}
```

### Current body
```
{{IMG:EB1911 Plate VII. v24, pg.508, Fig 1.jpg|A. FALGUIĖRE—St Vincent de Paul}}

{{IMG:EB1911 Plate VII. v24, pg.508, Fig 2.jpg|E. BARRIAS—The First Funeral}}

{{IMG:EB1911 Plate VII. v24, pg.508, Fig 3.jpg|E. DELAPLANCHE—The Virgin with the Lily}}

{{IMG:EB1911 Plate VII. v24, pg.508, Fig 4.jpg|A. IDRAC—Mercury inventing the Caduceus}}

{{IMG:EB1911 Plate VII. v24, pg.508, Fig 5.jpg|JUSTE BECQUER—St Sebastian}}

{{IMG:EB1911 Plate VII. v24, pg.508, Fig 7.jpg|L. GÉRÔME—Bonaparte at Cairo}}

{{IMG:EB1911 Plate VII. v24, pg.508, Fig 6.jpg|L. MARQUESTE—Galatea}}
```

---

## Plate VIII, PLATE VIII — vol 24

**Article ID:** 4246772  
**Signature:** `wikitable depth=1 wt=1 ht=0 has_colspan`

### Source excerpt
```
{| width="100%" align="center" style="text-align: center"
|- valign="bottom"
| rowspan="4" | [[File:EB1911 Plate VIII. v24, pg.509, Fig 1.jpg|center|425px]]
| [[File:EB1911 Plate VIII. v24, pg.509, Fig 2.jpg|center|250px]]
| rowspan="4" | [[File:EB1911 Plate VIII. v24, pg.509, Fig 4.jpg|center|310px]]
|- valign="top"
| FRÉMIET—The Bear Hunter.
|-
| &nbsp;
|- valign="bottom"
| [[File:EB1911 Plate VIII. v24, pg.509, Fig 3.jpg|center|310px]]
|- valign="top"
| L. LONGEPIED—Immortality.
| GUILLAUME—The Roman Marriage.
| D. PUECH—The Siren.
|-
| colspan="3" | &nbsp;
|- valign="bottom"
| [[File:EB1911 Plate VIII. v24, pg.509, Fig 5.jpg|center|290px]]
| [[File:EB1911 Plate VIII. v24, pg.509, Fig 6.jpg|center|265px]]
| [[File:EB1911 Plate VIII. v24, pg.509, Fig 7.jpg|center|350px]]
|- valign="top"
| R. DE SAINT-MARCEAUX—Genius guarding<br />the Secret of the Tomb.
| A. MERCIÉ—Souvenir.
| A. RODIN—The Kiss.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 7 | 7 |
| captioned       | 7 | 7 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **14** | **14** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Plate VIII. v24, pg.509, Fig 1.jpg|FRÉMIET—The Bear Hunter}}

{{IMG:EB1911 Plate VIII. v24, pg.509, Fig 2.jpg|L. LONGEPIED—Immortality}}

{{IMG:EB1911 Plate VIII. v24, pg.509, Fig 4.jpg|GUILLAUME—The Roman Marriage}}

{{IMG:EB1911 Plate VIII. v24, pg.509, Fig 3.jpg|D. PUECH—The Siren}}

{{IMG:EB1911 Plate VIII. v24, pg.509, Fig 5.jpg|R. DE SAINT-MARCEAUX—Genius guarding the Secret of the Tomb}}

{{IMG:EB1911 Plate VIII. v24, pg.509, Fig 6.jpg|A. MERCIÉ—Souvenir}}

{{IMG:EB1911 Plate VIII. v24, pg.509, Fig 7.jpg|A. RODIN—The Kiss}}
```

### Current body
```
{{IMG:EB1911 Plate VIII. v24, pg.509, Fig 1.jpg|FRÉMIET—The Bear Hunter}}

{{IMG:EB1911 Plate VIII. v24, pg.509, Fig 2.jpg|L. LONGEPIED—Immortality}}

{{IMG:EB1911 Plate VIII. v24, pg.509, Fig 4.jpg|GUILLAUME—The Roman Marriage}}

{{IMG:EB1911 Plate VIII. v24, pg.509, Fig 3.jpg|D. PUECH—The Siren}}

{{IMG:EB1911 Plate VIII. v24, pg.509, Fig 5.jpg|R. DE SAINT-MARCEAUX—Genius guarding the Secret of the Tomb}}

{{IMG:EB1911 Plate VIII. v24, pg.509, Fig 6.jpg|A. MERCIÉ—Souvenir}}

{{IMG:EB1911 Plate VIII. v24, pg.509, Fig 7.jpg|A. RODIN—The Kiss}}
```

---

## SCULPTURE—, PLATE IX — vol 24

**Article ID:** 4246773  
**Signature:** `wikitable depth=2 wt=multi ht=0`

### Source excerpt
```
{| width="100%" align="center" style="text-align: center"
|- valign="center"
|
{| width="100%" align="center" style="text-align: center"
|- valign="bottom"
| [[File:EB1911 Plate IX. v24, pg.510, Fig 1.jpg|235px]]
|- valign="top"
| G. MICHEL—Dreaming.<br />&nbsp;<br />&nbsp;
|- valign="bottom"
| [[File:EB1911 Plate IX. v24, pg.510, Fig 5.jpg|315px]]
|- valign="top"
| ROGER BLOCHE—The Child.
|}
|
{| width="100%" align="center" style="text-align: center"
|- valign="bottom"
| [[File:EB1911 Plate IX. v24, pg.510, Fig 2.jpg|390px]]
|- valign="top"
| J. DALOU—The Triumph of the Republic.<br />&nbsp;
|- valign="bottom"
| [[File:EB1911 Plate IX. v24, pg.510, Fig 4.jpg|365px]]
|- valign="top"
| H. CHAPU—Youth (Monument to Henri Regnault).<br />&nbsp;
|- valign="bottom"
| [[File:EB1911 Plate IX. v24, pg.510, Fig 6.jpg|290px]]
|- valign="top"
| GARDET—Fighting Panthers.
|}
|
{| width="100%" align="center" style="text-align: center"
|- valign="bottom"
| [[File:EB1911 Plate IX. v24, pg.510, Fig 3.jpg|235px]]
|- valign="top"
| P. AUBÉ—Bailly.<br />&nbsp;<br />&nbsp;
|- valign="bottom"
| [[File:EB1911 Plate IX. v24, pg.510, Fig 7.jpg|280px]]
|- valign="top"
| BARTHOLOMÉ—Young Girl dressing her Hair.
|}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 7 | 7 |
| captioned       | 7 | 7 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **14** | **14** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Plate IX. v24, pg.510, Fig 1.jpg|G. MICHEL—Dreaming}}

{{IMG:EB1911 Plate IX. v24, pg.510, Fig 5.jpg|ROGER BLOCHE—The Child}}

{{IMG:EB1911 Plate IX. v24, pg.510, Fig 2.jpg|J. DALOU—The Triumph of the Republic}}

{{IMG:EB1911 Plate IX. v24, pg.510, Fig 4.jpg|H. CHAPU—Youth (Monument to Henri Regnault)}}

{{IMG:EB1911 Plate IX. v24, pg.510, Fig 6.jpg|GARDET—Fighting Panthers}}

{{IMG:EB1911 Plate IX. v24, pg.510, Fig 3.jpg|P. AUBÉ—Bailly}}

{{IMG:EB1911 Plate IX. v24, pg.510, Fig 7.jpg|BARTHOLOMÉ—Young Girl dressing her Hair}}
```

### Current body
```
{{IMG:EB1911 Plate IX. v24, pg.510, Fig 1.jpg|G. MICHEL—Dreaming}}

{{IMG:EB1911 Plate IX. v24, pg.510, Fig 5.jpg|ROGER BLOCHE—The Child}}

{{IMG:EB1911 Plate IX. v24, pg.510, Fig 2.jpg|J. DALOU—The Triumph of the Republic}}

{{IMG:EB1911 Plate IX. v24, pg.510, Fig 4.jpg|H. CHAPU—Youth (Monument to Henri Regnault)}}

{{IMG:EB1911 Plate IX. v24, pg.510, Fig 6.jpg|GARDET—Fighting Panthers}}

{{IMG:EB1911 Plate IX. v24, pg.510, Fig 3.jpg|P. AUBÉ—Bailly}}

{{IMG:EB1911 Plate IX. v24, pg.510, Fig 7.jpg|BARTHOLOMÉ—Young Girl dressing her Hair}}
```

---

## SCULPTURE—Other Foreign Countries, PLATE X — vol 24

**Article ID:** 4246774  
**Signature:** `wikitable depth=1 wt=1 ht=0 has_colspan`

### Source excerpt
```
{| width="100%" align="center" style="text-align: center"
|- valign="bottom"
| colspan="2" | [[File:EB1911 Plate X. v24, pg.511, Fig 1.jpg|290px]]
| colspan="4" | [[File:EB1911 Plate X. v24, pg.511, Fig 2.jpg|615px]]
|- valign="top"
| colspan="2" | S. SINDING—The Captive Mother.<br />(Danish.)
| colspan="4" | (''Photo'', ''W. Titzenthalen'', ''Berlin''.)<br />REINHOLD BEGAS—Statue and Memorial of Emperor William I.<br />(German.)<br />&nbsp;
|- valign="bottom"
| colspan="2" | [[File:EB1911 Plate X. v24, pg.511, Fig 3.jpg|235px]]
| colspan="2" | [[File:EB1911 Plate X. v24, pg.511, Fig 4.jpg|380px]]
| colspan="2" | [[File:EB1911 Plate X. v24, pg.511, Fig 5.jpg|235px]]
|- valign="top"
| colspan="2" | ETTORE XIMENES—Revolution.<br />(German.)<br />&nbsp;
| colspan="2" | A. QUEROL—Memorial to Alphonso XII. (From the Model.)<br />(Spanish.)
| colspan="2" | M. ANTOKOLSKI—Satan.<br />(Russian.)
|- valign="bottom"
| colspan="3" | [[File:EB1911 Plate X. v24, pg.511, Fig 6.jpg|440px]]
| colspan="3" | [[File:EB1911 Plate X. v24, pg.511, Fig 7.jpg|445px]]
|- valign="top"
| colspan="3" | JEF LAMBEAUX—The Human Passions.<br />(Belgian.)
| colspan="3" | C. MEUNIER—Uploading.<br />(Belgian.)
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 7 | 7 |
| captioned       | 1 | 1 |
| legends         | 5 | 5 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **15** | **15** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | 'JEF LAMBEAUX—The Human Passions. (Belgian.) C. MEUNIER—Uploading. (Belgian.)' | 'JEF LAMBEAUX—The Human Passions. (Belgian.) C. MEUNIER—Uploading. (Belgian.)' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Plate X. v24, pg.511, Fig 1.jpg|(Photo, W. Titzenthalen, Berlin.) REINHOLD BEGAS—Statue and Memorial of Emperor William I. (German.)}}

{{IMG:EB1911 Plate X. v24, pg.511, Fig 2.jpg}}

{{IMG:EB1911 Plate X. v24, pg.511, Fig 3.jpg}}

{{IMG:EB1911 Plate X. v24, pg.511, Fig 4.jpg}}

{{IMG:EB1911 Plate X. v24, pg.511, Fig 5.jpg}}

{{IMG:EB1911 Plate X. v24, pg.511, Fig 6.jpg}}

{{IMG:EB1911 Plate X. v24, pg.511, Fig 7.jpg}}

{{LEGEND:S. SINDING—The Captive Mother. (Danish.)}LEGEND}

{{LEGEND:(Photo, W. Titzenthalen, Berlin.) REINHOLD BEGAS—Statue and Memorial of Emperor William I. (German.)}LEGEND}

{{LEGEND:ETTORE XIMENES—Revolution. (German.)}LEGEND}

{{LEGEND:A. QUEROL—Memorial to Alphonso XII. (From the Model.) (Spanish.)}LEGEND}

{{LEGEND:M. ANTOKOLSKI—Satan. (Russian.)}LEGEND}

JEF LAMBEAUX—The Human Passions. (Belgian.) C. MEUNIER—Uploading. (Belgian.)
```

### Current body
```
{{IMG:EB1911 Plate X. v24, pg.511, Fig 1.jpg|(Photo, W. Titzenthalen, Berlin.) REINHOLD BEGAS—Statue and Memorial of Emperor William I. (German.)}}

{{IMG:EB1911 Plate X. v24, pg.511, Fig 2.jpg}}

{{IMG:EB1911 Plate X. v24, pg.511, Fig 3.jpg}}

{{IMG:EB1911 Plate X. v24, pg.511, Fig 4.jpg}}

{{IMG:EB1911 Plate X. v24, pg.511, Fig 5.jpg}}

{{IMG:EB1911 Plate X. v24, pg.511, Fig 6.jpg}}

{{IMG:EB1911 Plate X. v24, pg.511, Fig 7.jpg}}

{{LEGEND:S. SINDING—The Captive Mother. (Danish.)}LEGEND}

{{LEGEND:(Photo, W. Titzenthalen, Berlin.) REINHOLD BEGAS—Statue and Memorial of Emperor William I. (German.)}LEGEND}

{{LEGEND:ETTORE XIMENES—Revolution. (German.)}LEGEND}

{{LEGEND:A. QUEROL—Memorial to Alphonso XII. (From the Model.) (Spanish.)}LEGEND}

{{LEGEND:M. ANTOKOLSKI—Satan. (Russian.)}LEGEND}

JEF LAMBEAUX—The Human Passions. (Belgian.) C. MEUNIER—Uploading. (Belgian.)
```

---

## SHAKESPEARE, PLATE I — vol 24

**Article ID:** 4247148  
**Signature:** `html_table depth=0 wt=0 ht=1 toplegend`

### Source excerpt
```
{{center|PORTRAITS OF SHAKESPEARE}}

<table {{Ts|ma}}>
<tr>
<td>[[Image:Britannica Shakespeare Stratford Bust.jpg|380px]]<br/>
{{EB1911 Fine Print|''Photo, Harold Baker, Birmingham.''}}
</td>
<td style="width: 2.5em"></td>
<td>[[Image:Britannica Shakespeare Droeshout Engraving.jpg|380px]]<br/>
{{EB1911 Fine Print|''Photo, Emery Walker.''}}
</td></tr>
<td><div style="margin-left: 4em; text-indent: -2.5em">
THE STRATFORD BUST AND MONUMENT<br>
IN HOLY TRINITY CHURCH,<br>
STRATFORD-ON-AVON. Erected before 1623.
</div></td>
<td></td>
<td align="center">
THE ENGRAVING BY MARTIN DROESHOUT.<br/>
In the First Folio Edition. 1623.
</td>
<tr style="height: 2.5em"></tr>
<tr>
<td>[[Image:Britannica Shakespeare Chandos Portrait.jpg|380px]]<br/>
{{EB1911 Fine Print|''Photo, Emery Walker.''}}
</td>
<td></td>
<td>[[Image:Britannica Shakespeare Flower Portrait.jpg|380px]]
</td>
</tr>
<tr>
<td align="center">
THE CHANDOS PORTRAIT.<br/>
In the National Portrait Gallery.
</td>
<td></td>
<td align="center">
THE FLOWER PORTRAIT.<br/>
(The “Droeshout Original”).<br/>
In the Shakespeare Memorial Gallery.
</td>
</tr>
</table>

{{nop}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **9** | **9** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:Britannica Shakespeare Stratford Bust.jpg|THE STRATFORD BUST AND MONUMENT IN HOLY TRINITY CHURCH, STRATFORD-ON-AVON. Erected before 1623}}

{{IMG:Britannica Shakespeare Droeshout Engraving.jpg|THE ENGRAVING BY MARTIN DROESHOUT. In the First Folio Edition. 1623}}

{{IMG:Britannica Shakespeare Chandos Portrait.jpg|THE CHANDOS PORTRAIT. In the National Portrait Gallery}}

{{IMG:Britannica Shakespeare Flower Portrait.jpg|THE FLOWER PORTRAIT. (The “Droeshout Original”). In the Shakespeare Memorial Gallery}}

{{LEGEND:PORTRAITS OF SHAKESPEARE}LEGEND}
```

### Current body
```
{{IMG:Britannica Shakespeare Stratford Bust.jpg|THE STRATFORD BUST AND MONUMENT IN HOLY TRINITY CHURCH, STRATFORD-ON-AVON. Erected before 1623}}

{{IMG:Britannica Shakespeare Droeshout Engraving.jpg|THE ENGRAVING BY MARTIN DROESHOUT. In the First Folio Edition. 1623}}

{{IMG:Britannica Shakespeare Chandos Portrait.jpg|THE CHANDOS PORTRAIT. In the National Portrait Gallery}}

{{IMG:Britannica Shakespeare Flower Portrait.jpg|THE FLOWER PORTRAIT. (The “Droeshout Original”). In the Shakespeare Memorial Gallery}}

{{LEGEND:PORTRAITS OF SHAKESPEARE}LEGEND}
```

---

## SHAKESPEARE, PLATE II — vol 24

**Article ID:** 4247149  
**Signature:** `html_table depth=0 wt=0 ht=1 toplegend`

### Source excerpt
```
{{center|PORTRAITS OF SHAKESPEARE}}

<table align="center">
<tr>
<td>[[Image:Britannica Shakespeare Janssen.jpg|180px]]<br/>
{{center|1. THE JANSSEN.}}
</td>
<td style="width: 1em"></td>
<td>[[Image:Britannica Shakespeare Felton.jpg|180px]]<br/>
{{center|2. THE FELTON.}}
</td>
<td style="width: 1em"></td>
<td>[[Image:Britannica Shakespeare Ely Palace.jpg|180px]]<br/>
{{center|3. THE ELY PALACE.}}
</td>
<td style="width: 1em"></td>
<td>[[Image:Britannica Shakespeare Hunt.jpg|180px]]<br/>
{{center|4. THE HUNT OR STRATFORD.}}
</td>
</tr>
<tr><td style="height: 1em"></td></tr>
<tr>
<td>[[Image:Britannica Shakespeare Lumley.jpg|180px]]<br/>
{{center|5. THE LUMLEY.}}
</td>
<td></td>
<td>[[Image:Britannica Shakespeare Ashbourne.jpg|180px]]<br/>
{{center|6. THE ASHBOURNE.}}
</td>
<td></td>
<td>[[Image:Britannica Shakespeare Hampton Court.jpg|180px]]<br/>
{{center|7. THE HAMPTON COURT.}}
</td>
<td></td>
<td>[[Image:Britannica Shakespeare Soest.jpg|180px]]<br/>
{{center|8. THE SOEST.}}
</td>
</tr>
<tr><td style="height: 1em"></td></tr>
<tr>
<td>[[Image:Britannica Shakespeare Hilliard.jpg|180px]]<br/>
{{center|9. THE HILLIARD MINIATURE.}}
</td>
<td></td>
<td>[[Image:Britannica Shakespeare Auriol.jpg|180px]]<br/>
{{center|10. THE AURIOL MINIATURE.}}
</td>
<td></td>
<td>[[Image:Britannica Shakespeare Dunford.jpg|180px]]<br/>
{{EB1911 Fine Print|''Photo, W.A. Mansell.''}}<br/>
{{center|11. THE DUNFORD.}}
</td>
<td></td>
<td>[[Image:Britannica Shakespeare Stace.jpg|180px]]<br/>
{{EB1911 Fin
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 16 | 16 |
| captioned       | 16 | 16 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **33** | **33** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:Britannica Shakespeare Janssen.jpg|THE JANSSEN}}

{{IMG:Britannica Shakespeare Felton.jpg|THE FELTON}}

{{IMG:Britannica Shakespeare Ely Palace.jpg|THE ELY PALACE}}

{{IMG:Britannica Shakespeare Hunt.jpg|THE HUNT OR STRATFORD}}

{{IMG:Britannica Shakespeare Lumley.jpg|THE LUMLEY}}

{{IMG:Britannica Shakespeare Ashbourne.jpg|THE ASHBOURNE}}

{{IMG:Britannica Shakespeare Hampton Court.jpg|THE HAMPTON COURT}}

{{IMG:Britannica Shakespeare Soest.jpg|THE SOEST}}

{{IMG:Britannica Shakespeare Hilliard.jpg|THE HILLIARD MINIATURE}}

{{IMG:Britannica Shakespeare Auriol.jpg|THE AURIOL MINIATURE}}

{{IMG:Britannica Shakespeare Dunford.jpg|THE DUNFORD}}

{{IMG:Britannica Shakespeare Stace.jpg|THE STACE}}

{{IMG:Britannica Shakespeare Death-Mask.jpg|THE DEATH-MASK}}

{{IMG:Britannica Shakespeare Roubiliac.jpg|THE ROUBILIAC STATUE}}

{{IMG:Britannica Shakespeare Scheemakers Statue.jpg|THE SCHEEMAKERS STATUE}}

{{IMG:Britannica Shakespeare Davenant Bust.jpg|THE DAVENANT BUST}}

{{LEGEND:PORTRAITS OF SHAKESPEARE}LEGEND}
```

### Current body
```
{{IMG:Britannica Shakespeare Janssen.jpg|THE JANSSEN}}

{{IMG:Britannica Shakespeare Felton.jpg|THE FELTON}}

{{IMG:Britannica Shakespeare Ely Palace.jpg|THE ELY PALACE}}

{{IMG:Britannica Shakespeare Hunt.jpg|THE HUNT OR STRATFORD}}

{{IMG:Britannica Shakespeare Lumley.jpg|THE LUMLEY}}

{{IMG:Britannica Shakespeare Ashbourne.jpg|THE ASHBOURNE}}

{{IMG:Britannica Shakespeare Hampton Court.jpg|THE HAMPTON COURT}}

{{IMG:Britannica Shakespeare Soest.jpg|THE SOEST}}

{{IMG:Britannica Shakespeare Hilliard.jpg|THE HILLIARD MINIATURE}}

{{IMG:Britannica Shakespeare Auriol.jpg|THE AURIOL MINIATURE}}

{{IMG:Britannica Shakespeare Dunford.jpg|THE DUNFORD}}

{{IMG:Britannica Shakespeare Stace.jpg|THE STACE}}

{{IMG:Britannica Shakespeare Death-Mask.jpg|THE DEATH-MASK}}

{{IMG:Britannica Shakespeare Roubiliac.jpg|THE ROUBILIAC STATUE}}

{{IMG:Britannica Shakespeare Scheemakers Statue.jpg|THE SCHEEMAKERS STATUE}}

{{IMG:Britannica Shakespeare Davenant Bust.jpg|THE DAVENANT BUST}}

{{LEGEND:PORTRAITS OF SHAKESPEARE}LEGEND}
```

---

## SHEEP — vol 24

**Article ID:** 4247206  
**Signature:** `wikitable depth=1 wt=1 ht=0 has_colspan`

### Source excerpt
```
{{right|{{sc|Plate I.}}}}

{|align="center" style="text-align: center"
|-
|[[Image:EB1911 Sheep - Lincoln Longwool Ram.jpg|x200px]]
|&emsp;
|[[Image:EB1911 Sheep - Leicester Ram.jpg|x200px]]
|-
|{{uc|Lincoln Longwool Ram}}
|
|{{uc|Leicester Ram}}
|-
|[[Image:EB1911 Sheep - Wensleydale Ram.jpg|x200px]]
|
|[[Image:EB1911 Sheep - Devon Longwool Ram.jpg|x200px]]
|-
|{{uc|Wensleydale Ram}}
|
|{{uc|Devon Longwool Ram}}
|-
|[[Image:EB1911 Sheep - Southdown Ram.jpg|x200px]]
|
|[[Image:EB1911 Sheep - Hampshire Down Ram.jpg|x200px]]
|-
|{{uc|Southdown Ram}}
|
|{{uc|Hampshire Down Ram}}
|-
|[[Image:EB1911 Sheep - Oxford Down Ram.jpg|x200px]]
|
|[[Image:EB1911 Sheep - Shropshire Ram.jpg|x200px]]
|-
|{{uc|Oxford Down Ram}}
|
|{{uc|Shropshire Ram}}
|-
|colspan="3"|
<div style="width: 750px; margin-left: auto; margin-right: auto">
BRITISH BREEDS OF SHEEP, from photographs by F. Babbage.  The comparative sizes of the animals are indicated by
the scale of reproduction.
</div>
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 8 | 8 |
| captioned       | 8 | 8 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **20** | **20** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **2** | **2** |
| header text     | 'Plate I.' | 'Plate I.' |
| footer text     | 'BRITISH BREEDS OF SHEEP, from photographs by F. Babbage. The comparative sizes of the animals are indicated by the scale' | 'BRITISH BREEDS OF SHEEP, from photographs by F. Babbage. The comparative sizes of the animals are indicated by the scale' |

**Verdict:** ✅ identical

### Baseline body
```
Plate I.

{{IMG:EB1911 Sheep - Lincoln Longwool Ram.jpg|LINCOLN LONGWOOL RAM}}

{{IMG:EB1911 Sheep - Leicester Ram.jpg|LEICESTER RAM}}

{{IMG:EB1911 Sheep - Wensleydale Ram.jpg|WENSLEYDALE RAM}}

{{IMG:EB1911 Sheep - Devon Longwool Ram.jpg|DEVON LONGWOOL RAM}}

{{IMG:EB1911 Sheep - Southdown Ram.jpg|SOUTHDOWN RAM}}

{{IMG:EB1911 Sheep - Hampshire Down Ram.jpg|HAMPSHIRE DOWN RAM}}

{{IMG:EB1911 Sheep - Oxford Down Ram.jpg|OXFORD DOWN RAM}}

{{IMG:EB1911 Sheep - Shropshire Ram.jpg|SHROPSHIRE RAM}}

BRITISH BREEDS OF SHEEP, from photographs by F. Babbage. The comparative sizes of the animals are indicated by the scale of reproduction
```

### Current body
```
Plate I.

{{IMG:EB1911 Sheep - Lincoln Longwool Ram.jpg|LINCOLN LONGWOOL RAM}}

{{IMG:EB1911 Sheep - Leicester Ram.jpg|LEICESTER RAM}}

{{IMG:EB1911 Sheep - Wensleydale Ram.jpg|WENSLEYDALE RAM}}

{{IMG:EB1911 Sheep - Devon Longwool Ram.jpg|DEVON LONGWOOL RAM}}

{{IMG:EB1911 Sheep - Southdown Ram.jpg|SOUTHDOWN RAM}}

{{IMG:EB1911 Sheep - Hampshire Down Ram.jpg|HAMPSHIRE DOWN RAM}}

{{IMG:EB1911 Sheep - Oxford Down Ram.jpg|OXFORD DOWN RAM}}

{{IMG:EB1911 Sheep - Shropshire Ram.jpg|SHROPSHIRE RAM}}

BRITISH BREEDS OF SHEEP, from photographs by F. Babbage. The comparative sizes of the animals are indicated by the scale of reproduction
```

---

## SHEEP — vol 24

**Article ID:** 4247207  
**Signature:** `wikitable depth=1 wt=1 ht=0 has_colspan`

### Source excerpt
```
{{sc|Plate II.}}

{|align="center" style="text-align: center"
|-
|[[Image:EB1911 Sheep - Suffolk Ram.jpg|x200px]]
|&emsp;
|[[Image:EB1911 Sheep - Ryeland Ram.jpg|x200px]]
|-
|{{uc|Suffolk Ram}}
|
|{{uc|Ryeland Ram}}
|-
|[[Image:EB1911 Sheep - Kent or Romney Marsh Ram.jpg|x200px]]
|
|[[Image:EB1911 Sheep - Dorset Horn Ram.jpg|x200px]]
|-
|{{uc|Kent or Romney Marsh Ram}}
|
|{{uc|Dorset Horn Ram}}
|-
|[[Image:EB1911 Sheep - Cheviot Ram.jpg|x200px]]
|
|[[Image:EB1911 Sheep - Cotswold Ram.jpg|x200px]]
|-
|{{uc|Cheviot Ram}}
|
|{{uc|Cotswold Ram}}
|-
|[[Image:EB1911 Sheep - Lonk Ram.jpg|x200px]]
|
|[[Image:EB1911 Sheep - Welsh Mountain Ram.jpg|x200px]]
|-
|{{uc|Lonk Ram}}
|
|{{uc|Welsh Mountain Ram}}
|-
|colspan="3"|
<div style="width: 750px; margin-left: auto; margin-right: auto">
BRITISH BREEDS OF SHEEP, from photographs by F. Babbage.  The comparative sizes of the animals are indicated by
the scale of reproduction.
</div>
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 8 | 8 |
| captioned       | 8 | 8 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **20** | **20** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **2** | **2** |
| header text     | 'Plate II.' | 'Plate II.' |
| footer text     | 'BRITISH BREEDS OF SHEEP, from photographs by F. Babbage. The comparative sizes of the animals are indicated by the scale' | 'BRITISH BREEDS OF SHEEP, from photographs by F. Babbage. The comparative sizes of the animals are indicated by the scale' |

**Verdict:** ✅ identical

### Baseline body
```
Plate II.

{{IMG:EB1911 Sheep - Suffolk Ram.jpg|SUFFOLK RAM}}

{{IMG:EB1911 Sheep - Ryeland Ram.jpg|RYELAND RAM}}

{{IMG:EB1911 Sheep - Kent or Romney Marsh Ram.jpg|KENT OR ROMNEY MARSH RAM}}

{{IMG:EB1911 Sheep - Dorset Horn Ram.jpg|DORSET HORN RAM}}

{{IMG:EB1911 Sheep - Cheviot Ram.jpg|CHEVIOT RAM}}

{{IMG:EB1911 Sheep - Cotswold Ram.jpg|COTSWOLD RAM}}

{{IMG:EB1911 Sheep - Lonk Ram.jpg|LONK RAM}}

{{IMG:EB1911 Sheep - Welsh Mountain Ram.jpg|WELSH MOUNTAIN RAM}}

BRITISH BREEDS OF SHEEP, from photographs by F. Babbage. The comparative sizes of the animals are indicated by the scale of reproduction
```

### Current body
```
Plate II.

{{IMG:EB1911 Sheep - Suffolk Ram.jpg|SUFFOLK RAM}}

{{IMG:EB1911 Sheep - Ryeland Ram.jpg|RYELAND RAM}}

{{IMG:EB1911 Sheep - Kent or Romney Marsh Ram.jpg|KENT OR ROMNEY MARSH RAM}}

{{IMG:EB1911 Sheep - Dorset Horn Ram.jpg|DORSET HORN RAM}}

{{IMG:EB1911 Sheep - Cheviot Ram.jpg|CHEVIOT RAM}}

{{IMG:EB1911 Sheep - Cotswold Ram.jpg|COTSWOLD RAM}}

{{IMG:EB1911 Sheep - Lonk Ram.jpg|LONK RAM}}

{{IMG:EB1911 Sheep - Welsh Mountain Ram.jpg|WELSH MOUNTAIN RAM}}

BRITISH BREEDS OF SHEEP, from photographs by F. Babbage. The comparative sizes of the animals are indicated by the scale of reproduction
```

---

## SHIP — vol 24

**Article ID:** 4247293  
**Signature:** `wikitable depth=2 wt=multi ht=0 has_colspan`

### Source excerpt
```
<!--- This page rotated right 90°. --->
{|{{Ts|ma|ac}}
|-
|{{Ts|ar}} colspan=3|{{sc|Plate I.}}
|- valign="bottom"
| rowspan="2" |
{|
|- valign="bottom"
| colspan="3" | [[File:EB1911 Ship, Antarctic Vessel, Terra Nova.jpg|420px]]
|- valign="top"
| {{em|4.4}}
| {{sc|Fig}}. 2.—Antarctic Vessel ''Terra Nova.''
| align="right" | <div style="text-align: right"><sup>(''Hopkins''.)</sup><!--- The photographer is an addition of 1922 edition of Encyclopaedia Britannica. ---></div>
|}
| rowspan="4" | &emsp;
| [[File:EB1911 Ship, Coasting Schooner.jpg|420px]]
|- valign="top"
| {{sc|Fig}}. 7.—Coasting Schooner.
|- valign="bottom"
| [[File:EB1911 Ship, Schooner, Helen W. Martin.jpg|420px]]
| [[File:EB1911 Ship, Victoria Regina.jpg|420px]]
|- valign="top"
| {{sc|Fig}}. 8.—Schooner ''Helen W. Martin.''
| {{sc|Fig}}. 9.—Ship ''Victoria Regina.''
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Ship, Antarctic Vessel, Terra Nova.jpg|Antarctic Vessel Terra Nova}}

{{IMG:EB1911 Ship, Coasting Schooner.jpg|Coasting Schooner}}

{{IMG:EB1911 Ship, Schooner, Helen W. Martin.jpg|Schooner Helen W. Martin}}

{{IMG:EB1911 Ship, Victoria Regina.jpg|Ship Victoria Regina}}
```

### Current body
```
{{IMG:EB1911 Ship, Antarctic Vessel, Terra Nova.jpg|Antarctic Vessel Terra Nova}}

{{IMG:EB1911 Ship, Coasting Schooner.jpg|Coasting Schooner}}

{{IMG:EB1911 Ship, Schooner, Helen W. Martin.jpg|Schooner Helen W. Martin}}

{{IMG:EB1911 Ship, Victoria Regina.jpg|Ship Victoria Regina}}
```

---

## SHIP — vol 24

**Article ID:** 4247294  
**Signature:** `wikitable depth=1 wt=1 ht=0 has_colspan`

### Source excerpt
```
<!--- This page rotated right 90°. --->
{| align="center" style="text-align: center"
|-
|{{Ts|ar}} colspan=3|{{sc|Plate II.}}
|- valign="bottom"
| [[File:EB1911 Ship, American Lake Steamer.jpg|420px]]
| rowspan="4" | &emsp;
| [[File:EB1911 Ship, Vessel with top-gallant forecastle, bridge house, and poop.jpg|420px]]
|- valign="top"
| {{sc|Fig}}. 13.—American Lake Steamer.
| {{sc|Fig}}. 14.—Vessel with top-gallant forecastle, bridge house, and poop.
|- valign="bottom"
| [[File:EB1911 Ship, Well-Decked Vessel.jpg|420px]]
| [[File:EB1911 Ship, Turret Steamer, Tulloch Moor.jpg|420px]]
|- valign="top"
| {{sc|Fig}}. 15.—Well-Decked Vessel.
| {{sc|Fig}}. 10.—Turret Steamer ''Tulloch Moor.''
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Ship, American Lake Steamer.jpg|American Lake Steamer}}

{{IMG:EB1911 Ship, Vessel with top-gallant forecastle, bridge house, and poop.jpg|Vessel with top-gallant forecastle, bridge house, and poop}}

{{IMG:EB1911 Ship, Well-Decked Vessel.jpg|Well-Decked Vessel}}

{{IMG:EB1911 Ship, Turret Steamer, Tulloch Moor.jpg|Turret Steamer Tulloch Moor}}
```

### Current body
```
{{IMG:EB1911 Ship, American Lake Steamer.jpg|American Lake Steamer}}

{{IMG:EB1911 Ship, Vessel with top-gallant forecastle, bridge house, and poop.jpg|Vessel with top-gallant forecastle, bridge house, and poop}}

{{IMG:EB1911 Ship, Well-Decked Vessel.jpg|Well-Decked Vessel}}

{{IMG:EB1911 Ship, Turret Steamer, Tulloch Moor.jpg|Turret Steamer Tulloch Moor}}
```

---

## SHIP — vol 24

**Article ID:** 4247295  
**Signature:** `wikitable depth=2 wt=multi ht=0 has_colspan`

### Source excerpt
```
{|{{Ts|ma|ac}}
|{{Ts|ar}}|{{sc|Plate III.}}
|- valign="bottom"
| [[File:EB1911 Ship, American River Steamer, Hendrick Hudson.jpg|720px]]
|- valign="top"
| {{sc|Fig}}. 18.—American River Steamer ''Hendrick Hudson.''
|-
|
{|{{Ts|ma|ac}}
|- valign="bottom"
| colspan=3 | [[File:EB1911 Ship, Cross-Channel Steamer, Prinses Juliana.jpg|720px]]
|- valign="top"
| {{em|7.2}}
| {{sc|Fig}}. 20.—Cross-Channel Steamer ''Prinses Juliana.''
| align="right" | <div style="text-align: right"><sup>(''Photo'', ''Frank & Son''.)</sup></div>
|}
|- valign="bottom"
| [[File:EB1911 Ship, Canadian Coasting Steamer, Prince Rupert.jpg|420px]]
|- valign="top"
| {{sc|Fig}}. 21.—Canadian Coasting Steamer ''Prince Rupert.''
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Ship, American River Steamer, Hendrick Hudson.jpg|American River Steamer Hendrick Hudson}}

{{IMG:EB1911 Ship, Cross-Channel Steamer, Prinses Juliana.jpg|Cross-Channel Steamer Prinses Juliana}}

{{IMG:EB1911 Ship, Canadian Coasting Steamer, Prince Rupert.jpg|Canadian Coasting Steamer Prince Rupert}}
```

### Current body
```
{{IMG:EB1911 Ship, American River Steamer, Hendrick Hudson.jpg|American River Steamer Hendrick Hudson}}

{{IMG:EB1911 Ship, Cross-Channel Steamer, Prinses Juliana.jpg|Cross-Channel Steamer Prinses Juliana}}

{{IMG:EB1911 Ship, Canadian Coasting Steamer, Prince Rupert.jpg|Canadian Coasting Steamer Prince Rupert}}
```

---

## SHIP — vol 24

**Article ID:** 4247296  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|{{Ts|ma|ac}}
|{{Ts|ar}}|{{sc|Plate IV.}}
|- valign="bottom"
| [[File:EB1911 Ship, Early Cunard Steamer, Persia.jpg|720px]]
|- valign="top"
| {{sc|Fig}}. 22.—Early Cunard Steamer ''Persia.''
|- valign="bottom"
| [[File:EB1911 Ship, Inmar Liner, City of Rome.jpg|720px]]
|- valign="top"
| {{sc|Fig}}. 23.—Inmar Liner ''City of Rome.''
|- valign="bottom"
| [[File:EB1911 Ship, Cunard Liner, Campania.jpg|720px]]
|- valign="top"
| {{sc|Fig}}. 24.—Cunard Liner ''Campania.''
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Ship, Early Cunard Steamer, Persia.jpg|Early Cunard Steamer Persia}}

{{IMG:EB1911 Ship, Inmar Liner, City of Rome.jpg|Inmar Liner City of Rome}}

{{IMG:EB1911 Ship, Cunard Liner, Campania.jpg|Cunard Liner Campania}}
```

### Current body
```
{{IMG:EB1911 Ship, Early Cunard Steamer, Persia.jpg|Early Cunard Steamer Persia}}

{{IMG:EB1911 Ship, Inmar Liner, City of Rome.jpg|Inmar Liner City of Rome}}

{{IMG:EB1911 Ship, Cunard Liner, Campania.jpg|Cunard Liner Campania}}
```

---

## SHIP — vol 24

**Article ID:** 4247297  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|{{Ts|ma|ac}}
|{{Ts|ar}}|{{sc|Plate V.}}
|- valign="bottom"
| [[File:EB1911 Ship, Hamburg-American Liner, Deutschland.jpg|720px]]
|- valign="top"
| {{sc|Fig}}. 25.—Hamburg-American Liner ''Deutschland.''
|- valign="bottom"
| [[File:EB1911 Ship, White Star Liner, Oceanic.jpg|720px]]
|- valign="top"
| {{sc|Fig}}. 30.—White Star Liner ''Oceanic.''
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Ship, Hamburg-American Liner, Deutschland.jpg|Hamburg-American Liner Deutschland}}

{{IMG:EB1911 Ship, White Star Liner, Oceanic.jpg|White Star Liner Oceanic}}
```

### Current body
```
{{IMG:EB1911 Ship, Hamburg-American Liner, Deutschland.jpg|Hamburg-American Liner Deutschland}}

{{IMG:EB1911 Ship, White Star Liner, Oceanic.jpg|White Star Liner Oceanic}}
```

---

## SHIP — vol 24

**Article ID:** 4247298  
**Signature:** `wikitable depth=2 wt=multi ht=0 has_colspan`

### Source excerpt
```
{|{{Ts|ma|ac}}
|{{Ts|ar}}|{{sc|Plate VI.}}
|- valign="bottom"
|
{| align="center" style="text-align: center"
|- valign="bottom"
| colspan="3" | [[File:EB1911 Ship, North German Lloid Liner, Kronprinzessin Cecilie.jpg|720px]]
|- valign="top"
| {{em|10.2}}
| {{sc|Fig}}. 26.—North German Lloyd Liner ''Kronprinzessin Cecilie.''
| align="right" | <div style="text-align: right"><sup>(''Photo'', ''Stuart'', ''Southampton''.)</sup></div>
|}
|- valign="bottom"
| [[File:EB1911 Ship, Cunard Liner, Mauretania, with Turbinia alongside.jpg|720px]]
|- valign="top"
| {{sc|Fig}}. 27.—Cunard Liner ''Mauretania'', with ''Turbinia'' alongside.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Ship, North German Lloid Liner, Kronprinzessin Cecilie.jpg|North German Lloyd Liner Kronprinzessin Cecilie}}

{{IMG:EB1911 Ship, Cunard Liner, Mauretania, with Turbinia alongside.jpg|Cunard Liner Mauretania, with Turbinia alongside}}
```

### Current body
```
{{IMG:EB1911 Ship, North German Lloid Liner, Kronprinzessin Cecilie.jpg|North German Lloyd Liner Kronprinzessin Cecilie}}

{{IMG:EB1911 Ship, Cunard Liner, Mauretania, with Turbinia alongside.jpg|Cunard Liner Mauretania, with Turbinia alongside}}
```

---

## SHIP — vol 24

**Article ID:** 4247299  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{{nop}}
{|{{Ts|ma|ac|width:760px}}
|{{Ts|ar}}|{{sc|Plate VII.}}
|- valign="bottom"
| [[File:EB1911 Ship, American Liner St. Paul.jpg|420px]]
|- valign="top"
| {{sc|Fig}}. 29.—American Liner ''St. Paul.''
|- valign="bottom"
| [[File:EB1911 Ship, White Star Liner, Adriatic.jpg|760px]]
|- valign="top"
| {{sc|Fig}}. 31.—White Star Liner ''Adriatic.''
|- valign="bottom"
|[[File:EB1911 Ship, Hamburg-American Liner, Kaiserin Auguste Victoria.jpg|610px]]
|-{{Ts|lh10}}
| {{Ts|ar|sm85|padding-right:6.5em}}|(''Stuart'', ''Southampton''.)
|-{{Ts|lh11}}
|{{sc|Fig}}. 32.—Hamburg-American Liner ''Kaiserin Auguste Victoria.''
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **7** | **7** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Ship, American Liner St. Paul.jpg|American Liner St. Paul}}

{{IMG:EB1911 Ship, White Star Liner, Adriatic.jpg|White Star Liner Adriatic}}

{{IMG:EB1911 Ship, Hamburg-American Liner, Kaiserin Auguste Victoria.jpg|(Stuart, Southampton.)}}

{{LEGEND:Hamburg-American Liner Kaiserin Auguste Victoria}LEGEND}
```

### Current body
```
{{IMG:EB1911 Ship, American Liner St. Paul.jpg|American Liner St. Paul}}

{{IMG:EB1911 Ship, White Star Liner, Adriatic.jpg|White Star Liner Adriatic}}

{{IMG:EB1911 Ship, Hamburg-American Liner, Kaiserin Auguste Victoria.jpg|(Stuart, Southampton.)}}

{{LEGEND:Hamburg-American Liner Kaiserin Auguste Victoria}LEGEND}
```

---

## SHIP — vol 24

**Article ID:** 4247300  
**Signature:** `wikitable depth=2 wt=multi ht=0 has_colspan`

### Source excerpt
```
{|{{Ts|ma|ac}}
|{{Ts|ar}}|{{sc|Plate VIII.}}
|-
|
{|{{Ts|ma|ac}}
|- valign="bottom"
| colspan="3" | [[File:EB1911 Ship, Royal Mail Steamer, Avon.jpg|720px]]
|- valign="top"
| {{em|3.3}}
| {{sc|Fig}}. 33.—Royal Mail Steamer ''Avon.''
| align="right" | <div style="text-align: right"><sup>(''Stuart''.)</sup></div>
|}
|-
|
{|{{Ts|ma|ac}}
|- valign="bottom"
| colspan="3" | [[File:EB1911 Ship, Union-Castle Liner, Kenilworth Castle.jpg|720px]]
|- valign="top"
| {{em|3.3}}
| {{sc|Fig}}. 34.—Union-Castle Liner ''Kenilworth Castle.''
| align="right" | <div style="text-align: right"><sup>(''Stuart''.)</sup></div>
|}
|- valign="bottom"
| [[File:EB1911 Ship, Orient Liner, Osterley.jpg|500px]]
|- valign="top"
| {{sc|Fig}}. 35.—Orient Liner ''Osterley''.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Ship, Royal Mail Steamer, Avon.jpg|Royal Mail Steamer Avon}}

{{IMG:EB1911 Ship, Union-Castle Liner, Kenilworth Castle.jpg|Union-Castle Liner Kenilworth Castle}}

{{IMG:EB1911 Ship, Orient Liner, Osterley.jpg|Orient Liner Osterley}}
```

### Current body
```
{{IMG:EB1911 Ship, Royal Mail Steamer, Avon.jpg|Royal Mail Steamer Avon}}

{{IMG:EB1911 Ship, Union-Castle Liner, Kenilworth Castle.jpg|Union-Castle Liner Kenilworth Castle}}

{{IMG:EB1911 Ship, Orient Liner, Osterley.jpg|Orient Liner Osterley}}
```

---

## SHIP — vol 24

**Article ID:** 4247301  
**Signature:** `wikitable depth=2 wt=multi ht=0 has_colspan`

### Source excerpt
```
{|{{Ts|ma|ac}}
|{{Ts|ar}}|{{sc|Plate}} IX.
|- valign="bottom"
| [[File:EB1911 Ship, River Volga Train Ferry.jpg|640px]]
|- valign="top"
| {{sc|Fig}}. 38.—River Volga Train Ferry.
|-
|
{|{{Ts|ma|ac}}
|- valign="bottom"
| colspan=3 | [[File:EB1911 Ship, Sea-going Train Ferry Steamer, Dröttning Victoria.jpg|720px]]
|- valign="top"
| {{em|5.5}}
| {{sc|Fig}}. 37.—Sea-going Train Ferry Steamer ''Dröttning Victoria''.
| align="right" | <div style="text-align: right"><sup>(''Frank & Sons''.)</sup></div>
|}
|- valign="bottom"
| [[File:EB1911 Ship, Ice-breaking Steamer, Ermack.jpg|640px]]
|- valign="top"
| {{sc|Fig}}. 39.—Ice-breaking Steamer ''Ermack''.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Ship, River Volga Train Ferry.jpg|River Volga Train Ferry}}

{{IMG:EB1911 Ship, Sea-going Train Ferry Steamer, Dröttning Victoria.jpg|Sea-going Train Ferry Steamer Dröttning Victoria}}

{{IMG:EB1911 Ship, Ice-breaking Steamer, Ermack.jpg|Ice-breaking Steamer Ermack}}
```

### Current body
```
{{IMG:EB1911 Ship, River Volga Train Ferry.jpg|River Volga Train Ferry}}

{{IMG:EB1911 Ship, Sea-going Train Ferry Steamer, Dröttning Victoria.jpg|Sea-going Train Ferry Steamer Dröttning Victoria}}

{{IMG:EB1911 Ship, Ice-breaking Steamer, Ermack.jpg|Ice-breaking Steamer Ermack}}
```

---

## SHIP — vol 24

**Article ID:** 4247302  
**Signature:** `wikitable depth=1 wt=1 ht=0 has_colspan`

### Source excerpt
```
<!--- This page rotated right 90°. --->
{|{{Ts|ma|ac}}
|{{Ts|ar}} colspan=3|{{sc|Plate}} X.
|- valign="bottom"
| [[File:EB1911 Ship, Excursion Steamer, Bournemouth Queen.jpg|420px]]
| &emsp;
| [[File:EB1911 Ship, Steam Fishing Vessel - Steel Screw Drifter, Three.jpg|420px]]
|- valign="top"
| {{sc|Fig}}. 17.—Excursion Steamer ''Bournemouth Queen''.
|
| {{sc|Fig}}. 41.—Steam Fishing Vessel—Steel Screw Drifter ''Three''.
|- valign="bottom"
| [[File:EB1911 Ship, Australian Motor Yacht, Bronzewing.jpg|420px]]
|
| [[File:EB1911 Ship, Motor-Driven Mail Boat, Manatee.jpg|420px]]
|- valign="top"
| {{sc|Fig}}. 45.—Australian Motor Yacht ''Bronzewing''.
|
| {{sc|Fig}}. 46.—Motor-Driven Mail Boat ''Manatee.''
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Ship, Excursion Steamer, Bournemouth Queen.jpg|Excursion Steamer Bournemouth Queen}}

{{IMG:EB1911 Ship, Steam Fishing Vessel - Steel Screw Drifter, Three.jpg|Steam Fishing Vessel—Steel Screw Drifter Three}}

{{IMG:EB1911 Ship, Australian Motor Yacht, Bronzewing.jpg|Australian Motor Yacht Bronzewing}}

{{IMG:EB1911 Ship, Motor-Driven Mail Boat, Manatee.jpg|Motor-Driven Mail Boat Manatee}}
```

### Current body
```
{{IMG:EB1911 Ship, Excursion Steamer, Bournemouth Queen.jpg|Excursion Steamer Bournemouth Queen}}

{{IMG:EB1911 Ship, Steam Fishing Vessel - Steel Screw Drifter, Three.jpg|Steam Fishing Vessel—Steel Screw Drifter Three}}

{{IMG:EB1911 Ship, Australian Motor Yacht, Bronzewing.jpg|Australian Motor Yacht Bronzewing}}

{{IMG:EB1911 Ship, Motor-Driven Mail Boat, Manatee.jpg|Motor-Driven Mail Boat Manatee}}
```

---

## SHIP — vol 24

**Article ID:** 4247303  
**Signature:** `wikitable depth=2 wt=multi ht=0 has_colspan`

### Source excerpt
```
{|{{Ts|ma|ac}}
|{{Ts|ar}}|{{sc|Plate}} XI.
|- valign="bottom"
| [[File:EB1911 Ship, Sailing Yacht with Auxiliary Steam Power, Sunbeam.jpg|400px]]
|- valign="top"
| {{sc|Fig}}. 42.—Sailing Yacht, with Auxiliary Steam Power, ''Sunbeam''.
|-
|
{|{{Ts|ma|ac}}
|- valign="bottom"
| colspan="3" | [[File:EB1911 Ship, Imperial German Steam Yacht, Hohenzollern.jpg|720px]]
|- valign="top"
| {{em|4.4}}
| {{sc|Fig}}. 43.—Imperial German Steam Yacht ''Hohenzollern.''
| align="right" | <div style="text-align: right"><sup>(''Photo'', ''West''.)</sup></div>
|}
|-
|
{|{{Ts|ma|ac}}
|- valign="bottom"
| colspan="3" | [[File:EB1911 Ship, The Royal Steam Yacht, Alexandra.jpg|720px]]
|- valign="top"
| {{em|3.3}}
| {{sc|Fig}}. 44.—The Royal Steam Yacht ''Alexandra.''
| align="right" | <div style="text-align: right"><sup>(''Hopkins''.)</sup></div>
|}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Ship, Sailing Yacht with Auxiliary Steam Power, Sunbeam.jpg|Sailing Yacht, with Auxiliary Steam Power, Sunbeam}}

{{IMG:EB1911 Ship, Imperial German Steam Yacht, Hohenzollern.jpg|Imperial German Steam Yacht Hohenzollern}}

{{IMG:EB1911 Ship, The Royal Steam Yacht, Alexandra.jpg|The Royal Steam Yacht Alexandra}}
```

### Current body
```
{{IMG:EB1911 Ship, Sailing Yacht with Auxiliary Steam Power, Sunbeam.jpg|Sailing Yacht, with Auxiliary Steam Power, Sunbeam}}

{{IMG:EB1911 Ship, Imperial German Steam Yacht, Hohenzollern.jpg|Imperial German Steam Yacht Hohenzollern}}

{{IMG:EB1911 Ship, The Royal Steam Yacht, Alexandra.jpg|The Royal Steam Yacht Alexandra}}
```

---

## SHIP — vol 24

**Article ID:** 4247304  
**Signature:** `wikitable depth=1 wt=1 ht=0 has_colspan`

### Source excerpt
```
<!--- This page rotated right 90°. --->
{|{{Ts|ma|ac}}
|{{Ts|ar}} colspan=3|{{sc|Plate}} XII.
|- valign="bottom"
| [[File:EB1911 Ship, H.M.S. Devastation.jpg|420px]]
| rowspan="4" | &emsp;
| [[File:EB1911 Ship, H.M.S. Inflexible.jpg|420px]]
|- valign="top"
| {{sc|Fig}}. 49.—H.M.S. ''Devastation.''
| {{sc|Fig}}. 50.—H.M.S. ''Inflexible.''
|- valign="bottom"
| [[File:EB1911 Ship, H.M.S. Camperdown.jpg|300px]]
| [[File:EB1911 Ship, H.M.S. Renown.jpg|300px]]
|- valign="top"
| {{sc|Fig}}. 53.—H.M.S. ''Camperdown.''
| {{sc|Fig}}. 55.—H.M.S. ''Renown.''
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Ship, H.M.S. Devastation.jpg|H.M.S. Devastation}}

{{IMG:EB1911 Ship, H.M.S. Inflexible.jpg|H.M.S. Inflexible}}

{{IMG:EB1911 Ship, H.M.S. Camperdown.jpg|H.M.S. Camperdown}}

{{IMG:EB1911 Ship, H.M.S. Renown.jpg|H.M.S. Renown}}
```

### Current body
```
{{IMG:EB1911 Ship, H.M.S. Devastation.jpg|H.M.S. Devastation}}

{{IMG:EB1911 Ship, H.M.S. Inflexible.jpg|H.M.S. Inflexible}}

{{IMG:EB1911 Ship, H.M.S. Camperdown.jpg|H.M.S. Camperdown}}

{{IMG:EB1911 Ship, H.M.S. Renown.jpg|H.M.S. Renown}}
```

---

## SHIP — vol 24

**Article ID:** 4247305  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|{{Ts|ma|ac}}
|{{Ts|ar}}|{{sc|Plate}} XIII.
|- 
| [[File:EB1911 Ship, H.M.S. Victory.jpg|720px]]
|-{{Ts|vtp}}
| {{sc|Fig}}. 1.—H.M.S. ''Victory''.<br><br>
|-
| [[File:EB1911 Ship, H.M.S. Dreadnought.jpg|720px]]
|-{{Ts|vtp}}
| {{sc|Fig}}. 64.—H.M.S. ''Dreadnought''.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Ship, H.M.S. Victory.jpg|H.M.S. Victory}}

{{IMG:EB1911 Ship, H.M.S. Dreadnought.jpg|H.M.S. Dreadnought}}
```

### Current body
```
{{IMG:EB1911 Ship, H.M.S. Victory.jpg|H.M.S. Victory}}

{{IMG:EB1911 Ship, H.M.S. Dreadnought.jpg|H.M.S. Dreadnought}}
```

---

## SHIP — vol 24

**Article ID:** 4247306  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|{{Ts|ma|ac}}
|{{Ts|ar}}|{{sc|Plate}} XIV.
|- valign="bottom"
| [[File:EB1911 Ship, H.M.S. Hannibal (Majestic Class).jpg|600px]]
|- valign="top"
| {{sc|Fig}}. 56.—H.M.S. ''Hannibal'' (Majestic Class).
|- valign="bottom"
| [[File:EB1911 Ship, H.M.S. King Edward VII.jpg|720px]]
|- valign="top"
| {{sc|Fig}}. 58.—H.M.S. ''King Edward VII''.
|- valign="bottom"
| [[File:EB1911 Ship, H.M.S. Agamemnon (Lord Nelson Class).jpg|720px]]
|- valign="top"
| {{sc|Fig}}. 60.—H.M.S. ''Agamemnon'' (Lord Nelson Class).
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Ship, H.M.S. Hannibal (Majestic Class).jpg|H.M.S. Hannibal (Majestic Class)}}

{{IMG:EB1911 Ship, H.M.S. King Edward VII.jpg|H.M.S. King Edward VII}}

{{IMG:EB1911 Ship, H.M.S. Agamemnon (Lord Nelson Class).jpg|H.M.S. Agamemnon (Lord Nelson Class)}}
```

### Current body
```
{{IMG:EB1911 Ship, H.M.S. Hannibal (Majestic Class).jpg|H.M.S. Hannibal (Majestic Class)}}

{{IMG:EB1911 Ship, H.M.S. King Edward VII.jpg|H.M.S. King Edward VII}}

{{IMG:EB1911 Ship, H.M.S. Agamemnon (Lord Nelson Class).jpg|H.M.S. Agamemnon (Lord Nelson Class)}}
```

---

## SHIP — vol 24

**Article ID:** 4247307  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|{{Ts|ma|ac}}
|{{Ts|ar}}|{{sc|Plate}} XV.
|- valign="bottom"
| [[File:EB1911 Ship, H.M.S. Bulwark.jpg|700px]]
|- valign="top"
| {{sc|Fig}}. 57.—H.M.S. ''Bulwark''.<br><br>
|- valign="bottom"
| [[File:EB1911 Ship, Norwegian, Norge.jpg|700px]]
|- valign="top"
| {{sc|Fig}}. 81.—Norwegian ''Norge''.<br><br>
|- valign="bottom"
| [[File:EB1911 Ship, Chilean, Chacabuco.jpg|750px]]
|- valign="top"
| {{sc|Fig}}. 98.—Chilean ''Chacabuco''.<br><br>
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Ship, H.M.S. Bulwark.jpg|H.M.S. Bulwark}}

{{IMG:EB1911 Ship, Norwegian, Norge.jpg|Norwegian Norge}}

{{IMG:EB1911 Ship, Chilean, Chacabuco.jpg|Chilean Chacabuco}}
```

### Current body
```
{{IMG:EB1911 Ship, H.M.S. Bulwark.jpg|H.M.S. Bulwark}}

{{IMG:EB1911 Ship, Norwegian, Norge.jpg|Norwegian Norge}}

{{IMG:EB1911 Ship, Chilean, Chacabuco.jpg|Chilean Chacabuco}}
```

---

## SHIP — vol 24

**Article ID:** 4247308  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|{{Ts|ma|ac}}
|{{Ts|ar}}|{{sc|Plate}} XVI.
|- valign="bottom"
| [[File:EB1911 Ship, U.S.A. Illinois.jpg|630px]]
|- valign="top"
| {{sc|Fig}}. 66.—U.S.A. ''Illinois.''<br><br>
|- valign="bottom"
| [[File:EB1911 Ship, German Kaiser Fredrich III.jpg|625px]]
|- valign="top"
| {{sc|Fig}}. 70.—German ''Kaiser Frederick III.''
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Ship, U.S.A. Illinois.jpg|U.S.A. Illinois}}

{{IMG:EB1911 Ship, German Kaiser Fredrich III.jpg|German Kaiser Frederick III}}
```

### Current body
```
{{IMG:EB1911 Ship, U.S.A. Illinois.jpg|U.S.A. Illinois}}

{{IMG:EB1911 Ship, German Kaiser Fredrich III.jpg|German Kaiser Frederick III}}
```

---

## SHIP — vol 24

**Article ID:** 4247309  
**Signature:** `wikitable depth=2 wt=multi ht=0 has_colspan`

### Source excerpt
```
<!--- This page rotated right 90°. --->
{|{{Ts|ma|ac}}
|{{Ts|ar}} colspan=3|{{sc|Plate}} XVII.
|-
|
{|{{Ts|ma|ac}}
|- valign="bottom"
| colspan="3" | [[File:EB1911 Ship, German Posen.jpg|420px]]
|- valign="top"
| {{em|4.4}}
| {{sc|Fig}}. 71.—German ''Posen.''
| align="right" | <div style="text-align: right"><sup>(''Photo'', ''Symons''.)</sup></div>
|}
| rowspan=3 | &emsp;
|
{|{{Ts|ma|ac}}
|- valign="bottom"
| colspan="3" | [[File:EB1911 Ship, Austrian Habsburg Class.jpg|420px]]
|- valign="top"
| {{em|4.4}}
| {{sc|Fig}}. 77.—Austrian Habsburg Class.
| align="right" | <div style="text-align: right"><sup>(''Photo'', ''Cribb''.)</sup></div>
|}
|-
| valign="bottom" | [[File:EB1911 Ship, Italian Regina Elena.jpg|420px]]
| rowspan="2" |
{| align="center" style="text-align: center"
|- valign="bottom"
| colspan="3" | [[File:EB1911 Ship, Japanese Kashima.jpg|420px]]
|- valign="top"
| {{em|4.4}}
| {{sc|Fig}}. 73.—Japanese ''Kashima.''
| align="right" | <div style="text-align: right"><sup>(''Photo'', ''Frank''.)</sup></div>
|}
|- valign="top"
| {{sc|Fig}}. 76.—Italian ''Regina Elena.''
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Ship, German Posen.jpg|German Posen}}

{{IMG:EB1911 Ship, Austrian Habsburg Class.jpg|Austrian Habsburg Class}}

{{IMG:EB1911 Ship, Italian Regina Elena.jpg|Japanese Kashima}}

{{IMG:EB1911 Ship, Japanese Kashima.jpg|Italian Regina Elena}}
```

### Current body
```
{{IMG:EB1911 Ship, German Posen.jpg|German Posen}}

{{IMG:EB1911 Ship, Austrian Habsburg Class.jpg|Austrian Habsburg Class}}

{{IMG:EB1911 Ship, Italian Regina Elena.jpg|Japanese Kashima}}

{{IMG:EB1911 Ship, Japanese Kashima.jpg|Italian Regina Elena}}
```

---

## SHIP — vol 24

**Article ID:** 4247310  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|{{Ts|ma|ac}}
|{{Ts|ar}}|{{sc|Plate}} XVIII.
|- valign="bottom"
| [[File:EB1911 Ship, Brazilian Minas Geraes.jpg|700px]]
|- valign="top"
| {{sc|Fig}}. 79.—Brazilian ''Minas Geraes''.{{dhr|90%}}
|- valign="bottom"
| [[File:EB1911 Ship, H.M.S. Triumph.jpg|720px]]
|- valign="top"
| {{sc|Fig}}. 69.—H.M.S. ''Triumph''.{{dhr|90%}}
|- valign="bottom"
| [[File:EB1911 Ship, U.S.A. Michigan.jpg|720px]]
|- valign="top"
| {{sc|Fig}}. 68.—U.S.A. ''Michigan''.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Ship, Brazilian Minas Geraes.jpg|Brazilian Minas Geraes}}

{{IMG:EB1911 Ship, H.M.S. Triumph.jpg|H.M.S. Triumph}}

{{IMG:EB1911 Ship, U.S.A. Michigan.jpg|U.S.A. Michigan}}
```

### Current body
```
{{IMG:EB1911 Ship, Brazilian Minas Geraes.jpg|Brazilian Minas Geraes}}

{{IMG:EB1911 Ship, H.M.S. Triumph.jpg|H.M.S. Triumph}}

{{IMG:EB1911 Ship, U.S.A. Michigan.jpg|U.S.A. Michigan}}
```

---

## SHIP — vol 24

**Article ID:** 4247311  
**Signature:** `wikitable depth=2 wt=multi ht=0 has_colspan`

### Source excerpt
```
<!--- This page rotated right 90°. --->
{|{{Ts|ma|ac}}
|{{Ts|ar}} colspan=3|{{sc|Plate}} XIX.
|- valign="bottom"
| [[File:EB1911 Ship, H.M.S. Edgar.jpg|420px]]
| rowspan="4" | &emsp;
| [[File:EB1911 Ship, H.M.S. Powerful.jpg|420px]]
|- valign="top"
| {{sc|Fig}}. 87.—H.M.S. ''Edgar''.<br><br>
| {{sc|Fig}}. 88.—H.M.S. ''Powerful''.
|-
| rowspan="2" |
{|{{Ts|ma|ac}}
|- valign="bottom"
| colspan="3" | [[File:EB1911 Ship, H.M.S. Attentive.jpg|420px]]
|- valign="top"
| {{em|4.4}}
| {{sc|Fig}}. 89.—H.M.S. ''Attentive''.
| align="right" | <div style="text-align: right"><sup>(''Photo'', ''West''.)</sup></div>
|}
| valign="bottom" | [[File:EB1911 Ship, H.M.S. Newcastle.jpg|420px]]
|- valign="top"
| {{sc|Fig}}. 90.—H.M.S. ''Newcastle''.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Ship, H.M.S. Edgar.jpg|H.M.S. Edgar}}

{{IMG:EB1911 Ship, H.M.S. Powerful.jpg|H.M.S. Powerful}}

{{IMG:EB1911 Ship, H.M.S. Attentive.jpg|H.M.S. Attentive}}

{{IMG:EB1911 Ship, H.M.S. Newcastle.jpg|H.M.S. Newcastle}}
```

### Current body
```
{{IMG:EB1911 Ship, H.M.S. Edgar.jpg|H.M.S. Edgar}}

{{IMG:EB1911 Ship, H.M.S. Powerful.jpg|H.M.S. Powerful}}

{{IMG:EB1911 Ship, H.M.S. Attentive.jpg|H.M.S. Attentive}}

{{IMG:EB1911 Ship, H.M.S. Newcastle.jpg|H.M.S. Newcastle}}
```

---

## SHIP — vol 24

**Article ID:** 4247312  
**Signature:** `wikitable depth=1 wt=1 ht=0 has_colspan`

### Source excerpt
```
{|{{Ts|ma|ac}}
|{{Ts|ar}} colspan=3|{{sc|Plate}} XX.
|- valign="bottom"
| [[File:EB1911 Ship, H.M.S. Hermes.jpg|400px]]
| rowspan="6" | &emsp;
| [[File:EB1911 Ship, H.M.S. Niobe.jpg|420px]]
|- valign="top"
| {{sc|Fig}}. 85.—H.M.S. ''Hermes''.<br><br>
| {{sc|Fig}}. 86.—H.M.S. ''Niobe''.
|- valign="bottom"
| [[File:EB1911 Ship, H.M.S. Sharpshooter.jpg|420px]]
| [[File:EB1911 Ship, H.M.S. Hazard.jpg|370px]]
|- valign="top"
| {{sc|Fig}}. 114.—H.M.S. ''Sharpshooter''.<br><br>
| {{sc|Fig}}. 115.—H.M.S. ''Hazard''.
|- valign="bottom"
| [[File:EB1911 Ship, H.M.S. Mosquito.jpg|420px]]
| [[File:EB1911 Ship, Nile Gunboat, Sultan.jpg|420px]]
|- valign="top"
| {{sc|Fig}}. 111.—H.M.S. ''Mosquito''.
| {{sc|Fig}}. 112.—Nile Gunboat ''Sultan''.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 6 | 6 |
| captioned       | 6 | 6 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **12** | **12** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Ship, H.M.S. Hermes.jpg|H.M.S. Hermes}}

{{IMG:EB1911 Ship, H.M.S. Niobe.jpg|H.M.S. Niobe}}

{{IMG:EB1911 Ship, H.M.S. Sharpshooter.jpg|H.M.S. Sharpshooter}}

{{IMG:EB1911 Ship, H.M.S. Hazard.jpg|H.M.S. Hazard}}

{{IMG:EB1911 Ship, H.M.S. Mosquito.jpg|H.M.S. Mosquito}}

{{IMG:EB1911 Ship, Nile Gunboat, Sultan.jpg|Nile Gunboat Sultan}}
```

### Current body
```
{{IMG:EB1911 Ship, H.M.S. Hermes.jpg|H.M.S. Hermes}}

{{IMG:EB1911 Ship, H.M.S. Niobe.jpg|H.M.S. Niobe}}

{{IMG:EB1911 Ship, H.M.S. Sharpshooter.jpg|H.M.S. Sharpshooter}}

{{IMG:EB1911 Ship, H.M.S. Hazard.jpg|H.M.S. Hazard}}

{{IMG:EB1911 Ship, H.M.S. Mosquito.jpg|H.M.S. Mosquito}}

{{IMG:EB1911 Ship, Nile Gunboat, Sultan.jpg|Nile Gunboat Sultan}}
```

---

## SHIP — vol 24

**Article ID:** 4247313  
**Signature:** `wikitable depth=1 wt=1 ht=0 has_colspan`

### Source excerpt
```
{|{{Ts|ma|ac}}
|{{Ts|ar}} colspan=3|{{sc|Plate}} XXI.
|-
|[[File:EB1911 Ship - Fig. 94 - H.M.S. Minotaur.png|450px]]
|{{em|1.5}}
|[[File:EB1911 Ship - Fig. 95 - H.M.S. Invincible.png|450px]]
|-
|{{Ts|pb1}}|{{sc|Fig}}. 94—H.M.S. ''Minotaur''.|| 
|{{Ts|pb1}}|{{sc|Fig}}. 95—H.M.S. ''Invincible''.
|-
|{{Ts|ar|vbm}}|[[File:EB1911 Ship - Fig. 83 - H.M.S. Cressy.png|430px]]
|
|[[File:EB1911 Ship - Fig. 93 - H.M.S. Cornwall.png|450px]]
|-
|&emsp;{{sc|Fig}}. 83—H.M.S. ''Cressy''.|| 
|{{sc|Fig}}. 93—H.M.S. ''Cornwall''.
|}
{{nop}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Ship - Fig. 94 - H.M.S. Minotaur.png|Fig . 94—H.M.S. Minotaur}}

{{IMG:EB1911 Ship - Fig. 95 - H.M.S. Invincible.png|Fig . 95—H.M.S. Invincible}}

{{IMG:EB1911 Ship - Fig. 83 - H.M.S. Cressy.png|Fig . 83—H.M.S. Cressy}}

{{IMG:EB1911 Ship - Fig. 93 - H.M.S. Cornwall.png|Fig . 93—H.M.S. Cornwall}}
```

### Current body
```
{{IMG:EB1911 Ship - Fig. 94 - H.M.S. Minotaur.png|Fig . 94—H.M.S. Minotaur}}

{{IMG:EB1911 Ship - Fig. 95 - H.M.S. Invincible.png|Fig . 95—H.M.S. Invincible}}

{{IMG:EB1911 Ship - Fig. 83 - H.M.S. Cressy.png|Fig . 83—H.M.S. Cressy}}

{{IMG:EB1911 Ship - Fig. 93 - H.M.S. Cornwall.png|Fig . 93—H.M.S. Cornwall}}
```

---

## SHIP — vol 24

**Article ID:** 4247314  
**Signature:** `wikitable depth=1 wt=1 ht=0 has_colspan`

### Source excerpt
```
{|{{Ts|ma|ac}}
|colspan=7 {{Ts|ar}}|{{sc|Plate}} XXII.
|-
|colspan=3|[[File:EB1911 Ship - Fig. 102 -German Von Der Tann.png|450px]]
|{{gap}}
|colspan=3|[[File:EB1911 Ship - Fig. 101 - German Blucher.png|450px]]
|-
|{{em|5}}||{{sc|Fig}}. 102—German ''Von-der-Tann''.||{{Ts|ar}}|<sup>(''Symons''.)</sup> 
|
|{{em|5}}||{{sc|Fig}}. 101—German ''Blücher''.||{{Ts|ar}}|<sup>(''Symons''.)</sup> 
|-
|&nbsp;
|-
|colspan=3|[[File:EB1911 Ship - Fig. 101 - German Victoria Luise.png|450px]]
|
|colspan=3 {{Ts|vbm}}|[[File:EB1911 Ship - Fig. 84 U.S.A. Brooklyn.png|434px]]
|-
|{{em|3}}||{{sc|Fig}}. 100—German ''Victoria Luise''.||{{Ts|ar}}|<sup>(''West''.) </sup>
|
|colspan=3|{{sc|Fig}}. 84—U.S.A. ''Brooklyn''.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 2 | 2 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **10** | **10** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Ship - Fig. 102 -German Von Der Tann.png|Fig . 102—German Von-der-Tann}}

{{IMG:EB1911 Ship - Fig. 101 - German Blucher.png|(Symons.)}}

{{IMG:EB1911 Ship - Fig. 101 - German Victoria Luise.png|Fig . 100—German Victoria Luise}}

{{IMG:EB1911 Ship - Fig. 84 U.S.A. Brooklyn.png|(West.)}}

{{LEGEND:Fig . 101—German Blücher}LEGEND}

{{LEGEND:Fig . 84—U.S.A. Brooklyn}LEGEND}
```

### Current body
```
{{IMG:EB1911 Ship - Fig. 102 -German Von Der Tann.png|Fig . 102—German Von-der-Tann}}

{{IMG:EB1911 Ship - Fig. 101 - German Blucher.png|(Symons.)}}

{{IMG:EB1911 Ship - Fig. 101 - German Victoria Luise.png|Fig . 100—German Victoria Luise}}

{{IMG:EB1911 Ship - Fig. 84 U.S.A. Brooklyn.png|(West.)}}

{{LEGEND:Fig . 101—German Blücher}LEGEND}

{{LEGEND:Fig . 84—U.S.A. Brooklyn}LEGEND}
```

---

## SHIP — vol 24

**Article ID:** 4247315  
**Signature:** `wikitable depth=1 wt=1 ht=0 has_colspan`

### Source excerpt
```
{|{{Ts|ma|ac}}
|{{Ts|ar}} colspan=3|{{sc|Plate}} XXIII.
|-
|[[File:EB1911 Ship - Fig. 104 -French Leon Gambetta.jpg|500px]]
|{{em|1.5}}
|{{Ts|vbm}}|[[File:EB1911 Ship - Fig. 103 -French Montcalm.jpg|500px]]
|-
|{{Ts|pb1}}|{{rh|{{em|3}}|{{sc|Fig}}. 104.—French ''Leon Gambetta''.|<sup>(''West''.)&thinsp;</sup>}}
| 
|{{Ts|pb1}}|{{sc|Fig}}. 103.—French ''Montcalm''.
|-
|{{Ts|vbm}}|[[File:EB1911 Ship - Fig. 99 - Japanese Idzumo.jpg|490px]]
|
|[[File:EB1911 Ship - Fig. 82 - Japanese Idzumi.jpg|500px]]
|-
|{{sc|Fig}}. 99.—Japanese ''Idzumo''.
| 
|{{sc|Fig}}. 82.—Japanese ''Idzumi'' (ex ''Esmeralda'').
|}
{{nop}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Ship - Fig. 104 -French Leon Gambetta.jpg|French Leon Gambetta. (West.)}}

{{IMG:EB1911 Ship - Fig. 103 -French Montcalm.jpg|French Montcalm}}

{{IMG:EB1911 Ship - Fig. 99 - Japanese Idzumo.jpg|Japanese Idzumo}}

{{IMG:EB1911 Ship - Fig. 82 - Japanese Idzumi.jpg|Japanese Idzumi (ex Esmeralda)}}
```

### Current body
```
{{IMG:EB1911 Ship - Fig. 104 -French Leon Gambetta.jpg|French Leon Gambetta. (West.)}}

{{IMG:EB1911 Ship - Fig. 103 -French Montcalm.jpg|French Montcalm}}

{{IMG:EB1911 Ship - Fig. 99 - Japanese Idzumo.jpg|Japanese Idzumo}}

{{IMG:EB1911 Ship - Fig. 82 - Japanese Idzumi.jpg|Japanese Idzumi (ex Esmeralda)}}
```

---

## SHIP — vol 24

**Article ID:** 4247316  
**Signature:** `wikitable depth=1 wt=1 ht=0 has_colspan`

### Source excerpt
```
{|{{Ts|ma|ac}}
|{{Ts|ar}} colspan=3|{{sc|Plate}} XXVI.
|-
|<br>[[File:EB1911 Ship Fig. 109 - HMS 'Thrush'.jpg|440px]]
|rowspan=2|{{em|1.5}}
|rowspan=2|[[File:EB1911 Ship Fig. 110 - HMS 'Dwarf'.jpg|450px]]
|-
|{{Ts|vtp}}|{{sc|Fig}}. 109.—H.M.S. ''Thrush''.<br>
|-
|
|
|{{Ts|pb15}}|{{sc|Fig}}. 110.—H.M.S. ''Dwarf''.
|-
|{{Ts|vbm}}|[[File:EB1911 Ship Fig. 116 - HMS 'Albatross'.jpg|450px]]
|
|[[File:EB1911 Ship Fig. 119 - 'Swift'.jpg|450px]]
|-
|{{sc|Fig}}. 116.—H.M.S. ''Albatross''.
| 
|{{sc|Fig}}. 119.—H.M.S. ''Swift''.
|}
{{nop}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Ship Fig. 109 - HMS 'Thrush'.jpg|H.M.S. Thrush}}

{{IMG:EB1911 Ship Fig. 110 - HMS 'Dwarf'.jpg|H.M.S. Dwarf}}

{{IMG:EB1911 Ship Fig. 116 - HMS 'Albatross'.jpg|H.M.S. Albatross}}

{{IMG:EB1911 Ship Fig. 119 - 'Swift'.jpg|H.M.S. Swift}}
```

### Current body
```
{{IMG:EB1911 Ship Fig. 109 - HMS 'Thrush'.jpg|H.M.S. Thrush}}

{{IMG:EB1911 Ship Fig. 110 - HMS 'Dwarf'.jpg|H.M.S. Dwarf}}

{{IMG:EB1911 Ship Fig. 116 - HMS 'Albatross'.jpg|H.M.S. Albatross}}

{{IMG:EB1911 Ship Fig. 119 - 'Swift'.jpg|H.M.S. Swift}}
```

---

## SHIPBUILDING, PLATE I — vol 24

**Article ID:** 4247318  
**Signature:** `center_template depth=0 wt=0 ht=0`

### Source excerpt
```
[[File:EB1911 - Shipbuilding - Fig 35.png|center|600px]]
{{center|{{sc|Fig}}. 35.—If length for 1,000 ton Ship be assumed 240 feet, then maximum ordinate of above curves represents—}}

279·9 square feet for Type 1
274·7 ” ” ” 2
269·0 " " " 3 and for other lengths, the number of square
265·5 " " " 4 feet varies inversely as the length.
262·1 " " " 5
255·4 " " " 6

[[File:EB1911 - Shipbuilding - Fig 36.png|center|300px]]
{{center|{{sc|Fig}}. 36.—Group B. Comparison of Types.}}

Type 1.

" 3.

" 6.
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | 'Type 1. " 3. " 6' | 'Type 1. " 3. " 6' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Shipbuilding - Fig 35.png|If length for 1,000 ton Ship be assumed 240 feet, then maximum ordinate of above curves represents—}}

{{IMG:EB1911 - Shipbuilding - Fig 36.png|Group B. Comparison of Types}}

Type 1. " 3. " 6
```

### Current body
```
{{IMG:EB1911 - Shipbuilding - Fig 35.png|If length for 1,000 ton Ship be assumed 240 feet, then maximum ordinate of above curves represents—}}

{{IMG:EB1911 - Shipbuilding - Fig 36.png|Group B. Comparison of Types}}

Type 1. " 3. " 6
```

---

## SHIPBUILDING, PLATE II — vol 24

**Article ID:** 4247319  
**Signature:** `center_template depth=0 wt=0 ht=0`

### Source excerpt
```
[[File:EB1911 - Shipbuilding - Fig 37.png|center|400px|Fig. 37.]]
{{center|{{sc|Fig}}. 37.}}


[[File:EB1911 - Shipbuilding - Fig 38.png|center|400px|Fig. 38.]]
{{center|{{sc|Fig}}. 38.—Curves of Surface Friction Correction.}}

[[File:EB1911 - Shipbuilding - Fig 39.png|center|400px|Fig. 39.]]
{{center|{{sc|Fig}}. 39.—Estimated Curve of E. H. P. for Vessel 320′ x 13′ x 2,135 Tons.}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Shipbuilding - Fig 37.png|Fig . 37}}

{{IMG:EB1911 - Shipbuilding - Fig 38.png|Curves of Surface Friction Correction}}

{{IMG:EB1911 - Shipbuilding - Fig 39.png|Estimated Curve of E. H. P. for Vessel 320′ x 13′ x 2,135 Tons}}
```

### Current body
```
{{IMG:EB1911 - Shipbuilding - Fig 37.png|Fig . 37}}

{{IMG:EB1911 - Shipbuilding - Fig 38.png|Curves of Surface Friction Correction}}

{{IMG:EB1911 - Shipbuilding - Fig 39.png|Estimated Curve of E. H. P. for Vessel 320′ x 13′ x 2,135 Tons}}
```

---

## SHIPBUILDING, PLATE III — vol 24

**Article ID:** 4247320  
**Signature:** `center_template depth=0 wt=0 ht=0`

### Source excerpt
```
[[File:EB1911 - Shipbuilding - Fig 40.png|center|400px]]
{{center|Fig. 40.—Curves of E.H.P. for a 1,000-ton Ship.<br>Group "A."<br>Type 1. Block Coefficient ·495.}}


[[File:EB1911 - Shipbuilding - Fig 41.png|center|400px]]
{{center|Fig. 41.—Curves of E.H.P. for a 1,000-ton Ship.<br>Group "A."<br>Type 2. Block Coefficient ·505.}}


[[File:EB1911 - Shipbuilding - Fig 42.png|center|400px]]
{{center|Fig. 42.—Curves of E.H.P. for a 1,000-ton Ship.<br>Group "A."<br>Type 3. Block Coefficient ·516.}}
 

[[File:EB1911 - Shipbuilding - Fig 43.png|center|400px]]
{{center|Fig. 43.—Curves of E.H.P. for a 1,000-ton Ship.<br>Group "A."<br>Type 3. Block Coefficient ·522.}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Shipbuilding - Fig 40.png|Curves of E.H.P. for a 1,000-ton Ship. Group "A." Type 1. Block Coefficient ·495}}

{{IMG:EB1911 - Shipbuilding - Fig 41.png|Curves of E.H.P. for a 1,000-ton Ship. Group "A." Type 2. Block Coefficient ·505}}

{{IMG:EB1911 - Shipbuilding - Fig 42.png|Curves of E.H.P. for a 1,000-ton Ship. Group "A." Type 3. Block Coefficient ·516}}

{{IMG:EB1911 - Shipbuilding - Fig 43.png|Curves of E.H.P. for a 1,000-ton Ship. Group "A." Type 3. Block Coefficient ·522}}
```

### Current body
```
{{IMG:EB1911 - Shipbuilding - Fig 40.png|Curves of E.H.P. for a 1,000-ton Ship. Group "A." Type 1. Block Coefficient ·495}}

{{IMG:EB1911 - Shipbuilding - Fig 41.png|Curves of E.H.P. for a 1,000-ton Ship. Group "A." Type 2. Block Coefficient ·505}}

{{IMG:EB1911 - Shipbuilding - Fig 42.png|Curves of E.H.P. for a 1,000-ton Ship. Group "A." Type 3. Block Coefficient ·516}}

{{IMG:EB1911 - Shipbuilding - Fig 43.png|Curves of E.H.P. for a 1,000-ton Ship. Group "A." Type 3. Block Coefficient ·522}}
```

---

## SHIPBUILDING, PLATE IV — vol 24

**Article ID:** 4247321  
**Signature:** `center_template depth=0 wt=0 ht=0`

### Source excerpt
```
[[File:EB1911 - Shipbuilding - Fig 44.png|center|400px]]
{{center|{{sc|Fig}}. 44.—Curves of E.H.P. for 1,000-ton Ship.<br>
Group “A.” Type 5. Block Coefficient ·529.}}


[[File:EB1911 - Shipbuilding - Fig 45.png|center|400px]]
{{center|{{sc|Fig}}. 45.—Curves of E.H.P. for 1,000-ton Ship.<br>
Group “A.” Type 6. Block Coefficient ·542.}}


[[File:EB1911 - Shipbuilding - Fig 46.png|center|400px]]
{{center|{{sc|Fig}}. 46.—Curves of E.H.P. for 1,000-ton Ship.<br>
Group “B.” Type 1. Block Coefficient ·495.}}

[[File:EB1911 - Shipbuilding - Fig 47.png|center|400px]]
{{center|{{sc|Fig}}. 47.—Curves of E.H.P. for 1,000-ton Ship.<br>
Group “B.” Type 2. Block Coefficient ·505.}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Shipbuilding - Fig 44.png|Curves of E.H.P. for 1,000-ton Ship. Group “A.” Type 5. Block Coefficient ·529}}

{{IMG:EB1911 - Shipbuilding - Fig 45.png|Curves of E.H.P. for 1,000-ton Ship. Group “A.” Type 6. Block Coefficient ·542}}

{{IMG:EB1911 - Shipbuilding - Fig 46.png|Curves of E.H.P. for 1,000-ton Ship. Group “B.” Type 1. Block Coefficient ·495}}

{{IMG:EB1911 - Shipbuilding - Fig 47.png|Curves of E.H.P. for 1,000-ton Ship. Group “B.” Type 2. Block Coefficient ·505}}
```

### Current body
```
{{IMG:EB1911 - Shipbuilding - Fig 44.png|Curves of E.H.P. for 1,000-ton Ship. Group “A.” Type 5. Block Coefficient ·529}}

{{IMG:EB1911 - Shipbuilding - Fig 45.png|Curves of E.H.P. for 1,000-ton Ship. Group “A.” Type 6. Block Coefficient ·542}}

{{IMG:EB1911 - Shipbuilding - Fig 46.png|Curves of E.H.P. for 1,000-ton Ship. Group “B.” Type 1. Block Coefficient ·495}}

{{IMG:EB1911 - Shipbuilding - Fig 47.png|Curves of E.H.P. for 1,000-ton Ship. Group “B.” Type 2. Block Coefficient ·505}}
```

---

## SHIPBUILDING, PLATE V — vol 24

**Article ID:** 4247322  
**Signature:** `center_template depth=0 wt=0 ht=0`

### Source excerpt
```
[[File:EB1911 - Shipbuilding - Fig 48.png|center|400px]]
{{center|{{sc|Fig}}. 48.—Curves of E.H.P. for a 1,000-ton Ship.<br>
Group "B."<br>
Type 3. Block Coefficient ·516.}} 


[[File:EB1911 - Shipbuilding - Fig 49.png|center|400px]]
{{center|{{sc|Fig}}. 49.—Curves of E.H.P. for a 1,000-ton Ship.<br>
Group "B."<br>
Type 4. Block Coefficient ·522.}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Shipbuilding - Fig 48.png|Curves of E.H.P. for a 1,000-ton Ship. Group "B." Type 3. Block Coefficient ·516}}

{{IMG:EB1911 - Shipbuilding - Fig 49.png|Curves of E.H.P. for a 1,000-ton Ship. Group "B." Type 4. Block Coefficient ·522}}
```

### Current body
```
{{IMG:EB1911 - Shipbuilding - Fig 48.png|Curves of E.H.P. for a 1,000-ton Ship. Group "B." Type 3. Block Coefficient ·516}}

{{IMG:EB1911 - Shipbuilding - Fig 49.png|Curves of E.H.P. for a 1,000-ton Ship. Group "B." Type 4. Block Coefficient ·522}}
```

---

## SHIPBUILDING, PLATE VI — vol 24

**Article ID:** 4247323  
**Signature:** `center_template depth=0 wt=0 ht=0`

### Source excerpt
```
[[File:EB1911 - Shipbuilding - Fig 50.png|center|400px]]
{{center|{{sc|Fig}}. 50.—Curves of E.H.P. for 1,000-ton Ship.<br>
Group "B." Type 5. Block Coefficient ·529.}}


[[File:EB1911 - Shipbuilding - Fig 51.png|center|400px]]
{{center|{{sc|Fig}}. 51.—Curves of E.H.P. for 1,000-ton Ship.<br>
Group “B.” Type 6. Block Coefficient ·542.}}


[[File:EB1911 - Shipbuilding - Fig 52.png|center|400px]]
{{center|{{sc|Fig}}. 52.—Speed trials of H.M. Torpedo Boat Destroyer “Cossack.” At Maplin and Skelmorlie. Displacement 836 tons.}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Shipbuilding - Fig 50.png|Curves of E.H.P. for 1,000-ton Ship. Group "B." Type 5. Block Coefficient ·529}}

{{IMG:EB1911 - Shipbuilding - Fig 51.png|Curves of E.H.P. for 1,000-ton Ship. Group “B.” Type 6. Block Coefficient ·542}}

{{IMG:EB1911 - Shipbuilding - Fig 52.png|Speed trials of H.M. Torpedo Boat Destroyer “Cossack.” At Maplin and Skelmorlie. Displacement 836 tons}}
```

### Current body
```
{{IMG:EB1911 - Shipbuilding - Fig 50.png|Curves of E.H.P. for 1,000-ton Ship. Group "B." Type 5. Block Coefficient ·529}}

{{IMG:EB1911 - Shipbuilding - Fig 51.png|Curves of E.H.P. for 1,000-ton Ship. Group “B.” Type 6. Block Coefficient ·542}}

{{IMG:EB1911 - Shipbuilding - Fig 52.png|Speed trials of H.M. Torpedo Boat Destroyer “Cossack.” At Maplin and Skelmorlie. Displacement 836 tons}}
```

---

## PLATE (VOL. 24, P. 1023), PLATE VII — vol 24

**Article ID:** 4247324  
**Signature:** `center_template depth=0 wt=0 ht=0`

### Source excerpt
```
[[File:EB1911 - Shipbuilding - Fig 62.png|center|400px]]
{{center|{{sc|Fig}}. 62.}}

{{block center|A, A, A, Curve described by pivoting point.<br>
B, B, B, Curve described by centre of gravity.<br>
C, C, C, Curve described by outer edge of stern.<br>
D, Position of ship’s centre of gravity when helm commenced to
move over.<br>
E, Position of ship’s centre of gravity when helm had reached 32′.<br>
F, Position of ship’s centre of gravity when vessel had turned
through 90°. Time from D, 49½ sec.<br>
G, Position of ship’s centre of gravity when vessel had turned
through 180°. Time from D, 1 min. 20 sec.}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **2** | **2** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Shipbuilding - Fig 62.png|A, A, A, Curve described by pivoting point. B, B, B, Curve described by centre of gravity. C, C, C, Curve described by outer edge of stern. D, Position of ship’s centre of gravity when helm commenced to move over. E, Position of ship’s centre of gravity when helm had reached 32′. F, Position of ship’s centre of gravity when vessel had turned through 90°. Time from D, 49½ sec. G, Position of ship’s centre of gravity when vessel had turned through 180°. Time from D, 1 min. 20 sec}}
```

### Current body
```
{{IMG:EB1911 - Shipbuilding - Fig 62.png|A, A, A, Curve described by pivoting point. B, B, B, Curve described by centre of gravity. C, C, C, Curve described by outer edge of stern. D, Position of ship’s centre of gravity when helm commenced to move over. E, Position of ship’s centre of gravity when helm had reached 32′. F, Position of ship’s centre of gravity when vessel had turned through 90°. Time from D, 49½ sec. G, Position of ship’s centre of gravity when vessel had turned through 180°. Time from D, 1 min. 20 sec}}
```

---

## SHIPBUILDING, PLATE VIII — vol 24

**Article ID:** 4247325  
**Signature:** `center_template depth=0 wt=0 ht=0`

### Source excerpt
```
[[File:EB1911 - Shipbuilding - Fig 80.jpg|center|400px]]
{{center|{{sc|Fig}}. 80.<br>
Gantry at Messrs Cramps' Shipbuilding Yard, Philadelphia.}}


[[File:EB1911 - Shipbuilding - Fig 81.jpg|center|400px]]
{{center|{{sc|Fig}}. 81.<br>
Gantry at Messrs Harland & Wolff's Shipbuilding Yard, Belfast.}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | "ig . 81. Gantry at Messrs Harland & Wolff's Shipbuilding Yard, Belfast" | "ig . 81. Gantry at Messrs Harland & Wolff's Shipbuilding Yard, Belfast" |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Shipbuilding - Fig 80.jpg|Fig . 80}}

{{IMG:EB1911 - Shipbuilding - Fig 81.jpg|Fig . 81}}

ig . 81. Gantry at Messrs Harland & Wolff's Shipbuilding Yard, Belfast
```

### Current body
```
{{IMG:EB1911 - Shipbuilding - Fig 80.jpg|Fig . 80}}

{{IMG:EB1911 - Shipbuilding - Fig 81.jpg|Fig . 81}}

ig . 81. Gantry at Messrs Harland & Wolff's Shipbuilding Yard, Belfast
```

---

## SHIPBUILDING, PLATE IX — vol 24

**Article ID:** 4247326  
**Signature:** `other depth=0 wt=0 ht=0 no_image`

### Source excerpt
```
{{raw image|EB1911 - Volume 24.djvu/1037}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 0 | 0 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **1** | **1** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:djvu_vol24_page1037.jpg}}
```

### Current body
```
{{IMG:djvu_vol24_page1037.jpg}}
```

---

## PLATE (VOL. 24, P. 1040), PLATE X — vol 24

**Article ID:** 4247327  
**Signature:** `other depth=0 wt=0 ht=0 no_image`

### Source excerpt
```
{{raw image|EB1911 - Volume 24.djvu/1040}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 0 | 0 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **1** | **1** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:djvu_vol24_page1040.jpg}}
```

### Current body
```
{{IMG:djvu_vol24_page1040.jpg}}
```

---

## PLATE (VOL. 24, P. 1043), PLATE XI — vol 24

**Article ID:** 4247328  
**Signature:** `bare_image depth=0 wt=0 ht=0`

### Source excerpt
```
[[File:EB1911 - Shipbuilding - Plate XI.png|center|400px]]
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 0 | 0 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **1** | **1** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Shipbuilding - Plate XI.png}}
```

### Current body
```
{{IMG:EB1911 - Shipbuilding - Plate XI.png}}
```

---

## PLATE (VOL. 24, P. 1046), PLATE — vol 24

**Article ID:** 4247329  
**Signature:** `bare_image depth=0 wt=0 ht=0`

### Source excerpt
```
[[File:EB1911 - Shipbuilding - Plate XII.png|center|400px]]
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 0 | 0 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **1** | **1** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Shipbuilding - Plate XII.png}}
```

### Current body
```
{{IMG:EB1911 - Shipbuilding - Plate XII.png}}
```

---

## SHIPBUILDING, PLATE XIII — vol 24

**Article ID:** 4247330  
**Signature:** `center_template depth=0 wt=0 ht=0 toplegend`

### Source excerpt
```
{{center|{{sc|Fig. 98.—Midship Section of H.M.S. "Lord Nelson."}}}}
[[File:EB1911 - Shipbuilding - Plate XIII.png|center|400px]]
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **2** | **2** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Shipbuilding - Plate XIII.png|Midship Section of H.M.S. "Lord Nelson."}}
```

### Current body
```
{{IMG:EB1911 - Shipbuilding - Plate XIII.png|Midship Section of H.M.S. "Lord Nelson."}}
```

---

## PLATE (VOL. 24, P. 1056), PLATE XIV — vol 24

**Article ID:** 4247331  
**Signature:** `other depth=0 wt=0 ht=0 no_image`

### Source excerpt
```
{{raw image|EB1911 - Volume 24.djvu/1056}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 0 | 0 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **1** | **1** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:djvu_vol24_page1056.jpg}}
```

### Current body
```
{{IMG:djvu_vol24_page1056.jpg}}
```

---

## SIGHTS — vol 25

**Article ID:** 4217537  
**Signature:** `center_template depth=0 wt=0 ht=0 toplegend`

### Source excerpt
```
[[File:EB1911 - Sights - Fig 9.jpg|center|400px]]
{{center|{{sc|Fig}}. 9.—SCOTT'S TELESCOPIC SIGHT.}}
{{smaller|By permission of the Controller, H.M. Stationery Office.}}

[[File:EB1911 - Sights - Fig 14.jpg|center|400px]]
{{smaller|''Photo, Friedr. Krupp, A.G.''}}
{{center|{{sc|Fig}}. 14.—KRUPP INDEPENDENT LINE OF SIGHT.}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Sights - Fig 9.jpg|SCOTT'S TELESCOPIC SIGHT. By permission of the Controller, H.M. Stationery Office}}

{{IMG:EB1911 - Sights - Fig 14.jpg|KRUPP INDEPENDENT LINE OF SIGHT}}
```

### Current body
```
{{IMG:EB1911 - Sights - Fig 9.jpg|SCOTT'S TELESCOPIC SIGHT. By permission of the Controller, H.M. Stationery Office}}

{{IMG:EB1911 - Sights - Fig 14.jpg|KRUPP INDEPENDENT LINE OF SIGHT}}
```

---

## Steel Construction, PLATE I — vol 25

**Article ID:** 4218397  
**Signature:** `other depth=0 wt=0 ht=0 no_image`

### Source excerpt
```
{{FI
| file = EB1911 Steel Construction - Fig. 1.jpg
| width = 700px
| caption = {{sc|Fig.}} 1.—THE MORNING POST BUILDING, LONDON.<br>
{{float left|{{smaller|Mewes & Davis, Architects.}}}}{{float right|{{smaller|Waring White Building Co. Ltd., Contractors.}}}}{{clear}}
}}

{{dhr}}

{{FI
| file = EB1911 Steel Construction - Fig. 2.jpg
| width = 700px
| caption ={{sc|Fig.}} 2.—THE FLATIRON BUILDING, NEW YORK CITY.<br>
{{float left|{{smaller|D. H. Burnham & Co., Architects.}}}}{{float right|{{smaller|Geo. A. Fuller & Co., Contractors.}}}}{{clear}}
}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 0 | 0 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **2** | **2** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Steel Construction - Fig. 1.jpg}}

{{IMG:EB1911 Steel Construction - Fig. 2.jpg}}
```

### Current body
```
{{IMG:EB1911 Steel Construction - Fig. 1.jpg}}

{{IMG:EB1911 Steel Construction - Fig. 2.jpg}}
```

---

## Steel Construction, PLATE II — vol 25

**Article ID:** 4218398  
**Signature:** `center_template depth=0 wt=0 ht=0 no_image`

### Source excerpt
```
{{FI
| file = EB1911 Steel Construction - Fig. 3.jpg
| width = 400px
| caption = {{sc|Fig.}} 3.—LAND TITLE BUILDING, PHILADELPHIA.<br>
{{float left|{{smaller|D. H. Burnham & Co., Architects.}}}}{{float right|{{smaller|Charles McCaul & Co., Contractors.}}}}{{clear}}
}}

{{dhr}}

{{FI
| file = EB1911 Steel Construction - Fig. 4.jpg
| width = 400px
| caption ={{sc|Fig.}} 4.—FLATIRON BUILDING, NEW YORK CITY.<br>
{{float left|{{smaller|D. H. Burnham & Co., Architects.}}}}{{float right|{{smaller|Geo. A. Fuller Co., Contractors.}}}}{{clear}}
{{center|{{smaller|(For illustration of finished building, see {{EB1911 article link|Architecture}}, Fig. 131, Plate XV.)}}}}
}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 0 | 0 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **2** | **2** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Steel Construction - Fig. 3.jpg}}

{{IMG:EB1911 Steel Construction - Fig. 4.jpg}}
```

### Current body
```
{{IMG:EB1911 Steel Construction - Fig. 3.jpg}}

{{IMG:EB1911 Steel Construction - Fig. 4.jpg}}
```

---

## STONEHENGE — vol 25

**Article ID:** 4218584  
**Signature:** `center_template depth=0 wt=0 ht=0 toplegend`

### Source excerpt
```
[[File:EB1911 - Stonehenge - Plate a.jpg|center|400px|STONEHENGE: FROM THE EAST.]]
{{center|STONEHENGE: FROM THE EAST.}}
{{smaller|''Photo, F. Frith & Co.''}}

[[File:EB1911 - Stonehenge - Plate b.jpg|center|400px|STONEHENGE: FROM THE WEST.]]
{{center|STONEHENGE: FROM THE WEST.}}
{{smaller|''Photo, F. Frith & Co.''}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | 'Photo, F. Frith & Co' | 'Photo, F. Frith & Co' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Stonehenge - Plate a.jpg|STONEHENGE: FROM THE EAST}}

{{IMG:EB1911 - Stonehenge - Plate b.jpg|STONEHENGE: FROM THE WEST}}

Photo, F. Frith & Co
```

### Current body
```
{{IMG:EB1911 - Stonehenge - Plate a.jpg|STONEHENGE: FROM THE EAST}}

{{IMG:EB1911 - Stonehenge - Plate b.jpg|STONEHENGE: FROM THE WEST}}

Photo, F. Frith & Co
```

---

## STONE MONUMENTS, PLATE — vol 25

**Article ID:** 4218585  
**Signature:** `other depth=0 wt=0 ht=0 no_image`

### Source excerpt
```
{{raw image|EB1911 - Volume 25.djvu/990}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 0 | 0 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **1** | **1** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:djvu_vol25_page0990.jpg}}
```

### Current body
```
{{IMG:djvu_vol25_page0990.jpg}}
```

---

## SUN, PLATE I — vol 26

**Article ID:** 4218823  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|{{ts|mc|ac}}
|-
|[[File:EB1911 - Sun - Plate 1a.png|400px]] ||[[File:EB1911 - Sun - Plate 1b.png|400px]]
|-
|(1) 1905, June 25d. 4h. 16m. 15s. ||(2) 1905, June 25d. 4h. 17m. 15s.
|-
|[[File:EB1911 - Sun - Plate 1c.png|400px]] ||[[File:EB1911 - Sun - Plate 1d.png|400px]]
|-
|(3) 1905, June 25d. 4h. 17m. 40s. ||(4) 1905, June 25d. 4h. 19m. 0s.
|}

{{center|ENLARGED PHOTOGRAPHS OF THE SOLAR SURFACE, Taken by M. A. Hansky at the Observatory of Pulkowa<br /> (1905, June 25), at intervals from 25s. to 80s.}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **10** | **10** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | 'ENLARGED PHOTOGRAPHS OF THE SOLAR SURFACE, Taken by M. A. Hansky at the Observatory of Pulkowa (1905, June 25), at inter' | 'ENLARGED PHOTOGRAPHS OF THE SOLAR SURFACE, Taken by M. A. Hansky at the Observatory of Pulkowa (1905, June 25), at inter' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Sun - Plate 1a.png|(1) 1905, June 25d. 4h. 16m. 15s}}

{{IMG:EB1911 - Sun - Plate 1b.png|(2) 1905, June 25d. 4h. 17m. 15s}}

{{IMG:EB1911 - Sun - Plate 1c.png|(3) 1905, June 25d. 4h. 17m. 40s}}

{{IMG:EB1911 - Sun - Plate 1d.png|(4) 1905, June 25d. 4h. 19m. 0s}}

ENLARGED PHOTOGRAPHS OF THE SOLAR SURFACE, Taken by M. A. Hansky at the Observatory of Pulkowa (1905, June 25), at intervals from 25s. to 80s
```

### Current body
```
{{IMG:EB1911 - Sun - Plate 1a.png|(1) 1905, June 25d. 4h. 16m. 15s}}

{{IMG:EB1911 - Sun - Plate 1b.png|(2) 1905, June 25d. 4h. 17m. 15s}}

{{IMG:EB1911 - Sun - Plate 1c.png|(3) 1905, June 25d. 4h. 17m. 40s}}

{{IMG:EB1911 - Sun - Plate 1d.png|(4) 1905, June 25d. 4h. 19m. 0s}}

ENLARGED PHOTOGRAPHS OF THE SOLAR SURFACE, Taken by M. A. Hansky at the Observatory of Pulkowa (1905, June 25), at intervals from 25s. to 80s
```

---

## SUN, PLATE II — vol 26

**Article ID:** 4218824  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{|{{ts|mc|ac}}
|-
|[[File:EB1911 - Sun - Plate 2a.png|400px]] ||[[File:EB1911 - Sun - Plate 2b.png|400px]]
|-
|1905, Jan. 30d. 12h. 8m. 27s. ||1905, Jan. 31d. 11h. 17m. 27s.
|-
|[[File:EB1911 - Sun - Plate 2c.png|400px]] ||[[File:EB1911 - Sun - Plate 2d.png|400px]]
|-
|1905, Feb. 2d. 10h. 50m. 28s. ||1905, Feb. 8d. 13h. 3m. 5s.
|}

{{center|PHOTOGRAPHS OF THE SUN, TAKEN AT THE ROYAL OBSERVATORY, GREENWICH.}}

{{center|{{smaller|Observer: E. W. Maunder. Instrument, Thompson Photoheliograph. Focal Length, 9ft. Aperture, 9 in.}}}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **11** | **11** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | '' | '' |
| footer text     | 'Observer: E. W. Maunder. Instrument, Thompson Photoheliograph. Focal Length, 9ft. Aperture, 9 in' | 'Observer: E. W. Maunder. Instrument, Thompson Photoheliograph. Focal Length, 9ft. Aperture, 9 in' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Sun - Plate 2a.png|1905, Jan. 30d. 12h. 8m. 27s}}

{{IMG:EB1911 - Sun - Plate 2b.png|1905, Jan. 31d. 11h. 17m. 27s}}

{{IMG:EB1911 - Sun - Plate 2c.png|1905, Feb. 2d. 10h. 50m. 28s}}

{{IMG:EB1911 - Sun - Plate 2d.png|1905, Feb. 8d. 13h. 3m. 5s}}

{{LEGEND:PHOTOGRAPHS OF THE SUN, TAKEN AT THE ROYAL OBSERVATORY, GREENWICH}LEGEND}

Observer: E. W. Maunder. Instrument, Thompson Photoheliograph. Focal Length, 9ft. Aperture, 9 in
```

### Current body
```
{{IMG:EB1911 - Sun - Plate 2a.png|1905, Jan. 30d. 12h. 8m. 27s}}

{{IMG:EB1911 - Sun - Plate 2b.png|1905, Jan. 31d. 11h. 17m. 27s}}

{{IMG:EB1911 - Sun - Plate 2c.png|1905, Feb. 2d. 10h. 50m. 28s}}

{{IMG:EB1911 - Sun - Plate 2d.png|1905, Feb. 8d. 13h. 3m. 5s}}

{{LEGEND:PHOTOGRAPHS OF THE SUN, TAKEN AT THE ROYAL OBSERVATORY, GREENWICH}LEGEND}

Observer: E. W. Maunder. Instrument, Thompson Photoheliograph. Focal Length, 9ft. Aperture, 9 in
```

---

## TAPESTRY — vol 26

**Article ID:** 4219183  
**Signature:** `wikitable depth=4 wt=multi ht=0`

### Source excerpt
```
{{right|{{sc|Plate}} I.}}
{{EB1911 fine print/s}}
{|{{ts|ac}} width="800"
|
{|width="100%"
|
{|{{ts|ba|bc}}
|{{ts|padding:1px}}|[[Image:EB1911 Tapestry - Egypto-Roman - curtain or wall hanging (fragment).jpg|x600px]]
|}
|{{ts|ar}}|
{|{{ts|ba|bc}}
|{{ts|padding:1px}}|[[Image:EB1911 Tapestry - Egypto-Roman - linen hanging or couch cover.jpg|x600px]]
|}
|}
|-
|&nbsp;
|-
|
{|width="100%"
|
{|{{ts|ba|border-spacing:0|height: 450px"}}
|{{ts|padding:0|ac}}|
{|
|[[Image:EB1911 Tapestry - Egypto-Roman - child mounted on a white horse.jpg|200px]]
|}
|-
|{{ts|padding:0}}|
{|
|[[Image:EB1911 Tapestry - Egypto-Roman - Hermes holding the caduceus and a purse.jpg|350px]]
|}
|}
|&emsp;
|{{ts|ar}}|
{|{{ts|ba|border-spacing:0}}
|{{ts|padding:1px}}|[[Image:EB1911 Tapestry - Egypto-Roman - couch or bed covering.jpg|x550px]]
|}
|}
|-
|{{ts|ac}}|{{sc|Figs.}} 5–9.—Specimens of Egypto-Roman tapestry weaving of about the 2nd to 5th century {{asc|A.D.}}&emsp;Victoria and Albert Museum.
|}
{{EB1911 fine print/e}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 5 | 5 |
| captioned       | 1 | 1 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **8** | **8** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'Plate I' | 'Plate I' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
Plate I

{{IMG:EB1911 Tapestry - Egypto-Roman - curtain or wall hanging (fragment).jpg|Figs. 5–9.—Specimens of Egypto-Roman tapestry weaving of about the 2nd to 5th century A.D. Victoria and Albert Museum}}

{{IMG:EB1911 Tapestry - Egypto-Roman - linen hanging or couch cover.jpg}}

{{IMG:EB1911 Tapestry - Egypto-Roman - child mounted on a white horse.jpg}}

{{IMG:EB1911 Tapestry - Egypto-Roman - Hermes holding the caduceus and a purse.jpg}}

{{IMG:EB1911 Tapestry - Egypto-Roman - couch or bed covering.jpg}}
```

### Current body
```
Plate I

{{IMG:EB1911 Tapestry - Egypto-Roman - curtain or wall hanging (fragment).jpg|Figs. 5–9.—Specimens of Egypto-Roman tapestry weaving of about the 2nd to 5th century A.D. Victoria and Albert Museum}}

{{IMG:EB1911 Tapestry - Egypto-Roman - linen hanging or couch cover.jpg}}

{{IMG:EB1911 Tapestry - Egypto-Roman - child mounted on a white horse.jpg}}

{{IMG:EB1911 Tapestry - Egypto-Roman - Hermes holding the caduceus and a purse.jpg}}

{{IMG:EB1911 Tapestry - Egypto-Roman - couch or bed covering.jpg}}
```

---

## TEXTILE PRINTING, PLATE I — vol 26

**Article ID:** 4219520  
**Signature:** `bare_image depth=0 wt=0 ht=0`

### Source excerpt
```
[[File:EB1911 - Textile Printing Plate 1 - Fig 1.jpg|center|250px]]
{{sc|Fig}}. 1.—Linen, dyed blue, the “reserved” parts represent the Annunciation; above the reclining figure of the Virgin Mary is the word MAPIA. Coptic, probably 5th or 6th century. 13 in. × 2 ft. 5 in.


[[File:EB1911 - Textile Printing Plate 1 - Fig 2.jpg|center|250px]]
{{sc|Fig}}. 2.—Child's Tunic of linen dyed blue, the pattern being “reserved” Coptic, 4th century (?). 18{{EB1911 tfrac|4}} m. × 23{{EB1911 tfrac|2}} in.


[[File:EB1911 - Textile Printing Plate 1 - Fig 3.jpg|center|250px]]
{{sc|Fig}}. 3.—Piece of red silk, printed in red, green, and black from wood blocks, with
a repeating pattern of black circles or rounds containing pairs of animals and
dragons; floriated crosses in the interspaces. Rhenish, 12th or 13th century.
15{{EB1911 tfrac|3|4}} in. × 12 {{EB1911 tfrac|3|4}} in.


[[File:EB1911 - Textile Printing Plate 1 - Fig 4.jpg|center|250px]]
{{sc|Fig}}. 4.—Piece of red silk, printed in black from wood blocks, with a trellis pattern enclosing pairs of birds and anthemions. Rhenish, 13111 or 14th century. 8{{EB1911 tfrac|8}} in. × 13{{EB1911 tfrac|3|4}} in.


[[File:EB1911 - Textile Printing Plate 1 - Fig 5.jpg|center|300px]]
{{sc|Fig}}. 5.—Piece of linen. printed in black from a wood block, with a pattern composed of repetitions of at lady 
on a turret, leafy sprays, a hound, and a bird on the wing. Rhenish, 14th century. 9{{EB1911 tfrac|2}} m. × 19{{EB1911 tfrac|3|4}} in.


[[File:EB1911 - 
…
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 6 | 6 |
| captioned       | 6 | 6 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **12** | **12** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 - Textile Printing Plate 1 - Fig 1.jpg|Linen, dyed blue, the “reserved” parts represent the Annunciation; above the reclining figure of the Virgin Mary is the word MAPIA. Coptic, probably 5th or 6th century. 13 in. × 2 ft. 5 in}}

{{IMG:EB1911 - Textile Printing Plate 1 - Fig 2.jpg|Child's Tunic of linen dyed blue, the pattern being “reserved” Coptic, 4th century (?). 184 m. × 232 in}}

{{IMG:EB1911 - Textile Printing Plate 1 - Fig 3.jpg|Piece of red silk, printed in red, green, and black from wood blocks, with a repeating pattern of black circles or rounds containing pairs of animals and dragons; floriated crosses in the interspaces. Rhenish, 12th or 13th century. 154 in. × 12 4 in}}

{{IMG:EB1911 - Textile Printing Plate 1 - Fig 4.jpg|Piece of red silk, printed in black from wood blocks, with a trellis pattern enclosing pairs of birds and anthemions. Rhenish, 13111 or 14th century. 88 in. × 134 in}}

{{IMG:EB1911 - Textile Printing Plate 1 - Fig 5.jpg|Piece of linen. printed in black from a wood block, with a pattern composed of repetitions of at lady on a turret, leafy sprays, a hound, and a bird on the wing. Rhenish, 14th century. 92 m. × 194 in}}

{{IMG:EB1911 - Textile Printing Plate 1 - Fig 6.jpg|Strip of linen printed in deep purple from a wood block, with at repeating pattern of eagles and conventional leaf and fruit forms. Rhenish. 14th or early 15th century. 204 in. × 62 in}}
```

### Current body
```
{{IMG:EB1911 - Textile Printing Plate 1 - Fig 1.jpg|Linen, dyed blue, the “reserved” parts represent the Annunciation; above the reclining figure of the Virgin Mary is the word MAPIA. Coptic, probably 5th or 6th century. 13 in. × 2 ft. 5 in}}

{{IMG:EB1911 - Textile Printing Plate 1 - Fig 2.jpg|Child's Tunic of linen dyed blue, the pattern being “reserved” Coptic, 4th century (?). 184 m. × 232 in}}

{{IMG:EB1911 - Textile Printing Plate 1 - Fig 3.jpg|Piece of red silk, printed in red, green, and black from wood blocks, with a repeating pattern of black circles or rounds containing pairs of animals and dragons; floriated crosses in the interspaces. Rhenish, 12th or 13th century. 154 in. × 12 4 in}}

{{IMG:EB1911 - Textile Printing Plate 1 - Fig 4.jpg|Piece of red silk, printed in black from wood blocks, with a trellis pattern enclosing pairs of birds and anthemions. Rhenish, 13111 or 14th century. 88 in. × 134 in}}

{{IMG:EB1911 - Textile Printing Plate 1 - Fig 5.jpg|Piece of linen. printed in black from a wood block, with a pattern composed of repetitions of at lady on a turret, leafy sprays, a hound, and a bird on the wing. Rhenish, 14th century. 92 m. × 194 in}}

{{IMG:EB1911 - Textile Printing Plate 1 - Fig 6.jpg|Strip of linen printed in deep purple from a wood block, with at repeating pattern of eagles and conventional leaf and fruit forms. Rhenish. 14th or early 15th century. 204 in. × 62 in}}
```

---

## Theatre, PLATE I — vol 26

**Article ID:** 4219554  
**Signature:** `other depth=0 wt=0 ht=0 toplegend`

### Source excerpt
```
{{block center|[[File:Britannica Theatre Plate Ia.jpg|frameless|center|420px]]
{{float right|{{x-smaller|''Photo, W. Leaf''.}}}}<br/>{{c|EPIDAURUS, THE THEATRE FROM THE WEST.}}}}


{{block center|[[File:Britannica Theatre Plate Ib.jpg|frameless|center|420px]]
{{float right|{{x-smaller|''Photo, R. Elsey Smith''.}}}}<br/>{{c|ATHENS, THE THEATRE OF DIONYSUS FROM THE ACROPOLIS.}}}}


{{nop}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'block center' | 'block center' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
block center

{{IMG:Britannica Theatre Plate Ia.jpg|EPIDAURUS, THE THEATRE FROM THE WEST}}

{{IMG:Britannica Theatre Plate Ib.jpg|ATHENS, THE THEATRE OF DIONYSUS FROM THE ACROPOLIS}}
```

### Current body
```
block center

{{IMG:Britannica Theatre Plate Ia.jpg|EPIDAURUS, THE THEATRE FROM THE WEST}}

{{IMG:Britannica Theatre Plate Ib.jpg|ATHENS, THE THEATRE OF DIONYSUS FROM THE ACROPOLIS}}
```

---

## Theatre, PLATE II — vol 26

**Article ID:** 4219555  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{| align="center" width="450px" 
|-style="text-align: center"
| rowspan="2" valign="center" | {{block center|[[File:Britannica Theatre Plate IIa.jpg|frameless|center|280px]]
{{float right|{{x-smaller|''Photo, R. Elsey Smith''.}}}}<br/>{{c|ATHENS, PRINCIPAL SEATS IN THE THEATRE OF DIONYSUS.}}}}
| valign="top" | {{block center|[[File:Britannica Theatre Plate IIb.jpg|frameless|center|140px]]
{{float right|{{x-smaller|''Photo, A. M, Woodward''.}}}}<br/>{{c|{{smaller|ASPENDUS, INTERIOR OF THE UPPER
GALLERY OF THE THEATRE.}}}}}}
|-valign="top" style="text-align: center"
| {{block center|[[File:Britannica Theatre Plate IIc.jpg|frameless|center|140px]]
{{float right|{{x-smaller|''Photo, A. M, Woodward''.}}}}<br/>{{c|{{smaller|ASPENDUS, THE STAGE WALL.}}}}}}
|}

{{block center|[[File:Britannica Theatre Plate IId.jpg|frameless|center|420px]]
{{float right|{{x-smaller|''Photo, Mansell & Co''.}}}}<br/>{{c|INTERIOR OF THEATRE, ORANGE.}}}}


{{nop}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 4 | 4 |
| captioned       | 4 | 4 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **10** | **10** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'block center' | 'block center' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
block center

{{IMG:Britannica Theatre Plate IIa.jpg|ATHENS, PRINCIPAL SEATS IN THE THEATRE OF DIONYSUS}}

{{IMG:Britannica Theatre Plate IIb.jpg|ASPENDUS, INTERIOR OF THE UPPER GALLERY OF THE THEATRE}}

{{IMG:Britannica Theatre Plate IIc.jpg|ASPENDUS, THE STAGE WALL}}

{{IMG:Britannica Theatre Plate IId.jpg|INTERIOR OF THEATRE, ORANGE}}
```

### Current body
```
block center

{{IMG:Britannica Theatre Plate IIa.jpg|ATHENS, PRINCIPAL SEATS IN THE THEATRE OF DIONYSUS}}

{{IMG:Britannica Theatre Plate IIb.jpg|ASPENDUS, INTERIOR OF THE UPPER GALLERY OF THE THEATRE}}

{{IMG:Britannica Theatre Plate IIc.jpg|ASPENDUS, THE STAGE WALL}}

{{IMG:Britannica Theatre Plate IId.jpg|INTERIOR OF THEATRE, ORANGE}}
```

---

## Theatre, PLATE III — vol 26

**Article ID:** 4219556  
**Signature:** `other depth=0 wt=0 ht=0 toplegend`

### Source excerpt
```
{{block center|[[File:Britannica Theatre Plate IIIa.jpg|frameless|center|420px]]
{{float left|{{x-smaller|''From a Photograph by S. B. Bolas & Co''.}}}}<br/>{{c|SACHS' ELECTRICAL STAGE "BRIDGES," ROYAL OPERA HOUSE, COVENT GARDEN.}}}}


{{block center|[[File:Britannica Theatre Plate IIIb.jpg|frameless|center|420px]]
{{float left|{{x-smaller|''From a Photograph by Alfred Ellis & Walery''.}}}}<br/>{{c|SACHS' ELECTRICAL STAGE "BRIDGES," THEATRE ROYAL, DRURY LANE.}}}}


{{nop}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'block center' | 'block center' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
block center

{{IMG:Britannica Theatre Plate IIIa.jpg|SACHS' ELECTRICAL STAGE "BRIDGES," ROYAL OPERA HOUSE, COVENT GARDEN}}

{{IMG:Britannica Theatre Plate IIIb.jpg|SACHS' ELECTRICAL STAGE "BRIDGES," THEATRE ROYAL, DRURY LANE}}
```

### Current body
```
block center

{{IMG:Britannica Theatre Plate IIIa.jpg|SACHS' ELECTRICAL STAGE "BRIDGES," ROYAL OPERA HOUSE, COVENT GARDEN}}

{{IMG:Britannica Theatre Plate IIIb.jpg|SACHS' ELECTRICAL STAGE "BRIDGES," THEATRE ROYAL, DRURY LANE}}
```

---

## Theatre, PLATE IV — vol 26

**Article ID:** 4219557  
**Signature:** `other depth=0 wt=0 ht=0 toplegend`

### Source excerpt
```
{{block center|[[File:Britannica Theatre Plate IV.jpg|frameless|center|420px]]
{{float left|{{x-smaller|''From a Photograph by Alfred Ellis & Walery''.}}}}<br/>{{c|THE NEW "GRIDIRON," ROYAL OPERA HOUSE, COVENT GARDEN.}}}}


{{nop}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 1 | 1 |
| captioned       | 1 | 1 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **4** | **4** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'block center' | 'block center' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
block center

{{IMG:Britannica Theatre Plate IV.jpg|THE NEW "GRIDIRON," ROYAL OPERA HOUSE, COVENT GARDEN}}
```

### Current body
```
block center

{{IMG:Britannica Theatre Plate IV.jpg|THE NEW "GRIDIRON," ROYAL OPERA HOUSE, COVENT GARDEN}}
```

---

## TOURNAMENT — vol 27

**Article ID:** 4220098  
**Signature:** `c_centered depth=0 wt=0 ht=0 toplegend`

### Source excerpt
```
{{nop}}


[[File:EB1911 Tournament, Plate, 1.jpg|400px|frameless|center]]

{{c|{{smaller|KNIGHTS JOUSTING WITH CRONELLS ON THEIR LANCES. French MS. early XIV Century. (Royal MS. 14 E. iii.)}}}}

[[File:EB1911 Tournament, Plate, 2.jpg|400px|frameless|center]]

{{c|{{smaller|{{uc|Knights Jousting}}. From a French MS. of the latter half of the XV Century. (Cotton MS. Nero D. ix.)}}}}

[[File:EB1911 Tournament, Plate, 3.jpg|300px|frameless|center]]

{{c|{{smaller|ENGLISH KNIGHTS RIDING INTO THE LISTS. From the Great Tournament Roll of 1511; by permission of the College of Arms.}}}}


{{nop}}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **6** | **6** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **0** | **0** |
| header text     | '' | '' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
{{IMG:EB1911 Tournament, Plate, 1.jpg|KNIGHTS JOUSTING WITH CRONELLS ON THEIR LANCES. French MS. early XIV Century. (Royal MS. 14 E. iii.)}}

{{IMG:EB1911 Tournament, Plate, 2.jpg|KNIGHTS JOUSTING . From a French MS. of the latter half of the XV Century. (Cotton MS. Nero D. ix.)}}

{{IMG:EB1911 Tournament, Plate, 3.jpg|ENGLISH KNIGHTS RIDING INTO THE LISTS. From the Great Tournament Roll of 1511; by permission of the College of Arms}}
```

### Current body
```
{{IMG:EB1911 Tournament, Plate, 1.jpg|KNIGHTS JOUSTING WITH CRONELLS ON THEIR LANCES. French MS. early XIV Century. (Royal MS. 14 E. iii.)}}

{{IMG:EB1911 Tournament, Plate, 2.jpg|KNIGHTS JOUSTING . From a French MS. of the latter half of the XV Century. (Cotton MS. Nero D. ix.)}}

{{IMG:EB1911 Tournament, Plate, 3.jpg|ENGLISH KNIGHTS RIDING INTO THE LISTS. From the Great Tournament Roll of 1511; by permission of the College of Arms}}
```

---

## WATER SUPPLY — vol 28

**Article ID:** 4221698  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{{right|{{sc|Plate I.}}}}<!-- label comes from reference on p. 404 in the third sentence of fine print section -->

{|style="margin: auto; text-align: center"
|style="border-style: solid; border-width: 1px"|[[Image:EB1911 Water Supply - Vyrnwy Valley.jpg|800px]]
|-
|THE VYRNWY VALLEY, MONTGOMERYSHIRE, June 1888.
|-
|&nbsp;
|-
|style="border-style: solid; border-width: 1px"|[[Image:EB1911 Water Supply - Lake Vyrnwy.jpg|800px]]
|-style="font-size: 75%; text-align: left"
|''From Photographs by J. Maclardy.''
|-
|LAKE VYRNWY, December 1889.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **7** | **7** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'Plate I.' | 'Plate I.' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
Plate I.

{{IMG:EB1911 Water Supply - Vyrnwy Valley.jpg|THE VYRNWY VALLEY, MONTGOMERYSHIRE, June 1888}}

{{IMG:EB1911 Water Supply - Lake Vyrnwy.jpg|From Photographs by J. Maclardy}}

{{LEGEND:LAKE VYRNWY, December 1889}LEGEND}
```

### Current body
```
Plate I.

{{IMG:EB1911 Water Supply - Vyrnwy Valley.jpg|THE VYRNWY VALLEY, MONTGOMERYSHIRE, June 1888}}

{{IMG:EB1911 Water Supply - Lake Vyrnwy.jpg|From Photographs by J. Maclardy}}

{{LEGEND:LAKE VYRNWY, December 1889}LEGEND}
```

---

## WOODCARVING — vol 28

**Article ID:** 4222332  
**Signature:** `wikitable depth=1 wt=1 ht=0`

### Source excerpt
```
{{sc|Plate II.}}

{|style="margin: auto; font-size: 90%; text-align: center"
|[[Image:EB1911 Wood-Carving - French cabinet.jpg|x750px]]
|&emsp;
|[[Image:EB1911 Wood-Carving - Doorway from Aal, Norway (detail).jpg|x750px]]
|-
|{{sc|Fig.}} 2.—FRENCH CABINET.  RENAISSANCE, 1577.
|
|{{sc|Fig.}} 3.—DETAIL OF DOORWAY FROM AAL, NORWAY.
|-
|
|
|SCANDINAVIAN, about 1200 A.D.
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 2 | 2 |
| captioned       | 2 | 2 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **7** | **7** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'Plate II' | 'Plate II' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
Plate II

{{IMG:EB1911 Wood-Carving - French cabinet.jpg|FRENCH CABINET. RENAISSANCE, 1577}}

{{IMG:EB1911 Wood-Carving - Doorway from Aal, Norway (detail).jpg|DETAIL OF DOORWAY FROM AAL, NORWAY}}

{{LEGEND:SCANDINAVIAN, about 1200 A.D}LEGEND}
```

### Current body
```
Plate II

{{IMG:EB1911 Wood-Carving - French cabinet.jpg|FRENCH CABINET. RENAISSANCE, 1577}}

{{IMG:EB1911 Wood-Carving - Doorway from Aal, Norway (detail).jpg|DETAIL OF DOORWAY FROM AAL, NORWAY}}

{{LEGEND:SCANDINAVIAN, about 1200 A.D}LEGEND}
```

---

## WOODCARVING — vol 28

**Article ID:** 4222333  
**Signature:** `wikitable depth=2 wt=multi ht=0 has_colspan`

### Source excerpt
```
{{right|{{sc|Plate III.}}}}
{|style="margin: auto; font-size: 90%; text-align: center"
|
{|
|[[Image:EB1911 Wood-Carving - Panel from front of stalls, Ulm Cathedral.jpg|400px]]
|-
|
{{sc|Fig.}} 4.—PANEL FROM FRONT OF STALLS,<br />
ULM CATHEDRAL.  1468-1474.
|}
|&emsp;
|
{|
|[[Image:EB1911 Wood-Carving - Arabian panel.jpg|200px]]
|-
|
{{sc|Fig.}} 5.—ARABIAN PANEL.<br />
13th century.
|}
|-
|colspan="3"|
{|
|[[Image:EB1911 Wood-Carving - German chest.jpg|700px]]
|-
|{{right|{{sm|''From Lessing's Holzschnitzereien, by permission of Ernst Wasmuth.''}}}}
|-
|{{sc|Fig.}} 6.—GERMAN CHEST.  Late 15th century.
|}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 3 | 3 |
| captioned       | 3 | 3 |
| legends         | 1 | 1 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **9** | **9** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'Plate III' | 'Plate III' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
Plate III

{{IMG:EB1911 Wood-Carving - Panel from front of stalls, Ulm Cathedral.jpg|PANEL FROM FRONT OF STALLS, ULM CATHEDRAL. 1468-1474}}

{{IMG:EB1911 Wood-Carving - Arabian panel.jpg|ARABIAN PANEL. 13th century}}

{{IMG:EB1911 Wood-Carving - German chest.jpg|From Lessing's Holzschnitzereien, by permission of Ernst Wasmuth}}

{{LEGEND:GERMAN CHEST. Late 15th century}LEGEND}
```

### Current body
```
Plate III

{{IMG:EB1911 Wood-Carving - Panel from front of stalls, Ulm Cathedral.jpg|PANEL FROM FRONT OF STALLS, ULM CATHEDRAL. 1468-1474}}

{{IMG:EB1911 Wood-Carving - Arabian panel.jpg|ARABIAN PANEL. 13th century}}

{{IMG:EB1911 Wood-Carving - German chest.jpg|From Lessing's Holzschnitzereien, by permission of Ernst Wasmuth}}

{{LEGEND:GERMAN CHEST. Late 15th century}LEGEND}
```

---

## WOODCARVING — vol 28

**Article ID:** 4222334  
**Signature:** `wikitable depth=2 wt=multi ht=0 has_colspan`

### Source excerpt
```
{{sc|Plate IV.}}
{|style="margin: auto; font-size: 90%; text-align: center"
|
{|
|colspan=3|[[Image:EB1911 Wood-Carving - Japanese panel.jpg|700px]]
|-
|colspan=3|{{sc|Fig.}} 7.—JAPANESE PANEL.
|-
|[[Image:EB1911 Wood-Carving - Detail of throne, Exeter Cathedral.jpg|x350px]]
|[[Image:EB1911 Wood-Carving - Flemish panel.jpg|x350px]]
|[[Image:EB1911 Wood-Carving - Detail of rood screen vaulting, Kenton, Devon.jpg|x350px]]
|-style="font-size: smaller; text-align: right"
|{{sm|''Photo, F. A. Crallan.''}}
|
|{{sm|''Photo, F. A. Crallan.''}}
|-
|{{sc|Fig.}} 8.—DETAIL OF BISHOP STAPLEDON'S<br />THRONE, 1308-1326 A.D.<br />EXETER CATHEDRAL.
|{{nowrap|{{sc|Fig.}} 9.—FLEMISH PANEL.}}<br />RENAISSANCE,<br />16th century.
|{{sc|Fig.}} 10.—DETAIL OF ROOD SCREEN<br />VAULTING. Late 15th century.<br />KENTON, DEVON.
|-
|colspan=3|[[Image:EB1911 Wood-Carving - Front of walnut coffer, Italian.jpg|700px]]
|-
|colspan=3|{{sc|Fig.}} 11.—FRONT OF WALNUT COFFER, 16th century. RENAISSANCE. ITALIAN.
|}
|}
```

### Stats

| | baseline | current |
|---|---|---|
| images          | 5 | 5 |
| captioned       | 5 | 5 |
| legends         | 0 | 0 |
| broken caps     | 0 | 0 |
| header leak     | 0 | 0 |
| footer leak     | 0 | 0 |
| header cap-shape| 0 | 0 |
| footer cap-shape| 0 | 0 |
| **matter**      | **12** | **12** |
| **penalty**     | **0** | **0** |
| **bookend_clean** | **1** | **1** |
| header text     | 'Plate IV.' | 'Plate IV.' |
| footer text     | '' | '' |

**Verdict:** ✅ identical

### Baseline body
```
Plate IV.

{{IMG:EB1911 Wood-Carving - Japanese panel.jpg|JAPANESE PANEL}}

{{IMG:EB1911 Wood-Carving - Detail of throne, Exeter Cathedral.jpg|DETAIL OF BISHOP STAPLEDON'S THRONE, 1308-1326 A.D. EXETER CATHEDRAL}}

{{IMG:EB1911 Wood-Carving - Flemish panel.jpg|FLEMISH PANEL. RENAISSANCE, 16th century}}

{{IMG:EB1911 Wood-Carving - Detail of rood screen vaulting, Kenton, Devon.jpg|DETAIL OF ROOD SCREEN VAULTING. Late 15th century. KENTON, DEVON}}

{{IMG:EB1911 Wood-Carving - Front of walnut coffer, Italian.jpg|FRONT OF WALNUT COFFER, 16th century. RENAISSANCE. ITALIAN}}
```

### Current body
```
Plate IV.

{{IMG:EB1911 Wood-Carving - Japanese panel.jpg|JAPANESE PANEL}}

{{IMG:EB1911 Wood-Carving - Detail of throne, Exeter Cathedral.jpg|DETAIL OF BISHOP STAPLEDON'S THRONE, 1308-1326 A.D. EXETER CATHEDRAL}}

{{IMG:EB1911 Wood-Carving - Flemish panel.jpg|FLEMISH PANEL. RENAISSANCE, 16th century}}

{{IMG:EB1911 Wood-Carving - Detail of rood screen vaulting, Kenton, Devon.jpg|DETAIL OF ROOD SCREEN VAULTING. Late 15th century. KENTON, DEVON}}

{{IMG:EB1911 Wood-Carving - Front of walnut coffer, Italian.jpg|FRONT OF WALNUT COFFER, 16th century. RENAISSANCE. ITALIAN}}
```

---
