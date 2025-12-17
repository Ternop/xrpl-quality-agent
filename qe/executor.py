from __future__ import annotations

import time
from dataclasses import dataclass

import httpx

from qe.validators import check_invariants

@dataclass(frozen=True)
class StepResult:
    ok: bool
    latency_ms: float
    status_code: int | None
    response_json: dict | None
    error: str | None

async def call_jsonrpc(endpoint: str, method: str, params: dict) -> tuple[int, dict]:
    # standard rippled JSON-RPC request shape
    payload = {"method": method, "params": [params]}
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(endpoint, json=payload)
        return r.status_code, r.json()

async def run_step(endpoint: str, step: dict) -> StepResult:
    start = time.time()
    try:
        sc, body = await call_jsonrpc(endpoint, step["method"], step.get("params", {}))
        latency_ms = (time.time() - start) * 1000.0
        ok, inv_errs = check_invariants(body, [i for i in step.get("invariants", [])])
        if not ok:
            return StepResult(False, latency_ms, sc, body, "; ".join(inv_errs))
        return StepResult(True, latency_ms, sc, body, None)
    except Exception as e:
        latency_ms = (time.time() - start) * 1000.0
        return StepResult(False, latency_ms, None, None, str(e))
