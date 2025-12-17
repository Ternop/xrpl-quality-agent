from __future__ import annotations

from typing import Any


def _jsonpath_get(obj: Any, path: str) -> Any:
    # tiny JSONPath-ish: "result.info.build_version"
    cur = obj
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            raise KeyError(path)
    return cur


def check_invariants(response_json: dict | None, invariants: list[dict]) -> tuple[bool, list[str]]:
    if response_json is None:
        return False, ["no response json"]
    errors: list[str] = []
    for inv in invariants:
        t = inv.get("type")
        if t == "status_ok":
            # rippled JSON-RPC returns `status: "success"` on success
            if (
                response_json.get("status") != "success"
                and response_json.get("result", {}).get("status") != "success"
            ):
                errors.append("status not success")
        elif t == "jsonpath_exists":
            path = inv.get("path")
            try:
                _jsonpath_get(response_json, path)
            except Exception:
                errors.append(f"missing path: {path}")
        elif t == "equals":
            path = inv.get("path")
            expected = inv.get("value")
            try:
                actual = _jsonpath_get(response_json, path)
                if actual != expected:
                    errors.append(f"expected {path}={expected} got {actual}")
            except Exception:
                errors.append(f"missing path: {path}")
        else:
            errors.append(f"unknown invariant type: {t}")
    return (len(errors) == 0), errors
