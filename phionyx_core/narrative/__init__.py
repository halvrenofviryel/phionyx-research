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

from .engine import NarrativeConfig, NarrativeEngine

# Lore mapping (moved from core-narrative)
from .lore_mapping import (
    ALL_MAPPINGS,
    InterventionMapping,
    InterventionType,
    LoreMapping,
    RiskLevel,
    get_intervention_mapping,
    get_lore_mapping,
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

