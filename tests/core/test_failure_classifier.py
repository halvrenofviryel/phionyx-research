"""
Tests for Failure Classifier — Patent SF1-9~13
================================================

Proves 4-category failure classification with typed recovery strategies.
"""

import pytest

from phionyx_core.governance.failure_classifier import (
    FailureClassifier,
    FailureCategory,
    FailureSeverity,
    RecoveryStrategy,
)


class TestEntropyOverflow:
    """SF1 Claim 9: Entropy overflow detection → dampening strategy."""

    def test_high_entropy_classified(self):
        """Entropy above threshold → EntropyOverflow."""
        clf = FailureClassifier(entropy_threshold=0.85)
        failures = clf.classify({"entropy": 0.92})
        assert len(failures) >= 1
        eof = [f for f in failures if f.category == FailureCategory.ENTROPY_OVERFLOW]
        assert len(eof) == 1
        assert eof[0].recovery_strategy == RecoveryStrategy.DAMPEN_ENTROPY
        assert eof[0].severity in (FailureSeverity.MEDIUM, FailureSeverity.HIGH)

    def test_normal_entropy_no_failure(self):
        """Entropy below threshold → no failure."""
        clf = FailureClassifier(entropy_threshold=0.85)
        failures = clf.classify({"entropy": 0.5})
        eof = [f for f in failures if f.category == FailureCategory.ENTROPY_OVERFLOW]
        assert len(eof) == 0

    def test_critical_entropy(self):
        """Entropy > 0.95 → HIGH severity."""
        clf = FailureClassifier(entropy_threshold=0.85)
        failures = clf.classify({"entropy": 0.98})
        eof = [f for f in failures if f.category == FailureCategory.ENTROPY_OVERFLOW]
        assert eof[0].severity == FailureSeverity.HIGH


class TestCoherenceViolation:
    """SF1 Claim 10: Coherence drop detection → recovery strategy."""

    def test_large_coherence_drop_classified(self):
        """Large coherence drop → CoherenceViolation."""
        clf = FailureClassifier(coherence_delta=0.3)
        failures = clf.classify(
            {"coherence": 0.4},
            previous_state={"coherence": 0.85}
        )
        cv = [f for f in failures if f.category == FailureCategory.COHERENCE_VIOLATION]
        assert len(cv) == 1
        assert cv[0].recovery_strategy == RecoveryStrategy.RESTORE_COHERENCE

    def test_small_coherence_drop_no_failure(self):
        """Small coherence drop → no failure."""
        clf = FailureClassifier(coherence_delta=0.3)
        failures = clf.classify(
            {"coherence": 0.75},
            previous_state={"coherence": 0.85}
        )
        cv = [f for f in failures if f.category == FailureCategory.COHERENCE_VIOLATION]
        assert len(cv) == 0


class TestEthicsRisk:
    """SF1 Claim 11: Ethics risk → HITL escalation."""

    def test_high_ethics_risk_classified(self):
        """High ethics risk → EthicsRisk with HITL escalation."""
        clf = FailureClassifier(ethics_risk_threshold=0.6)
        failures = clf.classify(
            {"entropy": 0.3},
            block_results={"ethics_pre_response": {"risk_level": 0.85}}
        )
        er = [f for f in failures if f.category == FailureCategory.ETHICS_RISK]
        assert len(er) == 1
        assert er[0].recovery_strategy == RecoveryStrategy.ESCALATE_TO_HITL

    def test_low_ethics_risk_no_failure(self):
        """Low ethics risk → no failure."""
        clf = FailureClassifier(ethics_risk_threshold=0.6)
        failures = clf.classify(
            {"entropy": 0.3},
            block_results={"ethics_pre_response": {"risk_level": 0.2}}
        )
        er = [f for f in failures if f.category == FailureCategory.ETHICS_RISK]
        assert len(er) == 0

    def test_critical_ethics_risk(self):
        """Risk > 0.9 → CRITICAL severity."""
        clf = FailureClassifier(ethics_risk_threshold=0.6)
        failures = clf.classify(
            {"entropy": 0.3},
            block_results={"ethics_pre_response": {"risk_level": 0.95}}
        )
        er = [f for f in failures if f.category == FailureCategory.ETHICS_RISK]
        assert er[0].severity == FailureSeverity.CRITICAL


class TestStateCorruption:
    """SF1 Claim 12-13: State invariant violations → checkpoint rollback."""

    def test_phi_out_of_range(self):
        """phi outside [0,1] → StateCorruption."""
        clf = FailureClassifier()
        failures = clf.classify({"phi": 1.5})
        sc = [f for f in failures if f.category == FailureCategory.STATE_CORRUPTION]
        assert len(sc) == 1
        assert sc[0].recovery_strategy == RecoveryStrategy.ROLLBACK_CHECKPOINT
        assert sc[0].severity == FailureSeverity.CRITICAL

    def test_negative_entropy(self):
        """Negative entropy → StateCorruption."""
        clf = FailureClassifier()
        failures = clf.classify({"entropy": -0.1})
        sc = [f for f in failures if f.category == FailureCategory.STATE_CORRUPTION]
        assert len(sc) >= 1

    def test_valid_state_no_corruption(self):
        """Valid phi/entropy → no state corruption."""
        clf = FailureClassifier()
        failures = clf.classify({"phi": 0.5, "entropy": 0.3})
        sc = [f for f in failures if f.category == FailureCategory.STATE_CORRUPTION]
        assert len(sc) == 0


class TestClassifySingle:
    """classify_single returns highest-severity failure."""

    def test_returns_highest_severity(self):
        """Multiple failures → returns critical one."""
        clf = FailureClassifier(entropy_threshold=0.85)
        result = clf.classify_single(
            {"entropy": 0.9, "phi": 1.5}  # Both entropy overflow AND state corruption
        )
        assert result is not None
        assert result.severity == FailureSeverity.CRITICAL
        assert result.category == FailureCategory.STATE_CORRUPTION

    def test_returns_none_when_no_failures(self):
        """No failures → returns None."""
        clf = FailureClassifier()
        result = clf.classify_single({"entropy": 0.3, "phi": 0.5, "coherence": 0.8})
        assert result is None

    def test_to_dict_serializable(self):
        """FailureClassification.to_dict() produces valid dict."""
        clf = FailureClassifier(entropy_threshold=0.85)
        result = clf.classify_single({"entropy": 0.95})
        assert result is not None
        d = result.to_dict()
        assert d["category"] == "entropy_overflow"
        assert d["recovery_strategy"] == "dampen_entropy"
        assert isinstance(d["confidence"], float)
