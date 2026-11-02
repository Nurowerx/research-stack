# Service contract

The local service exposes OpenAPI at `/openapi.json` and interactive documentation at `/docs`. Request schemas are generated directly from Pydantic. The checked-in `openapi.json` and shared JSON schema files are exported from the implemented application, not hand-authored placeholders. Frontend response interfaces are in `apps/research-console/src/types.ts`.

All mutations use JSON. Unknown request fields, invalid enum values and non-finite measurements are rejected. Missing records return 404, validation failures 422, immutable/conflicting persistence 409, untrusted mutation origins 403, and absent/insufficient access tokens 401. Tokens use `Authorization: Bearer …`.

| Method | Path | Behavior |
|---|---|---|
| GET | `/api/health` | Version, access mode and baseline disclosure |
| GET | `/api/ontology` | Entity, relationship and assessment enums |
| GET / POST | `/api/projects` | List/create projects |
| GET / POST | `/api/projects/{id}/records` | Query/create typed research records |
| GET | `/api/records/{id}` | Record, immutable version history, incoming/outgoing edges |
| POST | `/api/records/{id}/versions` | Append version with optimistic `expected_version` |
| GET | `/api/records/{id}/claim-state` | Assessed support/contradiction and source-lineage status |
| POST | `/api/edges` | Add validated typed relationship |
| GET | `/api/projects/{id}/graph` | Rooted traversal; `root`, `depth` 0–5, relation filter, `limit` up to 500 |
| GET | `/api/projects/{id}/integrity` | Verify record/edge content hashes |
| GET | `/api/projects/{id}/export` | Full project records, relationships and integrity result |
| POST | `/api/projects/{id}/fixtures` | Generate/register synthetic benchmark using seed and cases-per-family |
| POST | `/api/projects/{id}/benchmarks` | Register a validated synthetic Benchmark JSON document |
| GET | `/api/benchmarks/{id}` | Full benchmark and its provenance record |
| GET | `/api/targets` | Registered target names, versions and kinds |
| GET | `/api/projects/{id}/runs` | Evaluation summaries and lifecycle |
| POST | `/api/runs` | Execute actual evaluation synchronously |
| GET | `/api/runs/{id}` | Summary plus individual measured results |
| GET | `/api/compare?before=…&after=…` | Paired, same-version/split comparison |
| GET | `/api/runs/{id}/report` | Reproducible JSON report |
| GET | `/api/runs/{id}/results.csv` | Measured result table; spreadsheet formula cells escaped |
| POST | `/api/corrections` | Propose rule change for failed development case |
| GET | `/api/projects/{id}/corrections` | Corrections with derived current review state |
| GET | `/api/corrections/{id}` | Correction and full review history |
| POST | `/api/corrections/{id}/reviews` | Append attributed accept/reject decision |
| POST | `/api/corrections/{id}/rerun` | Apply accepted patch to parent effective config; affected or full split |
| GET / POST | `/api/projects/{id}/layouts` | Read/save workspace configuration snapshots |

Record-list responses omit very large external raw export payloads. The individual record and full project export endpoints retain them. Graph traversal reports truncation; a bounded display is not evidence that other relationships do not exist.

## Example request

```json
{
  "benchmark_id": "DATASET_VERSION_UUID",
  "target": "first-match",
  "split": "development",
  "repeats": 2,
  "parameters": {},
  "case_ids": [],
  "correction_ids": [],
  "actor": "Researcher name"
}
```

An empty `case_ids` list means the entire selected split. `parameters` supports JSON values for custom target adapters; bundled evidence-policy parameters are strictly boolean and restricted to the four documented rules. Every applied correction must belong to the same benchmark version and have an undisputed acceptance. The parent-run field preserves comparison lineage.

Use the high-level correction-rerun endpoint to inherit the parent's effective parameters. A direct `/api/runs` request is an explicit configuration and must supply any desired inherited settings itself.

## Validated graph exchange

`GET /api/projects/{id}/bundle` returns a schema-versioned TRACE snapshot. `POST /api/import/provenance` validates identities, histories, hashes and edges, then imports atomically. Identical repeat imports add zero rows. This does not reconstruct runnable LOOP database rows. Requests with an untrusted Host header are rejected with HTTP 400.
