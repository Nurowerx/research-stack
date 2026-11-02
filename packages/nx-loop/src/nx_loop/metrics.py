import statistics

from nx_schema import Case, Prediction, canonical

DEFINITIONS = {
    "accuracy": "Exact answer match, including correct abstention, divided by all cases.",
    "unsupported_assertion_rate": "Non-abstaining answers that disagree with the synthetic oracle divided by all non-abstaining answers.",
    "evidence_consistency": "Answered outputs with at least one citation and all cited visible items matching that answer, divided by answered outputs; not a truth test.",
    "retrieval_precision": "Correct cited oracle evidence IDs divided by unique cited IDs.",
    "retrieval_recall": "Correct cited oracle evidence IDs divided by oracle evidence IDs; abstention cases have denominator zero.",
    "appropriate_abstention": "Abstentions on unresolved cases divided by unresolved cases.",
    "memory_fidelity": "Exact correctness on revision cases divided by revision cases.",
    "error_recovery": "Exact correctness on recovery cases divided by recovery cases.",
    "output_consistency": "Cases whose repeated semantic outputs match divided by unique cases with at least two repeats.",
}


def score(case: Case, prediction: Prediction):
    correct = prediction.answer == case.expected_answer
    answered = prediction.answer is not None
    ids = set(prediction.evidence_ids)
    gold = set(case.expected_evidence_ids)
    visible = {e.id: e for e in case.input.evidence}
    consistent = (
        answered
        and bool(ids)
        and all(i in visible and visible[i].value == prediction.answer for i in ids)
    )
    pairs = {
        "accuracy": [int(correct), 1],
        "unsupported_assertion_rate": [int(answered and not correct), int(answered)],
        "evidence_consistency": [int(consistent), int(answered)],
        "retrieval_precision": [len(ids & gold), len(ids)],
        "retrieval_recall": [len(ids & gold), len(gold)],
        "appropriate_abstention": [
            int(case.expected_answer is None and not answered),
            int(case.expected_answer is None),
        ],
        "memory_fidelity": [
            int(correct and case.family == "revision"),
            int(case.family == "revision"),
        ],
        "error_recovery": [
            int(correct and case.family == "recovery"),
            int(case.family == "recovery"),
        ],
    }
    error = (
        None
        if correct
        else "unwarranted_abstention"
        if not answered
        else "unsupported_assertion"
        if case.expected_answer is None
        else "wrong_answer"
    )
    return {
        "pairs": pairs,
        "correct": correct,
        "error": error,
        "oracle_basis": "synthetic fixture, not human-verified real-world truth",
    }


def aggregate(rows):
    # Repeated deterministic measurements are not independent sample units.
    unique = {}
    for row in rows:
        unique.setdefault(row["case_id"], []).append(row)
    metrics = {}
    for name in DEFINITIONS:
        if name == "output_consistency":
            eligible = [group for group in unique.values() if len(group) > 1]
            n = sum(len({canonical(r["prediction"]) for r in group}) == 1 for group in eligible)
            d = len(eligible)
        else:
            # Equal weight per unique case, averaged across repeated executions.
            n = sum(
                statistics.mean(r["scores"]["pairs"][name][0] for r in group)
                for group in unique.values()
            )
            d = sum(
                statistics.mean(r["scores"]["pairs"][name][1] for r in group)
                for group in unique.values()
            )
        metrics[name] = {
            "value": n / d if d else None,
            "numerator": n,
            "denominator": d,
            "definition": DEFINITIONS[name],
        }
    latencies = [r["latency_ms"] for r in rows]
    metrics["latency_ms"] = {
        "value": statistics.mean(latencies) if latencies else None,
        "unit": "ms",
        "n": len(latencies),
        "min": min(latencies) if latencies else None,
        "max": max(latencies) if latencies else None,
        "definition": "Measured predict call elapsed time, excluding persistence and scoring.",
    }
    metrics["confidence_calibration"] = {
        "value": None,
        "reason": "Targets do not provide validated probabilistic predictions.",
    }
    groups = {
        family: aggregate_family([r for r in rows if r["family"] == family])
        for family in sorted({r["family"] for r in rows})
    }
    return {
        "metrics": metrics,
        "groups": groups,
        "unique_cases": len(unique),
        "executions": len(rows),
        "uncertainty": {
            "interval": None,
            "reason": "Descriptive census of fixed synthetic fixtures; repeated deterministic runs are not independent population samples.",
        },
    }


def aggregate_family(rows):
    unique = {}
    for r in rows:
        unique.setdefault(r["case_id"], []).append(r["scores"]["correct"])
    return {
        "accuracy": statistics.mean(statistics.mean(x) for x in unique.values())
        if unique
        else None,
        "cases": len(unique),
    }


def compare_rows(before, after):
    def group(rows):
        result = {}
        for r in rows:
            result.setdefault(r["case_id"], []).append(float(r["scores"]["correct"]))
        return {k: statistics.mean(v) for k, v in result.items()}

    a, b = group(before), group(after)
    keys = sorted(a.keys() & b.keys())
    if not keys:
        raise ValueError("No overlapping cases to compare")
    differences = [b[k] - a[k] for k in keys]
    failed_before = [k for k in keys if a[k] < 1]
    return {
        "paired_cases": len(keys),
        "before_accuracy": statistics.mean(a[k] for k in keys),
        "after_accuracy": statistics.mean(b[k] for k in keys),
        "accuracy_delta": statistics.mean(differences),
        "improved": sum(d > 0 for d in differences),
        "regressed": sum(d < 0 for d in differences),
        "unchanged": sum(d == 0 for d in differences),
        "regression_detected": any(d < 0 for d in differences),
        "partial_overlap": set(a) != set(b),
        "correction_success": {
            "value": sum(b[k] == 1 for k in failed_before) / len(failed_before)
            if failed_before
            else None,
            "numerator": sum(b[k] == 1 for k in failed_before),
            "denominator": len(failed_before),
            "definition": "Previously imperfect shared cases whose repeated outputs are all correct after the change. Descriptive, not causal attribution.",
        },
        "pairs": [
            {"case_id": k, "before": a[k], "after": b[k], "delta": b[k] - a[k]} for k in keys
        ],
        "interval": None,
        "p_value": None,
        "method": "Paired descriptive comparison over overlapping unique case IDs; no inferential significance claimed.",
    }
