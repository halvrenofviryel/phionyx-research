"""
Phionyx Narrative Engine
=========================

Provider-agnostic narrative generation with automatic physics and safety constraints.

The NarrativeEngine automatically:
- Injects Physics constraints (Phi, Entropy) into prompts
- Applies Safety filters (Ethics Engine)
- Uses LiteLLM for model-agnostic LLM calls
- Supports RAG context (Memory), GraphRAG (Intuition), and Seasonal context
"""

from .engine import NarrativeEngine, NarrativeConfig

# Lore mapping (moved from core-narrative)
from .lore_mapping import (
    LoreMapping,
    InterventionMapping,
    RiskLevel,
    InterventionType,
    get_lore_mapping,
    get_intervention_mapping,
    ALL_MAPPINGS
)

__all__ = [
    "NarrativeEngine",
    "NarrativeConfig",
    "LoreMapping",
    "InterventionMapping",
    "RiskLevel",
    "InterventionType",
    "get_lore_mapping",
    "get_intervention_mapping",
    "ALL_MAPPINGS"
]

