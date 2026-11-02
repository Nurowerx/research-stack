"""Render publication figures directly from executed NRS-Bench observations."""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument(
    "--results", type=Path, default=root / "research/results/nrs-bench/summary.json"
)
args = parser.parse_args()
data = json.loads(args.results.read_text())
plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "svg.hashsalt": "nrs-bench-1.0",
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)
fig, ax = plt.subplots(figsize=(8.5, 4.2), layout="constrained", facecolor="#f5f2eb")
ax.set_facecolor("#f5f2eb")
labels = ["First-match", "Reviewed prefer-latest", "Evidence-aware"]
keys = ["first_match", "corrected_full", "evidence_aware"]
for index, exp in enumerate(data["experiments"]):
    values = [exp["runs"][key]["summary"]["metrics"]["accuracy"]["value"] for key in keys]
    ax.bar(
        np.arange(3) + (index - 1) * 0.23,
        values,
        width=0.21,
        label=f"Seed {exp['seed']}",
        color=["#333c40", "#bc8b6f", "#829d90"][index],
    )
ax.set_xticks(range(3), labels)
ax.set_ylim(0, 1.13)
ax.set_yticks([0, 0.25, 0.5, 0.75, 1], ["0%", "25%", "50%", "75%", "100%"])
ax.set_ylabel("Correct unique cases / 60 development cases")
ax.set_title("Controlled synthetic evaluation · NRS-Bench 1.0.0", loc="left", fontsize=13)
ax.legend(loc="upper left", frameon=False)
ax.text(
    0.01,
    -0.2,
    "Finite fixture census; no inferential error bars. Affected-case 1/1 is excluded.",
    transform=ax.transAxes,
    fontsize=9,
)
folder = root / "research/figures"
folder.mkdir(parents=True, exist_ok=True)
fig.savefig(folder / "accuracy.svg", metadata={"Date": None})
fig.savefig(folder / "accuracy.png", dpi=180)
plt.close(fig)
