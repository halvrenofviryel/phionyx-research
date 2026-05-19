# OTel envelope export — Tempo + Grafana demo

A one-command stack that lets you see Phionyx governance envelopes flowing as OpenTelemetry spans into Tempo, queried from Grafana.

This is a worked example of the [F2 envelope exporter](../../README.md#mcp-companion-packages--runtime-evidence-over-claude-code) shipped in Phionyx Core v0.4.0.

## What you'll see

After running this example, you can open Grafana at `http://localhost:3000` and find:

- One span per governance envelope, named `phionyx.governed_response.v0_2`.
- Standard OTel GenAI attributes (`gen_ai.system`, `gen_ai.request.model`, `gen_ai.response.id`, etc.) so any GenAI dashboard works out of the box.
- Phionyx-specific governance attributes under `phionyx.*` for the trace id, decision, integrity chain, and MCP tool audit fields.
- One span event per pipeline block step (`phionyx.pipeline.block_step`) plus an extra event when the envelope carries an MCP tool call.

## Prerequisites

- Docker + Docker Compose (or Podman with compose)
- Python 3.10+ with `phionyx-core>=0.4.0` and the OpenTelemetry SDK:

```bash
pip install phionyx-core opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc
```

## Run

```bash
# 1. Start Tempo + Grafana stack
docker compose up -d

# 2. Emit a sample envelope as an OTel span
PHIONYX_OTEL_EXPORT_ENVELOPES=true \
OTEL_ENABLED=true \
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 \
python run_example.py

# 3. Open Grafana → http://localhost:3000 → Explore → Tempo
#    Search service name: phionyx.envelope_export
```

Default Grafana credentials: `admin / admin` (change at first login).

## What the script does

`run_example.py` builds a minimal RGE v0.2 envelope (subject + path + integrity + an `mcp_tool_audit` block) and calls `phionyx_core.telemetry.export_envelope`. The exporter:

1. Reads `PHIONYX_OTEL_EXPORT_ENVELOPES=true` and proceeds.
2. Pins to OTel GenAI semantic conventions `v1.36.0` (default; override with `PHIONYX_OTEL_SEMANTIC_VERSION`).
3. Maps the envelope fields onto span attributes + events using the hybrid `gen_ai.*` / `phionyx.*` namespace strategy.
4. Hands the span to the OTLP exporter, which ships it to Tempo over gRPC on `:4317`.

The mapping is read-only; the envelope itself is the authoritative record. The OTel span is a derived view for vendor backends.

## Bump policy

The OTel GenAI conventions are at **Development** status. Phionyx pins attribute names to a specific spec version so emitted spans don't silently break when the spec evolves. Full policy: [`docs/conventions/otel_semantic_bump_policy.md`](https://github.com/halvrenofviryel/phionyx-research/blob/main/docs/conventions/otel_semantic_bump_policy.md).

## Stop + clean up

```bash
docker compose down -v
```

## Troubleshooting

- **No spans in Grafana:** check `docker compose logs tempo` for OTLP receiver errors. Ensure `OTEL_EXPORTER_OTLP_ENDPOINT` points at the compose-mapped port (`:4317` by default).
- **`export_envelope returned False`:** the opt-in env var `PHIONYX_OTEL_EXPORT_ENVELOPES=true` is missing. The exporter is opt-in on purpose.
- **`ModuleNotFoundError: opentelemetry`:** install the SDK (`pip install opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc`). The Phionyx exporter is a no-op when the SDK isn't available.

## See also

- Phionyx Core SDK: https://pypi.org/project/phionyx-core/
- F2 release notes: https://github.com/halvrenofviryel/phionyx-research/blob/main/CHANGELOG.md
- Reasoned Governance Envelope v0.2 RFC: https://github.com/halvrenofviryel/phionyx-mcp-server/blob/main/specs/rge_v0_2/rge_v0_2.md
- Bump policy: https://github.com/halvrenofviryel/phionyx-research/blob/main/docs/conventions/otel_semantic_bump_policy.md
