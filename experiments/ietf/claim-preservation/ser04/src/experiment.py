"""Executable CP pressure cases and a narrowly scoped requirement matrix."""

import base64
import hashlib
import hmac
import json
from collections import Counter
from copy import deepcopy

from profile import (
    ROOT,
    REPRESENTATIONS,
    SCHEMA,
    VERSION,
    Unsupported,
    binding_matches,
    boundary,
    consume,
    digest,
    encode,
    exercise,
    extract_b,
    instance_binding,
    judge,
    parse,
    payload,
    rounded,
    select_receipt,
)


def receipt(name: str) -> bytes:
    """Read an extracted external fixture without reserializing it."""
    return (ROOT / "fixtures" / (name + ".receipt.json")).read_bytes()


def local_payload_probe(changes: dict) -> bytes:
    """Make an explicitly UNSIGNED specimen, not a valid signed receipt."""
    obj = parse(receipt("P1"))
    value = payload(extract_b(receipt("P1")))
    value.update(changes)
    obj["payload_b64"] = base64.b64encode(encode(value)).decode("ascii")
    # Empty signature is intentional. Never reuse P1's signature for mutated B.
    obj["signature"] = {"alg": "ed25519", "sig": ""}
    return encode(obj)


def test_auth(data: bytes) -> dict:
    """Test-only symmetric carrier authentication; NOT a signature or SER check."""
    key = b"PUBLIC LOCAL TEST KEY - NO SECURITY OR IDENTITY CLAIM"
    tag = hmac.new(key, data, hashlib.sha256).digest()
    valid = hmac.compare_digest(tag, hmac.new(key, data, hashlib.sha256).digest())
    changed = hmac.compare_digest(tag, hmac.new(key, data + b"x", hashlib.sha256).digest())
    return {
        "type": "LOCAL_TEST_HMAC_SHA256",
        "actor": "local-test-carrier",
        "procedure": "stdlib hmac SHA-256; public test-only symmetric key",
        "checked_input_sha256": digest(data),
        "result": "VERIFIED" if valid else "INVALID",
        "tampered_input_rejected": not changed,
        "limitation": "Not Ed25519, not a signature, no identity/authority/truth claim",
    }


