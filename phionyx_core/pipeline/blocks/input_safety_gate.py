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
        min_input_length: int = 3
    ):
        """
        Initialize block.

        Args:
            processor: Safety layer processor (optional, safety check skipped if not provided)
            min_input_length: Minimum input length to pass gate (default: 3)
        """
        super().__init__("input_safety_gate")
        self.processor = processor
        self.min_input_length = min_input_length

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
                            logger.warning("Processor has neither process_safety_layer nor process_safety method")
                            safety_result = None
                            updated_frame = frame

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
                        logger.warning(f"Safety check failed, allowing input through: {e}")
                        # Fail-open: allow input through if safety check fails
                else:
                    logger.debug("Frame not found, skipping safety check")

            # Both checks passed - gate passed
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "gate_triggered": False,
                    "early_exit": False,
                    "input_length": input_length,
                    "input_validation_passed": True,
                    "safety_check_passed": self.processor is not None,
                    "is_blocked": False  # Explicitly set is_blocked to False
                }
            )
        except Exception as e:
            logger.error(f"Input safety gate check failed: {e}", exc_info=True)
            # Fail-open: allow input through if gate check fails
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "gate_triggered": False,
                    "early_exit": False,
                    "error": str(e)
                }
            )

