"""Exact -04 fixture pins and measured public CLI boundaries, no synthetic gate."""

import importlib.metadata
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True

from check_frozen import check  # noqa: E402
from probe import OLD, generate, inputs, payload, published_expectations, sha  # noqa: E402


class FailureVectors04(unittest.TestCase):
    """Compare the draft's author expectations to independently captured CLI runs."""

    @classmethod
    def setUpClass(cls) -> None:
        cache = ROOT / ".reproduced"
        cache.mkdir(exist_ok=True)
        cls.temp = tempfile.TemporaryDirectory(prefix="test-", dir=cache)
        cls.first = Path(cls.temp.name) / "first"
        cls.second = Path(cls.temp.name) / "second"
        for directory in (cls.first, cls.second):
            subprocess.run(
                [sys.executable, str(ROOT / "probe.py"), "--output", str(directory)],
                cwd=ROOT.parents[3],
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                check=True,
                timeout=60,
            )
        cls.report = json.loads((cls.first / "results.json").read_text())
        cls.rows = {r["id"]: r for r in cls.report["vectors"]}
        cls.envs, cls.bases, cls.compatibility = generate()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def test_source_pins(self) -> None:
        for row in json.loads((ROOT / "sources/manifest.json").read_text()):
            self.assertEqual(row["http_status"], 200)
            self.assertTrue(row["accessed_at_utc"].endswith("+00:00"))
            self.assertEqual(sha((ROOT / "sources" / row["path"]).read_bytes()), row["sha256"])
        self.assertEqual(
            sha((ROOT / "sources/draft-gruszka-audit-decision-receipts-04.txt").read_bytes()),
            "f5065d91493fb15a4995f85ffd1a71911d01bc9c8b063b1938521e1bfc05c826",
        )

    def test_prior_experiment_remains_frozen(self) -> None:
        self.assertEqual(check(), 56)

    def test_exact_dependency_and_unmodified_module_pins(self) -> None:
        for line in (ROOT / "requirements.lock").read_text().splitlines():
            if line and not line.startswith("#"):
                package, version = line.split()[0].split("==")
                self.assertEqual(importlib.metadata.version(package), version)
        dist = importlib.metadata.distribution("proofbundle")
        pin = json.loads((ROOT / "evidence/package-pin.json").read_text())
        self.assertEqual(len(pin["installed_module_hashes"]), 80)
        for name, digest in pin["installed_module_hashes"].items():
            self.assertEqual(sha(dist.locate_file(name).read_bytes()), digest, name)

    def test_all_seven_base_payloads_and_signatures_match_04(self) -> None:
        self.assertEqual(len(self.compatibility), 7)
        source = (ROOT / "sources/draft-gruszka-audit-decision-receipts-04.txt").read_text()
        for row in self.compatibility:
            self.assertTrue(row["matches_04_A3"])
            self.assertIn(f"{row['payload_bytes']} bytes, signed by", source)
            self.assertIn(row["payload_sha256"], source)
            self.assertIn(row["signature_b64"], "".join(source.split()))

    def test_eight_new_payload_hashes_and_signatures_match_04(self) -> None:
        expected = published_expectations()
        self.assertEqual(set(expected), {"F1", "F2", "F3", "F6", "F7", "F8", "F9", "F10"})
        for name, pin in expected.items():
            row = self.rows[name]
            for key in ("payload_sha256", "payload_bytes", "signature_b64"):
                self.assertEqual(row[key], pin[key], name)
            self.assertTrue(row["signature_verified"], name)

    def test_f4_f5_preserve_exact_base_envelope_bytes(self) -> None:
        for name, base in (("F4", "V1-good"), ("F5", "V2-good")):
            self.assertEqual(
                (self.first / f"fixtures/{name}.envelope.json").read_bytes(),
                (OLD / f"cases/fixtures/{base}.json").read_bytes(),
            )
            self.assertTrue(self.rows[name]["signature_verified"])

    def test_approval_reissue_and_consumption_fixtures_are_exact_bytes_only(self) -> None:
        expected = {
            "ap2.json": (231, "37ec7f3fa06f086626268a6c818ba5b5af7fd16ba292735ce964a83c42c0357c"),
            "c1.json": (139, "f13fce72c54f1872232c0339fa98b33ffe5142f72481cd31e378bc6a680b6f6a"),
        }
        for name, (length, digest) in expected.items():
            raw = inputs()[name]
            self.assertEqual(len(raw), length)
            self.assertEqual(sha(raw), digest)
        # No membership lookup is used as an enforcement result.
        self.assertEqual(self.rows["F10"]["consumption_enforcement"], "NOT_EVALUATED")

    def test_ten_cli_exits_and_crypto_results(self) -> None:
        expected = {f"F{i}": 2 if i in (1, 2, 4) else 0 for i in range(1, 11)}
        self.assertEqual(
            {k: v["measured_cli"]["exit_code"] for k, v in self.rows.items()}, expected
        )
        for name, row in self.rows.items():
            result = json.loads(row["measured_cli"]["stdout"])
            self.assertIs(result["crypto_ok"], True, name)
            self.assertEqual(result["ok"], expected[name] == 0, name)
            self.assertEqual(row["measured_cli"]["stderr"], "")
            self.assertEqual(row["draft_expectation"]["author_reported_cli_exit"], expected[name])

    def test_expected_inputs_are_separate_from_cli_inputs(self) -> None:
        for name, row in self.rows.items():
            self.assertIn("AUTHOR_SPECIFIED", row["draft_expectation"]["provenance"])
            self.assertEqual(row["full_draft_procedure_execution"], "NOT_EVALUATED")
            command = row["measured_cli"]["command"]
            self.assertNotIn("inputs/c1.json", command)
            self.assertNotIn("inputs/e3.json", command)
            self.assertNotIn("--policy", command)
        self.assertEqual(
            self.rows["F5"]["expected_inputs_for_draft_procedure"]["action_bytes"], "a1.txt"
        )
        self.assertEqual(
            self.rows["F6"]["expected_inputs_for_draft_procedure"]["expected_executor.id"],
            "forge:agent-42-bot",
        )
        self.assertEqual(self.rows["F10"]["draft_expectation"]["receipt_procedure"], "PASS")
        self.assertEqual(self.rows["F10"]["draft_expectation"]["relying_party"], "REFUSE")

    def test_f7_is_missing_effect_with_supplied_effect_bytes_not_bad_status(self) -> None:
        pred = json.loads(payload(self.envs["F7"]))["predicate"]
        self.assertEqual(pred["status"], "refused")
        self.assertNotIn("effectDigest", pred)
        self.assertEqual(
            self.rows["F7"]["expected_inputs_for_draft_procedure"]["effect_bytes"], "e3.json"
        )
        self.assertEqual(self.rows["F7"]["draft_expectation"]["first_failing_check"], "3.4 step 6")

    def test_f9_approval_lifetime_violation_exists_independently_of_audit_time(self) -> None:
        pred = json.loads(payload(self.envs["F9"]))["predicate"]
        original_ap = json.loads(inputs()["ap.json"])
        self.assertGreater(pred["validity"]["expiresAt"], original_ap["validUntil"])
        self.assertIs(json.loads(self.rows["F9"]["measured_cli"]["stdout"])["freshness_ok"], True)

    def test_duplicate_members_and_boolean_controls_reach_cli_unchanged(self) -> None:
        rows = {row["id"]: row for row in self.report["controls"]}
        for name in ("C01", "C02", "C03", "C04"):
            self.assertEqual(rows[name]["measured_cli"]["exit_code"], 2)
        for name, member in (("C01", '"payload":'), ("C02", '"keyid":')):
            raw = (self.first / f"fixtures/{name}.envelope.json").read_text()
            self.assertEqual(raw.count(member), 2)
            self.assertIn("duplicate JSON key", rows[name]["measured_cli"]["stderr"])
        for name in ("C03", "C04"):
            result = json.loads(rows[name]["measured_cli"]["stdout"])
            self.assertTrue(result["crypto_ok"])
            self.assertFalse(result["structure_ok"])
            self.assertTrue(any("must be boolean" in e for e in result["errors"]))
        for name in ("P01", "P02"):
            self.assertEqual(rows[name]["measured_cli"]["exit_code"], 0)

    def test_cross_process_outputs_are_byte_identical_without_normalization(self) -> None:
        first = {
            p.relative_to(self.first): p.read_bytes() for p in self.first.rglob("*") if p.is_file()
        }
        second = {
            p.relative_to(self.second): p.read_bytes()
            for p in self.second.rglob("*")
            if p.is_file()
        }
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
