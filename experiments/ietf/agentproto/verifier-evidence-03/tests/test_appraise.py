"""Deterministic vectors, boundary cases and evidence mutations."""

import copy
import itertools
import json
from pathlib import Path

import pytest

from appraise import OUTCOMES, appraise, digest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = json.loads((ROOT / "vectors/completeness_vectors.json").read_text())
VECTORS = {v["id"]: v for v in FIXTURES["vectors"]}
NOW = FIXTURES["replay_at"]


def fresh(name: str = "closed_independent") -> dict:
    """Return fresh evaluator-visible evidence, excluding test oracle facts."""
    return copy.deepcopy(VECTORS[name]["input"])


def rebind(data: dict) -> None:
    """Bind deliberately changed synthetic evidence to the mutated test run."""
    data["run_binding"] = {
        "basis_id": data["basis"]["id"],
        "state_version": data["basis"]["state_version"],
        "sha256": digest(data["basis"]),
    }


@pytest.mark.parametrize("vector", FIXTURES["vectors"], ids=lambda v: v["id"])
def test_declared_vectors(vector: dict) -> None:
    result = appraise(vector["input"], NOW)
    assert result["result"] == vector["expected"]["result"]
    assert result["diagnostics"][-1]["code"] == vector["expected"]["diagnostic"]
    assert result["predicate_result"]["result"] == vector["expected"]["predicate_result"]
    assert result["result"] in OUTCOMES
    assert {
        "coverage_domain",
        "omission_detection_basis",
        "material_party_control",
        "evidence_present",
        "missing_or_unavailable_inputs",
        "requirement_ids",
        "diagnostics",
    } <= result.keys()
    assert ("check_performed_at" in result) == (result["result"] != "NOT_EVALUATED")
    assert result == appraise(copy.deepcopy(vector["input"]), NOW)


def test_hidden_truth_is_not_evaluator_evidence() -> None:
    vector = copy.deepcopy(VECTORS["withheld_unobservable"])
    before = appraise(vector["input"], NOW)
    vector["scenario_only"] = {"actual_record_ids": [], "actual_occurrences": 0}
    vector["expected"]["result"] = "SATISFIED"
    assert appraise(vector["input"], NOW) == before
    assert before["result"] == "INDETERMINATE"


def test_withheld_record_mutation_and_restoration() -> None:
    data = fresh()
    assert appraise(data, NOW)["result"] == "SATISFIED"
    withheld = data["disclosed"].pop()
    result = appraise(data, NOW)
    assert result["result"] == "UNSATISFIED"
    assert result["omission_detection_basis"]["omitted_record_ids"] == ["r2"]
    data["disclosed"].append(withheld)
    assert appraise(data, NOW)["result"] == "SATISFIED"


@pytest.mark.parametrize("status", ["UNAVAILABLE", "NOT_CONFIGURED", "UNKNOWN"])
def test_unavailable_resolver_cannot_use_cached_evidence(status: str) -> None:
    data = fresh()
    data["plan"]["resolver_status"] = status
    result = appraise(data, NOW)
    assert result["result"] == "INDETERMINATE"
    assert result["capability_context"]["declared_capability"] == "SUPPORTED"
    data["plan"]["resolver_status"] = "AVAILABLE"
    assert appraise(data, NOW)["result"] == "SATISFIED"


@pytest.mark.parametrize(
    "field,value",
    [
        ("operator", "producer"),
        ("input_selectors", ["producer"]),
        ("input_selectors", ["counterparty", "producer"]),
    ],
)
def test_control_mutation(field: str, value: object) -> None:
    data = fresh()
    data["basis"][field] = value
    rebind(data)
    assert appraise(data, NOW)["diagnostics"][-1]["code"] == "C_SAME_PARTY"


def test_signature_validity_does_not_change_completeness() -> None:
    data = fresh("same_party_only")
    before = appraise(data, NOW)["result"]
    for record in data["disclosed"]:
        record["authentication"] = "invalid_or_unknown"
    assert appraise(data, NOW)["result"] == before == "INDETERMINATE"
    # Membership-only appraisal is also not a validity verdict in the positive case.
    data = fresh()
    for record in data["disclosed"]:
        record["authentication"] = "invalid_or_unknown"
    assert appraise(data, NOW)["result"] == "SATISFIED"


