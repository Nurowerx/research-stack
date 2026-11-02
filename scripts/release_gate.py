"""Fail closed unless named validation workflows passed at this exact commit."""

import json
import os
import subprocess

repository = os.environ["GITHUB_REPOSITORY"]
sha = os.environ["GITHUB_SHA"]
response = subprocess.run(
    ["gh", "api", f"repos/{repository}/actions/runs?head_sha={sha}&per_page=100"],
    capture_output=True,
    text=True,
    check=True,
)
runs = json.loads(response.stdout)["workflow_runs"]
for name in ("CI", "Security", "Reproducibility"):
    candidates = [run for run in runs if run["name"] == name and run["event"] == "push"]
    if not candidates:
        raise SystemExit(f"No {name} evidence for {sha}")
    latest = max(candidates, key=lambda run: run["id"])
    if latest["conclusion"] != "success":
        raise SystemExit(f"{name} has not passed: {latest['html_url']}")
    print(f"Verified {name}: {latest['html_url']}")
