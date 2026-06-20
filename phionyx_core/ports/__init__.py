"""
Phionyx SDK Ports
==================

Port interfaces for all SDK modules.
Enables modular packaging: modules can be replaced with Null/No-Op implementations.

Port-Adapter Pattern:
- Each SDK module has a Port interface
- Real implementations (Physics v2.1, Memory, etc.)
- Null implementations (No-Op) for modules not included in product
- Product profiles select which ports to use
"""

from .physics_port import PhysicsPort
from .memory_port import MemoryPort
from .intuition_port import IntuitionPort
from .pedagogy_port import PedagogyPort
from .policy_port import PolicyPort
from .narrative_port import NarrativePort
from .meta_port import MetaPort
from .ood_scorer_port import OodScorerPort, OodSignal
from .learning_record_port import (
    LearningRecordPort,
    InMemoryLearningRecordPort,
    NullLearningRecordPort,
)

# NOTE: product-specific inspection adapters live in the product layer, not core.
# Per Echoism Core v1.0: domain-specific ingest ports are product-specific, not part of core SDK

__all__ = [
    "PhysicsPort",
    "MemoryPort",
    "IntuitionPort",
    "PedagogyPort",
    "PolicyPort",
    "NarrativePort",
    "MetaPort",
    "OodScorerPort",
    "OodSignal",
    "LearningRecordPort",
    "InMemoryLearningRecordPort",
    "NullLearningRecordPort",
]

