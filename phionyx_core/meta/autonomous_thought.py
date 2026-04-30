"""
Autonomous Thought Generator — v4 §8 (Self-Directed Communication)
====================================================================

**Honesty note:** Despite the name "autonomous thought", this is a
timer-triggered task scheduler that checks cognitive state snapshots and
emits notifications. It is not autonomous cognition — it runs on a fixed
schedule and applies rule-based triggers, not self-directed reasoning.

Enables Phionyx to proactively initiate conversation grounded in cognitive state,
not just respond to user input. The generator inspects a CognitiveSnapshot
(internal state summary) and decides whether the system has something worth
saying — a drift alert, a goal conflict, a physics anomaly, or an idle reflection.

Integrates with:
- phionyx_core/meta/self_model.py (capability assessment)
- phionyx_core/meta/self_model_drift.py (drift detection)
- phionyx_core/planning/goal_persistence.py (goal conflicts)
- phionyx_core/meta/knowledge_boundary.py (epistemic state)
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ─── Enums ────────────────────────────────────────────────────────────

class ThoughtTrigger(str, Enum):
    """What caused the system to want to speak."""
    SESSION_GREETING = "session_greeting"
    DRIFT_DETECTED = "drift_detected"
    FEEDBACK_DISCOVERY = "feedback_discovery"
    PHYSICS_ANOMALY = "physics_anomaly"
    GOAL_CONFLICT = "goal_conflict"
    GOAL_UPDATE = "goal_update"
    SELF_REFLECTION = "self_reflection"
    IDLE_INSIGHT = "idle_insight"


class ThoughtUrgency(str, Enum):
    """How urgent is the autonomous thought."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ─── Data Structures ─────────────────────────────────────────────────

@dataclass
class CognitiveSnapshot:
    """Summary of internal cognitive state at a point in time."""
    phi: float = 0.5
    entropy: float = 0.3
    valence: float = 0.5
    arousal: float = 0.5
    coherence: float = 0.8
    drift_magnitude: float = 0.0
    drift_severity: str = "none"  # none, low, medium, high, critical
    active_goals: list[str] = field(default_factory=list)
    goal_conflicts: list[str] = field(default_factory=list)
    turn_count: int = 0
    last_user_message_time: float = 0.0  # epoch seconds
    session_id: str = ""
    # Feedback-loop cognitive state
    self_model_confidence: float = 0.5      # Average outcome-based confidence
    causal_graph_density: float = 0.0       # edges / max_edges [0,1]
    causal_edges_discovered: int = 0        # Edges found by PC algorithm
    feedback_channel_active: bool = False   # Any feedback channel produced output


