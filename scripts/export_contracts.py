import json
import tempfile
from pathlib import Path

from nx_api.app import create_app
from nx_schema import (
    Benchmark,
    CorrectionInput,
    EdgeInput,
    EntityInput,
    ReviewInput,
    RunInput,
)
from nx_trace import TraceStore

root = Path(__file__).resolve().parents[1]
schemas = root / "packages/shared-schemas/json"
schemas.mkdir(parents=True, exist_ok=True)
for model in (
    EntityInput,
    EdgeInput,
    Benchmark,
    RunInput,
    CorrectionInput,
    ReviewInput,
):
    (schemas / f"{model.__name__}.schema.json").write_text(
        json.dumps(model.model_json_schema(), indent=2), encoding="utf-8"
    )
with tempfile.TemporaryDirectory(prefix="nx-contracts-") as folder:
    trace = TraceStore("sqlite:///" + str(Path(folder) / "contracts.sqlite"), initialize=True)
    (root / "docs/api/openapi.json").write_text(
        json.dumps(create_app(trace).openapi(), indent=2), encoding="utf-8"
    )
    trace.engine.dispose()
print("Exported implemented API and shared JSON schemas.")
