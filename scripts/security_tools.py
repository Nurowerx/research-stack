"""Download pinned scanners, verify publisher checksums, execute selected binaries."""

import hashlib
import io
import os
import platform
import subprocess
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_tool(name, repo, version, args):
    system = (
        "windows" if os.name == "nt" else "darwin" if platform.system() == "Darwin" else "linux"
    )
    arch = (
        "arm64"
        if platform.machine().lower() in ("arm64", "aarch64")
        else "x64"
        if name == "gitleaks"
        else "amd64"
    )
    extension = "zip" if system == "windows" else "tar.gz"
    filename = f"{name}_{version}_{system}_{arch}.{extension}"
    base = f"https://github.com/{repo}/releases/download/v{version}"
    with urllib.request.urlopen(f"{base}/{name}_{version}_checksums.txt", timeout=60) as response:
        checksums = response.read().decode()
    expected = next(
        line.split()[0] for line in checksums.splitlines() if line.split()[-1] == filename
    )
    with urllib.request.urlopen(f"{base}/{filename}", timeout=60) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != expected:
        raise RuntimeError("Scanner checksum mismatch")
    with tempfile.TemporaryDirectory(prefix="nrs-scanner-") as folder:
        binary_name = name + (".exe" if os.name == "nt" else "")
        if extension == "zip":
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                binary = archive.read(binary_name)
        else:
            with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
                member = archive.extractfile(binary_name)
                if member is None:
                    raise RuntimeError("Scanner executable absent")
                binary = member.read()
        path = Path(folder) / binary_name
        path.write_bytes(binary)
        path.chmod(0o700)
        subprocess.run([str(path), *args], cwd=ROOT, check=True)


if __name__ == "__main__":
    run_tool(
        "gitleaks",
        "gitleaks/gitleaks",
        "8.30.1",
        [
            "git",
            "--redact",
            "--no-banner",
            "--report-format",
            "json",
            "--report-path",
            "gitleaks.json",
        ],
    )
    run_tool("actionlint", "rhysd/actionlint", "1.7.12", ["-color"])
