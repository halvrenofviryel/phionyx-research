"""
Phionyx Context SDK
====================

Context Regulator Layer for managing state across LLM sessions.
"""

from .definitions import ContextMode, ContextRule, ContextDefinition
from .detector import ModeDetector, DetectionResult
from .manager import ContextManager
from .multi_intent import MultiIntentDetector, IntentSegment
from .composer import HarmonicComposer

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

