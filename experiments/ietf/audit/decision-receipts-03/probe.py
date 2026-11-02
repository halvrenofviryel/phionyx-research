"""Measure released receipt APIs without manufacturing a relying-party runtime."""

import argparse
import base64
import datetime
import json
import subprocess
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

import rfc8785
from proofbundle import dsse
from proofbundle.decision import (
    emit_decision_receipt,
    resolve_evidence_ref,
    verify_decision_receipt,
)
from proofbundle.outcome import (
    detect_outcome_sequence_gaps,
    emit_outcome_receipt,
    validate_outcome_predicate,
    verify_outcome_receipt,
)
from proofbundle.signature import verify_ed25519_pinned

from fixtures import (
    A1,
    APPROVAL,
    GATE,
    GATE_PUB,
    OBSERVER,
    OBSERVER_PUB,
    SER_PUB,
    digest,
    payload,
    predicate,
    ser_p1,
    vectors,
)


def utc_epoch(text: str) -> int:
    """Use a fixed historical audit time, never an authorization time."""
    return int(datetime.datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp())


def verify_decision(envelope: dict, *, time: str = "2026-10-15T09:01:00Z", **kwargs) -> dict:
    """Invoke the released verifier with explicit byte/key/time expectations."""
    return verify_decision_receipt(
        envelope,
        GATE_PUB,
        strict=True,
        expected_audience="observer-1",
        expected_nonce=predicate(envelope)["validity"]["nonce"],
        require_derived_subject=True,
        now=utc_epoch(time),
        **kwargs,
    )


def verify_outcome(envelope: dict, decision: dict, **kwargs) -> dict:
    """Invoke public receipt verification; this is not full draft section 3.4."""
    return verify_outcome_receipt(
        envelope,
        OBSERVER_PUB,
        strict=True,
        expected_decision_ref=digest(payload(decision))["sha256"],
        decision_maker_id="gate-1",
        require_derived_subject=True,
        **kwargs,
    )


def approval_fixture_facts() -> dict:
    """Check this published fixture's bindings; do not implement an approval verifier."""
    approval = json.loads(APPROVAL)
    return {
        "classification": "LOCAL_FIXTURE_PREFLIGHT",
        "canonical_bytes": rfc8785.dumps(approval) == APPROVAL,
        "sha256": digest(APPROVAL)["sha256"],
        "action_digest_matches_fixture": approval["actionDigest"] == digest(A1),
        "identity": {key: approval[key] for key in ("approvalId", "actionDigest", "session")},
        "fixture_time_bounds": (
            approval["approvedAt"]
            <= "2026-10-15T09:00:05Z"
            <= "2026-10-15T09:01:00Z"
            < "2026-10-15T09:05:05Z"
            <= approval["validUntil"]
        ),
        "human_authentication": "NOT_EVALUATED: the approval fixture is unsigned",
        "package_approval_verifier": "NOT_EVALUATED: no approval-record input in receipt API",
    }


def ser_fixture_facts() -> dict:
    """Preflight the pinned P1 vector with public crypto, not a full SER profile check."""
    body, raw = ser_p1()
    receipt = json.loads(raw)
    claim = json.loads(body)
    return {
        "classification": "PUBLISHED_P1_FIXTURE_PREFLIGHT",
        "source_expected_result": "SER -04 Appendix A.2.1: PASS",
        "payload_sha256": digest(body)["sha256"],
        "receipt_sha256": digest(raw)["sha256"],
        "payload_matches_receipt": base64.b64decode(receipt["payload_b64"], validate=True) == body,
        "canonical_payload": rfc8785.dumps(claim) == body,
        "signature_ok": verify_ed25519_pinned(
            SER_PUB,
            base64.b64decode(receipt["signature"]["sig"], validate=True),
            dsse.pae("application/vnd.signed-evidence.eval-receipt+json", body),
        ),
        "score_consistent": claim["passed"]
        == (Decimal(claim["score"]) >= Decimal(claim["threshold"])),
        "full_SER_profile_verification": "NOT_EVALUATED: no SER-profile API found in 6.4.0",
        "evaluation_actually_ran": "UNOBSERVED",
    }


def sequence_scan(envelopes: list[dict]) -> list[dict]:
    """Serialize the actual public sequence check, scoped to supplied predicates."""
    scan = detect_outcome_sequence_gaps([predicate(e) for e in envelopes])
    return [
        {"executor_id": key[0], "run_id": key[1], **value} for key, value in sorted(scan.items())
    ]


