"""Deterministic public test vectors; no approval store or executor is simulated.

Appendix A inputs: draft-gruszka-audit-decision-receipts-03 (K. Gruszka).
P1 inputs: draft-gruszka-signed-evaluation-receipts-04 (K. Gruszka).
Published test keys MUST NOT be used for real receipts.

For the IETF Code Components:
Copyright (c) 2026 IETF Trust and the persons identified as authors of the code.
All rights reserved.
Redistribution and use in source and binary forms, with or without modification,
is permitted pursuant to, and subject to the license terms contained in, the
Revised BSD License set forth in Section 4.c of the IETF Trust's Legal Provisions
Relating to IETF Documents (https://trustee.ietf.org/license-info).
Original document notices remain in sources/; see SOURCES.md.
"""

import base64
import copy
import hashlib
import json
import re
from pathlib import Path

import rfc8785
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from proofbundle import dsse
from proofbundle.decision import emit_decision_receipt
from proofbundle.outcome import emit_outcome_receipt

ROOT = Path(__file__).resolve().parent
GATE = Ed25519PrivateKey.from_private_bytes(
    bytes.fromhex("100fa92fa6464c141f791a96327f555c1c0cfbf3095af986537e50c3c4335f8c")
)
OBSERVER = Ed25519PrivateKey.from_private_bytes(
    bytes.fromhex("f03ad5b668ad225ea15fd9fd272fc8df84be59f467da86b0f2ad0a5ad26f4ddd")
)
GATE_PUB = GATE.public_key().public_bytes_raw()
OBSERVER_PUB = OBSERVER.public_key().public_bytes_raw()
SER_PUB = base64.b64decode("x7ppA99DtumHO/Au0M/gumSK8IwCzNwPiID92BSFbak=")
A1 = b"git push origin refs/heads/topic:refs/heads/topic\n"
A1X = b"git push --force origin refs/heads/topic:refs/heads/main\n"
A2 = b"gh pr merge 7 --repo acme/widgets --merge\n"
POL = b"example gate rules, revision 1\n"
A3 = rfc8785.dumps(
    {"body": "All required checks passed for 4f1c2a9.", "pull": 7, "repo": "acme/widgets"}
)
E3 = rfc8785.dumps(
    {
        "author": "agent-42-bot",
        "body": "All required checks passed for 4f1c2a9.",
        "id": 9001,
        "pull": 7,
    }
)


def digest(raw: bytes) -> dict:
    """Return a SHA-256 reference to exact bytes."""
    return {"sha256": hashlib.sha256(raw).hexdigest()}


def payload(envelope: dict) -> bytes:
    """Decode fixture payload bytes without reserialization."""
    return base64.b64decode(envelope["payload"], validate=True)


def predicate(envelope: dict) -> dict:
    """Read a locally generated fixture predicate, not an untrusted verifier input."""
    return json.loads(payload(envelope))["predicate"]


APPROVAL = rfc8785.dumps(
    {
        "actionDigest": digest(A1),
        "approvalId": "appr-001",
        "approvedAt": "2026-10-15T09:00:00Z",
        "approver": "user-123",
        "session": "sess-1",
        "validUntil": "2026-10-15T09:15:00Z",
    }
)


def ser_p1() -> tuple[bytes, bytes]:
    """Extract the exact published SER -04 P1 bytes (not a new SER validator)."""
    text = (ROOT / "sources/draft-gruszka-signed-evaluation-receipts-04.txt").read_text()
    block = text.split("A.2.1.  P1 (pass; expected PASS, step all)")[-1]
    block = block.split("A.2.2.  P2 (recorded-failure;")[0]
    body, receipt = block.split("B (hex):")[1].split("Receipt (hex):")

    def unhex(part: str) -> bytes:
        return bytes.fromhex("".join(re.findall(r"^   ([0-9a-f]+)$", part, re.MULTILINE)))

    return unhex(body), unhex(receipt)


