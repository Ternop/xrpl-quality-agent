from __future__ import annotations

import asyncio
from datetime import datetime

import typer
from rich.console import Console
from rich.table import Table

from qe.analysis import zscore_anomalies
from qe.executor import run_step
from qe.mock_server import run as run_mock
from qe.scenario import load_scenario
from qe.store import Store
from qe.summarize import heuristic_summary, llm_summary

app = typer.Typer(add_completion=False)
console = Console()


@app.command()
def mock_server(host: str = "127.0.0.1", port: int = 7000):
    """Run a local mock JSON-RPC server."""
    run_mock(host=host, port=port)


@app.command()
def run(
    scenario_path: str,
    endpoint: str = typer.Option(..., help="JSON-RPC endpoint (e.g., http://host:port)"),
    db: str = typer.Option("runs.db", help="SQLite DB file"),
):
    """Run a YAML scenario and store results."""
    scenario = load_scenario(scenario_path)
    store = Store(db)
    run_id = store.create_run(endpoint=endpoint, scenario_name=scenario.name)

    async def _run():
        for step in scenario.steps:
            res = await run_step(endpoint, step.model_dump())
            store.add_step(
                run_id,
                step.name,
                step.method,
                step.params,
                res.ok,
                res.latency_ms,
                res.status_code,
                res.response_json,
                res.error,
            )
            status = "OK" if res.ok else "FAIL"
            console.print(f"[{status}] {step.name} ({res.latency_ms:.1f}ms)")

    asyncio.run(_run())
    console.print(f"Saved run_id={run_id} to {db}")
    store.close()


@app.command()
def report(
    db: str = typer.Option("runs.db"),
    last: int = typer.Option(1, help="How many runs to include (most recent first)"),
    llm: bool = typer.Option(False, help="Generate LLM summary (requires QE_OPENAI_API_KEY)"),
):
    """Print a report for the most recent runs."""
    store = Store(db)
    runs = store.last_runs(last)
    if not runs:
        console.print("No runs found.")
        raise typer.Exit(code=1)

    baseline_steps = []
    if len(runs) >= 2:
        baseline_steps = store.steps_for_run(runs[-1].id)

    for r in runs:
        steps = store.steps_for_run(r.id)
        run_obj = {
            "run_id": r.id,
            "endpoint": r.endpoint,
            "scenario_name": r.scenario_name,
            "started_at": datetime.fromtimestamp(r.started_at).isoformat(),
            "steps": steps,
        }

        table = Table(title=f"Run {r.id}: {r.scenario_name}")
        table.add_column("Step")
        table.add_column("OK")
        table.add_column("Latency (ms)")
        table.add_column("Error")
        for s in steps:
            table.add_row(
                s["step_name"],
                "✅" if s["ok"] else "❌",
                f"{s['latency_ms']:.1f}",
                (s.get("error") or "")[:60],
            )
        console.print(table)

        anomalies = zscore_anomalies(steps, baseline_steps) if baseline_steps else []
        if anomalies:
            console.print("[bold yellow]Anomalies:[/bold yellow]")
            for a in anomalies:
                console.print(f"- {a.step_name}: {a.kind} ({a.detail})")

        console.print("\n[bold]Summary:[/bold]")
        console.print(heuristic_summary(run_obj))

        if llm:
            console.print("\n[bold]LLM Summary:[/bold]")
            try:
                console.print(asyncio.run(llm_summary(run_obj)))
            except Exception as e:
                console.print(f"[red]LLM summary failed:[/red] {e}")

    store.close()


def main():
    app()


if __name__ == "__main__":
    app()