def report_projection(value):
    """Mask only per-process origin tokens AFTER all upstream policy evaluation.

    The upstream CLI removes this field too (cli.py:_without_origin_token).
    No receipt, evidence digest, verdict, warning or null is changed. Serialized
    projections must never be passed back as authenticated verifier results.
    """
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if key == "verified_origin" and item is not None:
                if not isinstance(item, str) or len(item) != 64:
                    raise ValueError("unexpected upstream origin-token representation")
                int(item, 16)
                result[key] = "<PROCESS_LOCAL_TOKEN:64-hex>"
            else:
                result[key] = report_projection(item)
        return result
    if isinstance(value, list):
        return [report_projection(item) for item in value]
    return value


def collect() -> tuple[dict, dict, dict]:
    """Collect real API outputs and explicitly absent runtime observations."""
    envs = vectors()
    v1 = envs["V1-good"]
    raw = {"appendix_a": {}}
    for name in ("V1-good", "V1-bad", "V2-good", "V2-bad", "V3-decision"):
        time = {"V1": "09:01:00", "V2": "09:06:00", "V3": "09:11:00"}[name[:2]]
        raw["appendix_a"][name] = verify_decision(envs[name], time=f"2026-10-15T{time}Z")
    for name in ("V3-good", "V3-bad"):
        raw["appendix_a"][name] = verify_outcome(envs[name], envs["V3-decision"])

    baseline = {
        "schemaVersion": "0.1.0",
        "outcomeId": "local-baseline-01",
        "decisionRef": digest(payload(v1)),
        "executor": {"id": "observer-1"},
        "requestedActionDigest": digest(A1),
        "status": "executed",
        "performedAt": "2026-10-15T09:00:06Z",
        "effectDigest": digest(b"local synthetic effect bytes; no command executed\n"),
    }
    envs["baseline-outcome"] = emit_outcome_receipt(baseline, OBSERVER)
    raw["baseline"] = {
        "decision": verify_decision(v1),
        "outcome": verify_outcome(envs["baseline-outcome"], v1),
        "approval_fixture": approval_fixture_facts(),
    }
    raw["repeat_verification"] = [verify_decision(v1), verify_decision(v1)]

    unknown = predicate(v1)
    unknown["actionOutcome"] = {"status": "unknown", "performedAt": None, "outcomeRef": None}
    envs["unknown-decision"] = emit_decision_receipt(unknown, GATE)
    unknown_outcome = {**baseline, "status": "unknown"}
    raw["unknown"] = {
        "decision": verify_decision(envs["unknown-decision"]),
        "outcome_validation_errors": validate_outcome_predicate(unknown_outcome, strict=True),
        "timeout": "NOT_EVALUATED",
        "retry": "NOT_EVALUATED",
    }

    second = {**baseline, "outcomeId": "local-second-02", "performedAt": "2026-10-15T09:00:07Z"}
    envs["second-outcome"] = emit_outcome_receipt(second, OBSERVER)
    pair = [envs["baseline-outcome"], envs["second-outcome"]]
    raw["two_outcomes"] = {
        "verifications": [verify_outcome(e, v1) for e in pair],
        "local_inventory": {
            "distinct_outcome_payloads": len({digest(payload(e))["sha256"] for e in pair}),
            "distinct_decision_refs": len({predicate(e)["decisionRef"]["sha256"] for e in pair}),
            "classification": "LOCAL_INVENTORY_ONLY; not an upstream duplicate-execution verdict",
        },
        "public_sequence_scan_without_sequence": sequence_scan(pair),
    }
    numbered = []
    for seq, item in ((1, baseline), (3, second)):
        e = emit_outcome_receipt({**item, "sequence": {"runId": "local-run", "seq": seq}}, OBSERVER)
        envs[f"sequence-{seq}"] = e
        numbered.append(e)
    raw["sequence_control"] = {
        "verifications": [verify_outcome(e, v1) for e in numbered],
        "one_and_three": sequence_scan(numbered),
        "three_only": sequence_scan(numbered[1:]),
        "scope": "Only gaps between the supplied minimum and maximum; no population claim",
    }

    second_allow = predicate(v1)
    second_allow["decisionId"] = "local-second-allow"
    second_allow["validity"]["nonce"] = "local-second-allow"
    envs["second-allow"] = emit_decision_receipt(second_allow, GATE)
    raw["same_approval_two_allows"] = {
        "verifications": [verify_decision(v1), verify_decision(envs["second-allow"])],
        "local_inventory": {
            "consumption_scope": "local-fixtures-only; explicitly supplied by this harness",
            "distinct_decision_payloads": len(
                {digest(payload(v1))["sha256"], digest(payload(envs["second-allow"]))["sha256"]}
            ),
            "same_approval_bytes_referenced": (
                predicate(v1)["inputSnapshot"][1]
                == predicate(envs["second-allow"])["inputSnapshot"][1]
            ),
            "approval_identity": approval_fixture_facts()["identity"],
            "classification": "LOCAL_INVENTORY_ONLY; no released section-3.5 audit hook found",
        },
        "package_set_audit": "NOT_EVALUATED",
    }

    body, ser_raw = ser_p1()
    ref = {"relation": "evaluationResult", "digest": digest(body)}
    with_evidence = predicate(v1)
    with_evidence["evidenceRefs"] = [ref]
    with_evidence["decision"] = {"verdict": "DENY", "reasonCodes": ["required_check_failed"]}
    envs["deny-with-evaluation"] = emit_decision_receipt(with_evidence, GATE)
    policy = {
        "schema": "proofbundle/trust-policy/v0.2",
        "policy_id": "local-test-allow-only",
        "policyPurpose": "decision",
        "decision_receipt": {
            "trusted_decision_makers": [
                {"id": "gate-1", "public_key_b64": base64.b64encode(GATE_PUB).decode()}
            ],
            "allowed_decision_types": ["preActionAuthorization"],
            "allowed_verdicts": ["ALLOW"],
        },
    }

    def resolve(digest_object: dict) -> bool:
        return digest_object == digest(body)

    raw["evaluation_evidence"] = {
        "fixture_preflight": ser_fixture_facts(),
        "reference_resolution": resolve_evidence_ref(ref, evidence_payload=body),
        "wrong_content_control": resolve_evidence_ref(ref, evidence_payload=body + b"\n"),
        "deny_receipt": verify_decision(envs["deny-with-evaluation"], evidence_resolver=resolve),
        "deny_under_allow_only_policy": verify_decision(
            envs["deny-with-evaluation"], evidence_resolver=resolve, policy=policy
        ),
        "allow_policy_positive_control": verify_decision(v1, policy=policy),
        "ser_as_decision": verify_decision_receipt(
            json.loads(ser_raw), SER_PUB, strict=True, now=utc_epoch("2026-10-15T09:01:00Z")
        ),
        "recorded_verdict": predicate(envs["deny-with-evaluation"])["decision"]["verdict"],
    }

    names = [
        "Baseline approval -> ALLOW -> executed outcome",
        "Consumed approval presented again with state retained",
        "Rotation preserving required old state/digest",
        "Missing required consumption-state generation",
        "Reuse one ALLOW for two execution attempts",
        "Timeout with UNKNOWN/UNOBSERVED outcome followed by retry",
        "Two outcome receipts reference one ALLOW",
        "Two distinct ALLOW receipts cite the same approval identity",
        "Evaluation evidence is not authorization",
    ]
    observations = {
        1: "One ALLOW and one synthetic executed outcome verify; no action was run.",
        2: "No public consume/re-present hook; no behavior inferred.",
        3: "No public store/rotation/preservation hook; no behavior inferred.",
        4: "No public missing-generation hook; refusal vs indeterminate vs re-allow is unknown.",
        5: (
            "The same receipt verifies twice at the same audit time; "
            "these are not execution attempts."
        ),
        6: "Decision actionOutcome=unknown validates; outcome status=unknown is rejected by enum.",
        7: (
            "Both distinct outcomes verify against one decision. "
            "Unnumbered sequence scan returns no groups."
        ),
        8: (
            "Both distinct ALLOW payloads verify separately. "
            "Their identical approval fixture is visible."
        ),
        9: "P1 digest resolves; the decision stays DENY and is rejected by an ALLOW-only policy.",
    }
    raw_refs = {
        1: "baseline",
        5: "repeat_verification",
        6: "unknown",
        7: "two_outcomes",
        8: "same_approval_two_allows",
        9: "evaluation_evidence",
    }
    scenarios = []
    for number, name in enumerate(names, 1):
        unsupported = number in (2, 3, 4)
        record = {
            "id": f"S{number:02}",
            "scenario": name,
            "status": "NOT_EVALUATED" if unsupported else "PARTIALLY_EVALUATED",
            "approval_verification": {
                "status": "NOT_EVALUATED",
                "reason": (
                    "No package approval-record verifier; "
                    "unsigned fixture is not human authentication"
                ),
                "local_fixture_preflight": "api_results.json:baseline.approval_fixture"
                if not unsupported
                else None,
            },
            "approval_consumption_state": {
                "status": "NOT_EVALUATED",
                "reason": "No released durable consume/store/rotation API found",
            },
            "decision_receipt_validity": {
                "status": "NOT_EVALUATED" if unsupported else "MEASURED_API_SUBSET",
                "result_ref": None if unsupported else f"api_results.json:{raw_refs[number]}",
                "limit": (
                    "Package receipt verification is not full draft sections 3.2/3.3 conformance"
                ),
            },
            "outcome_receipt_validity": {
                "status": "MEASURED_API_SUBSET"
                if number in (1, 7)
                else ("MEASURED_ENUM_REJECTION" if number == 6 else "NOT_EVALUATED"),
                "result_ref": (
                    f"api_results.json:{raw_refs[number]}" if number in (1, 6, 7) else None
                ),
                "limit": (
                    "No actual effect, full cross-record temporal check, "
                    "or independent observer established"
                ),
            },
            "set_level_audit_finding": {
                "status": "NOT_EVALUATED",
                "reason": "No released section-3.5 duplicate-approval auditor found",
                "supplement": "api_results.json:two_outcomes and sequence_control"
                if number == 7
                else (
                    "api_results.json:same_approval_two_allows.local_inventory"
                    if number == 8
                    else None
                ),
            },
            "execution_observation_state": {
                "status": "UNOBSERVED",
                "runtime_probe": "NOT_EVALUATED",
                "reason": "No executor or Agent Guard was run; receipt assertions are synthetic",
            },
            "effect_observation_state": {
                "status": "UNOBSERVED",
                "reason": "No external effect-observation channel was exercised",
            },
            "observed_behavior": observations[number],
            "does_not_establish": [
                "human approval authenticity or durable consumption",
                "at-most-once authorization or at-most-once execution",
                "that a recorded executed effect occurred",
                "that a timeout means execution failed",
                "completeness beyond supplied records or operational independence of signing keys",
                "Agent Guard preview behavior or historical -00 execution observations",
            ],
        }
        scenarios.append(record)
    report = {
        "target_draft": "draft-gruszka-audit-decision-receipts-03",
        "implementation": "proofbundle==6.4.0, unmodified PyPI wheel",
        "scenario_count": len(scenarios),
        "status_counts": dict(Counter(s["status"] for s in scenarios)),
        "runtime_scenarios_executed": 0,
        "scenarios": scenarios,
    }
    return raw, report, envs


