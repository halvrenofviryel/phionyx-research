"""
Assumption Types
================

Shared types for assumption-related modules.
"""

from typing import List, Optional
from dataclasses import dataclass


@dataclass
class Assumption:
    """Assumption data structure."""
    type: str  # "input_type", "state", "dependency", "performance"
    description: str
    code_reference: Optional[str] = None  # File:line reference
    confidence: float = 1.0  # 0.0-1.0
    evidence: Optional[List[str]] = None


__all__ = ['Assumption']

