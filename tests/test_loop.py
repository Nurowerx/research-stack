import copy

import pytest
from nx_loop import generate
from nx_loop.metrics import aggregate, score
from nx_schema import Benchmark, CorrectionInput, Prediction, ReviewInput, RunInput
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError


def test_real_execution_reproducible_and_ground_truth_isolation(loop, benchmark, trace):
    first = loop.execute(RunInput(benchmark_id=benchmark))
    second = loop.execute(RunInput(benchmark_id=benchmark))
    assert first["semantic_digest"] == second["semantic_digest"]
    assert first["summary"]["unique_cases"] == 12 and first["summary"]["executions"] == 24
    assert first["summary"]["metrics"]["accuracy"]["value"] == pytest.approx(1 / 6)
    assert first["summary"]["metrics"]["accuracy"]["denominator"] == 12
    assert first["summary"]["metrics"]["latency_ms"]["value"] > 0
    aware = loop.execute(RunInput(benchmark_id=benchmark, target="evidence-aware"))
    assert aware["summary"]["metrics"]["accuracy"]["value"] == 1
    comparison = loop.compare(first["id"], aware["id"])
    assert comparison["improved"] == 10 and comparison["interval"] is None
    assert loop.compare(aware["id"], first["id"])["regression_detected"]
    state = trace.claim_state(first["results"][0]["claim_id"])
    assert state["status"] == "contradicted" and not state["incomplete_provenance"]
    with pytest.raises(IntegrityError), trace.engine.begin() as db:
        db.execute(
            text("UPDATE loop_runs SET status='running' WHERE id=:id"),
            {"id": first["id"]},
        )


def test_correction_review_disagreement_and_affected_rerun(loop, benchmark, trace):
    run = loop.execute(RunInput(benchmark_id=benchmark))
    cid = loop.propose(
        CorrectionInput(
            run_id=run["id"],
            case_id="revision-000",
            rule="prefer_latest",
            rationale="Prefer the newer source revision.",
            actor="Author",
        )
    )["id"]
    request = RunInput(
        benchmark_id=benchmark,
        case_ids=["revision-000"],
        correction_ids=[cid],
        parent_run_id=run["id"],
    )
    with pytest.raises(ValueError, match="undisputed"):
        loop.execute(request)
    assert (
        loop.review(
            cid,
            ReviewInput(
                decision="accept",
                rationale="Source revision resolves this case.",
                actor="Reviewer A",
            ),
        )["review_status"]
        == "accepted"
    )
    assert (
        loop.review(
            cid,
            ReviewInput(
                decision="reject",
                rationale="Need broader regression checks.",
                actor="Reviewer B",
            ),
        )["review_status"]
        == "disputed"
    )
    with pytest.raises(ValueError, match="undisputed"):
        loop.execute(request)
    resolved = loop.review(
        cid,
        ReviewInput(
            decision="accept",
            rationale="Accept for affected-case testing.",
            actor="Reviewer B",
        ),
    )
    assert resolved["review_status"] == "accepted" and len(resolved["reviews"]) == 3
    corrected = loop.execute(request)
    comparison = loop.compare(run["id"], corrected["id"])
    assert (
        comparison["paired_cases"] == 1
        and comparison["partial_overlap"]
        and comparison["improved"] == 1
    )
    assert loop.run_detail(run["id"])["semantic_digest"] == run["semantic_digest"]
    assert trace.verify(run["project_id"])["ok"]


def test_heldout_cannot_drive_correction(loop, benchmark):
    run = loop.execute(RunInput(benchmark_id=benchmark, split="heldout"))
    with pytest.raises(ValueError, match="development"):
        loop.propose(
            CorrectionInput(
                run_id=run["id"],
                case_id="revision-002",
                rule="prefer_latest",
                rationale="Inspect heldout",
                actor="Author",
            )
        )


def test_denominators_and_no_pseudoreplication():
    case = next(c for c in generate(per_family=4).cases if c.family == "missing")
    prediction = Prediction(answer=None)
    row = {
        "case_id": case.id,
        "family": case.family,
        "prediction": prediction.model_dump(),
        "scores": score(case, prediction),
        "latency_ms": 1.5,
    }
    result = aggregate([row, row])
    assert result["metrics"]["accuracy"]["denominator"] == 1
    assert result["metrics"]["unsupported_assertion_rate"]["value"] is None
    assert result["metrics"]["retrieval_precision"]["value"] is None
    assert result["metrics"]["appropriate_abstention"]["value"] == 1
    assert result["metrics"]["output_consistency"]["denominator"] == 1
    assert result["uncertainty"]["interval"] is None


def test_unknown_citation_cannot_pass_evidence_consistency():
    case = generate(per_family=4).cases[0]
    result = score(case, Prediction(answer=case.expected_answer, evidence_ids=["invented"]))
    assert result["correct"] and result["pairs"]["evidence_consistency"] == [0, 1]
    assert result["pairs"]["retrieval_precision"] == [0, 1]


def test_invalid_benchmark_identities_and_empty_dataset():
    data = generate(per_family=4).model_dump()
    with pytest.raises(ValueError):
        Benchmark.model_validate({**data, "cases": []})
    data["cases"][1] = copy.deepcopy(data["cases"][0])
    with pytest.raises(ValueError, match="Duplicate"):
        Benchmark.model_validate(data)


def test_target_failure_is_recorded_without_partial_results(loop, benchmark):
    class Broken:
        name = "broken"
        version = "1.0"

        def predict(self, query, parameters):
            assert not hasattr(query, "expected_answer")
            raise RuntimeError("Intentional target failure")

    loop.registry.register(Broken())
    with pytest.raises(RuntimeError, match="Intentional"):
        loop.execute(RunInput(benchmark_id=benchmark, target="broken"))
    _, data = loop.benchmark(benchmark)
    run = loop.runs(loop.trace.get(benchmark)["project_id"])[0]
    assert run["status"] == "failed" and loop.run_detail(run["id"])["results"] == []


def test_no_cross_split_comparison(loop, benchmark):
    before = loop.execute(RunInput(benchmark_id=benchmark))
    after = loop.execute(RunInput(benchmark_id=benchmark, split="heldout"))
    with pytest.raises(ValueError, match="same benchmark version and split"):
        loop.compare(before["id"], after["id"])


def test_dataset_revisions_preserve_old_cases(loop, project, trace):
    original = loop.register_benchmark(project, generate(seed=10, per_family=4))
    revision = loop.register_benchmark(project, generate(seed=11, per_family=4))
    assert original["logical_id"] == revision["logical_id"] and revision["version"] == 2
    assert trace.get(original["id"])["payload"]["benchmark"]["seed"] == 10
    assert len(trace.get(revision["id"])["history"]) == 2
    assert loop.register_benchmark(project, generate(seed=11, per_family=4))["id"] == revision["id"]


def test_policy_parameters_are_strict(loop, benchmark):
    with pytest.raises(ValueError, match="booleans"):
        loop.execute(RunInput(benchmark_id=benchmark, parameters={"prefer_latest": "true"}))
    with pytest.raises(ValueError, match="Unknown"):
        loop.execute(RunInput(benchmark_id=benchmark, parameters={"unknown": True}))
