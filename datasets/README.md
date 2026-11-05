# NRS-Bench datasets 1.0.0

All files in synthetic/v1 are original **synthetic** fixtures. No public external or private enterprise observations are mixed into them. Actual NRS executions are **research observations** in research/results. Each input has an ID, version, byte SHA-256, origin, generator, seed, schema reference, protocol and limitations in manifest.json. Generators are MIT; original dataset files are CC BY 4.0.

| Dataset | Variables and ground truth |
|---|---|
| evaluation-13, evaluation-42, evaluation-20261102 | Benchmark schema in schema.json: cases contain id, family, split, input evidence and expected answer/evidence IDs. 20 instances per family, six families, 10 development and 10 heldout per family. Ground truth follows the explicit construction rules in nx_loop/fixtures.py. |
| provenance | nodes: symbolic id/kind; edges: source, target, relation; expected_reachable_from_claim: exact seven labels; missing/cycle/conflict controls are designated invalid or conflicting cases. Runtime UUIDs are assigned separately. |
| visualization | values: finite ratios or null, mean=0.5 over four observed values; interval: supplied mean and bounds; time_series: x in illustrative milliseconds and y in arbitrary units including null; histogram: values with outliers; stress_values: 10,000 deterministic integers. |

For the normal-interval example, n=100, supplied sample mean=0.5 and known population sigma=1 imply bounds 0.5 ± 1.959963984540054/10. These are illustrative sufficient statistics, not a newly sampled empirical dataset. A SciPy normal-quantile oracle checks the numbers; frontend tests independently apply the SVG linear mapping. No confidence interval is attached to fixed synthetic policy accuracy.

Regenerate with `python scripts/generate_datasets.py`. Evaluate with `python scripts/benchmark.py --output results/nrs-bench`, `python -m pytest`, `npm test` and the browser workflow via scripts/clean_install.py. Compare cases within the same dataset version and split. Report affected-case and full-split outcomes separately. Do not pool repeat calls as independent cases or seeds as independent real-world populations.

The three seeds change generated identifiers and evidence values but retain the same task-family construction. Heldout cases share that generator. The policies are intentionally aligned to those rules. This suite measures implementation consistency and controlled failure detection, not generalization, scientific truth or usability in real research practice. Changes to schemas or ground truth require a version increment and new hashes.

The two original development fixtures in datasets/synthetic are documented separately in legacy-manifest.json, with hashes and a residency-contract schema. Their representative memory/latency values are synthetic inputs, not new measurements of Resident Model Lab. The benchmark runner verifies both manifests.