def run_case(case: dict, representation: str) -> dict:
    """Execute one published scenario's locally specified observable checks."""
    tid = case["id"]
    selected = "P2" if tid == "CP-T08" else "P10" if tid in ("CP-T11", "CP-T15") else "P1"
    source = receipt(selected)
    wire, view = exercise(source, representation)
    available = view["source_assertions"] is not None
    result, reason, observations = "PRESERVED", case["observable_expectation"], {}
    checks = {}

    if tid == "CP-T01":
        observations = boundary(
            {
                "execution": "completed",
                "score": "0.834",
                "criterion": "not_established",
                "source_verdict": None,
            }
        )
        checks = {"no_invented_criterion": observations["SER_encoding"] == "UNSUPPORTED"}
        result = "NOT_APPLICABLE"
        reason = "Valid SER requires a criterion comparison; a score-only completed run is outside its domain."
    elif tid == "CP-T02":
        explicit = boundary({"criterion": "explicitly_none", "score": "0.834"})
        unknown = boundary({"score": "0.834"})
        observations = {"explicit": explicit, "omitted": unknown}
        checks = {
            "distinction_retained_in_local_context": explicit["source_record"]
            != unknown["source_record"],
            "neither_forced_into_SER": explicit["SER_encoding"]
            == unknown["SER_encoding"]
            == "UNSUPPORTED",
        }
        result = "NOT_APPLICABLE"
        reason = (
            "Neither explicit no-criterion nor omitted unknown criterion is a valid SER assessment."
        )
    elif tid == "CP-T03":
        before = deepcopy(view["source_assertions"])
        observations = judge(view, "consumer-A", "0.900", "threshold-policy/1")
        checks = {
            "source_not_rewritten": before == view["source_assertions"],
            "new_judgment_separate": not available
            or observations["origin"] == "later_consumer_policy",
        }
        if not available:
            result, reason = (
                "QUALIFIED_LOSS",
                "Digest-only input supplies no score for the new assessment.",
            )
    elif tid == "CP-T04":
        second = local_payload_probe({"metric": "accuracy_secondary"})
        observations = {
            "local_context": {"run": "same-local-run", "task": "same-local-task"},
            "second_fixture": "author-constructed unsigned semantic specimen",
            "B_digests": [digest(extract_b(source)), digest(extract_b(second))],
        }
        try:
            select_receipt([source, second])
            checks["ambiguous_selection_rejected"] = False
        except Unsupported:
            checks["ambiguous_selection_rejected"] = True
        checks["explicit_snapshot_selection"] = (
            select_receipt([source, second], digest(extract_b(second))) == second
        )
        if not available:
            result, reason = (
                "UNESTABLISHED",
                "No payload metric visible; digest identity alone supplies no task/run context.",
            )
    elif tid == "CP-T05":
        states = [
            "ran",
            "did_not_run",
            "unavailable",
            "invalid",
            "not_evaluated",
            "error",
            "inconclusive",
        ]
        observations = {
            s: boundary({"measurement_state": s, "criterion_assessment": "not_evaluated"})
            for s in states
        }
        checks = {
            "all_distinct_in_local_context": len(
                {encode(v["source_record"]) for v in observations.values()}
            )
            == len(states),
            "no_boolean_coercion": all(
                v["SER_encoding"] == "UNSUPPORTED" for v in observations.values()
            ),
            "native_execution_unknown": view["measurement_state"] == "UNESTABLISHED",
        }
        result = "NOT_APPLICABLE"
        reason = "SER has no native execution-state field; local boundary states cannot be emitted as passed booleans."
    elif tid == "CP-T06":
        observations = {
            "issuer_n": view["source_assertions"]["n"] if available else None,
            "population_total": None,
            "claim": view["coverage"],
        }
        checks = {"no_complete_population_inferred": view["coverage"] == "UNESTABLISHED"}
        result, reason = (
            "UNESTABLISHED",
            "n is a reported sample count, not complete population or attempt accounting.",
        )
    elif tid == "CP-T07":
        attempts = [receipt("P1"), receipt("P2"), receipt("P1")]
        observations = {
            "local_context_only": {
                "supplied_records": len(attempts),
                "distinct_B": len({digest(extract_b(r)) for r in attempts}),
                "actual_attempts": None,
                "retry_or_duplicate": "unknown",
            },
            "transported_attempt_rule": None,
        }
        checks = {"no_unique_digest_denominator": view["coverage"] == "UNESTABLISHED"}
        result, reason = (
            "QUALIFIED_LOSS",
            "Three supplied records/two B digests do not encode retries or actual attempt count in SER.",
        )
    elif tid == "CP-T08":
        observations = rounded(view, 1)
        checks = {
            "source_false_presentation_true": not available
            or (
                observations["source_comparison"] is False
                and observations["presentation_comparison"] is True
            ),
            "source_score_retained": not available or view["source_assertions"]["score"] == "0.762",
        }
        if not available:
            result, reason = (
                "QUALIFIED_LOSS",
                "Digest-only input carries neither the exact score nor the threshold.",
            )
    elif tid == "CP-T09":
        observations = {
            "executed_identity": view["actual_executed_identity"],
            "declared_suite": view["source_assertions"]["suite"] if available else None,
            "model_commitment": view["source_assertions"]["model_id_commit"] if available else None,
            "evaluator_identity": None,
            "harness_config": None,
            "enforced_network_setting": None,
        }
        checks = {
            "no_execution_or_independence_claim": view["actual_executed_identity"]
            == "UNESTABLISHED"
        }
        if not available:
            result, reason = (
                "QUALIFIED_LOSS",
                "Digest citation alone does not carry the declared suite or model/dataset commitments.",
            )
    elif tid == "CP-T10":
        observations = {
            "origin": "author-constructed local evidence reference, NOT a SER member",
            "reference": "urn:local-test:missing-evidence",
            "actor": VERSION,
            "context": "offline fixture consumption; bytes not supplied; retrieval not attempted",
            "availability": "UNAVAILABLE",
            "digest_knowledge": "UNAVAILABLE",
            "digest": None,
            "custodian": None,
            "existence": "UNESTABLISHED",
        }
        checks = {
            "no_dummy_digest": observations["digest"] is None,
            "B_availability_not_external_evidence": view["evidence"]["B_availability"]
            in ("AVAILABLE", "UNAVAILABLE"),
        }
        result, reason = (
            "UNESTABLISHED",
            "No source evidence bytes/digest supplied; SER has no general evidence availability field.",
        )
    elif tid == "CP-T11":
        observations = {
            "B_digest": view["evidence"],
            "criteria_digest": view["source_assertions"].get("criteria_digest")
            if available
            else None,
            "criteria_digest_knowledge": "REPORTED" if available else "UNAVAILABLE",
            "criteria_bytes": "UNAVAILABLE",
            "source_authentication": "NOT_EVALUATED",
        }
        checks = {
            "not_claimed_recomputed": observations["criteria_digest_knowledge"] != "RECOMPUTED"
        }
        if not available:
            result, reason = (
                "QUALIFIED_LOSS",
                "The citation reports a digest of B, but the criteria digest inside B is unavailable.",
            )
    elif tid == "CP-T12":
        lost_context = {
            "origin": "author-constructed pre-SER context",
            "coverage": "partial",
            "excluded": 4,
            "upstream_attempts": "unknown",
        }
        auth = test_auth(wire)
        observations = {
            "earlier_context": lost_context,
            "later_authentication": auth,
            "surviving_coverage": view["coverage"],
            "reintroduced": False,
        }
        checks = {
            "auth_succeeded": auth["result"] == "VERIFIED",
            "tamper_detected": auth["tampered_input_rejected"],
            "auth_did_not_repair_loss": view["coverage"] == "UNESTABLISHED",
        }
        result, reason = (
            "QUALIFIED_LOSS",
            "A later test MAC verifies surviving bytes; the earlier partial/excluded qualification is absent.",
        )
    elif tid == "CP-T13":
        unsupported = consume(wire, representation, candidate=source, profile_version="unknown/2")
        auth = test_auth(wire)
        unsupported["checks"].append(auth)
        observations = unsupported
        checks = {
            "carrier_auth_distinct": auth["result"] == "VERIFIED",
            "no_semantic_assertion": unsupported["source_assertions"] is None,
            "SER_signature_not_claimed": unsupported["checks"][0]["result"] == "NOT_EVALUATED",
        }
    elif tid == "CP-T14":
        observations = {"reliance_records": view["reliance_records"], "exported": True}
        checks = {"no_decision_invented": not view["reliance_records"]}
        result, reason = "NOT_APPLICABLE", "No actual reliance/decision record exists in the input."
    elif tid == "CP-T15":
        observations = {
            "criteria_digest": view["source_assertions"].get("criteria_digest")
            if available
            else None,
            "ordering": view["criteria_before_run"],
        }
        checks = {"no_prerun_inference": view["criteria_before_run"] == "UNESTABLISHED"}
        result, reason = (
            "UNESTABLISHED",
            "P10 commitment and issuer timestamp provide no supported criteria-before-run relation.",
        )
    elif tid == "CP-T16":
        old_wire, old = exercise(receipt("P2"), representation)
        observations = {
            "old": old["source_assertions"],
            "new": view["source_assertions"],
            "old_wire_sha256": digest(old_wire),
            "new_wire_sha256": digest(wire),
            "amendment": {"origin": "local context only", "relation": "new corrects old"},
            "native_amendment_link": None,
        }
        checks = {
            "snapshots_not_overwritten": digest(old_wire) != digest(wire),
            "opposing_assertions_retained_if_available": not available
            or (
                old["source_assertions"]["passed"] is False
                and view["source_assertions"]["passed"] is True
            ),
        }
        result, reason = (
            "QUALIFIED_LOSS",
            "SER has no correction/amendment link; local context is not recovered from either carrier.",
        )
    elif tid == "CP-T17":
        new_view = consume(
            wire, representation, candidate=source, profile_version="cp-ser05/unknown"
        )
        new_source = local_payload_probe({"schema": SCHEMA + "-future"})
        if representation == "DSSE":
            new_envelope = parse(wire)
            new_envelope["payloadType"] += "-future"
            native_new = consume(encode(new_envelope), representation)
        else:
            _, native_new = exercise(new_source, representation)
        observations = {"new_local_profile": new_view, "new_native_basis": native_new}
        checks = {
            "local_basis_rejected": new_view["source_assertions"] is None,
            "native_basis_not_reinterpreted": native_new["source_assertions"] is None,
        }
    elif tid == "CP-T18":
        record = instance_binding(source, wire, "")
        other_source = receipt("P2")
        other_wire, _ = exercise(other_source, representation)
        observations = {"local_binding": record, "native_binding_field": None}
        checks = {
            "correct_binding": binding_matches(record, source, wire, ""),
            "substituted_source_rejected": not binding_matches(record, other_source, wire, ""),
            "substituted_output_rejected": not binding_matches(record, source, other_wire, ""),
            "substituted_selector_rejected": not binding_matches(record, source, wire, "/score"),
        }
        reason = "LOCAL record substitution detected; native SER/DSSE/reference still has no mapping-instance record."
    elif tid == "CP-T19":
        try:
            extract_b(receipt("N14"))
            rejected = False
        except Unsupported:
            rejected = True
        try:
            parse(b'{"score":"0.9","scor\\u0065":"0.1"}')
            escaped_rejected = False
        except Unsupported:
            escaped_rejected = True
        observations = {
            "external_vector": "N14",
            "escaped_duplicate": "author-constructed invalid JSON object",
        }
        checks = {
            "N14_rejected_before_mapping": rejected,
            "decoded_duplicate_rejected": escaped_rejected,
        }
    elif tid == "CP-T20":
        original = deepcopy(view["source_assertions"])
        a = judge(view, "consumer-A", "0.800", "policy-A/1")
        b = judge(view, "consumer-B", "0.900", "policy-B/1")
        observations = {"A": a, "B": b, "source": view["source_assertions"]}
        checks = {
            "unchanged_source": original == view["source_assertions"],
            "separate_policy_results": not available
            or (a["result"] is True and b["result"] is False),
        }
        if not available:
            result, reason = (
                "QUALIFIED_LOSS",
                "Neither policy can evaluate the unavailable source score.",
            )
    else:
        raise ValueError("unknown scenario: " + tid)
    if not checks or not all(checks.values()):
        raise AssertionError((tid, representation, checks))
    return {
        "id": tid,
        "requirement": case["requirement"],
        "representation": representation,
        "class": result,
        "reason": reason,
        "checks": checks,
        "observations": observations,
        "consumer_view": view,
        "wire_sha256": digest(wire),
        "source_fixture": selected,
    }


