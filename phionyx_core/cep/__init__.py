"""
Conscious Echo Proof (CEP) Core Module
======================================

Core module for evaluating responses against Conscious Echo Proof criteria.
Detects self-narrative patterns, trauma language, and echo repetition.

Exports:
- ConsciousEchoProofEngine: Main evaluation engine
- EchoSelfThresholdGuard: Φ-Yankı eşiği guard mekanizması
- CEPConfig: Configuration model
- CEPResult: Evaluation result
- CEPMetrics: Computed metrics
- CEPThresholds: Threshold configuration
- CEPFlags: Evaluation flags
"""

from .cep_engine import ConsciousEchoProofEngine
from .echo_self_guard import EchoSelfThresholdGuard
from .cep_config import CEPConfig, load_cep_config
from .cep_types import (
    CEPMetrics,
    CEPThresholds,
    CEPFlags,
    CEPResult
)

__all__ = [
    "ConsciousEchoProofEngine",
    "EchoSelfThresholdGuard",
    "CEPConfig",
    "load_cep_config",
    "CEPMetrics",
    "CEPThresholds",
    "CEPFlags",
    "CEPResult",
]

__version__ = "1.0.0"

