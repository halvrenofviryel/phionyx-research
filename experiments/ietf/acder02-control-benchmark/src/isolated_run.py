#!/usr/bin/env python3
"""Run frozen comparators with only evidence/profile/code mounted, no oracle."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(package, split, output):
    package = package.resolve(); output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise FileExistsError('Output must be empty; no pre-existing data may be mounted')
    prediction = output / 'predictions.json'
    if prediction.exists():
        raise FileExistsError('Use a new output directory; measurements are not overwritten')
    selected = package / 'scenarios' / split
    source_files = sorted(selected.rglob('evidence.json'))
    if not source_files: raise ValueError('No selected evidence files')
    with tempfile.TemporaryDirectory(prefix='k1-evidence-only-') as td:
        visible = Path(td) / 'input'; visible.mkdir()
        for path in source_files:
            dst = visible / path.relative_to(selected)
            dst.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(path, dst)
        cmd = ['bwrap', '--unshare-all', '--die-with-parent', '--new-session',
               '--ro-bind', '/usr', '/usr', '--symlink', 'usr/bin', '/bin',
               '--symlink', 'usr/lib', '/lib', '--symlink', 'usr/lib64', '/lib64',
               '--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp', '--dir', '/home',
               '--ro-bind', str(package / 'src' / 'evaluate.py'), '/evaluate.py',
               '--ro-bind', str(package / 'PROFILE.json'), '/profile.json',
               '--ro-bind', str(visible), '/input', '--bind', str(output), '/output',
               '--clearenv', '--setenv', 'PATH', '/usr/bin',
               '--setenv', 'PYTHONDONTWRITEBYTECODE', '1', '--chdir', '/tmp']
        probe_code = '''import json, os, pathlib
assert not pathlib.Path('/home/toygar').exists()
assert not pathlib.Path('/oracles').exists()
files=sorted(str(p) for p in pathlib.Path('/input').rglob('*') if p.is_file())
assert files and all(p.endswith('/evidence.json') for p in files)
json.dump({'visible_inputs':files,'home_entries':os.listdir('/home'),'environment':dict(os.environ),'network_namespace':os.readlink('/proc/self/ns/net'),'proc_net_dev':pathlib.Path('/proc/net/dev').read_text(),'oracle_path_absent':True,'host_home_absent':True},open('/output/boundary.json','w'),indent=2)
'''
        started = datetime.datetime.now(datetime.timezone.utc).isoformat()
        probe = subprocess.run(cmd + ['/usr/bin/python3', '-B', '-c', probe_code], capture_output=True, text=True)
        (output / 'boundary.log').write_text(probe.stdout + probe.stderr)
        if probe.returncode: raise RuntimeError('Isolation probe failed; no comparator was executed')
        invocation = cmd + ['/usr/bin/python3', '-B', '/evaluate.py', '--evidence-dir', '/input',
                            '--profile', '/profile.json', '--output', '/output/predictions.json']
        result = subprocess.run(invocation, capture_output=True, text=True)
        (output / 'evaluator.log').write_text(result.stdout + result.stderr)
        record = {'schema': 'acder-benchmark-isolated-run-v1', 'started_utc': started,
                  'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  'split': split, 'returncode': result.returncode,
                  'evidence_count': len(source_files), 'oracle_mounted': False,
                  'network': 'unshared; no external interface', 'argv': invocation,
                  'code_sha256': sha(package / 'src' / 'evaluate.py'),
                  'profile_sha256': sha(package / 'PROFILE.json'),
                  'input_hashes': [{'path': str(p.relative_to(package)), 'sha256': sha(p)} for p in source_files],
                  'predictions_sha256': sha(prediction) if prediction.exists() else None}
        (output / 'run_record.json').write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
        if result.returncode: raise RuntimeError('Comparator process failed; original output retained')
    return record


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--package', type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument('--split', choices=['development', 'holdout'], required=True)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args(); print(json.dumps(run(a.package, a.split, a.output), sort_keys=True))


if __name__ == '__main__': main()
