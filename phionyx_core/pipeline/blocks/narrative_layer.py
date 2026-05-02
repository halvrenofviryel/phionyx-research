"""
Narrative Layer Block
======================

Block: narrative_layer
Generates narrative response using LLM.
"""

import logging
from typing import Any, Protocol

from phionyx_core.templates import TemplateManager, get_template_manager
from phionyx_core.templates.response_templates import IntentType

from ..base import BlockContext, BlockResult, PipelineBlock

logger = logging.getLogger(__name__)


class NarrativeLayerProcessorProtocol(Protocol):
    """Protocol for narrative layer processing."""
    async def process_narrative_layer(
        self,
        frame: Any,
        user_input: str,
        card_type: str,
        card_result: str,
        scene_context: str,
        enhanced_context_string: str,
        system_prompt: str | None = None,
        physics_state: dict[str, Any] | None = None,
        selected_intent: dict[str, Any] | None = None,
        conversation_history: list[dict[str, Any]] | None = None,
    ) -> tuple[Any, str, Any]:  # Returns (frame, narrative_text, narrative_result)
        """Process narrative layer."""
        ...


class NarrativeLayerBlock(PipelineBlock):
    """
    Narrative Layer Block.

    Generates the narrative response using LLM generation.
    """

    determinism = "noisy_sensor"  # LLM text generation; v3.8.0 regenerate retry uses SHA-256 seed but output is still LLM-backed

    CLAIM_REFS = ("SF1:C4", "SF1:C14", "SF1:C15")

    def __init__(self, processor: NarrativeLayerProcessorProtocol | None = None, enable_templates: bool = True):
        """
        Initialize block.

        Args:
            processor: Narrative layer processor
            enable_templates: Enable template-based responses (default: True)
        """
        super().__init__("narrative_layer", claim_refs=self.CLAIM_REFS)
        self.processor = processor
        self.enable_templates = enable_templates
        self.template_manager: TemplateManager | None = (
            get_template_manager() if enable_templates else None
        )

    def should_skip(self, context: BlockContext) -> str | None:
        """Skip if processor not available."""
        if self.processor is None:
            return "processor_not_available"
        return None

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute narrative layer processing.

        Args:
            context: Block context with frame and inputs

        Returns:
            BlockResult with narrative text and result
        """
        try:
            # Get frame from context
            frame = context.metadata.get("frame") if context.metadata else None
            if not frame:
                return BlockResult(
                    block_id=self.block_id,
                    status="error",
                    error=ValueError("Frame not found in context")
                )

            # Get enhanced context and other parameters from metadata
            metadata = context.metadata or {}
            enhanced_context_string = metadata.get("enhanced_context_string", "")

            # --- Memory context injection: append retrieved memories ---
            retrieved_memories = metadata.get("retrieved_memories")
            if retrieved_memories and isinstance(retrieved_memories, (list, tuple)):
                memory_lines = []
                for m in retrieved_memories[:5]:  # Max 5 memories to control token budget
                    if isinstance(m, dict):
                        text = m.get("text", "") or m.get("content", "")
                    elif isinstance(m, str):
                        text = m
                    else:
                        text = str(m) if m else ""
                    if text:
                        memory_lines.append(f"- {text[:200]}")
                if memory_lines:
                    enhanced_context_string += (
                        "\n\nRelevant prior context:\n" + "\n".join(memory_lines)
                    )

            # --- Pipeline Self-State Assessment injection ---
            agi_sections: list[str] = []

            sm = metadata.get("_agi_self_model", {})
            if sm.get("can_do") is not None:
                conf = sm.get("confidence", 0)
                conf_str = f"{conf:.2f}" if isinstance(conf, (int, float)) else str(conf)
                agi_sections.append(
                    f"Self-Model: can_do={sm['can_do']}, confidence={conf_str}, "
                    f"available={sm.get('capabilities_available', 0)}, "
                    f"degraded={sm.get('capabilities_degraded', 0)}, "
                    f"unavailable={sm.get('capabilities_unavailable', 0)}"
                )
                limitations = sm.get("limitations")
                if limitations:
                    agi_sections.append(f"  Limitations: {', '.join(str(lim) for lim in limitations[:5])}")

            kb = metadata.get("_agi_knowledge_boundary", {})
            if kb.get("recommendation") is not None:
                bscore = kb.get("boundary_score", 0)
                bscore_str = f"{bscore:.3f}" if isinstance(bscore, (int, float)) else str(bscore)
                agi_sections.append(
                    f"Knowledge Boundary: within={kb.get('within_boundary')}, "
                    f"score={bscore_str}, "
                    f"recommendation={kb['recommendation']}"
                )

            de = metadata.get("_agi_deliberative_ethics", {})
            if de.get("deliberation_run") is not None:
                if de["deliberation_run"]:
                    agi_sections.append(
                        f"Ethics: verdict={de.get('final_verdict')}, consensus={de.get('consensus')}"
                    )

            if agi_sections:
                enhanced_context_string += "\n\nPipeline Self-State Assessment:\n" + "\n".join(f"- {s}" for s in agi_sections)

            # v3.8.0 + Plan v3: Regeneration constraint injection.
            # When orchestrator invokes this block on a retry pass, it writes
            # regeneration_constraints into metadata. We prepend a deterministic
            # constraint instruction so the LLM regenerates under the new
            # state-informed guardrail. No RNG or clock here — determinism per
            # Axiom 6 and SF1 C14.
            regen = metadata.get("regeneration_constraints")
            if regen and isinstance(regen, dict):
                reasons = regen.get("reasons") or []
                target_phi = regen.get("target_phi_min")
                target_conf = regen.get("target_confidence_min")
                prior_hash = regen.get("prior_narrative_hash", "")
                parts = [
                    "Previous response did not satisfy cognitive-state "
                    "guardrails. Regenerate under the following constraints:",
                    f"- Trigger reasons: {', '.join(str(r) for r in reasons) or 'unspecified'}",
                ]
                if isinstance(target_phi, (int, float)):
                    parts.append(f"- Target phi floor: phi must be ≥ {target_phi}")
                if isinstance(target_conf, (int, float)):
                    parts.append(f"- Target confidence: ≥ {target_conf}")
                if prior_hash:
                    parts.append(f"- Prior rejected narrative hash: {prior_hash}")
                parts.append("- Do not repeat the rejected framing.")
                enhanced_context_string = (
                    "Regeneration constraints:\n"
                    + "\n".join(parts)
                    + "\n\n"
                    + enhanced_context_string
                )

            system_prompt = metadata.get("system_prompt")
            physics_state = metadata.get("physics_state")
            selected_intent = metadata.get("selected_intent")

            # Inject w_final from confidence_fusion into physics_state for LLM control
            w_final = metadata.get("w_final")
            if w_final is not None:
                if physics_state is None:
                    physics_state = {}
                physics_state["w_final"] = w_final

            # Template check (if enabled and intent is available)
            if self.enable_templates and self.template_manager:
                intent_data = metadata.get("intent") or selected_intent
                if intent_data:
                    # Extract intent type and entropy
                    intent_type_str = None
                    if isinstance(intent_data, dict):
                        intent_type_str = intent_data.get("intent_type") or intent_data.get("intent")
                    elif isinstance(intent_data, str):
                        intent_type_str = intent_data

                    if intent_type_str:
                        try:
                            intent_type = IntentType(intent_type_str.lower())
                            entropy = context.current_entropy

                            # Check if template is eligible
                            if self.template_manager.is_eligible(intent_type, entropy):
                                # Get template response
                                template_response = self.template_manager.get_template(
                                    intent=intent_type,
                                    entropy=entropy,
                                    user_input=context.user_input
                                )

                                if template_response:
                                    logger.info(f"Template response used: intent={intent_type}, entropy={entropy:.2f}")
                                    # Return template response (skip LLM)
                                    return BlockResult(
                                        block_id=self.block_id,
                                        status="ok",
                                        data={
                                            "frame": frame,  # Frame unchanged
                                            "narrative_text": template_response,
                                            "narrative_result": {
                                                "source": "template",
                                                "intent": intent_type.value,
                                                "entropy": entropy
                                            }
                                        }
                                    )
                        except (ValueError, KeyError) as e:
                            # Invalid intent type, continue with normal processing
                            logger.debug(f"Template check skipped: {e}")

            # Normal LLM processing (no template match)
            assert self.processor is not None  # narrowed by should_skip()
            updated_frame, narrative_text, narrative_result = await self.processor.process_narrative_layer(
                frame=frame,
                user_input=context.user_input,
                card_type=context.card_type,
                card_result=context.card_result,
                scene_context=context.scene_context,
                enhanced_context_string=enhanced_context_string,
                system_prompt=system_prompt,
                physics_state=physics_state,
                selected_intent=selected_intent,
                conversation_history=metadata.get("conversation_history", []),
            )

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "frame": updated_frame,
                    "narrative_text": narrative_text,
                    "narrative_result": narrative_result
                }
            )
        except Exception as e:
            logger.error(f"Narrative layer processing failed: {e}", exc_info=True)
            return BlockResult(
                block_id=self.block_id,
                status="error",
                error=e
            )

