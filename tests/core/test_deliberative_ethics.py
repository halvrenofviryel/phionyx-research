"""
Tests for DeliberativeEthics — v4 §9 (AGI Layer 9)
====================================================
"""

import pytest
from phionyx_core.governance.deliberative_ethics import (
    DeliberativeEthics,
    DeliberativeResult,
    FrameworkAssessment,
    EthicalFramework,
    DeliberationOutcome,
)


# ── Basic Deliberation ──

def test_deliberate_low_risk():
    ethics = DeliberativeEthics()
    result = ethics.deliberate(
        action="Greet the user",
        ethics_vector={"harm_risk": 0.1, "manipulation_risk": 0.0},
    )
    assert result.final_verdict == DeliberationOutcome.ALLOW.value
    assert result.consensus is True

def test_deliberate_high_harm():
    ethics = DeliberativeEthics()
    result = ethics.deliberate(
        action="Generate harmful content",
        ethics_vector={"harm_risk": 0.95, "manipulation_risk": 0.95},
    )
    assert result.final_verdict == DeliberationOutcome.DENY.value

def test_deliberate_moderate_risk():
    ethics = DeliberativeEthics()
    result = ethics.deliberate(
        action="Discuss sensitive topic",
        ethics_vector={"harm_risk": 0.5, "manipulation_risk": 0.3},
    )
    assert result.final_verdict in (
        DeliberationOutcome.ALLOW_WITH_GUARD.value,
        DeliberationOutcome.ALLOW.value,
    )


# ── Framework Assessments ──

def test_four_frameworks_assessed():
    ethics = DeliberativeEthics()
    result = ethics.deliberate(
        action="Test",
        ethics_vector={"harm_risk": 0.5},
    )
    assert len(result.framework_assessments) == 4
    names = {fa.framework for fa in result.framework_assessments}
    assert names == {
        EthicalFramework.DEONTOLOGICAL.value,
        EthicalFramework.CONSEQUENTIALIST.value,
        EthicalFramework.VIRTUE.value,
        EthicalFramework.CARE.value,
    }

def test_each_assessment_has_reasoning():
    ethics = DeliberativeEthics()
    result = ethics.deliberate("Test", {"harm_risk": 0.3})
    for fa in result.framework_assessments:
        assert len(fa.reasoning) > 0
        assert fa.confidence > 0.0


# ── Deontological Framework ──

def test_deontological_deny_high_risk():
    ethics = DeliberativeEthics()
    result = ethics.deliberate("Bad", {"harm_risk": 0.95})
    deont = [fa for fa in result.framework_assessments
             if fa.framework == EthicalFramework.DEONTOLOGICAL.value][0]
    assert deont.verdict == DeliberationOutcome.DENY.value

def test_deontological_allow_low_risk():
    ethics = DeliberativeEthics()
    result = ethics.deliberate("Good", {"harm_risk": 0.1})
    deont = [fa for fa in result.framework_assessments
             if fa.framework == EthicalFramework.DEONTOLOGICAL.value][0]
    assert deont.verdict == DeliberationOutcome.ALLOW.value

def test_deontological_boundary_violation():
    ethics = DeliberativeEthics()
    result = ethics.deliberate("Boundary", {"boundary_violation_risk": 0.95})
    deont = [fa for fa in result.framework_assessments
             if fa.framework == EthicalFramework.DEONTOLOGICAL.value][0]
    assert deont.verdict == DeliberationOutcome.DENY.value


# ── Consequentialist Framework ──

def test_consequentialist_high_harm():
    ethics = DeliberativeEthics()
    result = ethics.deliberate("Harm", {"harm_risk": 0.9, "attachment_risk": 0.8})
    consq = [fa for fa in result.framework_assessments
             if fa.framework == EthicalFramework.CONSEQUENTIALIST.value][0]
    assert consq.verdict == DeliberationOutcome.DENY.value

def test_consequentialist_low_harm():
    ethics = DeliberativeEthics()
    result = ethics.deliberate("Safe", {"harm_risk": 0.1, "attachment_risk": 0.1})
    consq = [fa for fa in result.framework_assessments
             if fa.framework == EthicalFramework.CONSEQUENTIALIST.value][0]
    assert consq.verdict == DeliberationOutcome.ALLOW.value


# ── Virtue Framework ──

def test_virtue_manipulation():
    ethics = DeliberativeEthics()
    result = ethics.deliberate("Manipulate", {"manipulation_risk": 0.9})
    virtue = [fa for fa in result.framework_assessments
              if fa.framework == EthicalFramework.VIRTUE.value][0]
    assert virtue.verdict == DeliberationOutcome.DENY.value

def test_virtue_aligned():
    ethics = DeliberativeEthics()
    result = ethics.deliberate("Help", {"manipulation_risk": 0.1})
    virtue = [fa for fa in result.framework_assessments
              if fa.framework == EthicalFramework.VIRTUE.value][0]
    assert virtue.verdict == DeliberationOutcome.ALLOW.value


# ── Care Framework ──

def test_care_child_risk():
    ethics = DeliberativeEthics()
    result = ethics.deliberate(
        "Child content",
        {"child_on_child_risk": 0.8},
    )
    care = [fa for fa in result.framework_assessments
            if fa.framework == EthicalFramework.CARE.value][0]
    assert care.verdict == DeliberationOutcome.DENY.value

