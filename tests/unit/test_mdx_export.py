"""Container and lookup failures specific to the dictionary export."""
from pathlib import Path
from collections import defaultdict

import pytest

from britannica.mdx.build import (
    Links, add_headwords, article_key, bundle_body, compile_package,
    entry_url, lookup_fold, topic_key, label_content_entries, compact_aliases, validate, wrap,
)


def article(title, body):
    return {"title": title, "body": body, "volume": 1, "page_start": 1}


def test_duplicate_and_folded_headwords_keep_all_targets():
    articles = {"one": article("MERCURY", "A god."), "two": article("Mercury", "A metal.")}
    entries = {article_key(s): wrap(a["body"]) for s, a in articles.items()}
    assert add_headwords(entries, articles, {"MERCURY": {"one"}, "Mercury": {"two"}}) == 1
    assert entries["MERCURY"] == entries["Mercury"]
    choice = entries[entries["MERCURY"][8:]]
    assert entry_url(article_key("one")) in choice
    assert entry_url(article_key("two")) in choice
    assert lookup_fold("ABĀBDA") == lookup_fold("ababda")


def test_link_policy_preserves_identity_and_section():
    links = Links({"one"}, {"one", "two"})
    assert links.url_for("one", "history") == entry_url(article_key("one"), "section-history")
    assert links.url_for("two").startswith("https://britannica11.org/article/two")
    with pytest.raises(ValueError, match="Unknown article"):
        links.url_for("missing")


def test_descartes_aliases_collapse_to_book_title_but_distinct_names_remain():
    articles = {"one": article("DESCARTES, RENÉ", "Philosopher")}
    spellings = ["DESCARTES, RENÉ", "DESCARTES RENÉ", "DESCARTES RENE", "RENÉ DESCARTES", "RENE DESCARTES", "CARTESIUS"]
    aliases, removed = compact_aliases(articles, {s: {"one"} for s in spellings})
    assert aliases == {"DESCARTES, RENÉ": {"one"}, "RENÉ DESCARTES": {"one"}, "CARTESIUS": {"one"}}
    assert len(removed) == 3


def test_natural_name_lookup_resolves_person_without_splitting_words():
    articles = {"author": article("SWIFT, JONATHAN", "Author"),
                "bird": article("SWIFT", "Bird"), "name": article("JONATHAN", "Name")}
    aliases, _ = compact_aliases(articles, {"SWIFT, JONATHAN": {"author"},
        "SWIFT JONATHAN": {"author"}, "JONATHAN SWIFT": {"author"},
        "SWIFT": {"bird"}, "JONATHAN": {"name"}})
    entries = {article_key(s): wrap(a["body"]) for s, a in articles.items()}
    add_headwords(entries, articles, aliases)
    assert entries["JONATHAN SWIFT"] == "@@@LINK=" + article_key("author")


def test_alias_cleanup_preserves_ambiguous_targets_and_distinct_word_order_meanings():
    articles = {"one": article("MERCURY", "god"), "two": article("Mercury", "metal")}
    aliases, _ = compact_aliases(articles, {"MERCURY": {"one"}, "Mercury": {"two"},
        "A B": {"one"}, "B A": {"two"}})
    assert aliases["MERCURY"] == {"one", "two"}
    assert aliases["A B"] == {"one"} and aliases["B A"] == {"two"}


def test_deep_topics_fit_reader_key_limit_without_colliding():
    parent = "religion-and-theology/history-of-christianity/" + "long-parent-" * 15
    assert len(topic_key(parent + "biographies")) < 100
    assert topic_key(parent + "biographies") != topic_key(parent + "subjects")


def test_search_content_keys_are_readable_and_stable_links_still_resolve():
    articles = {"one": article("THUCYDIDES", "History"),
                "two": article("MERCURY", "A god"), "three": article("MERCURY", "A planet")}
    entries = {article_key(s): wrap('<h1>' + a['title'] + '</h1><p id="history">' + a['body'] + '</p>')
               for s, a in articles.items()}
    add_headwords(entries, articles, {"THUCYDIDES": {"one"}, "MERCURY": {"two", "three"}})
    transformed, names = label_content_entries(entries, articles)
    assert transformed["THUCYDIDES"] == entries[article_key("one")]
    assert transformed[article_key("one")] == "@@@LINK=THUCYDIDES"
    assert names[article_key("two")] != names[article_key("three")]
    assert all(not key.startswith("EB1911:") for key, value in transformed.items() if not value.startswith("@@@LINK="))
    transformed["Jump"] = wrap('<a href="' + entry_url(article_key("one"), "history") + '">History</a>')
    validate(transformed, {"britannica.css": b""})


