"""
Process Decision Use Case
=========================

Business logic for processing a decision request.
Extracted from API route handler to core layer.
"""

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ProcessDecisionInput:
    """Input for process decision use case."""
    user_input: str
    character_id: str
    character_archetype: str
    profile_name: str
    conversation_id: str | None = None
    actor_ref: str | None = None
    participant_type: str | None = None
    mode: str | None = None
    strategy: str | None = None
    turn_envelope: dict[str, Any] | None = None
    request_id: str | None = None
    debug: bool = False


@dataclass
class ProcessDecisionOutput:
    """Output from process decision use case."""
    result: dict[str, Any]
    conversation_id: str
    participant: Any | None = None
    envelope: Any | None = None
    delivery_ack: Any | None = None


class ProcessDecisionUseCase:
    """
    Use case for processing a decision request.

    This encapsulates the business logic for:
    - TurnEnvelope validation and idempotency
    - Turn lock management
    - Participant creation
    - Engine invocation
    - Result extraction
    """

    def __init__(
        self,
        engine: Any,  # UnifiedEchoEngineRefactored
        envelope_store: Any,  # TurnEnvelopeStore
        turn_lock_guard: Any,  # TurnLockGuard
        capability_deriver: Any | None = None
    ):
        """
        Initialize use case.

        Args:
            engine: Engine instance
            envelope_store: TurnEnvelope store for idempotency
            turn_lock_guard: Turn lock guard for concurrency control
            capability_deriver: Optional capability deriver
        """
        self.engine = engine
        self.envelope_store = envelope_store
        self.turn_lock_guard = turn_lock_guard
        self.capability_deriver = capability_deriver

    async def execute(self, input_data: ProcessDecisionInput) -> ProcessDecisionOutput:
        """
        Execute the process decision use case.

        Args:
            input_data: Input data for the use case

        Returns:
            ProcessDecisionOutput with result and metadata
        """
        # Import here to avoid circular dependencies
        from ..contracts.envelopes.turn_envelope import DeliveryAck, TurnEnvelope
        from ..contracts.participants import ParticipantRef, ParticipantType

        # Step 1: Validate and process TurnEnvelope
        envelope: TurnEnvelope | None = None
        delivery_ack: DeliveryAck | None = None
        _conversation_id_from_envelope: str | None = None
        _turn_id_from_envelope: int | None = None
        _message_id_from_envelope: str | None = None
        turn_lock_result = None

        if input_data.turn_envelope:
            try:
                # Validate TurnEnvelope
                envelope = TurnEnvelope(**input_data.turn_envelope)

                # Validate conversation_id
                if not envelope.conversation_id:
                    raise ValueError("TurnEnvelope: conversation_id is required")

                # Verify hash
                if not envelope.verify_hash():
                    logger.error(
                        f"[TURN_ENVELOPE] Hash mismatch: conversation_id={envelope.conversation_id}, "
                        f"turn_id={envelope.turn_id}, message_id={envelope.message_id}"
                    )
                    if input_data.debug:
                        raise ValueError(
                            f"TurnEnvelope hash mismatch: expected {envelope.user_text_sha256}, "
                            f"computed {envelope.compute_sha256(envelope.user_text)}"
                        )
                    else:
                        delivery_ack = DeliveryAck(
                            conversation_id=envelope.conversation_id,
                            turn_id=envelope.turn_id,
                            message_id=envelope.message_id,
                            received_user_text_sha256=envelope.compute_sha256(envelope.user_text),
                            delivery_status="mismatch",
                            delivery_error="Hash mismatch - user_text modified in transit"
                        )
                else:
                    # Hash matches - check idempotency
                    cached_response = self.envelope_store.get_cached_response(envelope.message_id)
                    if cached_response:
                        logger.info(
                            f"[TURN_ENVELOPE] Idempotent replay: conversation_id={envelope.conversation_id}, "
                            f"turn_id={envelope.turn_id}, message_id={envelope.message_id}"
                        )
                        # Return cached response
                        return ProcessDecisionOutput(
                            result=cached_response,
                            conversation_id=envelope.conversation_id,
                            envelope=envelope,
                            delivery_ack=DeliveryAck(
                                conversation_id=envelope.conversation_id,
                                turn_id=envelope.turn_id,
                                message_id=envelope.message_id,
                                received_user_text_sha256=envelope.user_text_sha256,
                                delivery_status="replayed",
                                delivery_error=None
                            )
                        )

                    # Validate turn_id is monotonic
                    is_valid, error_msg = self.envelope_store.validate_turn_id(
                        envelope.conversation_id,
                        envelope.turn_id
                    )
                    if not is_valid:
                        logger.warning(
                            f"[TURN_ENVELOPE] Turn ID validation failed: conversation_id={envelope.conversation_id}, "
                            f"turn_id={envelope.turn_id}, error={error_msg}"
                        )
                        if input_data.debug:
                            raise ValueError(f"Turn ID validation failed: {error_msg}")
                        else:
                            delivery_ack = DeliveryAck(
                                conversation_id=envelope.conversation_id,
                                turn_id=envelope.turn_id,
                                message_id=envelope.message_id,
                                received_user_text_sha256=envelope.user_text_sha256,
                                delivery_status="rejected",
                                delivery_error=f"Turn ID validation failed: {error_msg}"
                            )
                    else:
                        # Turn ID is valid - try to acquire turn lock
                        _conversation_id_from_envelope = envelope.conversation_id
                        _turn_id_from_envelope = envelope.turn_id
                        _message_id_from_envelope = envelope.message_id

                        turn_lock_result = self.turn_lock_guard.try_acquire(
                            conversation_id=envelope.conversation_id,
                            turn_id=envelope.turn_id,
                            message_id=envelope.message_id
                        )

                        if turn_lock_result.is_idempotent:
                            # Idempotent replay - return cached response
                            logger.info(
                                f"[TURN_LOCK] Idempotent replay: conversation_id={envelope.conversation_id}, "
                                f"turn_id={envelope.turn_id}, message_id={envelope.message_id}"
                            )
                            cached_response = turn_lock_result.cached_response
                            if cached_response:
                                return ProcessDecisionOutput(
                                    result=cached_response,
                                    conversation_id=envelope.conversation_id,
                                    envelope=envelope,
                                    delivery_ack=DeliveryAck(
                                        conversation_id=envelope.conversation_id,
                                        turn_id=envelope.turn_id,
                                        message_id=envelope.message_id,
                                        received_user_text_sha256=envelope.user_text_sha256,
                                        delivery_status="replayed",
                                        delivery_error=None
                                    )
                                )

                        elif turn_lock_result.is_conflict:
                            # Conflict - different message_id for same turn
                            raise ValueError(
                                f"Turn {envelope.turn_id} is already in progress with a different message. "
                                f"Existing message_id: {turn_lock_result.conflict_message_id}, "
                                f"New message_id: {envelope.message_id}"
                            )
            except Exception as e:
                logger.error(f"[TURN_ENVELOPE] Validation failed: {e}", exc_info=True)
                if input_data.debug:
                    raise
                # Prod mode: continue without envelope

        # Step 2: Generate or use conversation_id
        import uuid
        conversation_id = input_data.conversation_id
        if envelope and envelope.conversation_id:
            conversation_id = envelope.conversation_id
        elif not conversation_id:
            conversation_id = input_data.request_id or f"conv_{uuid.uuid4().hex[:16]}"
            logger.debug(f"[CONVERSATION_ID] Generated conversation_id={conversation_id}")

        # Step 3: Use envelope.user_text if envelope exists (source of truth)
        user_input_for_core = envelope.user_text if envelope else input_data.user_input

        # Step 4: Create participant
        participant = None
        if input_data.actor_ref:
            participant_type_str = input_data.participant_type or "human"
            try:
                participant_type = ParticipantType(participant_type_str)
            except ValueError:
                participant_type = ParticipantType.HUMAN
            participant = ParticipantRef(
                id=input_data.actor_ref,
                type=participant_type
            )
            # Handle both Enum and string types for participant.type
            participant_type_str = participant.type.value if hasattr(participant.type, 'value') else str(participant.type)
            logger.debug(f"[PARTICIPANT] Using participant: id={participant.id}, type={participant_type_str}")

        # Step 5: Call engine.process_decision
        capability_deriver = self.capability_deriver or getattr(self.engine, '_capability_deriver', None)
        result = await self.engine.process_decision(
            user_input=user_input_for_core,
            card_type=input_data.character_archetype,
            card_title="",
            scene_context="",
            card_result="neutral",
            session_id=conversation_id,
            participant=participant,
            mode=input_data.mode,
            strategy=input_data.strategy,
            envelope_message_id=envelope.message_id if envelope else None,
            envelope_turn_id=envelope.turn_id if envelope else None,
            envelope_user_text_sha256=envelope.user_text_sha256 if envelope else None,
            capability_deriver=capability_deriver
        )

        # Step 6: Validate result
        if result is None:
            raise ValueError("Engine process_decision returned None")
        if not isinstance(result, dict):
            raise ValueError(f"Engine process_decision returned unexpected type: {type(result)}")

        return ProcessDecisionOutput(
            result=result,
            conversation_id=conversation_id,
            participant=participant,
            envelope=envelope,
            delivery_ack=delivery_ack
        )

