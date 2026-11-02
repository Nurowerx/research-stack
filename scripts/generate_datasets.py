"""Generate original CC BY 4.0 fixtures, with byte hashes and explicit ground truth."""

import hashlib
import json
from pathlib import Path

from nx_loop import generate
from nx_schema import Benchmark

ROOT = Path(__file__).resolve().parents[1]


def datasets():
    values = [0.2, 0.4, None, 0.6, 0.8]
    yield (
        "visualization",
        {
            "values": values,
            "expected": {"n": 4, "missing": 1, "mean": 0.5},
            "interval": {
                "id": "estimate",
                "label": "Known-variance normal example",
                "value": 0.5,
                "low": 0.3040036015459946,
                "high": 0.6959963984540054,
                "sourceId": "normal-fixture",
                "n": 100,
            },
            "interval_design": {
                "sample_mean": 0.5,
                "known_sigma": 1,
                "n": 100,
                "confidence": 0.95,
                "method": "two-sided normal interval with known variance; illustrative sufficient statistics, not NRS accuracy uncertainty",
            },
            "time_series": [
                {
                    "id": str(i),
                    "x": i * 1000,
                    "y": y,
                    "label": str(i),
                    "sourceId": str(i),
                }
                for i, y in enumerate([-2, 0, None, 4, 100])
            ],
            "histogram": [-10, 0, 0, 1, 2, 100],
            "expected_histogram_total": 6,
            "stress_values": [i % 101 for i in range(10000)],
        },
        None,
        "Known means, missing values, a normal interval, gaps, outliers and 10,000 render inputs.",
    )
    yield (
        "provenance",
        {
            "nodes": [
                {"id": n, "kind": k}
                for n, k in [
                    ("source", "data_source"),
                    ("dataset", "dataset_version"),
                    ("algorithm", "algorithm"),
                    ("execution", "execution"),
                    ("output", "output"),
                    ("evidence", "evidence"),
                    ("claim", "claim"),
                ]
            ],
            "edges": [
                ["dataset", "source", "derived_from"],
                ["execution", "dataset", "evaluated_against"],
                ["execution", "algorithm", "depends_on"],
                ["output", "execution", "generated_by"],
                ["evidence", "output", "derived_from"],
                ["claim", "evidence", "supported_by"],
            ],
            "expected_reachable_from_claim": [
                "algorithm",
                "claim",
                "dataset",
                "evidence",
                "execution",
                "output",
                "source",
            ],
            "broken_edge": ["claim", "absent", "supported_by"],
            "cycle_control": [["output", "evidence", "derived_from"]],
            "conflict_control": ["claim", "evidence", "contradicted_by"],
        },
        None,
        "Symbolic seven-entity provenance graph and explicitly invalid controls.",
    )
    for seed in (13, 42, 20261102):
        yield (
            f"evaluation-{seed}",
            generate(seed=seed, per_family=20).model_dump(mode="json"),
            seed,
            "120 synthetic cases, six designed families, 60 development and 60 heldout instances.",
        )


def main():
    folder = ROOT / "datasets/synthetic/v1"
    folder.mkdir(parents=True, exist_ok=True)
    entries = []
    for name, data, seed, description in datasets():
        raw = (json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()
        path = folder / f"{name}.json"
        path.write_bytes(raw)
        entries.append(
            {
                "dataset_id": f"nrs-bench/{name}",
                "version": "1.0.0",
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "description": description,
                "origin": "synthetic: generated originally for Nurowerx; no external dataset copied",
                "generator": "scripts/generate_datasets.py",
                "seed": seed,
                "license": "CC-BY-4.0",
                "schema": "datasets/schema.json"
                if name.startswith("evaluation")
                else "datasets/README.md",
                "ground_truth": "explicit expected fields and independent formulas; policy answers constructed by family rules",
                "protocol": "python scripts/benchmark.py; npm test; python -m pytest; browser suite via scripts/clean_install.py",
                "limitations": "Designed finite synthetic tasks; seeds vary identifiers, not real-world task coverage.",
            }
        )
    (ROOT / "datasets/schema.json").write_text(
        json.dumps(Benchmark.model_json_schema(), indent=2) + "\n", encoding="utf-8"
    )
    (ROOT / "datasets/manifest.json").write_text(
        json.dumps({"version": "1.0.0", "datasets": entries}, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
