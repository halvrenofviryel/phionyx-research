# Phionyx Examples

Practical examples demonstrating the Phionyx Core SDK.

## Notebooks

| Notebook | Description |
|----------|-------------|
| [phionyx_quickstart.ipynb](notebooks/phionyx_quickstart.ipynb) | Core concepts: state vector, Phi, entropy, pipeline, safety gates |
| [01_determinism_and_physics.ipynb](notebooks/01_determinism_and_physics.ipynb) | `EchoState2`, `calculate_phi_v2_1`, 1000-run determinism proof, valence × arousal heatmap, side-by-side with a noisy alternative |
| [02_kill_switch_in_action.ipynb](notebooks/02_kill_switch_in_action.ipynb) | `KillSwitch` with the four documented triggers (ethics, T_meta, sustained drift, NaN fail-closed) and the tamper-evident event log |
| [03_pipeline_blocks_and_audit.ipynb](notebooks/03_pipeline_blocks_and_audit.ipynb) | Canonical 46-block pipeline (v3.8.0), a custom `PipelineBlock` subclass, 100-run determinism check |

Each of the three demo notebooks runs end-to-end in seconds and embeds verified outputs.

## Integration Examples

| Example | Description | Status |
|---------|-------------|--------|
| [FastAPI](fastapi/) | HTTP endpoint wrapping the governance pipeline | Planned |

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
