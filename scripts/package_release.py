"""Package source, datasets and research separately with SHA-256 checksums."""

import hashlib
import subprocess
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
output = root / "dist"
output.mkdir(exist_ok=True)
subprocess.run(
    ["git", "archive", "--format=zip", f"--output={output / 'nrs-source-v0.1.0.zip'}", "HEAD"],
    cwd=root,
    check=True,
)
for label, folder in (("datasets", "datasets"), ("research", "research")):
    with zipfile.ZipFile(output / f"nrs-{label}-v0.1.0.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted((root / folder).rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(root))
checksums = []
for path in sorted(output.iterdir()):
    if path.is_file() and path.name != "SHA256SUMS.txt":
        checksums.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}")
(output / "SHA256SUMS.txt").write_text("\n".join(checksums) + "\n", encoding="utf-8")
