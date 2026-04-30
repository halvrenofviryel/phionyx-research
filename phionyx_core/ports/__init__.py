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

from .intuition_port import IntuitionPort
from .memory_port import MemoryPort
from .meta_port import MetaPort
from .narrative_port import NarrativePort
from .pedagogy_port import PedagogyPort
from .physics_port import PhysicsPort
from .policy_port import PolicyPort

# NOTE: OfstedPort moved to apps/school_ingest/ports/ofsted_port.py
# Per Echoism Core v1.0: Ofsted is product-specific, not part of core SDK

__all__ = [
    "PhysicsPort",
    "MemoryPort",
    "IntuitionPort",
    "PedagogyPort",
    "PolicyPort",
    "NarrativePort",
    "MetaPort",
]

