"""K5 package boundary tests; no network, runtime/provider, or external claim."""
import hashlib
import io
import json
import os
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

import run


class PackageTests(unittest.TestCase):
    def test_real_package_hashes(self):
        self.assertGreater(len(run.verify_package(run.PACKAGE)['files']), 60)

    def test_external_template_is_blank_and_role_names_are_documented(self):
        template = run.load(run.PACKAGE / 'EXTERNAL_RUN_SUBMISSION_TEMPLATE.json')
        checklist = (run.PACKAGE / 'role-and-independence-checklist.md').read_text()
        self.assertIsNone(template['role_requested'])
        self.assertEqual(template['review_decision']['classification'], 'NOT_EVALUATED')
        self.assertFalse(template['public_permissions']['permission_to_cite_identity'])
        self.assertFalse(template['public_permissions']['permission_to_publish_artifacts'])
        for role in template['role_values']:
            self.assertIn('| ' + role + ' |', checklist)

    def test_corrupt_source_bundle_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            p = root / 'bundles/airep-sources.bundle'; p.parent.mkdir(); p.write_bytes(b'altered')
            run.save(root / 'MANIFEST.json', {'files': [{'path': 'bundles/airep-sources.bundle',
                        'sha256': hashlib.sha256(b'original').hexdigest(), 'byte_length': 8}]})
            with self.assertRaisesRegex(run.ReproductionError, 'hash mismatch'):
                run.verify_package(root)

    def test_manifest_traversal_and_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for path in ('../outside', '/absolute'):
                run.save(root / 'MANIFEST.json', {'files': [{'path': path}]})
                with self.assertRaises(run.ReproductionError):
                    run.verify_package(root)
            (root / 'link').symlink_to('/etc/passwd')
            run.save(root / 'MANIFEST.json', {'files': [{'path': 'link'}]})
            with self.assertRaises(run.ReproductionError):
                run.verify_package(root)

    def test_wheel_archive_member_and_bytes_checked(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / 'wheels.tar'
            with tarfile.open(archive, 'w') as out:
                member = tarfile.TarInfo('dep.whl'); member.size = 3
                out.addfile(member, io.BytesIO(b'bad'))
            rows = [{'filename': 'dep.whl', 'byte_length': 4, 'sha256': run.sha(b'good')}]
            with self.assertRaisesRegex(run.ReproductionError, 'content mismatch'):
                run.unpack_wheels(archive, root / 'extracted', rows)

    def test_output_refuses_existing_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(FileExistsError):
                run.Runner(run.PACKAGE, Path(temp))

    def test_child_environment_does_not_inherit_credentials_or_proxy(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {'K5_TEST_SECRET': 'invented', 'HTTPS_PROXY': 'invented'}):
            runner = run.Runner(run.PACKAGE, Path(temp) / 'new')
            self.assertNotIn('K5_TEST_SECRET', runner.env)
            self.assertNotIn('HTTPS_PROXY', runner.env)
            self.assertEqual(runner.env['GIT_CONFIG_GLOBAL'], os.devnull)
            self.assertEqual(runner.record['external_evidence'], 'NOT_EVALUATED')

    def test_failed_command_preserved_not_promoted(self):
        with tempfile.TemporaryDirectory() as temp:
            runner = run.Runner(run.PACKAGE, Path(temp) / 'new')
            with self.assertRaises(run.ReproductionError):
                runner.command('negative', [run.sys.executable, '-c', 'print("claimed success"); raise SystemExit(7)'])
            self.assertEqual(runner.record['commands'][0]['exit_code'], 7)


if __name__ == '__main__':
    unittest.main()
