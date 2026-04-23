"""
v4 Schema Contracts — AGI/ASI Deterministic System v4.0
=======================================================

13 canonical schemas that compose/wrap existing Phionyx models.
Architectural Decision AD-1: Composition > Replacement.

All v4 schemas are backward-compatible — existing pipelines continue
to work without v4 fields (Optional everywhere).
"""

from .input_signal import InputSignal
from .perceptual_frame import PerceptualFrame
from .world_state_snapshot import WorldStateSnapshot
from .goal_object import GoalObject, GoalPriority, GoalStatus
from .memory_entry import MemoryEntry, BoundaryZone
from .action_intent import ActionIntent, ActionType, ReversibilityLevel
from .ethics_decision import EthicsDecision, EthicsVerdict, DeliberationLayer
from .confidence_payload import ConfidencePayload, UncertaintyType
from .workspace_event import WorkspaceEvent, SalienceLevel
from .audit_record import AuditRecord
from .learning_update import LearningUpdate, LearningGateDecision
from .discovery_candidate import DiscoveryCandidate
from .error_payload import ErrorPayload, ErrorSeverity

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
