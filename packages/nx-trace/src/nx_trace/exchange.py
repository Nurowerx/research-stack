"""Validated, atomic TRACE graph exchange. LOOP execution tables are not reconstructed."""

from collections import defaultdict
from typing import Literal
from uuid import UUID

from nx_schema import EdgeInput, EntityInput, Kind, StrictModel, digest
from pydantic import Field, field_validator
from sqlalchemy import select

from .db import Edge, Record
from .store import serialize


class RecordSnapshot(EntityInput):
    id: str
    project_id: str
    logical_id: str
    version: int = Field(ge=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    created: float = Field(ge=0)

    @field_validator("id", "project_id", "logical_id")
    @classmethod
    def uuid(cls, value):
        UUID(value)
        return value


class EdgeSnapshot(EdgeInput):
    id: str
    project_id: str
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    created: float = Field(ge=0)

    @field_validator("id", "project_id", "source_id", "target_id")
    @classmethod
    def uuid(cls, value):
        UUID(value)
        return value


class ProvenanceBundle(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    records: list[RecordSnapshot] = Field(min_length=1, max_length=20000)
    edges: list[EdgeSnapshot] = Field(default_factory=list, max_length=100000)


def export_bundle(trace, project_id):
    with trace.sessions() as db:
        trace.require_project(db, project_id)
        return {
            "schema_version": "1.0",
            "records": [
                serialize(r)
                for r in db.scalars(
                    select(Record).where(Record.project_id == project_id).order_by(Record.id)
                )
            ],
            "edges": [
                serialize(e)
                for e in db.scalars(
                    select(Edge).where(Edge.project_id == project_id).order_by(Edge.id)
                )
            ],
        }


def import_bundle(trace, value):
    bundle = ProvenanceBundle.model_validate(value)
    records = {r.id: r for r in bundle.records}
    if len(records) != len(bundle.records) or len({e.id for e in bundle.edges}) != len(
        bundle.edges
    ):
        raise ValueError("Duplicate snapshot identity")
    projects = [r for r in bundle.records if r.kind == Kind.PROJECT]
    if len(projects) != 1:
        raise ValueError("A bundle must contain exactly one project")
    pid = projects[0].id
    histories = defaultdict(list)
    for record in bundle.records:
        if record.project_id != pid:
            raise ValueError("Cross-project bundle record")
        if (
            digest(record.model_dump(mode="json", include={"kind", "label", "payload"}))
            != record.content_hash
        ):
            raise ValueError("Record content hash mismatch")
        histories[record.logical_id].append(record)
    for history in histories.values():
        if (
            sorted(r.version for r in history) != list(range(1, len(history) + 1))
            or len({r.kind for r in history}) != 1
        ):
            raise ValueError("Incomplete or inconsistent version history")
    for edge in bundle.edges:
        if edge.project_id != pid or edge.source_id not in records or edge.target_id not in records:
            raise ValueError("Missing or cross-project edge endpoint")
        if (
            digest(edge.model_dump(mode="json", include=set(EdgeInput.model_fields)))
            != edge.content_hash
        ):
            raise ValueError("Edge content hash mismatch")
    added_records = added_edges = 0
    with trace.sessions.begin() as db:
        for record in bundle.records:
            raw = record.model_dump(mode="json")
            existing = db.get(Record, record.id)
            if existing:
                if serialize(existing) != raw:
                    raise ValueError("Existing record identity has different content or metadata")
                continue
            trace.add_record(
                db,
                pid,
                EntityInput.model_validate(
                    record.model_dump(include=set(EntityInput.model_fields))
                ),
                logical_id=record.logical_id,
                version=record.version,
                record_id=record.id,
                created=record.created,
            )
            added_records += 1
        for edge in bundle.edges:
            raw = edge.model_dump(mode="json")
            existing = db.get(Edge, edge.id)
            if existing:
                if serialize(existing) != raw:
                    raise ValueError("Existing edge identity has different content or metadata")
                continue
            created = trace.add_edge(
                db,
                EdgeInput.model_validate(edge.model_dump(include=set(EdgeInput.model_fields))),
                edge_id=edge.id,
                created=edge.created,
            )
            if created.id != edge.id:
                raise ValueError("Relationship identity collision")
            added_edges += 1
    return {
        "project_id": pid,
        "records_added": added_records,
        "edges_added": added_edges,
        "scope": "TRACE provenance only; imported execution records are historical evidence, not runnable LOOP run rows.",
    }
