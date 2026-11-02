"""Deterministic semantic, extraction and provenance tests, without crypto claims."""

import base64
import json
import re
import unittest
from copy import deepcopy

from experiment import generate, local_payload_probe, receipt, test_auth
from profile import (
    ROOT,
    MAX_BYTES,
    MAX_DEPTH,
    REPRESENTATIONS,
    SCHEMA,
    ResourceLimit,
    Unsupported,
    binding_matches,
    boundary,
    compare,
    consume,
    decode64,
    digest,
    encode,
    exercise,
    extract_b,
    from_dsse,
    instance_binding,
    judge,
    parse,
    payload,
    reference_status,
    rounded,
    select_receipt,
    to_dsse,
    to_reference,
)


class ProvenanceTests(unittest.TestCase):
    """Check pinned external bytes, not merely the presence of a checksum string."""

    def test_every_external_source_hash_and_size(self) -> None:
        pins = json.loads((ROOT / "SOURCE_PINS.json").read_bytes())["sources"]
        for pin in pins:
            with self.subTest(source=pin["id"]):
                self.assertEqual(pin["status"], "AVAILABLE")
                raw = (ROOT / pin["path"]).read_bytes()
                self.assertEqual(len(raw), pin["bytes"])
                self.assertEqual(digest(raw), pin["sha256"])
                self.assertRegex(pin["accessed_at_utc"], r"T.*(?:\+00:00|Z)$")

    def test_expected_revisions_not_silently_advanced(self) -> None:
        pins = json.loads((ROOT / "SOURCE_PINS.json").read_bytes())["sources"]
        meta = [x for x in pins if x["role"] == "latest_revision_discovery"]
        self.assertEqual(len(meta), 4)
        for item in meta:
            self.assertEqual(item["expected_revision"], item["observed_latest_revision"])
            self.assertEqual(
                json.loads((ROOT / item["path"]).read_bytes())["rev"], item["expected_revision"]
            )

    def test_official_66_vector_file_matches_SER04_pin(self) -> None:
        raw = (ROOT / "sources/ser-v1-test-vectors.json").read_bytes()
        self.assertEqual(len(raw), 232309)
        self.assertEqual(
            digest(raw), "710cb8abab7ca51cf61b85c5610018f9a153add4c3db4f71b2d597e57b1671d1"
        )
        doc = json.loads(raw)
        self.assertEqual(doc["count"], 66)
        self.assertEqual(len(doc["vectors"]), 66)
        for vector in doc["vectors"]:
            for part in vector["bytes"]:
                with self.subTest(vector=vector["id"], part=part["label"]):
                    data = bytes.fromhex(part["hex"])
                    self.assertEqual(len(data), part["length"])
                    self.assertEqual(digest(data), part["sha256"])

    def test_all_proofbundle_receipts_reconstruct_official_bytes(self) -> None:
        bundle = json.loads((ROOT / "sources/proofbundle-ser-vectors.json").read_bytes())
        official = json.loads((ROOT / "sources/ser-v1-test-vectors.json").read_bytes())
        by_id = {
            v["id"]: bytes.fromhex(next(p["hex"] for p in v["bytes"] if p["label"] == "Receipt"))
            for v in official["vectors"]
        }
        self.assertEqual(len(bundle["vectors"]), 66)
        for vector in bundle["vectors"]:
            with self.subTest(vector=vector["id"]):

                def replace(match: re.Match) -> bytes:
                    value = bundle["payloads"][match[1].decode("ascii")]
                    raw = (
                        value["text"].encode("utf-8")
                        if "text" in value
                        else base64.b64decode(value["b64"])
                    )
                    return base64.b64encode(raw)

                template = (
                    vector["receipt_text"].encode("utf-8")
                    if "receipt_text" in vector
                    else base64.b64decode(vector["receipt_b64"])
                )
                raw = re.sub(rb"@(B[0-9]+)@", replace, template)
                self.assertEqual(digest(raw), vector["receipt_sha256"])
                self.assertEqual(raw, by_id[vector["id"]])

    def test_extracted_fixtures_match_provenance(self) -> None:
        for entry in json.loads((ROOT / "fixtures/MANIFEST.json").read_bytes()):
            self.assertEqual(digest((ROOT / entry["path"]).read_bytes()), entry["sha256"])
            self.assertFalse(entry["crypto_executed_here"])

    def test_cp_ids_and_sections_derived_from_published_text(self) -> None:
        text = (ROOT / "sources/draft-abak-ai-evaluation-claim-preservation-00.txt").read_text()
        profile = json.loads((ROOT / "mapping_profile.json").read_bytes())
        cases = json.loads((ROOT / "fixtures/scenarios.json").read_bytes())
        reqs = re.findall(r"^4\.(\d+)\.  (R-CP-\d+): (.+)$", text, re.M)
        scenarios = re.findall(r"^   (CP-T\d+) \(Section (4\.\d+)\):", text, re.M)
        self.assertEqual(len(reqs), 12)
        self.assertEqual(len(scenarios), 20)
        self.assertEqual([r["id"] for r in profile["requirements"]], [r[1] for r in reqs])
        self.assertEqual([c["id"] for c in cases], [s[0] for s in scenarios])
        for case, (_, section) in zip(cases, scenarios):
            self.assertEqual(case["requirement"], "R-CP-" + section.split(".")[1])


