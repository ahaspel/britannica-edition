"""Regression tests for folded-row wikitable unfolding.

A folded wikitable row is a single ``|-`` row whose cells each hold N
logical values stacked with ``<br>`` — common in EB1911 dense-data
articles (ATMOSPHERIC ELECTRICITY, BEER analyses, ATMOSPHERE hourly
records). ``unfold_folded_rows`` rewrites these as N real rows so the
existing table pipeline sees a well-formed N-row table.

Fixtures (both positive and negative):

* ATM_ELEC_T1 — ATMOSPHERIC ELECTRICITY Table I (vol 2 p0909): 11-row
  fold with 13 cells, all folded uniformly.
* BEER_MILD_ALES — ENGLISH BEERS Mild Ales (vol 3 p0662): 3-row fold,
  4 cells, all folded.
* SIMPLE_2ROW — minimal 2-row fold.
* CONSTANT_COLUMN — fold with one cell having split=1 (a column label
  that replicates across all N rows).

Negative fixtures — these tables must pass through unchanged:

* BATTLESHIP_ANOMALY — data row with 2 multi-line description cells in
  a 17-row table (vol24 p0957 shape). Lone candidate doesn't dominate.
* UNIT_CONVERSION — table where every data row has a ``°F<br>(°C)``
  unit-conversion cell (vol10 p0423 shape). Multiple candidates.
* HEADER_LINE_WRAP — header row with per-cell multi-line labels but
  mismatched counts (vol24 p0957 shape).
"""
from __future__ import annotations

import pytest

from britannica.pipeline.stages.fold_unfold import unfold_folded_rows


ATM_ELEC_T1 = """
{|class=wikitable
|-
| Place and Period. || Jan. || Feb.
|-
| Karasjok, 1903–1904<br>Sodankyla, 1882–1883<br>Potsdam, 1904
| 143<br>94<br>167
| 150<br>133<br>95
|}
""".strip()


BEER_MILD_ALES = """
{| class="wikitable"
|+Mild Ales
|-
| Number. || Original Gravity. || Alcohol %. ||Extractives %.
|-
| 1.<br>2.<br>3. ||1055·13<br>1055·64<br>1071·78 ||4·17<br>4·47<br>5·57 ||6·1<br>5·7<br>7·3
|}
""".strip()


SIMPLE_2ROW = """
{|
|-
| A || B
|-
| 1<br>2 || 3<br>4
|}
""".strip()


CONSTANT_COLUMN = """
{|
|-
| Header1 || Header2 || Header3
|-
| Const
| 1<br>2<br>3
| x<br>y<br>z
|}
""".strip()


BATTLESHIP_ANOMALY = """
{|
|-
| Vessel. || Date || Machinery || Guns
|-
| Agincourt || 1865 || Horizontal || 6 guns
|-
| Bellerophon || 1865 || Horizontal || 8 guns
|-
| Benbow || 1885 || Vertical<br>2 expansions<br>3 cylinders<br>52in+74in || 4 guns<br>6 torpedo<br>tubes<br>plus chasers
|-
| Majestic || 1896 || Triple || 10 guns
|-
| Duncan || 1901 || Triple || 12 guns
|}
""".strip()


UNIT_CONVERSION = """
{|
|-
| Class || Duration || Temp. || Area
|-
| A || 45 mins || 1500°F<br>(815.5°C) || 100 sq ft<br>(9.290 sq m)
|-
| B || 60 mins || 1500°F<br>(815.5°C) || 100 sq ft<br>(9.290 sq m)
|-
| C || 90 mins || 1700°F<br>(926.7°C) || 100 sq ft<br>(9.290 sq m)
|}
""".strip()


HEADER_LINE_WRAP = """
{|
|-
| Vessel. || Date<br>of<br>Launch || Hull || Armament<br>(incl.<br>Machine<br>Guns)
|-
| Warrior || 1860 || Iron || 40 guns
|-
| Agincourt || 1865 || Iron || 24 guns
|}
""".strip()


# ---- Positive cases ----

def test_atm_elec_unfolds_to_three_rows():
    out = unfold_folded_rows(ATM_ELEC_T1)
    # Each station name should appear as its own row (no <br> between them).
    assert "Karasjok, 1903–1904<br>" not in out
    assert "Karasjok, 1903–1904" in out
    assert "Sodankyla, 1882–1883" in out
    assert "Potsdam, 1904" in out
    # Values should be distributed, not concatenated.
    assert out.count("|-") == 4  # header + 3 unfolded data rows