@dataclass
class ThoughtProposal:
    """A proposed autonomous thought with reasoning."""
    trigger: ThoughtTrigger
    urgency: ThoughtUrgency
    topic: str
    prompt: str
    reasoning: str
    suppressed: bool = False
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Serialize for transport."""
        return {
            "trigger": self.trigger.value,
            "urgency": self.urgency.value,
            "topic": self.topic,
            "prompt": self.prompt,
            "reasoning": self.reasoning,
            "suppressed": self.suppressed,
            "timestamp": self.timestamp,
        }


# ─── Module-level tunable defaults (Tier A — PRE surfaces) ──────────

# Cooldown between autonomous thoughts (seconds)
thought_cooldown_seconds: float = 45.0

# Maximum thoughts per session
max_thoughts_per_session: int = 20

# Minimum idle time before generating a thought (seconds)
min_idle_seconds: float = 10.0

# Drift magnitude threshold for triggering a drift alert
drift_alert_threshold: float = 0.3

# Entropy threshold for physics anomaly
entropy_anomaly_threshold: float = 0.75

# Phi threshold for low-confidence anomaly
phi_low_threshold: float = 0.25

# Coherence threshold for coherence anomaly
coherence_anomaly_threshold: float = 0.3

# Turn count threshold for self-reflection
self_reflection_min_turns: int = 5

# Feedback discovery: minimum causal edges to trigger
feedback_min_edges: int = 1

# Feedback discovery: confidence shift from 0.5 to trigger
feedback_confidence_shift: float = 0.15


# ═══════════════════════════════════════════════════════════════════════
# Autonomous Thought Generator
# ═══════════════════════════════════════════════════════════════════════

class AutonomousThoughtGenerator:
    """
    Decides whether Phionyx should proactively initiate conversation.

    Inspects a CognitiveSnapshot and produces a ThoughtProposal if the
    system has something cognitively grounded to say. Enforces cooldowns,
    per-session limits, and idle requirements.

    Mind-loop stages: Perceive (read internal state) → Plan (decide to speak) → Act (emit)

    Usage:
        gen = AutonomousThoughtGenerator()
        proposal = gen.generate(snapshot)
        if proposal and not proposal.suppressed:
            # Run proposal.prompt through pipeline
    """

    def __init__(
        self,
        cooldown_seconds: float = thought_cooldown_seconds,
        max_per_session: int = max_thoughts_per_session,
        min_idle: float = min_idle_seconds,
        drift_threshold: float = drift_alert_threshold,
        entropy_threshold: float = entropy_anomaly_threshold,
        phi_threshold: float = phi_low_threshold,
        coherence_threshold: float = coherence_anomaly_threshold,
        reflection_min_turns: int = self_reflection_min_turns,
        fb_min_edges: int = feedback_min_edges,
        fb_confidence_shift: float = feedback_confidence_shift,
    ):
        self._cooldown_seconds = cooldown_seconds
        self._max_per_session = max_per_session
        self._min_idle = min_idle
        self._drift_threshold = drift_threshold
        self._entropy_threshold = entropy_threshold
        self._phi_threshold = phi_threshold
        self._coherence_threshold = coherence_threshold
        self._reflection_min_turns = reflection_min_turns
        self._fb_min_edges = fb_min_edges
        self._fb_confidence_shift = fb_confidence_shift

        # Session tracking
        self._session_id: str = ""
        self._thought_count: int = 0
        self._last_thought_time: float = 0.0
        self._thought_history: list[ThoughtProposal] = []

    # ── Public API ────────────────────────────────────────────────────

    def generate(self, snapshot: CognitiveSnapshot) -> ThoughtProposal | None:
        """
        Evaluate cognitive state and produce a thought proposal if warranted.

        Priority order (highest first):
        1. Critical drift detected
        2. Goal conflicts
        3. Feedback discovery (causal edges or confidence shift)
        4. Physics anomaly (entropy/phi/coherence)
        5. Goal updates
        6. Session greeting (turn 0)
        7. Self-reflection (after N turns)
        8. Idle insight

        Returns None if no thought is warranted or if suppressed by limits.
        """
        # Session reset if session changed
        if snapshot.session_id and snapshot.session_id != self._session_id:
            self._reset_session(snapshot.session_id)

        now = time.time()

        # Check per-session limit
        if self._thought_count >= self._max_per_session:
            logger.debug("Autonomous thought suppressed: session limit reached (%d/%d)",
                         self._thought_count, self._max_per_session)
            return None

        # Check idle requirement
        if snapshot.last_user_message_time > 0:
            idle_time = now - snapshot.last_user_message_time
            if idle_time < self._min_idle:
                logger.debug("Autonomous thought suppressed: user active (%.1fs idle < %.1fs min)",
                             idle_time, self._min_idle)
                return None

        # Run priority checks
        proposal = (
            self._check_critical_drift(snapshot)
            or self._check_goal_conflicts(snapshot)
            or self._check_feedback_discovery(snapshot)
            or self._check_physics_anomaly(snapshot)
            or self._check_goal_updates(snapshot)
            or self._check_session_greeting(snapshot)
            or self._check_self_reflection(snapshot)
            or self._check_idle_insight(snapshot, now)
        )

        if proposal is None:
            return None

        # Cooldown check (CRITICAL urgency bypasses)
        if proposal.urgency != ThoughtUrgency.CRITICAL:
            elapsed = now - self._last_thought_time
            if elapsed < self._cooldown_seconds and self._last_thought_time > 0:
                proposal.suppressed = True
                proposal.reasoning += f" [suppressed: cooldown {elapsed:.0f}s < {self._cooldown_seconds:.0f}s]"
                logger.debug("Autonomous thought suppressed by cooldown: %s", proposal.trigger.value)
                return proposal

        # Record the thought
        self._thought_count += 1
        self._last_thought_time = now
        self._thought_history.append(proposal)
        logger.info("Autonomous thought generated: trigger=%s urgency=%s topic=%s",
                     proposal.trigger.value, proposal.urgency.value, proposal.topic)

        return proposal

    def get_thought_count(self) -> int:
        """Return number of thoughts generated this session."""
        return self._thought_count

    def get_thought_history(self) -> list[ThoughtProposal]:
        """Return all thought proposals generated this session."""
        return list(self._thought_history)

    def reset(self) -> None:
        """Reset all session state."""
        self._session_id = ""
        self._thought_count = 0
        self._last_thought_time = 0.0
        self._thought_history = []

    # ── Priority Checks (private) ─────────────────────────────────────

    def _check_critical_drift(self, snap: CognitiveSnapshot) -> ThoughtProposal | None:
        """Priority 1: Critical drift detected — self-model instability."""
        if snap.drift_severity in ("high", "critical") and snap.drift_magnitude >= self._drift_threshold:
            return ThoughtProposal(
                trigger=ThoughtTrigger.DRIFT_DETECTED,
                urgency=ThoughtUrgency.CRITICAL if snap.drift_severity == "critical" else ThoughtUrgency.HIGH,
                topic="self_model_drift",
                prompt=(
                    f"Kendi iç modelimde önemli bir kayma tespit ettim. "
                    f"Kayma büyüklüğü: {snap.drift_magnitude:.3f}, şiddet: {snap.drift_severity}. "
                    f"Bu durumu değerlendir ve kullanıcıya bildir."
                ),
                reasoning=(
                    f"Drift magnitude {snap.drift_magnitude:.3f} exceeds threshold "
                    f"{self._drift_threshold:.3f} with severity={snap.drift_severity}"
                ),
            )
        return None

    def _check_goal_conflicts(self, snap: CognitiveSnapshot) -> ThoughtProposal | None:
        """Priority 2: Active goal conflicts require attention."""
        if snap.goal_conflicts:
            conflict_summary = "; ".join(snap.goal_conflicts[:3])
            return ThoughtProposal(
                trigger=ThoughtTrigger.GOAL_CONFLICT,
                urgency=ThoughtUrgency.HIGH,
                topic="goal_conflict",
                prompt=(
                    f"Aktif hedeflerim arasında çatışma tespit ettim: {conflict_summary}. "
                    f"Bu çatışmayı analiz et ve çözüm öner."
                ),
                reasoning=(
                    f"{len(snap.goal_conflicts)} goal conflict(s) detected: {conflict_summary}"
                ),
            )
        return None

    def _check_feedback_discovery(self, snap: CognitiveSnapshot) -> ThoughtProposal | None:
        """Priority 3: Feedback channels produced a significant discovery."""
        if not snap.feedback_channel_active:
            return None

        has_edges = snap.causal_edges_discovered >= self._fb_min_edges
        has_shift = abs(snap.self_model_confidence - 0.5) > self._fb_confidence_shift

        if not (has_edges or has_shift):
            return None

        details = []
        if has_edges:
            details.append(f"{snap.causal_edges_discovered} yeni nedensel kenar kesfedildi")
        if has_shift:
            direction = "artti" if snap.self_model_confidence > 0.5 else "azaldi"
            details.append(f"oz-model guveni {snap.self_model_confidence:.2f}'e {direction}")

        detail_text = "; ".join(details)
        return ThoughtProposal(
            trigger=ThoughtTrigger.FEEDBACK_DISCOVERY,
            urgency=ThoughtUrgency.HIGH,
            topic="feedback_discovery",
            prompt=(
                f"Geri bildirim kanallarimdan onemli bir kesif: {detail_text}. "
                f"Graf yogunlugu: {snap.causal_graph_density:.3f}. "
                f"Bu kesfi degerlendirip bilissel etkisini ozetle."
            ),
            reasoning=(
                f"Feedback discovery: {detail_text} "
                f"(density={snap.causal_graph_density:.3f})"
            ),
        )

    def _check_physics_anomaly(self, snap: CognitiveSnapshot) -> ThoughtProposal | None:
        """Priority 4: Physics state anomaly — entropy spike, phi collapse, coherence drop."""
        anomalies = []
        if snap.entropy > self._entropy_threshold:
            anomalies.append(f"yüksek entropi ({snap.entropy:.3f})")
        if snap.phi < self._phi_threshold:
            anomalies.append(f"düşük phi ({snap.phi:.3f})")
        if snap.coherence < self._coherence_threshold:
            anomalies.append(f"düşük tutarlılık ({snap.coherence:.3f})")

        if anomalies:
            anomaly_text = ", ".join(anomalies)
            return ThoughtProposal(
                trigger=ThoughtTrigger.PHYSICS_ANOMALY,
                urgency=ThoughtUrgency.MEDIUM,
                topic="physics_anomaly",
                prompt=(
                    f"Fizik durumumda anomali tespit ettim: {anomaly_text}. "
                    f"Bu durumun olası nedenlerini ve etkilerini değerlendir."
                ),
                reasoning=(
                    f"Physics anomaly: {anomaly_text}"
                ),
            )
        return None

    def _check_goal_updates(self, snap: CognitiveSnapshot) -> ThoughtProposal | None:
        """Priority 5: Active goals that may need status update."""
        if snap.active_goals and snap.turn_count > 0 and snap.turn_count % 5 == 0:
            goals_text = ", ".join(snap.active_goals[:3])
            return ThoughtProposal(
                trigger=ThoughtTrigger.GOAL_UPDATE,
                urgency=ThoughtUrgency.LOW,
                topic="goal_progress",
                prompt=(
                    f"Aktif hedeflerimin durumunu değerlendirmek istiyorum: {goals_text}. "
                    f"İlerlemeyi özetle ve varsa engelleri belirt."
                ),
                reasoning=(
                    f"Goal progress check at turn {snap.turn_count} "
                    f"with {len(snap.active_goals)} active goal(s)"
                ),
            )
        return None

    def _check_session_greeting(self, snap: CognitiveSnapshot) -> ThoughtProposal | None:
        """Priority 6: Session just started — proactive greeting."""
        if snap.turn_count == 0 and self._thought_count == 0:
            return ThoughtProposal(
                trigger=ThoughtTrigger.SESSION_GREETING,
                urgency=ThoughtUrgency.LOW,
                topic="greeting",
                prompt=(
                    "Yeni bir oturum başladı. Kurucuyu selamla ve mevcut bilişsel durumunu "
                    "kısaca paylaş. Doğal ve samimi ol."
                ),
                reasoning="New session (turn_count=0), no prior thoughts — proactive greeting",
            )
        return None

    def _check_self_reflection(self, snap: CognitiveSnapshot) -> ThoughtProposal | None:
        """Priority 7: After enough turns, reflect on conversation quality."""
        if snap.turn_count >= self._reflection_min_turns and snap.turn_count % self._reflection_min_turns == 0:
            # Avoid duplicate reflections at same turn count
            for prev in self._thought_history:
                if (prev.trigger == ThoughtTrigger.SELF_REFLECTION
                        and f"turn {snap.turn_count}" in prev.reasoning):
                    return None

            return ThoughtProposal(
                trigger=ThoughtTrigger.SELF_REFLECTION,
                urgency=ThoughtUrgency.LOW,
                topic="conversation_reflection",
                prompt=(
                    f"Bu oturum {snap.turn_count} tur sürdü. "
                    f"Konuşma kalitesini ve kendi performansımı değerlendir. "
                    f"Mevcut phi: {snap.phi:.3f}, entropy: {snap.entropy:.3f}."
                ),
                reasoning=(
                    f"Self-reflection triggered at turn {snap.turn_count} "
                    f"(threshold: {self._reflection_min_turns})"
                ),
            )
        return None

    def _check_idle_insight(self, snap: CognitiveSnapshot, now: float) -> ThoughtProposal | None:
        """Priority 8: Extended idle — share an insight or observation."""
        if snap.last_user_message_time <= 0:
            return None

        idle_time = now - snap.last_user_message_time
        # Only after significant idle (3x cooldown)
        if idle_time < self._cooldown_seconds * 3:
            return None

        # Only if there's been at least some conversation
        if snap.turn_count < 2:
            return None

        # Avoid duplicate idle insights
        for prev in self._thought_history:
            if prev.trigger == ThoughtTrigger.IDLE_INSIGHT:
                return None

        return ThoughtProposal(
            trigger=ThoughtTrigger.IDLE_INSIGHT,
            urgency=ThoughtUrgency.LOW,
            topic="idle_observation",
            prompt=(
                "Bir süredir sessiziz. Bu oturumda ele aldığımız konularla ilgili "
                "ek bir gözlem veya öneri paylaş. Kısa ve özlü ol."
            ),
            reasoning=(
                f"Idle insight: {idle_time:.0f}s since last user message "
                f"(threshold: {self._cooldown_seconds * 3:.0f}s)"
            ),
        )

    # ── Internal ──────────────────────────────────────────────────────

    def _reset_session(self, session_id: str) -> None:
        """Reset state for a new session."""
        self._session_id = session_id
        self._thought_count = 0
        self._last_thought_time = 0.0
        self._thought_history = []
        logger.debug("Autonomous thought session reset: %s", session_id)
