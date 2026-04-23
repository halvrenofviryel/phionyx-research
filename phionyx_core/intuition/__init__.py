"""
Core Intuition Module - GraphRAG Engine
========================================

The Intuition Engine provides hidden concept association discovery
through a lightweight graph-based knowledge system.

Key Features:
- Concept extraction from natural language
- Phi-weighted association formation
- Multi-hop inference for hidden context
- Physics-driven edge strength
"""

from .graph_engine import GraphEngine, Concept, Association, HiddenContext
from .visualizer import GraphVisualizer

__all__ = ["GraphEngine", "Concept", "Association", "HiddenContext", "GraphVisualizer"]

