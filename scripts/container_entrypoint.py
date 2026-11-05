"""Initialize the dedicated container volume, then serve with explicit access token."""

import os
import subprocess
import sys

if not os.environ.get("NX_WRITER_TOKEN"):
    raise SystemExit("Set NX_WRITER_TOKEN to enable the container's network listener.")
for command in ("init", "seed"):
    subprocess.run([sys.executable, "-m", "nx_api.cli", command], check=True)
os.execv(sys.executable, [sys.executable, "-m", "nx_api.cli", "serve", "--host", "0.0.0.0"])
