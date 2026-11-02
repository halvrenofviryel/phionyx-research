"""Regression probes of pinned bytes and real released APIs; no runtime simulation."""

import copy
import hashlib
import importlib.metadata
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fixtures import GATE_PUB, OBSERVER, OBSERVER_PUB, digest, payload, predicate  # noqa: E402
from probe import collect, report_projection, verify_decision, verify_outcome  # noqa: E402
from proofbundle.decision import verify_decision_receipt  # noqa: E402
from proofbundle.outcome import emit_outcome_receipt  # noqa: E402


class ReleasedAPIProbe(unittest.TestCase):
    """Check observable boundaries against independent pinned vector expectations."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.raw, cls.report, cls.envs = collect()

    def test_exact_dependency_versions(self) -> None:
        for line in (ROOT / "requirements.lock").read_text().splitlines():
            if line and not line.startswith("#"):
                package, version = line.split()[0].split("==")
                self.assertEqual(importlib.metadata.version(package), version, package)

    def test_preserved_source_bytes(self) -> None:
        for row in json.loads((ROOT / "sources/manifest.json").read_text()):
            if row["path"].startswith("../.downloads/"):
                # Acquired binaries are cache-only; installation checks the hash lock.
                continue
            self.assertEqual(row["status"], 200)
            self.assertTrue(row["accessed_at_utc"].endswith("+00:00"))
            raw = (ROOT / "sources" / row["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row["sha256"], row["path"])

    def test_installed_source_is_unmodified(self) -> None:
        dist = importlib.metadata.distribution("proofbundle")
        for module, row in json.loads((ROOT / "evidence/api-inventory.json").read_text()).items():
            raw = dist.locate_file(f"proofbundle/{module}.py").read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row["sha256"], module)

    def test_appendix_a_payloads_and_signatures_match_published_bytes(self) -> None:
        expected = {
            "V1-good": (1829, "b9dfd26537542632013d0df166141a788551b4987dfa33b060d5b5ebba78dfb1"),
            "V1-bad": (1829, "69eb87fb33a29153182b0e0c89a444023cc00c82fe7c8db1c7e0893363b2c926"),
            "V2-good": (1765, "ed149a1c7383842eebf8304001da9de97d130b0b15080d1315ab8fbf1274ed44"),
            "V2-bad": (1866, "646d4b2229a55c54848361030bf6d57816597a96bd7d1fb00d7da0f03b009bd2"),
            "V3-decision": (
                1827,
                "0014b1c419798125c3984e85a4b322ee619a3227978840cac5f9d282b189521f",
            ),
            "V3-good": (694, "f0ff90cf25e2db1e989fa79869d4b3b46899112e8c2269d9a18a64b751aa7274"),
            "V3-bad": (694, "48be708cf3f959556323474f4a5c9193b417d2bfea5c88bb852daf00b64827b4"),
        }
        text = (ROOT / "sources/draft-gruszka-audit-decision-receipts-03.txt").read_text()
        compact = "".join(text.split())
        for name, (size, sha) in expected.items():
            with self.subTest(vector=name):
                self.assertEqual(len(payload(self.envs[name])), size)
                self.assertEqual(digest(payload(self.envs[name]))["sha256"], sha)
                self.assertIn(sha, text)
                self.assertIn(self.envs[name]["signatures"][0]["sig"], compact)

    def test_appendix_a_positive_and_negative_controls(self) -> None:
        rows = self.raw["appendix_a"]
        for name in ("V1-good", "V2-good", "V3-decision", "V3-good"):
            self.assertIs(rows[name]["ok"], True, name)
        self.assertIs(rows["V1-bad"]["crypto_ok"], False)
        self.assertIsNone(rows["V1-bad"]["audience_ok"])
        self.assertIs(rows["V2-bad"]["crypto_ok"], True)
        self.assertIs(rows["V2-bad"]["structure_ok"], False)
        self.assertIs(rows["V3-bad"]["crypto_ok"], True)
        self.assertIs(rows["V3-bad"]["decision_bound"], False)
        for name in ("V1-bad", "V2-bad", "V3-bad"):
            self.assertIs(rows[name]["ok"], False, name)

    def test_wrong_key_nonce_and_expiry_are_refused(self) -> None:
        env = self.envs["V1-good"]
        wrong_key = verify_decision_receipt(env, OBSERVER_PUB, strict=True, now=1792054860)
        wrong_nonce = verify_decision_receipt(
            env, GATE_PUB, strict=True, expected_nonce="wrong-context", now=1792054860
        )
        expired = verify_decision(env, time="2026-10-15T09:05:05Z")
        self.assertIs(wrong_key["crypto_ok"], False)
        self.assertIs(wrong_nonce["nonce_ok"], False)
        self.assertIs(expired["freshness_ok"], False)
        for result in (wrong_key, wrong_nonce, expired):
            self.assertIs(result["ok"], False)

    def test_baseline_receipt_is_not_execution_observation(self) -> None:
        row = self.raw["baseline"]
        self.assertIs(row["decision"]["ok"], True)
        self.assertIsNone(row["decision"]["action_outcome_proven"])
        self.assertIs(row["outcome"]["ok"], True)
        self.assertIs(row["outcome"]["execution_proven"], True)
        self.assertEqual(
            row["outcome"]["evidence_levels"]["effect"]["level_name"], "REFERENCE_WELL_FORMED"
        )
        self.assertIsNone(row["outcome"]["executor_role_trusted"])
        self.assertTrue(row["approval_fixture"]["fixture_time_bounds"])

    def test_repeated_receipt_verification_is_stateless(self) -> None:
        first, second = self.raw["repeat_verification"]
        self.assertIs(first["ok"], True)
        self.assertEqual(first, second)

    def test_unknown_is_preserved_not_changed_to_failure(self) -> None:
        row = self.raw["unknown"]
        self.assertIs(row["decision"]["ok"], True)
        self.assertIsNone(row["decision"]["action_outcome_proven"])
        self.assertEqual(
            predicate(self.envs["unknown-decision"])["actionOutcome"]["status"], "unknown"
        )
        self.assertTrue(any("status must be one of" in x for x in row["outcome_validation_errors"]))
        self.assertEqual(row["timeout"], "NOT_EVALUATED")

    def test_two_outcomes_can_bind_one_allow_without_execution_evidence(self) -> None:
        row = self.raw["two_outcomes"]
        self.assertTrue(
            all(v["ok"] is True and v["decision_bound"] is True for v in row["verifications"])
        )
        self.assertEqual(row["local_inventory"]["distinct_outcome_payloads"], 2)
        self.assertEqual(row["local_inventory"]["distinct_decision_refs"], 1)
        self.assertEqual(row["public_sequence_scan_without_sequence"], [])

    def test_outcome_same_executor_id_control_is_rejected(self) -> None:
        p = copy.deepcopy(predicate(self.envs["baseline-outcome"]))
        p["executor"]["id"] = "gate-1"
        result = verify_outcome(emit_outcome_receipt(p, OBSERVER), self.envs["V1-good"])
        self.assertIs(result["role_separation_ok"], False)
        self.assertIs(result["ok"], False)

    def test_sequence_complete_is_only_within_observed_bounds(self) -> None:
        row = self.raw["sequence_control"]
        self.assertTrue(all(v["ok"] is True for v in row["verifications"]))
        self.assertEqual(row["one_and_three"][0]["gaps"], [2])
        self.assertIs(row["one_and_three"][0]["complete"], False)
        self.assertIs(row["three_only"][0]["complete"], True)
        self.assertEqual(row["three_only"][0]["seqs"], [3])

    def test_two_allow_payloads_do_not_claim_a_package_set_audit(self) -> None:
        row = self.raw["same_approval_two_allows"]
        self.assertTrue(all(v["ok"] is True for v in row["verifications"]))
        self.assertEqual(row["local_inventory"]["distinct_decision_payloads"], 2)
        self.assertIs(row["local_inventory"]["same_approval_bytes_referenced"], True)
        self.assertEqual(row["package_set_audit"], "NOT_EVALUATED")

    def test_evaluation_evidence_does_not_promote_deny_to_allow(self) -> None:
        row = self.raw["evaluation_evidence"]
        preflight = row["fixture_preflight"]
        for key in (
            "signature_ok",
            "payload_matches_receipt",
            "canonical_payload",
            "score_consistent",
        ):
            self.assertIs(preflight[key], True, key)
        self.assertEqual(
            preflight["payload_sha256"],
            "8cd849a6dcce08aee334511d7b2f31c54e478885dda1795d3c8f972dd0d4811c",
        )
        self.assertEqual(
            preflight["receipt_sha256"],
            "02036d1f57509858330383755ec16c532bdc58b0f2d949464488d57abc9f95e7",
        )
        self.assertIs(row["reference_resolution"]["content_root_ok"], True)
        self.assertIs(row["wrong_content_control"]["content_root_ok"], False)
        self.assertEqual(row["recorded_verdict"], "DENY")
        self.assertIs(row["deny_receipt"]["ok"], True)
        self.assertIs(row["deny_under_allow_only_policy"]["ok"], False)
        self.assertIs(row["deny_under_allow_only_policy"]["policy_ok"], False)
        self.assertIs(row["allow_policy_positive_control"]["ok"], True)
        self.assertIs(row["ser_as_decision"]["ok"], False)

    def test_all_nine_cases_keep_unknown_axes_visible(self) -> None:
        self.assertEqual(self.report["scenario_count"], 9)
        self.assertEqual(self.report["runtime_scenarios_executed"], 0)
        self.assertEqual(
            self.report["status_counts"], {"PARTIALLY_EVALUATED": 6, "NOT_EVALUATED": 3}
        )
        for case in self.report["scenarios"]:
            self.assertEqual(case["approval_consumption_state"]["status"], "NOT_EVALUATED")
            self.assertEqual(case["execution_observation_state"]["status"], "UNOBSERVED")
            self.assertEqual(case["effect_observation_state"]["status"], "UNOBSERVED")
            self.assertEqual(case["set_level_audit_finding"]["status"], "NOT_EVALUATED")

    def test_cli_vectors_and_repeated_output_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory(prefix="decision-receipts-") as temp:
            first, second = Path(temp) / "first", Path(temp) / "second"
            for directory in (first, second):
                subprocess.run(
                    [sys.executable, str(ROOT / "probe.py"), "--output", str(directory)],
                    check=True,
                    timeout=60,
                )
            for f in first.rglob("*"):
                if f.is_file():
                    self.assertEqual(f.read_bytes(), (second / f.relative_to(first)).read_bytes())
            expected = {
                "V1-good": 0,
                "V1-bad": 1,
                "V2-good": 0,
                "V2-bad": 2,
                "V3-decision": 0,
                "V3-good": 0,
                "V3-bad": 2,
            }
            observed = json.loads((first / "cli_results.json").read_text())
            self.assertEqual({r["vector"]: r["exit_code"] for r in observed}, expected)
            self.assertTrue(all(r["stderr"] == "" for r in observed))
            archived = json.loads((ROOT / "evidence/api_results.original.json").read_text())
            projected = json.loads((first / "api_results.json").read_text())
            projected.pop("_serialization")
            self.assertEqual(projected, report_projection(archived))


if __name__ == "__main__":
    unittest.main()
