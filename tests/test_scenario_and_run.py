import asyncio

from fastapi.testclient import TestClient

from qe.executor import run_step
from qe.mock_server import app


def test_mock_server_methods():
    client = TestClient(app)
    r = client.post("/", json={"method": "server_info", "params": [{}]})
    assert r.status_code == 200
    assert r.json()["status"] == "success"


def test_executor_step_against_mock():
    # Use TestClient as transport by spinning uvicorn is overkill; just hit app directly
    client = TestClient(app)
    endpoint = "http://testserver/"

    async def _call_jsonrpc(endpoint, method, params):
        resp = client.post("/", json={"method": method, "params": [params]})
        return resp.status_code, resp.json()

    # monkeypatch by direct import override
    import qe.executor as ex

    ex.call_jsonrpc = _call_jsonrpc  # type: ignore

    res = asyncio.run(
        run_step(endpoint, {"method": "fee", "params": {}, "invariants": [{"type": "status_ok"}]})
    )
    assert res.ok
