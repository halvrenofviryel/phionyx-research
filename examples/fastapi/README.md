# FastAPI Integration Example

**Status:** Implemented — resolves Issue #2

A minimal FastAPI wrapper exposing the Phionyx governance pipeline as an HTTP endpoint.

## Architecture Note

Phionyx Core is framework-agnostic. FastAPI lives in this example, not in the core SDK.  
The core never imports delivery-layer frameworks—external dependencies enter through ports.

## Getting Started

Install the Core SDK in development mode:

```bash
pip install -e .
```

Ensure you have installed `PyYAML` as it is a core dependency for physics profiles.

Install example dependencies:

```bash
pip install -r examples/fastapi/requirements.txt
```

Run the server:

```bash
python examples/fastapi/main.py
```

## API Endpoint

### `POST /govern`

Wraps the 46-block Phionyx pipeline (v3.8.0) to process user input.

### Request Body

```json
{
  "text": "User input text",
  "profile": "edu"
}
```

### Test with curl

```bash
curl -X POST http://127.0.0.1:8000/govern \
  -H "Content-Type: application/json" \
  -d '{"text": "How can I improve my study habits?", "profile": "edu"}'
```
### Swagger UI

Open `http://localhost:8000/docs` for interactive API documentation.

## Expected Response

The endpoint returns a structured envelope containing the governed response, state metrics, and execution telemetry.

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
    "record_id": "aud_1714175400",
    "hash_chain": "...",
    "timestamp": "2026-04-26T23:50:00Z"
  }
}
```
