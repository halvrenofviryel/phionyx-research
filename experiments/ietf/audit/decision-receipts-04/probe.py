"""Generate -04 A.5 failure fixtures and measure the released CLI, not a runtime.

IETF Code Components: draft-gruszka-audit-decision-receipts-04, K. Gruszka.
Copyright (c) 2026 IETF Trust and the persons identified as authors of the code.
All rights reserved. Redistribution and use in source and binary forms, with or
without modification, is permitted pursuant to, and subject to the license terms
contained in, the Revised BSD License set forth in Section 4.c of the IETF Trust's
Legal Provisions Relating to IETF Documents (https://trustee.ietf.org/license-info).
Published test keys MUST NOT be used for real receipts.
"""

import argparse
import base64
import copy
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import rfc8785
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from proofbundle import dsse

ROOT = Path(__file__).resolve().parent
OLD = ROOT.with_name("decision-receipts-03")
BASE_NAMES = ("V1-good", "V1-bad", "V2-good", "V2-bad", "V3-decision", "V3-good", "V3-bad")
GATE = Ed25519PrivateKey.from_private_bytes(
    bytes.fromhex("100fa92fa6464c141f791a96327f555c1c0cfbf3095af986537e50c3c4335f8c")
)
OBSERVER = Ed25519PrivateKey.from_private_bytes(
    bytes.fromhex("f03ad5b668ad225ea15fd9fd272fc8df84be59f467da86b0f2ad0a5ad26f4ddd")
)
TIMES = {
    1: "09:01:00",
    2: "09:06:00",
    3: "09:06:00",
    4: "09:05:05",
    5: "09:06:00",
    6: "09:11:00",
    7: "09:11:00",
    8: "09:11:00",
    9: "09:16:00",
    10: "09:21:00",
}
BASE_FOR = {
    1: "V1-good",
    2: "V2-good",
    3: "V2-good",
    4: "V1-good",
    5: "V2-good",
    6: "V3-good",
    7: "V3-good",
    8: "V3-good",
    9: "V1-good",
    10: "V1-good",
}
CHECKS = {
    1: "3.2 step 7",
    2: "3.2 step 7",
    3: "3.2 step 8",
    4: "3.2 step 9",
    5: "3.2 step 10",
    6: "3.4 step 5",
    7: "3.4 step 6",
    8: "3.4 step 7",
    9: "3.3 Case 1",
    10: "4 (relying party, after receipt verification)",
}
EXPLANATIONS = {
    1: "agent is null instead of a required object",
    2: "policyBoundary.validFrom uses +00:00 rather than trailing Z",
    3: "decisionMaker.id is gate-2 but expected identity for the pinned key is gate-1",
    4: "T equals expiresAt; expiry comparison is strict",
    5: "supplied action a1 does not match the digest of a2 in V2-good",
    6: "executor.id differs from the expected forge:agent-42-bot",
    7: "effect bytes e3 are supplied but effectDigest is absent (status is refused)",
    8: "performedAt is earlier than V3-decision.decidedAt",
    9: "receipt expiresAt exceeds ap.validUntil; approval is also expired at T",
    10: "author supplies c1 as prior consumed state; no consumption hook is exercised here",
}


def sha(raw: bytes) -> str:
    """Hash exact bytes."""
    return hashlib.sha256(raw).hexdigest()


def payload(envelope: dict) -> bytes:
    """Decode the envelope without repairing its payload."""
    return base64.b64decode(envelope["payload"], validate=True)


def draft_text() -> str:
    """Remove pagination only for reading definitions; keep raw source untouched."""
    raw = (ROOT / "sources/draft-gruszka-audit-decision-receipts-04.txt").read_text()
    return "\n".join(
        line for line in raw.splitlines() if not line.startswith(("Gruszka ", "Internet-Draft "))
    )


