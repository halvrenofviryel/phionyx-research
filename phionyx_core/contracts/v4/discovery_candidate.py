"""
DiscoveryCandidate — v4 Schema §3.12
=======================================

Extends IntuitionGraph with novelty/transfer/robustness scoring
for open-ended discovery evaluation.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DiscoveryCandidate(BaseModel):
    """
    v4 DiscoveryCandidate schema.

    Represents a candidate discovery from the IntuitionGraph
    with v4 novelty and transfer scoring.
    """
    candidate_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique candidate identifier"
    )
    description: str = Field(
        ...,
        description="Discovery candidate description"
    )

    # Novelty scoring (v4 §7)
    novelty_score: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Novelty = 1 - max_cosine_similarity to existing knowledge"
    )
    transfer_potential: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Average relevance across domains"
    )
    robustness_score: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="How robust this discovery is to perturbation"
    )
    composite_score: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Weighted composite of novelty, transfer, robustness"
    )

    # Discovery provenance
    source_graph_nodes: list[str] = Field(
        default_factory=list,
        description="IntuitionGraph node IDs that contributed"
    )
    source_patterns: list[str] = Field(
        default_factory=list,
        description="Patterns identified"
    )
    domain: str = Field(
        default="general",
        description="Discovery domain"
    )

    # Cross-domain relevance
    domain_relevance: dict[str, float] = Field(
        default_factory=dict,
        description="Relevance score per domain"
    )

    # Embedding for similarity computation
    embedding_vector: list[float] | None = Field(
        None,
        description="Embedding vector for novelty computation"
    )

    # Evaluation
    human_validated: bool = Field(
        default=False,
        description="Whether a human has validated this discovery"
    )
    validation_score: float | None = Field(
        None, ge=0.0, le=1.0,
        description="Human validation score"
    )

    # Timestamps
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    validated_at: datetime | None = None

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

    def compute_composite(
        self,
        w_novelty: float = 0.4,
        w_transfer: float = 0.3,
        w_robustness: float = 0.3
    ) -> float:
        """Compute weighted composite score."""
        self.composite_score = (
            w_novelty * self.novelty_score
            + w_transfer * self.transfer_potential
            + w_robustness * self.robustness_score
        )
        return self.composite_score

    model_config = ConfigDict(json_schema_extra={'example': {'description': 'Emotional resonance correlates with learning retention', 'novelty_score': 0.85, 'transfer_potential': 0.6, 'robustness_score': 0.7}})
