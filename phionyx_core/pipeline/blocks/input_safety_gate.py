"""
Input Safety Gate Block
=======================

Block: input_safety_gate
Combined block that performs both input validation and safety checks for early exit.

This block merges:
- low_input_gate: Input length/quality validation
- safety_layer_pre_cep: Safety assessment

Both blocks serve the same purpose: early rejection of problematic inputs.
"""

import logging
from typing import Any, Optional, Protocol

from ..base import PipelineBlock, BlockContext, BlockResult

logger = logging.getLogger(__name__)


class SafetyLayerProcessorProtocol(Protocol):
    """Protocol for safety layer processing."""
    async def process_safety(
        self,
        frame: Any,
        user_input: str,
        narrative_response: str,
        cognitive_state: Any,
        context_string: str,
        cep_flags: Optional[Any] = None,
        cep_config: Optional[Any] = None
    ) -> tuple[Any, Any]:  # Returns (frame, safety_result)
        """Process safety layer."""
        ...


class InputSafetyGateBlock(PipelineBlock):
    """
    Input Safety Gate Block.

    Combined block that performs:
    1. Input validation (length/quality check) - from low_input_gate
    2. Safety assessment (safety check) - from safety_layer_pre_cep

    Both checks are performed for early exit/rejection of problematic inputs.
    """

    def __init__(
        self,
        processor: Optional[SafetyLayerProcessorProtocol] = None,
        min_input_length: int = 3,
        fail_closed: bool = False,
    ):
        """
        Initialize block.

        Args:
            processor: Safety layer processor (optional, safety check skipped if not provided)
            min_input_length: Minimum input length to pass gate (default: 3)
            fail_closed: When True, a missing/crashing safety processor BLOCKS the
                turn (early exit) instead of passing it through unverified. High-risk
                deployment profiles (Safety Gate Profile) MUST set this True. When
                False (default, backward-compatible), an unavailable scorer passes the
                input through — but the event is ALWAYS recorded as an auditable
                ``gate_unavailable`` signal so a fail-open is never silent.
                Founder-directed credibility-floor fix (value study §9 P0, 2026-06-07).
        """
        super().__init__("input_safety_gate")
        self.processor = processor
        self.min_input_length = min_input_length
        self.fail_closed = fail_closed

    def _unavailable(self, reason: str, *, input_length: int = 0) -> BlockResult:
        """Emit an auditable 'safety scorer unavailable' result.

        fail_closed=True  → block the turn (early_exit), enforced decision.
        fail_closed=False → pass through UNVERIFIED, but flag it so the audit
        chain records that the gate could not actually verify this input.
        """
        data = {
            "gate_triggered": self.fail_closed,
            "gate_type": "safety_unavailable",
            "early_exit": self.fail_closed,
            "gate_unavailable": True,
            "enforced": self.fail_closed,
            "decision": "blocked" if self.fail_closed else "passed_unverified",
            "is_blocked": self.fail_closed,
            "safety_check_passed": False,
            "input_validation_passed": True,
            "input_length": input_length,
            "reason": reason,
        }
        if self.fail_closed:
            data["clarifying_question"] = (
                "I can't process this safely right now because the safety check is "
                "unavailable. Please try again shortly."
            )
            logger.error(
                f"[INPUT_SAFETY_GATE] safety scorer unavailable ({reason}); "
                f"BLOCKED (fail-closed)"
            )
        else:
            logger.warning(
                f"[INPUT_SAFETY_GATE] safety scorer unavailable ({reason}); "
                f"passed UNVERIFIED (fail-open) — recorded as gate_unavailable"
            )
        return BlockResult(block_id=self.block_id, status="ok", data=data)

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute input safety gate check.

        Performs both input validation and safety check.
        If either fails, triggers early exit.

        Args:
            context: Block context with user_input and frame

        Returns:
            BlockResult with gate status and optional early exit
        """
        try:
            user_input = context.user_input or ""
            input_length = len(user_input.strip())

            # Step 1: Input validation (from low_input_gate)
            if input_length < self.min_input_length:
                clarifying_question = "Could you tell me more about what you're thinking or feeling?"

                logger.debug(
                    f"[INPUT_SAFETY_GATE] Input too short: length={input_length}, "
                    f"min={self.min_input_length}, triggering early exit"
                )

                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={
                        "gate_triggered": True,
                        "gate_type": "input_validation",
                        "early_exit": True,
                        "clarifying_question": clarifying_question,
                        "input_length": input_length,
                        "min_length": self.min_input_length
                    }
                )

            # Step 2: Safety check (from safety_layer_pre_cep)
            if self.processor:
                metadata = context.metadata or {}
                frame = metadata.get("frame")
                cognitive_state = metadata.get("cognitive_state")
                context_string = metadata.get("context_string", "")

                if frame:
                    try:
                        # Process safety layer
                        # Check if processor has process_safety_layer (async) or process_safety (async)
                        if hasattr(self.processor, 'process_safety_layer'):
                            # Use process_safety_layer if available (async method)
                            safety_result_tuple = await self.processor.process_safety_layer(
                                frame=frame,
                                user_input=user_input,
                                narrative_response="",  # Not available yet before narrative layer
                                cognitive_state=cognitive_state or getattr(frame, 'cognitive_state', None),
                                context_string=context_string or getattr(frame, 'context_string', ""),
                                cep_flags=None,
                                cep_config=None
                            )
                            updated_frame, safety_result = safety_result_tuple
                        elif hasattr(self.processor, 'process_safety'):
                            # Fallback to process_safety (async method)
                            updated_frame, safety_result = await self.processor.process_safety(
                                frame=frame,
                                user_input=user_input,
                                narrative_response="",  # Not available yet before narrative layer
                                cognitive_state=cognitive_state or getattr(frame, 'cognitive_state', None),
                                context_string=context_string or getattr(frame, 'context_string', ""),
                                cep_flags=None,
                                cep_config=None
                            )
                        else:
                            return self._unavailable(
                                "processor_no_method", input_length=input_length
                            )

                        # Check if blocked by safety
                        is_blocked = getattr(safety_result, 'is_blocked', False) if safety_result else False

                        if is_blocked:
                            logger.debug(
                                f"[INPUT_SAFETY_GATE] Input blocked by safety check: "
                                f"user_input={user_input[:50]}..."
                            )

                            return BlockResult(
                                block_id=self.block_id,
                                status="ok",
                                data={
                                    "gate_triggered": True,
                                    "gate_type": "safety_check",
                                    "early_exit": True,
                                    "is_blocked": True,
                                    "safety_result": safety_result,
                                    "frame": updated_frame
                                }
                            )

                        # Safety check passed, update frame in metadata
                        if context.metadata is None:
                            context.metadata = {}
                        context.metadata["frame"] = updated_frame
                        context.metadata["safety_result"] = safety_result

                        # CRITICAL: Also include safety_result in block data for test compatibility
                        # This allows tests to check harm_risk even when input is not blocked
                        return BlockResult(
                            block_id=self.block_id,
                            status="ok",
                            data={
                                "gate_triggered": False,
                                "early_exit": False,
                                "input_length": input_length,
                                "input_validation_passed": True,
                                "safety_check_passed": True,
                                "safety_result": safety_result,  # Include safety_result for test compatibility
                                "is_blocked": False  # Explicitly set is_blocked to False
                            }
                        )
                    except Exception as e:
                        # Was fail-open; now an auditable gate_unavailable event
                        # (blocks under fail_closed).
                        return self._unavailable(
                            f"safety_check_exception:{type(e).__name__}",
                            input_length=input_length,
                        )
                else:
                    return self._unavailable("no_frame", input_length=input_length)
            else:
                # No safety processor wired at all — the gate cannot verify the input.
                return self._unavailable(
                    "no_safety_processor", input_length=input_length
                )

            # Defensive fallback (all branches above return); treat as unverified.
            return self._unavailable("unreached_fallthrough", input_length=input_length)
        except Exception as e:
            logger.error(f"Input safety gate check failed: {e}", exc_info=True)
            # Was fail-open; now an auditable gate_unavailable event (blocks under fail_closed).
            return self._unavailable(
                f"gate_exception:{type(e).__name__}", input_length=len(context.user_input or "")
            )

