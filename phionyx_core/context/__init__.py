"""
Phionyx Context SDK
====================

Context Regulator Layer for managing state across LLM sessions.
"""

from .composer import HarmonicComposer
from .definitions import ContextDefinition, ContextMode, ContextRule
from .detector import DetectionResult, ModeDetector
from .manager import ContextManager
from .multi_intent import IntentSegment, MultiIntentDetector

__all__ = [
    "ContextMode",
    "ContextRule",
    "ContextDefinition",
    "ModeDetector",
    "DetectionResult",
    "ContextManager",
    "MultiIntentDetector",
    "IntentSegment",
    "HarmonicComposer",
]

