"""
OOD Scorer Port
===============

Port interface for the out-of-distribution / coverage signal that feeds the
``knowledge_boundary_check`` gate (the D-pillar abstention decision).

Why a port: the abstention gate must be able to use a *real* OOD signal
(embedding distance + retrieval coverage) without ``phionyx_core`` importing any
embedding library or framework. The scorer enters through this port; concrete
embedding access happens via the already-sanctioned ``LLMProviderProtocol``
(see ``phionyx_core/meta/ood_scorer.py::EmbeddingOodScorer``).

The consumer (``KnowledgeBoundaryDetector.assess``) is unchanged — all the work
is on the producer side. The signal is deterministic given its inputs; the
embedding-backed scorer pins ``model_id`` + ``corpus_version`` so the score is
replay-stable per Echoism decision-keyed determinism.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class OodSignal:
    """The three inputs the knowledge-boundary detector needs, plus provenance.

    All scores are clamped to ``[0.0, 1.0]``:
      * ``ood_score``       — 0.0 = in-distribution, 1.0 = fully out-of-distribution
      * ``graph_relevance`` — 0.0 = no retrieval/graph coverage, 1.0 = fully covered
      * ``novelty_score``   — 0.0 = familiar, 1.0 = completely novel

    ``source`` records which scorer produced the signal (``heuristic`` /
    ``heuristic_neutral`` / ``embedding`` / ``null``). ``model_id`` and
    ``corpus_version`` are populated only by the embedding-backed path so the
    decision can be replayed against the exact frozen reference set.
    """

    ood_score: float
    graph_relevance: float
    novelty_score: float
    source: str
    model_id: str | None = None
    corpus_version: str | None = None


class OodScorerPort(ABC):
    """Produces an :class:`OodSignal` for a query.

    Implementations MUST be deterministic given their inputs and MUST NOT raise
    into the caller — degrade to a safe in-distribution default rather than
    emitting a spurious ``refuse`` (an OOD scorer that fails closed on its own
    error would over-refuse, the documented failure mode).
    """

    @abstractmethod
    async def score(
        self,
        query_text: str,
        *,
        query_embedding: list[float] | None = None,
        relevance_scores: list[float] | None = None,
    ) -> OodSignal:
        """Return the OOD/coverage signal for ``query_text``.

        Args:
            query_text: the user/query text being assessed.
            query_embedding: a precomputed embedding, if the caller already has one.
            relevance_scores: per-memory retrieval similarities the RAG block
                already computed (``rag_result['relevance_scores']``) — the basis
                for the deterministic retrieval-coverage signal.
        """
        ...
