"""Independent readers. These never import or modify external project code."""

import hashlib
import json
from pathlib import Path
from typing import Literal

from nx_schema import EdgeInput, Kind, Relation, StrictModel, digest
from nx_trace.db import Record
from pydantic import Field
from sqlalchemy import select


def etl_digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def read_etl_directory(folder):
    folder = Path(folder)

    def read(name):
        return json.loads((folder / name).read_text(encoding="utf-8"))

    data = {
        "metadata": read("metadata.json"),
        "benchmark": read("benchmark.json"),
        "config": read("config.json"),
        "rows": [
            json.loads(line)
            for line in (folder / "observations.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ],
    }
    validate_etl(data)
    return data


def validate_etl(data):
    meta = data["metadata"]
    rows = data["rows"]
    if meta["schema_version"] != "1.0" or meta.get("status") != "complete":
        raise ValueError("Unsupported or incomplete ETL export")
    if meta.get("synthetic") is not True or meta.get("participant_count") != 0:
        raise ValueError("This adapter contract accepts synthetic ETL exports only")
    for key, value in [
        ("observation_digest", rows),
        ("benchmark_digest", data["benchmark"]),
        ("config_digest", data["config"]),
    ]:
        if etl_digest(value) != meta[key]:
            raise ValueError(f"ETL {key} mismatch")
    if len(rows) != meta["observations"] or len({r["case_id"] for r in rows}) != meta["cases"]:
        raise ValueError("ETL count mismatch")
    identities = [(r["case_id"], r["adapter"], r["memory"], r["distraction"]) for r in rows]
    if len(set(identities)) != len(identities):
        raise ValueError("Duplicate ETL observation identity")
    for row in rows:
        if row["scores"]["exact_accuracy"] not in (0, 1):
            raise ValueError("Invalid ETL correctness")
    return {
        "adapter": "epistemic-trust-lab/1.0",
        "origin_run": meta["run_id"],
        "observations": len(rows),
        "unique_cases": meta["cases"],
        "verified": [
            "observation_digest",
            "benchmark_digest",
            "config_digest",
            "row identities",
            "counts",
        ],
        "scope": "Read-only export validation. Not execution of ETL or verification of its scientific claims.",
        "synthetic": True,
    }


class ResidencyRow(StrictModel):
    case_id: str
    strategy: str
    memory_budget_mb: float = Field(gt=0)
    resident_experts: int = Field(ge=0)
    latency_ms: float = Field(ge=0)
    peak_memory_mb: float = Field(ge=0)
    output_match: bool


class ResidencyExport(StrictModel):
    schema_version: Literal["nx-residency-fixture-1"] = "nx-residency-fixture-1"
    representative_fixture: Literal[True] = True
    source_label: str = "Representative synthetic Resident Model Lab contract; no live integration"
    rows: list[ResidencyRow] = Field(min_length=1)


def residency_fixture():
    return ResidencyExport(
        rows=[
            ResidencyRow(
                case_id=f"fixture-{i}",
                strategy=strategy,
                memory_budget_mb=1024,
                resident_experts=count,
                latency_ms=latency,
                peak_memory_mb=memory,
                output_match=True,
            )
            for i, (strategy, count, latency, memory) in enumerate(
                [
                    ("fifo", 2, 120, 800),
                    ("lru", 3, 95, 950),
                    ("oracle-fixture", 4, 80, 1020),
                ]
            )
        ]
    )


def import_etl(
    trace, project_id, data, origin="User-provided ETL export", actor="Local researcher"
):
    validation = validate_etl(data)
    with trace.sessions.begin() as db:
        trace.require_project(db, project_id)
        checksum = digest(data)
        for existing in db.scalars(
            select(Record).where(
                Record.project_id == project_id, Record.kind == Kind.DATASET_VERSION
            )
        ):
            if (
                existing.payload.get("adapter") == "epistemic-trust-lab/1.0"
                and existing.payload.get("content_hash") == checksum
            ):
                return {
                    "dataset_version_id": existing.id,
                    "already_imported": True,
                    **validation,
                }
        source = trace.add_record(
            db,
            project_id,
            {
                "kind": Kind.SOURCE,
                "label": "Epistemic Trust Lab export",
                "payload": {"origin": origin, "validation": validation},
                "actor": actor,
            },
        )
        dataset = trace.add_record(
            db,
            project_id,
            {
                "kind": Kind.DATASET_VERSION,
                "label": f"ETL / {validation['origin_run']}",
                "payload": {
                    "content_hash": checksum,
                    "adapter": "epistemic-trust-lab/1.0",
                    "external_export": data,
                    "synthetic": True,
                    "validation": validation,
                },
                "actor": actor,
            },
        )
        trace.add_edge(
            db,
            EdgeInput(
                source_id=dataset.id,
                target_id=source.id,
                relation=Relation.DERIVED,
                actor=actor,
            ),
        )
        for i, row in enumerate(data["rows"]):
            observation = trace.add_record(
                db,
                project_id,
                {
                    "kind": Kind.OBSERVATION,
                    "label": f"{row['case_id']} / {row['adapter']} / {row['memory']}",
                    "payload": {
                        "dataset_version_id": dataset.id,
                        "row_index": i,
                        "external_observation": row,
                        "synthetic": True,
                    },
                    "actor": actor,
                },
            )
            trace.add_edge(
                db,
                EdgeInput(
                    source_id=observation.id,
                    target_id=dataset.id,
                    relation=Relation.DERIVED,
                    actor=actor,
                ),
            )
    return {"dataset_version_id": dataset.id, **validation}
