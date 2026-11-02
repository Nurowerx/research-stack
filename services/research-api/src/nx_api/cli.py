import argparse
import json
import os
import tempfile
from pathlib import Path

from nx_loop import LoopEngine, generate
from nx_schema import Benchmark, Kind, RunInput
from nx_trace import TraceStore


def seed(trace):
    projects = trace.records(kind=Kind.PROJECT)
    existing = next((p for p in projects if p["label"] == "Evidence under revision"), None)
    project = existing or trace.project("Evidence under revision")
    loop = LoopEngine(trace)
    benchmark = loop.register_benchmark(project["id"], generate())
    existing_runs = loop.runs(project["id"])
    for target in ("first-match", "evidence-aware"):
        if not any(r["target"] == target and r["status"] == "complete" for r in existing_runs):
            loop.execute(RunInput(benchmark_id=benchmark["id"], target=target))
    return {
        "project_id": project["id"],
        "benchmark_id": benchmark["id"],
        "url": "http://127.0.0.1:8876",
    }


def main():
    parser = argparse.ArgumentParser(description="Nurowerx Research Stack local tools")
    parser.add_argument(
        "--database",
        default=os.environ.get("NX_DATABASE_URL", "sqlite:///research-stack.sqlite"),
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init")
    commands.add_parser("seed")
    serve = commands.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8876)
    run = commands.add_parser("run")
    run.add_argument("--benchmark", required=True)
    run.add_argument("--target", default="first-match")
    run.add_argument("--split", choices=["development", "heldout"], default="development")
    run.add_argument("--report")
    report = commands.add_parser("report")
    report.add_argument("--run", required=True)
    report.add_argument("--output", required=True)
    reproduce = commands.add_parser("reproduce")
    reproduce.add_argument("--report", required=True)
    imported = commands.add_parser("import-etl")
    imported.add_argument("--folder", required=True)
    imported.add_argument("--project", required=True)
    args = parser.parse_args()
    if args.command == "reproduce":
        exported = json.loads(Path(args.report).read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(prefix="nx-reproduce-") as folder:
            trace = TraceStore(
                "sqlite:///" + str(Path(folder) / "reproduce.sqlite"), initialize=True
            )
            loop = LoopEngine(trace)
            pid = trace.project("Reproduction")["id"]
            bid = loop.register_benchmark(pid, Benchmark.model_validate(exported["benchmark"]))[
                "id"
            ]
            cfg = exported["configuration"]["payload"]
            actual = loop.execute(
                RunInput(
                    benchmark_id=bid,
                    target=cfg["target"],
                    split=cfg["split"],
                    repeats=cfg["repeats"],
                    parameters=cfg["parameters"],
                    case_ids=cfg["case_ids"],
                )
            )
            matched = actual["semantic_digest"] == exported["semantic_digest"]
            print(
                json.dumps(
                    {
                        "matched": matched,
                        "expected": exported["semantic_digest"],
                        "actual": actual["semantic_digest"],
                        "scope": "Semantic results only; latency, IDs and timestamps vary.",
                    },
                    indent=2,
                )
            )
            trace.engine.dispose()
            if not matched:
                raise SystemExit(1)
        return
    trace = TraceStore(args.database, initialize=True)
    if args.command == "init":
        # Stamp the initial schema through Alembic; future revisions run here.
        from alembic import command
        from alembic.config import Config

        config = Config()
        config.set_main_option("script_location", str(Path(__file__).parent / "migrations"))
        config.set_main_option("sqlalchemy.url", args.database)
        command.upgrade(config, "head")
        print("Schema initialized at revision 0001")
    elif args.command == "seed":
        print(json.dumps(seed(trace), indent=2))
    elif args.command == "serve":
        if args.host not in ("127.0.0.1", "localhost", "::1") and not os.environ.get(
            "NX_WRITER_TOKEN"
        ):
            raise SystemExit(
                "Remote binding requires NX_WRITER_TOKEN; terminate TLS at a trusted proxy."
            )
        import uvicorn

        from .app import create_app

        uvicorn.run(create_app(trace), host=args.host, port=args.port)
    elif args.command == "run":
        loop = LoopEngine(trace)
        result = loop.execute(
            RunInput(benchmark_id=args.benchmark, target=args.target, split=args.split)
        )
        print(json.dumps({k: v for k, v in result.items() if k != "results"}, indent=2))
        if args.report:
            Path(args.report).write_text(
                json.dumps(loop.report(result["id"]), indent=2), encoding="utf-8"
            )
    elif args.command == "report":
        Path(args.output).write_text(
            json.dumps(LoopEngine(trace).report(args.run), indent=2), encoding="utf-8"
        )
    elif args.command == "import-etl":
        from nx_adapters.exports import import_etl, read_etl_directory

        print(
            json.dumps(
                import_etl(
                    trace,
                    args.project,
                    read_etl_directory(args.folder),
                    origin=str(Path(args.folder).resolve()),
                ),
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
