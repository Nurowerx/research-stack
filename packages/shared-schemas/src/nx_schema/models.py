import hashlib
import json
import re
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator


def canonical(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Kind(StrEnum):
    PROJECT = "research_project"
    DATASET = "dataset"
    DATASET_VERSION = "dataset_version"
    SOURCE = "data_source"
    OBSERVATION = "observation"
    SCENARIO = "experimental_scenario"
    EXPERIMENT = "experiment"
    MODEL = "model"
    MODEL_VERSION = "model_version"
    ALGORITHM = "algorithm"
    CONFIG = "configuration"
    EXECUTION = "execution"
    OUTPUT = "output"
    CLAIM = "claim"
    EVIDENCE = "evidence"
    EVALUATION = "evaluation"
    METRIC = "metric"
    ANNOTATION = "annotation"
    CORRECTION = "correction"
    RESEARCHER = "researcher"
    REVIEW = "review"
    CONCLUSION = "conclusion"


class Relation(StrEnum):
    DERIVED = "derived_from"
    GENERATED = "generated_by"
    EVALUATED = "evaluated_against"
    SUPPORTED = "supported_by"
    CONTRADICTED = "contradicted_by"
    DEPENDS = "depends_on"
    REVIEWED = "reviewed_by"
    CORRECTED = "corrected_by"
    SUPERSEDES = "supersedes"
    ASSOCIATED = "associated_with"
    BELONGS = "belongs_to_experiment"


class EntityInput(StrictModel):
    kind: Kind
    label: str = Field(min_length=1, max_length=200)
    payload: dict[str, JsonValue] = Field(default_factory=dict)
    actor: str = Field(default="Local researcher", min_length=1, max_length=100)

    @model_validator(mode="after")
    def finite_and_typed(self):
        canonical(self.payload)
        required = {
            Kind.CLAIM: "statement",
            Kind.CONCLUSION: "statement",
            Kind.CONFIG: "parameters",
            Kind.DATASET_VERSION: "content_hash",
            Kind.SOURCE: "origin",
            Kind.ANNOTATION: "text",
        }
        key = required.get(self.kind)
        if key and key not in self.payload:
            raise ValueError(f"{self.kind} requires payload.{key}")
        if key in ("statement", "origin", "text") and (
            not isinstance(self.payload[key], str) or not self.payload[key].strip()
        ):
            raise ValueError(f"{key} must be a nonempty string")
        if key == "parameters" and not isinstance(self.payload[key], dict):
            raise ValueError("parameters must be an object")
        if key == "content_hash" and (
            not isinstance(self.payload[key], str)
            or not re.fullmatch("[0-9a-f]{64}", self.payload[key])
        ):
            raise ValueError("content_hash must be SHA-256 hex")
        return self


class EdgeInput(StrictModel):
    source_id: str
    target_id: str
    relation: Relation
    rationale: str = Field(default="", max_length=2000)
    assessment: Literal["citation_only", "fixture_oracle", "human_judgment", "structural"] = (
        "structural"
    )
    actor: str = Field(default="Local researcher", min_length=1, max_length=100)


class EvidenceItem(StrictModel):
    id: str = Field(min_length=1, max_length=100)
    key: str
    value: str
    revision: int = Field(ge=1)
    trusted: bool = True
    source: str


class QueryInput(StrictModel):
    case_id: str
    query_key: str
    evidence: list[EvidenceItem]


class Case(StrictModel):
    id: str
    family: Literal["lookup", "revision", "conflict", "missing", "distractor", "recovery"]
    split: Literal["development", "heldout"]
    question: str
    input: QueryInput
    expected_answer: str | None
    expected_evidence_ids: list[str]


class Benchmark(StrictModel):
    name: str = Field(min_length=1, max_length=200)
    schema_version: Literal["1.0"] = "1.0"
    generator_version: str = "nx-fixtures-1"
    seed: int = 20261102
    synthetic: Literal[True] = True
    cases: list[Case] = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def identities(self):
        ids = [c.id for c in self.cases]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate case IDs")
        for c in self.cases:
            evidence_ids = [e.id for e in c.input.evidence]
            if c.id != c.input.case_id:
                raise ValueError("Query/case ID mismatch")
            if len(evidence_ids) != len(set(evidence_ids)):
                raise ValueError("Duplicate evidence IDs")
            if not set(c.expected_evidence_ids) <= set(evidence_ids):
                raise ValueError("Ground-truth evidence ID is missing")
            if c.expected_answer is None and c.expected_evidence_ids:
                raise ValueError("Abstention fixture cannot nominate an answer citation")
        return self


class Prediction(StrictModel):
    answer: str | None
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0, le=1)


class RunInput(StrictModel):
    benchmark_id: str
    target: str = "first-match"
    split: Literal["development", "heldout"] = "development"
    repeats: int = Field(default=2, ge=1, le=5)
    parameters: dict[str, JsonValue] = Field(default_factory=dict)
    case_ids: list[str] = Field(default_factory=list, max_length=1000)
    correction_ids: list[str] = Field(default_factory=list, max_length=30)
    parent_run_id: str | None = None
    actor: str = Field(default="Local researcher", min_length=1, max_length=100)


class CorrectionInput(StrictModel):
    run_id: str
    case_id: str
    rule: Literal["prefer_latest", "trusted_only", "abstain_conflict", "abstain_missing"]
    rationale: str = Field(min_length=5, max_length=2000)
    actor: str = Field(min_length=1, max_length=100)


class ReviewInput(StrictModel):
    decision: Literal["accept", "reject"]
    rationale: str = Field(min_length=3, max_length=2000)
    actor: str = Field(min_length=1, max_length=100)
