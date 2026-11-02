from typing import Protocol

from nx_schema import Prediction, QueryInput
from pydantic import JsonValue

RULES = {"prefer_latest", "trusted_only", "abstain_conflict", "abstain_missing"}


class EvaluationTarget(Protocol):
    name: str
    version: str

    def predict(self, query: QueryInput, parameters: dict[str, JsonValue]) -> Prediction: ...


class EvidencePolicy:
    version = "1.0.0"
    kind = "deterministic fixture policy"

    def __init__(self, name):
        self.name = name

    def validate_parameters(self, parameters):
        if set(parameters) - RULES:
            raise ValueError("Unknown algorithm rule")
        if any(type(value) is not bool for value in parameters.values()):
            raise ValueError("Evidence policy rules must be booleans")

    def predict(self, query, parameters):
        options = {key: self.name == "evidence-aware" for key in RULES} | parameters
        facts = [
            e
            for e in query.evidence
            if e.key == query.query_key and (not options["trusted_only"] or e.trusted)
        ]
        if not facts:
            return Prediction(
                answer=None if options["abstain_missing"] else "unresolved",
                evidence_ids=[],
            )
        if options["prefer_latest"]:
            latest = max(e.revision for e in facts)
            facts = [e for e in facts if e.revision == latest]
        if options["abstain_conflict"] and len({e.value for e in facts}) > 1:
            return Prediction(answer=None)
        chosen = facts[0]
        return Prediction(answer=chosen.value, evidence_ids=[chosen.id])


class TargetRegistry:
    def __init__(self):
        self.targets = {name: EvidencePolicy(name) for name in ("first-match", "evidence-aware")}

    def register(self, target: EvaluationTarget):
        if target.name in self.targets:
            raise ValueError("Target already registered")
        self.targets[target.name] = target

    def get(self, name):
        if name not in self.targets:
            raise ValueError("Unknown target")
        return self.targets[name]

    def describe(self):
        return [
            {
                "name": t.name,
                "version": t.version,
                "kind": getattr(t, "kind", "registered evaluation target"),
            }
            for t in self.targets.values()
        ]
