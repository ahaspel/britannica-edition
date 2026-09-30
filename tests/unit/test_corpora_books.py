"""The book's side of the corpus seam: the facts EB1911's profile carries.  The
engine's side (selection, refusal, declared data) is tested in wikikit, against
a fixture book; the DNB's profile is tested in its own repository, dnb-edition.

The load-bearing test is `test_eb1911_titles_are_unchanged`: Phase 0's whole
claim is that introducing a second book moves nothing about the first, and the
page title is the one value the profile took over from a hardcoded format
string.  If that drifts, 37,000 live articles are being rebuilt from pages
fetched under different names.
"""
from eb1911 import EB1911
from wikikit.corpora import KNOWN_DATA, current_corpus


def test_the_committed_book_is_the_britannica():
    """book.env names the Britannica.  The engine has NO default (it was the
    key "eb1911"): the book is named by the repository that builds it."""
    assert current_corpus() is EB1911


def test_eb1911_titles_are_unchanged():
    """Byte-identical to the format string the fetcher used to hold.

    This is the gate in miniature.  The old line was:
        f"Page:EB1911 - Volume {volume:02d}.djvu/{page_number}"
    """
    for volume in range(1, 30):
        for page in (1, 7, 42, 1234):
            assert EB1911.page_title(volume, page) == (
                f"Page:EB1911 - Volume {volume:02d}.djvu/{page}")


def test_eb1911_names_itself():
    assert EB1911.need("site") == "https://britannica11.org"


def test_every_file_eb1911_declares_exists():
    """A declaration is a promise."""
    for name in EB1911.data_files:
        assert EB1911.data(name).is_file(), name
    assert EB1911.data_files <= KNOWN_DATA


def test_the_page_manifest_covers_every_volume():
    """A missing volume means a silently short import, not an error."""
    assert EB1911.volumes == list(range(1, 30))
    assert all(n > 0 for n in EB1911.pages.values())


def test_eb1911_page_counts_match_the_array_they_replaced():
    """Verbatim, not re-derived.

    They lived in a bash array in fetch_all.sh.  The article span
    (`EB1911.article_pages`) looks like the same fact and is not — it is the
    span holding ARTICLES, and it disagrees for volumes 20 and 29, the index
    volume being absent from it entirely.
    """
    was = [0, 1029, 1027, 1015, 1031, 1002, 1017, 1008, 1027, 997, 967, 968,
           985, 985, 953, 994, 1016, 1039, 1000, 1034, 1054, 1019, 993, 1069,
           1100, 1090, 1104, 1092, 1091, 982]
    assert [EB1911.pages[v] for v in range(1, 30)] == was[1:]


def test_eb1911_raw_path_is_unchanged():
    """29,688 files already sit at data/raw/wikisource.

    The name is a legacy of there being only one book.  Renaming it would buy
    tidiness at the cost of a mass move, and every test that reads a fixture
    page hardcodes the old path.
    """
    from wikikit.source_pages import raw_dir, volume_dir, page_filename
    assert raw_dir().as_posix() == "data/raw/wikisource"
    assert volume_dir(3).as_posix() == "data/raw/wikisource/vol_03"
    assert page_filename(3, 42) == "vol03-page0042.json"
