"""
Base Pipeline Block
===================

Base class for all pipeline blocks in the 46-block canonical pipeline.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar, Literal

DeterminismClass = Literal["strict", "seeded", "noisy_sensor"]
"""Determinism classification for a pipeline block.

- ``strict``: Given identical ``BlockContext``, produces identical ``BlockResult``
  (byte-for-byte on serialized data). No randomness, no wall-clock reads, no
  external I/O. Validated by the 100-run hash test in
  ``tests/contract/test_block_determinism.py``.
- ``seeded``: Uses randomness that is fully determined by a SHA-256 seed
  derived from ``BlockContext`` (e.g. ``turn_id``). Reproducible per turn but
  not cross-turn.
- ``noisy_sensor``: Delegates to an external measurement (LLM call, network,
  clock). Output is not reproducible across runs — treated as sensor input
  per Echoism Axiom 1.
"""


@dataclass
class BlockContext:
    """
    Context passed to each pipeline block.

    Contains all necessary state and services needed for block execution.
    """
    # State
    user_input: str
    card_type: str
    card_title: str
    scene_context: str
    card_result: str

    # Session/Scenario
    scenario_id: str | None = None
    scenario_step_id: str | None = None
    session_id: str | None = None

    # Physics State
    current_amplitude: float = 5.0
    current_entropy: float = 0.5
    current_integrity: float = 100.0
    previous_phi: float | None = None

    # Participant & Runtime
    participant: Any | None = None  # Participant abstraction
    mode: str | None = None  # Runtime mode (e.g., "toygar_core", "story", "game_scenario")
    strategy: str | None = None  # Runtime strategy (e.g., "normal", "stabilize", "comfort")

    # Envelope tracking
    envelope_message_id: str | None = None  # TurnEnvelope message_id for transcript tracking
    envelope_turn_id: int | None = None  # TurnEnvelope turn_id for transcript tracking
    envelope_user_text_sha256: str | None = None  # TurnEnvelope user_text_sha256 for integrity

    # Capabilities
    capabilities: Any | None = None  # RunCapabilities
    capability_deriver: Any | None = None  # CapabilityDeriverProtocol

    # v4 optional extensions (AD-6: backward compat via Optional)
    v4_perceptual_frame: Any | None = None   # PerceptualFrame
    v4_world_state: Any | None = None        # WorldStateSnapshot
    v4_active_goals: Any | None = None       # List[GoalObject]
    v4_action_intent: Any | None = None      # ActionIntent
    v4_ethics_decision: Any | None = None    # EthicsDecision
    v4_confidence: Any | None = None         # ConfidencePayload
    v4_workspace_events: Any | None = None   # List[WorkspaceEvent]
    v4_audit_record: Any | None = None       # AuditRecord
    v4_learning_updates: Any | None = None   # List[LearningUpdate]
    v4_error_payload: Any | None = None      # ErrorPayload
    pipeline_version: str = "3.0.0"             # "2.5.0" or "3.0.0"

    # Additional context (extensible)
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class BlockResult:
    """
    Result of a pipeline block execution.
    """
    block_id: str
    status: str  # "ok", "error", "skipped"
    data: dict[str, Any] | None = None
    error: Exception | None = None
    skip_reason: str | None = None
    # v4 optional extension (AD-6)
    v4_error_payload: Any | None = None  # ErrorPayload

    def is_success(self) -> bool:
        """Check if block executed successfully."""
        return self.status == "ok"

    def is_skipped(self) -> bool:
        """Check if block was skipped."""
        return self.status == "skipped"

    def is_error(self) -> bool:
        """Check if block encountered an error."""
        return self.status == "error"


class PipelineBlock(ABC):
    """
    Base class for all pipeline blocks.

    Each of the 46 canonical blocks (v3.8.0, see
    ``phionyx_core/contracts/telemetry/canonical_blocks_v3_8_0.json``) should
    extend this class. v3.7.0 (45 blocks) remains loadable for backwards
    compatibility.
    """

    # Default determinism class. Subclasses that call an LLM, read the wall
    # clock, or consume entropy should override this. See ``DeterminismClass``
    # docstring and ``docs/arxiv/DETERMINISM_MATRIX.md``.
    determinism: ClassVar[DeterminismClass] = "strict"

    def __init__(self, block_id: str, claim_refs: tuple = ()):
        """
        Initialize pipeline block.

        Args:
            block_id: Canonical block ID (e.g., "cognitive_layer", "narrative_layer").
            claim_refs: Optional tuple of UKIPO patent-claim references this block
                implements. Format: ``("SF1:C4", "SF1:C15", ...)``. Additive and
                optional; existing blocks that do not pass this argument keep an
                empty tuple for backwards compatibility. Used by contract tests
                to prove claim→code traceability.
        """
        self.block_id = block_id
        self.claim_refs = tuple(claim_refs)

    @abstractmethod
    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute the block logic.

        Args:
            context: Block context containing state and inputs

        Returns:
            BlockResult with execution status and data
        """
        pass

    def should_skip(self, context: BlockContext) -> str | None:
        """
        Check if this block should be skipped.

        Args:
            context: Block context

        Returns:
            Skip reason string if block should be skipped, None otherwise
        """
        return None

    def get_dependencies(self) -> list[str]:
        """
        Get list of block IDs that must execute before this block.

        Returns:
            List of block IDs
        """
        return []

