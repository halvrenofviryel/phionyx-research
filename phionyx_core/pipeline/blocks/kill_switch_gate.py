"""
Kill Switch Gate Block
======================

Block: kill_switch_gate
Evaluates kill switch conditions each turn. If triggered, forces early exit
with shutdown signal. Integrates with ethics, meta-cognition, and drift detection.

Position in pipeline: After confidence_fusion, before narrative_layer.
"""

import logging
from typing import Any

from ..base import BlockContext, BlockResult, PipelineBlock

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

    def __init__(self, kill_switch=None):
        """
        Args:
            kill_switch: KillSwitch instance (injected via DI)
        """
        super().__init__("kill_switch_gate")
        self._kill_switch = kill_switch

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Evaluate kill switch conditions.

        Reads metrics from previous pipeline blocks via context.metadata.
        """
        if self._kill_switch is None:
            return BlockResult(
                block_id=self.block_id,
                status="skipped",
                data={"reason": "No kill switch instance configured"}
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
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={
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

    def _extract_ethics_risk(self, metadata: dict[str, Any]) -> float:
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

    def _extract_t_meta(self, metadata: dict[str, Any]) -> float:
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

    def _extract_drift(self, metadata: dict[str, Any]) -> bool:
        """Extract drift detection status."""
        drift_result = metadata.get("drift_result")
        if drift_result:
            if hasattr(drift_result, "drift_detected"):
                return drift_result.drift_detected
            if isinstance(drift_result, dict):
                return drift_result.get("drift_detected", False)
        return False
