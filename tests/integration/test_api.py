from fastapi.testclient import TestClient
from nx_api.app import create_app


def test_complete_research_workflow(trace):
    with TestClient(create_app(trace), base_url="http://127.0.0.1") as client:
        project = client.post("/api/projects", json={"label": "End-to-end investigation"}).json()
        pid = project["id"]
        benchmark = client.post(
            f"/api/projects/{pid}/fixtures", json={"seed": 13, "per_family": 4}
        ).json()
        bid = benchmark["id"]
        before = client.post("/api/runs", json={"benchmark_id": bid}).json()
        assert before["status"] == "complete"
        failed = next(r for r in before["results"] if r["case_id"] == "revision-000")
        claim = client.get(f"/api/records/{failed['claim_id']}/claim-state").json()
        assert claim["status"] == "contradicted" and not claim["incomplete_provenance"]
        graph = client.get(
            f"/api/projects/{pid}/graph",
            params={"root": failed["claim_id"], "depth": 3},
        ).json()
        assert any(n["kind"] == "execution" for n in graph["nodes"])
        proposal = client.post(
            "/api/corrections",
            json={
                "run_id": before["id"],
                "case_id": failed["case_id"],
                "rule": "prefer_latest",
                "rationale": "Use newer evidence revision",
                "actor": "Investigator",
            },
        ).json()
        cid = proposal["id"]
        assert client.post(f"/api/corrections/{cid}/rerun", json={}).status_code == 422
        review = client.post(
            f"/api/corrections/{cid}/reviews",
            json={
                "decision": "accept",
                "rationale": "The newer revision resolves the failure",
                "actor": "Reviewer",
            },
        ).json()
        assert review["review_status"] == "accepted"
        after = client.post(f"/api/corrections/{cid}/rerun", json={"scope": "affected"}).json()
        assert (
            after["summary"]["unique_cases"] == 1
            and after["summary"]["metrics"]["accuracy"]["value"] == 1
        )
        comparison = client.get(
            "/api/compare", params={"before": before["id"], "after": after["id"]}
        ).json()
        assert comparison["paired_cases"] == 1 and comparison["partial_overlap"]
        exported = client.get(f"/api/runs/{after['id']}/report").json()
        assert exported["configuration"]["payload"]["parameters"]["prefer_latest"] is True
        assert exported["semantic_digest"] == after["semantic_digest"]
        assert "expected_answer" in exported["benchmark"]["cases"][0]
        assert client.get(f"/api/projects/{pid}/integrity").json()["ok"]
        assert client.get(f"/api/runs/{after['id']}/results.csv").text.startswith("case_id,repeat,")
        saved = client.post(
            f"/api/projects/{pid}/layouts",
            json={
                "name": "Failure analysis",
                "view": "evaluations",
                "inspector_width": 400,
                "run_id": after["id"],
                "family": "revision",
            },
        )
        assert saved.status_code == 201
        assert (
            client.get(f"/api/projects/{pid}/layouts").json()[0]["configuration"]["inspector_width"]
            == 400
        )


def test_reader_writer_access_and_csrf(trace):
    with TestClient(
        create_app(trace, reader_token="read-test", writer_token="write-test"),
        base_url="http://127.0.0.1",
    ) as client:
        assert client.get("/api/health").status_code == 200
        assert client.get("/api/projects").status_code == 401
        assert (
            client.get("/api/projects", headers={"Authorization": "Bearer read-test"}).status_code
            == 200
        )
        assert (
            client.post(
                "/api/projects",
                json={"label": "Denied"},
                headers={"Authorization": "Bearer read-test"},
            ).status_code
            == 401
        )
        assert (
            client.post(
                "/api/projects",
                json={"label": "Allowed"},
                headers={"Authorization": "Bearer write-test"},
            ).status_code
            == 201
        )
        assert (
            client.post(
                "/api/projects",
                json={"label": "Cross origin"},
                headers={
                    "Authorization": "Bearer write-test",
                    "Origin": "https://untrusted.example",
                },
            ).status_code
            == 403
        )
        assert (
            client.post(
                "/api/projects",
                data="label=x",
                headers={
                    "Authorization": "Bearer write-test",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            ).status_code
            == 415
        )


def test_errors_and_strict_contract(trace):
    with TestClient(create_app(trace), base_url="http://127.0.0.1") as client:
        assert client.get("/api/records/missing").status_code == 404
        assert client.post("/api/projects", json={"label": "", "extra": True}).status_code == 422
        project = client.post("/api/projects", json={"label": "Project"}).json()["id"]
        assert (
            client.post(f"/api/projects/{project}/fixtures", json={"per_family": 10000}).status_code
            == 422
        )
        assert client.get(f"/api/projects/{project}/graph?depth=99").status_code == 422
        assert "Benchmark" in client.get("/openapi.json").json()["components"]["schemas"]
