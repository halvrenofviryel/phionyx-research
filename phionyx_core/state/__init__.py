"""
Phionyx State - EchoState2 Core Module
========================================

Echoism Core v1.0 canonical state model implementation.

Exports:
- EchoState2: Canonical state model
- AuxState: Optional control layer state
- StateMigration: Old to new state mapper
- StateSnapshot: Serialize/deserialize utilities
"""

from phionyx_core.state.aux_state import AuxState
from phionyx_core.state.echo_event import EchoEvent, EventReference
from phionyx_core.state.echo_ontology import EchoOntology
from phionyx_core.state.echo_state_2 import EchoState2, EchoState2Plus
from phionyx_core.state.ethics import EthicsRiskAssessor, EthicsVector
from phionyx_core.state.ethics_enforcement import (
    EthicsEnforcementConfig,
    EthicsPolicyConfig,
    apply_ethics_after_response,
    apply_ethics_enforcement,
    apply_forced_damping,
    check_ethics_before_response,
    generate_safety_message,
    generate_safety_message_policy,
)
from phionyx_core.state.measurement_mapper import MeasurementMapper, MeasurementVector
from phionyx_core.state.measurement_mapper_v2 import EvidenceSpan, MeasurementPacket
from phionyx_core.state.physics_integration import (
    calculate_phi_v2_with_state,
    get_time_delta_from_state,
    update_physics_params_with_state,
)
from phionyx_core.state.resonance import (
    calculate_resonance_score,
    get_resonance_growth_rate,
    update_resonance_from_events,
)
from phionyx_core.state.state_adapter import EchoState2Adapter

# StateMigration is not a class, it's a module with functions
# from phionyx_core.state.state_migration import unified_to_echo_state2, echo_state2_to_unified
from phionyx_core.state.state_snapshot import StateSnapshot
from phionyx_core.state.time_manager import TimeManager
from phionyx_core.state.ukf_adaptive_noise import (
    calculate_dynamic_measurement_noise,
    calculate_dynamic_process_noise,
    calculate_emotional_volatility,
    create_dynamic_measurement_noise_matrix,
    create_dynamic_process_noise_matrix,
    get_sensor_quality_from_provider,
)
from phionyx_core.state.ukf_measurement_integration import UKFMeasurementIntegration
from phionyx_core.state.ukf_process_model import create_echoism_process_model, echoism_process_model

__all__ = [
    "EchoState2",
    "EchoState2Plus",
    "AuxState",
    "StateSnapshot",
    "EchoState2Adapter",
    "TimeManager",
    "get_time_delta_from_state",
    "calculate_phi_v2_with_state",
    "update_physics_params_with_state",
    "EchoEvent",
    "EventReference",
    "EchoOntology",
    "MeasurementMapper",
    "MeasurementVector",
    "MeasurementPacket",
    "EvidenceSpan",
    "UKFMeasurementIntegration",
    "echoism_process_model",
    "create_echoism_process_model",
    "calculate_resonance_score",
    "update_resonance_from_events",
    "get_resonance_growth_rate",
    "calculate_dynamic_measurement_noise",
    "create_dynamic_measurement_noise_matrix",
    "calculate_emotional_volatility",
    "calculate_dynamic_process_noise",
    "create_dynamic_process_noise_matrix",
    "get_sensor_quality_from_provider",
    "EthicsVector",
    "EthicsRiskAssessor",
    "EthicsEnforcementConfig",
    "EthicsPolicyConfig",
    "apply_ethics_enforcement",
    "apply_forced_damping",
    "generate_safety_message",
    "generate_safety_message_policy",
    "check_ethics_before_response",
    "apply_ethics_after_response",
]

