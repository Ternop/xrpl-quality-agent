from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  started_at REAL NOT NULL,
  endpoint TEXT NOT NULL,
  scenario_name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS steps (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id INTEGER NOT NULL,
  step_name TEXT NOT NULL,
  method TEXT NOT NULL,
  params_json TEXT NOT NULL,
  ok INTEGER NOT NULL,
  latency_ms REAL NOT NULL,
  status_code INTEGER,
  response_json TEXT,
  error TEXT,
  FOREIGN KEY(run_id) REFERENCES runs(id)
);
"""

@dataclass(frozen=True)
class RunRow:
    id: int
    started_at: float
    endpoint: str
    scenario_name: str

class Store:
    def __init__(self, db_path: str):
        self.path = Path(db_path)
        self.conn = sqlite3.connect(self.path)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA foreign_keys=ON;")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self):
        self.conn.close()

    def create_run(self, endpoint: str, scenario_name: str) -> int:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO runs(started_at, endpoint, scenario_name) VALUES(?,?,?)",
            (time.time(), endpoint, scenario_name),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def add_step(
        self,
        run_id: int,
        step_name: str,
        method: str,
        params: dict,
        ok: bool,
        latency_ms: float,
        status_code: int | None,
        response: dict | None,
        error: str | None,
    ) -> None:
        self.conn.execute(
            "INSERT INTO steps(run_id, step_name, method, params_json, ok, latency_ms, status_code, response_json, error) "
            "VALUES(?,?,?,?,?,?,?,?,?)",
            (
                run_id,
                step_name,
                method,
                json.dumps(params, sort_keys=True),
                1 if ok else 0,
                latency_ms,
                status_code,
                json.dumps(response, sort_keys=True) if response is not None else None,
                error,
            ),
        )
        self.conn.commit()

    def last_runs(self, n: int) -> list[RunRow]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, started_at, endpoint, scenario_name FROM runs ORDER BY id DESC LIMIT ?",
            (n,),
        )
        out = []
        for rid, started, endpoint, name in cur.fetchall():
            out.append(RunRow(id=rid, started_at=started, endpoint=endpoint, scenario_name=name))
        return out

    def steps_for_run(self, run_id: int) -> list[dict]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT step_name, method, params_json, ok, latency_ms, status_code, response_json, error "
            "FROM steps WHERE run_id = ? ORDER BY id",
            (run_id,),
        )
        rows = []
        for step_name, method, params_json, ok, lat, sc, resp_json, err in cur.fetchall():
            rows.append(
                {
                    "step_name": step_name,
                    "method": method,
                    "params": json.loads(params_json),
                    "ok": bool(ok),
                    "latency_ms": float(lat),
                    "status_code": sc,
                    "response": json.loads(resp_json) if resp_json else None,
                    "error": err,
                }
            )
        return rows