def requirement_matrix(cases: list[dict]) -> list[dict]:
    """Summarize bounded questions; never promote tested behavior to full conformance."""
    rows = []
    for rep in REPRESENTATIONS:
        sample = next(c for c in cases if c["representation"] == rep and c["id"] == "CP-T03")
        available = sample["consumer_view"]["source_assertions"] is not None
        questions = [
            (
                "Native mapping-instance identity and history recoverable?",
                "UNESTABLISHED",
                "No native converter/profile/source-selection record; local binding probe is separately scoped.",
            ),
            (
                "Selected single B and available metric kept unambiguous?",
                "PRESERVED" if available else "UNESTABLISHED",
                "One explicit B; ambiguous multi-record selection and duplicates rejected."
                if available
                else "Only digest identity is visible; metric/task/attempt context is unavailable.",
            ),
            (
                "Execution / observation / non-assessment states transportable?",
                "UNESTABLISHED",
                "SER requires a comparison and has no execution-state enum; boundary cases cannot be encoded.",
            ),
            (
                "Exact score/comparator/threshold and explicit rounding kept separate?",
                "PRESERVED" if available else "QUALIFIED_LOSS",
                "P2 exact false comparison remains separate from true rounded display; units/uncertainty absent, not inferred."
                if available
                else "Digest alone omits numeric values and transformation interpretation.",
            ),
            (
                "Source/later judgment separation AND pre-run criterion ordering established?",
                "UNESTABLISHED",
                "Later judgments stay separate when B is available; criteria_digest/timestamp do not establish ordering.",
            ),
            (
                "Population and known retry/attempt qualifications recoverable?",
                "QUALIFIED_LOSS",
                "Only reported n; supplied record/retry/exclusion context has no native field. Full population unknown.",
            ),
            (
                "Declared identity strength retained without claiming executed identity?",
                "PRESERVED" if available else "QUALIFIED_LOSS",
                "Names and salted identifier commitments retained as declarations; executed model/corpus/config unestablished."
                if available
                else "Digest-only citation carries no suite or model/dataset identity declarations.",
            ),
            (
                "General source evidence availability/qualification recoverable?",
                "UNESTABLISHED",
                "No general evidence-reference/access field; B availability and digest recomputation are separately scoped.",
            ),
            (
                "Known earlier loss and amendment link survive in the carrier?",
                "QUALIFIED_LOSS",
                "Earlier partial/excluded context and amendment links are absent; later test authentication cannot restore them.",
            ),
            (
                "Typed checks and bounded unsupported consumption stay separate?",
                "PRESERVED",
                "Digest match, local test MAC and semantic support stay distinct; SER signature remains NOT_EVALUATED.",
            ),
            (
                "Actual downstream decision transported?",
                "NOT_APPLICABLE",
                "No reliance event supplied; successful export produces no decision/control assertion.",
            ),
            (
                "This local supported basis and negative behavior explicitly versioned?",
                "PRESERVED",
                "Exact draft/profile/implementation/fixture hashes recorded; unknown basis refuses semantics. Local evidence only.",
            ),
        ]
        for number, (question, result, reason) in enumerate(questions, 1):
            relevant = [
                c
                for c in cases
                if c["requirement"] == f"R-CP-{number}" and c["representation"] == rep
            ]
            if not relevant or not all(all(c["checks"].values()) for c in relevant):
                raise AssertionError("missing or failed probes")
            rows.append(
                {
                    "requirement": f"R-CP-{number}",
                    "representation": rep,
                    "question": question,
                    "class": result,
                    "reason": reason,
                    "scenarios": [c["id"] for c in relevant],
                }
            )
    return rows


