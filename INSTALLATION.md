# Installation

## Requirements

- Python 3.10 or higher
- pip ≥ 22

## Install from source (current canonical path)

```bash
git clone https://github.com/halvrenofviryel/phionyx-research.git
cd phionyx-research
pip install -e .
```

After install, a one-line smoke test:

```python
from phionyx_core import EchoState2, calculate_phi_v2_1
state = EchoState2(A=0.5, V=0.3, H=0.4)
phi = calculate_phi_v2_1(
    valence=state.V, arousal=state.A, amplitude=5.0, time_delta=0.1,
    gamma=0.15, stability=state.stability, entropy=state.H,
    w_c=0.6, w_p=0.4,
)
print(phi["phi"])  # deterministic, reproducible
```

## Install from PyPI

Coming soon. The package metadata, build, and `twine check` are clean,
but the upload is gated on a TestPyPI verification run. Track
[`#packaging/pypi-readiness`](https://github.com/halvrenofviryel/phionyx-research/pulls?q=label%3Apackaging)
for status. Once uploaded the install will be:

```bash
pip install phionyx-core
```

## Required dependencies

These are pulled automatically by `pip install`:

- `pydantic >= 2.0`
- `typing-extensions >= 4.0`
- `PyYAML >= 6.0` — required because `phionyx_core.physics.profiles`
  and `phionyx_core.cep.cep_config` parse YAML at import time
- `numpy >= 1.24` — required because `phionyx_core.state.ukf_*` imports
  numpy at module top level

## Optional extras

```bash
pip install -e ".[graph]"        # networkx — CausalGraph, graph_engine
pip install -e ".[telemetry]"    # OpenTelemetry SDK + API
pip install -e ".[postgres]"     # asyncpg adapter
pip install -e ".[supabase]"     # supabase adapter
pip install -e ".[dev]"          # pytest, ruff, mypy — for contributing
pip install -e ".[all]"          # graph + telemetry (production adapters)
```

## Run the tests

```bash
pip install -e ".[dev]"
pytest tests/core -q
```

A clean clone should produce **1013 passed, 5 skipped** in `tests/core`
(roughly two seconds on a recent laptop). Other test directories
(`tests/contract`, `tests/benchmarks`) are also runnable but require
some extras.

## Run the demo notebooks

```bash
pip install jupyter matplotlib
jupyter notebook examples/notebooks/
```

See [`examples/notebooks/README.md`](examples/notebooks/README.md) for
what each notebook demonstrates.

## Troubleshooting

**`ModuleNotFoundError: No module named 'phionyx_core'`**

You're not in the venv where you ran `pip install`. Activate it:

```bash
source venv/bin/activate
which python  # should point inside the venv
```

**`ImportError: cannot import name 'EchoOrchestrator'`**

Import from the package root, not a submodule:

```python
from phionyx_core import EchoOrchestrator  # correct
# from phionyx_core.orchestrator import EchoOrchestrator  # internal
```

**Postgres / Supabase connection errors**

Install the matching extra:

```bash
pip install -e ".[postgres]"  # asyncpg
pip install -e ".[supabase]"
```

## Environment variables

Optional, all unset by default:

```bash
export PHIONYX_LOG_LEVEL=INFO
export PHIONYX_OPENTELEMETRY_ENABLED=true
```
