# Contributing

Start with the [installation guide](docs/installation/README.md). Discuss substantial changes in an issue before implementing them. Use a feature branch and a pull request; include the concrete problem, resulting behavior, and validation evidence.

Run `python -m ruff check .`, `python -m ruff format --check .`, `npm run format:check`, `npm run check`, `python -m pytest`, `npm test`, and `npm run build`. Run `python scripts/clean_install.py --destination <new-directory>` for changes affecting workflows or installation. The destination must be outside the source tree.

Keep research observations distinct from fixtures. Never replace recorded results with hand-edited successful results. Include failing controls for integrity changes. Semantic digests omit timing and identity fields deliberately; explain any change to their definition. Describe fixture revisions and regenerate the manifest.

Contributions to software are submitted under MIT; contributions to original benchmark data and papers under CC BY 4.0. Do not submit private datasets, credentials or material you cannot redistribute. Declare third-party origins and preserve applicable notices. Maintainers review contributions; passing tests does not establish scientific validity or guarantee acceptance.