def test_validator_rejects_missing_fragments_alias_cycles_and_assets():
    resources = {"britannica.css": b""}
    entries = {"one": wrap('<a href="entry://two#section-history">go</a>'), "two": wrap('<p id="section-history">text</p>')}
    assert validate(entries, resources)["internal_links"] == 1
    entries["two"] = wrap("text")
    with pytest.raises(ValueError, match="Missing fragment"):
        validate(entries, resources)
    with pytest.raises(ValueError, match="Alias loop"):
        validate({"one": "@@@LINK=two", "two": "@@@LINK=one"}, {})
    with pytest.raises(ValueError, match="Missing resource"):
        validate({"one": wrap('<img src="missing.png">')}, resources)


def test_remote_assets_fail_instead_of_shipping_online_dependency():
    with pytest.raises(ValueError, match="Unbundled"):
        bundle_body('<img src="https://example.org/image.png">', {}, {})
    # The Reader's Guide extractor supplies already-local MDD resource names.
    assert bundle_body('<img src="images/guide.jpg">', {"images/guide.jpg": b"image"}, {}) == '<img src="images/guide.jpg">'


def test_known_missing_source_link_is_visible_and_repaired_source_retires_exception():
    from britannica.mdx.link_exceptions import mark_unavailable
    key = article_key("20-0065-dd33a0")
    link = '<a href="' + entry_url(key, "section-oil-testing") + '">Oil Testing</a>'
    entries = {key: wrap(link)}
    issues = mark_unavailable(entries)
    assert len(issues) == 1
    assert "Oil Testing" in entries[key] and "[source link unavailable]" in entries[key]
    assert validate(entries, {"britannica.css": b""})["internal_links"] == 0
    repaired = {key: wrap(link + '<h2 id="section-oil-testing">Oil Testing</h2>')}
    assert mark_unavailable(repaired) == []
    assert link in repaired[key]


def test_new_missing_source_link_still_fails():
    from britannica.mdx.link_exceptions import mark_unavailable
    key = article_key("20-0065-dd33a0")
    entries = {key: wrap('<a href="' + entry_url(key, "new-missing-section") + '">New problem</a>')}
    assert mark_unavailable(entries) == []
    with pytest.raises(ValueError, match="Missing fragment"):
        validate(entries, {"britannica.css": b""})


def test_reference_aliases_preserve_ambiguity_and_exclude_display_and_sections():
    from britannica.mdx.navigation import add_reference_aliases
    articles = {"one": article("First", "text"), "two": article("Second", "text")}
    articles["one"]["xrefs"] = [
        {"status": "resolved", "target_filename": target + ".json",
         "normalized_target": "Shared name", "surface_text": "see above"}
        for target in articles
    ] + [
        {"status": "resolved", "target_filename": "one.json",
         "normalized_target": "History", "target_section": "history"},
        {"status": "unresolved", "target_filename": "one.json",
         "normalized_target": "Unproved"},
    ]
    aliases = defaultdict(set)
    report = add_reference_aliases(articles, aliases)
    assert aliases["Shared name"] == {"one", "two"}
    assert not {"see above", "History", "Unproved"}.intersection(aliases)
    assert report["accepted"]["Shared name"] == ["one", "two"]


def test_mdx_mdd_roundtrip_unicode_alias_and_binary_resource(tmp_path: Path):
    pytest.importorskip("mdict_utils")
    entries = {"ABĀBDA": wrap('<p id="x">α &amp; β</p><img src="image.png">'), "ababda": "@@@LINK=ABĀBDA"}
    resources = {"image.png": b"\x89PNG\r\n\x1a\n\x00binary", "britannica.css": b".eb1911 {color:inherit}"}
    compile_package(tmp_path, entries, resources, "sample")
    assert (tmp_path / "sample.mdx").stat().st_size > 0
    # Compilation closes SQLite handles even on Windows; another build can
    # replace the staging file immediately, without waiting for process exit.
    (tmp_path / "stage.db").unlink()
