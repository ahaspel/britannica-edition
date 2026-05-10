# Cross-reference coverage audit

- Articles scanned: **36991**
- Normalized titles: **35915**

## Pattern hit-rates

| pattern | candidates | resolvable | match rate |
|---|---|---|---|
| see X (lowercase 'see', mixed-case target) | 3500 | 781 | 22.3% |
| See X (mixed-case target) | 4158 | 524 | 12.6% |
| see article X | 22 | 15 | 68.2% |
| See also X (mixed-case) | 598 | 61 | 10.2% |
| cf. X | 1761 | 243 | 13.8% |
| vide X | 5 | 0 | 0.0% |
| v. X (Latin abbreviation) | 666 | 72 | 10.8% |
| compare X | 85 | 14 | 16.5% |

*Resolvable* = candidate's target normalizes to an existing article title.  Higher match rate → expanding the extractor to cover this shape produces real links rather than noise.

## Examples — see X (lowercase 'see', mixed-case target)

- vol  1 'AARON' → 'see Gray' → matches 'GRAY'
- vol  1 'ACOLYTE' → 'see Eusebius' → matches 'EUSEBIUS'
- vol  3 'BABBAGE, CHARLES' → 'see Calculating Machines' → matches 'CALCULATING MACHINES'
- vol  2 'ASSEMBLY, UNLAWFUL' → 'see Bishop' → matches 'BISHOP'
- vol  2 'ANTHEMIUS' → 'see Procopius' → matches 'PROCOPIUS'
- vol  2 'ANTHRAX' → 'see Virgil' → matches 'VIRGIL'
- vol  2 'ANTHROPOLOGY' → 'see Plate' → matches 'PLATE'
- vol  2 'ANTICHRIST' → 'see Basset' → matches 'BASSET'
- vol 18 'METAPHYSICS' → 'see Aristotle' → matches 'ARISTOTLE'
- vol 18 'METAPHYSICS' → 'see Bacon' → matches 'BACON'
- vol  2 'APOCALYPTIC LITERATURE' → 'see James' → matches 'JAMES'
- vol  2 'APOCRYPHAL LITERATURE' → 'see Origen' → matches 'ORIGEN'
- vol  2 'APOCRYPHAL LITERATURE' → 'see Smith' → matches 'SMITH'
- vol  2 'APOSTOLICI' → 'see St Augustine' → matches 'ST AUGUSTINE'
- vol  1 'ALBUMIN' → 'see Purin' → matches 'PURIN'

## Examples — See X (mixed-case target)

- vol 10 'FIRST OF JUNE' → 'See James' → matches 'JAMES'
- vol  6 'CLEVES' → 'See Char' → matches 'CHAR'
- vol  1 'ACEPHALI' → 'See Gibbon' → matches 'GIBBON'
- vol  4 'BRISTOL, EARLS AND MARQUESSES OF' → 'See John' → matches 'JOHN'
- vol  1 'ADALBERT' → 'See Adam' → matches 'ADAM'
- vol  1 'ADAM' → 'See Eden' → matches 'EDEN'
- vol  1 'ADAM' → 'See Paradise' → matches 'PARADISE'
- vol  1 'ADAM' → 'See Life' → matches 'LIFE'
- vol  1 'ADAM' → 'See Smith' → matches 'SMITH'
- vol  1 'ÆTHELBALD' → 'See Asser' → matches 'ASSER'
- vol  1 'ÆTHELBERHT' → 'See Bede' → matches 'BEDE'
- vol  1 'ÆTHELFRITH' → 'See Bede' → matches 'BEDE'
- vol  1 'ÆTHELWULF' → 'See Asser' → matches 'ASSER'
- vol  1 'AFER, DOMITIUS' → 'See Quintilian' → matches 'QUINTILIAN'
- vol  1 'AFGHANISTAN' → 'See Baluchistan' → matches 'BALUCHISTAN'

## Examples — see article X

