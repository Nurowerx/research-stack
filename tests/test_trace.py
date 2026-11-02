import pytest
from nx_schema import EdgeInput, EntityInput
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError


def test_claim_citation_is_not_truth(trace, project):
    claim = trace.create(
        project, EntityInput(kind="claim", label="Claim", payload={"statement": "A"})
    )
    evidence = trace.create(project, EntityInput(kind="evidence", label="Evidence"))
    assert trace.claim_state(claim["id"])["status"] == "unsupported"
    trace.edge(
        EdgeInput(
            source_id=claim["id"],
            target_id=evidence["id"],
            relation="supported_by",
            assessment="citation_only",
        )
    )
    state = trace.claim_state(claim["id"])
    assert state["status"] == "awaiting_review" and state["incomplete_provenance"]
    trace.edge(
        EdgeInput(
            source_id=claim["id"],
            target_id=evidence["id"],
            relation="supported_by",
            assessment="human_judgment",
        )
    )
    assert trace.claim_state(claim["id"])["status"] == "supported"
    trace.edge(
        EdgeInput(
            source_id=claim["id"],
            target_id=evidence["id"],
            relation="contradicted_by",
            assessment="human_judgment",
        )
    )
    assert trace.claim_state(claim["id"])["status"] == "conflicting"


def test_version_and_immutability(trace, project):
    old = trace.create(
        project,
        EntityInput(kind="annotation", label="Interpretation", payload={"text": "Original"}),
    )
    new = trace.version(
        old["id"],
        EntityInput(kind="annotation", label="Revised", payload={"text": "Revision"}),
        1,
    )
    assert old["id"] != new["id"] and new["logical_id"] == old["logical_id"] and new["version"] == 2
    assert trace.get(old["id"])["payload"]["text"] == "Original"
    assert len(trace.get(new["id"])["history"]) == 2
    with pytest.raises(ValueError, match="Version conflict"):
        trace.version(
            old["id"],
            EntityInput(kind="annotation", label="Lost update", payload={"text": "Bad"}),
            1,
        )
    for operation in (
        "UPDATE trace_records SET label='corrupt' WHERE id=:id",
        "DELETE FROM trace_records WHERE id=:id",
    ):
        with pytest.raises(IntegrityError), trace.engine.begin() as db:
            db.execute(text(operation), {"id": old["id"]})
    assert trace.verify(project)["ok"]


def test_graph_types_cycles_and_scope(trace, project):
    a = trace.create(project, EntityInput(kind="observation", label="A"))
    b = trace.create(project, EntityInput(kind="observation", label="B"))
    trace.edge(EdgeInput(source_id=a["id"], target_id=b["id"], relation="derived_from"))
    with pytest.raises(ValueError, match="Cyclic"):
        trace.edge(EdgeInput(source_id=b["id"], target_id=a["id"], relation="derived_from"))
    with pytest.raises(ValueError, match="Evidence relationships"):
        trace.edge(EdgeInput(source_id=a["id"], target_id=b["id"], relation="supported_by"))
    other = trace.project("Other")
    with pytest.raises(ValueError, match="Cross-project"):
        trace.edge(EdgeInput(source_id=a["id"], target_id=other["id"], relation="associated_with"))
    graph = trace.graph(project, a["id"], 1)
    assert {n["id"] for n in graph["nodes"]} == {a["id"], b["id"]}
    assert len(trace.graph(project, a["id"], 0)["nodes"]) == 1
    assert trace.graph(project, a["id"], 1, limit=1)["truncated"]


@pytest.mark.parametrize(
    "body",
    [
        {"kind": "claim", "label": "Bad", "payload": {}},
        {"kind": "data_source", "label": "Bad", "payload": {"origin": 5}},
        {
            "kind": "dataset_version",
            "label": "Bad",
            "payload": {"content_hash": "z" * 64},
        },
        {"kind": "observation", "label": "Bad", "payload": {"x": float("nan")}},
        {"kind": "imaginary", "label": "Bad"},
    ],
)
def test_schema_rejects_invalid(body):
    with pytest.raises((ValueError, ValidationError)):
        EntityInput.model_validate(body)
