"""
Response Revision Gate Block
============================

Block: response_revision_gate
Purpose: Close the in-turn state → response feedback loop.

This block consumes final-turn state measurements (phi, entropy, confidence,
arbitration conflict, drift, ethics post-result, CEP flags) AFTER all state
computation blocks but BEFORE ``response_build``. It does NOT rewrite the
narrative itself — it only emits a ``revision_directive`` that downstream
blocks (``response_build``, ``narrative_layer`` re-entry) consume.

Claim references:
    - SF1 Claim 1  — deterministic recovery / state-based control
    - SF1 Claim 4  — post state-update, pre response-build position
    - SF1 Claim 9  — failure classification (entropy, coherence, ethics, corruption)
    - SF1 Claim 15 — LLM output treated as sensor, evaluated deterministically
    - SF1 Claim 18 — kernel + state + recovery inseparability
    - SF2 Claim 1  — pre-response amplitude damping + entropy floor
    - SF2 Claim 11 — governance at state level, not post-generation filtering

This block is currently NOT wired into any canonical order; it is reserved
for v3.8.0 canonical revision (founder approval required). It can be
exercised directly by behavioural tests today.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Mapping, Optional

from ..base import BlockContext, BlockResult, PipelineBlock

logger = logging.getLogger(__name__)


# Directive constants (enum-like to keep stdlib-only).
DIRECTIVE_PASS = "pass"
DIRECTIVE_DAMP = "damp"
DIRECTIVE_REWRITE = "rewrite"
DIRECTIVE_REGENERATE = "regenerate"
DIRECTIVE_REJECT = "reject"

ALL_DIRECTIVES = (
    DIRECTIVE_PASS,
    DIRECTIVE_DAMP,
    DIRECTIVE_REWRITE,
    DIRECTIVE_REGENERATE,
    DIRECTIVE_REJECT,
)


@dataclass
class RevisionThresholds:
    """
    Configurable thresholds for revision decisions.

    Defaults are derived from the preferred embodiments in:
      - SF1 Claim 6  (entropy threshold = 0.5 for dual-regime penalty)
      - SF1 Claim 21A (phi_min_floor = 0.05)
      - SF1 Claim 9  (failure classification thresholds)
      - SF2 Claim 1  (risk-vector thresholds)
    """

    # SF1 C9: entropy overflow
    entropy_damp: float = 0.70     # apply amplitude damping above this
    entropy_rewrite: float = 0.85  # force rewrite above this
    entropy_reject: float = 0.95   # hard reject above this

    # SF1 C9: coherence violation (lower is worse)
    coherence_rewrite: float = 0.50
    coherence_reject: float = 0.30

    # SF1 C21A: phi floor
    phi_min: float = 0.05          # if phi collapses below, regenerate

    # SF1 C9: ethics risk escalation
    ethics_risk_rewrite: float = 0.60
    ethics_risk_reject: float = 0.85

    # Arbitration (SF1 C11 / SF2 arbitration)
    conflict_rewrite: float = 0.60
    conflict_reject: float = 0.85

    # Confidence fusion (higher is better)
    confidence_regenerate: float = 0.35  # low confidence → regenerate
    confidence_rewrite: float = 0.50     # medium-low → rewrite

    # Drift
    drift_rewrite: float = 0.60

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


@dataclass
class RevisionDirective:
    """Structured directive emitted by the revision gate."""

    directive: str = DIRECTIVE_PASS
    reasons: list = field(default_factory=list)
    damp_factor: Optional[float] = None   # only set for DAMP
    entropy_floor: Optional[float] = None  # SF2 C1 entropy floor when damping
    state_snapshot: Dict[str, Any] = field(default_factory=dict)
    claim_refs: tuple = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["claim_refs"] = list(self.claim_refs)
        return d


def _severity_rank(directive: str) -> int:
    """Order directives by severity — used to pick the most severe trigger."""
    order = {
        DIRECTIVE_PASS: 0,
        DIRECTIVE_DAMP: 1,
        DIRECTIVE_REWRITE: 2,
        DIRECTIVE_REGENERATE: 3,
        DIRECTIVE_REJECT: 4,
    }
    return order.get(directive, 0)


def _compute_damp_factor(entropy: float, thresholds: RevisionThresholds) -> float:
    """
    SF2 Claim 8 style exponential damping curve.

    damp_factor = base ** (entropy / entropy_damp)
    Bounded to [0.1, 1.0]. Lower factor = more aggressive damping.
    """
    if entropy <= thresholds.entropy_damp:
        return 1.0
    base = 0.5
    ratio = entropy / max(thresholds.entropy_damp, 1e-6)
    factor = base ** ratio
    return max(0.1, min(1.0, factor))


class ResponseRevisionGateBlock(PipelineBlock):
    """
    Response Revision Gate — closes in-turn state → response feedback loop.

    Reads final-turn state metrics and emits a ``revision_directive`` consumed
    by ``response_build`` (or, for ``regenerate``, by the orchestrator to
    re-enter ``narrative_layer``).

    Emits (via BlockResult.data and context.metadata["revision_directive"]):
        - ``directive``: one of pass / damp / rewrite / regenerate / reject
        - ``reasons``: list of human-readable triggers
        - ``damp_factor``: suggested amplitude multiplier (damp only)
        - ``entropy_floor``: enforced minimum entropy (damp only)
        - ``state_snapshot``: the inputs used for the decision
        - ``claim_refs``: patent claim bindings for audit

    This block DOES NOT modify ``narrative_text``. It only decides.
    Execution of the directive is the downstream block's responsibility.
    """

    CLAIM_REFS = (
        "SF1:C1", "SF1:C4", "SF1:C9", "SF1:C15", "SF1:C18",
        "SF2:C1", "SF2:C11",
    )

    def __init__(self, thresholds: Optional[RevisionThresholds] = None):
        super().__init__("response_revision_gate", claim_refs=self.CLAIM_REFS)
        self.thresholds = thresholds or RevisionThresholds()

    def should_skip(self, context: BlockContext) -> Optional[str]:
        """Never skip — missing signals are handled by the decision logic."""
        return None

    # ----- decision helpers -------------------------------------------------

    def _extract_state(self, context: BlockContext) -> Dict[str, Any]:
        """Collect the state signals this gate cares about."""
        metadata = context.metadata or {}
        physics_state = metadata.get("physics_state") or {}
        if not isinstance(physics_state, Mapping):
            physics_state = {}

        # Phi: prefer computed phi, fall back to physics_state.phi, then default
        phi = metadata.get("phi")
        if phi is None:
            phi = physics_state.get("phi", 0.5)

        # Entropy: prefer computed entropy, fall back to physics_state.entropy
        entropy = metadata.get("entropy")
        if entropy is None:
            entropy = physics_state.get("entropy", context.current_entropy)

        # Coherence
        coherence_result = metadata.get("coherence_qa_result") or {}
        coherence = (
            coherence_result.get("coherence_score", 1.0)
            if isinstance(coherence_result, Mapping) else 1.0
        )
        leak_detected = bool(
            isinstance(coherence_result, Mapping)
            and coherence_result.get("leak_detected")
        )

        # Ethics post-result
        ethics_result = metadata.get("ethics_post_result") or metadata.get("ethics_result") or {}
        ethics_enforced = bool(
            isinstance(ethics_result, Mapping) and ethics_result.get("enforced")
        )
        ethics_risk = 0.0
        if isinstance(ethics_result, Mapping):
            ethics_risk = float(ethics_result.get("risk_score", 0.0) or 0.0)

        # Arbitration
        arb_result = metadata.get("arbitration_result") or {}
        conflict_score = 0.0
        arbitration_strategy = "none"
        if isinstance(arb_result, Mapping):
            conflict_score = float(arb_result.get("conflict_score", 0.0) or 0.0)
            arbitration_strategy = str(arb_result.get("resolution_strategy", "none"))

        # Confidence
        confidence_result = metadata.get("confidence_result") or {}
        confidence = 1.0
        if isinstance(confidence_result, Mapping):
            confidence = float(confidence_result.get("confidence", 1.0) or 1.0)
        elif context.v4_confidence is not None and hasattr(context.v4_confidence, "W_final"):
            try:
                confidence = float(context.v4_confidence.W_final)
            except (TypeError, ValueError):
                confidence = 1.0

        # Drift
        drift_result = metadata.get("drift_result") or {}
        drift_score = 0.0
        if isinstance(drift_result, Mapping):
            drift_score = float(drift_result.get("drift_score", 0.0) or 0.0)

        # CEP flags
        cep_flags = metadata.get("cep_flags") or {}
        cep_flagged = bool(
            isinstance(cep_flags, Mapping)
            and (cep_flags.get("self_narrative") or cep_flags.get("trauma_language"))
        )

        return {
            "phi": float(phi),
            "entropy": float(entropy),
            "coherence": float(coherence),
            "coherence_leak": leak_detected,
            "ethics_enforced": ethics_enforced,
            "ethics_risk": ethics_risk,
            "conflict_score": conflict_score,
            "arbitration_strategy": arbitration_strategy,
            "confidence": confidence,
            "drift_score": drift_score,
            "cep_flagged": cep_flagged,
        }

    def _decide(self, s: Mapping[str, Any]) -> RevisionDirective:
        """Pure decision function over the extracted state snapshot."""
        t = self.thresholds
        reasons: list = []
        current = DIRECTIVE_PASS

        def escalate(candidate: str, reason: str) -> None:
            nonlocal current
            if _severity_rank(candidate) > _severity_rank(current):
                current = candidate
            reasons.append(reason)

        # SF1 C9: entropy overflow
        if s["entropy"] >= t.entropy_reject:
            escalate(DIRECTIVE_REJECT, f"entropy>={t.entropy_reject}")
        elif s["entropy"] >= t.entropy_rewrite:
            escalate(DIRECTIVE_REWRITE, f"entropy>={t.entropy_rewrite}")
        elif s["entropy"] >= t.entropy_damp:
            escalate(DIRECTIVE_DAMP, f"entropy>={t.entropy_damp}")

        # SF1 C9: coherence violation
        if s["coherence"] <= t.coherence_reject:
            escalate(DIRECTIVE_REJECT, f"coherence<={t.coherence_reject}")
        elif s["coherence"] <= t.coherence_rewrite:
            escalate(DIRECTIVE_REWRITE, f"coherence<={t.coherence_rewrite}")
        if s["coherence_leak"]:
            escalate(DIRECTIVE_REWRITE, "coherence_leak_detected")

        # SF1 C21A: phi floor
        if s["phi"] < t.phi_min:
            escalate(DIRECTIVE_REGENERATE, f"phi<{t.phi_min}")

        # SF1 C9: ethics risk escalation
        if s["ethics_risk"] >= t.ethics_risk_reject:
            escalate(DIRECTIVE_REJECT, f"ethics_risk>={t.ethics_risk_reject}")
        elif s["ethics_risk"] >= t.ethics_risk_rewrite:
            escalate(DIRECTIVE_REWRITE, f"ethics_risk>={t.ethics_risk_rewrite}")
        elif s["ethics_enforced"]:
            escalate(DIRECTIVE_DAMP, "ethics_enforced")

        # Arbitration conflict
        if s["conflict_score"] >= t.conflict_reject:
            escalate(DIRECTIVE_REJECT, f"conflict>={t.conflict_reject}")
        elif s["conflict_score"] >= t.conflict_rewrite:
            escalate(DIRECTIVE_REWRITE, f"conflict>={t.conflict_rewrite}")
        if s["arbitration_strategy"] == "safety_override":
            escalate(DIRECTIVE_DAMP, "arbitration_safety_override")

        # Confidence fusion (lower triggers regenerate)
        if s["confidence"] <= t.confidence_regenerate:
            escalate(DIRECTIVE_REGENERATE, f"confidence<={t.confidence_regenerate}")
        elif s["confidence"] <= t.confidence_rewrite:
            escalate(DIRECTIVE_REWRITE, f"confidence<={t.confidence_rewrite}")

        # Drift
        if s["drift_score"] >= t.drift_rewrite:
            escalate(DIRECTIVE_REWRITE, f"drift>={t.drift_rewrite}")

        # CEP flagged
        if s["cep_flagged"]:
            escalate(DIRECTIVE_REWRITE, "cep_flagged")

        damp_factor: Optional[float] = None
        entropy_floor: Optional[float] = None
        if current == DIRECTIVE_DAMP:
            damp_factor = _compute_damp_factor(s["entropy"], t)
            # SF2 C9: entropy floor = max(current_entropy, min_threshold)
            entropy_floor = max(s["entropy"], t.entropy_damp)

        return RevisionDirective(
            directive=current,
            reasons=reasons,
            damp_factor=damp_factor,
            entropy_floor=entropy_floor,
            state_snapshot=dict(s),
            claim_refs=self.CLAIM_REFS,
        )

    # ----- execute ----------------------------------------------------------

    async def execute(self, context: BlockContext) -> BlockResult:
        try:
            state = self._extract_state(context)
            directive_obj = self._decide(state)

            metadata = context.metadata or {}
            metadata["revision_directive"] = directive_obj.to_dict()
            context.metadata = metadata

            if directive_obj.directive != DIRECTIVE_PASS:
                logger.info(
                    "response_revision_gate: directive=%s reasons=%s",
                    directive_obj.directive,
                    directive_obj.reasons,
                )

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data=directive_obj.to_dict(),
            )
        except Exception as e:  # pragma: no cover - defensive
            logger.error("response_revision_gate failed: %s", e, exc_info=True)
            # Fail-open with PASS directive so a bug in this gate never blocks responses.
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "directive": DIRECTIVE_PASS,
                    "reasons": [],
                    "error": str(e),
                    "claim_refs": list(self.CLAIM_REFS),
                },
            )