class MappingTests(unittest.TestCase):
    """Pin actual observable carriage, loss and independent reference states."""

    def test_DSSE_M1_exact_bytes(self) -> None:
        m1 = (ROOT / "fixtures/M1.dsse.json").read_bytes()
        self.assertEqual(to_dsse(receipt("P1")), m1)
        rebuilt = from_dsse(m1)
        self.assertEqual(extract_b(rebuilt), extract_b(receipt("P1")))
        self.assertEqual(
            parse(rebuilt)["signature"]["sig"], parse(receipt("P1"))["signature"]["sig"]
        )
        self.assertNotIn("key", parse(rebuilt)["signature"])

    def test_same_B_different_receipt_bytes_no_key_binding(self) -> None:
        candidates = [receipt(x) for x in ("P1", "P4", "P6", "N7")]
        self.assertEqual(len({digest(c) for c in candidates}), 4)
        self.assertEqual(len({digest(extract_b(c)) for c in candidates}), 1)
        # N7's published signature expectation is FAIL, but MATCH is still possible.
        ref = to_reference(candidates[0])
        for c in candidates:
            self.assertEqual(reference_status(ref, c)["matching"], "MATCH")
        view = consume(ref, "DIGEST_RESOLVED", candidate=receipt("N7"))
        self.assertEqual(view["checks"][0]["result"], "NOT_EVALUATED")

    def test_mapping_C1_through_C8(self) -> None:
        ref = to_reference(receipt("P1"))
        for name, expected in [
            ("P1", "MATCH"),
            ("P4", "MATCH"),
            ("P6", "MATCH"),
            ("P2", "NO_MATCH"),
            ("N7", "MATCH"),
            ("N13", "INDETERMINATE"),
            ("N14", "INDETERMINATE"),
        ]:
            with self.subTest(vector=name):
                self.assertEqual(reference_status(ref, receipt(name))["matching"], expected)
        wrong_algorithm = parse(ref)
        wrong_algorithm["digest_alg"] = "SHA256"
        self.assertEqual(
            reference_status(encode(wrong_algorithm), receipt("P1"))["matching"], "INDETERMINATE"
        )

    def test_mapping_R1_through_R16(self) -> None:
        ref = parse(to_reference(receipt("P1")))
        variants = []

        def variant(changes: dict) -> bytes:
            return encode(ref | changes)

        variants.extend(
            [
                (encode(ref), "P1", "Verified", "MATCH"),
                (variant({"purpose": "evaluation"}), "P1", "Unresolved", "MATCH"),
                (variant({"digest_alg": "sha-256"}), "P1", "Failed", "INDETERMINATE"),
                (variant({"digest": ref["digest"].upper()}), "P1", "Failed", "INDETERMINATE"),
                (variant({"digest": digest(extract_b(receipt("P2")))}), "P1", "Failed", "NO_MATCH"),
                (encode(ref), "N13", "Failed", "INDETERMINATE"),
                (variant({"x": 1}), "P1", "Malformed", "MATCH"),
                (
                    encode(ref)[:-1]
                    + b',"digest":"'
                    + digest(extract_b(receipt("P2"))).encode()
                    + b'"}',
                    "P1",
                    "Malformed",
                    "INDETERMINATE",
                ),
                (
                    encode({k: v for k, v in ref.items() if k != "digest_alg"}),
                    "P1",
                    "Malformed",
                    "INDETERMINATE",
                ),
                (encode([ref]), "P1", "Malformed", "INDETERMINATE"),
                (variant({"purpose": None}), "P1", "Malformed", "MATCH"),
                (encode(ref).replace(b'"digest":', b'"\\u0064igest":'), "P1", "Verified", "MATCH"),
                (
                    encode(ref)[:-1] + b',"\\u0064igest":"' + ref["digest"].encode() + b'"}',
                    "P1",
                    "Malformed",
                    "INDETERMINATE",
                ),
                (b"\xef\xbb\xbf" + encode(ref), "P1", "Malformed", "INDETERMINATE"),
                (
                    variant({"purpose": "evaluation"}).replace(b"evaluation", b"\xffvaluation"),
                    "P1",
                    "Malformed",
                    "INDETERMINATE",
                ),
                (variant({"type": "text/plain"}), "P1", "Unresolved", "MATCH"),
            ]
        )
        for number, (raw, candidate, state, match) in enumerate(variants, 1):
            with self.subTest(vector=f"R{number}"):
                result = reference_status(raw, receipt(candidate))
                self.assertEqual((result["state"], result["matching"]), (state, match))

    def test_unavailable_unimplemented_unaccepted_resource_limit(self) -> None:
        ref = to_reference(receipt("P1"))
        self.assertEqual(reference_status(ref, None)["reason"], "unavailable")
        self.assertEqual(
            reference_status(ref, receipt("P1"), implements_context=False)["reason"],
            "unimplemented",
        )
        self.assertEqual(
            reference_status(ref, receipt("P1"), accepts_context=False)["state"], "Unresolved"
        )
        bounded = reference_status(ref, b" " * (MAX_BYTES + 1))
        self.assertIsNone(bounded["state"])
        self.assertEqual(bounded["reason"], "RESOURCE_LIMIT")
        self.assertEqual(bounded["matching"], "INDETERMINATE")
        oversized_reference = reference_status(b" " * (MAX_BYTES + 1), receipt("P1"))
        self.assertIsNone(oversized_reference["state"])
        self.assertEqual(oversized_reference["reason"], "RESOURCE_LIMIT")

    def test_digest_only_consumer_does_not_read_hidden_candidate(self) -> None:
        ref = to_reference(receipt("P1"))
        view = consume(ref, "DIGEST_ONLY", candidate=receipt("P1"))
        self.assertIsNone(view["source_assertions"])
        self.assertEqual(view["reference"]["state"], "Unresolved")
        self.assertEqual(view["evidence"]["digest_knowledge"], "REPORTED")
        self.assertEqual(view["evidence"]["B_availability"], "UNAVAILABLE")

    def test_mismatch_does_not_supply_payload(self) -> None:
        view = consume(to_reference(receipt("P1")), "DIGEST_RESOLVED", candidate=receipt("P2"))
        self.assertIsNone(view["source_assertions"])
        self.assertEqual(view["reference"]["matching"], "NO_MATCH")

    def test_full_routes_carry_exact_assertions(self) -> None:
        expected = payload(extract_b(receipt("P10")))
        for rep in ("SER", "DSSE", "DIGEST_RESOLVED"):
            _, view = exercise(receipt("P10"), rep)
            self.assertEqual(view["source_assertions"], expected)
            self.assertEqual(view["evidence"]["digest_knowledge"], "RECOMPUTED")
            self.assertEqual(view["actual_executed_identity"], "UNESTABLISHED")

    def test_signature_is_never_promoted_to_truth(self) -> None:
        for rep in REPRESENTATIONS:
            _, view = exercise(receipt("P2"), rep)
            self.assertEqual(view["checks"][0]["type"], "signature")
            self.assertEqual(view["checks"][0]["result"], "NOT_EVALUATED")
            self.assertEqual(view["measurement_state"], "UNESTABLISHED")
            self.assertEqual(view["coverage"], "UNESTABLISHED")

    def test_unknown_version_member_and_payload_basis(self) -> None:
        for changes in (
            {"schema": SCHEMA + "/new"},
            {"execution_state": "ran"},
            {"passed": "true"},
        ):
            view = consume(local_payload_probe(changes), "SER")
            self.assertIsNone(view["source_assertions"])
        self.assertIsNone(
            consume(receipt("P1"), "SER", profile_version="new/2")["source_assertions"]
        )
        self.assertIsNone(consume(receipt("P1"), "OTHER")["source_assertions"])

    def test_multi_signature_DSSE_does_not_pick_first(self) -> None:
        obj = parse(to_dsse(receipt("P1")))
        obj["signatures"].append(obj["signatures"][0])
        self.assertIsNone(consume(encode(obj), "DSSE")["source_assertions"])


