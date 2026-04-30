"""
v4 Schema Contracts — AGI/ASI Deterministic System v4.0
=======================================================

13 canonical schemas that compose/wrap existing Phionyx models.
Architectural Decision AD-1: Composition > Replacement.

All v4 schemas are backward-compatible — existing pipelines continue
to work without v4 fields (Optional everywhere).
"""

from .action_intent import ActionIntent, ActionType, ReversibilityLevel
from .audit_record import AuditRecord
from .confidence_payload import ConfidencePayload, UncertaintyType
from .discovery_candidate import DiscoveryCandidate
from .error_payload import ErrorPayload, ErrorSeverity
from .ethics_decision import DeliberationLayer, EthicsDecision, EthicsVerdict
from .goal_object import GoalObject, GoalPriority, GoalStatus
from .input_signal import InputSignal
from .learning_update import LearningGateDecision, LearningUpdate
from .memory_entry import BoundaryZone, MemoryEntry
from .perceptual_frame import PerceptualFrame
from .workspace_event import SalienceLevel, WorkspaceEvent
from .world_state_snapshot import WorldStateSnapshot

__all__ = [
    # Schemas
    "InputSignal",
    "PerceptualFrame",
    "WorldStateSnapshot",
    "GoalObject", "GoalPriority", "GoalStatus",
    "MemoryEntry", "BoundaryZone",
    "ActionIntent", "ActionType", "ReversibilityLevel",
    "EthicsDecision", "EthicsVerdict", "DeliberationLayer",
    "ConfidencePayload", "UncertaintyType",
    "WorkspaceEvent", "SalienceLevel",
    "AuditRecord",
    "LearningUpdate", "LearningGateDecision",
    "DiscoveryCandidate",
    "ErrorPayload", "ErrorSeverity",
]

V4_SCHEMA_VERSION = "4.0.0"
