from __future__ import annotations

import os
from typing import Any

import httpx
from rich.text import Text

from qe.config import openai_config

def heuristic_summary(run: dict) -> str:
    steps = run["steps"]
    ok = sum(1 for s in steps if s["ok"])
    total = len(steps)
    p95 = sorted([s["latency_ms"] for s in steps])[int(0.95 * max(0, total - 1))] if total else 0
    errors = [s for s in steps if not s["ok"]]
    lines = []
    lines.append(f"Scenario '{run['scenario_name']}' against {run['endpoint']}")
    lines.append(f"Steps OK: {ok}/{total} | p95 latency: {p95:.1f}ms")
    if errors:
        lines.append("Failures:")
        for e in errors[:5]:
            lines.append(f"- {e['step_name']}: {e.get('error')}")
    return "\n".join(lines)

async def llm_summary(run: dict) -> str:
    cfg = openai_config()
    if not cfg.api_key:
        raise RuntimeError("QE_OPENAI_API_KEY not set")

    # OpenAI-compatible Chat Completions
    url = cfg.base_url.rstrip("/") + "/chat/completions"
    prompt = (
        "You are summarizing an XRPL JSON-RPC test run for developers. "
        "Write a concise summary with: overall status, key failures, anomalies, and next steps. "
        "Use bullet points.\n\n"
        f"RUN JSON:\n{run}"
    )
    payload = {
        "model": cfg.model,
        "messages": [
            {"role": "system", "content": "Be precise and technical."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 400,
    }
    headers = {"Authorization": f"Bearer {cfg.api_key}"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(url, json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"]