- vol  2 'ARTHROPODA' → 'see article Arachnida' → matches 'ARACHNIDA'
- vol 14 'HYDROZOA' → 'see article Medusa' → matches 'MEDUSA'
- vol 10 'FIFE (MILITARY FLUTE)' → 'see article Flute' → matches 'FLUTE'
- vol  7 'CRITICISM' → 'see the article Textual Criticism' → matches 'TEXTUAL CRITICISM'
- vol  7 'CYTOLOGY' → 'see article Reproduction' → matches 'REPRODUCTION'
- vol  8 'DRAMA' → 'see the article German Literature' → matches 'GERMAN LITERATURE'
- vol 11 'FREE TRADE' → 'see the article on Chamberlain' → matches 'CHAMBERLAIN'
- vol 22 'PRECEDENCE' → 'see article Peerage' → matches 'PEERAGE'
- vol 20 'ORCHIDS' → 'see article Angiosperms' → matches 'ANGIOSPERMS'
- vol 24 'SHERIDAN, PHILIP HENRY' → 'see the article WILDERNESS' → matches 'WILDERNESS'
- vol 23 'ROME' → 'see the article Pyrrhus' → matches 'PYRRHUS'
- vol 23 'ROME' → 'see the article Agrarian Laws' → matches 'AGRARIAN LAWS'
- vol 25 'STEPHAN, HEINRICH VON' → 'see article Germany' → matches 'GERMANY'
- vol 26 'TERRACOTTA' → 'see article DELLA ROBBIA' → matches 'DELLA ROBBIA'
- vol 27 'VALDES, JUAN DE' → 'see article Socinus' → matches 'SOCINUS'

## Examples — See also X (mixed-case)

- vol  2 'ANNE' → 'See also Shrewsbury' → matches 'SHREWSBURY'
- vol 11 'FREDERICK III' → 'See also Bismarck' → matches 'BISMARCK'
- vol  1 'ALBANIA' → 'See also Murray' → matches 'MURRAY'
- vol  8 'DEMOCHARES' → 'See also Plutarch' → matches 'PLUTARCH'
- vol 19 'NEUHOF, THEODORE STEPHEN, BARON VON' → 'See also Fitzgerald' → matches 'FITZGERALD'
- vol  6 'CHURCH HISTORY' → 'See also Smith' → matches 'SMITH'
- vol  5 'CAMBRIDGE (ENGLAND)' → 'See also Universities' → matches 'UNIVERSITIES'
- vol  5 'CAPE COLONY' → 'See also Transvaal' → matches 'TRANSVAAL'
- vol  5 'CAROL' → 'See also Julian' → matches 'JULIAN'
- vol  6 'COLOUR' → 'See also Newton' → matches 'NEWTON'
- vol 23 'ROMAN CATHOLIC CHURCH' → 'See also Stephen' → matches 'STEPHEN'
- vol  7 'CONTRABAND' → 'See also Hall' → matches 'HALL'
- vol 17 'LOUIS IX' → 'See also William' → matches 'WILLIAM'
- vol 13 'HEBREW RELIGION' → 'See also Birch' → matches 'BIRCH'
- vol 13 'HEBREWS, EPISTLE TO THE' → 'See also Hastings' → matches 'HASTINGS'

## Examples — cf. X

