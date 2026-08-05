"""
Behavioral Drift Detection Block
Pipeline-integrated drift detection for Silent Failure Firewall.
"""

from typing import Dict, Optional, cast
import logging

from ..base import PipelineBlock, BlockContext, BlockResult
from ..outcome import (
    BlockOutcome,
    BlockRunStatus,
    Observation,
    RecoveryAction,
    errored,
    measured_fail,
    measured_pass,
    not_measured,
)
from ...monitoring.behavioral_drift import (
    BehavioralDriftDetector,
)
from ...monitoring.circuit_breaker import (
    CircuitBreaker,
)

logger = logging.getLogger(__name__)


class BehavioralDriftDetectionBlock(PipelineBlock):
    """
    Behavioral drift detection block.

    Integration:
    - Insert after `ethics_post_response`
    - Before `telemetry_publish`
    - Block ID: `behavioral_drift_detection`

    Functionality:
    1. Extract current output and metrics from context
    2. Detect drift using BehavioralDriftDetector
    3. Check circuit breaker state
    4. Update context with drift information
    5. Block execution if circuit is OPEN
    """

    def __init__(
        self,
        drift_detector: Optional[BehavioralDriftDetector] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        enabled: bool = True
    ):
        """
        Initialize drift detection block.

        Args:
            drift_detector: Optional drift detector instance
            circuit_breaker: Optional circuit breaker instance
            enabled: Enable/disable drift detection
        """
        super().__init__("behavioral_drift_detection")
        self.drift_detector = drift_detector
        self.circuit_breaker = circuit_breaker
        self.enabled = enabled

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute drift detection.

        Args:
            context: Block context with state and output

        Returns:
            BlockResult with drift information
        """
        if not self.enabled:
            logger.debug("Behavioral drift detection disabled")
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={"drift_detection": "disabled"}
            )

        if not self.drift_detector:
            logger.warning("Drift detector not configured, skipping drift detection")
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={"drift_detection": "not_configured"}
            )

        try:
            # 1. Extract current state from metadata
            metadata = context.metadata or {}
            session_id = context.session_id or "unknown"

            # Get narrative response from metadata
            current_output = (
                metadata.get("narrative_response") or
                metadata.get("narrative_text") or
                ""
            )

            if not current_output:
                # No response yet - skip drift detection
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={"drift_detected": False, "skip_reason": "no_response"}
                )

            # Extract physics metrics from metadata or context
            current_metrics = {
                "phi": metadata.get("phi") or getattr(context, 'previous_phi', 0.0),
                "entropy": context.current_entropy or 0.0,
                "valence": metadata.get("valence") or 0.0,
                "arousal": metadata.get("arousal") or 0.5,
            }

            # Extract ethics vector from metadata
            ethics_vector = metadata.get("ethics_vector")
            if ethics_vector and hasattr(ethics_vector, '__dict__'):
                # Convert EthicsVector to dict
                ethics_vector = {
                    "harm_risk": getattr(ethics_vector, 'harm_risk', 0.0),
                    "manipulation_risk": getattr(ethics_vector, 'manipulation_risk', 0.0),
                    "attachment_risk": getattr(ethics_vector, 'attachment_risk', 0.0),
                    "boundary_violation_risk": getattr(ethics_vector, 'boundary_violation_risk', 0.0),
                }

            # 2. Check circuit breaker (pre-gate)
            if self.circuit_breaker:
                circuit_context = {
                    "session_id": session_id,
                    "ethics_vector": ethics_vector,
                    "current_entropy": current_metrics.get("entropy", 0.0),
                    "current_amplitude": context.current_amplitude or 1.0,
                }
                circuit_result = await self.circuit_breaker.check_before_execution(circuit_context)

                if not circuit_result.allowed:
                    logger.warning(f"Circuit breaker blocked execution: {circuit_result.reason}")
                    # Update metadata with circuit state
                    metadata["circuit_blocked"] = True
                    metadata["circuit_state"] = "OPEN"
                    metadata["circuit_reason"] = circuit_result.reason
                    context.metadata = metadata

                    return BlockResult(
                        block_id=self.block_id,
                        status="ok",
                        data={
                            "drift_detected": False,
                            "circuit_blocked": True,
                            "early_exit": True,
                            "early_exit_reason": circuit_result.reason,
                            "human_approval_required": circuit_result.human_approval_required,
                            "safe_mode_required": circuit_result.safe_mode_required,
                        }
                    )

            # 3. Detect drift
            drift_report = await self.drift_detector.detect_drift(
                current_output=current_output,
                current_metrics=cast(Dict[str, float], current_metrics),
                ethics_vector=ethics_vector,
                session_id=session_id,
                agent_id=getattr(context, 'agent_id', None)
            )

            # 4. Check circuit breaker (post-gate)
            if self.circuit_breaker:
                circuit_result = await self.circuit_breaker.check_after_execution(drift_report)

                if not circuit_result.allowed:
                    logger.warning(f"Circuit breaker opened after drift detection: {circuit_result.reason}")
                    # Update metadata
                    metadata["circuit_blocked"] = True
                    metadata["circuit_state"] = "OPEN"
                    metadata["drift_detected"] = True
                    metadata["drift_score"] = drift_report.drift_score
                    context.metadata = metadata

                    return BlockResult(
                        block_id=self.block_id,
                        status="ok",
                        data={
                            "drift_detected": True,
                            "circuit_blocked": True,
                            "early_exit": True,
                            "early_exit_reason": circuit_result.reason,
                            "drift_score": drift_report.drift_score,
                            "drift_types": [dt.value for dt in drift_report.drift_type],
                            "human_approval_required": circuit_result.human_approval_required,
                            "safe_mode_required": circuit_result.safe_mode_required,
                            "drift_report": {
                                "drift_score": drift_report.drift_score,
                                "drift_types": [dt.value for dt in drift_report.drift_type],
                                "degraded_metrics": drift_report.degraded_metrics,
                                "recommendation": drift_report.recommendation,
                            }
                        }
                    )

            # 5. Update context metadata with drift information
            # A report built without a baseline carries drift_score 0.0,
            # recommendation "allow" and semantic_similarity 1.0 — a perfectly
            # clean result produced by the branch whose own comment says
            # "cannot detect drift" (monitoring/behavioral_drift.py:103-115).
            # Its one honest field is `confidence`, which that branch sets to
            # 0.0. Since `response_revision_gate` now reads `drift_score`, a
            # zero-confidence score must not be published as a measurement:
            # the gate would record the criterion as checked and clean on every
            # turn that had nothing to compare against.
            drift_measured = drift_report.confidence > 0.0

            metadata["drift_detection"] = "completed" if drift_measured else "no_baseline"
            metadata["drift_detected"] = drift_report.drift_detected
            if drift_measured:
                metadata["drift_score"] = drift_report.drift_score
            metadata["drift_types"] = [dt.value for dt in drift_report.drift_type]
            metadata["degraded_metrics"] = drift_report.degraded_metrics
            metadata["recommendation"] = drift_report.recommendation
            metadata["semantic_similarity"] = drift_report.semantic_similarity
            metadata["physics_drift"] = drift_report.physics_drift
            metadata["confidence"] = drift_report.confidence

            if drift_report.ethics_escalation:
                metadata["ethics_escalation"] = drift_report.ethics_escalation

            if self.circuit_breaker:
                circuit_stats = self.circuit_breaker.get_stats()
                metadata["circuit_state"] = circuit_stats["state"]
                metadata["circuit_failure_count"] = circuit_stats["failure_count"]

            context.metadata = metadata

            # 6. Apply recommendation (throttle if needed)
            if drift_report.recommendation == "throttle" and drift_report.drift_detected:
                logger.info(f"Drift detected (score={drift_report.drift_score:.2f}), throttling response")
                # Throttle: reduce amplitude
                context.current_amplitude = (context.current_amplitude or 1.0) * 0.7  # 30% reduction

            if drift_measured:
                measurement = (
                    measured_fail(
                        f"drift {drift_report.drift_score:.3f} above the "
                        f"{self.drift_detector.drift_threshold} threshold: "
                        + ", ".join(dt.value for dt in drift_report.drift_type),
                        items_checked=1, drift_score=drift_report.drift_score)
                    if drift_report.drift_detected
                    else measured_pass(1, drift_score=drift_report.drift_score,
                                       confidence=drift_report.confidence))
            else:
                measurement = not_measured(
                    "no behavioural baseline for this session — the detector "
                    "returned a zero-confidence report",
                    cause="input_absent")
            outcome = BlockOutcome(
                block_id=self.block_id,
                legacy_control_status="ok",
                block_run_status=BlockRunStatus.COMPLETED,
                measurement=measurement,
            )
            data = {
                    "drift_detected": drift_report.drift_detected,
                    "drift_types": [dt.value for dt in drift_report.drift_type],
                    "degraded_metrics": drift_report.degraded_metrics,
                    "recommendation": drift_report.recommendation,
                    "block_outcome": outcome.to_record_fields(),
                    "drift_report": {
                        "drift_score": drift_report.drift_score,
                        "drift_types": [dt.value for dt in drift_report.drift_type],
                        "degraded_metrics": drift_report.degraded_metrics,
                        "recommendation": drift_report.recommendation,
                        "semantic_similarity": drift_report.semantic_similarity,
                        "physics_drift": drift_report.physics_drift,
                        "confidence": drift_report.confidence,
                    }
            }
            if drift_measured:
                # Only a score the detector had a baseline for is published
                # under the key `response_revision_gate` reads.
                data["drift_score"] = drift_report.drift_score
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data=data,
            )

        except Exception as e:
            logger.error(f"Error in behavioral drift detection: {e}", exc_info=True)
            # `error` and not a quiet `ok`: this block already failed loudly and
            # that is left alone. What is added is the record — and no
            # `drift_score`, so a crash here cannot read as a clean turn.
            outcome = BlockOutcome(
                block_id=self.block_id,
                legacy_control_status="error",
                block_run_status=BlockRunStatus.FAILED,
                measurement=errored(
                    f"drift detection raised {type(e).__name__}: {e}"),
                recovery_action=RecoveryAction.FALLBACK,
                observation=Observation.RECORDED,
                operating_mode="degraded",
            )
            return BlockResult(
                block_id=self.block_id,
                status="error",
                error=e,
                data={"drift_detected": False, "error_fallback": True,
                      "block_outcome": outcome.to_record_fields()}
            )

