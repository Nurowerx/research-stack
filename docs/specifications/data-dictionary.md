# Data dictionary and metric definitions

## Core records

| Field | Meaning |
|---|---|
| `id` | UUID identifying one immutable record/version |
| `project_id` | Owning workspace; graph edges cannot cross project boundaries |
| `logical_id` | Stable identity shared by successive versions |
| `version` | Positive revision sequence; unique with logical ID |
| `kind` | Shared research ontology enum |
| `label` | Human-readable name, up to 200 characters |
| `payload` | Typed-required fields plus JSON extension fields; non-finite values rejected |
| `content_hash` | SHA-256 of canonical `{kind,label,payload}` JSON |
| `actor` | Attributed researcher label, not authenticated identity proof |
| `created` | UTC Unix timestamp in seconds |

The ontology includes project, dataset, dataset version, data source, observation, experimental scenario, experiment, model, model version, algorithm, configuration, execution, output, claim, evidence, evaluation, metric, annotation, correction, researcher, review and conclusion. Required payload fields include claim/conclusion `statement`, source `origin`, configuration `parameters`, annotation `text`, and dataset-version `content_hash`. Additional domain-specific payloads can be validated by adapters.

Relations include `derived_from`, `generated_by`, `evaluated_against`, `supported_by`, `contradicted_by`, `depends_on`, `reviewed_by`, `corrected_by`, `supersedes`, `associated_with`, and `belongs_to_experiment`. Evidence relationships must start at a claim/conclusion and point to evidence/observation/output. `generated_by` must point to an execution. Causal derivation/dependency/supersession cycles are rejected. `supersedes` must point backwards within one logical identity.

## Evaluation fields

`benchmark_id`, `config_id`, and `execution_id` reference version-specific TRACE records. `split` is development or heldout. `scope` is full_split or selected_cases. `status` is running, complete or failed. A result records `case_id`, zero-based `repeat`, `family`, `prediction`, `scores`, `latency_ms`, `output_id`, and `claim_id`. `semantic_digest` hashes ordered case/repeat/family/prediction/scores values, excluding timing and generated IDs.

## Metrics

| Metric | Numerator | Denominator / unit |
|---|---|---|
| Accuracy | Exact expected answers, including appropriate abstention | All unique cases |
| Unsupported assertion rate | Non-abstaining answers differing from the synthetic oracle | Non-abstaining cases |
| Evidence consistency | Answered outputs citing at least one visible item, with every cited item matching the answer | Answered cases; consistency is not truth |
| Retrieval precision | Unique cited IDs intersecting oracle evidence IDs | Unique cited IDs |
| Retrieval recall | Unique cited IDs intersecting oracle evidence IDs | Oracle evidence IDs; unresolved cases contribute zero denominator |
| Appropriate abstention | Abstentions where the expected answer is absent | Unresolved cases |
| Memory fidelity | Correct revision-family cases | Revision-family cases; fixture-specific name |
| Error recovery | Correct recovery-family cases | Recovery-family cases |
| Output consistency | Cases with identical repeated prediction objects | Cases with two or more executions |
| Correction success | Previously imperfect shared cases that become fully correct | Previously imperfect shared cases |
| Latency | Arithmetic mean of measured prediction-call durations | Milliseconds; `n` counts calls |
| Resource utilization | Process RSS before/after; overall run wall time | Bytes and seconds; snapshots, not isolated peak usage |
| Confidence calibration | Not calculated for these non-probabilistic targets | Null with explanation |

Repeated observations are averaged within case before ratio aggregation. For a stochastic custom target, weighted numerators can be fractional. Zero denominators stay null. The implementation emits raw per-result numerator/denominator pairs for auditing.

## Human review

A correction contains `run_id`, `case_id`, `benchmark_id`, proposed `rule`, boolean `patch`, `rationale`, and `actor`. A review contains `correction_id`, `decision` (accept/reject), `rationale`, and `actor`. Latest-per-actor votes derive pending/accepted/rejected/disputed state without changing any review records. An annotation contains `text`; an `interpretation` extension explicitly separates it from a measurement.
