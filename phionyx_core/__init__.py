"""
Phionyx Core -- Deterministic, Auditable AI Cognition Runtime
=============================================================

Kernel, physics, pipeline, state, contracts, schemas.

This is the canonical CORE package for Phionyx.
All kernel logic, physics computations, and contracts live here.

Boundaries:
- CORE must not import from BRIDGE or PRODUCT
- CORE must not contain product-specific terms
- CORE must enforce canonical block order
- CORE must maintain determinism guarantees

Quick start::

    from phionyx_core import BlockContext, BlockResult, PipelineBlock
    from phionyx_core.physics import calculate_phi_v2, calculate_dynamic_entropy

Public API is organized into the following namespaces:

- ``phionyx_core.pipeline``   -- Pipeline block base classes
- ``phionyx_core.physics``    -- Physics formulas, constants, types
- ``phionyx_core.state``      -- EchoState2 canonical state model
- ``phionyx_core.profiles``   -- Profile configuration system
- ``phionyx_core.contracts``  -- Telemetry contracts, envelopes
- ``phionyx_core.causality``  -- Causal graph, intervention, counterfactual
- ``phionyx_core.governance`` -- Kill switch, HITL, RBAC, deliberative ethics
- ``phionyx_core.meta``       -- Confidence estimation, self-model, knowledge boundary
- ``phionyx_core.orchestrator`` -- Echo orchestrator, block factory
- ``phionyx_core.cep``         -- Conscious Echo Proof engine, guards, config
"""

__version__ = "0.2.0"

# ---------------------------------------------------------------------------
# Pipeline (always available -- no external deps)
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# CEP (Conscious Echo Proof) -- synthetic psychopathology prevention
# ---------------------------------------------------------------------------
from .cep import (
    CEPConfig,
    CEPFlags,
    CEPMetrics,
    CEPResult,
    CEPThresholds,
    ConsciousEchoProofEngine,
    EchoSelfThresholdGuard,
    load_cep_config,
)

# ---------------------------------------------------------------------------
# Contracts
# ---------------------------------------------------------------------------
from .contracts.telemetry import get_canonical_blocks

# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------
from .orchestrator.echo_orchestrator import EchoOrchestrator, OrchestratorServices

# ---------------------------------------------------------------------------
# Physics dynamics (entropy, stability, complexity)
# ---------------------------------------------------------------------------
from .physics.dynamics import (
    calculate_complexity,
    calculate_dynamic_entropy,
    update_stability,
)

# ---------------------------------------------------------------------------
# Physics formulas (pure math -- no external deps)
# ---------------------------------------------------------------------------
from .physics.formulas import (
    calculate_echo_energy,
    calculate_entropy_shannon,
    calculate_momentum,
    calculate_phi_cognitive,
    calculate_phi_physical,
    calculate_phi_v2,
    calculate_phi_v2_1,
    calculate_resonance_force,
    classify_resonance,
)

# ---------------------------------------------------------------------------
# Physics tuner & params
# ---------------------------------------------------------------------------
from .physics.tuner import PhysicsParams, ProfileTuner

# ---------------------------------------------------------------------------
# Physics types (pydantic models -- core dependency)
# ---------------------------------------------------------------------------
from .physics.types import PhiComponents, PhysicsInput, PhysicsOutput, PhysicsState
from .pipeline.base import BlockContext, BlockResult, PipelineBlock

# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------
from .profiles import (
    Profile,
    ProfileLoader,
    ProfileManager,
    get_active_profile,
    get_global_manager,
)

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
from .state.echo_state_2 import EchoState2, EchoState2Plus

# ---------------------------------------------------------------------------
# __all__ -- explicit public API surface
# ---------------------------------------------------------------------------
__all__ = [
    # Version
    "__version__",

    # Pipeline
    "PipelineBlock",
    "BlockContext",
    "BlockResult",

    # Physics types
    "PhysicsInput",
    "PhysicsOutput",
    "PhysicsState",
    "PhiComponents",

    # Physics formulas
    "calculate_phi_v2",
    "calculate_phi_v2_1",
    "calculate_phi_cognitive",
    "calculate_phi_physical",
    "calculate_resonance_force",
    "calculate_echo_energy",
    "calculate_entropy_shannon",
    "calculate_momentum",
    "classify_resonance",

    # Physics dynamics
    "calculate_dynamic_entropy",
    "update_stability",
    "calculate_complexity",

    # Physics tuner
    "PhysicsParams",
    "ProfileTuner",

    # State
    "EchoState2",
    "EchoState2Plus",

    # Orchestrator
    "EchoOrchestrator",
    "OrchestratorServices",

    # Profiles
    "ProfileLoader",
    "ProfileManager",
    "Profile",
    "get_global_manager",
    "get_active_profile",

    # Contracts
    "get_canonical_blocks",

    # CEP (Conscious Echo Proof)
    "ConsciousEchoProofEngine",
    "EchoSelfThresholdGuard",
    "CEPConfig",
    "load_cep_config",
    "CEPResult",
    "CEPMetrics",
    "CEPThresholds",
    "CEPFlags",
]
