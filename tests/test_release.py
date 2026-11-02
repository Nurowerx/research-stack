"""Release regressions and adversarial TRACE exchange controls."""

import copy
import os
import subprocess
import sys
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from nx_adapters.exports import import_etl
from nx_api.app import create_app
from nx_schema import EdgeInput, EntityInput, digest
from nx_trace import TraceStore
from nx_trace.exchange import export_bundle, import_bundle
from test_adapters import sample


def graph(trace, project):
    a = trace.create(project, EntityInput(kind="observation", label="A"))
    b = trace.create(project, EntityInput(kind="observation", label="B"))
    trace.edge(EdgeInput(source_id=b["id"], target_id=a["id"], relation="derived_from"))
    return export_bundle(trace, project)


def test_exchange_roundtrip_and_idempotence(trace, project, tmp_path):
    data = graph(trace, project)
    target = TraceStore("sqlite:///" + str(tmp_path / "target.sqlite"), initialize=True)
    try:
        assert import_bundle(target, data)["records_added"] == 3
        assert export_bundle(target, project) == data
        assert import_bundle(target, data)["records_added"] == 0
        assert target.verify(project)["ok"]
    finally:
        target.engine.dispose()


@pytest.mark.parametrize(
    "fault", ["content", "missing", "duplicate", "cycle", "history", "metadata"]
)
def test_exchange_rejects_corruption_atomically(trace, project, tmp_path, fault):
    data = copy.deepcopy(graph(trace, project))
    edge = data["edges"][0]
    if fault == "content":
        data["records"][0]["label"] = "Tampered"
    elif fault == "missing":
        data["records"] = [r for r in data["records"] if r["id"] != edge["source_id"]]
    elif fault == "duplicate":
        data["records"].append(data["records"][0])
    elif fault == "history":
        data["records"][0]["version"] = 7
    elif fault == "metadata":
        edge["rationale"] = "Changed but hash not updated"
    else:
        reverse = dict(
            edge,
            id=str(uuid4()),
            source_id=edge["target_id"],
            target_id=edge["source_id"],
        )
        reverse["content_hash"] = digest({k: reverse[k] for k in EdgeInput.model_fields})
        data["edges"].append(reverse)
    target = TraceStore("sqlite:///" + str(tmp_path / "target.sqlite"), initialize=True)
    try:
        with pytest.raises(ValueError):
            import_bundle(target, data)
        assert target.records() == []
    finally:
        target.engine.dispose()


def test_duplicate_relationship_does_not_discard_new_judgment(trace, project):
    data = graph(trace, project)
    edge = data["edges"][0]
    body = EdgeInput.model_validate({k: edge[k] for k in EdgeInput.model_fields})
    assert trace.edge(body)["id"] == edge["id"]
    with pytest.raises(ValueError, match="different"):
        trace.edge(body.model_copy(update={"rationale": "A new interpretation"}))


def test_etl_reimport_preserves_counts_and_source(trace, project):
    first = import_etl(trace, project, sample(), origin="Original synthetic fixture")
    before = export_bundle(trace, project)
    second = import_etl(trace, project, sample(), origin="Repeated transport")
    assert first["dataset_version_id"] == second["dataset_version_id"]
    assert second["already_imported"]
    assert before == export_bundle(trace, project)


def test_nonproject_registration_rejected(loop, trace, project):
    from nx_loop import generate

    row = trace.create(project, EntityInput(kind="observation", label="Not a project"))
    with pytest.raises(ValueError, match="project"):
        loop.register_benchmark(row["id"], generate(per_family=4))


def test_host_header_and_bundle_api(trace, project):
    with TestClient(create_app(trace), base_url="http://127.0.0.1") as client:
        assert client.get("/api/projects", headers={"Host": "untrusted.example"}).status_code == 400
        body = client.get(f"/api/projects/{project}/bundle").json()
        response = client.post("/api/import/provenance", json=body)
        assert response.status_code == 201
        assert response.json()["records_added"] == 0


def test_hard_interruption_does_not_complete_or_commit_partial_results(tmp_path):
    """A killed target leaves an explicit running row; v0.1 has no automatic recovery."""
    db = "sqlite:///" + str(tmp_path / "interrupted.sqlite")
    code = """
import os, sys
from nx_trace import TraceStore
from nx_loop import LoopEngine, generate
from nx_schema import RunInput
class Interrupted:
    name = "interrupted"
    version = "1.0"
    def predict(self, query, parameters):
        os._exit(17)
trace = TraceStore(sys.argv[1], initialize=True)
loop = LoopEngine(trace)
pid = trace.project("Interruption control")["id"]
bid = loop.register_benchmark(pid, generate(per_family=4))["id"]
loop.registry.register(Interrupted())
loop.execute(RunInput(benchmark_id=bid, target="interrupted"))
"""
    result = subprocess.run([sys.executable, "-c", code, db], timeout=30, env=os.environ.copy())
    assert result.returncode == 17
    trace = TraceStore(db)
    from nx_loop import LoopEngine
    from nx_schema import RunInput

    try:
        loop = LoopEngine(trace)
        pid = trace.records(kind="research_project")[0]["id"]
        run = loop.runs(pid)[0]
        assert run["status"] == "running"
        assert loop.run_detail(run["id"])["results"] == []
        fresh = loop.execute(RunInput(benchmark_id=run["benchmark_id"]))
        assert fresh["status"] == "complete"
        assert loop.run_detail(run["id"])["status"] == "running"
    finally:
        trace.engine.dispose()