def test_atm_elec_numeric_values_distribute_correctly():
    out = unfold_folded_rows(ATM_ELEC_T1)
    # The three Jan values should each appear, separately.
    # After unfolding, "143" is on Karasjok's row, "94" on Sodankyla's, "167" on Potsdam's.
    karasjok_idx = out.index("Karasjok")
    sodankyla_idx = out.index("Sodankyla")
    potsdam_idx = out.index("Potsdam")
    v143_idx = out.index("143")
    v94_idx = out.index("94")
    v167_idx = out.index("167")
    # 143 should come between Karasjok and Sodankyla (same row), etc.
    assert karasjok_idx < v143_idx < sodankyla_idx
    assert sodankyla_idx < v94_idx < potsdam_idx
    assert potsdam_idx < v167_idx


def test_beer_mild_ales_unfolds():
    out = unfold_folded_rows(BEER_MILD_ALES)
    assert "1055·13<br>" not in out
    assert out.count("|-") == 4  # header + 3 data rows


def test_simple_2row_unfolds():
    out = unfold_folded_rows(SIMPLE_2ROW)
    assert "1<br>2" not in out
    assert "1" in out and "2" in out and "3" in out and "4" in out
    assert out.count("|-") == 3  # header + 2 data rows


def test_constant_column_replicates():
    out = unfold_folded_rows(CONSTANT_COLUMN)
    # "Const" appears in all 3 unfolded rows.
    assert out.count("Const") == 3
    assert "1<br>2" not in out
    assert out.count("|-") == 4  # header + 3 data rows


# ---- Negative cases: must pass through unchanged ----

def test_battleship_anomaly_unchanged():
    out = unfold_folded_rows(BATTLESHIP_ANOMALY)
    assert out == BATTLESHIP_ANOMALY


def test_unit_conversion_unchanged():
    out = unfold_folded_rows(UNIT_CONVERSION)
    assert out == UNIT_CONVERSION


def test_header_line_wrap_unchanged():
    out = unfold_folded_rows(HEADER_LINE_WRAP)
    assert out == HEADER_LINE_WRAP


# ---- Multi-header tables with large-N data fold ----
# ATMOSPHERIC ELECTRICITY Tables II and III (vol 2 p0910): several
# header rows precede the single folded data row, and header cells
# have incidental ``<br>`` splits (period ``1862–<br>1864`` etc.).
# The large-N fold (25 hourly readings) should dominate and unfold
# despite the small-N (=2) header candidate and the non-dominant
# segment count (>2 non-empty segments).

ATM_ELEC_T2_SHAPE = """
{|class=wikitable
|-
| Station. || Karasjok. || Sodankylä. || Lisbon.
|-
| Period. || 1903–4. || 1882–<br>1883. || 1884–<br>1886.
|-
| Days. || All. || All. || Fine.
|-
| Hour.<br>1<br>2<br>3<br>4<br>5<br>6 || <br>83<br>73<br>66<br>63<br>60<br>68 || <br>91<br>85<br>82<br>84<br>89<br>91 || <br>84<br>80<br>78<br>81<br>83<br>92
|}
"""


def test_atm_elec_t2_shape_unfolds_despite_header_splits():
    """Table II shape: 3 header rows (one with N=2 incidental splits) +
    1 big N=7 data fold. Large-N rule wins over non-dominance."""
    out = unfold_folded_rows(ATM_ELEC_T2_SHAPE)
    # Hour row should have unfolded: originally 1 data row (N=7 fold),
    # now 7 separate rows.
    # 3 original header rows + 7 unfolded data rows = 10 |- separators
    assert out.count("|-") == 10
    # Each hour value now on its own row
    assert "Hour.<br>1" not in out
    for h in ("Hour.", "1", "2", "3", "4", "5", "6"):
        assert h in out
    # The incidental N=2 splits in the Period row must NOT unfold —
    # they should survive as literal ``<br>``-joined text since they
    # weren't the dominant fold.
    assert "1882" in out and "1883" in out


# ---- Idempotence and empty-input sanity ----

def test_idempotent():
    once = unfold_folded_rows(ATM_ELEC_T1)
    twice = unfold_folded_rows(once)
    assert once == twice


def test_no_tables_noop():
    text = "Just some prose. No tables here."
    assert unfold_folded_rows(text) == text


def test_no_br_noop():
    text = "{|\n|-\n| a || b || c\n|-\n| 1 || 2 || 3\n|}"
    assert unfold_folded_rows(text) == text
