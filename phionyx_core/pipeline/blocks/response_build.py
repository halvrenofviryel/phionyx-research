"""
Response Build Block
=====================

Block: response_build
Builds final response payload (always-on block).
"""

import logging
from typing import Dict, Any, Optional, Protocol

from ..base import PipelineBlock, BlockContext, BlockResult

logger = logging.getLogger(__name__)


class ResponseBuilderProtocol(Protocol):
    """Protocol for response building."""
    def build_response(
        self,
        frame: Any,
        narrative_response: str,
        physics_state: Dict[str, Any],
        emotional_state: Optional[Dict[str, Any]] = None,
        memory_result: Optional[Any] = None,
        growth_metrics: Optional[Dict[str, Any]] = None,
        confidence_result: Optional[Any] = None,
        cep_metrics: Optional[Dict[str, Any]] = None,
        cep_flags: Optional[Dict[str, Any]] = None,
        entropy_modulated_amplitude: Optional[float] = None,
        behavior_modulation: Optional[Dict[str, Any]] = None,
        current_unified_state: Optional[Any] = None,
        esc_available: bool = False,
        mode: Optional[str] = None,
        strategy: Optional[str] = None,
        prompt_context: Optional[str] = None
    ) -> Dict[str, Any]:  # Returns response payload
        """Build response payload."""
        ...