def write_report(output: Path) -> None:
    """Write deterministic API outputs and the scenario evidence matrix."""
    raw, report, envs = collect()
    output.mkdir(parents=True, exist_ok=True)
    projected = report_projection(raw)
    projected["_serialization"] = {
        "normalization": "Only non-null verified_origin tokens replaced after all API calls",
        "reason": (
            "Upstream HMAC origin tokens are process-local, not reproducible receipt evidence"
        ),
        "raw_original": (
            "evidence/api_results.original.json (archived original run, not replay input)"
        ),
    }
    for name, content in (("api_results.json", projected), ("scenario_results.json", report)):
        (output / name).write_text(json.dumps(content, indent=2, sort_keys=True) + "\n")
    fixture_dir = output / "fixtures"
    fixture_dir.mkdir(exist_ok=True)
    for name, content in sorted(envs.items()):
        (fixture_dir / f"{name}.json").write_text(
            json.dumps(content, indent=2, sort_keys=True) + "\n"
        )
    body, receipt = ser_p1()
    (fixture_dir / "SER-P1.payload.json").write_bytes(body)
    (fixture_dir / "SER-P1.receipt.json").write_bytes(receipt)
    (fixture_dir / "approval.json").write_bytes(APPROVAL)
    cli = []
    for name in ("V1-good", "V1-bad", "V2-good", "V2-bad", "V3-decision", "V3-good", "V3-bad"):
        outcome = name in ("V3-good", "V3-bad")
        args = [
            "outcome" if outcome else "decision",
            "verify",
            f"fixtures/{name}.json",
            "--pub",
            base64.b64encode(OBSERVER_PUB if outcome else GATE_PUB).decode(),
            "--strict",
            "--json",
        ]
        if outcome:
            args += [
                "--expected-decision-ref",
                digest(payload(envs["V3-decision"]))["sha256"],
                "--decision-maker-id",
                "gate-1",
            ]
        else:
            time = {"V1": "09:01:00", "V2": "09:06:00", "V3": "09:11:00"}[name[:2]]
            args += [
                "--aud",
                "observer-1",
                "--nonce",
                predicate(envs[name])["validity"]["nonce"],
                "--verification-time",
                f"2026-10-15T{time}Z",
            ]
        result = subprocess.run(
            [str(Path(sys.executable).with_name("proofbundle")), *args],
            cwd=output,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        cli.append(
            {
                "vector": name,
                "command": ["proofbundle", *args],
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        )
    (output / "cli_results.json").write_text(json.dumps(cli, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    write_report(parser.parse_args().output)
