"""
Knowledge Boundary Check Block
===============================

Block: knowledge_boundary_check
Detects out-of-distribution queries and determines appropriate response strategy.

Position in pipeline: After self_model_assessment, before narrative_layer.
"""

import logging

from ..base import PipelineBlock, BlockContext, BlockResult

logger = logging.getLogger(__name__)


class KnowledgeBoundaryCheckBlock(PipelineBlock):
    """
    Knowledge Boundary Check Block (S2 Self-Awareness Sprint).

    Evaluates OOD score, graph relevance, and novelty to determine
    if the system should proceed, hedge, admit ignorance, or refuse.
    """

    def __init__(self, knowledge_boundary=None):
        """
        Args:
            knowledge_boundary: KnowledgeBoundaryDetector instance (injected via DI)
        """
        super().__init__("knowledge_boundary_check")
        self._knowledge_boundary = knowledge_boundary

    async def execute(self, context: BlockContext) -> BlockResult:
        try:
            metadata = context.metadata or {}

            # Extract OOD indicators from prior blocks
            ood_score = metadata.get("ood_score", 0.0)
            graph_relevance = metadata.get("graph_relevance", 1.0)
            novelty_score = metadata.get("novelty_score", 0.0)

            # Try to extract from RAG/context retrieval results
            rag_result = metadata.get("rag_result", {})
            if isinstance(rag_result, dict):
                if "relevance_score" in rag_result:
                    graph_relevance = rag_result["relevance_score"]
                if "novelty" in rag_result:
                    novelty_score = rag_result["novelty"]

            if self._knowledge_boundary is not None:
                # Full KnowledgeBoundaryDetector assessment
                assessment = self._knowledge_boundary.assess(
                    ood_score=ood_score,
                    graph_relevance=graph_relevance,
                    novelty_score=novelty_score,
                )
                result_data = {
                    "within_boundary": assessment.within_boundary,
                    "boundary_score": assessment.boundary_score,
                    "ood_component": assessment.ood_component,
                    "relevance_component": assessment.relevance_component,
                    "novelty_component": assessment.novelty_component,
                    "recommendation": assessment.recommendation,
                    "reasoning": assessment.reasoning,
                }
            else:
                # Inline fallback: heuristic boundary check using entropy + RAG relevance
                entropy = context.current_entropy if context.current_entropy is not None else 0.5
                # boundary_score: high = within boundary, low = outside
                boundary_score = (1.0 - ood_score) * 0.4 + graph_relevance * 0.4 + (1.0 - entropy) * 0.2
                boundary_score = max(0.0, min(1.0, boundary_score))

                within = boundary_score >= 0.5
                if boundary_score >= 0.7:
                    recommendation = "proceed"
                elif boundary_score >= 0.5:
                    recommendation = "hedge"
                elif boundary_score >= 0.3:
                    recommendation = "admit_ignorance"
                else:
                    recommendation = "refuse"

                result_data = {
                    "within_boundary": within,
                    "boundary_score": boundary_score,
                    "ood_component": ood_score,
                    "relevance_component": graph_relevance,
                    "novelty_component": novelty_score,
                    "recommendation": recommendation,
                    "reasoning": f"Inline heuristic: score={boundary_score:.3f} (entropy={entropy:.2f})",
                }

            if result_data.get("recommendation") in ("admit_ignorance", "refuse"):
                logger.warning(
                    f"[KNOWLEDGE_BOUNDARY] Recommendation: {result_data['recommendation']} "
                    f"(score={result_data['boundary_score']:.3f})"
                )

            # Store with prefixed key for downstream AGI context injection
            if context.metadata is not None:
                context.metadata["_agi_knowledge_boundary"] = result_data

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data=result_data,
            )

        except Exception as e:
            logger.error(f"Knowledge boundary check error: {e}", exc_info=True)
            return BlockResult(
                block_id=self.block_id,
                status="error",
                data={"error": str(e)}
            )

    def get_dependencies(self) -> list:
        return ["self_model_assessment"]