class SemanticTests(unittest.TestCase):
    """Test negative behavior and transformations independently of case labels."""

    def test_rounding_crosses_threshold_without_rewriting_source(self) -> None:
        view = consume(receipt("P2"), "SER")
        original = deepcopy(view["source_assertions"])
        derivation = rounded(view, 1)
        self.assertEqual(derivation["input_score"], "0.762")
        self.assertEqual(derivation["presentation_score"], "0.8")
        self.assertFalse(derivation["source_comparison"])
        self.assertTrue(derivation["presentation_comparison"])
        self.assertEqual(original, view["source_assertions"])
        self.assertEqual(derivation["source_uncertainty"], "UNESTABLISHED")

    def test_decimal_and_integer_exactness(self) -> None:
        self.assertFalse(compare("0." + "9" * 100, ">=", "1"))
        self.assertTrue(compare("0.800", ">=", "0.8"))
        self.assertTrue(compare("-1", "<", "0"))
        self.assertTrue(compare("2", ">", "1"))
        obj = local_payload_probe({"n": 2**53 - 1})
        self.assertEqual(consume(obj, "SER")["source_assertions"]["n"], 2**53 - 1)
        for changes in (
            {"n": 2**53},
            {"n": True},
            {"score": "1e-3"},
            {"score": "+1"},
            {"score": "00.1"},
            {"passed": False},
            {"model_id_commit": "sha256:dummy"},
        ):
            self.assertIsNone(consume(local_payload_probe(changes), "SER")["source_assertions"])

    def test_two_policy_results_not_source_rewrites(self) -> None:
        view = consume(receipt("P1"), "SER")
        before = deepcopy(view["source_assertions"])
        a = judge(view, "A", "0.800", "A/1")
        b = judge(view, "B", "0.900", "B/1")
        self.assertTrue(a["result"])
        self.assertFalse(b["result"])
        self.assertEqual(len(view["consumer_judgments"]), 2)
        self.assertEqual(view["source_assertions"], before)
        self.assertFalse(view["reliance_records"])

    def test_no_criterion_and_missing_criterion_not_conflated(self) -> None:
        a = boundary({"criterion": "explicit_none"})
        b = boundary({})
        self.assertNotEqual(a["source_record"], b["source_record"])
        self.assertEqual(a["SER_encoding"], b["SER_encoding"])
        source = parse(receipt("P1"))
        value = payload(extract_b(receipt("P1")))
        for key in ("passed", "comparator", "threshold"):
            del value[key]
        source["payload_b64"] = base64.b64encode(encode(value)).decode()
        self.assertIsNone(consume(encode(source), "SER")["source_assertions"])

    def test_ambiguous_selection_and_duplicate_attempts(self) -> None:
        for records in ([], [receipt("P1"), receipt("P2")], [receipt("P1"), receipt("P1")]):
            with self.assertRaises(Unsupported):
                select_receipt(records)
        with self.assertRaises(Unsupported):
            select_receipt([receipt("P1"), receipt("P1")], digest(extract_b(receipt("P1"))))
        self.assertEqual(
            select_receipt([receipt("P1"), receipt("P2")], digest(extract_b(receipt("P2")))),
            receipt("P2"),
        )

    def test_later_authentication_cannot_restore_absent_coverage(self) -> None:
        wire = to_dsse(receipt("P1"))
        auth = test_auth(wire)
        self.assertEqual(auth["result"], "VERIFIED")
        self.assertTrue(auth["tampered_input_rejected"])
        view = consume(wire, "DSSE")
        view["checks"].append(auth)
        self.assertEqual(view["coverage"], "UNESTABLISHED")
        self.assertNotIn("excluded", view["source_assertions"])
        self.assertEqual(view["prior_mapping_history"], "UNESTABLISHED")

    def test_binding_substitution(self) -> None:
        source = receipt("P1")
        output = to_dsse(source)
        binding = instance_binding(source, output, "")
        self.assertTrue(binding_matches(binding, source, output, ""))
        self.assertFalse(binding_matches(binding, receipt("P2"), output, ""))
        self.assertFalse(binding_matches(binding, source, output + b" ", ""))
        self.assertFalse(binding_matches(binding, source, output, "/score"))
        binding["material"]["source_sha256"] = digest(receipt("P2"))
        self.assertFalse(binding_matches(binding, source, output, ""))

    def test_all_published_scenario_routes_and_class_counts(self) -> None:
        data = generate()
        self.assertEqual(len(data["matrix"]), 48)
        self.assertEqual(len(data["scenarios"]), 80)
        self.assertEqual(
            data["matrix_counts"],
            {"PRESERVED": 17, "QUALIFIED_LOSS": 10, "UNESTABLISHED": 17, "NOT_APPLICABLE": 4},
        )
        for row in data["scenarios"]:
            self.assertTrue(all(row["checks"].values()))
        by_id = {(r["id"], r["representation"]): r for r in data["scenarios"]}
        for rep in REPRESENTATIONS:
            for tid in ("CP-T01", "CP-T02", "CP-T05", "CP-T14"):
                self.assertEqual(by_id[tid, rep]["class"], "NOT_APPLICABLE")
            for tid in ("CP-T07", "CP-T12", "CP-T16"):
                self.assertEqual(by_id[tid, rep]["class"], "QUALIFIED_LOSS")


