from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Mock rippled JSON-RPC")


@app.post("/")
async def rpc(payload: dict):
    method = payload.get("method")
    # minimal pretend responses
    if method == "server_info":
        return JSONResponse(
            {
                "status": "success",
                "result": {"info": {"build_version": "1.0.0-mock", "complete_ledgers": "1-10"}},
            }
        )
    if method == "fee":
        return JSONResponse(
            {"status": "success", "result": {"drops": {"base_fee": "10", "median_fee": "12"}}}
        )
    if method == "ledger":
        return JSONResponse(
            {"status": "success", "result": {"ledger_index": "validated", "validated": True}}
        )
    return JSONResponse(
        {"status": "error", "error": "unknownMethod", "request": payload}, status_code=400
    )


def run(host: str = "127.0.0.1", port: int = 7000):
    uvicorn.run(app, host=host, port=port, log_level="info")
