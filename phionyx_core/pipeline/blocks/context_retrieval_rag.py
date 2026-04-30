"""
Context Retrieval RAG Block
============================

Block: context_retrieval_rag
Retrieves relevant context using RAG (Retrieval Augmented Generation).

This block:
- Retrieves relevant memories from vector store
- Applies intent-based query optimization
- Manages token budget for context injection
- Applies semantic decay (Patent Aile 4)
- Filters by relevance threshold
"""

import logging
from typing import Any

from phionyx_core.services.rag_service import RAGService

from ..base import BlockContext, BlockResult, PipelineBlock

logger = logging.getLogger(__name__)


class ContextRetrievalRagBlock(PipelineBlock):
    """
    Context Retrieval RAG Block.

    Retrieves relevant context using RAG for narrative generation.
    """

    def __init__(
        self,
        rag_service: RAGService | None = None,
        vector_store: Any | None = None,
        max_context_tokens: int = 2000,
        relevance_threshold: float = 0.7
    ):
        """
        Initialize block.

        Args:
            rag_service: Optional RAG service (will be created if not provided)
            vector_store: Optional vector store (for RAG service)
            max_context_tokens: Maximum context tokens to inject
            relevance_threshold: Minimum similarity threshold
        """
        super().__init__("context_retrieval_rag")

        if rag_service is None:
            self.rag_service = RAGService(
                vector_store=vector_store,
                max_context_tokens=max_context_tokens,
                relevance_threshold=relevance_threshold
            )
        else:
            self.rag_service = rag_service

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute context retrieval using RAG.

        Args:
            context: Block context with user_input and intent

        Returns:
            BlockResult with retrieved context
        """
        try:
            user_input = context.user_input or ""

            # Get intent from metadata (from intent_classification block)
            metadata = context.metadata or {}
            intent_data = metadata.get("intent") or metadata.get("selected_intent")
            intent_type = None
            if isinstance(intent_data, dict):
                intent_type = intent_data.get("intent")
            elif isinstance(intent_data, str):
                intent_type = intent_data

            # Get actor_ref for scoping
            actor_ref = None
            if context.participant:
                actor_ref = getattr(context.participant, 'actor_ref', None) or getattr(context.participant, 'id', None)

            # Get semantic time from context metadata (if available) - Patent Aile 4
            t_local = None
            t_global = None
            if context.metadata:
                # Try to get from time_update_sot block result
                time_data = context.metadata.get("time_update_sot") or context.metadata.get("time_delta")
                if time_data:
                    if isinstance(time_data, dict):
                        t_local = time_data.get("t_local") or time_data.get("time_delta")
                        t_global = time_data.get("t_global")
                # Try to get from echo_state if available
                echo_state = context.metadata.get("echo_state")
                if echo_state:
                    t_local = getattr(echo_state, 't_local', None)
                    t_global = getattr(echo_state, 't_global', None)

            # Retrieve context using RAG (with semantic time if available)
            rag_result = await self.rag_service.retrieve_context(
                query=user_input,
                intent=intent_type,
                actor_ref=actor_ref,
                limit=5,
                t_local=t_local,
                t_global=t_global
            )

            # Store context in metadata for downstream blocks
            if context.metadata is None:
                context.metadata = {}

            # Store enhanced context string (for narrative_layer)
            context.metadata["enhanced_context_string"] = rag_result["context_string"]
            context.metadata["rag_result"] = rag_result
            context.metadata["retrieved_memories"] = rag_result["memories"]
            context.metadata["context_token_count"] = rag_result["token_count"]

            logger.debug(
                f"RAG context retrieved: "
                f"memories={len(rag_result['memories'])}, "
                f"tokens={rag_result['token_count']}, "
                f"method={rag_result['method']}"
            )

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "context_string": rag_result["context_string"],
                    "memories": rag_result["memories"],
                    "token_count": rag_result["token_count"],
                    "relevance_scores": rag_result["relevance_scores"],
                    "method": rag_result["method"]
                }
            )
        except Exception as e:
            logger.error(f"Context retrieval RAG failed: {e}", exc_info=True)
            # Fallback: empty context
            fallback_result = {
                "context_string": "",
                "memories": [],
                "token_count": 0,
                "relevance_scores": [],
                "method": "fallback",
                "error": str(e)
            }

            # Store fallback context in metadata
            if context.metadata is None:
                context.metadata = {}
            context.metadata["enhanced_context_string"] = ""
            context.metadata["rag_result"] = fallback_result

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data=fallback_result
            )

