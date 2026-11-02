"""Bounded synthetic CMP appraisal; stdlib only, with no project imports.

Authority, identity and authentication are stipulated fixture facts. This is
an offline set-reconciliation experiment, not a verifier for real attestations.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

PROFILE = "synthetic-finite-counterparty-v1"
OUTCOMES = ("SATISFIED", "UNSATISFIED", "INDETERMINATE", "NOT_EVALUATED")


def digest(value: Any) -> str:
    """Hash canonical local fixture JSON; this is not a wire encoding."""
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def instant(value: str) -> datetime:
    """Parse a timezone-aware instant, rejecting naive timestamps."""
    if not isinstance(value, str):
        raise ValueError("string timestamp required")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timezone required")
    return parsed


def contains(outer: dict, inner: dict) -> bool:
    """Check containment of nonempty half-open time windows."""
    try:
        return (
            instant(outer["start"])
            <= instant(inner["start"])
            < instant(inner["end"])
            <= instant(outer["end"])
        )
    except (KeyError, TypeError, ValueError):
        return False


def control(evidence: dict | None, material: list[str]) -> str:
    """Classify operation and input selection using explicit fixture roles."""
    if not evidence or not evidence.get("operator") or not evidence.get("input_selectors"):
        return "UNKNOWN"
    if evidence["operator"] in material or set(evidence["input_selectors"]) & set(material):
        return "MATERIAL_PARTY_CONTROL"
    return "NON_MATERIAL_CONTROL"


def evidence_summary(data: dict) -> list[dict]:
    """Retain references, digests and carried times of supplied fixture evidence."""
    items = []
    for key in ("disclosed", "mechanism", "basis", "authority", "run_binding", "plan"):
        value = data.get(key)
        if value is None:
            continue
        item = {"input_path": key, "sha256": digest(value)}
        if isinstance(value, dict):
            for name in ("id", "issued_at", "expires_at"):
                if name in value:
                    item[name] = value[name]
        items.append(item)
    return items


def predicate(data: dict, completeness: str) -> dict:
    """Keep a disclosed at-most-once predicate separate from completeness."""
    if data.get("predicate") != "at_most_once":
        return {"result": "NOT_EVALUATED", "reason": "No predicate requested."}
    records = data.get("disclosed", [])
    known = {
        r["occurrence_id"]
        for r in records
        if r.get("authentication") == "stipulated_valid" and r.get("occurrence_id")
    }
    if len(known) > 1:
        result = "UNSATISFIED"
    elif completeness == "SATISFIED" and all(
        r.get("authentication") == "stipulated_valid" and r.get("occurrence_id") for r in records
    ):
        result = "SATISFIED"
    else:
        result = "INDETERMINATE"
    return {
        "result": result,
        "known_disclosed_occurrences": sorted(known),
        "reason": "Only stipulated-authenticated disclosed occurrences counted; "
        "no scenario truth or signature inference.",
    }


def appraise(data: dict, replay_at: str) -> dict:
    """Appraise only evaluator-visible input under the documented local policy."""
    instant(replay_at)
    claim = data.get("claim") or {}
    domain = claim.get("domain")
    mechanism = data.get("mechanism")
    basis = data.get("basis")
    authority = data.get("authority") or {}
    binding = data.get("run_binding") or {}
    plan = data.get("plan") or {}
    material = claim.get("material_parties", [])
    output = {
        "result": None,
        "coverage_domain": domain,
        "coverage_qualification": claim.get("qualification"),
        "omission_detection_basis": {
            "mechanism_id": (mechanism or {}).get("id"),
            "basis_id": (basis or {}).get("id"),
            "kind": (basis or {}).get("kind"),
            "state_version": (basis or {}).get("state_version"),
            "appraisal_checks": [],
        },
        "material_party_control": {
            "material_parties": material,
            "mechanism": control(mechanism, material),
            "basis": control(basis, material),
            "assurance": "Stipulated synthetic roles; not externally verified.",
        },
        "evidence_present": evidence_summary(data),
        "missing_or_unavailable_inputs": [],
        "requirement_ids": ["CMP-1", "CMP-2", "OUTCOME-4", "OUTCOME-TIME"],
        "diagnostics": [],
        "record_produced_at": replay_at,
        "capability_context": {
            "declared_capability": plan.get("capability", "UNKNOWN"),
            "attempt_requested": plan.get("attempt"),
            "evidence_ref": "plan" if plan else None,
            "resolver_status": plan.get("resolver_status", "UNKNOWN"),
        },
    }

    def finish(result: str, code: str, detail: str, missing: str | None = None) -> dict:
        output["result"] = result
        output["diagnostics"].append({"code": code, "detail": detail})
        if missing:
            output["missing_or_unavailable_inputs"].append(missing)
        if result != "NOT_EVALUATED":
            output["check_performed_at"] = replay_at
        output["predicate_result"] = predicate(data, result)
        return output

    def check(name: str, passed: bool, refs: list[str]) -> bool:
        output["omission_detection_basis"]["appraisal_checks"].append(
            {"check": name, "passed": bool(passed), "evidence_refs": refs}
        )
        return bool(passed)

    if claim.get("kind") in (None, "none"):
        return finish("NOT_EVALUATED", "C_NO_CLAIM", "No completeness claim to appraise.")
    if plan.get("attempt") is False:
        return finish("NOT_EVALUATED", "C_SKIPPED", "Evaluation plan explicitly skipped check.")
    if claim.get("kind") != "complete" or data.get("profile") != PROFILE:
        return finish("INDETERMINATE", "C_PROFILE", "Unsupported local claim/profile.", "profile")
    if plan.get("capability") != "SUPPORTED":
        return finish(
            "INDETERMINATE",
            "C_CAPABILITY",
            "Capability unavailable or unknown; see explicit plan evidence.",
            "plan.capability",
        )
    if plan.get("attempt") is not True:
        return finish("INDETERMINATE", "C_PLAN", "Attempt plan not established.", "plan.attempt")
    if not domain or not domain.get("id") or not domain.get("population"):
        return finish(
            "INDETERMINATE", "C_DOMAIN", "Claimed domain is not identified.", "claim.domain"
        )
    if not check(
        "finite_domain",
        domain.get("closure") == "closed"
        and contains(domain.get("window", {}), domain.get("window", {})),
        ["claim.domain"],
    ):
        return finish(
            "INDETERMINATE",
            "C_DOMAIN_UNCLOSED",
            "Domain not closed under local policy.",
            "closed coverage domain and window",
        )
    if not mechanism or not mechanism.get("id"):
        return finish("INDETERMINATE", "C_MECHANISM", "No omission detector named.", "mechanism")
    if plan.get("resolver_status") != "AVAILABLE":
        return finish(
            "INDETERMINATE",
            "C_RESOLVER",
            "Index lookup unavailable; no negative lookup or missing capability is inferred.",
            "resolved independent index",
        )
    if not basis:
        return finish("INDETERMINATE", "C_BASIS", "No basis supplied.", "basis")
    independent = (
        bool(material)
        and control(basis, material) == "NON_MATERIAL_CONTROL"
        and basis.get("constrained_at_production") is True
    )
    if not check("independent_at_production", independent, ["claim.material_parties", "basis"]):
        return finish(
            "INDETERMINATE",
            "C_SAME_PARTY",
            "No independent production-time constraint "
            "established; absence of one is not proof of omission.",
            "independent basis",
        )
    authoritative = (
        basis.get("kind") == "exhaustive_counterparty_index"
        and bool(authority.get("id"))
        and authority.get("profile") == PROFILE
        and authority.get("party") == basis.get("operator")
        and authority.get("basis_id") == basis.get("id")
        and authority.get("domain_id") == domain["id"]
    )
    if not check("authority", authoritative, ["authority", "basis", "claim.domain"]):
        return finish(
            "INDETERMINATE",
            "C_AUTHORITY",
            "Authority not established under fixture policy.",
            "matching stipulated authority",
        )
    bound = (
        bool(basis.get("state_version"))
        and binding.get("basis_id") == basis.get("id")
        and binding.get("state_version") == basis["state_version"]
        and binding.get("sha256") == digest(basis)
    )
    if not check("state_binding", bound, ["run_binding", "basis"]):
        return finish(
            "INDETERMINATE",
            "C_STATE_BINDING",
            "Detector state/version is not bound to this evaluation.",
            "matching state version and digest",
        )
    scoped = (
        basis.get("domain_id") == domain["id"]
        and basis.get("result_id") == data.get("result_id")
        and bool(data.get("result_id"))
    )
    if not check("result_and_domain_binding", scoped, ["basis", "claim.domain", "result_id"]):
        return finish(
            "INDETERMINATE",
            "C_SCOPE",
            "Basis is not bound to this result/domain.",
            "matching result and domain",
        )
    if not check(
        "coverage_window",
        contains(basis.get("window", {}), domain["window"])
        and contains(authority.get("window", {}), domain["window"]),
        ["basis.window", "authority.window", "claim.domain.window"],
    ):
        return finish(
            "INDETERMINATE",
            "C_WINDOW",
            "Anchor/authority does not cover claimed window.",
            "independent coverage for the entire declared window",
        )
    try:
        timely = all(
            instant(e["issued_at"]) <= instant(replay_at) < instant(e["expires_at"])
            for e in (basis, authority)
        )
    except (KeyError, TypeError, ValueError):
        timely = False
    if not check("issue_and_expiry", timely, ["basis", "authority"]):
        return finish(
            "INDETERMINATE",
            "C_TIME",
            "Evidence not established in force at replay.",
            "usable evidence issue/expiry times",
        )
    expected_records = basis.get("records")
    disclosed_records = data.get("disclosed")
    enumerable = (
        basis.get("exhaustive") is True
        and isinstance(expected_records, list)
        and isinstance(disclosed_records, list)
    )
    if not check("coverage_extent", enumerable, ["basis.records", "basis.exhaustive", "disclosed"]):
        return finish(
            "INDETERMINATE",
            "C_EXTENT",
            "No exhaustive enumeration available.",
            "exhaustive independent enumeration",
        )
    expected = {r.get("record_id") for r in expected_records}
    disclosed = {r.get("record_id") for r in disclosed_records}
    if (
        None in expected
        or None in disclosed
        or "" in expected
        or "" in disclosed
        or len(expected) != len(expected_records)
        or len(disclosed) != len(disclosed_records)
    ):
        return finish(
            "INDETERMINATE",
            "C_IDENTITIES",
            "Missing or duplicate record IDs.",
            "unique record identities",
        )
    if disclosed - expected:
        return finish(
            "INDETERMINATE",
            "C_OUTSIDE_DOMAIN",
            "Disclosed IDs exceed bound domain.",
            "consistent domain membership",
        )
    omitted = sorted(expected - disclosed)
    output["omission_detection_basis"]["omitted_record_ids"] = omitted
    check("reconciliation", not omitted, ["basis.records", "disclosed"])
    if omitted:
        return finish(
            "UNSATISFIED",
            "C_OMISSION",
            "Appraised index exposes missing IDs: " + ", ".join(omitted),
        )
    return finish(
        "SATISFIED",
        "C_COMPLETE",
        "Disclosed IDs cover the independently indexed "
        "finite fixture domain only; signature validity is not used for completeness.",
    )
