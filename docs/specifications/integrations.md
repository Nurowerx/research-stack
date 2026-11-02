# Independent integration contracts

## Epistemic Trust Lab export reader

`nx_adapters.exports.read_etl_directory(folder)` reads `metadata.json`, `benchmark.json`, `config.json`, and `observations.jsonl`. It never imports ETL source code, invokes its service, writes to its folder, or changes its results.

The accepted export is schema 1.0, complete, synthetic, and has zero research participants. The adapter verifies observation/benchmark/configuration digests using ETL's documented JSON canonicalization (ASCII escaping, sorted keys, compact separators). It checks unique `(case_id, adapter, memory, distraction)` identities and declared observation/case counts. These checks establish consistency of the supplied export, not independent validation of its scoring methodology or original source code.

`import_etl(trace, project_id, data)` stores the complete external export as a content-hashed dataset version, one original data source, and individual observation records linked to that dataset. External rows remain under `external_observation` and are not converted into native LOOP scores or counted as new model executions. The UI can inspect these TRACE records; native LOOP charts operate on native runs.

```powershell
nx-stack import-etl --folder path/to/reference-export --project PROJECT_UUID
```

The bundled verification record reports the actual local reference export: 240 synthetic cases, 5,760 imported observations, 5,763 TRACE records and 5,761 relationships. No existing ETL code or files were modified. Original raw ETL exports are not redistributed in this source archive; the user's local imported database retains them.

## Resident Model Lab representative contract

`ResidencyExport` accepts `schema_version: nx-residency-fixture-1`, requires `representative_fixture: true`, and validates rows containing case ID, strategy, memory budget in MiB-equivalent labeled MB, resident expert count, latency in milliseconds, peak memory in MB, and output-match boolean. The fixture contains three invented, conspicuously labeled example rows solely for contract/UI development.

No real Resident Model Lab run was accessed or imported. Its measurements are not added to LOOP or presented as findings. Before a real integration, agree on memory units, timing boundaries, hardware/model metadata, output-equivalence definitions and immutable source manifests; introduce a separate schema that does not carry the representative-fixture flag.

## Evaluation target extension

Implement `name`, `version`, and `predict(query: QueryInput, parameters: dict[str, JsonValue]) -> Prediction`. Optional `kind` describes the target, and `validate_parameters` rejects inappropriate configurations. Register it with `TargetRegistry.register`, then construct `LoopEngine(trace, registry)`. A target receives only query inputs, never expected-answer fields. Ground truth remains in the scorer.

The default console exposes the two bundled deterministic policies. New providers can use the Python registry and API composition root; no paid-provider adapter, model download, agent sandbox or credentials service is bundled. Custom targets must map their outputs to the current answer/evidence contract or introduce a separately validated scorer and benchmark schema.
