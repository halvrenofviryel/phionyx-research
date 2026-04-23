"""
Autonomous Thought Generator Unit Tests — Sprint A+B
=====================================================

Tests for the self-directed communication module.
Total: 22 tests

Structure:
- TestThoughtTriggerEnum (2): enum values and str inheritance
- TestCognitiveSnapshot (2): defaults and custom values
- TestThoughtProposal (2): creation and serialization
- TestAutonomousGeneration (5): priority-based generation
- TestCooldownAndLimits (4+1): cooldown, session limits, idle requirements
- TestFeedbackDiscovery (7): FEEDBACK_DISCOVERY trigger, new fields, priority
"""

import time
import pytest

from phionyx_core.meta.autonomous_thought import (
    ThoughtTrigger,
    ThoughtUrgency,
    CognitiveSnapshot,
    ThoughtProposal,
    AutonomousThoughtGenerator,
)


# ─── Helpers ──────────────────────────────────────────────────────────

def _base_snapshot(**overrides) -> CognitiveSnapshot:
    """Create a CognitiveSnapshot with sensible defaults and overrides."""
    defaults = {
        "phi": 0.5,
        "entropy": 0.3,
        "valence": 0.5,
        "arousal": 0.5,
        "coherence": 0.8,
        "drift_magnitude": 0.0,
        "drift_severity": "none",
        "active_goals": [],
        "goal_conflicts": [],
        "turn_count": 1,
        "last_user_message_time": time.time() - 60,  # 60s idle by default
        "session_id": "test-session-1",
    }
    defaults.update(overrides)
    return CognitiveSnapshot(**defaults)


# ═══════════════════════════════════════════════════════════════════════
# Enums — 2 Tests
# ═══════════════════════════════════════════════════════════════════════

class TestThoughtTriggerEnum:
    """Tests for ThoughtTrigger enum."""

    def test_trigger_values(self):
        """All 8 trigger types exist with correct string values."""
        assert ThoughtTrigger.SESSION_GREETING == "session_greeting"
        assert ThoughtTrigger.DRIFT_DETECTED == "drift_detected"
        assert ThoughtTrigger.FEEDBACK_DISCOVERY == "feedback_discovery"
        assert ThoughtTrigger.PHYSICS_ANOMALY == "physics_anomaly"
        assert ThoughtTrigger.GOAL_CONFLICT == "goal_conflict"
        assert ThoughtTrigger.GOAL_UPDATE == "goal_update"
        assert ThoughtTrigger.SELF_REFLECTION == "self_reflection"
        assert ThoughtTrigger.IDLE_INSIGHT == "idle_insight"
        assert len(ThoughtTrigger) == 8

    def test_urgency_values(self):
        """All 4 urgency levels exist with correct string values."""
        assert ThoughtUrgency.LOW == "low"
        assert ThoughtUrgency.MEDIUM == "medium"
        assert ThoughtUrgency.HIGH == "high"
        assert ThoughtUrgency.CRITICAL == "critical"
        assert len(ThoughtUrgency) == 4


# ═══════════════════════════════════════════════════════════════════════
# CognitiveSnapshot — 2 Tests
# ═══════════════════════════════════════════════════════════════════════

class TestCognitiveSnapshot:
    """Tests for CognitiveSnapshot dataclass."""

    def test_default_values(self):
        """Snapshot has sensible defaults."""
        snap = CognitiveSnapshot()
        assert snap.phi == 0.5
        assert snap.entropy == 0.3
        assert snap.coherence == 0.8
        assert snap.drift_severity == "none"
        assert snap.active_goals == []
        assert snap.goal_conflicts == []
        assert snap.turn_count == 0

    def test_custom_values(self):
        """Snapshot accepts custom values."""
        snap = CognitiveSnapshot(
            phi=0.9, entropy=0.8, coherence=0.2,
            drift_magnitude=0.5, drift_severity="high",
            active_goals=["goal_a"], goal_conflicts=["conflict_x"],
            turn_count=10, session_id="s1",
        )
        assert snap.phi == 0.9
        assert snap.drift_severity == "high"
        assert snap.goal_conflicts == ["conflict_x"]
        assert snap.session_id == "s1"


# ═══════════════════════════════════════════════════════════════════════
# ThoughtProposal — 2 Tests
# ═══════════════════════════════════════════════════════════════════════

class TestThoughtProposal:
    """Tests for ThoughtProposal dataclass."""

    def test_creation(self):
        """Proposal creates with all fields."""
        p = ThoughtProposal(
            trigger=ThoughtTrigger.DRIFT_DETECTED,
            urgency=ThoughtUrgency.HIGH,
            topic="self_model_drift",
            prompt="Test prompt",
            reasoning="Test reason",
        )
        assert p.trigger == ThoughtTrigger.DRIFT_DETECTED
        assert p.urgency == ThoughtUrgency.HIGH
        assert p.suppressed is False
        assert p.timestamp > 0

    def test_to_dict(self):
        """Proposal serializes correctly."""
        p = ThoughtProposal(
            trigger=ThoughtTrigger.SESSION_GREETING,
            urgency=ThoughtUrgency.LOW,
            topic="greeting",
            prompt="Hello",
            reasoning="New session",
        )
        d = p.to_dict()
        assert d["trigger"] == "session_greeting"
        assert d["urgency"] == "low"
        assert d["topic"] == "greeting"
        assert d["suppressed"] is False
        assert "timestamp" in d


