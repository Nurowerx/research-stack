import pytest
from nx_adapters.exports import (
    ResidencyExport,
    etl_digest,
    import_etl,
    residency_fixture,
    validate_etl,
)


def sample():
    rows = [
        {
            "case_id": "example-0",
            "adapter": "naive",
            "memory": "none",
            "distraction": False,
            "scores": {"exact_accuracy": 0},
        }
    ]
    data = {
        "rows": rows,
        "benchmark": {"representative_fixture": True},
        "config": {"representative_fixture": True},
    }
    data["metadata"] = {
        "schema_version": "1.0",
        "status": "complete",
        "run_id": "representative-etl-fixture",
        "synthetic": True,
        "participant_count": 0,
        "observations": 1,
        "cases": 1,
        "observation_digest": etl_digest(rows),
        "benchmark_digest": etl_digest(data["benchmark"]),
        "config_digest": etl_digest(data["config"]),
    }
    return data


def test_etl_contract_and_integrity(trace, project):
    data = sample()
    assert validate_etl(data)["observations"] == 1
    imported = import_etl(
        trace, project, data, origin="Representative fixture, not an actual ETL run"
    )
    assert trace.get(imported["dataset_version_id"])["payload"]["external_export"] == data
    assert trace.verify(project)["ok"]
    data["rows"][0]["scores"]["exact_accuracy"] = 1
    with pytest.raises(ValueError, match="observation_digest"):
        validate_etl(data)


def test_resident_contract_does_not_claim_real_measurements():
    data = residency_fixture()
    assert data.representative_fixture is True and len(data.rows) == 3
    changed = data.model_dump()
    changed["representative_fixture"] = False
    with pytest.raises(ValueError):
        ResidencyExport.model_validate(changed)
