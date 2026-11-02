import pytest
from nx_loop import LoopEngine, generate
from nx_trace import TraceStore


@pytest.fixture
def trace(tmp_path):
    store = TraceStore("sqlite:///" + str(tmp_path / "test.sqlite"), initialize=True)
    yield store
    store.engine.dispose()


@pytest.fixture
def project(trace):
    return trace.project("Test investigation")["id"]


@pytest.fixture
def loop(trace):
    return LoopEngine(trace)


@pytest.fixture
def benchmark(loop, project):
    return loop.register_benchmark(project, generate(per_family=4))["id"]
