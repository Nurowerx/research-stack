"""Optional explicit read-only verification/import of an existing ETL export."""

import argparse
import json
from pathlib import Path

from nx_adapters.exports import import_etl, read_etl_directory, validate_etl
from nx_trace import TraceStore

parser = argparse.ArgumentParser()
parser.add_argument("--folder", required=True)
parser.add_argument("--database")
parser.add_argument("--output", required=True)
args = parser.parse_args()
data = read_etl_directory(args.folder)
result = validate_etl(data)
if args.database:
    trace = TraceStore(args.database, initialize=True)
    project = trace.project("Epistemic Trust Lab / imported reference")
    result = import_etl(
        trace,
        project["id"],
        data,
        origin="Existing local Epistemic Trust Lab reference export; imported read-only",
    )
    result["project_id"] = project["id"]
    result["trace_integrity"] = trace.verify(project["id"])
    trace.engine.dispose()
Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
