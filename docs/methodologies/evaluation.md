# Evaluation methodology

## Research question and scope

The supplied investigation asks whether explicit evidence-selection rules change the behavior of deterministic policies on fixed synthetic problems. It exercises research infrastructure and makes no empirical claim about general language models, human cognition, or organizational trust.

The seeded generator produces six families: direct lookup, revised evidence, same-revision conflict, missing relevant evidence, an untrusted distractor, and recovery from an outdated answer. For the standard seed `20261102`, each family contains 20 cases. The first ten belong to development and the remaining ten to held-out evaluation. Both splits use the same generator; this is instance holdout, not an external generalization benchmark.

Expected answers are author-defined synthetic oracle labels. The first-match target chooses the first matching item and emits `unresolved` when no item matches. The evidence-aware target filters untrusted items, prefers the latest revision, abstains on equally current conflicts, and abstains when relevant evidence is absent. Neither target is a learned model or supplies a probabilistic confidence estimate.

## Independence and denominators

Two default repeats measure output stability and local timing. They do not create two independent research cases. For correctness and evidence metrics, each unique case receives equal weight; per-repeat numerators and denominators are averaged within case before aggregation. Ratio metrics use the sum of those case-level numerators divided by the sum of case-level denominators. A zero denominator yields JSON `null`, displayed as N/A.

Latency counts actual prediction calls. It excludes scoring and persistence; it includes the target's Python execution and output validation. Reported process RSS values are snapshots before and after a run, not peak memory and not memory isolated to the target. Overall wall time includes provenance persistence up to summary construction. These observations depend on host load, warm-up and process history and are not hardware-comparison results.

## Uncertainty and comparison

The reference is a descriptive census of fixed deterministic fixtures. No confidence intervals or significance tests are justified for a population claim, so the report records their absence and reason. LENS can render supplied bounds; it does not silently manufacture them.

Comparisons require the same benchmark version and split. They join by case ID, average correctness within repeated case observations, and report paired accuracy change, improvements, regressions and unchanged cases. A change is flagged as a regression if any shared case's mean correctness decreases. Partial overlap is prominently disclosed. The affected-only rerun does not estimate full-benchmark improvement.

Correction success is the fraction of previously imperfect shared cases whose repeated outputs are all correct after the change. This is descriptive; it is not causal attribution and is not interchangeable with overall accuracy.

## Feedback and held-out discipline

Interactive rule proposals require an observed failed development case. Held-out failures cannot directly generate a proposal through this workflow. Accepted development corrections may then be evaluated on held-out cases. Reviewers are identified by attribution labels. Each review is immutable. The latest vote per reviewer determines their current position; mixed accept/reject votes yield `disputed` and block application. Earlier votes stay visible.

Corrections apply to a new configuration. They do not edit synthetic oracle values, prior outputs or historical metrics. A corrected report includes the correction and review history, parent run reference and paired comparison. Annotations and human evidence challenges remain distinct from fixture oracle assessments.

## Evidence semantics

`citation_only` means an output cited a record. It does not certify the answer. Assessed support and contradiction use `fixture_oracle` or `human_judgment`, which remain explicit in the record and inspector. A claim can be supported, contradicted, conflicting, awaiting review, or unsupported. Incomplete provenance is a separate flag: causal/evidence traversal must reach a data source. Graph proximity or membership alone cannot satisfy source lineage.

## Reproduction

Reports preserve the entire benchmark, effective configuration, individual results, execution metadata, source-file hashes, applicable corrections, and semantic digest. Reproduction runs the installed named target against the exported cases in a fresh temporary SQLite database. It compares canonical predictions and scores, excluding generated IDs, timestamps and runtime measurements. A matching digest verifies semantic agreement with the exported result; it does not prove identical hardware or source authenticity.

Target source/version metadata identifies the implementation, but automatic installation of arbitrary historical target code is not supported. Preserve the source archive and dependency locks with each report. Run the command in the report and retain its exit status and digest comparison.