def generate() -> dict:
    """Return deterministic measured outputs and their exact input hashes."""
    scenarios = json.loads((ROOT / "fixtures/scenarios.json").read_bytes())
    cases = [run_case(c, rep) for rep in REPRESENTATIONS for c in scenarios]
    matrix = requirement_matrix(cases)
    inputs = {}
    for directory in ("src", "tests", "fixtures", "sources"):
        for path in sorted((ROOT / directory).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                inputs[str(path.relative_to(ROOT))] = digest(path.read_bytes())
    inputs["mapping_profile.json"] = digest((ROOT / "mapping_profile.json").read_bytes())
    return {
        "profile": VERSION,
        "scope": "local semantic probes, NOT full requirement conformance",
        "input_sha256": inputs,
        "matrix_counts": dict(sorted(Counter(x["class"] for x in matrix).items())),
        "scenario_counts": dict(sorted(Counter(x["class"] for x in cases).items())),
        "matrix": matrix,
        "scenarios": cases,
        "crypto": {
            "SER_Ed25519": "NOT_EVALUATED",
            "COSE_SCITT": "NOT_EVALUATED",
            "local_test_HMAC": "executed for CP-T12 and CP-T13 only",
        },
    }


def markdown(data: dict) -> str:
    """Render the reproducible measured matrix and case results."""
    lines = [
        "# Results — NON-NORMATIVE local mapping experiment",
        "",
        "This is a same-author implementation experiment against CP-00, SER-04 and mappings-04. "
        "It does not establish independent interoperability, full CP/SER conformance, event truth, "
        "model safety, complete populations, trusted identity, or endorsement/adoption. EQR-05 is context only.",
        "",
        "All 12 requirements have bounded questions below; all 20 Appendix A scenarios run through "
        "four routes (80 scenario-route observations). Native-domain boundary probes and missing "
        "reliance events are explicitly NOT_APPLICABLE, not successful native mappings.",
        "",
        "**48 matrix cells:** "
        + ", ".join(f"{k}={v}" for k, v in data["matrix_counts"].items())
        + ".",
        "**80 scenario-route results:** "
        + ", ".join(f"{k}={v}" for k, v in data["scenario_counts"].items())
        + ".",
        "",
        "Labels apply to the stated bounded question, not the whole normative requirement. "
        "Matrix judgments combine measured field visibility with the explicit native field limits; "
        "they are not a mechanical conformance verdict or an average of scenario labels.",
        "",
        "## Concrete losses and ambiguities",
        "",
        "1. **Coverage and history do not cross.** SER carries reported n but no population, retries, "
        "excluded-count or amendment/mapping-history fields. Three supplied records with two distinct "
        "B digests establish neither two nor three actual attempts. Later local MAC authentication "
        "leaves the lost partial/excluded qualification absent (CP-T06/07/12/16).",
        "2. **A digest-only route cannot supply payload semantics.** Without the cited receipt bytes, "
        "the typed reference is Unresolved/unavailable and matching is INDETERMINATE. Score, threshold "
        "and identity commitments are unavailable. Providing a matching receipt restores access to B, "
        "not signature/key verification or qualifications lost before B (CP-T03/08/09/11/20).",
        "3. **Comparison and execution are different.** SER cannot encode no-criterion completion or "
        "did-not-run/invalid/not-evaluated states. P2 reports score 0.762, threshold 0.800, passed=false; "
        "rounding to one decimal gives 0.8 and a true presentation comparison. The source assertion "
        "remains false; no execution status is inferred (CP-T01/02/05/08).",
        "",
        "## Requirement × representation matrix",
        "",
        "SER = direct receipt; DSSE = section 4.1 exact-payload envelope; DIGEST_ONLY = section 5.1 "
        "typed reference without candidate; DIGEST_RESOLVED = same reference with matching candidate. "
        "No live SCITT registration or COSE statement validation was performed.",
        "",
        "| CP requirement | Representation | Result | Bounded question and reason | Probes |",
        "|---|---|---|---|---|",
    ]
    for row in data["matrix"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["requirement"],
                    row["representation"],
                    row["class"],
                    row["question"] + " " + row["reason"],
                    ", ".join(row["scenarios"]),
                ]
            )
            + " |"
        )
    lines += [
        "",
        "## Scenario results",
        "",
        "| CP scenario | Representation | Result | Reason |",
        "|---|---|---|---|",
    ]
    for row in data["scenarios"]:
        lines.append(
            "| "
            + " | ".join([row["id"], row["representation"], row["class"], row["reason"]])
            + " |"
        )
    lines += [
        "",
        "## Verification limits",
        "",
        "The complete 66-vector public file and proofbundle fixture are byte-pinned and their receipt "
        "reconstruction is checked for equality. This is not a 66-vector cryptographic verification run. "
        "Selected external receipts and M1 exercise semantic carriage; mappings C1–C8 and R1–R16 "
        "exercise digest extraction/matching/reference states. Ed25519 and COSE/SCITT checks are "
        "NOT_EVALUATED. Published PASS/FAIL expectations remain external expectations. "
        "The two later-auth probes use an explicitly local, public-key-material-free symmetric HMAC "
        "test key, not an Ed25519 signature or independent evidence.",
        "",
        "Local context records for unsupported states, exclusions, evidence references and amendment "
        "links are marked author-constructed and NOT SER. They are used to expose missing carrier "
        "capacity, never read by consume() as hidden evidence. The internal analysis and binding "
        "records are not proposed wire formats or new normative requirements.",
        "",
        "A preserved declaration does not establish exact evaluator, harness, test/corpus bytes, "
        "model/configuration actually used, evaluator independence or an enforcement event. "
        "Reported criteria_digest is not recomputed without criteria bytes; timestamps do not "
        "establish criteria chronology. Binding hashes demonstrate local tuple consistency, not "
        "authentication or completeness of a loss inventory.",
        "",
        "Reproduce offline: `python3 experiments/ietf/claim-preservation/ser04/src/run.py --check`. "
        "Full machine-readable observations and input hashes are in `results.json`; source access "
        "times/hashes and environment are in SOURCE_PINS.json and run_record.json.",
    ]
    return "\n".join(lines) + "\n"
