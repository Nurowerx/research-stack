"""Verify a fresh source install without changing the delivered instance."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--destination", required=True)
parser.add_argument("--port", type=int, default=8877)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
destination = Path(args.destination).resolve()
if destination == root or root in destination.parents:
    raise SystemExit("Destination must be outside the source tree.")
if destination.exists():
    raise SystemExit("Destination must not exist; refusing to overwrite an earlier verification.")
destination.mkdir(parents=True)
source = destination / "source"
shutil.copytree(
    root,
    source,
    ignore=shutil.ignore_patterns(
        ".git",
        ".coverage",
        "build",
        "node_modules",
        ".venv",
        "__pycache__",
        "*.egg-info",
        ".pytest_cache",
        ".ruff_cache",
        "dist",
        "test-results",
        "playwright-report",
        "*.sqlite",
        "*.sqlite-*",
    ),
)
env = os.environ.copy()
revision = subprocess.run(
    ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=False
)
if revision.returncode == 0:
    env["NX_SOURCE_COMMIT"] = revision.stdout.strip()
env["TEMP"] = env["TMP"] = str(destination / "temp")
Path(env["TEMP"]).mkdir()
env.setdefault("PIP_CACHE_DIR", str(destination / "pip-cache"))
env.setdefault("npm_config_cache", str(destination / "npm-cache"))
env["NX_BASE_URL"] = f"http://127.0.0.1:{args.port}"
env["NX_TEST_OUTPUT"] = str(destination / "browser-artifacts")
env["NX_TEST_REPORT"] = str(destination / "browser-results.json")
env["NX_SCREENSHOTS"] = str(destination / "screenshots")
env["NX_API_PROXY"] = env["NX_BASE_URL"]
for key in ("NX_DATABASE_URL", "NX_READER_TOKEN", "NX_WRITER_TOKEN", "NX_STATIC_DIR"):
    env.pop(key, None)
npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
python = destination / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
checks = []
start = time.perf_counter()


def run(name, command):
    print(f"CHECK: {name}", flush=True)
    clock = time.perf_counter()
    result = subprocess.run(
        [str(x) for x in command],
        cwd=source,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )
    (destination / f"{name}.log").write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")
    checks.append(
        {
            "name": name,
            "exit_code": result.returncode,
            "seconds": round(time.perf_counter() - clock, 3),
        }
    )
    if result.returncode:
        print(result.stdout[-5000:] + result.stderr[-5000:], flush=True)
        raise RuntimeError(f"{name} failed; inspect its log")
    return result.stdout


def wait_ready(url, process):
    for _ in range(100):
        if process.poll() is not None:
            raise RuntimeError("Service exited before readiness")
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(0.2)
    raise RuntimeError(f"Service did not become ready at {url}")


service = None
frontend = None
handles = []
try:
    run("create-venv", [sys.executable, "-m", "venv", destination / "venv"])
    run(
        "locked-python-install",
        [python, "-m", "pip", "install", "-r", "requirements-lock.txt"],
    )
    run(
        "editable-source-install",
        [python, "-m", "pip", "install", "-e", ".", "--no-deps"],
    )
    run("locked-npm-install", [npm, "ci", "--no-audit", "--no-fund"])
    run(
        "python-tests",
        [python, "-m", "pytest", "-q", "--junitxml=" + str(destination / "pytest.xml")],
    )
    run("chart-data-tests", [npm, "test"])
    run(
        "nrs-bench",
        [python, "scripts/benchmark.py", "--output", str(destination / "nrs-bench")],
    )
    run("production-build", [npm, "run", "build"])
    run("database-migration", [python, "-m", "nx_api.cli", "init"])
    run("fixture-seed", [python, "-m", "nx_api.cli", "seed"])
    run(
        "browser-runtime-install",
        [npm, "exec", "--", "playwright", "install", "chromium"],
    )
    handles = [
        (destination / "backend.log").open("w", encoding="utf-8"),
        (destination / "frontend.log").open("w", encoding="utf-8"),
    ]
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    service = subprocess.Popen(
        [str(python), "-m", "nx_api.cli", "serve", "--port", str(args.port)],
        cwd=source,
        env=env,
        stdout=handles[0],
        stderr=subprocess.STDOUT,
        creationflags=flags,
    )
    wait_ready(env["NX_BASE_URL"] + "/api/health", service)
    checks.append({"name": "production-service-ready", "exit_code": 0})
    run("browser-workflow-accessibility-mobile", [npm, "run", "test:e2e"])
    # Start the development frontend separately; check its real proxied API as well.
    frontend = subprocess.Popen(
        [
            shutil.which("node"),
            str(source / "node_modules/vite/bin/vite.js"),
            "--config",
            "apps/research-console/vite.config.ts",
            "--host",
            "127.0.0.1",
            "--port",
            "5174",
            "--strictPort",
        ],
        cwd=source,
        env=env,
        stdout=handles[1],
        stderr=subprocess.STDOUT,
        creationflags=flags,
    )
    wait_ready("http://127.0.0.1:5174/", frontend)
    with urllib.request.urlopen("http://127.0.0.1:5174/api/projects", timeout=10) as response:
        assert len(json.load(response)) >= 1
    checks.append({"name": "vite-frontend-and-proxy-ready", "exit_code": 0})
    reproduction = run(
        "semantic-reproduction",
        [
            python,
            "-m",
            "nx_api.cli",
            "reproduce",
            "--report",
            "examples/model-evaluation/corrected-affected-report.json",
        ],
    )
    report = {
        "status": "passed",
        "checks": checks,
        "duration_seconds": round(time.perf_counter() - start, 3),
        "platform": sys.platform,
        "python": run("python-version", [python, "--version"]).strip(),
        "node": run("node-version", [shutil.which("node"), "--version"]).strip(),
        "reproduction": json.loads(reproduction),
        "browser": json.loads((destination / "browser-results.json").read_text(encoding="utf-8"))[
            "stats"
        ],
        "scope": "Fresh copied source, new virtual environment, locked installs, new database, production and Vite startup, real browser workflow; public dependency caches may be reused.",
    }
    (destination / "clean-install.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)
finally:
    for process in (frontend, service):
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
    for handle in handles:
        handle.close()
