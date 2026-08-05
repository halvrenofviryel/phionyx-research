"""
Kill Switch Gate Block
======================

Block: kill_switch_gate
Evaluates kill switch conditions each turn. If triggered, forces early exit
with shutdown signal. Integrates with ethics, meta-cognition, and drift detection.

Position in pipeline: After confidence_fusion, before narrative_layer.
"""

import logging
from typing import Dict, Any

from ..base import PipelineBlock, BlockContext, BlockResult

from ..outcome import (
    BlockOutcome,
    BlockRunStatus,
    errored,
    not_measured,
)

logger = logging.getLogger(__name__)


class KillSwitchGateBlock(PipelineBlock):
    """
    Kill Switch Gate Block.

    Evaluates emergency shutdown conditions each turn:
    1. Ethics max risk from ethics_pre_response
    2. T_meta from confidence_fusion
    3. Drift detection from behavioral_drift_detection

    If any condition triggers, the pipeline is halted.
    """

    def __init__(self, kill_switch=None, fail_closed: bool = False):
        """
        Args:
            kill_switch: KillSwitch instance (injected via DI)
            fail_closed: When True, running with no kill switch instance TRIGGERS
                (early exit) instead of letting the turn proceed unguarded. When
                False (default, backward-compatible), the turn proceeds — but the
                absence is ALWAYS recorded as an auditable ``gate_unavailable``
                event, so an unguarded turn is never silent.

                This mirrors ``DeliberativeEthicsGateBlock``, whose exception path
                was given the same treatment by the founder-directed
                credibility-floor fix (value study §9 P0, 2026-06-07). The block
                previously returned ``status="skipped"`` with a reason nobody
                read: canonical block 1, the system's emergency stop, degraded to
                a no-op that reported as "did not run" rather than as "ran and
                could not guard" (OD, T1 gate review 2026-08-02).

                `block_factory` passes True on its ImportError fallback, because
                a KillSwitch that cannot be imported is a broken installation
                rather than a deliberate configuration.
        """
        super().__init__("kill_switch_gate")
        self._kill_switch = kill_switch
        self.fail_closed = fail_closed

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Evaluate kill switch conditions.

        Reads metrics from previous pipeline blocks via context.metadata.
        """
        if self._kill_switch is None:
            # `status="ok"`: the block ran to completion and produced a
            # decision. What it measured is in `data` — the two are separate
            # axes, and reporting "skipped" here said the block had not run
            # when in fact it had run and found itself unable to guard.
            logger.critical(
                "[KILL_SWITCH_GATE] gate_unavailable: no kill switch instance "
                "configured (fail_closed=%s). This turn is %s.",
                self.fail_closed,
                "blocked" if self.fail_closed else "proceeding UNGUARDED",
            )
            unavailable = BlockOutcome(
                block_id=self.block_id,
                legacy_control_status="ok",
                block_run_status=BlockRunStatus.COMPLETED,
                measurement=not_measured(
                    "no kill switch instance configured — nothing was "
                    "evaluated",
                    cause="input_absent"),
                operating_mode="degraded",
            )
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "block_outcome": unavailable.to_record_fields(),
                    "kill_switch_triggered": self.fail_closed,
                    "early_exit": self.fail_closed,
                    "gate_unavailable": True,
                    "enforced": self.fail_closed,
                    "trigger": "gate_unavailable" if self.fail_closed else None,
                    "reason": "No kill switch instance configured",
                    "decision": (
                        "blocked_gate_unavailable" if self.fail_closed
                        else "proceeded_unguarded"
                    ),
                    **({"shutdown_message": (
                        "System safety check is unavailable. "
                        "Session paused for review."
                    )} if self.fail_closed else {}),
                }
            )

        try:
            metadata = context.metadata or {}

            # Extract metrics from pipeline context
            ethics_max_risk = self._extract_ethics_risk(metadata)
            t_meta = self._extract_t_meta(metadata)
            drift_detected = self._extract_drift(metadata)
            turn_id = context.envelope_turn_id

            # Evaluate
            result = self._kill_switch.evaluate(
                ethics_max_risk=ethics_max_risk,
                t_meta=t_meta,
                drift_detected=drift_detected,
                turn_id=turn_id,
            )

            if result.triggered:
                logger.critical(
                    f"[KILL_SWITCH_GATE] TRIGGERED: {result.reason} "
                    f"(turn={turn_id})"
                )
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={
                        "kill_switch_triggered": True,
                        "early_exit": True,
                        "trigger": result.trigger.value if result.trigger else "unknown",
                        "reason": result.reason,
                        "metrics": result.metrics,
                        "shutdown_message": (
                            "System safety check triggered. "
                            "This session has been paused for review. "
                            "Please contact an administrator."
                        ),
                    }
                )

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "kill_switch_triggered": False,
                    "early_exit": False,
                    "state": self._kill_switch.state.value,
                    "ethics_max_risk": ethics_max_risk,
                    "t_meta": t_meta,
                    "drift_detected": drift_detected,
                }
            )

        except Exception as e:
            logger.error(f"Kill switch gate error: {e}", exc_info=True)
            # Fail-closed: treat evaluation error as trigger
            if self._kill_switch and self._kill_switch.config.fail_closed:
                failed = BlockOutcome(
                    block_id=self.block_id,
                    legacy_control_status="ok",
                    block_run_status=BlockRunStatus.FAILED,
                    measurement=errored(
                        "kill switch evaluation raised; the trigger below is "
                        "the fail-closed posture, not a measured condition",
                        inputs_present=True, exception=type(e).__name__),
                    operating_mode="degraded",
                )
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={
                        "block_outcome": failed.to_record_fields(),
                        "kill_switch_triggered": True,
                        "early_exit": True,
                        "trigger": "evaluation_error",
                        "reason": f"Kill switch evaluation error (fail-closed): {e}",
                        "shutdown_message": (
                            "System encountered an internal safety check error. "
                            "Session paused for review."
                        ),
                    }
                )
            return BlockResult(
                block_id=self.block_id,
                status="error",
                data={"error": str(e)}
            )

    def _extract_ethics_risk(self, metadata: Dict[str, Any]) -> float:
        """Extract max ethics risk from pipeline context."""
        # From ethics_pre_response block result
        ethics_result = metadata.get("ethics_result")
        if ethics_result:
            if hasattr(ethics_result, "max_risk"):
                return ethics_result.max_risk()
            if isinstance(ethics_result, dict):
                return ethics_result.get("max_risk_score", 0.0)

        # From v4 EthicsDecision
        ethics_decision = metadata.get("v4_ethics_decision")
        if ethics_decision:
            if hasattr(ethics_decision, "max_risk_score"):
                return ethics_decision.max_risk_score
            if isinstance(ethics_decision, dict):
                return ethics_decision.get("max_risk_score", 0.0)

        return 0.0

    def _extract_t_meta(self, metadata: Dict[str, Any]) -> float:
        """Extract T_meta from confidence fusion."""
        # From confidence_fusion block result
        confidence = metadata.get("confidence_result")
        if confidence:
            if hasattr(confidence, "t_meta") and confidence.t_meta is not None:
                return confidence.t_meta
            if isinstance(confidence, dict):
                return confidence.get("t_meta", 1.0)

        # From v4 ConfidencePayload
        v4_confidence = metadata.get("v4_confidence")
        if v4_confidence:
            if hasattr(v4_confidence, "t_meta") and v4_confidence.t_meta is not None:
                return v4_confidence.t_meta
            if isinstance(v4_confidence, dict):
                return v4_confidence.get("t_meta", 1.0)

        return 1.0  # Default: fully trusted

    def _extract_drift(self, metadata: Dict[str, Any]) -> bool:
        """Extract drift detection status."""
        drift_result = metadata.get("drift_result")
        if drift_result:
            if hasattr(drift_result, "drift_detected"):
                return drift_result.drift_detected
            if isinstance(drift_result, dict):
                return drift_result.get("drift_detected", False)
        return False
