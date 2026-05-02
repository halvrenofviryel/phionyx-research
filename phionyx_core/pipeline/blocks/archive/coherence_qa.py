"""
Coherence QA Block
===================

Block: coherence_qa
Quality assurance check for coherence — detects state leak patterns,
computes coherence scores, and applies redaction when internal state
information would be inappropriately exposed in responses.
"""

import logging
import re
from typing import Any, Protocol

from ...base import BlockContext, BlockResult, PipelineBlock

logger = logging.getLogger(__name__)

# State leak patterns (inline from CoherenceProcessor for zero-dependency operation)
_STATE_LEAK_PATTERNS = [
    r'\bphi\s*(?:is|[=:])\s*[\d.]+',
    r'\bentropy\s*(?:is|[=:])\s*[\d.]+',
    r'\bvalence\s*(?:is|[=:])\s*[\d.]+',
    r'\barousal\s*(?:is|[=:])\s*[\d.]+',
    r'\btrust\s*(?:is|[=:])\s*[\d.]+',
    r'\bcoherence\s*(?:is|[=:])\s*[\d.]+',
    r'\bdrive\s*(?:is|[=:])\s*[\d.]+',
    r'Current State:.*',
    r'State:.*phi',
    r'Metrics:.*',
    r'Internal:.*',
    r'Debug:.*',
    r'\[PHI\].*',
    r'\[ENTROPY\].*',
    r'\[VALENCE\].*',
    r'\bmy current phi\b',
    r'\bmy phi is\b',
    r'\bmy entropy is\b',
]
_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in _STATE_LEAK_PATTERNS]


class CoherenceQAProtocol(Protocol):
    """Protocol for coherence QA."""
    def check_coherence(
        self,
        unified_state: Any,
        narrative_response: str
    ) -> dict[str, Any]:
        """Check coherence quality."""
        ...


class CoherenceQaBlock(PipelineBlock):
    """
    Coherence QA Block.

    Performs quality assurance on narrative coherence by detecting state leak
    patterns, computing coherence scores, and applying redaction when internal
    state information would be inappropriately exposed in responses.

    When no external qa_checker is injected, the block runs its own inline
    leak detection and scoring logic (fail-open design).
    """

    def __init__(self, qa_checker: CoherenceQAProtocol | None = None):
        super().__init__("coherence_qa")
        self.qa_checker = qa_checker

    async def execute(self, context: BlockContext) -> BlockResult:
        try:
            metadata = context.metadata or {}
            narrative_text = metadata.get("narrative_text", "")

            # Delegate to injected checker if available
            if self.qa_checker:
                unified_state = metadata.get("unified_state")
                qa_result = self.qa_checker.check_coherence(
                    unified_state=unified_state,
                    narrative_response=narrative_text,
                )
                context.metadata["coherence_qa_result"] = qa_result
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={"qa_result": qa_result},
                )

            # --- Inline coherence QA logic ---
            violations: list[str] = []
            leak_detected = False

            for pattern in _COMPILED_PATTERNS:
                match = pattern.search(narrative_text)
                if match:
                    violations.append(match.group())
                    leak_detected = True

            # Coherence score: 1.0 minus penalties
            score = 1.0 - (len(violations) * 0.1) - (0.3 if leak_detected else 0.0)
            score = max(0.0, min(1.0, score))

            # Redaction: remove leak patterns from text
            redacted_text: str | None = None
            if leak_detected:
                cleaned = narrative_text
                for pattern in _COMPILED_PATTERNS:
                    cleaned = pattern.sub("", cleaned)
                redacted_text = re.sub(r"\s+", " ", cleaned).strip()

            qa_result = {
                "coherence_score": score,
                "leak_detected": leak_detected,
                "violations": violations,
                "violation_count": len(violations),
                "redacted_text": redacted_text,
            }

            # Enrich metadata for downstream blocks
            context.metadata["coherence_qa_result"] = qa_result

            # State snapshot reference on violation (SF1 Claim 15/17)
            if leak_detected:
                context.metadata["_state_snapshot_coherence_violation"] = {
                    "violation_count": len(violations),
                    "coherence_score": score,
                    "pre_physics_snapshot": context.metadata.get("_state_snapshot_pre_physics"),
                }

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={"qa_result": qa_result},
            )
        except Exception as e:
            logger.error(f"Coherence QA check failed: {e}", exc_info=True)
            # Fail-open: continue pipeline
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={"qa_result": None, "error": str(e)},
            )

