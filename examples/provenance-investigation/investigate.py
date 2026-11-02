"""Standalone TRACE usage, independent of LOOP or the HTTP service."""

from nx_schema import EdgeInput, EntityInput
from nx_trace import TraceStore

trace = TraceStore("sqlite:///trace-example.sqlite", initialize=True)
pid = trace.project("Standalone evidence investigation")["id"]
source = trace.create(
    pid,
    EntityInput(
        kind="data_source",
        label="Declared synthetic ledger",
        payload={"origin": "Explicitly invented example"},
    ),
)
evidence = trace.create(
    pid,
    EntityInput(
        kind="evidence",
        label="Synthetic record",
        payload={"value": "zone-7", "synthetic": True},
    ),
)
claim = trace.create(
    pid,
    EntityInput(
        kind="claim",
        label="Inspect this claim",
        payload={"statement": "The synthetic item is in zone-7."},
    ),
)
trace.edge(EdgeInput(source_id=evidence["id"], target_id=source["id"], relation="derived_from"))
trace.edge(
    EdgeInput(
        source_id=claim["id"],
        target_id=evidence["id"],
        relation="supported_by",
        assessment="citation_only",
    )
)
print(trace.claim_state(claim["id"]))  # awaiting_review, not automatically true
print(trace.graph(pid, claim["id"], depth=2))
print(trace.verify(pid))
trace.engine.dispose()
