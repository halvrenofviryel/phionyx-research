# Phionyx Examples

Practical examples demonstrating the Phionyx Core SDK.

## Notebooks

| Notebook | Description | Run time |
|----------|-------------|----------|
| [phionyx_quickstart.ipynb](notebooks/phionyx_quickstart.ipynb) | "Hello Phionyx" — state vector, Φ, determinism check, kill switch, 46-block pipeline | <30 s |
| [01_determinism_and_physics.ipynb](notebooks/01_determinism_and_physics.ipynb) | `EchoState2`, `calculate_phi_v2_1`, 1000-run determinism proof, valence × arousal Φ heatmap, side-by-side with a noisy alternative | ~30 s |
| [02_kill_switch_in_action.ipynb](notebooks/02_kill_switch_in_action.ipynb) | `KillSwitch` with the four documented triggers + NaN fail-closed guard, tamper-evident event log | ~5 s |
| [03_pipeline_blocks_and_audit.ipynb](notebooks/03_pipeline_blocks_and_audit.ipynb) | Canonical 46-block pipeline (v3.8.0), custom `PipelineBlock` subclass, 100-run determinism check | ~5 s |
| [04_governed_envelope.ipynb](notebooks/04_governed_envelope.ipynb) | Build a governed-response envelope end-to-end (input safety → state → Φ → kill switch → narrative → tamper-evident hash). Produces [`envelopes/governed_response.json`](envelopes/governed_response.json) | <5 s |

Every notebook runs end-to-end on a fresh `pip install phionyx-core`. No LLM, no API key.

## Integration Examples

| Example | Description | Status |
|---------|-------------|--------|
| [FastAPI](fastapi/) | HTTP `/govern` endpoint over the governance pipeline | Planned |
| [`envelopes/governed_response.json`](envelopes/governed_response.json) | Canonical governed-response envelope sample (output of notebook 04) | Reference |
| [`profiles/`](profiles/) | Three runnable profile YAMLs — `education`, `creative_writing`, `customer_support`. All validate against `phionyx_core.Profile` | Reference |
| [`comparison/`](comparison/) | Phionyx as a governance layer on top of LangChain / LlamaIndex / any orchestrator (`with_orchestrator.py` + role-distinction note) | Reference |

## Running Notebooks

```bash
pip install -e .
pip install jupyter matplotlib
jupyter notebook examples/notebooks/
```

Smoke test that all three demos execute cleanly:

```bash
for nb in examples/notebooks/0*.ipynb; do
  jupyter nbconvert --to notebook --execute --inplace "$nb"
done
```

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines. Examples are a great way to get started — check the [open issues](https://github.com/halvrenofviryel/phionyx-research/issues?q=label%3A%22good+first+issue%22) for ideas.