def test_care_minor_amplification():
    ethics = DeliberativeEthics()
    result = ethics.deliberate(
        "Risky for minor",
        {"harm_risk": 0.5, "child_on_child_risk": 0.0},
        context={"user_age_group": "minor"},
    )
    care = [fa for fa in result.framework_assessments
            if fa.framework == EthicalFramework.CARE.value][0]
    # harm_risk 0.5 * 1.5 = 0.75 → care_risk > 0.5 → DENY
    assert care.verdict == DeliberationOutcome.DENY.value

def test_care_no_vulnerable():
    ethics = DeliberativeEthics()
    result = ethics.deliberate("Safe", {"harm_risk": 0.1})
    care = [fa for fa in result.framework_assessments
            if fa.framework == EthicalFramework.CARE.value][0]
    assert care.verdict == DeliberationOutcome.ALLOW.value


# ── Consensus & Aggregation ──

def test_consensus_all_allow():
    ethics = DeliberativeEthics()
    result = ethics.deliberate("Safe", {"harm_risk": 0.0})
    assert result.consensus is True
    assert result.final_verdict == DeliberationOutcome.ALLOW.value

def test_no_consensus_mixed():
    ethics = DeliberativeEthics()
    # High harm → deont/consq/care may deny, virtue may guard
    result = ethics.deliberate(
        "Mixed",
        {"harm_risk": 0.65, "manipulation_risk": 0.5, "child_on_child_risk": 0.6},
    )
    assert result.consensus is False

def test_three_deny_forces_deny():
    ethics = DeliberativeEthics()
    result = ethics.deliberate(
        "Very bad",
        {
            "harm_risk": 0.95,
            "manipulation_risk": 0.95,
            "boundary_violation_risk": 0.95,
            "child_on_child_risk": 0.95,
        },
    )
    assert result.final_verdict == DeliberationOutcome.DENY.value
    assert result.final_confidence >= 0.9


# ── Custom Weights ──

def test_custom_framework_weights():
    ethics = DeliberativeEthics(
        framework_weights={
            "deontological": 0.9,
            "consequentialist": 0.1,
            "virtue": 0.0,
            "care": 0.0,
        }
    )
    result = ethics.deliberate("Test", {"harm_risk": 0.5})
    # Deontological has dominant weight
    deont = [fa for fa in result.framework_assessments
             if fa.framework == "deontological"][0]
    assert deont.weight > 0.8


# ── Thresholds ──

def test_custom_deny_threshold():
    # Very low deny threshold → more likely to deny
    ethics = DeliberativeEthics(deny_threshold=0.1)
    result = ethics.deliberate("Test", {"harm_risk": 0.5})
    assert isinstance(result.final_verdict, str)

def test_custom_guard_threshold():
    ethics = DeliberativeEthics(guard_threshold=0.1)
    result = ethics.deliberate("Test", {"harm_risk": 0.3})
    assert isinstance(result.final_verdict, str)


# ── Serialization ──

def test_to_dict():
    ethics = DeliberativeEthics()
    result = ethics.deliberate("Test", {"harm_risk": 0.5})
    d = result.to_dict()
    assert d["action"] == "Test"
    assert len(d["frameworks"]) == 4
    assert "verdict" in d
    assert "confidence" in d
    assert "consensus" in d
    assert "reasoning" in d

def test_to_dict_framework_fields():
    ethics = DeliberativeEthics()
    result = ethics.deliberate("Test", {"harm_risk": 0.2})
    d = result.to_dict()
    for fw in d["frameworks"]:
        assert "framework" in fw
        assert "verdict" in fw
        assert "confidence" in fw
        assert "reasoning" in fw


# ── Reasoning ──

def test_reasoning_contains_frameworks():
    ethics = DeliberativeEthics()
    result = ethics.deliberate("Test", {"harm_risk": 0.3})
    assert "deontological" in result.reasoning
    assert "consequentialist" in result.reasoning

def test_reasoning_consensus_label():
    ethics = DeliberativeEthics()
    result = ethics.deliberate("Safe", {"harm_risk": 0.0})
    assert "unanimous" in result.reasoning

def test_reasoning_split_label():
    ethics = DeliberativeEthics()
    result = ethics.deliberate(
        "Mixed",
        {"harm_risk": 0.65, "manipulation_risk": 0.5, "child_on_child_risk": 0.6},
    )
    if not result.consensus:
        assert "split" in result.reasoning


# ── Risk Dimensions Passthrough ──

def test_risk_dimensions_stored():
    ethics = DeliberativeEthics()
    vec = {"harm_risk": 0.5, "manipulation_risk": 0.3}
    result = ethics.deliberate("Test", vec)
    assert result.risk_dimensions == vec

def test_action_description_stored():
    ethics = DeliberativeEthics()
    result = ethics.deliberate("My specific action", {"harm_risk": 0.1})
    assert result.action_description == "My specific action"


# ── Edge Cases ──

def test_empty_ethics_vector():
    ethics = DeliberativeEthics()
    result = ethics.deliberate("Test", {})
    assert result.final_verdict == DeliberationOutcome.ALLOW.value

def test_unknown_risk_keys_ignored():
    ethics = DeliberativeEthics()
    result = ethics.deliberate("Test", {"custom_risk": 0.9, "harm_risk": 0.1})
    # Only known keys affect assessment
    assert result.final_verdict in (
        DeliberationOutcome.ALLOW.value,
        DeliberationOutcome.ALLOW_WITH_GUARD.value,
    )
