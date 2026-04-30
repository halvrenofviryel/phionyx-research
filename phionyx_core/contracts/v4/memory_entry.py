"""
MemoryEntry — v4 Schema §3.5
==============================

Composes existing ForgettingManager + SemanticTimeDecayManager logic
with v4 boundary zone concept (immutable/gated/adaptive).
"""

from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, timezone
import uuid


class BoundaryZone(str, Enum):
    """Memory boundary zone classification (v4 §3.5)."""
    IMMUTABLE = "immutable"     # Core identity, safety rules — never modified
    GATED = "gated"             # Requires approval to modify (learning gate)
    ADAPTIVE = "adaptive"       # Free to update via standard learning


class MemoryType(str, Enum):
    """Memory content type."""
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    WORKING = "working"


class MemoryEntry(BaseModel):
    """
    v4 MemoryEntry schema.

    Adds boundary zone classification to existing memory infrastructure.
    Composes ForgettingManager decay semantics and EmbeddingCache vectors.
    """
    memory_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique memory identifier"
    )
    content: str = Field(..., description="Memory content text")
    memory_type: MemoryType = Field(
        default=MemoryType.EPISODIC,
        description="Memory classification"
    )
    boundary_zone: BoundaryZone = Field(
        default=BoundaryZone.ADAPTIVE,
        description="v4 boundary zone — controls mutability"
    )

    # Embedding / retrieval
    embedding_vector: Optional[List[float]] = Field(
        None,
        description="Embedding vector for similarity search"
    )
    similarity_score: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description="Last retrieval similarity score"
    )

    # Decay semantics (from SemanticTimeDecay)
    decay_rate: float = Field(
        default=0.1,
        ge=0.0,
        description="Decay rate lambda for exp(-lambda*t)"
    )
    half_life_seconds: float = Field(
        default=86400.0,
        gt=0.0,
        description="Half-life in seconds"
    )
    current_strength: float = Field(
        default=1.0,
        ge=0.0, le=1.0,
        description="Current memory strength after decay"
    )
    last_access: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last access timestamp for decay calculation"
    )

    # Provenance
    source_module: str = Field(
        default="memory_store",
        description="Module that created this memory"
    )
    source_turn_id: Optional[int] = Field(
        None,
        description="Turn ID when memory was created"
    )
    conversation_id: Optional[str] = None

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

    # Metadata
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def is_modifiable(self) -> bool:
        """Check if this memory can be modified."""
        return self.boundary_zone != BoundaryZone.IMMUTABLE

    def requires_approval(self) -> bool:
        """Check if modification requires learning gate approval."""
        return self.boundary_zone == BoundaryZone.GATED

    model_config = ConfigDict(json_schema_extra={'example': {'content': 'User prefers concise responses', 'memory_type': 'semantic', 'boundary_zone': 'adaptive', 'decay_rate': 0.1}})
