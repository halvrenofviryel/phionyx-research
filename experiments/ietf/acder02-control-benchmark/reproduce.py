#!/usr/bin/env python3
"""One-command offline replay of the frozen 24-case K1 comparison."""
import argparse
import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

PACKAGE = Path(__file__).resolve().parent
sys.path.insert(0, str(PACKAGE / 'src'))
from isolated_run import run
from score import load_cases, score


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def semantic_projection(report):
    result = copy.deepcopy(report)
    # File locations change when the same immutable packet is relocated. All
    # source hashes, query scopes, oracle values, predictions and metrics remain.
    for row in result['all_rows']:
        for value in row.get('input_files', {}).values(): value.pop('path', None)
    return result


def semantic_sha(report):
    return hashlib.sha256(json.dumps(semantic_projection(report), sort_keys=True,
                                    separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def verify():
    freeze = json.loads((PACKAGE / 'LOGIC_FREEZE.json').read_text())
    for item in freeze['files']:
        if sha(PACKAGE / item['path']) != item['sha256']:
            raise ValueError('Frozen logic/profile mismatch: ' + item['path'])
    manifest_path = PACKAGE / 'PACKAGE_MANIFEST.json'
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        for item in manifest['files']:
            if sha(PACKAGE / item['path']) != item['sha256']:
                raise ValueError('Package hash mismatch: ' + item['path'])
    return freeze


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path)
    ap.add_argument('--check-only', action='store_true')
    args = ap.parse_args()
    freeze = verify()
    if args.check_only:
        print('PASS: frozen logic and package hashes'); return
    if args.out is None: ap.error('--out is required unless --check-only')
    output = args.out.resolve(); output.mkdir(parents=True, exist_ok=False)
    record = {'schema': 'acder-benchmark-reproduction-v1', 'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'python': sys.version, 'platform': platform.platform(), 'freeze': freeze,
              'scope': 'Same-owner frozen synthetic benchmark; no external implementation or operational safety claim'}
    try:
        # Evaluators run first, with neither oracle nor latent truth mounted.
        measurements = [run(PACKAGE, split, output / split) for split in ('development', 'holdout')]
        combined = {}
        for split in ('development', 'holdout'):
            for baseline, cases in json.loads((output / split / 'predictions.json').read_text()).items():
                combined.setdefault(baseline, []).extend(cases)
        (output / 'predictions.json').write_text(json.dumps(combined, indent=2, sort_keys=True) + '\n')
        scored = score(load_cases(PACKAGE / 'scenarios', PACKAGE / 'oracles'), combined)
        (output / 'score.json').write_text(json.dumps(scored, indent=2, sort_keys=True) + '\n')
        actual = semantic_sha(scored)
        expected = (PACKAGE / 'results' / 'EXPECTED_SEMANTIC_SHA256').read_text().strip()
        if actual != expected: raise ValueError('Frozen first-measurement semantic result differs')
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', K1_TEST_INCLUDE_HOLDOUT='1')
        tests = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
                               cwd=PACKAGE, env=env, text=True, capture_output=True)
        (output / 'tests.txt').write_text(tests.stdout + tests.stderr)
        if tests.returncode: raise RuntimeError('Validation suite failed; original outputs retained')
        record.update(status='REPRODUCED_FROZEN_RESULT', measurements=measurements, semantic_sha256=actual,
                      scored_claim_rows=len(scored['all_rows']), tests_returncode=tests.returncode)
    except Exception as exc:
        record.update(status='FAILED', error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        record['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        record['output_hashes'] = [{'path': str(f.relative_to(output)), 'sha256': sha(f)}
                                   for f in sorted(output.rglob('*')) if f.is_file()]
        (output / 'run_record.json').write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': record['status'], 'cases': scored['case_count'],
                      'claim_rows': len(scored['all_rows']), 'semantic_sha256': actual}))


if __name__ == '__main__': main()
