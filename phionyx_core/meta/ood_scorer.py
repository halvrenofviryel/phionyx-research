"""
OOD Scorers — producers for the knowledge-boundary abstention signal
====================================================================

Two concrete :class:`~phionyx_core.ports.ood_scorer_port.OodScorerPort`
implementations:

* :class:`HeuristicOodScorer` — the DEFAULT. Derives the OOD/coverage signal
  from the retrieval relevance scores the RAG block already computes
  (``rag_result['relevance_scores']``). Pure stdlib, deterministic, no network.
  When no retrieval signal is present it returns the neutral in-distribution
  default — it does NOT fabricate OOD.

* :class:`EmbeddingOodScorer` — OPTIONAL. Cosine distance from a *frozen,
  versioned* reference corpus, using the existing
  :func:`phionyx_core.meta.uncertainty.compute_ood_score` cosine math.
  Embeddings enter only through the injected ``LLMProviderProtocol`` (no
  embedding library is imported into core). Replay-deterministic: it pins
  ``model_id`` + ``corpus_version`` into the signal. Degrades to the heuristic
  whenever the provider, corpus, or embedding is unavailable or zero — so it
  never emits a spurious ``refuse``.

Core-boundary: stdlib + pydantic-free; the only external touch-point is the
``LLMProviderProtocol`` Protocol, imported under ``TYPE_CHECKING`` exactly as
``memory/vector_store.py`` does it.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ..ports.ood_scorer_port import OodScorerPort, OodSignal
from .uncertainty import compute_ood_score

if TYPE_CHECKING:  # pragma: no cover - typing only, no runtime import
    from ..contracts.llm_provider import LLMProviderProtocol

logger = logging.getLogger(__name__)


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def _coverage_from_relevance(relevance_scores: list[float] | None) -> float | None:
    """Retrieval coverage = the best retrieval similarity, clamped. None if absent."""
    if not relevance_scores:
        return None
    try:
        return _clamp(max(relevance_scores))
    except (TypeError, ValueError):
        return None


def _is_zero_vector(vec: list[float] | None) -> bool:
    """A provider returns a zero vector when the embedding service is unavailable;
    cosine against zeros would spuriously read as fully-OOD, so treat as 'no signal'."""
    return not vec or all(x == 0.0 for x in vec)


class HeuristicOodScorer(OodScorerPort):
    """Default OOD scorer: retrieval-coverage, deterministic, stdlib-only."""

    async def score(
        self,
        query_text: str,
        *,
        query_embedding: list[float] | None = None,
        relevance_scores: list[float] | None = None,
    ) -> OodSignal:
        coverage = _coverage_from_relevance(relevance_scores)
        if coverage is None:
            # No retrieval signal — stay neutral (in-distribution). Do NOT
            # fabricate OOD; that would over-refuse with no basis.
            return OodSignal(
                ood_score=0.0,
                graph_relevance=1.0,
                novelty_score=0.0,
                source="heuristic_neutral",
            )
        ood = _clamp(1.0 - coverage)
        return OodSignal(
            ood_score=ood,
            graph_relevance=coverage,
            novelty_score=ood,
            source="heuristic",
        )


@dataclass(frozen=True)
class ReferenceCorpus:
    """A frozen, versioned set of reference embeddings for the embedding-OOD path.

    Pinning ``model_id`` + ``corpus_version`` is what makes the embedding score
    replay-deterministic (same query + same pinned corpus + same model →
    same OOD score), independent of any live, mutating vector store.
    """

    model_id: str
    corpus_version: str
    vectors: list[list[float]] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.vectors


def load_reference_corpus(path: str) -> ReferenceCorpus | None:
    """Load a frozen reference corpus JSON ``{model_id, corpus_version, vectors}``.

    Returns ``None`` (→ heuristic fallback) when the file is missing or malformed.
    Build one offline with ``scripts/active/build_ood_reference_corpus.py``.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        logger.debug("load_reference_corpus: %s (%s)", path, exc)
        return None
    if not isinstance(data, dict):
        return None
    return ReferenceCorpus(
        model_id=str(data.get("model_id", "")),
        corpus_version=str(data.get("corpus_version", "")),
        vectors=list(data.get("vectors") or []),
    )


class EmbeddingOodScorer(OodScorerPort):
    """Embedding-backed OOD scorer with a deterministic frozen reference corpus."""

    def __init__(
        self,
        llm_provider: LLMProviderProtocol | None = None,
        reference_corpus: ReferenceCorpus | None = None,
        fallback: OodScorerPort | None = None,
    ) -> None:
        self._provider = llm_provider
        self._corpus = reference_corpus
        self._fallback: OodScorerPort = fallback or HeuristicOodScorer()

    async def score(
        self,
        query_text: str,
        *,
        query_embedding: list[float] | None = None,
        relevance_scores: list[float] | None = None,
    ) -> OodSignal:
        try:
            if self._corpus is None or self._corpus.is_empty:
                return await self._fallback.score(
                    query_text, query_embedding=query_embedding, relevance_scores=relevance_scores
                )

            emb = query_embedding
            if emb is None and self._provider is not None:
                emb = await self._provider.embedding(query_text)

            if emb is None or _is_zero_vector(emb):
                return await self._fallback.score(
                    query_text, relevance_scores=relevance_scores
                )

            ood = _clamp(compute_ood_score(emb, self._corpus.vectors))
            coverage = _coverage_from_relevance(relevance_scores)
            graph_relevance = coverage if coverage is not None else _clamp(1.0 - ood)
            return OodSignal(
                ood_score=ood,
                graph_relevance=graph_relevance,
                novelty_score=ood,
                source="embedding",
                model_id=self._corpus.model_id,
                corpus_version=self._corpus.corpus_version,
            )
        except Exception as exc:  # noqa: BLE001 — OOD scorer must never raise into the gate
            logger.debug("EmbeddingOodScorer fell back to heuristic: %s", exc)
            return await self._fallback.score(
                query_text, relevance_scores=relevance_scores
            )
