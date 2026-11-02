#!/usr/bin/env bash
# Reproduce only this local experiment. No git mutation or external write.
set -euo pipefail
EXPERIMENT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
PROBE_VENV="${PROBE_VENV:-$EXPERIMENT_DIR/.venv}"
cd "$EXPERIMENT_DIR/../../../.."
export PYTHONDONTWRITEBYTECODE=1
if [ ! -x "$PROBE_VENV/bin/python" ]; then
    python3 -m venv "$PROBE_VENV"
fi
if [ -d "$EXPERIMENT_DIR/.downloads" ]; then
    "$PROBE_VENV/bin/python" -m pip install --disable-pip-version-check --no-cache-dir \
        --no-index --find-links "$EXPERIMENT_DIR/.downloads" --require-hashes \
        -r "$EXPERIMENT_DIR/requirements.lock"
else
    "$PROBE_VENV/bin/python" -m pip install --disable-pip-version-check --no-cache-dir \
        --index-url https://pypi.org/simple --require-hashes \
        -r "$EXPERIMENT_DIR/requirements.lock"
fi
"$PROBE_VENV/bin/python" -m pip --no-cache-dir check
"$PROBE_VENV/bin/python" -m unittest discover -s "$EXPERIMENT_DIR/tests" -v
"$PROBE_VENV/bin/python" "$EXPERIMENT_DIR/probe.py" --output "$EXPERIMENT_DIR/.reproduced/current"
"$PROBE_VENV/bin/python" - "$EXPERIMENT_DIR" <<'PY'
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
expected = root / "cases"
actual = root / ".reproduced/current"
expected_files = {p.relative_to(expected) for p in expected.rglob("*") if p.is_file()}
actual_files = {p.relative_to(actual) for p in actual.rglob("*") if p.is_file()}
if expected_files != actual_files:
    raise SystemExit("FAIL: artifact file sets differ")
for path in sorted(expected_files):
    if (expected / path).read_bytes() != (actual / path).read_bytes():
        raise SystemExit(f"FAIL: artifact differs: {path}")
print(f"PASS: {len(expected_files)} recorded artifacts reproduced byte-for-byte")
print("9 scenarios: 6 PARTIALLY_EVALUATED, 3 NOT_EVALUATED; runtime executions observed: 0")
PY
