# NRS-Bench: A Reproducible Benchmark Suite for Evidence Provenance, Evaluation, Correction, and Research Workflows

Spencer H. Walker · Nurowerx · [ORCID 0009-0005-3574-1057](https://orcid.org/0009-0005-3574-1057)

Technical report, version 1.0, 2 November 2026. Software: NRS 0.1.0. CC BY 4.0. Not peer reviewed. AI-assisted implementation and manuscript preparation; all empirical claims below refer to executed software observations. No participants, independent replication, university sponsorship or DOI are claimed.

## Abstract

NRS-Bench 1.0.0 is a versioned collection of original synthetic fixtures and executable protocols for a research software stack. It covers provenance integrity, semantic repetition, correction and regression, numerical visualization, complete research workflows, robustness and interface integrity. Data manifests record origin, generation, schema, seed, hashes and limitations. The reference execution comprises three seeded evaluation datasets and 18 runs, accompanied by backend, chart and browser controls. This report specifies reuse and interpretation. NRS-Bench is a bounded software-validation suite, not a general leaderboard for AI intelligence or research quality.

## 1. Motivation and intended use

A useful validation package must expose its inputs and failure expectations. NRS-Bench supplies known answers for relationships and predictions, explicit corrupted cases and a protocol connecting raw outputs to displayed results. The design draws on provenance concepts [1], executable scientific software practices [2], reproducibility reporting [3] and dataset documentation [6]. Its intended users are developers and researchers auditing or extending NRS. Reuse for another system requires an adapter and a declared equivalence of task semantics.

## 2. Dataset construction and schemas

Three evaluation files are generated with seeds 13, 42 and 20261102. Each contains 120 cases, with six families and equal development/heldout partitions. A case specifies identity, family, split, query evidence, expected answer and acceptable evidence IDs. Lookup requires ordinary retrieval; revision and recovery require selecting newer evidence; conflict and missing cases exercise abstention; distractor cases separate relevant trusted evidence from misleading alternatives. The implementation source is the normative generator and the JSON Schema defines the contract.

The provenance fixture has seven symbolic nodes: source, dataset, algorithm, execution, output, evidence and claim. Six typed relationships form a traceable chain with an algorithm branch. The exact reachable set is listed rather than computed by the implementation under test. Missing endpoints and cycles are invalid controls; contradictory assessments represent a valid conflicting state. Runtime UUIDs are separate from symbolic fixture identities.

The visualization fixture supplies values 0.2, 0.4, null, 0.6 and 0.8, whose observed mean is 0.5 with n=4 and one missing value. A normal-interval example supplies mean 0.5, known sigma 1, n=100 and 95% confidence. Its bounds are 0.3040036015459946 and 0.6959963984540054. This is a mathematical fixture, not a sample of NRS accuracy. Time-series values include a negative value, a missing sample and an outlier. A deterministic 10,000-value array checks that histogram bins retain every input.

## 3. Task definitions and protocols

| Category | Protocol and known answer | Executable evidence |
|---|---|---|
| 1. Provenance integrity | Traverse seven expected nodes; exchange graph exactly; reject missing/cyclic/corrupt links without partial commits | scripts/benchmark.py; tests/test_trace.py; tests/test_release.py |
| 2. Evaluation reproducibility | Execute identical inputs twice; compare semantic digest and exact denominators | scripts/benchmark.py; tests/test_loop.py |
| 3. Correction and regression | Require accepted review; preserve original run; compare affected and full scopes; detect a deliberate downgrade | scripts/benchmark.py; tests/test_loop.py |
| 4. Visualization fidelity | Match independent SVG coordinates, mean, interval, outliers, gaps and histogram counts | packages/nx-lens/src/benchmark.test.tsx; release-regression.test.tsx |
| 5. Complete workflow | Register dataset, execute, inspect, review correction, rerun, compare and export | tests/integration/test_api.py; tests/end-to-end/workflow.spec.ts |
| 6. Robustness | Invalid fields/identities, absent evidence, disputes, repeated imports, target exception, hard exit and bounded load | Backend controls plus 501-record and 10,000-value fixtures |
| 7. Interface integrity | Keyboard linked filtering, source-preserving SVG, persisted layout, visible failure, accessibility and mobile assertions | tests/end-to-end/workflow.spec.ts |

```mermaid
flowchart LR
  G[Generator + explicit oracles] --> M[Versioned inputs + manifest]
  M --> E[Execution and negative controls]
  E --> O[Raw reports + test logs]
  O --> C[Assertions + paired comparison]
  C --> P[Documented results and limits]
```

*Figure 1. Reproduction flow. Original inputs are preserved separately from research observations and presentation.*

## 4. Metrics and reference expectations

Correctness is a per-case comparison with expected answers. Accuracy aggregates unique cases, not repeat calls. Evidence measures retain their own eligibility denominators; undefined rates remain null. Reproducibility is exact semantic-digest agreement. Graph completeness is equality with the listed reachable set. Integrity controls succeed only when the expected rejection occurs and the destination remains unchanged. Visualization error is the difference between expected and rendered coordinates, with tolerance 1e-10 for SVG mapping and 1e-12 for the independent interval calculation.

The reference development results are 10/60 for first-match, 60/60 for evidence-aware and 30/60 for the reviewed prefer-latest full rerun. The selected revision case yields 1/1. Heldout evidence-aware yields 60/60. These outcomes repeat across the three seeds. A valid implementation need not achieve a particular speed; stress timings are observations, not pass thresholds. Test counts report the suite execution, not a calibrated measure of overall software quality.

## 5. Validation and versioning

Manifest SHA-256 values identify exact UTF-8 fixture bytes. Regeneration and evaluation verify those hashes before running comparisons. The backend validates schemas and stores execution configuration and source hashes. Imported graph snapshots validate identities, histories and hashes atomically. Tests preserve failure evidence, including the four frontend regressions observed before repair. The release clean-install run passes 54 tests and reproduces the reference report digest.

Benchmark version 1.0.0 is distinct from software version 0.1.0. Changes to ground truth, case inclusion or schema require a new benchmark version and regenerated manifest. New software implementations should retain prior raw observations rather than overwrite them. A changed timing is not a semantic failure; a changed prediction, score or expected relationship requires investigation. Published summaries must point to the tested code commit.

## 6. Reuse instructions

Clone the release and install requirements-lock.txt plus editable source and npm dependencies. Run `python scripts/generate_datasets.py` and inspect fixture diffs. Run `python scripts/benchmark.py --output results/nrs-bench`, `python -m pytest`, `npm test` and the full clean-install script for browser coverage. The reproduction package includes data, generators, schemas, raw outputs, figures and instructions. Figure generation has a separate pinned dependency file. Cite the software and dataset version, and preserve attribution under CC BY 4.0 for original datasets. The code is MIT.

To compare another system, document any mapping of records, relations, nulls, review states and digest fields. Keep exact tasks and denominators visible. Do not claim comparability from a shared category name alone. Public Palantir references [8] are not an executed benchmark participant. No external dataset is redistributed.

## 7. Limitations and ethical scope

The suite contains no personal research data or human participants. Synthetic review actors do not represent independent reviewers. The deterministic targets and their ground truth share a designed task structure. The normal interval is an illustrative analytic fixture. Automated interface correctness does not establish human decision quality or accessibility in every assistive environment [4,5]. Large-enterprise workloads, network partitions, distributed scheduling and real model drift are outside version 1.0.0.

Tests can detect designated failures but cannot certify the absence of all defects. Hashes do not authenticate a malicious source. External replication has not yet occurred. The appropriate next step is to publish and investigate independently reproduced results, then expand task diversity and scale based on observed gaps.

## 8. Conclusion and availability

NRS-Bench makes a bounded validation protocol inspectable: inputs, expected answers, transformations, negative controls and measured outputs are available together. It supports reproducible testing of evidence-centered workflows while keeping synthetic success distinct from scientific validity. The dataset and source are included in https://github.com/Nurowerx/research-stack/releases/tag/v0.1.0; separate archival metadata is prepared without inventing a DOI.

## References

1. Moreau, L., and Missier, P., eds. (2013). *PROV-DM: The PROV Data Model*. W3C Recommendation, 30 April 2013. https://www.w3.org/TR/2013/REC-prov-dm-20130430/
2. Wilson, G., et al. (2014). Best Practices for Scientific Computing. *PLOS Biology*, 12(1), e1001745. https://doi.org/10.1371/journal.pbio.1001745
3. Pineau, J., et al. (2021). Improving Reproducibility in Machine Learning Research (A Report from the NeurIPS 2019 Reproducibility Program). *JMLR*, 22(164), 1–20. https://www.jmlr.org/papers/v22/20-303.html
4. Munzner, T. (2009). A Nested Model for Visualization Design and Validation. *IEEE TVCG*, 15(6), 921–928. Author publication record: https://www.cs.ubc.ca/labs/imager/tr/2009/NestedModel/
5. Amershi, S., et al. (2019). Guidelines for Human-AI Interaction. *CHI 2019*. Author publication record: https://www.microsoft.com/en-us/research/publication/guidelines-for-human-ai-interaction/
6. Gebru, T., et al. (2021 revision). Datasheets for Datasets. arXiv:1803.09010v8. https://arxiv.org/abs/1803.09010v8
7. Ribeiro, M. T., Singh, S., and Guestrin, C. (2016). “Why Should I Trust You?”: Explaining the Predictions of Any Classifier. arXiv:1602.04938v3. https://arxiv.org/abs/1602.04938v3
8. Palantir Technologies. Public ontology starter, AIP community registry, Plottable and Blueprint repositories. Versions and inspected files in [the pinned reference manifest](../references/palantir-sources.json), retrieved 2 November 2026. Qualitative design references, not measured comparison systems.
