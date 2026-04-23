"""
Core Metrics Module
===================

Duygusal AI NPC garantileri için metrik ve KPI hesaplama modülleri.
"""

from core.metrics.emotional_kpi_engine import (
    EmotionalTelemetryInput,
    EmotionalKPIOutput,
    compute_all_kpis,
    validate_kpi_thresholds,
    calculate_profile_separation,
    calculate_long_term_recall,
    calculate_personality_drift,
    calculate_echo_reactivity,
    calculate_empathy_safety,
    calculate_ethical_violation,
)

__all__ = [
    "EmotionalTelemetryInput",
    "EmotionalKPIOutput",
    "compute_all_kpis",
    "validate_kpi_thresholds",
    "calculate_profile_separation",
    "calculate_long_term_recall",
    "calculate_personality_drift",
    "calculate_echo_reactivity",
    "calculate_empathy_safety",
    "calculate_ethical_violation",
]

