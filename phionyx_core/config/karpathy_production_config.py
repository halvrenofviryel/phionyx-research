"""
Karpathy Features Production Configuration
==========================================

Faz 3.5: Production Deployment

Production-ready configuration for Karpathy features.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import os


@dataclass
class KarpathyProductionConfig:
    """Production configuration for Karpathy features."""
    
    # Feature flags
    assumption_enabled: bool = True
    inconsistency_enabled: bool = True
    complexity_enabled: bool = True
    pushback_enabled: bool = True
    success_criteria_enabled: bool = True
    tradeoff_enabled: bool = True
    plan_enabled: bool = True
    clarification_enabled: bool = True
    dead_code_enabled: bool = True
    orthogonal_guard_enabled: bool = True
    challenge_enabled: bool = True
    
    # Complexity budget
    max_cyclomatic: int = 10
    max_cognitive: int = 15
    max_nesting: int = 4
    max_function_length: int = 50
    max_class_complexity: int = 20
    
    # Governance
    strict_mode: bool = True
    block_on_critical: bool = True
    block_on_high: bool = True
    
    # Performance
    cache_enabled: bool = True
    parallel_execution: bool = True
    max_analysis_depth: int = 100
    
    # Monitoring
    metrics_enabled: bool = True
    audit_trail_enabled: bool = True
    evidence_chain_enabled: bool = True
    
    @classmethod
    def from_env(cls) -> 'KarpathyProductionConfig':
        """Load configuration from environment variables."""
        return cls(
            assumption_enabled=os.getenv('KARPATHY_ASSUMPTION_ENABLED', 'true').lower() == 'true',
            inconsistency_enabled=os.getenv('KARPATHY_INCONSISTENCY_ENABLED', 'true').lower() == 'true',
            complexity_enabled=os.getenv('KARPATHY_COMPLEXITY_ENABLED', 'true').lower() == 'true',
            pushback_enabled=os.getenv('KARPATHY_PUSHBACK_ENABLED', 'true').lower() == 'true',
            max_cyclomatic=int(os.getenv('COMPLEXITY_MAX_CYCLOMATIC', '10')),
            max_cognitive=int(os.getenv('COMPLEXITY_MAX_COGNITIVE', '15')),
            max_nesting=int(os.getenv('COMPLEXITY_MAX_NESTING', '4')),
            max_function_length=int(os.getenv('COMPLEXITY_MAX_FUNCTION_LENGTH', '50')),
            strict_mode=os.getenv('GOVERNANCE_STRICT_MODE', 'true').lower() == 'true',
            block_on_critical=os.getenv('GOVERNANCE_BLOCK_ON_CRITICAL', 'true').lower() == 'true',
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "assumption_enabled": self.assumption_enabled,
            "inconsistency_enabled": self.inconsistency_enabled,
            "complexity_enabled": self.complexity_enabled,
            "pushback_enabled": self.pushback_enabled,
            "max_cyclomatic": self.max_cyclomatic,
            "max_cognitive": self.max_cognitive,
            "max_nesting": self.max_nesting,
            "max_function_length": self.max_function_length,
            "strict_mode": self.strict_mode,
            "block_on_critical": self.block_on_critical,
        }


__all__ = [
    'KarpathyProductionConfig',
]

