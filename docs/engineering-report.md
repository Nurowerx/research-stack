# Public release engineering report

The release preserves the existing TRACE, LOOP, LENS and FRAME implementation. The original source archive was audited and rerun from a fresh installation before changes. Its SHA-256 is `778c5dc42b80d41db7a746a7ea4f778e3d2dba78a654477e3d41beffb0f0225f` (see validation evidence for the authoritative archive hash). The original delivered application and unrelated research repositories were not modified.

Release changes address chart missing values and malformed intervals, time-series gaps, packaged migrations, repeated ETL import, conflicting duplicate relationship metadata and allowed-host enforcement. TRACE now supports validated atomic graph exchange with history preservation and idempotent import. The console previews actual exported report JSON. The original API, target execution and review architecture remain in place.

NRS-Bench adds three seeded evaluation datasets, a known graph, numeric visualization fixtures and bounded stress data. Evaluation produces 18 raw reports, paired comparisons, semantic digests and environment metadata. Backend negative controls include corruption, incomplete histories, invalid project identity and abrupt process termination. Browser checks cover the actual correction workflow, persisted layouts, keyboard filtering, source-preserving SVG export, visible failures, automated accessibility and mobile behavior.

See [validation](validation/README.md) for exact executed results and [security audit](security/audit.md) for scan evidence. [Historical development evidence](verification/historical-engineering-report.md) preserves the earlier 31-test report, whose ETL-import observations are historical and were not rerun against an external private project for this release.

Distribution includes complete source, locked dependencies, packaged Python migrations, versioned data, reports, screenshots, three technical manuscripts and professional contribution/security metadata. CI separates unit/build, clean cross-platform reproduction, vulnerability/secret/static scans and CodeQL. Release publication checks all named workflows at the exact commit before uploading versioned assets and checksums.

Limits include local SQLite-oriented operation, synthetic target evaluation, no independent review identity, no hard-interruption recovery, no human-user study, no independent-party reproduction and incomplete Zenodo access. The wheel supplies the API; the source archive supplies the complete frontend and research package. Research claims are limited to the executed finite fixtures.
