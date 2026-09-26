# Britannica Edition

A pipeline and datastore for producing a faithful digital scholarly edition of the 11th Encyclopaedia Britannica.

## Principles

- Source-first
- Reproducible transforms
- Auditable editorial intervention
- Article as primary unit, page as provenance unit
- Publication is derived output

## Status

Repo scaffold.

## License

The **code** in this repository is released under the [MIT License](LICENSE).

The **text** is not. The Encyclopædia Britannica's text comes from
[Wikisource](https://en.wikisource.org/) under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), and everything
derived from it stays under that license: the site, the corpus downloads, the
TEI, EPUB and MDX editions, and the source text quoted in files under `data/`
(for example the literal readings in `data/corrections.json`). Each published
bundle carries its own `LICENSE` with the attribution it requires.
