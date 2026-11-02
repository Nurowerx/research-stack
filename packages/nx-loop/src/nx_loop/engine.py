import hashlib
import importlib.metadata
import inspect
import platform
import time
from pathlib import Path
from threading import Lock
from uuid import uuid4

import psutil
from nx_schema import (
    Benchmark,
    CorrectionInput,
    EdgeInput,
    Kind,
    Prediction,
    Relation,
    ReviewInput,
    RunInput,
    digest,
)
from nx_trace.db import Record, Result, Run
from nx_trace.store import serialize
from sqlalchemy import select

from .metrics import aggregate, compare_rows, score
from .targets import TargetRegistry


class LoopEngine:
    def __init__(self, trace, registry=None):
        self.trace = trace
        self.registry = registry or TargetRegistry()
        self.lock = Lock()

    def register_benchmark(self, project_id, benchmark: Benchmark, actor="Local researcher"):
        payload = benchmark.model_dump(mode="json")
        checksum = digest(payload)
        with self.trace.sessions.begin() as db:
            self.trace.require_project(db, project_id)
            for r in db.scalars(
                select(Record).where(
                    Record.project_id == project_id, Record.kind == Kind.DATASET_VERSION
                )
            ):
                if r.payload.get("content_hash") == checksum and "benchmark" in r.payload:
                    return serialize(r)
            source = self.trace.add_record(
                db,
                project_id,
                {
                    "kind": Kind.SOURCE,
                    "label": "Synthetic ledger generator",
                    "payload": {
                        "origin": "nx_loop.fixtures.generate",
                        "generator_version": benchmark.generator_version,
                        "seed": benchmark.seed,
                        "synthetic": True,
                        "content_hash": checksum,
                    },
                    "actor": actor,
                },
            )
            dataset = db.scalar(
                select(Record).where(
                    Record.project_id == project_id,
                    Record.kind == Kind.DATASET,
                    Record.label == benchmark.name,
                )
            )
            if dataset is None:
                dataset = self.trace.add_record(
                    db,
                    project_id,
                    {
                        "kind": Kind.DATASET,
                        "label": benchmark.name,
                        "payload": {"synthetic": True},
                        "actor": actor,
                    },
                )
            previous = next(
                (
                    r
                    for r in db.scalars(
                        select(Record)
                        .where(
                            Record.project_id == project_id,
                            Record.kind == Kind.DATASET_VERSION,
                        )
                        .order_by(Record.version.desc())
                    )
                    if r.payload.get("dataset_id") == dataset.id
                ),
                None,
            )
            version = self.trace.add_record(
                db,
                project_id,
                {
                    "kind": Kind.DATASET_VERSION,
                    "label": f"{benchmark.name} / {checksum[:8]}",
                    "payload": {
                        "content_hash": checksum,
                        "benchmark": payload,
                        "dataset_id": dataset.id,
                    },
                    "actor": actor,
                },
                logical_id=previous.logical_id if previous else None,
                version=previous.version + 1 if previous else 1,
            )
            if previous:
                self.trace.add_edge(
                    db,
                    EdgeInput(
                        source_id=version.id,
                        target_id=previous.id,
                        relation=Relation.SUPERSEDES,
                        actor=actor,
                    ),
                )
            self.trace.add_edge(
                db,
                EdgeInput(
                    source_id=version.id,
                    target_id=source.id,
                    relation=Relation.DERIVED,
                    actor=actor,
                ),
            )
            self.trace.add_edge(
                db,
                EdgeInput(
                    source_id=version.id,
                    target_id=dataset.id,
                    relation=Relation.ASSOCIATED,
                    actor=actor,
                ),
            )
            for case in benchmark.cases:
                scenario = self.trace.add_record(
                    db,
                    project_id,
                    {
                        "kind": Kind.SCENARIO,
                        "label": case.id,
                        "payload": {
                            "benchmark_id": version.id,
                            **case.model_dump(mode="json"),
                        },
                        "actor": actor,
                    },
                )
                self.trace.add_edge(
                    db,
                    EdgeInput(
                        source_id=scenario.id,
                        target_id=version.id,
                        relation=Relation.DERIVED,
                        actor=actor,
                    ),
                )
                for item in case.input.evidence:
                    evidence = self.trace.add_record(
                        db,
                        project_id,
                        {
                            "kind": Kind.EVIDENCE,
                            "label": f"{case.id} / {item.id}",
                            "payload": {
                                "benchmark_id": version.id,
                                "case_id": case.id,
                                "item": item.model_dump(mode="json"),
                                "synthetic": True,
                            },
                            "actor": actor,
                        },
                    )
                    self.trace.add_edge(
                        db,
                        EdgeInput(
                            source_id=evidence.id,
                            target_id=scenario.id,
                            relation=Relation.DERIVED,
                            actor=actor,
                        ),
                    )
            return serialize(version)

    def benchmark(self, rid):
        row = self.trace.get(rid)
        if row["kind"] != Kind.DATASET_VERSION or "benchmark" not in row["payload"]:
            raise ValueError("Not an executable benchmark version")
        benchmark = Benchmark.model_validate(row["payload"]["benchmark"])
        if digest(benchmark.model_dump(mode="json")) != row["payload"]["content_hash"]:
            raise ValueError("Benchmark content integrity mismatch")
        return row, benchmark

    def correction_state(self, cid):
        correction = self.trace.get(cid)
        if correction["kind"] != Kind.CORRECTION:
            raise ValueError("Not a correction")
        with self.trace.sessions() as db:
            reviews = [
                serialize(r)
                for r in db.scalars(
                    select(Record)
                    .where(
                        Record.project_id == correction["project_id"],
                        Record.kind == Kind.REVIEW,
                    )
                    .order_by(Record.created)
                )
                if r.payload.get("correction_id") == cid
            ]
        latest = {r["actor"]: r for r in reviews}
        votes = {r["payload"]["decision"] for r in latest.values()}
        status = (
            "disputed"
            if len(votes) > 1
            else "accepted"
            if votes == {"accept"}
            else "rejected"
            if votes == {"reject"}
            else "pending"
        )
        return {
            **correction,
            "review_status": status,
            "reviews": reviews,
            "basis": "Attributed human judgment, not verified ground truth.",
        }

    def propose(self, body: CorrectionInput):
        run = self.run_detail(body.run_id)
        _, benchmark = self.benchmark(run["benchmark_id"])
        case = next((c for c in benchmark.cases if c.id == body.case_id), None)
        if not case or not any(r["case_id"] == body.case_id for r in run["results"]):
            raise ValueError("Case is not in this execution")
        if case.split != "development":
            raise ValueError("Interactive corrections are restricted to development cases")
        if all(r["scores"]["correct"] for r in run["results"] if r["case_id"] == body.case_id):
            raise ValueError("Select a failed case to propose a correction")
        with self.trace.sessions.begin() as db:
            correction = self.trace.add_record(
                db,
                run["project_id"],
                {
                    "kind": Kind.CORRECTION,
                    "label": f"{body.rule} / {body.case_id}",
                    "payload": {
                        **body.model_dump(),
                        "benchmark_id": run["benchmark_id"],
                        "patch": {body.rule: True},
                        "kind": "algorithm_rule_proposal",
                    },
                    "actor": body.actor,
                },
            )
            for r in run["results"]:
                if r["case_id"] == body.case_id:
                    self.trace.add_edge(
                        db,
                        EdgeInput(
                            source_id=r["output_id"],
                            target_id=correction.id,
                            relation=Relation.CORRECTED,
                            actor=body.actor,
                        ),
                    )
            return serialize(correction)

    def review(self, cid, body: ReviewInput):
        correction = self.trace.get(cid)
        if correction["kind"] != Kind.CORRECTION:
            raise ValueError("Not a correction")
        with self.trace.sessions.begin() as db:
            row = self.trace.add_record(
                db,
                correction["project_id"],
                {
                    "kind": Kind.REVIEW,
                    "label": f"{body.decision} / {body.actor}",
                    "payload": {"correction_id": cid, **body.model_dump()},
                    "actor": body.actor,
                },
            )
            self.trace.add_edge(
                db,
                EdgeInput(
                    source_id=cid,
                    target_id=row.id,
                    relation=Relation.REVIEWED,
                    actor=body.actor,
                ),
            )
        return self.correction_state(cid)

    def execute(self, request: RunInput):
        if not self.lock.acquire(blocking=False):
            raise ValueError("Another evaluation is running; retry after it completes")
        try:
            return self._execute(request)
        finally:
            self.lock.release()

    def _execute(self, request):
        version, benchmark = self.benchmark(request.benchmark_id)
        target = self.registry.get(request.target)
        parameters = dict(request.parameters)
        if hasattr(target, "validate_parameters"):
            target.validate_parameters(parameters)
        for cid in request.correction_ids:
            correction = self.correction_state(cid)
            if correction["review_status"] != "accepted":
                raise ValueError("Every applied correction must have an undisputed acceptance")
            if correction["payload"]["benchmark_id"] != request.benchmark_id:
                raise ValueError("Correction belongs to a different benchmark version")
            parameters.update(correction["payload"]["patch"])
        if hasattr(target, "validate_parameters"):
            target.validate_parameters(parameters)
        if request.parent_run_id:
            parent = self.run_detail(request.parent_run_id)
            if parent["benchmark_id"] != request.benchmark_id:
                raise ValueError("Parent run uses a different benchmark version")
        selected = [
            c
            for c in benchmark.cases
            if c.split == request.split and (not request.case_ids or c.id in request.case_ids)
        ]
        if not selected or (request.case_ids and set(request.case_ids) != {c.id for c in selected}):
            raise ValueError("Selected case IDs do not match the requested split")
        pid = version["project_id"]
        rid = str(uuid4())
        start = time.perf_counter()
        process = psutil.Process()
        rss_before = process.memory_info().rss
        with self.trace.sessions.begin() as db:
            config = self.trace.add_record(
                db,
                pid,
                {
                    "kind": Kind.CONFIG,
                    "label": f"{request.target} / configuration",
                    "payload": {
                        "parameters": parameters,
                        "target": target.name,
                        "target_version": target.version,
                        "split": request.split,
                        "repeats": request.repeats,
                        "case_ids": [c.id for c in selected],
                        "correction_ids": request.correction_ids,
                    },
                    "actor": request.actor,
                },
            )
            try:
                target_source_hash = digest(inspect.getsource(type(target)))
            except (OSError, TypeError):
                target_source_hash = None
            algorithm = self.trace.add_record(
                db,
                pid,
                {
                    "kind": Kind.ALGORITHM,
                    "label": target.name,
                    "payload": {
                        "version": target.version,
                        "source_hash": target_source_hash,
                        "kind": getattr(target, "kind", "registered evaluation target"),
                        "source_hash_scope": "Canonical JSON string containing target class source; null if unavailable.",
                    },
                    "actor": request.actor,
                },
            )
            source_files = {
                str(p.name): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in Path(__file__).parent.glob("*.py")
            }
            execution = self.trace.add_record(
                db,
                pid,
                {
                    "kind": Kind.EXECUTION,
                    "label": f"{target.name} / {rid[:8]}",
                    "payload": {
                        "run_id": rid,
                        "python": platform.python_version(),
                        "platform": platform.platform(),
                        "benchmark_hash": version["payload"]["content_hash"],
                        "loop_source_hashes": source_files,
                        "dependencies": {
                            name: importlib.metadata.version(name)
                            for name in ("pydantic", "SQLAlchemy", "psutil")
                        },
                        "target_kind": getattr(target, "kind", "registered evaluation target"),
                    },
                    "actor": request.actor,
                },
            )
            for entity in (config, algorithm):
                self.trace.add_edge(
                    db,
                    EdgeInput(
                        source_id=execution.id,
                        target_id=entity.id,
                        relation=Relation.DEPENDS,
                        actor=request.actor,
                    ),
                )
            self.trace.add_edge(
                db,
                EdgeInput(
                    source_id=execution.id,
                    target_id=request.benchmark_id,
                    relation=Relation.EVALUATED,
                    actor=request.actor,
                ),
            )
            if request.parent_run_id:
                self.trace.add_edge(
                    db,
                    EdgeInput(
                        source_id=execution.id,
                        target_id=parent["execution_id"],
                        relation=Relation.DERIVED,
                        actor=request.actor,
                    ),
                )
            for cid in request.correction_ids:
                self.trace.add_edge(
                    db,
                    EdgeInput(
                        source_id=config.id,
                        target_id=cid,
                        relation=Relation.DERIVED,
                        actor=request.actor,
                    ),
                )
            run = Run(
                id=rid,
                project_id=pid,
                execution_id=execution.id,
                benchmark_id=request.benchmark_id,
                config_id=config.id,
                status="running",
                target=target.name,
                split=request.split,
                scope="selected_cases" if request.case_ids else "full_split",
                request=request.model_dump(),
                summary={},
                created=time.time(),
            )
            db.add(run)
        try:
            rows = []
            with self.trace.sessions.begin() as db:
                scenarios = {
                    r.payload["id"]: r
                    for r in db.scalars(
                        select(Record).where(Record.project_id == pid, Record.kind == Kind.SCENARIO)
                    )
                    if r.payload.get("benchmark_id") == request.benchmark_id
                }
                evidence = {
                    (r.payload["case_id"], r.payload["item"]["id"]): r
                    for r in db.scalars(
                        select(Record).where(Record.project_id == pid, Record.kind == Kind.EVIDENCE)
                    )
                    if r.payload.get("benchmark_id") == request.benchmark_id and "item" in r.payload
                }
                for case in selected:
                    for repetition in range(request.repeats):
                        clock = time.perf_counter_ns()
                        prediction = Prediction.model_validate(
                            target.predict(case.input.model_copy(deep=True), dict(parameters))
                        )
                        latency = (time.perf_counter_ns() - clock) / 1e6
                        scores = score(case, prediction)
                        output = self.trace.add_record(
                            db,
                            pid,
                            {
                                "kind": Kind.OUTPUT,
                                "label": f"{case.id} / repeat {repetition + 1}",
                                "payload": {
                                    "case_id": case.id,
                                    "prediction": prediction.model_dump(),
                                    "run_id": rid,
                                    "repeat": repetition,
                                },
                                "actor": request.actor,
                            },
                        )
                        self.trace.add_edge(
                            db,
                            EdgeInput(
                                source_id=output.id,
                                target_id=execution.id,
                                relation=Relation.GENERATED,
                                actor=request.actor,
                            ),
                        )
                        self.trace.add_edge(
                            db,
                            EdgeInput(
                                source_id=output.id,
                                target_id=scenarios[case.id].id,
                                relation=Relation.DERIVED,
                                actor=request.actor,
                            ),
                        )
                        claim = self.trace.add_record(
                            db,
                            pid,
                            {
                                "kind": Kind.CLAIM,
                                "label": f"{case.id} / answer claim",
                                "payload": {
                                    "statement": prediction.answer or "The policy abstained.",
                                    "case_id": case.id,
                                    "run_id": rid,
                                    "synthetic": True,
                                },
                                "actor": request.actor,
                            },
                        )
                        self.trace.add_edge(
                            db,
                            EdgeInput(
                                source_id=claim.id,
                                target_id=output.id,
                                relation=Relation.DERIVED,
                                actor=request.actor,
                            ),
                        )
                        for eid in prediction.evidence_ids:
                            if (case.id, eid) in evidence:
                                self.trace.add_edge(
                                    db,
                                    EdgeInput(
                                        source_id=claim.id,
                                        target_id=evidence[(case.id, eid)].id,
                                        relation=Relation.SUPPORTED,
                                        assessment="citation_only",
                                        actor=request.actor,
                                    ),
                                )
                        witness = self.trace.add_record(
                            db,
                            pid,
                            {
                                "kind": Kind.EVIDENCE,
                                "label": f"{case.id} / oracle assessment",
                                "payload": {
                                    "expected_answer": case.expected_answer,
                                    "actual_answer": prediction.answer,
                                    "correct": scores["correct"],
                                    "basis": "synthetic fixture oracle",
                                    "run_id": rid,
                                },
                                "actor": request.actor,
                            },
                        )
                        self.trace.add_edge(
                            db,
                            EdgeInput(
                                source_id=witness.id,
                                target_id=scenarios[case.id].id,
                                relation=Relation.DERIVED,
                                actor=request.actor,
                            ),
                        )
                        self.trace.add_edge(
                            db,
                            EdgeInput(
                                source_id=claim.id,
                                target_id=witness.id,
                                relation=Relation.SUPPORTED
                                if scores["correct"]
                                else Relation.CONTRADICTED,
                                assessment="fixture_oracle",
                                actor=request.actor,
                            ),
                        )
                        data = {
                            "case_id": case.id,
                            "repeat": repetition,
                            "family": case.family,
                            "prediction": prediction.model_dump(),
                            "scores": scores,
                            "latency_ms": latency,
                            "output_id": output.id,
                            "claim_id": claim.id,
                        }
                        db.add(Result(id=str(uuid4()), run_id=rid, **data))
                        rows.append(data)
                summary = aggregate(rows)
                summary["resources"] = {
                    "rss_before_bytes": rss_before,
                    "rss_after_bytes": process.memory_info().rss,
                    "wall_seconds": time.perf_counter() - start,
                    "scope": "Process RSS snapshots; not peak allocation or isolated target memory.",
                }
                evaluation = self.trace.add_record(
                    db,
                    pid,
                    {
                        "kind": Kind.EVALUATION,
                        "label": f"{target.name} / measured evaluation",
                        "payload": {"run_id": rid, "summary": summary},
                        "actor": request.actor,
                    },
                )
                self.trace.add_edge(
                    db,
                    EdgeInput(
                        source_id=evaluation.id,
                        target_id=execution.id,
                        relation=Relation.GENERATED,
                        actor=request.actor,
                    ),
                )
                self.trace.add_edge(
                    db,
                    EdgeInput(
                        source_id=evaluation.id,
                        target_id=request.benchmark_id,
                        relation=Relation.EVALUATED,
                        actor=request.actor,
                    ),
                )
                run = db.get(Run, rid)
                run.summary = summary
                run.status = "complete"
                run.completed = time.time()
                run.semantic_digest = digest(
                    [
                        {
                            k: r[k]
                            for k in (
                                "case_id",
                                "repeat",
                                "family",
                                "prediction",
                                "scores",
                            )
                        }
                        for r in rows
                    ]
                )
            return self.run_detail(rid)
        except Exception as exc:
            with self.trace.sessions.begin() as db:
                run = db.get(Run, rid)
                run.status = "failed"
                run.completed = time.time()
                run.error = f"{type(exc).__name__}: {str(exc)[:300]}"
            raise

    def run_detail(self, rid):
        with self.trace.sessions() as db:
            run = db.get(Run, rid)
            if not run:
                raise KeyError("Evaluation run not found")
            return {
                **serialize(run),
                "results": [
                    serialize(r)
                    for r in db.scalars(
                        select(Result)
                        .where(Result.run_id == rid)
                        .order_by(Result.case_id, Result.repeat)
                    )
                ],
            }

    def runs(self, pid):
        with self.trace.sessions() as db:
            return [
                serialize(r)
                for r in db.scalars(
                    select(Run).where(Run.project_id == pid).order_by(Run.created.desc())
                )
            ]

    def compare(self, before_id, after_id):
        before, after = self.run_detail(before_id), self.run_detail(after_id)
        if before["status"] != "complete" or after["status"] != "complete":
            raise ValueError("Only completed runs can be compared")
        if before["benchmark_id"] != after["benchmark_id"] or before["split"] != after["split"]:
            raise ValueError("Comparison requires the same benchmark version and split")
        return {
            "before_id": before_id,
            "after_id": after_id,
            **compare_rows(before["results"], after["results"]),
        }

    def report(self, rid):
        run = self.run_detail(rid)
        version, benchmark = self.benchmark(run["benchmark_id"])
        configuration = self.trace.get(run["config_id"])
        return {
            "schema_version": "1.0",
            "product": "Nurowerx Research Systems",
            "run": run,
            "benchmark": benchmark.model_dump(),
            "benchmark_record": version,
            "configuration": configuration,
            "semantic_digest": run["semantic_digest"],
            "execution": self.trace.get(run["execution_id"]),
            "corrections": [
                self.correction_state(cid) for cid in configuration["payload"]["correction_ids"]
            ],
            "comparison": self.compare(run["request"]["parent_run_id"], rid)
            if run["request"].get("parent_run_id")
            else None,
            "limitations": [
                "Synthetic deterministic policies only. No real language model or research participant evaluated.",
                "Held-out instances share the fixture generator with development cases.",
                "Human corrections are attributed judgments; applying them changes a new configuration, never historical truth.",
                "Runtime latency and resource measurements vary across executions.",
            ],
            "reproduce": {
                "command": "nx-stack reproduce --report report.json",
                "comparison": "semantic_digest excludes UUIDs, times and latency",
            },
        }
