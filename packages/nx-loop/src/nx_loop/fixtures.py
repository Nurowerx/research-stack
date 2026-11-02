import random

from nx_schema import Benchmark, Case, EvidenceItem, QueryInput

FAMILIES = ("lookup", "revision", "conflict", "missing", "distractor", "recovery")


def generate(seed=20261102, per_family=20):
    rng = random.Random(seed)  # nosec B311: seeded synthetic fixtures, never credentials.
    cases = []
    for family in FAMILIES:
        for i in range(per_family):
            cid = f"{family}-{i:03}"
            key = f"asset-{rng.randrange(10000, 99999)}"
            old = f"zone-{rng.randrange(10, 40)}"
            new = f"zone-{rng.randrange(50, 90)}"

            def evidence(suffix, value, revision=1, trusted=True, k=key, case_id=cid):
                return EvidenceItem(
                    id=f"{case_id}-{suffix}",
                    key=k,
                    value=value,
                    revision=revision,
                    trusted=trusted,
                    source="seeded synthetic ledger",
                )

            if family == "lookup":
                facts = [evidence("a", new), evidence("d", old, k="other")]
                answer = new
                ids = [facts[0].id]
            elif family in ("revision", "recovery"):
                facts = [evidence("a", old), evidence("b", new, 2)]
                answer = new
                ids = [facts[1].id]
            elif family == "conflict":
                facts = [evidence("a", old, 2), evidence("b", new, 2)]
                answer = None
                ids = []
            elif family == "missing":
                facts = [evidence("d", old, k="other")]
                answer = None
                ids = []
            else:
                facts = [evidence("a", old, 9, False), evidence("b", new, 2, True)]
                answer = new
                ids = [facts[1].id]
            cases.append(
                Case(
                    id=cid,
                    family=family,
                    split="development" if i < per_family // 2 else "heldout",
                    question=f"What is the current supported zone for {key}? Abstain if unresolved.",
                    input=QueryInput(case_id=cid, query_key=key, evidence=facts),
                    expected_answer=answer,
                    expected_evidence_ids=ids,
                )
            )
    return Benchmark(name="Evidence revision benchmark", seed=seed, cases=cases)
