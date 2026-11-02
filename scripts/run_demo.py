"""Execute the documented research workflow. All measurements are actual calls."""

import argparse
import json
from pathlib import Path

from nx_adapters.exports import residency_fixture
from nx_loop import LoopEngine, generate
from nx_schema import (
    CorrectionInput,
    EdgeInput,
    EntityInput,
    Kind,
    ReviewInput,
    RunInput,
)
from nx_trace import TraceStore

parser = argparse.ArgumentParser()
parser.add_argument("--database", default="sqlite:///research-stack.sqlite")
parser.add_argument("--output", default="examples/model-evaluation")
args = parser.parse_args()
output = Path(args.output)
output.mkdir(parents=True, exist_ok=True)
trace = TraceStore(args.database, initialize=True)
loop = LoopEngine(trace)
project = next(
    (p for p in trace.records(kind=Kind.PROJECT) if p["label"] == "Evidence under revision"),
    None,
) or trace.project("Evidence under revision")
pid = project["id"]
benchmark = loop.register_benchmark(pid, generate())
experiment = trace.create(
    pid,
    EntityInput(
        kind="experiment",
        label="Evidence selection / revision rules",
        payload={
            "question": "Which deterministic evidence rules resolve the fixed fixture failures?",
            "synthetic": True,
            "inference_scope": "Descriptive fixture comparison",
        },
    ),
)
before = loop.execute(RunInput(benchmark_id=benchmark["id"]))
aware = loop.execute(RunInput(benchmark_id=benchmark["id"], target="evidence-aware"))
heldout = loop.execute(
    RunInput(benchmark_id=benchmark["id"], target="evidence-aware", split="heldout")
)
correction = loop.propose(
    CorrectionInput(
        run_id=before["id"],
        case_id="revision-000",
        rule="prefer_latest",
        rationale="Select the highest available revision for the requested key; test this proposed change without changing the oracle.",
        actor="Demonstration author",
    )
)
loop.review(
    correction["id"],
    ReviewInput(
        decision="accept",
        rationale="Accepted for the synthetic demonstration after inspecting the versioned source items.",
        actor="Demonstration reviewer",
    ),
)
after = loop.execute(
    RunInput(
        benchmark_id=benchmark["id"],
        case_ids=["revision-000"],
        correction_ids=[correction["id"]],
        parent_run_id=before["id"],
    )
)
full = loop.execute(
    RunInput(
        benchmark_id=benchmark["id"],
        correction_ids=[correction["id"]],
        parent_run_id=before["id"],
    )
)
for name, run in [
    ("baseline", before),
    ("evidence-aware", aware),
    ("heldout", heldout),
    ("corrected-affected", after),
    ("corrected-full", full),
]:
    trace.edge(
        EdgeInput(
            source_id=run["execution_id"],
            target_id=experiment["id"],
            relation="belongs_to_experiment",
        )
    )
    (output / f"{name}-report.json").write_text(
        json.dumps(loop.report(run["id"]), indent=2), encoding="utf-8"
    )
comparison = loop.compare(before["id"], after["id"])
full_comparison = loop.compare(before["id"], full["id"])
summary = {
    "project_id": pid,
    "benchmark_id": benchmark["id"],
    "experiment_id": experiment["id"],
    "baseline_run": before["id"],
    "aware_run": aware["id"],
    "heldout_run": heldout["id"],
    "correction_id": correction["id"],
    "corrected_affected_run": after["id"],
    "corrected_full_run": full["id"],
    "baseline_accuracy": before["summary"]["metrics"]["accuracy"],
    "aware_accuracy": aware["summary"]["metrics"]["accuracy"],
    "affected_comparison": comparison,
    "full_comparison": full_comparison,
    "integrity": trace.verify(pid),
    "disclosure": "Actual executions of deterministic synthetic policies. Demonstration author/reviewer are scripted attribution labels; no human-participant study.",
}
(output / "workflow-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
root = Path(__file__).resolve().parents[1]
(root / "datasets/synthetic").mkdir(parents=True, exist_ok=True)
(root / "datasets/synthetic/evidence-revision.json").write_text(
    json.dumps(generate().model_dump(), indent=2), encoding="utf-8"
)
(root / "datasets/synthetic/residency-contract-fixture.json").write_text(
    json.dumps(residency_fixture().model_dump(), indent=2), encoding="utf-8"
)
print(json.dumps({k: v for k, v in summary.items() if not isinstance(v, dict)}, indent=2))
trace.engine.dispose()