# ═══════════════════════════════════════════════════════════════════════
# Autonomous Generation — 5 Tests
# ═══════════════════════════════════════════════════════════════════════

class TestAutonomousGeneration:
    """Tests for AutonomousThoughtGenerator.generate() priority logic."""

    def test_session_greeting_on_turn_zero(self):
        """Turn 0 with no prior thoughts → SESSION_GREETING."""
        gen = AutonomousThoughtGenerator(cooldown_seconds=0, min_idle=0)
        snap = _base_snapshot(turn_count=0)
        proposal = gen.generate(snap)
        assert proposal is not None
        assert proposal.trigger == ThoughtTrigger.SESSION_GREETING
        assert proposal.urgency == ThoughtUrgency.LOW
        assert not proposal.suppressed

    def test_critical_drift_highest_priority(self):
        """Critical drift overrides all other triggers."""
        gen = AutonomousThoughtGenerator(cooldown_seconds=0, min_idle=0)
        snap = _base_snapshot(
            drift_magnitude=0.6,
            drift_severity="critical",
            goal_conflicts=["conflict_a"],  # also present, but drift wins
            entropy=0.9,  # also anomalous, but drift wins
        )
        proposal = gen.generate(snap)
        assert proposal is not None
        assert proposal.trigger == ThoughtTrigger.DRIFT_DETECTED
        assert proposal.urgency == ThoughtUrgency.CRITICAL

    def test_goal_conflict_before_physics(self):
        """Goal conflicts have higher priority than physics anomaly."""
        gen = AutonomousThoughtGenerator(cooldown_seconds=0, min_idle=0)
        snap = _base_snapshot(
            goal_conflicts=["goal_a vs goal_b"],
            entropy=0.9,  # also anomalous
        )
        proposal = gen.generate(snap)
        assert proposal is not None
        assert proposal.trigger == ThoughtTrigger.GOAL_CONFLICT

    def test_physics_anomaly_high_entropy(self):
        """High entropy triggers physics anomaly."""
        gen = AutonomousThoughtGenerator(cooldown_seconds=0, min_idle=0)
        snap = _base_snapshot(entropy=0.85)
        proposal = gen.generate(snap)
        assert proposal is not None
        assert proposal.trigger == ThoughtTrigger.PHYSICS_ANOMALY
        assert "entropi" in proposal.prompt

    def test_self_reflection_at_threshold(self):
        """Self-reflection triggers at turn count multiples."""
        gen = AutonomousThoughtGenerator(
            cooldown_seconds=0, min_idle=0, reflection_min_turns=5,
        )
        snap = _base_snapshot(turn_count=5)
        proposal = gen.generate(snap)
        assert proposal is not None
        assert proposal.trigger == ThoughtTrigger.SELF_REFLECTION

    def test_no_thought_for_normal_state(self):
        """Normal cognitive state with no triggers → None."""
        gen = AutonomousThoughtGenerator(cooldown_seconds=999, min_idle=0)
        snap = _base_snapshot(turn_count=3, last_user_message_time=time.time() - 5)
        proposal = gen.generate(snap)
        assert proposal is None


# ═══════════════════════════════════════════════════════════════════════
# Cooldown and Limits — 4 Tests
# ═══════════════════════════════════════════════════════════════════════

class TestCooldownAndLimits:
    """Tests for cooldown, session limits, and idle requirements."""

    def test_cooldown_suppresses_non_critical(self):
        """Non-critical thoughts are suppressed during cooldown."""
        gen = AutonomousThoughtGenerator(cooldown_seconds=60, min_idle=0)

        # First thought: session greeting (turn 0)
        snap1 = _base_snapshot(turn_count=0)
        p1 = gen.generate(snap1)
        assert p1 is not None
        assert not p1.suppressed

        # Second thought immediately: should be suppressed by cooldown
        snap2 = _base_snapshot(entropy=0.9, turn_count=1)
        p2 = gen.generate(snap2)
        assert p2 is not None
        assert p2.suppressed

    def test_critical_bypasses_cooldown(self):
        """CRITICAL urgency bypasses cooldown."""
        gen = AutonomousThoughtGenerator(cooldown_seconds=60, min_idle=0)

        # First thought
        snap1 = _base_snapshot(turn_count=0)
        gen.generate(snap1)

        # Critical drift immediately after → should NOT be suppressed
        snap2 = _base_snapshot(drift_magnitude=0.6, drift_severity="critical")
        p2 = gen.generate(snap2)
        assert p2 is not None
        assert not p2.suppressed
        assert p2.urgency == ThoughtUrgency.CRITICAL

    def test_session_limit_reached(self):
        """No more thoughts after max_per_session."""
        gen = AutonomousThoughtGenerator(cooldown_seconds=0, min_idle=0, max_per_session=2)

        # Generate 2 thoughts
        gen.generate(_base_snapshot(turn_count=0))
        gen.generate(_base_snapshot(entropy=0.9, turn_count=1))
        assert gen.get_thought_count() == 2

        # Third should be None (limit reached)
        p3 = gen.generate(_base_snapshot(drift_magnitude=0.6, drift_severity="critical"))
        assert p3 is None

    def test_idle_requirement(self):
        """Thoughts suppressed when user is still active (< min_idle)."""
        gen = AutonomousThoughtGenerator(cooldown_seconds=0, min_idle=30)

        # User active 5 seconds ago — too recent
        snap = _base_snapshot(
            turn_count=0,
            last_user_message_time=time.time() - 5,
        )
        proposal = gen.generate(snap)
        assert proposal is None

    def test_session_reset_on_new_session(self):
        """Switching session resets thought count and history."""
        gen = AutonomousThoughtGenerator(cooldown_seconds=0, min_idle=0)

        # Generate in session 1
        gen.generate(_base_snapshot(turn_count=0, session_id="s1"))
        assert gen.get_thought_count() == 1

        # Switch to session 2 — count resets
        gen.generate(_base_snapshot(turn_count=0, session_id="s2"))
        assert gen.get_thought_count() == 1  # 1 from new session, not 2 total
        assert len(gen.get_thought_history()) == 1


