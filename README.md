# XRPL Quality Agent (Scenario Runner + Telemetry + Summaries)

A portfolio project aligned to RippleX “Quality Enforcers / Developer Insights” style work:
- Load high-level scenarios (YAML) describing JSON-RPC calls and invariants
- Run scenarios against a target endpoint (or the included mock server)
- Store run artifacts (requests/responses/latency) in SQLite
- Time-series style anomaly detection (simple z-score over latency/error rate)
- Human-readable summary report + optional **LLM** summary (OpenAI-compatible) via env var

## Install
```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
```

## Run against the included mock server
Terminal A:
```bash
qe mock-server
```

Terminal B:
```bash
qe run scenarios/sample.yml --endpoint http://127.0.0.1:7000 --db runs.db
qe report --db runs.db --last 1
```

## Run against a real rippled JSON-RPC endpoint
```bash
qe run scenarios/sample.yml --endpoint https://your-rippled:port --db runs.db
```

## Optional LLM summary
Set environment variables:
```bash
export QE_OPENAI_API_KEY="..."
export QE_OPENAI_BASE_URL="https://api.openai.com/v1"   # or your gateway
export QE_OPENAI_MODEL="gpt-4.1-mini"                   # example
qe report --db runs.db --last 1 --llm
```