def published_expectations() -> dict:
    """Read eight new payload/signature pins from the frozen A.5 text."""
    section = draft_text().split("\nA.5.  Failure Vectors\n", 1)[1]
    compact = " ".join(section.split())
    pattern = (
        r"(F\d+), T (\S+), fails at (.*?), exit ([0-9]+) "
        r"(\d+) bytes, signed by ([\w-]+) ([0-9a-f]{64}) "
        r"([A-Za-z0-9+/=]{44}) ([A-Za-z0-9+/=]{44})"
    )
    result = {}
    for name, time, check, code, size, signer, digest, sig1, sig2 in re.findall(pattern, compact):
        result[name] = {
            "time": time,
            "first_failing_check": check,
            "cli_exit_author_reported": int(code),
            "payload_bytes": int(size),
            "signer": signer,
            "payload_sha256": digest,
            "signature_b64": sig1 + sig2,
        }
    if len(result) != 8:
        raise ValueError(f"expected eight novel A.5 payload definitions, found {len(result)}")
    return result


def inputs() -> dict[str, bytes]:
    """Create exact A.1/A.5 inputs; c1 is inert bytes, never an enforcement store."""
    approval = (OLD / "cases/fixtures/approval.json").read_bytes()
    ap = json.loads(approval)
    ap2 = {**ap, "validUntil": "2026-10-15T09:30:00Z"}
    c1 = [{key: ap[key] for key in ("actionDigest", "approvalId", "session")}]
    return {
        "a1.txt": b"git push origin refs/heads/topic:refs/heads/topic\n",
        "a2.txt": b"gh pr merge 7 --repo acme/widgets --merge\n",
        "ap.json": approval,
        "ap2.json": rfc8785.dumps(ap2),
        "c1.json": rfc8785.dumps(c1),
        "e3.json": rfc8785.dumps(
            {
                "author": "agent-42-bot",
                "body": "All required checks passed for 4f1c2a9.",
                "id": 9001,
                "pull": 7,
            }
        ),
    }


def sign_statement(statement: dict, *, outcome: bool = False) -> dict:
    """Sign intentionally invalid as well as valid fixtures using public DSSE.

    Recompute the subject exactly as A.2 says. No high-level producer validation
    is claimed, and no upstream validator is modified to admit negative fixtures.
    """
    statement = copy.deepcopy(statement)
    pred = statement["predicate"]
    name = ("outcome:" + pred["outcomeId"]) if outcome else ("decision:" + pred["decisionId"])
    statement["subject"] = [{"name": name, "digest": {"sha256": sha(rfc8785.dumps(pred))}}]
    return dsse.sign_envelope(
        rfc8785.dumps(statement),
        OBSERVER if outcome else GATE,
        payload_type="application/vnd.in-toto+json",
    )


def generate() -> tuple[dict, dict, list]:
    """Apply exactly the A.5 mutations to the seven unchanged base envelopes."""
    bases = {
        name: json.loads((OLD / f"cases/fixtures/{name}.json").read_bytes()) for name in BASE_NAMES
    }
    source_a3 = draft_text().split("\nA.3.  Results\n", 1)[1].split("\nA.4.", 1)[0]
    compact_a3 = "".join(source_a3.split())
    compatibility = []
    for name, envelope in bases.items():
        raw = payload(envelope)
        digest = sha(raw)
        signature = envelope["signatures"][0]["sig"]
        if digest not in source_a3 or signature not in compact_a3:
            raise ValueError(f"frozen -03 base {name} is not the -04 A.3 payload/signature")
        compatibility.append(
            {
                "vector": name,
                "payload_bytes": len(raw),
                "payload_sha256": digest,
                "signature_b64": signature,
                "matches_04_A3": True,
                "seven_vector_suite_rerun": False,
            }
        )
    envs = {}
    for number in range(1, 11):
        original = bases[BASE_FOR[number]]
        if number in (4, 5):
            envs[f"F{number}"] = copy.deepcopy(original)
            continue
        statement = json.loads(payload(original))
        p = statement["predicate"]
        if number == 1:
            p["agent"] = None
        elif number == 2:
            p["policyBoundary"]["validFrom"] = "2026-10-15T09:00:00+00:00"
        elif number == 3:
            p["decisionMaker"]["id"] = "gate-2"
        elif number == 6:
            p["executor"]["id"] = "forge:another-actor"
        elif number == 7:
            p["status"] = "refused"
            del p["effectDigest"]
        elif number == 8:
            p["performedAt"] = "2026-10-15T09:09:59Z"
        elif number == 9:
            p["validity"]["expiresAt"] = "2026-10-15T10:00:00Z"
        elif number == 10:
            p.update(decidedAt="2026-10-15T09:20:00Z", decisionId="dec-0004")
            p["inputSnapshot"][1]["digest"]["sha256"] = sha(inputs()["ap2.json"])
            p["validity"].update(expiresAt="2026-10-15T09:25:00Z", nonce="dec-0004")
        envs[f"F{number}"] = sign_statement(statement, outcome=number in (6, 7, 8))
    for name, expected in published_expectations().items():
        raw = payload(envs[name])
        assert len(raw) == expected["payload_bytes"], name
        assert sha(raw) == expected["payload_sha256"], name
        assert envs[name]["signatures"][0]["sig"] == expected["signature_b64"], name
    return envs, bases, compatibility


