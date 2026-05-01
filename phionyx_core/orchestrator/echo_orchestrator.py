"""
Echo Orchestrator
=================

Core orchestration logic for the 46-block Phionyx pipeline (v3.8.0).

This class contains the business logic for orchestrating the pipeline execution.
It has NO dependencies on FastAPI, HTTP, or database models.
"""

import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional, Protocol

from ..pipeline.base import BlockContext, BlockResult, PipelineBlock

if TYPE_CHECKING:
    from ..profiles.schema import ExecutionGuardConfig
# Import canonical block order
from phionyx_core.contracts.telemetry import get_canonical_blocks as get_canonical_block_order

from .dependency_validator import DependencyValidator
from .dynamic_grouping import DynamicGrouping
from .early_exit_optimizer import EarlyExitOptimizer
from .execution_guard import ExecutionGuard
from .parallel_executor import ParallelExecutor
from .rollback_manager import RollbackManager

logger = logging.getLogger(__name__)

# OpenTelemetry integration (optional)
try:
    from opentelemetry.trace import Status, StatusCode

    from phionyx_core.telemetry import get_tracer, is_opentelemetry_enabled
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    get_tracer = None
    def is_opentelemetry_enabled() -> bool:
        return False
    Status = None
    StatusCode = None


class TelemetryCollectorProtocol(Protocol):
    """Protocol for telemetry collection (to avoid direct dependency)."""
    def start_block(self, block_id: str, timing_label: str, metadata: dict[str, Any] | None = None) -> None:
        """Start tracking a block."""
        ...

    def end_block(self, block_id: str, status: str = "ok", events: list | None = None) -> None:
        """End tracking a block."""
        ...


@dataclass
class OrchestratorServices:
    """
    Services needed by the orchestrator.

    All services are injected via dependency injection to avoid hard dependencies.
    This allows the orchestrator to remain in core without bridge dependencies.
    """
    # Processor services
    processor: Any | None = None  # EngineProcessor
    response_generator: Any | None = None  # EngineResponseGenerator

    # Physics/Math services
    phi_engine: Any | None = None  # PhiEngine
    entropy_engine: Any | None = None  # EntropyEngine

    # Emotion services
    emotion_estimator: Any | None = None  # EmotionEstimator
    neurotransmitter: Any | None = None  # NeurotransmitterEngine

    # State services
    state_store: Any | None = None  # StateStore
    echo_state_store: Any | None = None  # EchoStateStore (legacy)

    # Time management
    time_managers: dict[str, Any] | None = None  # Dict of TimeManager instances

    # Additional services (can be extended)
    additional_services: dict[str, Any] | None = None

    def __post_init__(self):
        """Initialize default values."""
        if self.time_managers is None:
            self.time_managers = {}
        if self.additional_services is None:
            self.additional_services = {}


