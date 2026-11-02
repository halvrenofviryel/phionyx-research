#!/usr/bin/env python3
"""Read-only packet, frozen review-patch and measured-evidence hash check."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import tarfile

HERE = Path(__file__).resolve().parent
PACKET = HERE.parents[1] / 'docs/external-replication'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    spec = importlib.util.spec_from_file_location('packet_runner', PACKET / 'run.py')
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    manifest = runner.verify_package(PACKET)
    report = read(HERE / 'run_record.json')
    assert digest((HERE / 'run_record.json').read_bytes()) == (HERE / 'run_record.sha256').read_text().split()[0]
    assert digest((PACKET / 'MANIFEST.json').read_bytes()) == report['final_packet_manifest_sha256']
    assert report['classification'] == 'AUTHOR_SIDE_REFERENCE'
    assert report['external_evidence'] == 'NOT_EVALUATED'
    for lane in ('k2', 'd-plus-k3'):
        folder = PACKET / 'review' / lane
        review = read(folder / 'review.json')
        assert digest(gzip.decompress((folder / 'complete.diff.gz').read_bytes())) == review['complete_diff_sha256']
        assert digest((folder / 'implementation.diff').read_bytes()) == review['implementation_diff_sha256']
        assert review['F_included'] is False
    total = 0
    for validation in report['validations']:
        raw = (HERE / validation['archive']).read_bytes()
        assert len(raw) == validation['archive_byte_length'] and digest(raw) == validation['archive_sha256']
        inventory_path = HERE / validation['inventory']
        assert digest(inventory_path.read_bytes()) == validation['inventory_sha256']
        inventory = {r['path']: r for r in read(inventory_path)['files']}
        with tarfile.open(HERE / validation['archive']) as source:
            members = source.getmembers()
            assert len(members) == len(inventory) and {m.name for m in members} == set(inventory)
            blobs = {}
            for item in members:
                assert item.isfile() and not Path(item.name).is_absolute() and '..' not in Path(item.name).parts
                data = source.extractfile(item).read()
                row = inventory[item.name]
                assert len(data) == row['byte_length'] and digest(data) == row['sha256']
                blobs[item.name] = data
            run = json.loads(blobs['result/run_record.json'])
            assert run['package_manifest_sha256'] == digest(blobs['input-MANIFEST.json']) == validation['packet_manifest_sha256']
            assert run['status'] == 'LOCAL_PACKAGE_CHECKS_COMPLETED'
            assert run['external_evidence'] == 'NOT_EVALUATED'
            for row in run['output_files']:
                data = blobs['result/' + row['path']]
                assert len(data) == row['byte_length'] and digest(data) == row['sha256']
            sandbox = json.loads(blobs['sandbox-command.json'])
            probe = json.loads(blobs['sandbox-probe.json'])
            assert sandbox['exit_code'] == 0 and all(sandbox['namespace_separation'].values())
            assert all(probe['hidden_host_roots'].values())
            assert run['experiments']['k2']['reference_summary']['status'] == 'INCOMPLETE'
            assert run['experiments']['k3']['D_cli_equals_saved_view'] is True
            for scenario in run['experiments']['k3']['observed_steps']:
                view = json.loads(blobs['result/results/k3/' + scenario + '/explain.json'])
                for claim in ('enforcement_observed', 'relying_party_claim_support'):
                    row = next(r for r in view['claim_matrix'] if r['claim'] == claim)
                    assert row['source_status'] is None and row['explanatory_status'] == 'NOT_EVALUATED'
        total += len(inventory)
    print(f'VERIFIED: {len(manifest["files"])} packet inputs; {len(report["validations"])} clean sandbox runs; {total} archived evidence files; K2 and D+K3 review diffs.')
    print('AUTHOR_SIDE_REFERENCE; external evidence NOT_EVALUATED; publication NOT_PERFORMED.')


if __name__ == '__main__':
    main()
