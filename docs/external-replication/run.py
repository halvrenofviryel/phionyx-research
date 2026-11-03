#!/usr/bin/env python3
"""Offline self-service replay of two separate frozen AIREP source lanes.

New K5 orchestration code: repository AGPL-3.0 license. Bundled components retain
their own licenses. This runner never submits results or labels a run external.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import signal
import subprocess
import sys
import tarfile
import time

PACKAGE = Path(__file__).resolve().parent


class ReproductionError(RuntimeError):
    """An input, environment, command or expected-observation check failed."""


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def utc():
    return datetime.now(timezone.utc).isoformat()


def verify_package(package):
    """Check every declared file, including this runner, before executing code."""
    manifest = load(package / 'MANIFEST.json')
    seen = set()
    for row in manifest['files']:
        relative = Path(row['path'])
        if relative.is_absolute() or '..' in relative.parts or str(relative) in seen:
            raise ReproductionError('Unsafe or duplicate package path')
        seen.add(str(relative))
        path = package / relative
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(package.resolve()):
            raise ReproductionError('Missing/unsafe package file: ' + str(relative))
        raw = path.read_bytes()
        if len(raw) != row['byte_length'] or sha(raw) != row['sha256']:
            raise ReproductionError('Package hash mismatch: ' + str(relative))
    for required in ('run.py', 'protocol-pins.json', 'DEPENDENCY_ARTIFACTS.json',
                     'bundles/airep-sources.bundle', 'bundles/langgraph-wheelhouse.tar.gz'):
        if required not in seen:
            raise ReproductionError('Required package member not pinned: ' + required)
    return manifest


def unpack_wheels(archive, dest, records):
    """Extract only the exact, hash-pinned regular wheel members."""
    expected = {row['filename']: row for row in records}
    dest.mkdir(parents=True, exist_ok=False)
    with tarfile.open(archive) as source:
        members = source.getmembers()
        if len(members) != len(expected) or {m.name for m in members} != set(expected):
            raise ReproductionError('Wheel archive inventory mismatch')
        for member in members:
            if not member.isfile() or Path(member.name).name != member.name:
                raise ReproductionError('Unsafe wheel archive member')
            raw = source.extractfile(member).read()
            row = expected[member.name]
            if sha(raw) != row['sha256'] or len(raw) != row['byte_length']:
                raise ReproductionError('Wheel archive content mismatch: ' + member.name)
            (dest / member.name).write_bytes(raw)


class Runner:
    """Commands receive an isolated HOME and an explicit noncredential environment."""
    def __init__(self, package, out):
        self.package, self.out = package.resolve(), out.resolve()
        self.out.mkdir(parents=True, exist_ok=False)
        self.work = self.out / 'work'
        for name in ('home', 'tmp'):
            (self.work / name).mkdir(parents=True)
        self.env = {'PATH': str(Path(sys.executable).parent) + os.pathsep + os.environ.get('PATH', os.defpath),
                    'HOME': str(self.work / 'home'), 'TMPDIR': str(self.work / 'tmp'),
                    'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8',
                    'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONNOUSERSITE': '1',
                    'PIP_NO_INDEX': '1', 'PIP_CONFIG_FILE': os.devnull,
                    'PIP_DISABLE_PIP_VERSION_CHECK': '1', 'PIP_NO_CACHE_DIR': '1',
                    'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull,
                    'GIT_TERMINAL_PROMPT': '0'}
        self.record = {'schema': 'k5-local-run-v1', 'started_utc': utc(),
                       'classification': 'AUTHOR_SIDE_REFERENCE',
                       'external_evidence': 'NOT_EVALUATED', 'external_participation': False,
                       'publication': 'NOT_PERFORMED', 'commands': [], 'experiments': {},
                       'python': sys.version, 'platform': platform.platform(),
                       'package_manifest_sha256': sha((self.package / 'MANIFEST.json').read_bytes()),
                       'source_pins': load(self.package / 'protocol-pins.json'),
                       'environment': 'Explicit PATH/locale plus fresh HOME/TMPDIR; no inherited credentials, proxies, user Git/pip configuration or user site-packages'}

    def command(self, name, argv, cwd=None, *, timeout=300, tests=None):
        cwd = Path(cwd or self.work)
        entry = {'name': name, 'argv': [str(x) for x in argv], 'cwd': str(cwd), 'timeout_seconds': timeout}
        start = time.monotonic()
        output, error, code = b'', b'', -1
        try:
            with subprocess.Popen(entry['argv'], cwd=cwd, env=self.env, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, start_new_session=True) as process:
                try:
                    output, error = process.communicate(timeout=timeout)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    output, error = process.communicate()
                    entry['timed_out'] = True
                code = process.returncode
        except OSError as exc:
            error = str(exc).encode()
        entry['seconds'] = round(time.monotonic() - start, 3)
        entry['exit_code'] = code
        for stream, raw in [('stdout', output), ('stderr', error)]:
            path = self.out / 'logs' / f'{len(self.record["commands"])+1:02d}-{name}.{stream}'
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(raw)
            entry[stream] = {'path': str(path.relative_to(self.out)), 'sha256': sha(raw)}
        self.record['commands'].append(entry)
        if code or entry.get('timed_out'):
            raise ReproductionError(f'{name} failed; inspect captured stdout/stderr')
        if tests is not None:
            text = (output + error).decode('utf-8', errors='replace')
            matched = re.search(r'Ran (\d+) tests?', text)
            if not matched or int(matched[1]) != tests or re.search(r'OK \(.*skipped=', text):
                raise ReproductionError(f'{name}: expected {tests} executed tests without skips')
            entry['tests_executed'] = tests
        print(name + ': completed', flush=True)
        return output

    def checkout(self, lane):
        pins = self.record['source_pins']
        source = self.work / ('airep-' + lane)
        self.command(lane + '-clone', ['git', 'clone', '--no-hardlinks', '--branch', lane + '-source',
                                      self.package / 'bundles/airep-sources.bundle', source])
        actual = self.command(lane + '-source-pin', ['git', 'rev-parse', 'HEAD'], source).decode().strip()
        if actual != pins[lane]['source_commit']:
            raise ReproductionError('Source commit mismatch for ' + lane)
        return source

    def k2(self):
        source = self.checkout('k2')
        folder = 'interop/same-version/v0.2.0-beta.1'
        self.command('k2-harness-tests', [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', folder,
                                      '-p', 'test_*.py', '-v'], source, tests=28)
        result = self.out / 'results/k2'
        result.parent.mkdir(exist_ok=True)
        self.command('k2-measurement', [sys.executable, '-B', folder + '/harness.py', 'run', '--out', result], source)
        record = load(result / 'run_record.json')
        if not (record['status'] == 'LOCAL_CHECKS_COMPLETED' and record['reference_expectation_met']
                and record['node_reference_parity']['agrees']
                and all(r['assertion_met'] for r in record['negative_controls'])
                and record['external_result'] == 'EXTERNAL_RESULT_NOT_SUPPLIED'):
            raise ReproductionError('K2 bounded reference expectations did not hold')
        self.record['experiments']['k2'] = {
            'status': 'LOCAL_CHECKS_COMPLETED', 'test_count': 28,
            'reference_summary': record['reference_to_reference']['reconcile']['result']['summary'],
            'external_roles': 'NOT_EVALUATED', 'external_result': record['external_result'],
            'run_record': 'results/k2/run_record.json', 'same_first_party_family': True}

    def k3(self):
        source = self.checkout('k3')
        deps = load(self.package / 'DEPENDENCY_ARTIFACTS.json')
        wheels = self.work / 'wheels'
        unpack_wheels(self.package / 'bundles/langgraph-wheelhouse.tar.gz', wheels, deps['k3_runtime'])
        lock = source / 'integrations/langgraph/requirements.lock'
        if sha(lock.read_bytes()) != self.record['source_pins']['k3']['runtime_lock_sha256']:
            raise ReproductionError('K3 dependency lock changed')
        self.command('k3-create-venv', [sys.executable, '-m', 'venv', '.venv'], source)
        python = source / '.venv/bin/python'
        self.command('k3-offline-install', [python, '-m', 'pip', 'install', '--no-index', '--find-links', wheels,
                                          '--require-hashes', '-r', lock], source)
        self.command('k3-runtime-tests', [python, '-B', '-m', 'unittest', 'discover', '-s',
                                         'integrations/langgraph/tests', '-v'], source, tests=13)
        result = self.out / 'results/k3'
        result.parent.mkdir(exist_ok=True)
        self.command('k3-runtime-measurement', [python, '-B', 'integrations/langgraph/run.py', '--out', result], source)
        record = load(result / 'run_record.json')
        observed = {r['scenario']: r['observed_steps'] for r in record['scenarios']}
        expected = {'normal': 4, 'stop-before-start': 0, 'stop-during-action': 1,
                    'receiver-unreachable': 4, 'receiver-ignores-stop': 4, 'effect-unobserved': None}
        if observed != expected or any(r['cleanup']['worker_alive'] or r['cleanup']['forced_termination'] for r in record['scenarios']):
            raise ReproductionError('K3 bounded runtime observations/cleanup differ')
        case = result / 'stop-during-action'
        fresh = self.command('D-explain-check', [python, '-B', '-m', 'tools.airep_v02', 'explain', '--input',
                             case / 'lifecycle.json', '--bindings', case / 'bindings.json', '--revocation',
                             case / 'revocation.json', '--json'], source)
        if json.loads(fresh) != load(case / 'explain.json'):
            raise ReproductionError('D CLI view differs from saved runtime view')
        for scenario in observed:
            view = load(result / scenario / 'explain.json')
            for claim in ('enforcement_observed', 'relying_party_claim_support'):
                row = next(r for r in view['claim_matrix'] if r['claim'] == claim)
                if row['source_status'] is not None or row['explanatory_status'] != 'NOT_EVALUATED':
                    raise ReproductionError('An unavailable native claim was upgraded')
        self.record['experiments']['k3'] = {'status': 'LOCAL_CHECKS_COMPLETED', 'test_count': 13,
            'observed_steps': observed, 'D_cli_equals_saved_view': True, 'enforcement_native_predicate': 'NOT_EVALUATED',
            'external_roles': 'NOT_EVALUATED', 'run_record': 'results/k3/run_record.json',
            'scope': 'Real local LangGraph cooperative pause; same-executor observations; no LLM/preemptive cancellation/independent witness'}

    def finish(self):
        self.record['finished_utc'] = utc()
        self.record['output_files'] = [
            {'path': str(path.relative_to(self.out)), 'byte_length': path.stat().st_size, 'sha256': sha(path.read_bytes())}
            for directory in ('logs', 'results') for path in sorted((self.out / directory).rglob('*'))
            if path.is_file() and '__pycache__' not in path.parts]
        save(self.out / 'run_record.json', self.record)
        (self.out / 'run_record.sha256').write_text(sha((self.out / 'run_record.json').read_bytes()) + '  run_record.json\n')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--experiment', choices=('k2', 'k3', 'all'), default='all')
    parser.add_argument('--out', type=Path)
    parser.add_argument('--check-package', action='store_true')
    args = parser.parse_args(argv)
    try:
        manifest = verify_package(PACKAGE)
        if args.check_package:
            print('PACKAGE_HASHES_VERIFIED files=' + str(len(manifest['files'])))
            return 0
        if args.out is None:
            parser.error('--out is required when running experiments')
        if platform.system() != 'Linux' or platform.machine() != 'x86_64' or sys.version_info[:2] != (3, 12):
            raise ReproductionError('Supported axis: Linux x86_64, CPython 3.12 with venv/ensurepip, Node 20.19.6 and Git')
        runner = Runner(PACKAGE, args.out)
        try:
            runner.record['node'] = runner.command('node-version', ['node', '--version']).decode().strip()
            runner.record['git'] = runner.command('git-version', ['git', '--version']).decode().strip()
            if runner.record['node'] != 'v20.19.6':
                raise ReproductionError('Expected Node v20.19.6; install that public runtime before replay')
            for lane in ('k2', 'k3') if args.experiment == 'all' else (args.experiment,):
                getattr(runner, lane)()
            runner.record['status'] = 'LOCAL_PACKAGE_CHECKS_COMPLETED'
        except (ReproductionError, ValueError, KeyError, OSError) as exc:
            runner.record['status'] = 'FAILED'
            runner.record['error'] = str(exc)
        finally:
            runner.finish()
        print(runner.record['status'] + '; external evidence remains NOT_EVALUATED')
        return int(runner.record['status'] == 'FAILED')
    except (ReproductionError, ValueError, KeyError, OSError) as exc:
        print('FAILED: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
