# Reproduction protocol

From a fresh clone, run `python scripts/clean_install.py --destination ../nrs-reproduction`. This creates a new source copy, Python virtual environment, npm installation and SQLite database; installs pinned dependencies; runs the full test suite and NRS-Bench; builds and starts the application; tests the browser workflow and Vite proxy; and reproduces the committed affected-case report. It refuses to overwrite an existing destination. A network connection is needed for uncached dependencies. Public dependency caches may be reused.

The output directory contains individual command logs, pytest.xml, browser-results.json, screenshots, nrs-bench/summary.json, eighteen raw experiment reports, and clean-install.json. CI runs this workflow on Linux, Windows and macOS and retains artifacts for 30 days. The release research archive retains selected versioned observations beyond CI retention.

Run `python scripts/generate_datasets.py` to regenerate fixtures, then inspect `git diff --exit-code -- datasets` for byte equality. Every dataset hash is checked by the benchmark runner. It compares known answers, paired outcomes, graph reachability and exact export/import preservation, with independent SciPy verification of the illustrative normal interval. Backend tests cover adversarial inputs; chart tests verify SVG coordinates; browser tests verify keyboard filtering, exports, saved layouts and visible failures.

The semantic digest hashes case IDs, repeat indices, families, predictions and scores. UUIDs, timestamps, latency and memory vary and are excluded. A match establishes result reproduction with the installed implementation, not authenticity or truth. It does not automatically retrieve historical source. Preserve the source commit and dependency locks with the report.

The original 31-test baseline was rerun separately before release changes. New tests are a separate validation set. All executions described here are developer-controlled. CI on other machines is automated cross-platform reproduction, not reproduction by an independent research group. PostgreSQL remains an unverified deployment target.
