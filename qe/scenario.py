from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import yaml
from pydantic import BaseModel, Field

class Invariant(BaseModel):
    type: str  # "status_ok" | "jsonpath_exists" | "equals"
    path: str | None = None
    value: Any | None = None

class Step(BaseModel):
    name: str
    method: str = Field(default="server_info")
    params: dict = Field(default_factory=dict)
    invariants: list[Invariant] = Field(default_factory=list)

class Scenario(BaseModel):
    name: str
    steps: list[Step]

def load_scenario(path: str) -> Scenario:
    raw = yaml.safe_load(open(path, "r", encoding="utf-8"))
    return Scenario.model_validate(raw)