def cli_call(
    output: Path, file: str, envelope: dict, *, outcome: bool, time: str, decision_ref: str
) -> dict:
    """Run the real CLI on file bytes; duplicate JSON names reach its own reader."""
    key = OBSERVER if outcome else GATE
    pub = base64.b64encode(key.public_key().public_bytes_raw()).decode()
    args = [
        "outcome" if outcome else "decision",
        "verify",
        file,
        "--pub",
        pub,
        "--strict",
        "--json",
    ]
    if outcome:
        args += ["--expected-decision-ref", decision_ref, "--decision-maker-id", "gate-1"]
    else:
        nonce = json.loads(payload(envelope))["predicate"]["validity"]["nonce"]
        args += ["--aud", "observer-1", "--nonce", nonce, "--verification-time", time]
    result = subprocess.run(
        [str(Path(sys.executable).with_name("proofbundle")), *args],
        cwd=output,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    return {
        "command": ["proofbundle", *args],
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def controls(bases: dict) -> list[dict]:
    """Four small raw-envelope/field controls plus two positive counterparts."""
    base = bases["V1-good"]
    raw = json.dumps(base, separators=(",", ":"))
    root_duplicate = '{"payload":' + json.dumps(base["payload"]) + "," + raw[1:]
    keyid = base["signatures"][0]["keyid"]
    nested_duplicate = raw.replace(
        '"keyid":' + json.dumps(keyid),
        '"keyid":' + json.dumps(keyid) + ',"keyid":' + json.dumps(keyid),
        1,
    )
    result = [
        {
            "id": "C01",
            "description": "duplicate root payload member (identical values)",
            "bytes": root_duplicate.encode(),
            "envelope": base,
            "draft_expected": "REJECT at 3.2 step 1",
        },
        {
            "id": "C02",
            "description": "duplicate nested signature keyid member (identical values)",
            "bytes": nested_duplicate.encode(),
            "envelope": base,
            "draft_expected": "REJECT at 3.2 step 1",
        },
    ]
    for name, value in (("C03", "false"), ("C04", 0)):
        statement = json.loads(payload(base))
        statement["predicate"]["privacy"]["rawInputsIncluded"] = value
        env = sign_statement(statement)
        result.append(
            {
                "id": name,
                "description": f"rawInputsIncluded={value!r} (not JSON boolean)",
                "bytes": rfc8785.dumps(env),
                "envelope": env,
                "draft_expected": "REJECT at 3.2 step 7 / 3.8 boolean type",
            }
        )
    for name, vector in (("P01", "V1-good"), ("P02", "V3-good")):
        result.append(
            {
                "id": name,
                "description": f"positive CLI control: {vector}",
                "bytes": rfc8785.dumps(bases[vector]),
                "envelope": bases[vector],
                "draft_expected": "PASS under Appendix A.3 stated inputs",
            }
        )
    return result


def write_report(output: Path) -> None:
    """Freeze measurements and author expectations in separate report fields."""
    output.mkdir(parents=True, exist_ok=True)
    (output / "fixtures").mkdir(exist_ok=True)
    (output / "inputs").mkdir(exist_ok=True)
    envs, bases, compatibility = generate()
    data = inputs()
    for name, raw in data.items():
        (output / "inputs" / name).write_bytes(raw)
    ref = sha(payload(bases["V3-decision"]))
    rows = []
    for number in range(1, 11):
        name = f"F{number}"
        env = envs[name]
        body = payload(env)
        raw = (
            (OLD / f"cases/fixtures/{BASE_FOR[number]}.json").read_bytes()
            if number in (4, 5)
            else rfc8785.dumps(env)
        )
        file = f"fixtures/{name}.envelope.json"
        (output / file).write_bytes(raw)
        (output / f"fixtures/{name}.payload.json").write_bytes(body)
        outcome = number in (6, 7, 8)
        time = "2026-10-15T" + TIMES[number] + "Z"
        expected_inputs = {
            "evaluation_time": time,
            "expected_decisionMaker.id": "gate-1",
            "expected_executor.id": "forge:agent-42-bot" if outcome else None,
            "decision_ref": ref if outcome else None,
            "action_bytes": None if outcome else ("a2.txt" if number in (2, 3) else "a1.txt"),
            "effect_bytes": "e3.json" if outcome else None,
            "approval_bytes": ("ap2.json" if number == 10 else "ap.json")
            if number in (1, 4, 9, 10)
            else None,
            "consumption_state_bytes": "c1.json" if number == 10 else None,
            "expected_audience": None if outcome else "observer-1",
            "expected_nonce": None if outcome else json.loads(body)["predicate"]["decisionId"],
        }
        rows.append(
            {
                "id": name,
                "base_vector": BASE_FOR[number],
                "definition": EXPLANATIONS[number],
                "payload_bytes": len(body),
                "payload_sha256": sha(body),
                "envelope_sha256": sha(raw),
                "signature_b64": env["signatures"][0]["sig"],
                "signature_verified": dsse.verify_envelope(
                    env,
                    (OBSERVER if outcome else GATE).public_key().public_bytes_raw(),
                    payload_type="application/vnd.in-toto+json",
                ),
                "expected_inputs_for_draft_procedure": expected_inputs,
                "draft_expectation": {
                    "provenance": "AUTHOR_SPECIFIED, Appendix A.5; not a local full draft verifier",
                    "receipt_procedure": "PASS" if number == 10 else "REJECT",
                    "relying_party": "REFUSE" if number == 10 else "NOT_APPLICABLE",
                    "first_failing_check": CHECKS[number],
                    "author_reported_cli_exit": 2 if number in (1, 2, 4) else 0,
                },
                "measured_cli": cli_call(
                    output, file, env, outcome=outcome, time=time, decision_ref=ref
                ),
                "consumption_enforcement": "NOT_EVALUATED" if number == 10 else "NOT_APPLICABLE",
                "full_draft_procedure_execution": "NOT_EVALUATED",
                "scope_limit": (
                    "No action/effect bytes, approval or consumption inputs in these commands. "
                    "No expected decisionMaker.id policy is supplied; "
                    "outcome --decision-maker-id "
                    "checks inequality, not expected executor.id. No full cross-record time check."
                ),
            }
        )
    control_rows = []
    for control in controls(bases):
        file = f"fixtures/{control['id']}.envelope.json"
        (output / file).write_bytes(control["bytes"])
        control_rows.append({k: v for k, v in control.items() if k not in ("bytes", "envelope")})
        control_rows[-1].update(
            {
                "envelope_sha256": sha(control["bytes"]),
                "measured_cli": cli_call(
                    output,
                    file,
                    control["envelope"],
                    outcome=control["id"] == "P02",
                    time="2026-10-15T09:01:00Z",
                    decision_ref=ref,
                ),
            }
        )
    report = {
        "target": "draft-gruszka-audit-decision-receipts-04",
        "package": "proofbundle==6.4.0",
        "vectors": rows,
        "controls": control_rows,
        "input_hashes": {
            name: {"bytes": len(raw), "sha256": sha(raw)} for name, raw in data.items()
        },
        "base_compatibility": compatibility,
        "SCITT_A4": "NOT_EVALUATED: source delta only; no COSE or transparency verification",
        "runtime_execution": "NOT_EVALUATED",
        "effect_observation": "UNOBSERVED",
    }
    (output / "results.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    write_report(parser.parse_args().output)
