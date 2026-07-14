"""The genealogy producer: chart2 / familytree / tree-chart grid macros → their
pre-cropped page-scan image, with any inner ``<ref>`` recursed to a footnote.

This path was dormant from the day it was written — preprocess substituted every
block to an IMG before the walk ever saw it — so it had no coverage, and a latent
walker-ordering bug (the generic ``{{…}}`` recognizer claiming the bare
``{{chart2/start}}`` opener before the genealogy recognizer ran) sat unnoticed.
These are the first tests; they exercise the producer end-to-end through
``process_elements``.
"""
from britannica.pipeline.stages.elements import ElementContext, process_elements


def _walk(raw: str, volume: int) -> str:
    # The producer keys the crop lookup on volume; page is irrelevant.
    return process_elements(raw, ElementContext(volume=volume))


def test_chart2_block_becomes_its_cropped_image():
    out = _walk("{{chart2/start}}\n{{chart2| |A}}\n{{chart2/end}}", 1)
    assert "{{IMG:chart2_vol01_page0124.jpg|Genealogical table}}" in out
    # The grid macro is fully consumed — no opener/row leaks as prose.
    assert "chart2/start" not in out and "chart2/end" not in out


def test_familytree_recurses_inner_ref_to_a_footnote():
    out = _walk(
        "{{familytree/start}}\n{{familytree|A<ref>Cooper note</ref>}}\n"
        "{{familytree/end}}", 7)
    assert "{{IMG:familytree_vol07_page0369.jpg|Genealogical table}}" in out
    # The node footnote survives the flattening, as an ordinary article footnote.
    assert "«FN:Cooper note«/FN»" in out
    assert "familytree/start" not in out


def test_tree_chart_block_becomes_its_cropped_image():
    out = _walk("{{Tree chart/start|align=center}}\n{{Tree chart|A}}\n"
                "{{Tree chart/end}}", 25)
    assert "{{IMG:treechart_vol25_page0382.jpg|Genealogical table}}" in out
    assert "Tree chart/start" not in out


def test_unknown_volume_strips_rather_than_leaking_the_raw_macro():
    # No crop for vol 99 → the block is consumed to nothing, never leaked raw.
    out = _walk("{{chart2/start}}\n{{chart2|A}}\n{{chart2/end}}", 99)
    assert "IMG" not in out
    assert "chart2/start" not in out