def vectors() -> dict:
    """Emit Appendix A's seven envelopes through unmodified public APIs."""
    body, _ = ser_p1()
    p1 = {
        "schemaVersion": "0.1.0",
        "decisionId": "dec-0001",
        "decisionType": "preActionAuthorization",
        "decidedAt": "2026-10-15T09:00:05Z",
        "decisionMaker": {"id": "gate-1"},
        "agent": {"id": "agent-42"},
        "principal": {"id": "user-123"},
        "proposedAction": {
            "actionType": "git.push",
            "method": "write",
            "parametersDigest": digest(A1),
            "target": {
                "name": "https://git.example/acme/widgets refs/heads/topic",
                "uri": "https://git.example/acme/widgets",
            },
        },
        "inputSnapshot": [
            {"digest": digest(A1), "mediaType": "text/plain", "name": "approved bytes"},
            {
                "digest": digest(APPROVAL),
                "mediaType": "application/json",
                "name": "approval record",
            },
        ],
        "policyBoundary": {
            "bundleRevision": "1",
            "decisionPath": "outbound-gate/allow-write",
            "policyDigest": digest(POL),
            "policyEngine": "proofbundle-pilot/github-write",
            "policyId": "outbound-gate-rules",
        },
        "evidenceRefs": [],
        "decision": {"verdict": "ALLOW", "reasonCodes": ["user_approval"]},
        "notChecked": [
            {
                "field": "content",
                "impact": "an approved text can be wrong",
                "reason": "the gate does not judge whether the text is true",
            }
        ],
        "decisionChangeConditions": [
            {
                "conditionType": "ruleChange",
                "description": "a changed gate, mode or rule of the gate",
            }
        ],
        "privacy": {"rawInputsIncluded": False},
        "traceContext": {"parentId": "int-002", "traceId": "trace-abc"},
        "validity": {
            "audience": ["observer-1"],
            "expiresAt": "2026-10-15T09:05:05Z",
            "nonce": "dec-0001",
        },
    }
    p2 = copy.deepcopy(p1)
    p2.update(
        {
            "actionOutcome": {"outcomeRef": None, "performedAt": None, "status": "blocked"},
            "decidedAt": "2026-10-15T09:05:00Z",
            "decisionId": "dec-0002",
            "decision": {"verdict": "DENY", "reasonCodes": ["required_check_failed"]},
            "inputSnapshot": [
                {"digest": digest(A2), "mediaType": "text/plain", "name": "proposed bytes"}
            ],
            "validity": {
                "audience": ["observer-1"],
                "expiresAt": "2026-10-15T09:10:00Z",
                "nonce": "dec-0002",
            },
        }
    )
    p2["policyBoundary"]["decisionPath"] = "outbound-gate/deny-write"
    p2["proposedAction"].update(
        {
            "actionType": "github.merge",
            "parametersDigest": digest(A2),
            "target": {
                "name": "https://git.example/acme/widgets/pull/7",
                "uri": "https://git.example/acme/widgets/pull/7",
            },
        }
    )
    p2["traceContext"]["parentId"] = "int-003"
    p3 = copy.deepcopy(p1)
    p3.update(
        {
            "decidedAt": "2026-10-15T09:10:00Z",
            "decisionId": "dec-0003",
            "decision": {"verdict": "ALLOW", "reasonCodes": ["evidence_verified"]},
            "evidenceRefs": [{"digest": digest(body), "relation": "evaluationResult"}],
            "inputSnapshot": [
                {"digest": digest(A3), "mediaType": "application/json", "name": "approved bytes"}
            ],
            "validity": {
                "audience": ["observer-1"],
                "expiresAt": "2026-10-15T09:15:00Z",
                "nonce": "dec-0003",
            },
        }
    )
    p3["proposedAction"].update(
        {
            "actionType": "github.conversationComment",
            "parametersDigest": digest(A3),
            "target": {
                "name": "https://git.example/acme/widgets/pull/7",
                "uri": "https://git.example/acme/widgets/pull/7",
            },
        }
    )
    p3["traceContext"]["parentId"] = "int-004"
    envs = {
        "V1-good": emit_decision_receipt(p1, GATE),
        "V2-good": emit_decision_receipt(p2, GATE),
        "V3-decision": emit_decision_receipt(p3, GATE),
    }
    op = {
        "schemaVersion": "0.1.0",
        "outcomeId": "out-0001",
        "decisionRef": digest(payload(envs["V3-decision"])),
        "effectDigest": digest(E3),
        "executor": {"id": "forge:agent-42-bot"},
        "performedAt": "2026-10-15T09:10:02Z",
        "requestedActionDigest": digest(A3),
        "status": "executed",
    }
    envs["V3-good"] = emit_outcome_receipt(op, OBSERVER)
    bad_op = copy.deepcopy(op)
    bad_op.update({"decisionRef": digest(payload(envs["V1-good"])), "outcomeId": "out-0002"})
    envs["V3-bad"] = emit_outcome_receipt(bad_op, OBSERVER)
    envs["V1-bad"] = copy.deepcopy(envs["V1-good"])
    tampered = payload(envs["V1-good"]).replace(
        digest(A1)["sha256"].encode(), digest(A1X)["sha256"].encode()
    )
    envs["V1-bad"]["payload"] = base64.b64encode(tampered).decode()
    noncanonical = json.dumps(json.loads(payload(envs["V2-good"])), sort_keys=True).encode()
    envs["V2-bad"] = dsse.sign_envelope(
        noncanonical, GATE, payload_type="application/vnd.in-toto+json"
    )
    return envs
