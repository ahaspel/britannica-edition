"""The reader's "Dictionary info" pane says what the dictionary is."""
from wikikit.mdx.build import dictionary_description


def test_complete_edition_describes_itself_with_its_own_numbers():
    html = dictionary_description(sample=False, articles=37225, contributors=1508,
                                  illustrations=10744, headwords=46688)
    for fact in ("Eleventh Edition", "37,225 articles", "1,508 contributors",
                 "10,744 illustrations", "46,688 headwords", "Edited by Aaron Haspel",
                 "Wikisource", "https://britannica11.org", "CC BY-SA 4.0",
                 "<i>Britannica 11</i>"):
        assert fact in html, fact
    assert "sample" not in html


def test_sample_points_at_its_own_help_page():
    html = dictionary_description(sample=True, articles=13, contributors=11,
                                  illustrations=40, headwords=40)
    assert "<i>Britannica 11 sample</i>" in html and "compatibility sample" in html
    # Its help page lists articles only; promising the complete edition's
    # indexes would send the reader looking for pages that are not there.
    assert "Reader’s Guide" not in html and "topics" not in html
