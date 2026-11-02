#!/usr/bin/env bash
# All writes stay in this -04 directory; the -03 environment is read-only.
set -euo pipefail
PROBE_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
OLD_PROBE="$PROBE_ROOT/../decision-receipts-03"
cd "$PROBE_ROOT/../../../.."
export PYTHONDONTWRITEBYTECODE=1
if [ "${PROBE_USE_NEW_VENV:-0}" != 1 ] && [ -x "$OLD_PROBE/.venv/bin/python" ]; then
    PROBE_PYTHON="$OLD_PROBE/.venv/bin/python"
else
    if [ ! -x "$PROBE_ROOT/.venv/bin/python" ]; then
        python3 -m venv "$PROBE_ROOT/.venv"
    fi
    PROBE_PYTHON="$PROBE_ROOT/.venv/bin/python"
    if [ -d "$OLD_PROBE/.downloads" ]; then
        "$PROBE_PYTHON" -m pip install --disable-pip-version-check --no-cache-dir \
            --no-index --find-links "$OLD_PROBE/.downloads" --require-hashes \
            -r "$PROBE_ROOT/requirements.lock"
    else
        "$PROBE_PYTHON" -m pip install --disable-pip-version-check --no-cache-dir \
            --index-url https://pypi.org/simple --require-hashes \
            -r "$PROBE_ROOT/requirements.lock"
    fi
fi
"$PROBE_PYTHON" -m pip --no-cache-dir check
"$PROBE_PYTHON" "$PROBE_ROOT/check_frozen.py"
"$PROBE_PYTHON" -m unittest discover -s "$PROBE_ROOT/tests" -v
"$PROBE_PYTHON" "$PROBE_ROOT/probe.py" --output "$PROBE_ROOT/.reproduced/current"
"$PROBE_PYTHON" - "$PROBE_ROOT" <<'PY'
import pathlib
import sys

root = pathlib.Path(sys.argv[1])

def files(directory):
    return {p.relative_to(directory): p.read_bytes() for p in directory.rglob('*') if p.is_file()}

expected = files(root / 'cases')
observed = files(root / '.reproduced/current')
if expected != observed:
    raise SystemExit('FAIL: frozen -04 artifacts differ')
print(f'PASS: {len(expected)} frozen -04 artifacts reproduced byte-for-byte without normalization')
PY
"$PROBE_PYTHON" "$PROBE_ROOT/check_frozen.py"
