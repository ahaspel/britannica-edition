"""Re-read pages for their TABLES through the Batch API (half price, within a
day): the engine's batch run (`wikikit.scan.batch`) with its output set to
data/readings/tables/ — never data/supplied/ (a build would read it) and no
figure crops (they would overwrite the book's images).  The run's state is the
engine's own (data/derived/scan_batch/state.json): stop and resume at will.

    read_tables.py add VOL:WS [VOL:WS ...]   put pages into the run, one step
    read_tables.py                            advance the run one step
    read_tables.py --wait                     advance until every page is done

Usage from the book root, with --env-file .env."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))
from paths import TABLE_READINGS

from wikikit.corpora import current_corpus
from wikikit.scan import batch


def main(argv: list[str]) -> int:
    book = current_corpus()
    scan, scan_url = book.page_scan, book.page_scan_url
    if argv and argv[0] == "add":
        pages = [tuple(map(int, a.split(":"))) for a in argv[1:]]
        batch.add_pages([(v, p, scan_url(v, p)) for v, p in pages], scan, out=TABLE_READINGS)
        print(f"{len(pages)} page(s) in the run, written to {TABLE_READINGS}/ when done")
    if "--wait" in argv:
        batch.run_until_done(scan)
    else:
        print(json.dumps(batch.advance(scan), default=str, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
