#!/usr/bin/env python3
"""Optional Linux/bubblewrap validation of the standalone packet, with no network.

The experiment runner itself requires no bubblewrap. This additional validation
mounts only /usr, one selected Node binary, the packet, and fresh scratch storage.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def inside():
    hidden = ['/home', '/root', '/run', '/var', '/etc']
    probe = {
        'classification': 'AUTHOR_SIDE_REFERENCE', 'external_evidence': 'NOT_EVALUATED',
        'uid': os.getuid(), 'pid': os.getpid(), 'cwd': os.getcwd(),
        'namespaces': {name: os.readlink('/proc/self/ns/' + name) for name in ('mnt', 'pid', 'user', 'net')},
        'environment': dict(os.environ),
        'hidden_host_roots': {name: not Path(name).exists() for name in hidden},
        'proc_pids': sorted(p.name for p in Path('/proc').iterdir() if p.name.isdecimal()),
        'network_devices': Path('/proc/net/dev').read_text(),
        'mountinfo': Path('/proc/self/mountinfo').read_text(),
    }
    write(Path('/work/sandbox-probe.json'), probe)
    if not all(probe['hidden_host_roots'].values()):
        raise RuntimeError('Unexpected host root exposed')
    commands = [
        ['/usr/bin/python3', '-B', '-m', 'unittest', 'discover', '-s', '/packet', '-p', 'test_runner.py', '-v'],
        ['/usr/bin/python3', '-B', '/packet/run.py', '--experiment', 'all', '--out', '/work/result'],
    ]
    records = []
    for index, command in enumerate(commands):
        result = subprocess.run(command, capture_output=True, timeout=900)
        records.append({'argv': command, 'exit_code': result.returncode})
        for stream in ('stdout', 'stderr'):
            raw = getattr(result, stream)
            name = f'{index + 1:02d}-validation.{stream}'
            Path('/work', name).write_bytes(raw)
            records[-1][stream] = {'path': name, 'sha256': hashlib.sha256(raw).hexdigest()}
            print(raw.decode(errors='replace'), end='', flush=True)
        write(Path('/work/validation-commands.json'), records)
        if result.returncode:
            return result.returncode
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node', type=Path, help='Caller-provided Node 20.19.6 binary; defaults to node on PATH')
    parser.add_argument('--out', type=Path, help='New scratch directory, outside the packet')
    parser.add_argument('--inside', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.inside:
        return inside()
    package = Path(__file__).resolve().parent
    node = (args.node or Path(shutil.which('node') or '/missing-node')).resolve()
    if not node.is_file() or subprocess.check_output([node, '--version'], text=True).strip() != 'v20.19.6':
        parser.error('Provide an existing Node v20.19.6 binary with --node')
    if args.out is None:
        parser.error('--out is required')
    out = args.out.resolve()
    if out.is_relative_to(package):
        parser.error('Scratch output must be outside the read-only packet')
    out.mkdir(parents=True, exist_ok=False)
    command = ['bwrap', '--die-with-parent', '--new-session', '--unshare-all', '--clearenv',
               '--ro-bind', '/usr', '/usr', '--symlink', 'usr/bin', '/bin',
               '--symlink', 'usr/lib', '/lib', '--symlink', 'usr/lib64', '/lib64',
               '--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp',
               '--ro-bind', str(node), '/usr/bin/node',
               '--ro-bind', str(package), '/packet', '--bind', str(out), '/work',
               '--setenv', 'PATH', '/usr/bin:/bin', '--setenv', 'HOME', '/work/home',
               '--setenv', 'LANG', 'C.UTF-8', '--setenv', 'PYTHONDONTWRITEBYTECODE', '1',
               '--chdir', '/packet', '/usr/bin/python3', '-B', '/packet/validate_offline.py', '--inside']
    record = {'schema': 'k5-clean-sandbox-validation-v1', 'command': command,
              'package_manifest_sha256': hashlib.sha256((package / 'MANIFEST.json').read_bytes()).hexdigest(),
              'host_namespaces': {name: os.readlink('/proc/self/ns/' + name) for name in ('mnt', 'pid', 'user', 'net')},
              'classification': 'AUTHOR_SIDE_REFERENCE', 'external_evidence': 'NOT_EVALUATED',
              'note': 'Host paths in mount arguments are provenance, not replay inputs. No HOME/history/auth/apps/private repository mount; only package source bytes and system runtime.'}
    write(out / 'sandbox-command.json', record)
    result = subprocess.run(command, capture_output=True, timeout=1200, env={'PATH': '/usr/bin:/bin'})
    for stream in ('stdout', 'stderr'):
        raw = getattr(result, stream)
        (out / ('sandbox.' + stream)).write_bytes(raw)
        print(raw.decode(errors='replace'), end='', flush=True)
    record['exit_code'] = result.returncode
    probe = out / 'sandbox-probe.json'
    if probe.exists():
        child = json.loads(probe.read_text())
        record['namespace_separation'] = {name: value != child['namespaces'][name] for name, value in record['host_namespaces'].items()}
    write(out / 'sandbox-command.json', record)
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
