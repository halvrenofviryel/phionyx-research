"""Offline one-command integrity check, deterministic replay and isolated pytest run."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    """Hash exact file bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    """Verify the frozen inputs before evaluating and comparing deterministic output."""
    expected_record_hash = (ROOT / "run_record.sha256").read_text().split()[0]
    if sha256(ROOT / "run_record.json") != expected_record_hash:
        raise SystemExit("Frozen run_record.json SHA-256 mismatch")
    record = json.loads((ROOT / "run_record.json").read_text())
    for name, expected in record["frozen_files_sha256"].items():
        if sha256(ROOT / name) != expected:
            raise SystemExit(f"Frozen file SHA-256 mismatch: {name}")
    commitment = json.loads((ROOT / "provenance/pre_run_commitment.json").read_text())
    for name, expected in commitment["inputs_sha256"].items():
        if sha256(ROOT / name) != expected:
            raise SystemExit(f"Pre-run commitment mismatch: {name}")
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    replay = subprocess.run(
        [sys.executable, str(ROOT / "src/run.py")],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        check=True,
    )
    if replay.stdout != (ROOT / "results.json").read_bytes():
        raise SystemExit("Replay differs from frozen results.json")
    with tempfile.TemporaryDirectory(prefix="agentproto-replay-") as tmp:
        tests = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-c",
                str(ROOT / "pytest.ini"),
                f"--confcutdir={ROOT}",
                str(ROOT / "tests"),
                "-q",
                "-o",
                f"cache_dir={tmp}/pytest-cache",
            ],
            cwd=ROOT,
            env=environment,
        )
    if tests.returncode:
        return tests.returncode
    result = json.loads(replay.stdout)
    print(
        json.dumps(
            {
                "integrity": "MATCH",
                "replay": "BYTE_IDENTICAL",
                "vectors": result["vector_count"],
                "outcomes": result["outcome_counts"],
                "run_record_sha256": expected_record_hash,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
