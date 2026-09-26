"""Exercise packaged native search using the real JS helper and SQLite store."""
import json
from pathlib import Path
import shutil
import re
import subprocess
from urllib.parse import quote, unquote

import pytest

from britannica.mdx.build import article_key, label_content_entries, add_headwords, wrap
from britannica.mdx.native import package_search


@pytest.fixture
def edition(tmp_path):
    root = Path(__file__).resolve().parents[2]
    articles = {
        'swift': {'title':'SWIFT, JONATHAN', 'volume':1, 'page_start':1},
        'metal': {'title':'MERCURY', 'volume':1, 'page_start':2},
        'god': {'title':'MERCURY', 'volume':1, 'page_start':3},
        'descartes': {'title':'DESCARTES, RENÉ', 'volume':1, 'page_start':4},
    }
    aliases = {'JONATHAN SWIFT':{'swift'}, 'MERCURY':{'metal','god'}, 'RENE DESCARTES':{'descartes'}}
    for stem, a in articles.items():
        a['body'] = stem
        aliases.setdefault(a['title'], set()).add(stem)
    entries = {article_key(s): wrap('<h1>'+a['title']+'</h1><img src="images/test.png">'
               '<a href="entry://EB1911%3Aarticle%3Ametal#section-history">link</a>'
               '<a href="#note-1">note</a>') for s,a in articles.items()}
    add_headwords(entries, articles, aliases)
    entries, keys = label_content_entries(entries, articles)
    clean, files = package_search(tmp_path, entries, keys, articles, aliases, '.eb1911{color:black}', root)
    (tmp_path/'search/binding.json').write_text(json.dumps({'dictionaryId':'test-id'}))
    return tmp_path, clean, keys


def lookup(folder, query, article=False):
    node = shutil.which('node')
    if not node:
        pytest.skip('Node is required for native search integration')
    args = [node, '--no-warnings', str(folder/'search/lookup.cjs'), str(folder/'search/titles.json')]
    if article:
        args += ['--article', str(folder/'search/articles.sqlite'), str(folder/'search/binding.json')]
    return subprocess.run(args, input=query, encoding='utf-8', capture_output=True, check=True).stdout


def test_native_names_are_unique_and_hidden(edition):
    folder, clean, keys = edition
    assert 'JONATHAN SWIFT' not in clean
    assert lookup(folder, 'Jonathan Swift').splitlines() == ['SWIFT, JONATHAN']
    assert lookup(folder, 'swift jonathan').splitlines() == ['SWIFT, JONATHAN']
    assert lookup(folder, 'Rene Descartes').splitlines() == ['DESCARTES, RENÉ']
    assert len(lookup(folder, 'mercury').splitlines()) == 2
    assert all('Articles named' not in key for key in clean)


def test_native_resolution_resources_fragments_and_duplicates(edition):
    folder, _, keys = edition
    # The link carries the DISPLAY key now: the stable identifier is no longer a
    # headword, so nothing could resolve it.  Read it from the map rather than
    # pinning a literal, which would only restate what the code just computed.
    metal = quote(keys[article_key('metal')], safe='')
    body = lookup(folder, 'Jonathan Swift', True)
    assert '<h1>SWIFT, JONATHAN</h1>' in body
    assert 'bres://test-id/images/test.png' in body
    assert f'word={metal}&amp;group=4294967294&amp;gdanchor=section-history' in body
    assert 'href="#note-1"' in body
    assert lookup(folder, 'SWIFT, JONATHAN', True) == ''
    assert lookup(folder, 'EB1911:article:swift', True) == ''
    choices = lookup(folder, 'mercury', True)
    assert 'Choose an article' in choices
    assert choices.count('<li>') == 2
    # encodeURIComponent leaves `()` literal where Python's quote escapes them;
    # both decode to the same headword, which is the claim being made.
    assert keys[article_key('metal')] in [
        unquote(w) for w in re.findall(r'\?word=([^&"]+)', choices)]
    assert lookup(folder, 'nonexistentname', True) == ''


def test_installer_preserves_config_and_binds_portable_resources(edition, monkeypatch):
    from britannica.mdx.install_search import install
    from xml.etree import ElementTree as ET
    folder, _, _ = edition
    reader = folder/'reader'
    (reader/'portable').mkdir(parents=True)
    (reader/'goldendict.exe').write_bytes(b'fixture')
    config = reader/'portable/config'
    config.write_text('<config><preferences><ignoreDiacritics>0</ignoreDiacritics>'
                     '<custom>preserved</custom></preferences><programs>'
                     '<program id="unrelated" enabled="0"/></programs></config>')
    (folder/'manifest.json').write_text(json.dumps({'native_search':True, 'edition':'complete', 'article_count':4}))
    for ext in ('mdx','mdd'):
        (folder/('Britannica11.'+ext)).write_bytes(b'fixture')
    actual_run = subprocess.run
    def run(args, **kwargs):
        if args[0] == 'tasklist':
            return subprocess.CompletedProcess(args, 0, stdout='No tasks', stderr='')
        return actual_run(args, **kwargs)
    monkeypatch.setattr(subprocess, 'run', run)
    install(folder, reader, shutil.which('node'))
    install(folder, reader, shutil.which('node'))
    tree = ET.parse(config)
    assert tree.findtext('preferences/custom') == 'preserved'
    assert len(tree.findall('programs/program')) == 3
    assert tree.findtext('preferences/ignoreDiacritics') == '1'
    binding = json.loads((reader/'content/search/binding.json').read_text())
    assert binding['dictionaryId'] == '149fc35a1954586eac330c2aa7075e74'
    for program in tree.findall('programs/program'):
        if program.get('id').startswith('eb1911-'):
            assert '%GDWORD%' not in program.get('commandLine')
            assert '--no-warnings' in program.get('commandLine')
