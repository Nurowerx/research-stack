# Installation

Use a fresh clone of https://github.com/Nurowerx/research-stack and the commands in the root README. Python 3.11 and Node.js 24 are the release validation targets. Dependencies are pinned in requirements-lock.txt and package-lock.json. Virtual environments and npm installations may require several gigabytes of free disk space; caches may be reused but are not part of the scientific evidence.

Activate a virtual environment with `.venv\Scripts\Activate.ps1` in Windows PowerShell or `source .venv/bin/activate` in Linux/macOS. If activation is unavailable, invoke the environment's Python and nx-stack executables directly. No global security policy change is needed.

`nx-stack --database sqlite:///new.sqlite init` creates/migrates a database. Pass the same database argument before `seed`, `run`, `report` and `serve`. `nx-stack seed` loads the 120-case synthetic demonstration. `nx-stack run --benchmark <record-id> --target evidence-aware --report report.json` executes a target; `nx-stack report --run <run-id> --output report.json` exports an existing run. The console lists dataset and run IDs. `nx-stack reproduce --report report.json` uses a new temporary database and returns nonzero on a semantic mismatch.

For development, run `nx-stack serve` in one terminal and `npm run dev` in another. The production server serves the frontend built by `npm run build`. Set NX_API_PROXY when changing the backend port for Vite. Keep the service bound to loopback unless deliberately configuring authenticated remote access; see SECURITY.md.

The wheel contains the Python API and packaged migrations; the source release is the recommended full application distribution because it also includes the frontend, fixtures, tests and manuscripts. Build the frontend from source. The wheel alone does not bundle a compiled browser console.

Clean reproduction: `python scripts/clean_install.py --destination ../nrs-reproduction`. The new destination must be outside the source checkout. Linux browser dependencies can be installed with `npm ci` followed by `npx playwright install-deps chromium`. The script installs Chromium itself. Avoid running on ports already serving another project; use `--port 8877` or another free port. The Vite check also uses port 5174.
