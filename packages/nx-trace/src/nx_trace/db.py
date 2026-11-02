from sqlalchemy import (
    JSON,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    event,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class Record(Base):
    __tablename__ = "trace_records"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), index=True)
    logical_id: Mapped[str] = mapped_column(String(36), index=True)
    version: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(40), index=True)
    label: Mapped[str] = mapped_column(String(200))
    payload: Mapped[dict] = mapped_column(JSON)
    content_hash: Mapped[str] = mapped_column(String(64))
    actor: Mapped[str] = mapped_column(String(100))
    created: Mapped[float] = mapped_column(Float)
    __table_args__ = (UniqueConstraint("logical_id", "version"),)


class Edge(Base):
    __tablename__ = "trace_edges"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), index=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("trace_records.id"), index=True)
    target_id: Mapped[str] = mapped_column(ForeignKey("trace_records.id"), index=True)
    relation: Mapped[str] = mapped_column(String(40))
    rationale: Mapped[str] = mapped_column(Text)
    assessment: Mapped[str] = mapped_column(String(30))
    actor: Mapped[str] = mapped_column(String(100))
    created: Mapped[float] = mapped_column(Float)
    content_hash: Mapped[str] = mapped_column(String(64))
    __table_args__ = (UniqueConstraint("source_id", "target_id", "relation", "assessment"),)


class Run(Base):
    __tablename__ = "loop_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), index=True)
    execution_id: Mapped[str] = mapped_column(ForeignKey("trace_records.id"))
    benchmark_id: Mapped[str] = mapped_column(ForeignKey("trace_records.id"))
    config_id: Mapped[str] = mapped_column(ForeignKey("trace_records.id"))
    status: Mapped[str] = mapped_column(String(20))
    target: Mapped[str] = mapped_column(String(80))
    split: Mapped[str] = mapped_column(String(20))
    scope: Mapped[str] = mapped_column(String(30))
    request: Mapped[dict] = mapped_column(JSON)
    summary: Mapped[dict] = mapped_column(JSON)
    semantic_digest: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created: Mapped[float] = mapped_column(Float)
    completed: Mapped[float | None] = mapped_column(Float, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class Result(Base):
    __tablename__ = "loop_results"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("loop_runs.id"), index=True)
    case_id: Mapped[str] = mapped_column(String(100))
    repeat: Mapped[int] = mapped_column(Integer)
    family: Mapped[str] = mapped_column(String(30))
    output_id: Mapped[str] = mapped_column(ForeignKey("trace_records.id"))
    claim_id: Mapped[str] = mapped_column(ForeignKey("trace_records.id"))
    prediction: Mapped[dict] = mapped_column(JSON)
    scores: Mapped[dict] = mapped_column(JSON)
    latency_ms: Mapped[float] = mapped_column(Float)
    __table_args__ = (UniqueConstraint("run_id", "case_id", "repeat"),)


class Layout(Base):
    __tablename__ = "frame_layouts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), index=True)
    name: Mapped[str] = mapped_column(String(100))
    configuration: Mapped[dict] = mapped_column(JSON)
    created: Mapped[float] = mapped_column(Float)


IMMUTABLE = ("trace_records", "trace_edges", "loop_results")


def install_guards(connection):
    if connection.dialect.name == "sqlite":
        for table in IMMUTABLE:
            for operation in ("UPDATE", "DELETE"):
                connection.exec_driver_sql(
                    f"CREATE TRIGGER IF NOT EXISTS immutable_{table}_{operation.lower()} BEFORE {operation} ON {table} BEGIN SELECT RAISE(ABORT, 'immutable research record'); END"
                )
        connection.exec_driver_sql(
            "CREATE TRIGGER IF NOT EXISTS immutable_completed_run BEFORE UPDATE ON loop_runs WHEN OLD.status IN ('complete','failed') BEGIN SELECT RAISE(ABORT, 'completed runs are immutable'); END"
        )
        connection.exec_driver_sql(
            "CREATE TRIGGER IF NOT EXISTS immutable_run_delete BEFORE DELETE ON loop_runs BEGIN SELECT RAISE(ABORT, 'runs cannot be deleted'); END"
        )
    elif connection.dialect.name == "postgresql":
        connection.exec_driver_sql(
            "CREATE OR REPLACE FUNCTION nx_immutable() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'immutable research record'; END; $$"
        )
        for table in IMMUTABLE:
            connection.exec_driver_sql(f"DROP TRIGGER IF EXISTS immutable_{table} ON {table}")
            connection.exec_driver_sql(
                f"CREATE TRIGGER immutable_{table} BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION nx_immutable()"
            )
        connection.exec_driver_sql(
            "CREATE OR REPLACE FUNCTION nx_run_guard() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN IF TG_OP = 'DELETE' OR OLD.status IN ('complete','failed') THEN RAISE EXCEPTION 'completed runs are immutable'; END IF; RETURN NEW; END; $$"
        )
        connection.exec_driver_sql("DROP TRIGGER IF EXISTS immutable_completed_run ON loop_runs")
        connection.exec_driver_sql(
            "CREATE TRIGGER immutable_completed_run BEFORE UPDATE OR DELETE ON loop_runs FOR EACH ROW EXECUTE FUNCTION nx_run_guard()"
        )


def connect(url):
    engine = create_engine(
        url,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False, "timeout": 30}
        if url.startswith("sqlite")
        else {},
    )
    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def pragma(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA journal_mode=WAL")

    return engine, sessionmaker(engine, expire_on_commit=False)
