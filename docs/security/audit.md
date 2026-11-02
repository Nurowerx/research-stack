# Security and redistribution audit

The release was assembled from the original source archive in a separate directory. No existing repository history was imported. Local databases, environments, caches, credentials and machine-specific runtime paths are excluded. Original examples are synthetic. Historical ETL verification counts are explicitly historical; the private external project and its raw data are not bundled.

Python dependency audit (pip-audit 2.10.1) and npm audit completed without known vulnerabilities in the audited locked dependency graphs. Bandit 1.9.4 completed with no findings in application packages/services after an explicit suppression for the seeded noncryptographic fixture generator. Reports are in research/results. These tools do not guarantee the absence of vulnerabilities. Optional figure-rendering dependencies have a separate lock and audit scope.

Gitleaks 8.30.1 scans the complete public Git history before push and in CI. Actionlint 1.7.12 validates workflows; scanner downloads are checked against publisher SHA-256 files. CodeQL covers Python and JavaScript/TypeScript in GitHub Actions. Exact remote workflow outcomes are recorded in the release validation ledger. Dependency Review runs on pull requests; a workflow definition alone is not a completed scan.

All GitHub actions are pinned to full commit IDs. Ordinary jobs have read-only repository access; CodeQL receives security-events write access and only the gated release job receives contents write access. PR jobs do not receive production secrets. Release creation verifies successful CI, Security and Reproducibility workflows for the exact tagged commit.

Public reference repositories were read at pinned commits. No source or dataset from those repositories is redistributed. The ontology starter had no explicit root license located, so it was used only as a conceptual reference. Dependency metadata is inventoried in research/references/dependency-licenses.json; third-party packages and bundled fonts retain their own licenses and are installed through package managers. Repository-owned code is MIT; original benchmark data and research text are CC BY 4.0. This is a technical provenance inventory, not an assertion of legal certification.

The threat model and limits are in SECURITY.md. In particular, hash checks are not signatures, actor labels are not authenticated users, and the service is intended for local/trusted use. No security certification or penetration-test claim is made.
