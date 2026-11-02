# Security policy

The supported public series is 0.1.x. Report vulnerabilities using **Security → Report a vulnerability** in this repository when enabled. Do not post working credentials or private research data in public issues. There is no guaranteed response SLA.

The default service binds to loopback. Set `NX_WRITER_TOKEN` and, for private read access, `NX_READER_TOKEN` before remote deployment. Explicitly set `NX_ALLOWED_HOSTS` to permitted host names. Use HTTPS at a trusted reverse proxy. An actor field is an attribution label, not an authenticated identity. Shared bearer tokens are not a multi-user authorization system.

SQLite triggers protect against application-level rewriting of completed evidence. A database administrator can bypass them. Hashes detect accidental content changes; they are not signatures, authenticated authorship, trusted timestamps or protection against a malicious administrator recomputing hashes. TRACE record content hashes cover kind, label and payload; edge hashes cover relationship input fields. Export/import validates identity and version structure but does not prove the truth of evidence.

Large imports and synchronous evaluations can consume CPU, memory and disk. Keep this release local or behind a trusted access boundary. Hard interruption leaves a running row; preserve it as evidence and start a new run. Do not present that row as complete. See [audit evidence](docs/security/audit.md) for executed scans and limitations.
