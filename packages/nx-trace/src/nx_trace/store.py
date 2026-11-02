import time
from collections import deque
from uuid import uuid4

from nx_schema import EdgeInput, EntityInput, Kind, Relation, digest
from sqlalchemy import func, select

from .db import Base, Edge, Record, connect, install_guards


def serialize(record):
    return {c.name: getattr(record, c.name) for c in record.__table__.columns}


class TraceStore:
    def __init__(self, url, initialize=False):
        self.engine, self.sessions = connect(url)
        if initialize:
            Base.metadata.create_all(self.engine)
            with self.engine.begin() as c:
                install_guards(c)

    def add_record(
        self,
        db,
        project_id,
        body,
        logical_id=None,
        version=1,
        record_id=None,
        created=None,
    ):
        if not isinstance(body, EntityInput):
            body = EntityInput.model_validate(body)
        rid = record_id or str(uuid4())
        canonical = {
            "kind": body.kind.value,
            "label": body.label,
            "payload": body.payload,
        }
        row = Record(
            id=rid,
            project_id=project_id,
            logical_id=logical_id or rid,
            version=version,
            **canonical,
            content_hash=digest(canonical),
            actor=body.actor,
            created=time.time() if created is None else created,
        )
        db.add(row)
        db.flush()
        return row

    def project(self, label, actor="Local researcher"):
        pid = str(uuid4())
        with self.sessions.begin() as db:
            return serialize(
                self.add_record(
                    db,
                    pid,
                    EntityInput(
                        kind=Kind.PROJECT,
                        label=label,
                        payload={"description": "Local research workspace"},
                        actor=actor,
                    ),
                    record_id=pid,
                )
            )

    def require(self, db, rid):
        row = db.get(Record, rid)
        if not row:
            raise KeyError("Research record not found")
        return row

    def create(self, project_id, body):
        with self.sessions.begin() as db:
            if self.require(db, project_id).kind != Kind.PROJECT:
                raise ValueError("Not a project")
            return serialize(self.add_record(db, project_id, body))

    def require_project(self, db, project_id):
        project = self.require(db, project_id)
        if project.kind != Kind.PROJECT:
            raise ValueError("Expected a research project identity")
        return project

    def version(self, rid, body, expected_version):
        with self.sessions.begin() as db:
            old = self.require(db, rid)
            latest = db.scalar(
                select(func.max(Record.version)).where(Record.logical_id == old.logical_id)
            )
            if latest != expected_version or old.version != latest:
                raise ValueError("Version conflict: reload the latest record")
            if old.kind != body.kind.value:
                raise ValueError("Version must preserve entity kind")
            if old.kind == Kind.PROJECT:
                raise ValueError("Project identities cannot be revised in this release")
            new = self.add_record(
                db, old.project_id, body, logical_id=old.logical_id, version=latest + 1
            )
            self.add_edge(
                db,
                EdgeInput(
                    source_id=new.id,
                    target_id=old.id,
                    relation=Relation.SUPERSEDES,
                    actor=body.actor,
                ),
            )
            return serialize(new)

    def add_edge(self, db, body, edge_id=None, created=None):
        if not isinstance(body, EdgeInput):
            body = EdgeInput.model_validate(body)
        a, b = self.require(db, body.source_id), self.require(db, body.target_id)
        if a.project_id != b.project_id:
            raise ValueError("Cross-project edges are not permitted")
        if a.id == b.id:
            raise ValueError("Self edges are not permitted")
        if body.relation in (Relation.SUPPORTED, Relation.CONTRADICTED):
            if a.kind not in (Kind.CLAIM, Kind.CONCLUSION) or b.kind not in (
                Kind.EVIDENCE,
                Kind.OBSERVATION,
                Kind.OUTPUT,
            ):
                raise ValueError(
                    "Evidence relationships require claim/conclusion → evidence/observation/output"
                )
        if body.relation == Relation.GENERATED and b.kind != Kind.EXECUTION:
            raise ValueError("generated_by must point to an execution")
        if body.relation == Relation.SUPERSEDES and (
            a.logical_id != b.logical_id or a.version <= b.version
        ):
            raise ValueError("supersedes must link a newer version to its own history")
        if body.relation in (Relation.DERIVED, Relation.DEPENDS, Relation.SUPERSEDES):
            queue = [b.id]
            seen = set()
            while queue:
                node = queue.pop()
                if node == a.id:
                    raise ValueError("Cyclic derivation is not permitted")
                if node in seen:
                    continue
                seen.add(node)
                queue.extend(
                    db.scalars(
                        select(Edge.target_id).where(
                            Edge.source_id == node,
                            Edge.relation.in_(
                                [
                                    Relation.DERIVED,
                                    Relation.DEPENDS,
                                    Relation.SUPERSEDES,
                                ]
                            ),
                        )
                    )
                )
        existing = db.scalar(
            select(Edge).where(
                Edge.source_id == a.id,
                Edge.target_id == b.id,
                Edge.relation == body.relation.value,
                Edge.assessment == body.assessment,
            )
        )
        if existing:
            if existing.actor != body.actor or existing.rationale != body.rationale:
                raise ValueError(
                    "Relationship already exists with different attribution; append a separate annotation or review to preserve the new judgment"
                )
            return existing
        fields = body.model_dump(mode="json")
        row = Edge(
            id=edge_id or str(uuid4()),
            project_id=a.project_id,
            created=time.time() if created is None else created,
            content_hash=digest(fields),
            **fields,
        )
        db.add(row)
        db.flush()
        return row

    def edge(self, body):
        with self.sessions.begin() as db:
            return serialize(self.add_edge(db, body))

    def get(self, rid):
        with self.sessions() as db:
            row = self.require(db, rid)
            return {
                **serialize(row),
                "history": [
                    serialize(r)
                    for r in db.scalars(
                        select(Record)
                        .where(Record.logical_id == row.logical_id)
                        .order_by(Record.version)
                    )
                ],
                "outgoing": [
                    serialize(e) for e in db.scalars(select(Edge).where(Edge.source_id == rid))
                ],
                "incoming": [
                    serialize(e) for e in db.scalars(select(Edge).where(Edge.target_id == rid))
                ],
            }

    def records(self, project_id=None, kind=None, limit=300):
        with self.sessions() as db:
            query = select(Record)
            if project_id:
                query = query.where(Record.project_id == project_id)
            if kind:
                query = query.where(Record.kind == kind)
            return [
                serialize(r) for r in db.scalars(query.order_by(Record.created.desc()).limit(limit))
            ]

    def graph(self, project_id, root=None, depth=2, relation=None, limit=200):
        with self.sessions() as db:
            self.require(db, project_id)
            edges = list(db.scalars(select(Edge).where(Edge.project_id == project_id)))
            if relation:
                edges = [e for e in edges if e.relation == relation]
            if root:
                if self.require(db, root).project_id != project_id:
                    raise ValueError("Root belongs to another project")
                seen = {root}
                queue = deque([(root, 0)])
                truncated = False
                while queue:
                    node, level = queue.popleft()
                    if level >= depth:
                        continue
                    for e in edges:
                        neighbor = (
                            e.target_id
                            if e.source_id == node
                            else e.source_id
                            if e.target_id == node
                            else None
                        )
                        if neighbor and neighbor not in seen:
                            if len(seen) >= limit:
                                truncated = True
                                continue
                            seen.add(neighbor)
                            queue.append((neighbor, level + 1))
                rows = list(db.scalars(select(Record).where(Record.id.in_(seen))))
            else:
                rows = list(
                    db.scalars(
                        select(Record)
                        .where(Record.project_id == project_id)
                        .order_by(Record.created)
                        .limit(limit + 1)
                    )
                )
                truncated = len(rows) > limit
                rows = rows[:limit]
                seen = {r.id for r in rows}
            return {
                "nodes": [serialize(r) for r in rows],
                "edges": [
                    serialize(e) for e in edges if e.source_id in seen and e.target_id in seen
                ],
                "truncated": truncated,
                "root": root,
                "depth": depth,
                "semantics": "Version-specific records; graph adjacency is not a truth score.",
            }

    def claim_state(self, rid):
        with self.sessions() as db:
            claim = self.require(db, rid)
            if claim.kind not in (Kind.CLAIM, Kind.CONCLUSION):
                raise ValueError("Select a claim or conclusion")
            edges = list(db.scalars(select(Edge).where(Edge.source_id == rid)))
            support = [
                e
                for e in edges
                if e.relation == Relation.SUPPORTED
                and e.assessment in ("fixture_oracle", "human_judgment")
            ]
            contrary = [
                e
                for e in edges
                if e.relation == Relation.CONTRADICTED
                and e.assessment in ("fixture_oracle", "human_judgment")
            ]
            citations = [
                e for e in edges if e.relation in (Relation.SUPPORTED, Relation.CONTRADICTED)
            ]
            status = (
                "conflicting"
                if support and contrary
                else "contradicted"
                if contrary
                else "supported"
                if support
                else "awaiting_review"
                if citations
                else "unsupported"
            )
            # Causal/evidence ancestors, never undirected membership, establish source lineage.
            seen = {rid}
            queue = [rid]
            has_source = False
            all_edges = list(db.scalars(select(Edge).where(Edge.project_id == claim.project_id)))
            while queue:
                current = queue.pop()
                row = db.get(Record, current)
                if row.kind == Kind.SOURCE:
                    has_source = True
                for e in all_edges:
                    if (
                        e.source_id == current
                        and e.relation
                        in (
                            Relation.DERIVED,
                            Relation.SUPPORTED,
                            Relation.CONTRADICTED,
                            Relation.DEPENDS,
                        )
                        and e.target_id not in seen
                    ):
                        seen.add(e.target_id)
                        queue.append(e.target_id)
            return {
                "status": status,
                "incomplete_provenance": not has_source,
                "support_count": len(support),
                "contradiction_count": len(contrary),
                "citation_count": len(citations),
                "basis": sorted({e.assessment for e in support + contrary}),
                "caveat": "Evidence linkage and fixture judgments do not establish real-world factual correctness.",
            }

    def verify(self, project_id):
        with self.sessions() as db:
            records = list(db.scalars(select(Record).where(Record.project_id == project_id)))
            edges = list(db.scalars(select(Edge).where(Edge.project_id == project_id)))
            bad = [
                r.id
                for r in records
                if digest({"kind": r.kind, "label": r.label, "payload": r.payload})
                != r.content_hash
            ]
            for e in edges:
                fields = {
                    k: getattr(e, k)
                    for k in (
                        "source_id",
                        "target_id",
                        "relation",
                        "rationale",
                        "assessment",
                        "actor",
                    )
                }
                if digest(fields) != e.content_hash:
                    bad.append(e.id)
            return {
                "ok": not bad,
                "records_checked": len(records),
                "edges_checked": len(edges),
                "invalid_ids": bad,
                "scope": "Content hash consistency, not source authenticity or factual correctness.",
            }
