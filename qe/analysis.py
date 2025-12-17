from __future__ import annotations

import math
from dataclasses import dataclass

@dataclass(frozen=True)
class Anomaly:
    step_name: str
    kind: str
    detail: str

def zscore_anomalies(steps: list[dict], baseline_steps: list[dict]) -> list[Anomaly]:
    """Simple z-score anomalies on latency_ms per step_name."""
    by_name = {}
    for s in baseline_steps:
        by_name.setdefault(s["step_name"], []).append(s["latency_ms"])

    out: list[Anomaly] = []
    for s in steps:
        name = s["step_name"]
        lat = float(s["latency_ms"])
        base = by_name.get(name, [])
        if len(base) < 5:
            continue
        mu = sum(base) / len(base)
        var = sum((x - mu) ** 2 for x in base) / (len(base) - 1)
        sd = math.sqrt(var) if var > 1e-9 else 0.0
        if sd > 0 and (lat - mu) / sd >= 3.0:
            out.append(Anomaly(step_name=name, kind="latency_spike", detail=f"{lat:.1f}ms vs {mu:.1f}±{sd:.1f}"))
    return out
