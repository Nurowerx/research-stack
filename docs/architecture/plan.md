# Nurowerx Research Stack: implementation plan

## Working core and boundaries

Build a modular local application on port 8876. TRACE owns append-only, versioned research records and typed graph edges. LOOP executes deterministic evidence-retrieval policies against immutable synthetic benchmark versions and records measured outputs. LENS renders result-linked analytical components. FRAME composes the workbench and persists layouts. Dependencies flow from shared schemas into TRACE/LOOP and into independent frontend component libraries; packages never depend on the integrated console.

## Execution milestones

1. Define typed ontology, version/hash semantics, SQL migrations, synthetic evidence fixtures and validated graph operations.
2. Implement independently callable evaluation targets, transparent metric numerators/denominators, immutable result records, accepted correction configuration patches and paired comparisons.
3. Expose project, provenance, benchmark, execution, review and export APIs. Run the whole workflow through the backend before building UI.
4. Build evidence-aware charts, a keyboard-accessible graph and alternative tables. Compose them in a graphite/copper research console with saved resizable panels.
5. Implement representative integration adapters, inspect available Epistemic Trust Lab export contracts read-only, and verify any claimed import against actual data.
6. Exercise API, scientific calculations, correction history, browser workflows, accessibility and clean installation. Package source, sample reports, screenshots and precise documentation.

## Experimental design

The baseline uses 120 seeded synthetic cases spanning lookup, revision, conflicting evidence, missing evidence, distractors and recovery. Development and held-out instances are explicitly separated. Deterministic policies receive visible evidence and a query, never the ground-truth answer. Both naive and evidence-aware policies are actually executed. Recorded runtime measurements are separated from deterministic semantic outputs.

Corrections are proposed on development failures as named algorithm-rule changes. Human reviews append records; conflicting reviewer decisions block application. Accepted changes create a fresh configuration and execution. Affected-only reruns identify their scope, and comparisons use paired overlapping cases. Historical outputs are never rewritten. Held-out cases are barred from interactive correction authoring to reduce direct answer leakage.

No population confidence intervals or significance tests are attached to this fixed synthetic fixture census. Comparisons are descriptive paired changes with explicit denominators. Confidence calibration is unavailable for policies that do not emit validated probabilities. Repeated deterministic outputs measure consistency, not independent experimental replication.

## Deployment scope

Default trusted, single-user loopback operation requires no API keys. Optional reader/writer tokens protect a shared deployment; remote serving requires a configured write token and a TLS reverse proxy. SQLite is the tested local persistence target; PostgreSQL compatibility is optional and must be labeled according to actual validation. Existing Nurowerx repositories, website and the VEYDRIS implementation are outside the modification scope.
