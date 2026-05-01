"""
Integration test: install ``phionyx-core`` from PyPI in a *fresh* venv
and exercise the public API.

Why this exists separate from ``tests/core``:

  Editable installs (``pip install -e .``) hide a class of packaging
  bug — missing wheel files, MANIFEST drift, declared-but-unshipped
  modules, broken module top-level imports under default deps. The
  unit suite passes against the working tree, so it can't catch these.
  This test goes through the same install path a real user uses
  (``pip install phionyx-core``) and runs the public API in the
  resulting venv.

  CI does not run this by default — it requires network and is too
  expensive for every PR. Opt in with:

      pytest tests/integration -m integration

  Or, as part of the CI surface, set the env var ``PHIONYX_RUN_PYPI``
  to a non-empty value.

Override the install target at runtime:

  PHIONYX_INSTALL_TARGET="phionyx-core==0.2.1" pytest tests/integration -m integration
  PHIONYX_INSTALL_TARGET="phionyx-core" \
      PHIONYX_PIP_INDEX_ARGS="--index-url https://test.pypi.org/simple/ \
                              --extra-index-url https://pypi.org/simple/" \
      pytest tests/integration -m integration
"""
from __future__ import annotations

import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


pytestmark = pytest.mark.integration


def test_pypi_install_round_trip(tmp_path: Path) -> None:
    target = os.environ.get("PHIONYX_INSTALL_TARGET", "phionyx-core")
    pip_index_args = shlex.split(os.environ.get("PHIONYX_PIP_INDEX_ARGS", ""))

    venv_dir = tmp_path / "venv"
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
    pip = venv_dir / "bin" / "pip"
    py = venv_dir / "bin" / "python"
    if not pip.exists():        # Windows fallback
        pip = venv_dir / "Scripts" / "pip.exe"
        py = venv_dir / "Scripts" / "python.exe"

    subprocess.run(
        [str(pip), "install", "--quiet", "--upgrade", "pip"],
        check=True,
    )
    subprocess.run(
        [str(pip), "install", "--quiet", *pip_index_args, target],
        check=True,
    )

    # Smoke flow inside the freshly-installed venv. Each assert covers
    # a different surface so a single failed assert points at the
    # actual broken thing rather than a generic ImportError.
    smoke = (
        "import phionyx_core;"
        "assert phionyx_core.__version__, 'no version';"
        "from phionyx_core import EchoState2, calculate_phi_v2_1;"
        "from phionyx_core.governance.kill_switch import KillSwitch;"
        "from phionyx_core.contracts.telemetry import get_canonical_blocks;"
        "assert len(get_canonical_blocks()) == 46, 'block count drift';"
        "s = EchoState2(A=0.5, V=0.3, H=0.4);"
        "r = calculate_phi_v2_1(valence=s.V, arousal=s.A, amplitude=5.0, "
        "time_delta=0.1, gamma=0.15, stability=s.stability, entropy=s.H, "
        "w_c=0.6, w_p=0.4);"
        "assert r['phi'] > 0, 'phi must be positive';"
        "assert KillSwitch().state.value == 'armed', 'kill switch should arm by default';"
        "print('pypi-install round-trip: ok', phionyx_core.__version__)"
    )

    result = subprocess.run(
        [str(py), "-c", smoke],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.fail(
            "smoke failed in fresh PyPI-install venv\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    assert "pypi-install round-trip: ok" in result.stdout
