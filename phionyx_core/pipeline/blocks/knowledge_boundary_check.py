"""
Knowledge Boundary Check Block
===============================

Block: knowledge_boundary_check
Detects out-of-distribution queries and determines appropriate response strategy
(proceed / hedge / admit_ignorance / refuse) — the D-pillar "calibrated abstention"
decision.

Position in pipeline: After self_model_assessment, before narrative_layer.

Two behaviours layered on the historical detector — both additive, but with
DIFFERENT default postures (be precise about this):

1. REAL OOD SIGNAL (producer) — ON BY DEFAULT, advisory only. Historically
   ``ood_score`` was never populated, so the detector always saw the all-safe
   defaults (ood=0, relevance=1) → always "proceed" → false-negative-rate 1.00.
   This block now (a) reads the RAG block's ``relevance_scores`` (plural — the
   historical code read the never-emitted singular ``relevance_score``), and
   (b) calls an injected ``OodScorerPort`` to produce a real ood/coverage/novelty
   signal. This is the FNR-1.00 fix and it is intentionally on by default, so the
   ``recommendation`` becomes meaningful. It is **advisory** unless (2) is enabled:
   no control flow changes, but a RAG-active deployment's recommendation (consumed
   by narrative_layer as prompt text) does become real rather than always-"proceed".
   When no ``relevance_scores`` are present the signal is neutral (== legacy).

2. ENFORCEMENT (fail-closed, OPT-IN, default-OFF). Historically the recommendation was advisory
   only (logged, never gated). When ``fail_closed`` is set (the abstention_boundary
   profile / ``PHIONYX_ABSTAIN_FAIL_CLOSED=1``) an ``admit_ignorance``/``refuse``
   recommendation now short-circuits the turn via ``data['early_exit']`` — the same
   data-flag convention every other gate uses (kill_switch, ethics). An always-on
   auditable marker is emitted even when enforcement is OFF (never a silent
   fail-open). The gate's own enforcement logic fails OPEN (never breaks the turn).
"""

import logging

from ...ports.ood_scorer_port import OodScorerPort
from ..base import BlockContext, BlockResult, PipelineBlock

logger = logging.getLogger(__name__)


