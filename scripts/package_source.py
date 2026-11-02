"""Archive committed source only; exclude all untracked local files by construction."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--output", default="../nurowerx-research-stack.zip")
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
output = Path(args.output).resolve()
subprocess.run(
    ["git", "archive", "--format=zip", "--prefix=research-stack/", f"--output={output}", "HEAD"],
    cwd=root,
    check=True,
)
print(
    json.dumps(
        {
            "archive": str(output),
            "scope": "committed HEAD only",
            "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        }
    )
)