# ═══════════════════════════════════════════════════════════════════════
# Feedback Discovery — 7 Tests
# ═══════════════════════════════════════════════════════════════════════

class TestFeedbackDiscovery:
    """Tests for FEEDBACK_DISCOVERY trigger and CognitiveSnapshot new fields."""

    def test_feedback_discovery_in_enum(self):
        """FEEDBACK_DISCOVERY is a valid trigger with 8 total triggers."""
        assert ThoughtTrigger.FEEDBACK_DISCOVERY == "feedback_discovery"
        assert len(ThoughtTrigger) == 8

    def test_cognitive_snapshot_new_fields(self):
        """CognitiveSnapshot has feedback-related fields with correct defaults."""
        snap = CognitiveSnapshot()
        assert snap.self_model_confidence == 0.5
        assert snap.causal_graph_density == 0.0
        assert snap.causal_edges_discovered == 0
        assert snap.feedback_channel_active is False

    def test_feedback_causal_edges_triggers(self):
        """Causal edge discovery triggers FEEDBACK_DISCOVERY."""
        gen = AutonomousThoughtGenerator(cooldown_seconds=0, min_idle=0)
        snap = _base_snapshot(
            feedback_channel_active=True,
            causal_edges_discovered=3,
            causal_graph_density=0.15,
        )
        proposal = gen.generate(snap)
        assert proposal is not None
        assert proposal.trigger == ThoughtTrigger.FEEDBACK_DISCOVERY
        assert proposal.urgency == ThoughtUrgency.HIGH
        assert "nedensel kenar" in proposal.prompt

    def test_feedback_confidence_shift_triggers(self):
        """Confidence shift beyond threshold triggers FEEDBACK_DISCOVERY."""
        gen = AutonomousThoughtGenerator(cooldown_seconds=0, min_idle=0)
        snap = _base_snapshot(
            feedback_channel_active=True,
            self_model_confidence=0.72,  # shift = 0.22 > 0.15 threshold
            causal_edges_discovered=0,
        )
        proposal = gen.generate(snap)
        assert proposal is not None
        assert proposal.trigger == ThoughtTrigger.FEEDBACK_DISCOVERY
        assert "guven" in proposal.prompt

    def test_no_trigger_when_inactive(self):
        """feedback_channel_active=False prevents FEEDBACK_DISCOVERY even with edges."""
        gen = AutonomousThoughtGenerator(cooldown_seconds=0, min_idle=0)
        snap = _base_snapshot(
            feedback_channel_active=False,
            causal_edges_discovered=5,
            self_model_confidence=0.8,
        )
        # Should NOT get feedback_discovery (inactive), but might get other triggers
        proposal = gen.generate(snap)
        if proposal is not None:
            assert proposal.trigger != ThoughtTrigger.FEEDBACK_DISCOVERY

    def test_priority_above_physics(self):
        """FEEDBACK_DISCOVERY fires before PHYSICS_ANOMALY."""
        gen = AutonomousThoughtGenerator(cooldown_seconds=0, min_idle=0)
        snap = _base_snapshot(
            feedback_channel_active=True,
            causal_edges_discovered=2,
            entropy=0.9,  # would trigger physics anomaly
        )
        proposal = gen.generate(snap)
        assert proposal is not None
        assert proposal.trigger == ThoughtTrigger.FEEDBACK_DISCOVERY

    def test_priority_below_drift(self):
        """Critical drift still has higher priority than FEEDBACK_DISCOVERY."""
        gen = AutonomousThoughtGenerator(cooldown_seconds=0, min_idle=0)
        snap = _base_snapshot(
            drift_magnitude=0.6,
            drift_severity="critical",
            feedback_channel_active=True,
            causal_edges_discovered=5,
        )
        proposal = gen.generate(snap)
        assert proposal is not None
        assert proposal.trigger == ThoughtTrigger.DRIFT_DETECTED
