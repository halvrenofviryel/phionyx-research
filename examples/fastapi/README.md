# FastAPI Integration Example

> Status: Planned — see [Issue #2](https://github.com/halvrenofviryel/phionyx-research/issues/2)

A minimal FastAPI wrapper exposing the Phionyx governance pipeline as an HTTP endpoint.

## Planned Endpoint

```
POST /govern
Content-Type: application/json

{
  "text": "User input text",
  "profile": "edu"
}
```

## Planned Response

```json
{
  "governed_response": "...",
  "state": {
    "A": 0.5,
    "V": 0.0,
    "H": 0.3,
    "phi": 0.82,
    "entropy": 0.31
  },
  "safety": {
    "kill_switch": "inactive",
    "ethics_gate": "pass",
    "input_safety": "pass",
    "revision_directive": "pass"
  },
  "telemetry": {
    "pipeline_blocks_executed": 46,
    "execution_time_ms": 120,
    "deterministic": true
  },
  "audit": {
    "record_id": "...",
    "hash_chain": "...",
    "timestamp": "..."
  }
}
```

## Architecture Note

Phionyx Core is **framework-agnostic**. FastAPI lives in this example, not in the core SDK. The core never imports delivery-layer frameworks — external dependencies enter through ports.

## Coming Soon

- `main.py` — Minimal server
- `requirements.txt` — FastAPI + Uvicorn only
- Full walkthrough with curl examples