- vol  2 'ANGLO-NORMAN LITERATURE' → 'cf. Ward' → matches 'WARD'
- vol  1 'ABIGAIL' → 'cf. Abigail' → matches 'ABIGAIL'
- vol  1 'ACCOMMODATION' → 'cf. John xviii' → matches 'JOHN XVIII'
- vol  1 'ACTS OF THE APOSTLES' → 'cf. Philo' → matches 'PHILO'
- vol  1 'AEGINA' → 'cf. Herod' → matches 'HEROD'
- vol  2 'ANTIOCH' → 'cf. Nicaea' → matches 'NICAEA'
- vol  1 'AGINCOURT' → 'cf. Bannockburn' → matches 'BANNOCKBURN'
- vol  1 'AGRARIAN LAWS' → 'cf. Festus' → matches 'FESTUS'
- vol  1 'AHASUERUS' → 'cf. Herod' → matches 'HEROD'
- vol  2 'ASPHODEL' → 'cf. Hesiod' → matches 'HESIOD'
- vol  2 'ASPHODEL' → 'cf. Herod' → matches 'HEROD'
- vol  2 'ARMS AND ARMOUR' → 'cf. Munro' → matches 'MUNRO'
- vol  2 'APHRODITE' → 'cf. Harmonia' → matches 'HARMONIA'
- vol  2 'APOSTLE' → 'cf. Ignatius' → matches 'IGNATIUS'
- vol  2 'ARISTOCRACY' → 'cf. Sparta' → matches 'SPARTA'

## Examples — v. X (Latin abbreviation)

- vol  2 'ARUNDEL, EARLS OF' → 'v. Arundel' → matches 'ARUNDEL'
- vol  1 'ALDRINGER (Altringer, Aldringen), JOHANN' → 'v. Gallas' → matches 'GALLAS'
- vol  2 'ARCHAEOPTERYX' → 'v. Meyer' → matches 'MEYER'
- vol  1 'AMERICAN LAW' → 'v. New York' → matches 'NEW YORK'
- vol  1 'AMERICAN LAW' → 'v. Illinois' → matches 'ILLINOIS'
- vol  1 'AMERICAN LAW' → 'v. Iowa' → matches 'IOWA'
- vol  1 'AMERICAN LAW' → 'v. Illinois' → matches 'ILLINOIS'
- vol  1 'AMERICAN LAW' → 'v. Smith' → matches 'SMITH'
- vol 10 'FOOTBALL' → 'v. Scotland' → matches 'SCOTLAND'
- vol  2 'ASIA MINOR' → 'v. Lennep' → matches 'LENNEP'
- vol  3 'AUSTRIA-HUNGARY' → 'v. Liechtenstein' → matches 'LIECHTENSTEIN'
- vol  3 'AUSTRIA-HUNGARY' → 'v. Liechtenstein' → matches 'LIECHTENSTEIN'
- vol  3 'BATRACHIA' → 'v. Ammon' → matches 'AMMON'
- vol  5 'CAPPADOCIA' → 'v. Lennep' → matches 'LENNEP'
- vol  5 'CAVALRY' → 'v. Bismarck' → matches 'BISMARCK'

## Examples — compare X

- vol  2 'ARABICI' → 'compare Tatian' → matches 'TATIAN'
- vol  2 'ATOM' → 'compare Dalton' → matches 'DALTON'
- vol  9 'ETHICS' → 'compare Ambrose' → matches 'AMBROSE'
- vol  6 'CLEISTHENES' → 'compare Cleisthenes' → matches 'CLEISTHENES'
- vol  8 'DEMOCRATIC PARTY' → 'compare Cleveland' → matches 'CLEVELAND'
- vol 10 'FEASTS AND FESTIVALS' → 'compare Socrates' → matches 'SOCRATES'
- vol 14 'INSCRIPTIONS' → 'compare Jordan' → matches 'JORDAN'
- vol 17 'MARATHI' → 'compare Marathi' → matches 'MARATHI'
- vol 22 'PROPHET' → 'compare Ezekiel' → matches 'EZEKIEL'
- vol 22 'PSYCHOLOGY' → 'Compare Spencer' → matches 'SPENCER'
- vol 28 'WAGES' → 'Compare Marshall' → matches 'MARSHALL'
- vol 21 'PICTON, SIR THOMAS' → 'compare Napier' → matches 'NAPIER'
- vol 25 'SOCRATES' → 'compare Xenophon' → matches 'XENOPHON'
- vol 26 'TALE' → 'Compare Chambers' → matches 'CHAMBERS'