class BoundedInputTests(unittest.TestCase):
    """Malformed and expensive inputs cannot become accepted source assertions."""

    def test_duplicate_unescaped_and_escaped_keys(self) -> None:
        for raw in (b'{"x":1,"x":2}', b'{"x":1,"\\u0078":2}', b'{"x":{"a":1,"a":2}}'):
            with self.assertRaises(Unsupported):
                parse(raw)

    def test_json_unicode_and_byte_boundaries(self) -> None:
        for raw in (
            b"\xef\xbb\xbf{}",
            b"{}x",
            b"\xff",
            b'{"x":NaN}',
            b'{"x":"\\ud800"}',
            b'{"x":"\\uffff"}',
            b'{"x":"\\ufdd0"}',
        ):
            with self.assertRaises(Unsupported):
                parse(raw)
        self.assertEqual(parse(b" \n{}\t"), {})
        with self.assertRaises(ResourceLimit):
            parse(b" " * (MAX_BYTES + 1))
        with self.assertRaises(ResourceLimit):
            parse(b"[" * (MAX_DEPTH + 1) + b"]" * (MAX_DEPTH + 1))
        self.assertEqual(
            parse(encode({"quoted_brackets": "[" * 40})), {"quoted_brackets": "[" * 40}
        )

    def test_canonical_base64_only(self) -> None:
        for bad in ("Zg", "Zg===", "Zg==\n", "Zh==", "*", 3, "é"):
            with self.assertRaises(Unsupported):
                decode64(bad)
        self.assertEqual(decode64("Zg=="), b"f")
        with self.assertRaises(Unsupported):
            extract_b(receipt("N13"))

    def test_receipt_shape_and_canonical_B(self) -> None:
        obj = parse(receipt("P1"))
        obj["extra"] = "unknown"
        with self.assertRaises(Unsupported):
            extract_b(encode(obj))
        obj = parse(receipt("P1"))
        obj["payload_b64"] = base64.b64encode(extract_b(receipt("P1")) + b"\n").decode()
        self.assertIsNone(consume(encode(obj), "SER")["source_assertions"])

    def test_timestamp_year_zero_and_unknown_order(self) -> None:
        view = consume(local_payload_probe({"timestamp": "0000-02-29T00:00:00Z"}), "SER")
        self.assertIsNotNone(view["source_assertions"])
        self.assertEqual(view["criteria_before_run"], "UNESTABLISHED")
        for invalid in (
            "2026-02-29T00:00:00Z",
            "2026-01-01T00:00:60Z",
            "2026-01-01T00:00:00+00:00",
            "2026-00-01T00:00:00Z",
        ):
            self.assertIsNone(
                consume(local_payload_probe({"timestamp": invalid}), "SER")["source_assertions"]
            )