@pytest.mark.parametrize(
    "path,value,code",
    [
        (("profile",), "other", "C_PROFILE"),
        (("claim", "kind"), "unknown", "C_PROFILE"),
        (("claim", "domain"), None, "C_DOMAIN"),
        (("claim", "domain", "window"), {}, "C_DOMAIN_UNCLOSED"),
        (("mechanism",), None, "C_MECHANISM"),
        (("basis",), None, "C_BASIS"),
        (("claim", "material_parties"), [], "C_SAME_PARTY"),
        (("basis", "operator"), None, "C_SAME_PARTY"),
        (("basis", "constrained_at_production"), False, "C_SAME_PARTY"),
        (("authority", "party"), "unbound-party", "C_AUTHORITY"),
        (("authority",), None, "C_AUTHORITY"),
        (("run_binding", "state_version"), "stale-v0", "C_STATE_BINDING"),
        (("basis", "result_id"), "other-result", "C_SCOPE"),
        (("basis", "domain_id"), "other-domain", "C_SCOPE"),
        (("authority", "window"), {}, "C_WINDOW"),
        (("basis", "issued_at"), "2026-11-03T00:00:00Z", "C_TIME"),
        (("basis", "expires_at"), NOW, "C_TIME"),
        (("basis", "issued_at"), "2026-11-01T00:00:00", "C_TIME"),
        (("basis", "expires_at"), None, "C_TIME"),
        (("basis", "exhaustive"), False, "C_EXTENT"),
        (("basis", "records"), None, "C_EXTENT"),
        (("plan", "attempt"), None, "C_PLAN"),
        (("plan", "capability"), "UNSUPPORTED", "C_CAPABILITY"),
        (("plan", "capability"), "UNKNOWN", "C_CAPABILITY"),
    ],
)
def test_evidence_gaps_stay_indeterminate(path: tuple, value: object, code: str) -> None:
    data = fresh()
    target = data
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    if path[0] == "basis" and data["basis"] is not None:
        rebind(data)
    result = appraise(data, NOW)
    assert result["result"] == "INDETERMINATE"
    assert result["diagnostics"][-1]["code"] == code
    assert result["missing_or_unavailable_inputs"]


def test_digest_tampering_without_rebinding() -> None:
    data = fresh()
    data["basis"]["records"].pop()
    assert appraise(data, NOW)["diagnostics"][-1]["code"] == "C_STATE_BINDING"


def test_explicit_skip_has_no_check_time_and_preserves_capability() -> None:
    data = fresh()
    data["plan"]["attempt"] = False
    result = appraise(data, NOW)
    assert result["result"] == "NOT_EVALUATED"
    assert "check_performed_at" not in result
    assert result["capability_context"]["declared_capability"] == "SUPPORTED"


@pytest.mark.parametrize(
    "mutation,code",
    [("duplicate", "C_IDENTITIES"), ("missing_id", "C_IDENTITIES"), ("extra", "C_OUTSIDE_DOMAIN")],
)
def test_record_identity_boundaries(mutation: str, code: str) -> None:
    data = fresh()
    if mutation == "duplicate":
        data["disclosed"].append(data["disclosed"][0])
    elif mutation == "missing_id":
        data["disclosed"][0].pop("record_id")
    else:
        data["disclosed"].append({"record_id": "r3"})
    assert appraise(data, NOW)["diagnostics"][-1]["code"] == code


def test_all_subsets_of_two_record_domain() -> None:
    for bits in itertools.product((False, True), repeat=2):
        data = fresh()
        data["disclosed"] = [r for r, keep in zip(data["disclosed"], bits) if keep]
        expected = "SATISFIED" if all(bits) else "UNSATISFIED"
        assert appraise(data, NOW)["result"] == expected


def test_empty_but_closed_independent_domain_is_not_no_claim() -> None:
    data = fresh()
    data["disclosed"] = []
    data["basis"]["records"] = []
    rebind(data)
    assert appraise(data, NOW)["result"] == "SATISFIED"


def test_predicate_and_completeness_are_separate() -> None:
    data = fresh("two_disclosed_predicate")
    result = appraise(data, NOW)
    assert result["result"] == "INDETERMINATE"
    assert result["predicate_result"]["result"] == "UNSATISFIED"
    data["disclosed"][1]["authentication"] = "unknown"
    assert appraise(data, NOW)["predicate_result"]["result"] == "INDETERMINATE"
    data = fresh("qualified_sample")
    data["predicate"] = "at_most_once"
    assert appraise(data, NOW)["predicate_result"]["result"] == "SATISFIED"


def test_completed_appraisal_retains_checked_evidence() -> None:
    result = appraise(fresh(), NOW)
    checks = result["omission_detection_basis"]["appraisal_checks"]
    assert {c["check"] for c in checks} == {
        "finite_domain",
        "independent_at_production",
        "authority",
        "state_binding",
        "result_and_domain_binding",
        "coverage_window",
        "issue_and_expiry",
        "coverage_extent",
        "reconciliation",
    }
    assert all(c["passed"] and c["evidence_refs"] for c in checks)
    assert {e["input_path"] for e in result["evidence_present"]} >= {"basis", "authority"}
    assert next(e for e in result["evidence_present"] if e["input_path"] == "basis")["issued_at"]


def test_input_is_not_mutated() -> None:
    data = fresh()
    before = copy.deepcopy(data)
    appraise(data, NOW)
    assert data == before