class EchoOrchestrator:
    """
    Core orchestrator for the Phionyx pipeline.

    Responsibilities:
    - Execute the 46-block canonical pipeline in order (v3.8.0)
    - Coordinate block execution
    - Handle block dependencies and ordering
    - Manage pipeline state transitions

    This class contains NO HTTP/FastAPI/DB dependencies.
    """

    def __init__(
        self,
        services: OrchestratorServices,
        telemetry_collector: TelemetryCollectorProtocol | None = None,
        enable_rollback: bool = True,
        enable_parallel: bool = True,
        enable_execution_guard: bool = True,
        execution_guard_config: Optional["ExecutionGuardConfig"] = None,
    ):
        """
        Initialize orchestrator.

        Args:
            services: Injected services
            telemetry_collector: Optional telemetry collector for observability
            enable_rollback: Whether to enable rollback on block failures (default: True)
            enable_parallel: Whether to enable parallel execution (default: True)
            enable_execution_guard: Enable comprehensive execution guard (CRITICAL for infinite loop prevention, default: True)
            execution_guard_config: Optional per-profile limits. ``None`` reproduces the
                hard-coded defaults (max_iterations=3× block count, max_block_executions=2,
                max_execution_time=300s, max_repeated_sequence=3) for backwards compatibility.
        """
        self.services = services
        self.telemetry_collector = telemetry_collector
        self.enable_parallel = enable_parallel
        self.enable_execution_guard = enable_execution_guard

        # Load canonical block order
        self.block_order = get_canonical_block_order()

        # Block registry (will be populated with block implementations)
        self.blocks: dict[str, PipelineBlock] = {}

        # CRITICAL: Execution guard (infinite loop prevention)
        # Multiple protection layers: iteration limit, block execution tracking, timeout, circular sequence detection
        self.execution_guard = (
            ExecutionGuard.from_config(
                execution_guard_config,
                block_order_length=len(self.block_order),
            )
            if enable_execution_guard
            else None
        )

        if self.execution_guard:
            logger.info("Execution guard enabled: Infinite loop prevention active")

        # Dependency validator
        self.dependency_validator = DependencyValidator()

        # Parallel executor
        self.parallel_executor = ParallelExecutor(
            dependency_validator=self.dependency_validator,
            enable_parallel=enable_parallel
        )

        # Early exit optimizer
        self.early_exit_optimizer = EarlyExitOptimizer()

        # Dynamic grouping
        self.dynamic_grouping = DynamicGrouping()

        # Validate execution order on initialization
        is_valid, violations = self.dependency_validator.validate_execution_order(self.block_order)
        if not is_valid:
            logger.warning(f"Block execution order validation failed: {violations}")
        else:
            logger.debug("Block execution order validated successfully")

        # Rollback manager
        self.rollback_manager = RollbackManager(enabled=enable_rollback)

    def register_block(self, block: PipelineBlock) -> None:
        """
        Register a pipeline block.

        Args:
            block: Pipeline block instance
        """
        self.blocks[block.block_id] = block
        logger.debug(f"Registered block: {block.block_id}")

    # ------------------------------------------------------------------ #
    # Plan v3: bounded narrative regenerate retry                        #
    # ------------------------------------------------------------------ #

    #: Allowlist of blocks that re-run on a regenerate retry. State-mutating
    #: blocks (unified_state_update_esc, state_update_physics,
    #: neurotransmitter_memory_growth, emotion_estimation, causal_graph_update,
    #: phi_publish, world_state_snapshot, memory_consolidation) are
    #: deliberately EXCLUDED so a retry never double-writes state (P2 scope
    #: bound). Order here mirrors v3.8.0 canonical order between
    #: narrative_layer and response_revision_gate.
    _REGEN_RETRY_BLOCKS = (
        "narrative_layer",
        "ethics_post_response",
        "action_intent_gate",
        "behavioral_drift_detection",
        "entropy_amplitude_post_gate",
        "phi_computation",
        "entropy_computation",
        "confidence_fusion",
        "arbitration_resolve",
        "response_revision_gate",
    )

    #: Hard cap on regenerate retries per turn. Axiom 6 determinism +
    #: prevents retry storms.
    _REGEN_MAX_ATTEMPTS = 1

    def _compute_retry_seed(self, context: "BlockContext") -> str:
        """Deterministic retry seed: SHA-256 of turn-id + state snapshot.

        No clock sources — reproducible per Axiom 6 and SF1 Claim 14.
        """
        import hashlib
        import json as _json

        payload = {
            "turn_id": getattr(context, "envelope_turn_id", None),
            "session_id": getattr(context, "session_id", None),
            "scenario_step_id": getattr(context, "scenario_step_id", None),
            "attempts": (context.metadata or {}).get("_regen_attempts", 0),
            "phi": (context.metadata or {}).get("phi"),
            "entropy": (context.metadata or {}).get("entropy"),
            "confidence": ((context.metadata or {}).get("confidence_result") or {}).get("confidence"),
        }
        blob = _json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()

    def _build_regeneration_constraints(self, context: "BlockContext") -> dict[str, Any]:
        """Assemble constraint payload written to ``metadata['regeneration_constraints']``."""
        import hashlib

        metadata = context.metadata or {}
        directive = metadata.get("revision_directive") or {}
        snapshot = directive.get("state_snapshot") or {}
        prior = metadata.get("narrative_text") or ""
        prior_hash = hashlib.sha256(prior.encode("utf-8")).hexdigest()[:16] if prior else ""
        # Thresholds used by response_revision_gate — mirrored here for the
        # constraint prompt so the LLM has explicit targets.
        from phionyx_core.pipeline.blocks.response_revision_gate import RevisionThresholds
        t = RevisionThresholds()
        return {
            "target_phi_min": t.phi_min,
            "target_confidence_min": t.confidence_regenerate,
            "reasons": directive.get("reasons", []),
            "prior_narrative_hash": prior_hash,
            "retry_seed": self._compute_retry_seed(context),
            "attempt": metadata.get("_regen_attempts", 0) or 1,
            "claim_refs": ["SF1:C1", "SF1:C14", "SF1:C15", "SF1:C18"],
            "state_snapshot": snapshot,
        }

    async def _maybe_regenerate(self, context: "BlockContext") -> bool:
        """
        Post-``response_revision_gate`` hook.

        Returns True if a retry was performed, False otherwise. Retry scope is
        strictly bounded to ``_REGEN_RETRY_BLOCKS`` — no state-mutating block
        is re-invoked, so per-turn state remains idempotent.
        """
        metadata = context.metadata or {}
        directive_payload = metadata.get("revision_directive") or {}
        directive = directive_payload.get("directive", "pass")
        attempts = int(metadata.get("_regen_attempts", 0))

        if directive != "regenerate":
            return False
        if attempts >= self._REGEN_MAX_ATTEMPTS:
            logger.info(
                "orchestrator.regenerate.retry: cap reached (attempts=%d), "
                "falling through to response_build fallback",
                attempts,
            )
            return False

        # Commit attempt counter + constraint payload BEFORE re-running blocks.
        metadata["_regen_attempts"] = attempts + 1
        metadata["regeneration_constraints"] = self._build_regeneration_constraints(context)
        context.metadata = metadata

        logger.info(
            "orchestrator.regenerate.retry: attempt=%d reasons=%s",
            metadata["_regen_attempts"],
            directive_payload.get("reasons"),
        )

        for rid in self._REGEN_RETRY_BLOCKS:
            block = self.blocks.get(rid)
            if block is None:
                # Block not registered in this runtime; skip silently. This is
                # common in unit-test setups where only a subset is wired.
                continue
            try:
                retry_result = await block.execute(context)
            except Exception as e:  # pragma: no cover - defensive
                logger.error("regenerate retry block %s failed: %s", rid, e, exc_info=True)
                continue
            # Shallow merge of retry result.data into metadata so subsequent
            # retry blocks see updated narrative / gate fields. Uses the same
            # filtering philosophy as the main loop (primitives + nested dicts
            # / lists only).
            if retry_result is not None and getattr(retry_result, "data", None):
                if isinstance(retry_result.data, dict):
                    for k, v in retry_result.data.items():
                        if isinstance(v, (dict, list, tuple, str, int, float, bool, type(None))):
                            metadata[k] = v
                    context.metadata = metadata

        return True

    async def execute_pipeline(
        self,
        context: BlockContext
    ) -> dict[str, Any]:
        """
        Execute the full 46-block pipeline (v3.8.0).

        Args:
            context: Initial pipeline context

        Returns:
            Final pipeline result
        """
        logger.debug(f"Executing pipeline with {len(self.block_order)} blocks (parallel={self.enable_parallel})")

        # Record pipeline start time for latency calculation
        pipeline_start_time = time.time()

        # OpenTelemetry: Create pipeline-level span
        pipeline_span = None
        tracer = None
        # Use global is_opentelemetry_enabled, not local import
        try:
            if OPENTELEMETRY_AVAILABLE and is_opentelemetry_enabled():
                from phionyx_core.telemetry.opentelemetry_config import get_or_create_tracer
                tracer = get_or_create_tracer()
                if tracer:
                    pipeline_span = tracer.start_as_current_span("phionyx.pipeline.execute")
                    pipeline_span.set_attribute("pipeline.version", "2.5.0")
                    pipeline_span.set_attribute("pipeline.parallel_enabled", self.enable_parallel)
                    pipeline_span.set_attribute("pipeline.execution_guard_enabled", self.execution_guard is not None)
        except Exception as e:
            logger.debug(f"OpenTelemetry pipeline span creation failed (non-critical): {e}")
            tracer = None

        # STATE PERSISTENCE: Load state before execution (if state_store available)
        if self.services.state_store and context.session_id:
            try:
                loaded_state = await self.services.state_store.load_state(context.session_id)
                if loaded_state:
                    # Set unified_state in context metadata
                    if context.metadata is None:
                        context.metadata = {}
                    context.metadata["unified_state"] = loaded_state
                    logger.debug(f"State loaded for session: {context.session_id}")
            except Exception as e:
                logger.warning(f"Failed to load state for session {context.session_id}: {e}")

        results = {}
        current_context = context
        skipped_blocks: set[str] = set()  # Track skipped blocks for propagation
        early_exit_triggered = False  # Track early exit status
        executed_blocks: set[str] = set()  # Track executed blocks for parallel execution

        # Initialize execution guard (CRITICAL: Infinite loop prevention)
        if self.execution_guard:
            self.execution_guard.reset(block_order_length=len(self.block_order))

        # Get intent for dynamic grouping (if available)
        intent = None
        intent_result = current_context.metadata.get("intent") if current_context.metadata else None
        if isinstance(intent_result, dict):
            intent = intent_result.get("intent")
        elif isinstance(intent_result, str):
            intent = intent_result

        # Execute blocks (with parallel execution support)
        block_index = 0
        previous_block_index = -1
        iterations_without_progress = 0

        while block_index < len(self.block_order):
            # CRITICAL: Check execution guard (multiple protection layers)
            if self.execution_guard:
                # Record iteration
                self.execution_guard.record_iteration("iteration")

                # Check if block_index is making progress
                if block_index == previous_block_index:
                    iterations_without_progress += 1
                else:
                    iterations_without_progress = 0
                    previous_block_index = block_index

                # Get current block_id for guard checks (if available)
                current_block_id_for_guard = self.block_order[block_index] if block_index < len(self.block_order) else "unknown"

                # Comprehensive safety check
                should_abort, reason = self.execution_guard.should_abort(
                    block_id=current_block_id_for_guard,
                    block_index=block_index,
                    block_order_length=len(self.block_order),
                    iterations_without_progress=iterations_without_progress
                )

                if should_abort:
                    logger.error("CRITICAL: Execution guard triggered - ABORTING pipeline execution!")
                    logger.error(f"Reason: {reason}")
                    stats = self.execution_guard.get_statistics()
                    logger.error(f"Execution statistics: {stats}")
                    # Add guard statistics to results
                    results["_execution_guard"] = {
                        "status": "aborted",
                        "reason": reason,
                        "statistics": stats
                    }
                    break
            # Try to identify parallel groups (dynamic grouping first, then static)
            parallel_groups = []
            if self.enable_parallel:
                # Try dynamic grouping based on intent
                if intent:
                    parallel_groups = self.dynamic_grouping.get_groups_for_intent(
                        intent=intent,
                        block_order=self.block_order,
                        executed_blocks=executed_blocks
                    )

                # Fallback to static parallel groups if dynamic grouping didn't find any
                if not parallel_groups:
                    parallel_groups = self.parallel_executor.identify_parallel_groups(
                        block_order=self.block_order,
                        executed_blocks=executed_blocks,
                        context=current_context
                    )

                # Execute parallel groups if found
                # CRITICAL: Process only ONE parallel group per iteration to preserve sequential order
                # After executing a parallel group, we need to check sequential blocks before forming new parallel groups
                if parallel_groups:
                    # Take only the first parallel group (process one group at a time)
                    group = parallel_groups[0]

                    # Execute parallel group
                    group_results = await self.parallel_executor.execute_parallel_group(
                        group=group,
                        blocks=self.blocks,
                        context=current_context
                    )

                    # Merge results
                    results.update(group_results)
                    current_context = self.parallel_executor.merge_results(
                        group_results,
                        current_context
                    )

                    # CRITICAL: Write physics block results to context (same as sequential path)
                    # This ensures entropy_computation, phi_computation, and emotion_estimation results are properly propagated
                    for block_id, result in group_results.items():
                        if not result.is_success() or not result.data:
                            continue

                        # CRITICAL: Ensure result.data is a dictionary, not a Mock object
                        if not isinstance(result.data, dict):
                            continue

                        # CRITICAL: Ensure metadata is a dictionary
                        if current_context.metadata is None:
                            current_context.metadata = {}

                        # Handle entropy_computation
                        if block_id == "entropy_computation" and "entropy" in result.data:
                            entropy_value = result.data.get("entropy")
                            if entropy_value is not None:
                                current_context.current_entropy = float(entropy_value)
                                current_context.metadata["current_entropy"] = float(entropy_value)
                                logger.debug(f"[Parallel] Updated current_entropy: {entropy_value}")

                            # Update physics_state with entropy
                            # CRITICAL: Ensure physics_state is a dictionary, not a Mock object
                            # Get current physics_state safely
                            current_physics_state = current_context.metadata.get("physics_state")
                            if not isinstance(current_physics_state, dict):
                                current_physics_state = {}
                                current_context.metadata["physics_state"] = current_physics_state

                            # Update entropy value
                            current_physics_state["entropy"] = float(entropy_value)

                        # Handle phi_computation
                        if block_id == "phi_computation" and "phi" in result.data:
                            phi_value = result.data.get("phi")
                            if phi_value is not None:
                                current_context.previous_phi = float(phi_value)
                                current_context.metadata["previous_phi"] = float(phi_value)
                                logger.debug(f"[Parallel] Updated previous_phi: {phi_value}")

                        # Handle emotion_estimation
                        if block_id == "emotion_estimation":
                            valence = result.data.get("valence")
                            arousal = result.data.get("arousal")
                            if valence is not None or arousal is not None:
                                # CRITICAL: Ensure physics_state is a dictionary, not a Mock object
                                # Get current physics_state safely
                                current_physics_state = current_context.metadata.get("physics_state")
                                if not isinstance(current_physics_state, dict):
                                    current_physics_state = {}
                                    current_context.metadata["physics_state"] = current_physics_state

                                if valence is not None:
                                    current_physics_state["valence"] = float(valence)
                                    logger.debug(f"[Parallel] Updated physics_state.valence: {valence}")
                                if arousal is not None:
                                    current_physics_state["arousal"] = float(arousal)
                                    logger.debug(f"[Parallel] Updated physics_state.arousal: {arousal}")

                                # CRITICAL: Also update unified_state (EchoState2) if available
                                unified_state = current_context.metadata.get("unified_state")
                                if unified_state and not isinstance(unified_state, type):
                                    try:
                                        if valence is not None and hasattr(unified_state, 'V'):
                                            unified_state.V = float(valence)
                                            logger.debug(f"[Parallel] Updated unified_state.V (EchoState2): {valence}")
                                        if arousal is not None and hasattr(unified_state, 'A'):
                                            unified_state.A = float(arousal)
                                            logger.debug(f"[Parallel] Updated unified_state.A (EchoState2): {arousal}")
                                    except (AttributeError, ValueError, TypeError) as e:
                                        logger.debug(f"[Parallel] Could not update unified_state V/A: {e}")

                    # Mark blocks as executed
                    executed_blocks.update(group.block_ids)

                    # Check for early exit
                    for block_id, result in group_results.items():
                        if result.data and (result.data.get("early_exit", False) or result.data.get("early_exit_triggered", False)):
                            early_exit_triggered = True
                            logger.debug(f"Early exit triggered by block: {block_id}")

                    # CRITICAL FIX: Update block_index correctly after parallel group execution
                    # We should NOT jump ahead - instead, we need to ensure block_index stays at the correct position
                    # for sequential execution. Parallel groups can execute blocks out of order, but we must
                    # still process sequential blocks in canonical order.
                    #
                    # Strategy: Don't update block_index based on parallel group execution.
                    # Let sequential execution continue from current block_index, and it will skip already-executed blocks.
                    # This ensures we don't miss any blocks that should execute between current position and parallel-executed blocks.
                    logger.debug(f"Parallel group executed {len(group.block_ids)} blocks: {group.block_ids}. block_index remains at {block_index} for sequential check")

                    # Continue to sequential execution - it will skip already-executed blocks via the check at line 304

            # Execute next block sequentially (if not already executed in parallel)
            if block_index >= len(self.block_order):
                break

            block_id = self.block_order[block_index]

            # Skip if already executed in parallel
            if block_id in executed_blocks:
                block_index += 1
                logger.debug(f"Block {block_id} already executed in parallel, skipping. block_index={block_index}")
                continue
            if block_id not in self.blocks:
                always_on_blocks = {"response_build", "phi_computation", "entropy_computation"}
                if block_id in always_on_blocks:
                    logger.error(f"CRITICAL: Always-on block {block_id} not registered in orchestrator.blocks (keys: {list(self.blocks.keys())[:5]}...)")
                logger.warning(f"Block {block_id} not registered, skipping. block_index={block_index}")
                skipped_blocks.add(block_id)
                block_index += 1  # CRITICAL: Increment index when skipping unregistered blocks
                continue

            block = self.blocks[block_id]

            # Check for early exit propagation
            if early_exit_triggered:
                # Skip all remaining blocks except always-on blocks
                always_on_blocks = {"response_build", "phi_computation", "entropy_computation"}
                if block_id not in always_on_blocks:
                    skip_reason = "Early exit triggered"
                else:
                    skip_reason = None
            else:
                skip_reason = None

            # Check if block should be skipped (either by should_skip() or dependency)
            # CRITICAL: Always-on blocks should not be skipped due to dependencies
            always_on_blocks = {"response_build", "phi_computation", "entropy_computation"}
            is_always_on = block_id in always_on_blocks

            # Intent-based skip check (if not already set)
            if not skip_reason and intent:
                intent_skip_blocks = self.dynamic_grouping.get_blocks_to_skip_for_intent(intent)
                if block_id in intent_skip_blocks and not is_always_on:
                    skip_reason = f"Intent-based skip: {intent}"

            if not skip_reason:
                skip_reason = block.should_skip(current_context)

            # Check if any dependency was skipped
            # Always-on blocks should run even if dependencies are skipped
            if not skip_reason and not is_always_on:
                block_deps = self.dependency_validator.get_block_dependencies(block_id)
                skipped_deps = [dep for dep in block_deps if dep in skipped_blocks]
                if skipped_deps:
                    skip_reason = f"Dependency blocks skipped: {skipped_deps}"

            if skip_reason:
                always_on_blocks = {"response_build", "phi_computation", "entropy_computation"}
                if block_id in always_on_blocks:
                    logger.warning(f"CRITICAL: Always-on block {block_id} is being skipped: {skip_reason}. This should not happen!")
                if self.telemetry_collector:
                    self.telemetry_collector.start_block(block_id, block_id)
                    self.telemetry_collector.end_block(block_id, status="skipped")
                results[block_id] = BlockResult(
                    block_id=block_id,
                    status="skipped",
                    skip_reason=skip_reason
                )
                skipped_blocks.add(block_id)
                logger.info(f"Block {block_id} skipped: {skip_reason}. block_index={block_index}")
                block_index += 1  # CRITICAL: Increment index when skipping blocks
                continue

            # Execute block
            try:
                if self.telemetry_collector:
                    self.telemetry_collector.start_block(block_id, block_id)

                if block_id == "response_build":
                    logger.debug("[ORCHESTRATOR] Executing response_build block")

                # CRITICAL: Record block execution in guard BEFORE execution
                if self.execution_guard:
                    # Pre-check: Will this block execution violate limits?
                    pre_check_safe, pre_check_reason = self.execution_guard.check_block_execution_limit(block_id)
                    if not pre_check_safe:
                        logger.error(f"CRITICAL: Block '{block_id}' execution would violate guard limits. {pre_check_reason}")
                        # Revert the count increment
                        if block_id in self.execution_guard.block_execution_count:
                            self.execution_guard.block_execution_count[block_id] -= 1
                        results[block_id] = BlockResult(
                            block_id=block_id,
                            status="error",
                            error=Exception(f"Execution guard: {pre_check_reason}")
                        )
                        block_index += 1
                        continue

                # OpenTelemetry: Create block-level span
                block_span = None
                block_start_time = None
                # Use global is_opentelemetry_enabled, not local import
                if OPENTELEMETRY_AVAILABLE and is_opentelemetry_enabled() and tracer:
                    try:
                        block_start_time = time.time()
                        block_span = tracer.start_as_current_span(f"block.{block_id}")
                        block_span.set_attribute("block.name", block_id)
                        # Get block category (simplified - can be enhanced later)
                        # Block categories: core, middleware, physics, safety, etc.
                        block_category = "core"  # Default
                        if "middleware" in block_id or block_id in ["request_processor", "engine_initializer", "response_serializer"]:
                            block_category = "middleware"
                        elif block_id in ["entropy_computation", "phi_computation", "emotion_estimation", "state_update_physics"]:
                            block_category = "physics"
                        elif "safety" in block_id or "gate" in block_id or "ethics" in block_id:
                            block_category = "safety"
                        block_span.set_attribute("block.category", block_category)
                        if intent:
                            block_span.set_attribute("block.intent", str(intent))
                    except Exception as e:
                        logger.debug(f"OpenTelemetry block span creation failed (non-critical): {e}")

                result = await block.execute(current_context)
                results[block_id] = result

                # OpenTelemetry: Update block span with results
                if block_span:
                    try:
                        if block_start_time:
                            duration_ms = (time.time() - block_start_time) * 1000
                            duration_seconds = duration_ms / 1000.0
                            block_span.set_attribute("block.duration_ms", duration_ms)

                            # Record latency metric
                            try:
                                from phionyx_core.telemetry.otel_metrics import record_latency
                                record_latency(duration_seconds, block_id=block_id)
                            except Exception:
                                pass

                        block_span.set_attribute("block.success", result.is_success())
                        if result.data:
                            if "entropy" in result.data:
                                entropy_value = float(result.data["entropy"])
                                block_span.set_attribute("block.entropy", entropy_value)
                                # Record entropy metric
                                try:
                                    from phionyx_core.telemetry.otel_metrics import record_entropy
                                    record_entropy(entropy_value, block_id=block_id)
                                except Exception:
                                    pass
                            if "phi" in result.data:
                                block_span.set_attribute("block.phi", float(result.data["phi"]))
                        if result.is_error() and result.error:
                            block_span.set_status(Status(StatusCode.ERROR, str(result.error)))
                            block_span.record_exception(result.error)
                        elif result.is_skipped():
                            block_span.set_attribute("block.skipped", True)
                            if result.skip_reason:
                                block_span.set_attribute("block.skip_reason", result.skip_reason)
                        block_span.end()
                    except Exception as e:
                        logger.debug(f"OpenTelemetry block span update failed (non-critical): {e}")

                # CRITICAL: Record successful block execution in guard AFTER execution
                if self.execution_guard:
                    self.execution_guard.check_circular_sequence(block_id)  # Already recorded in pre-check, but verify pattern

                if block_id == "response_build":
                    logger.debug(f"[ORCHESTRATOR] response_build executed: status={result.status}, has_data={result.data is not None}")

                # Update context with block result data
                if result.data:
                    if current_context.metadata is None:
                        current_context.metadata = {}

                    if isinstance(result.data, dict):
                        # Filter result.data: only merge real values
                        filtered_data = {}
                        for k, v in result.data.items():
                            if k == "frame":
                                if isinstance(v, dict):
                                    filtered_data[k] = v
                                else:
                                    try:
                                        filtered_data[k] = {"narrative_text": getattr(v, 'narrative_text', None)}
                                    except Exception:
                                        filtered_data[k] = {}
                                continue
                            # Skip non-serializable placeholder objects
                            if not isinstance(v, (dict, list, tuple, str, int, float, bool, type(None))):
                                logger.debug(f"Skipping non-serializable object in result.data['{k}'] (type: {type(v).__name__})")
                                continue
                            if k == "physics_state" and isinstance(v, dict):
                                filtered_physics_state = {pk: pv for pk, pv in v.items()
                                                         if isinstance(pv, (str, int, float, bool, type(None)))}
                                filtered_data[k] = filtered_physics_state
                            else:
                                filtered_data[k] = v
                        current_context.metadata.update(filtered_data)
                    else:
                        # If result.data is not a dict, skip it
                        logger.warning(f"result.data is not a dictionary (type: {type(result.data)}), skipping metadata update")

                    # Update physics values in context (if computed by physics blocks)
                    if block_id == "entropy_computation" and "entropy" in result.data:
                        entropy_value = result.data.get("entropy")
                        if entropy_value is not None:
                            current_context.current_entropy = entropy_value
                            current_context.metadata["current_entropy"] = entropy_value
                            logger.debug(f"Updated current_entropy: {entropy_value}")

                            # Update physics_state with entropy
                            # CRITICAL: Ensure physics_state is a dictionary, not a Mock object
                            current_physics_state = current_context.metadata.get("physics_state")
                            if not isinstance(current_physics_state, dict):
                                current_physics_state = {}
                                current_context.metadata["physics_state"] = current_physics_state
                            current_physics_state["entropy"] = float(entropy_value)

                    if block_id == "emotion_estimation" and ("valence" in result.data or "arousal" in result.data):
                        # CRITICAL: Write emotion_estimation results to physics_state
                        # This ensures phi_computation can use valence/arousal from emotion_estimation
                        # CRITICAL: Ensure physics_state is a dictionary, not a Mock object
                        current_physics_state = current_context.metadata.get("physics_state")
                        if not isinstance(current_physics_state, dict):
                            current_physics_state = {}
                            current_context.metadata["physics_state"] = current_physics_state

                        valence = result.data.get("valence")
                        arousal = result.data.get("arousal")
                        if valence is not None:
                            current_physics_state["valence"] = float(valence)
                            logger.debug(f"Updated physics_state.valence: {valence}")
                        if arousal is not None:
                            current_physics_state["arousal"] = float(arousal)
                            logger.debug(f"Updated physics_state.arousal: {arousal}")

                        # CRITICAL: Also update unified_state (EchoState2) if available
                        # This ensures EchoState2.V and EchoState2.A are updated with emotion_estimation results
                        unified_state = current_context.metadata.get("unified_state")
                        if unified_state:
                            try:
                                if valence is not None and hasattr(unified_state, 'V'):
                                    unified_state.V = float(valence)
                                    logger.debug(f"Updated unified_state.V (EchoState2): {valence}")
                                if arousal is not None and hasattr(unified_state, 'A'):
                                    unified_state.A = float(arousal)
                                    logger.debug(f"Updated unified_state.A (EchoState2): {arousal}")
                            except (AttributeError, ValueError, TypeError) as e:
                                logger.debug(f"Could not update unified_state V/A: {e}")

                    if block_id == "phi_computation" and "phi" in result.data:
                        phi_value = result.data.get("phi")
                        if phi_value is not None:
                            current_context.previous_phi = phi_value
                            current_context.metadata["previous_phi"] = phi_value
                            logger.debug(f"Updated previous_phi: {phi_value}")

                    # Coherence enforcement: apply redaction if state leak detected
                    if block_id == "coherence_qa" and isinstance(result.data, dict):
                        qa = result.data.get("qa_result")
                        if qa and isinstance(qa, dict) and qa.get("leak_detected"):
                            redacted = qa.get("redacted_text")
                            if redacted:
                                current_context.metadata["narrative_text"] = redacted
                                logger.info(
                                    "Coherence QA: leak detected, applied redaction "
                                    f"(score={qa.get('coherence_score', 'N/A')}, "
                                    f"violations={qa.get('violation_count', 0)})"
                                )

                    # Update amplitude and integrity if available
                    if "amplitude" in result.data:
                        current_context.current_amplitude = result.data.get("amplitude")
                        current_context.metadata["current_amplitude"] = result.data.get("amplitude")

                    if "integrity" in result.data:
                        current_context.current_integrity = result.data.get("integrity")
                        current_context.metadata["current_integrity"] = result.data.get("integrity")

                    # Check for early exit trigger
                    if result.data.get("early_exit", False) or result.data.get("early_exit_triggered", False):
                        early_exit_triggered = True
                        logger.debug(f"Early exit triggered by block: {block_id}")

                    # Check for short-circuit optimization
                    short_circuit_condition = self.early_exit_optimizer.should_short_circuit(
                        block_id=block_id,
                        context=current_context,
                        result=result
                    )

                    if short_circuit_condition:
                        blocks_to_skip = self.early_exit_optimizer.get_blocks_to_skip(
                            condition=short_circuit_condition,
                            current_block_id=block_id
                        )
                        skipped_blocks.update(blocks_to_skip)
                        self.early_exit_optimizer.metrics["blocks_skipped"] += len(blocks_to_skip)
                        logger.debug(f"Short-circuit: Skipping {len(blocks_to_skip)} blocks: {blocks_to_skip}")

                if self.telemetry_collector:
                    self.telemetry_collector.end_block(
                        block_id,
                        status=result.status,
                        events=[{"type": "result", "data": result.data}] if result.data else None
                    )

                # Create checkpoint after successful block execution
                if result.is_success():
                    self.rollback_manager.create_checkpoint(block_id, current_context)

                # Handle block errors - but continue pipeline for always-on blocks
                if result.is_error():
                    logger.error(f"Block {block_id} failed, attempting rollback")

                    # CRITICAL: Always-on blocks must still execute even if previous blocks fail
                    # Don't break the pipeline - continue to allow always-on blocks (phi_computation, entropy_computation) to run
                    always_on_blocks = {"response_build", "phi_computation", "entropy_computation"}
                    if block_id in always_on_blocks:
                        logger.warning(f"CRITICAL: Always-on block {block_id} failed, but pipeline will continue to ensure other always-on blocks execute")
                        block_index += 1
                        continue  # Continue to next block, don't break
                    else:
                        # Attempt rollback (if enabled)
                        rollback_success = self.rollback_manager.rollback_to_checkpoint(
                            block_id, current_context
                        )

                        if rollback_success:
                            logger.info(f"Rollback successful after block {block_id} failure")
                        else:
                            logger.warning(f"Rollback failed or not available after block {block_id} failure")

                        # Continue to next block (don't break) to allow always-on blocks to execute
                        block_index += 1
                        continue

            except Exception as e:
                logger.error(f"Error executing block {block_id}: {e}", exc_info=True)
                results[block_id] = BlockResult(
                    block_id=block_id,
                    status="error",
                    error=e
                )
                if self.telemetry_collector:
                    self.telemetry_collector.end_block(block_id, status="error")

                # CRITICAL: Always-on blocks must still execute even if previous blocks fail
                # Don't break the pipeline - continue to allow always-on blocks (phi_computation, entropy_computation) to run
                always_on_blocks = {"response_build", "phi_computation", "entropy_computation"}
                if block_id in always_on_blocks:
                    logger.warning(f"CRITICAL: Always-on block {block_id} failed, but pipeline will continue to ensure other always-on blocks execute")
                    block_index += 1
                    continue  # Continue to next block, don't break
                else:
                    # For non-always-on blocks, attempt rollback and continue (don't break)
                    logger.warning(f"Block {block_id} failed, attempting rollback and continuing")

                    # Attempt rollback (if enabled)
                    if self.rollback_manager:
                        rollback_success = self.rollback_manager.rollback_to_checkpoint(
                            block_id, current_context
                        )
                        if rollback_success:
                            logger.info(f"Rollback successful after block {block_id} failure")
                        else:
                            logger.warning(f"Rollback failed or not available after block {block_id} failure")

                    # Continue to next block (don't break) to allow always-on blocks to execute
                    block_index += 1
                    continue

            # v3.8.0 + Plan v3: State-driven narrative re-entry hook.
            # When response_revision_gate emits REGENERATE, rewind-lite: re-run
            # only response-shape + measurement blocks with fresh state-informed
            # constraints. State-mutating blocks are NOT re-run (scope bound).
            if block_id == "response_revision_gate":
                try:
                    await self._maybe_regenerate(current_context)
                except Exception as retry_exc:  # pragma: no cover - defensive
                    logger.error(
                        "regenerate retry hook failed (pipeline continues): %s",
                        retry_exc,
                        exc_info=True,
                    )

            # CRITICAL: Always increment block_index after block execution (success or skip)
            # This prevents infinite loop where the same block executes repeatedly
            block_index += 1
            logger.debug(f"Block {block_id} execution complete. Incremented block_index to {block_index}")

        # Final execution guard statistics
        guard_stats = None
        if self.execution_guard:
            guard_stats = self.execution_guard.get_statistics()
            if not self.execution_guard.is_safe:
                logger.warning(f"Pipeline execution completed but execution guard detected violations: {self.execution_guard.violations}")
            else:
                logger.debug(f"Pipeline execution completed safely. Guard statistics: {guard_stats}")

        # STATE PERSISTENCE: Save state after execution (if state_store available)
        if self.services.state_store and current_context.session_id:
            try:
                unified_state = current_context.metadata.get("unified_state") if current_context.metadata else None
                if unified_state:
                    # Import EchoState2 to check type
                    from phionyx_core.state.echo_state_2 import EchoState2
                    if isinstance(unified_state, EchoState2):
                        await self.services.state_store.save_state(current_context.session_id, unified_state)
                        logger.debug(f"State saved for session: {current_context.session_id}")
                    else:
                        logger.debug(f"unified_state is not EchoState2 instance (type: {type(unified_state)}), skipping save")
                else:
                    logger.debug(f"No unified_state found in context metadata for session: {current_context.session_id}")
            except Exception as e:
                logger.warning(f"Failed to save state for session {current_context.session_id}: {e}", exc_info=True)

        # Calculate pipeline latency
        pipeline_latency = time.time() - pipeline_start_time

        # OpenTelemetry: Update pipeline span with final results
        if pipeline_span:
            try:
                pipeline_span.set_attribute("pipeline.blocks_executed", len(results))
                pipeline_span.set_attribute("pipeline.blocks_skipped", len(skipped_blocks))
                pipeline_span.set_attribute("pipeline.latency_seconds", pipeline_latency)
                if current_context.current_entropy is not None:
                    pipeline_span.set_attribute("pipeline.final_entropy", float(current_context.current_entropy))
                if current_context.previous_phi is not None:
                    pipeline_span.set_attribute("pipeline.final_phi", float(current_context.previous_phi))
                pipeline_span.set_status(Status(StatusCode.OK))
                pipeline_span.end()
            except Exception as e:
                logger.debug(f"OpenTelemetry pipeline span update failed (non-critical): {e}")

        # Record pipeline latency metric
        try:
            from phionyx_core.telemetry.otel_metrics import record_latency
            record_latency(pipeline_latency, block_id=None)  # None = pipeline-level
        except Exception:
            pass

        return {
            "results": results,
            "final_context": current_context,
            "skipped_blocks": list(skipped_blocks),
            "execution_guard": guard_stats  # Include guard statistics in results
        }

    async def run(
        self,
        user_input: str,
        card_type: str = "shadow",
        card_title: str = "",
        scene_context: str = "",
        card_result: str = "neutral",
        scenario_id: str | None = None,
        scenario_step_id: str | None = None,
        session_id: str | None = None,
        participant: Any | None = None,  # Participant abstraction
        mode: str | None = None,  # Runtime mode (e.g., "toygar_core", "story", "game_scenario")
        strategy: str | None = None,  # Runtime strategy (e.g., "normal", "stabilize", "comfort")
        envelope_message_id: str | None = None,  # TurnEnvelope message_id for transcript tracking
        envelope_turn_id: int | None = None,  # TurnEnvelope turn_id for transcript tracking
        envelope_user_text_sha256: str | None = None,  # TurnEnvelope user_text_sha256 for integrity
        capabilities: Any | None = None,  # RunCapabilities
        capability_deriver: Any | None = None,  # CapabilityDeriverProtocol
        current_amplitude: float = 5.0,
        current_entropy: float = 0.5,
        current_integrity: float = 100.0,
        previous_phi: float | None = None,
        **kwargs
    ) -> dict[str, Any]:
        """
        Main entry point for pipeline execution.

        This method matches the signature of UnifiedEchoEngineRefactored.process_decision
        to enable seamless integration.

        Args:
            user_input: User input text
            card_type: Card type
            card_title: Card title
            scene_context: Scene context
            card_result: Card result
            scenario_id: Scenario ID
            scenario_step_id: Scenario step ID
            session_id: Session ID
            participant: Participant abstraction
            mode: Runtime mode
            strategy: Runtime strategy
            envelope_message_id: TurnEnvelope message_id for transcript tracking
            envelope_turn_id: TurnEnvelope turn_id for transcript tracking
            envelope_user_text_sha256: TurnEnvelope user_text_sha256 for integrity
            capabilities: RunCapabilities flags
            capability_deriver: CapabilityDeriverProtocol
            current_amplitude: Current amplitude
            current_entropy: Current entropy
            current_integrity: Current integrity
            previous_phi: Previous phi value
            **kwargs: Additional parameters

        Returns:
            Pipeline execution result
        """
        # Create initial context
        context = BlockContext(
            user_input=user_input,
            card_type=card_type,
            card_title=card_title,
            scene_context=scene_context,
            card_result=card_result,
            scenario_id=scenario_id,
            scenario_step_id=scenario_step_id,
            session_id=session_id,
            participant=participant,
            mode=mode,
            strategy=strategy,
            envelope_message_id=envelope_message_id,
            envelope_turn_id=envelope_turn_id,
            envelope_user_text_sha256=envelope_user_text_sha256,
            capabilities=capabilities,
            capability_deriver=capability_deriver,
            current_amplitude=current_amplitude,
            current_entropy=current_entropy,
            current_integrity=current_integrity,
            previous_phi=previous_phi,
            metadata=kwargs
        )

        # Execute pipeline
        return await self.execute_pipeline(context)

