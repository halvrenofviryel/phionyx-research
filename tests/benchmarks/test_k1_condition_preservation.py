"""Run the frozen and versioned K1 checks in the existing benchmark CI job."""
import json
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
FROZEN = ROOT / 'experiments/ietf/acder02-control-benchmark'
REPAIR = ROOT / 'experiments/ietf/acder02-condition-preservation-v2'


def checked(cwd, *arguments, env=None):
    result = subprocess.run([sys.executable, '-B', *arguments], cwd=cwd,
        env=env, capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout + result.stderr


def test_frozen_packet_and_original_44_tests():
    checked(ROOT, str(FROZEN / 'reproduce.py'), '--check-only')
    log = checked(FROZEN, '-m', 'unittest', 'discover', '-s', 'tests', '-v',
                  env=dict(os.environ, K1_TEST_INCLUDE_HOLDOUT='1', PYTHONDONTWRITEBYTECODE='1'))
    assert 'Ran 44 tests' in log


def test_versioned_condition_repairs():
    log = checked(REPAIR, '-m', 'unittest', '-v', 'test_conditions.py')
    assert 'Ran 10 tests' in log


def test_known_case_comparison_preserves_states_and_qualifications(tmp_path):
    out = tmp_path / 'comparison'
    checked(ROOT, str(REPAIR / 'report.py'), '--out', str(out))
    report = json.loads((out / 'comparison.json').read_text())
    assert report['case_count'] == 24
    assert report['claim_count'] == 107
    assert report['state_or_qualification_changes'] == 0
    assert len(report['condition_changes']) == 9
