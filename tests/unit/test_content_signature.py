"""The content-signature counter must be trustworthy before any change leans on it.

`export_fingerprint.content_tokens` is the net that separates a benign styling
relocation from an article silently LOSING text — the failure mode both pending
sweeper removals risk (the `{|`/`|}` swallow eating prose, a dropped table cell).
If the counter itself is wrong it manufactures fake all-clear or fake alarms
([[feedback_verify_the_counter]]), so it is pinned directly: markup must be
invisible to it, words must not be.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "diagnostics"))
from export_fingerprint import content_tokens  # noqa: E402


def test_markup_is_invisible_to_the_signature():
    """Wrapping the SAME words in different tags/markers yields the same tokens —
    the exact case a styling relocation (bdo→span, an added «DIV») produces."""
    plain = "the quick brown fox"
    assert content_tokens(plain) == ["the", "quick", "brown", "fox"]
    assert content_tokens("<div><span>the quick</span> brown fox</div>") == \
        content_tokens(plain)
    assert content_tokens("the «DIV[style:font-size:83%]»quick brown«/DIV» fox") == \
        content_tokens(plain)
    assert content_tokens("<p>the</p><p>quick brown fox</p>") == \
        content_tokens(plain)


def test_attribute_text_is_not_content():
    """Words living inside a tag (href, style, class) are markup, not article text,
    and must not count — else a link's URL would look like content."""
    assert content_tokens('<a href="http://swallow.example/prose">go</a>') == ["go"]
    assert content_tokens('<span style="font-size:smaller">x</span>') == ["x"]


def test_entities_decode_to_their_word():
    assert content_tokens("caf&eacute; &amp; bar") == content_tokens("café & bar")


def test_losing_words_changes_the_signature():
    """The whole point: dropping a run of words is visible."""
    full = content_tokens("alpha beta gamma delta epsilon")
    swallowed = content_tokens("alpha beta epsilon")        # gamma delta eaten
    assert full != swallowed
    assert len(swallowed) < len(full)


def test_reordering_words_changes_the_signature():
    """Sequence, not a bag — a swallow that also transposes is still caught."""
    assert content_tokens("alpha beta gamma") != content_tokens("gamma beta alpha")
