# Historical development evidence — before public-release changes

# Engineering delivery report

**Nurowerx Research Stack 0.1.0 — 2 November 2026**

The local implementation provides the complete dataset → provenance → evaluation → visualization → failure inspection → correction → review → rerun → paired comparison → reproducible report workflow. The development instance used loopback port 8876. This historical report does not assert that a service is currently running.

## Built and verified

| System | Delivered behavior |
|---|---|
| TRACE | Typed ontology; real relational graph edges; version IDs and hashes; append-only database guards; bounded graph traversal; claim assessment and incomplete-lineage states; historical inspection and exports |
| LOOP | Actual deterministic target execution; 120-case seeded benchmark with separate splits; target protocol; configuration/source/environment snapshots; transparent per-result scoring; failed-run recording; review disagreements; affected/full reruns; regression and correction-success comparisons; JSON/CSV reports and digest reproduction |
| LENS | Reusable evidence-linked bars, scatterplots, histograms, time series and graphs; shared filters; zoom/pan; alternative tables; optional supplied interval bounds; actual SVG/CSV exports |
| FRAME | Project and dataset management; execution setup; comparison workspace; source inspector; annotations and immutable revisions; correction review; saved layouts; resizable panels; responsive and accessible navigation |

The repository includes FastAPI, SQLAlchemy and Pydantic backend modules; a React/TypeScript/Vite console; shared JSON schemas; OpenAPI export; Alembic migration; locked dependencies; executable examples; documentation; screenshots; and example reports.

## Validation results

| Check | Result |
|---|---|
| Python unit and API tests | **23 passed** |
| LENS chart-data tests | **3 passed** |
| Playwright browser tests | **5 passed**, no skipped/flaky tests |
| Accessibility | Zero automated WCAG A/AA violations in the five rendered workspace views and the tested mobile dataset view |
| Mobile behavior | Verified at 390 × 844; viewport overflow fixed and analytical tables retain internal scrolling |
| TypeScript and Vite | Type check and production build passed |
| Python static import/undefined-name checks | Ruff F checks passed |
| Clean installation | Fresh source copy, new venv, locked pip/npm installs, new SQLite database and migration, seeded evaluations, production server, Vite frontend/proxy, and full browser suite passed |
| Semantic reproduction | Corrected report reproduced in a new temporary database with matching SHA-256 digest |

The clean check used Python 3.11.9 and Node 24.20.0 on Windows and completed in approximately 110 seconds, reusing public dependency caches. [Machine-readable clean-install evidence](verification/clean-install.json), [Python results](verification/python-tests.xml), and [browser summary](verification/browser-summary.json) accompany this report.

Two non-failing dependency deprecation warnings were observed in the Python test runner: Starlette's current TestClient warns about its HTTPX compatibility path, and HTTPX warns about a legacy request-upload argument in an access-control test. Neither warning represents a failed application check. Broader assistive-technology testing and other operating systems remain unverified.

## Reference observations

The fixture contains 120 unique synthetic cases, split 60 development / 60 held-out. Full-split runs use two repeats, producing 120 predict calls per run.

- First-match development accuracy: **10/60 (16.7%)**.
- Evidence-aware development accuracy: **60/60 (100%)**.
- Evidence-aware held-out accuracy: **60/60**, on instances from the same generator.
- Latest-revision correction: the affected case changed from incorrect to correct. Its comparison contains exactly **one shared case**.
- Full development rerun with that correction: **30/60 (50%)**; 20 cases improved and no shared cases regressed.

These are actual executions of programmed synthetic policies. They are not model benchmarks, participant research, or evidence of generalization to real data. Latency and memory snapshots are measured locally and disclosed with their scope. No unsupported confidence intervals or significance claims are displayed.

## Existing-project integration

The independent Epistemic Trust Lab adapter verified and imported the existing reference export: **240 synthetic cases and 5,760 observations**. It checked three content digests, identities and counts; TRACE integrity checked 5,763 records and 5,761 edges. This is a functional read-only export import, not a new ETL experiment or shared execution service.

Resident Model Lab is represented by a validated, explicitly synthetic contract fixture only. No live integration is claimed. Existing project repositories, the Nurowerx website and remote GitHub repositories were left unchanged.

## Run and inspect

Use the current root README for portable installation. Local development paths have been removed from this historical report. The [reference workflow summary](../examples/model-evaluation/workflow-summary.json) links every demonstration run and correction by stable ID.

The delivered source archive includes built frontend assets, all application sources, dependency locks, schemas, tests, reports and screenshots. It excludes installed dependencies, caches, live databases and unrelated projects. The live local database remains available in the dedicated runtime directory.

## Remaining boundaries

Real-model providers, production multi-user identity/authorization, distributed or cancellable execution, PostgreSQL validation, advanced statistical inference, arbitrary chart composition and a real Resident Model Lab adapter remain future work. The implemented core workflow is operational. These limits and the next development sequence are detailed in the [roadmap](roadmap.md).