class ResponseBuildBlock(PipelineBlock):
    """
    Response Build Block.

    Builds final response payload (always-on block).
    This block MUST ALWAYS run, even on early exit.
    """

    determinism = "noisy_sensor"  # assembles LLM-generated narrative into final payload

    CLAIM_REFS = ("SF1:C4", "SF1:C15", "SF2:C1", "SF2:C11")

    def __init__(self, builder: ResponseBuilderProtocol):
        """
        Initialize block.

        Args:
            builder: Response builder service
        """
        super().__init__("response_build", claim_refs=self.CLAIM_REFS)
        self.builder = builder

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute response building.

        Args:
            context: Block context with frame and state

        Returns:
            BlockResult with response payload
        """
        try:
            # Get frame and state from metadata
            metadata = context.metadata or {}
            frame = metadata.get("frame")
            narrative_response = metadata.get("narrative_text", "")
            physics_state = metadata.get("physics_state", {})

            # CRITICAL: Ensure physics_state is a dictionary, not a Mock object
            if not isinstance(physics_state, dict):
                logger.warning(f"physics_state is not a dictionary (type: {type(physics_state)}), creating new dictionary")
                physics_state = {}

            # Coherence enforcement: prefer redacted text when state leak was detected
            coherence_result = metadata.get("coherence_qa_result")
            if coherence_result and isinstance(coherence_result, dict):
                if coherence_result.get("leak_detected") and coherence_result.get("redacted_text"):
                    narrative_response = coherence_result["redacted_text"]
                    logger.info("response_build: using redacted narrative (coherence leak detected)")

            # Trust evaluation: inject disclaimer when context is untrusted
            trust_result = metadata.get("trust_result", {})
            if trust_result and isinstance(trust_result, dict):
                is_trusted = trust_result.get("is_trusted", True)
                if not is_trusted:
                    narrative_response = (
                        "[Note: Response generated in reduced-trust context] "
                        + narrative_response
                    )

            # Arbitration conflict resolution: safety override note
            arb_result = metadata.get("arbitration_result", {})
            if arb_result and isinstance(arb_result, dict) and arb_result.get("arbitration_needed"):
                strategy = arb_result.get("resolution_strategy", "none")
                if strategy == "safety_override":
                    narrative_response = (
                        narrative_response.rstrip(".")
                        + " (Please note: this response was generated with "
                        "additional safety considerations.)"
                    )

            # v3.8.0: state-driven revision directive consumption.
            # Directive emitted by response_revision_gate, which runs
            # immediately before response_build in v3.8.0 canonical order.
            # Claims: SF1 C1/C4/C15, SF2 C1/C11.
            revision_directive = metadata.get("revision_directive")
            revision_action_taken = "none"
            if revision_directive and isinstance(revision_directive, dict):
                directive = revision_directive.get("directive", "pass")
                if directive == "reject":
                    narrative_response = (
                        "I can't safely respond to this request. "
                        "A human reviewer has been notified."
                    )
                    revision_action_taken = "rejected"
                    logger.info(
                        "response_build: state-driven REJECT applied (reasons=%s)",
                        revision_directive.get("reasons"),
                    )
                elif directive == "regenerate":
                    # Orchestrator-level narrative re-entry is a bounded
                    # follow-up refactor. For now, fall back to a deterministic
                    # in-place clarification response so the user receives a
                    # safe reply instead of a low-phi / low-confidence answer.
                    narrative_response = (
                        "I need a bit more context to answer confidently. "
                        "Could you rephrase or add detail?"
                    )
                    revision_action_taken = "clarification_fallback"
                    logger.info(
                        "response_build: state-driven REGENERATE → clarification fallback (reasons=%s)",
                        revision_directive.get("reasons"),
                    )
                elif directive == "rewrite":
                    if not narrative_response.lstrip().startswith("["):
                        narrative_response = (
                            "[Revised under cognitive-state governance] "
                            + narrative_response
                        )
                        revision_action_taken = "rewrite_prefix"
                elif directive == "damp":
                    damp_factor = revision_directive.get("damp_factor")
                    if isinstance(damp_factor, (int, float)) and 0.0 < damp_factor < 1.0:
                        current_amp = physics_state.get(
                            "amplitude", context.current_amplitude
                        )
                        try:
                            physics_state["amplitude"] = float(current_amp) * float(damp_factor)
                        except (TypeError, ValueError):
                            pass
                        physics_state["amplitude_damped_by"] = float(damp_factor)
                        revision_action_taken = "amplitude_damped"

            # Check for early exit
            early_exit = metadata.get("early_exit_triggered", False)
            if early_exit:
                # Use clarifying question as narrative response
                narrative_response = metadata.get("clarifying_question", "How can I help you today?")

            # Fallback values if missing
            if not narrative_response:
                narrative_response = "I'm processing your request. Please wait a moment."

            # Ensure phi is in physics_state
            if 'phi' not in physics_state:
                unified_state = metadata.get("unified_state")
                if unified_state and hasattr(unified_state, 'phi'):
                    physics_state['phi'] = unified_state.phi
                    physics_state['phi_source'] = 'unified_state'
                else:
                    physics_state['phi'] = 0.5  # Safe default
                    physics_state['phi_source'] = 'fallback'

            # Build response
            response = self.builder.build_response(
                frame=frame,
                narrative_response=narrative_response,
                physics_state=physics_state,
                emotional_state=metadata.get("emotional_state"),
                memory_result=metadata.get("memory_result"),
                growth_metrics=metadata.get("growth_metrics"),
                confidence_result=metadata.get("confidence_result"),
                cep_metrics=metadata.get("cep_metrics"),
                cep_flags=metadata.get("cep_flags"),
                entropy_modulated_amplitude=metadata.get("entropy_modulated_amplitude"),
                behavior_modulation=metadata.get("behavior_modulation"),
                current_unified_state=metadata.get("unified_state"),
                esc_available=metadata.get("esc_available", False),
                mode=metadata.get("mode"),
                strategy=metadata.get("strategy"),
                prompt_context=metadata.get("enhanced_context_string")
            )

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "response": response,
                    "early_exit": early_exit,
                    "revision_action_taken": revision_action_taken,
                }
            )
        except Exception as e:
            logger.error(f"Response building failed: {e}", exc_info=True)
            # Fail-open: return minimal response
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "response": {
                        "narrative": "I'm processing your request. Please wait a moment.",
                        "physics": {"phi": 0.5, "entropy": 0.5},
                        "error": str(e)
                    },
                    "error": str(e)
                }
            )

