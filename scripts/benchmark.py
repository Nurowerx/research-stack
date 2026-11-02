"""Execute controlled NRS-Bench experiments; exit nonzero on any failed oracle."""

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import tempfile
import time
from pathlib import Path

import psutil
from nx_loop import LoopEngine
from nx_schema import (
    Benchmark,
    CorrectionInput,
    EdgeInput,
    EntityInput,
    ReviewInput,
    RunInput,
)
from nx_trace import TraceStore
from nx_trace.exchange import export_bundle, import_bundle
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def execute(output):
    manifest = json.loads((ROOT / "datasets/manifest.json").read_text())
    for dataset in manifest["datasets"]:
        assert (
            hashlib.sha256((ROOT / dataset["path"]).read_bytes()).hexdigest() == dataset["sha256"]
        )
    git = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    start = time.perf_counter()
    rows = []
    with tempfile.TemporaryDirectory(prefix="nrs-bench-") as folder:
        trace = TraceStore("sqlite:///" + str(Path(folder) / "bench.sqlite"), initialize=True)
        try:
            loop = LoopEngine(trace)
            for seed in (13, 42, 20261102):
                pid = trace.project(f"NRS-Bench seed {seed}")["id"]
                data = Benchmark.model_validate_json(
                    (ROOT / f"datasets/synthetic/v1/evaluation-{seed}.json").read_text()
                )
                bid = loop.register_benchmark(pid, data)["id"]
                before = loop.execute(RunInput(benchmark_id=bid))
                repeat = loop.execute(RunInput(benchmark_id=bid))
                aware = loop.execute(RunInput(benchmark_id=bid, target="evidence-aware"))
                heldout = loop.execute(
                    RunInput(benchmark_id=bid, target="evidence-aware", split="heldout")
                )
                assert before["semantic_digest"] == repeat["semantic_digest"]
                assert before["summary"]["metrics"]["accuracy"]["numerator"] == 10
                assert aware["summary"]["metrics"]["accuracy"]["value"] == 1
                assert heldout["summary"]["metrics"]["accuracy"]["value"] == 1
                cid = loop.propose(
                    CorrectionInput(
                        run_id=before["id"],
                        case_id="revision-000",
                        rule="prefer_latest",
                        rationale="Synthetic protocol: prefer newer revision",
                        actor="Benchmark script",
                    )
                )["id"]
                loop.review(
                    cid,
                    ReviewInput(
                        decision="accept",
                        rationale="Scripted fixture review, not a participant judgment",
                        actor="Benchmark script",
                    ),
                )
                affected = loop.execute(
                    RunInput(
                        benchmark_id=bid,
                        case_ids=["revision-000"],
                        correction_ids=[cid],
                        parent_run_id=before["id"],
                    )
                )
                full = loop.execute(
                    RunInput(
                        benchmark_id=bid,
                        correction_ids=[cid],
                        parent_run_id=before["id"],
                    )
                )
                comparison = loop.compare(before["id"], full["id"])
                regression = loop.compare(aware["id"], before["id"])
                assert affected["summary"]["metrics"]["accuracy"]["value"] == 1
                assert full["summary"]["metrics"]["accuracy"]["value"] == 0.5
                assert comparison["improved"] == 20 and regression["regression_detected"]
                assert trace.verify(pid)["ok"]
                runs = {
                    "first_match": before,
                    "repeat": repeat,
                    "evidence_aware": aware,
                    "heldout": heldout,
                    "corrected_affected": affected,
                    "corrected_full": full,
                }
                rows.append(
                    {
                        "seed": seed,
                        "runs": {
                            name: {
                                "id": run["id"],
                                "semantic_digest": run["semantic_digest"],
                                "summary": run["summary"],
                            }
                            for name, run in runs.items()
                        },
                        "paired_full": comparison,
                        "negative_regression_control": regression,
                    }
                )
                for name, run in runs.items():
                    write(
                        output / "reports" / f"{seed}-{name}.json",
                        loop.report(run["id"]),
                    )
            graph_data = json.loads((ROOT / "datasets/synthetic/v1/provenance.json").read_text())
            pid = trace.project("Known-answer graph")["id"]
            nodes = {}
            for node in graph_data["nodes"]:
                payload = {
                    "origin": "NRS synthetic graph",
                    "content_hash": "0" * 64,
                    "statement": "Synthetic claim",
                }
                nodes[node["id"]] = trace.create(
                    pid,
                    EntityInput(kind=node["kind"], label=node["id"], payload=payload),
                )["id"]
            for source, target, relation in graph_data["edges"]:
                trace.edge(
                    EdgeInput(
                        source_id=nodes[source],
                        target_id=nodes[target],
                        relation=relation,
                        assessment="fixture_oracle",
                    )
                )
            reachable = trace.graph(pid, nodes["claim"], depth=10, limit=100)
            assert (
                sorted(n["label"] for n in reachable["nodes"])
                == graph_data["expected_reachable_from_claim"]
            )
            bundle = export_bundle(trace, pid)
            clone = TraceStore("sqlite:///" + str(Path(folder) / "clone.sqlite"), initialize=True)
            try:
                import_bundle(clone, bundle)
                assert export_bundle(clone, pid) == bundle
            finally:
                clone.engine.dispose()
            write(output / "provenance-bundle.json", bundle)
            stress_pid = trace.project("Bounded stress graph")["id"]
            clock = time.perf_counter()
            for i in range(500):
                trace.create(
                    stress_pid,
                    EntityInput(kind="observation", label=f"stress-{i}", payload={"i": i}),
                )
            assert len(trace.records(stress_pid, limit=1000)) == 501
            assert trace.verify(stress_pid)["ok"]
            stress = {
                "records": 501,
                "wall_seconds": time.perf_counter() - clock,
                "process_rss_bytes": psutil.Process().memory_info().rss,
                "scope": "one local run; RSS snapshot includes interpreter and all experiments; no performance SLA",
            }
        finally:
            trace.engine.dispose()
    visual = json.loads((ROOT / "datasets/synthetic/v1/visualization.json").read_text())
    ci = visual["interval"]
    half = norm.ppf(0.975) / (100**0.5)
    assert abs(ci["low"] - (0.5 - half)) < 1e-12
    assert abs(ci["high"] - (0.5 + half)) < 1e-12
    result = {
        "suite": "NRS-Bench",
        "version": "1.0.0",
        "status": "passed",
        "code_commit": os.environ.get("NX_SOURCE_COMMIT")
        or (git.stdout.strip() if git.returncode == 0 else None),
        "environment": {
            "os": platform.platform(),
            "python": platform.python_version(),
            "processor": platform.processor(),
            "logical_cpus": psutil.cpu_count(),
            "dependencies": {
                name: importlib.metadata.version(name)
                for name in ("numpy", "scipy", "SQLAlchemy", "pydantic", "psutil")
            },
        },
        "command": "python scripts/benchmark.py --output <result-directory>",
        "duration_seconds": time.perf_counter() - start,
        "experiments": rows,
        "graph": {"nodes": 7, "edges": 6, "reachable": 7, "roundtrip_exact": True},
        "stress": stress,
        "visualization_oracle": {
            "method": "SciPy normal quantile, independent of the chart implementation",
            "absolute_tolerance": 1e-12,
            "passed": True,
        },
        "interpretation": "Finite synthetic census; seeds are controlled variations, not independent real-world datasets. No accuracy confidence intervals or significance tests. Automated UI and adversarial controls are recorded separately in test-suite reports. No independent-party reproduction.",
    }
    write(output / "summary.json", result)
    print(
        json.dumps(
            {
                "status": result["status"],
                "seeds": len(rows),
                "runs": 18,
                "seconds": result["duration_seconds"],
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "results/nrs-bench")
    execute(parser.parse_args().output.resolve())
