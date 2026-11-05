# Executed validation evidence

The original 31-test baseline was rerun in a fresh Windows installation before release changes: 23 backend, 3 chart and 5 browser tests passed. It is retained separately in [historical-baseline](../../research/results/historical-baseline/). The original source archive SHA-256 is recorded in the engineering report.

The expanded fresh-install run passed **54 tests**: 35 backend, 12 chart and 7 browser tests, with zero skipped/flaky browser tests. See [release-clean-install](../../research/results/release-clean-install/) for command logs, JUnit, browser JSON and clean-install.json. It also ran NRS-Bench, the production build/service, Vite proxy and semantic reproduction. Its Windows execution used Python 3.11.9 and Node 24.20.0. This run predates the public Git history; subsequent source-commit observations are recorded in [nrs-bench](../../research/results/nrs-bench/).

The benchmark summary records its exact tested code commit, platform, CPU description, dependency versions, command, duration, RSS snapshots and run digests. Eighteen raw JSON reports retain inputs, outputs and source relationships. UUIDs, timestamps and resource measurements are observations, not deterministic expected outputs.

The initial frontend regression run failed four new cases while the three original chart tests passed. Before/after evidence is preserved in research/results/lens-before-fixes.json and lens-after-fixes.json; the complete expanded suite is lens-expanded.json. These failures document discovered defects, not omitted tests. Python coverage is in coverage-summary.json; it is line coverage of the named backend packages, not a scientific validity metric.

Seven actual screenshots in docs/screenshots cover the workspace/LENS view, TRACE graph, LOOP evaluation, correction review, corrected workflow, report preview and mobile interface. Browser logs record automated accessibility checks of five workspace views and one mobile dataset view; zero reported violations does not establish universal accessibility or human usability.

Local path prefixes in published raw logs were replaced with <release-workspace> and <user-home>; numeric results, assertions and error messages are otherwise retained. Original unsanitized development logs remain outside the public repository. CI artifacts provide additional fresh-machine evidence and retain their runner paths.

CI results and the fresh remote-clone verification are recorded in public-release.json after execution. No independent-party reproduction is claimed.

## Public candidate verification

The public candidate `475b6cb1d141c65c33c86ada43f14f2af13ae88e` passed CI, Security (dependency scans, Bandit, Gitleaks, actionlint and both CodeQL languages), and full clean reproduction on Linux, Windows and macOS. Exact job URLs are in public-release.json. A fresh HTTPS clone from GitHub also passed the complete 54-test workflow locally and reproduced the reference digest; logs are in research/results/public-clone. This is developer-controlled reproduction, not an independent-party claim.

The optional Linux container passed build/startup/authenticated-read checks. The static demonstration passed source-score, seed-selection and mobile-overflow checks. These are separately scoped checks rather than additions to the 54-test suite. The release gate requires a new successful CI/Security/Reproducibility run after the final packaging/documentation changes.