class KnowledgeBoundaryCheckBlock(PipelineBlock):
    """
    Knowledge Boundary Check Block (S2 Self-Awareness Sprint).

    Evaluates OOD score, graph relevance, and novelty to determine
    if the system should proceed, hedge, admit ignorance, or refuse.
    """

    def __init__(
        self,
        knowledge_boundary=None,
        ood_scorer: OodScorerPort | None = None,
        fail_closed: bool = False,
    ):
        """
        Args:
            knowledge_boundary: KnowledgeBoundaryDetector instance (injected via DI)
            ood_scorer: OodScorerPort producing a real OOD/coverage signal (DI).
                When None, the block derives coverage inline from RAG relevance
                scores if present, else keeps the historical safe defaults.
            fail_closed: when True, an ``admit_ignorance``/``refuse`` recommendation
                ENFORCES (sets ``early_exit``) instead of staying advisory. Default
                False = backward-compatible advisory behaviour.
        """
        super().__init__("knowledge_boundary_check")
        self._knowledge_boundary = knowledge_boundary
        self._ood_scorer = ood_scorer
        self.fail_closed = fail_closed

    async def execute(self, context: BlockContext) -> BlockResult:
        try:
            metadata = context.metadata or {}

            # Extract OOD indicators from prior blocks (historical defaults)
            ood_score = metadata.get("ood_score", 0.0)
            graph_relevance = metadata.get("graph_relevance", 1.0)
            novelty_score = metadata.get("novelty_score", 0.0)
            ood_source: str | None = None
            model_id: str | None = None
            corpus_version: str | None = None

            # Retrieval coverage from the RAG block. FIX: the RAG service emits
            # 'relevance_scores' (plural list, rag_service.py); the historical code
            # read the never-emitted singular 'relevance_score', so coverage was
            # always the default. Read the plural list here.
            rag_result = metadata.get("rag_result", {})
            relevance_scores = None
            if isinstance(rag_result, dict):
                rs = rag_result.get("relevance_scores")
                if isinstance(rs, list) and rs:
                    relevance_scores = rs
                # Legacy singular keys preserved for any caller that set them.
                if "relevance_score" in rag_result:
                    graph_relevance = rag_result["relevance_score"]
                if "novelty" in rag_result:
                    novelty_score = rag_result["novelty"]

            # Produce a REAL OOD signal when a scorer is injected.
            if self._ood_scorer is not None:
                try:
                    signal = await self._ood_scorer.score(
                        getattr(context, "user_input", "") or "",
                        relevance_scores=relevance_scores,
                    )
                    ood_score = signal.ood_score
                    graph_relevance = signal.graph_relevance
                    novelty_score = signal.novelty_score
                    ood_source = signal.source
                    model_id = signal.model_id
                    corpus_version = signal.corpus_version
                except Exception as scorer_exc:  # noqa: BLE001 — scorer must never break the gate
                    logger.debug("ood_scorer failed, using metadata defaults: %s", scorer_exc)
            elif relevance_scores is not None:
                # No scorer wired but retrieval scores exist → derive coverage
                # inline (deterministic; turns the dead 0.0 default into a real
                # retrieval-coverage signal).
                coverage = max(0.0, min(1.0, max(relevance_scores)))
                ood_score = 1.0 - coverage
                graph_relevance = coverage
                if novelty_score == 0.0:
                    novelty_score = 1.0 - coverage
                ood_source = "inline_retrieval_coverage"

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

            # OOD provenance (for replaying an embedding-backed decision).
            result_data["ood_source"] = ood_source
            if model_id:
                result_data["model_id"] = model_id
            if corpus_version:
                result_data["corpus_version"] = corpus_version

            final_recommendation = result_data.get("recommendation")

            # --- Abstention enforcement (default-OFF; data-flag convention) ---
            self._apply_abstention(result_data, final_recommendation)

            if final_recommendation in ("admit_ignorance", "refuse"):
                logger.warning(
                    f"[KNOWLEDGE_BOUNDARY] Recommendation: {final_recommendation} "
                    f"(score={result_data['boundary_score']:.3f}, "
                    f"enforced={result_data.get('enforced', False)})"
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

    def _apply_abstention(self, result_data: dict, recommendation) -> None:
        """Turn the advisory recommendation into an enforced/recorded verdict.

        Mirrors the established fail-closed idiom (input_safety_gate / ethics gate):
        block via the ``data`` flag (``early_exit``), never via status='error'; emit
        an always-on auditable marker even when enforcement is OFF (never a silent
        fail-open); the gate's own logic fails OPEN — it must never break the turn.

        - ``refuse``           → hard abstain (early_exit when fail_closed)
        - ``admit_ignorance``  → abstain + defer_to_human when fail_closed
        - ``hedge``/``proceed``→ advisory only (never gates)
        """
        try:
            is_abstain = recommendation in ("admit_ignorance", "refuse")
            enforced = bool(self.fail_closed and is_abstain)

            # Always-on auditable markers (never silent), regardless of mode.
            result_data["abstention_signal"] = is_abstain
            result_data["enforced"] = enforced

            if enforced:
                result_data["early_exit"] = True
                result_data["defer_to_human"] = recommendation == "admit_ignorance"
                result_data["decision"] = "abstained"
                result_data["abstain_action"] = recommendation
            elif is_abstain:
                # Recommendation says abstain but enforcement is off — record the
                # advisory event so the fail-open is visible, but do not gate.
                result_data["decision"] = "abstained_advisory"
            else:
                result_data["decision"] = "answered"
        except Exception as enf_exc:  # noqa: BLE001 — enforcement must never break the gate
            logger.debug("abstention enforcement soft-failed: %s", enf_exc)
            result_data.setdefault("decision", "answered")
            result_data.setdefault("enforced", False)

    def get_dependencies(self) -> list:
        return ["self_model_assessment"]
