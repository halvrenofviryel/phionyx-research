"""
Social Module — v4 §5 (AGI Layer 5)
=====================================

Social reality modeling for Phionyx cognitive runtime.

Components:
- TrustPropagation: Transitive trust computation
"""

from .trust_propagation import TrustAssessment, TrustEdge, TrustNetwork

__all__ = [
    "TrustNetwork",
    "TrustEdge",
    "TrustAssessment",
]
