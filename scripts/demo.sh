#!/usr/bin/env bash
# Phionyx — one-command local demo.
#
# Creates a fresh virtual environment, installs phionyx-core from PyPI,
# then runs a short import + Φ + KillSwitch smoke flow. The point of
# the script is that it works end-to-end on a clean machine — no
# editable install, no source checkout, no API key.
#
# Usage:
#   bash scripts/demo.sh
#
# Optional: override the install target (e.g. for TestPyPI smoke):
#   PHIONYX_INSTALL_TARGET="phionyx-core==0.2.1" bash scripts/demo.sh
#   PHIONYX_PIP_INDEX_ARGS="--index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/" \
#     PHIONYX_INSTALL_TARGET="phionyx-core" bash scripts/demo.sh

set -euo pipefail

VENV="${PHIONYX_DEMO_VENV:-/tmp/phionyx-demo-venv}"
TARGET="${PHIONYX_INSTALL_TARGET:-phionyx-core}"
PIP_ARGS="${PHIONYX_PIP_INDEX_ARGS:-}"

echo "==> creating fresh venv at ${VENV}"
rm -rf "${VENV}"
python3 -m venv "${VENV}"

echo "==> installing ${TARGET}"
# shellcheck disable=SC2086
"${VENV}/bin/pip" install --quiet --upgrade pip
# shellcheck disable=SC2086
"${VENV}/bin/pip" install --quiet ${PIP_ARGS} "${TARGET}"

echo "==> running smoke"
"${VENV}/bin/python" - <<'PY'
import phionyx_core
from phionyx_core import EchoState2, calculate_phi_v2_1
from phionyx_core.governance.kill_switch import KillSwitch
from phionyx_core.contracts.telemetry import get_canonical_blocks

print(f"phionyx_core version : {phionyx_core.__version__}")
print(f"canonical blocks     : {len(get_canonical_blocks())}")

state = EchoState2(A=0.6, V=0.3, H=0.4)
phi = calculate_phi_v2_1(
    valence=state.V, arousal=state.A, amplitude=state.A * 10.0,
    time_delta=0.1, gamma=0.15, stability=state.stability,
    entropy=state.H, w_c=0.6, w_p=0.4,
)
assert phi["phi"] > 0, "phi must be positive"

ks = KillSwitch()
result = ks.evaluate(ethics_max_risk=0.10, t_meta=0.85, drift_detected=False, turn_id=1)
assert ks.state.value == "armed"
assert result.triggered is False

print(f"phi                  : {phi['phi']:.4f}")
print(f"phi_cognitive        : {phi['phi_cognitive']:.4f}")
print(f"kill switch state    : {ks.state.value}")
print()
print("local demo: ok")
PY

echo "==> done. venv kept at ${VENV} for further inspection (delete with rm -rf ${VENV})"
