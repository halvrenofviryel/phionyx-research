"""
Agent-to-Agent Bridge Models - Message Envelope and Handshake
==============================================================

Models for AI↔AI communication protocol bridge (Paket A).
Enhanced with envelope hardening (Paket E): message_id, turn_id, timestamp, TTL, nonce.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, field_validator

# Use core ParticipantRef to maintain layer isolation
from phionyx_core.contracts.participants import ParticipantRef, ParticipantType


class CognitiveMetrics(BaseModel):
    """
    Structured cognitive state metrics captured at message creation time.

    Patent SF2-14: Envelope metadata includes typed cognitive state metrics
    used for cognitive integrity checking when present.
    """
    phi: float = Field(0.0, ge=0.0, le=1.0, description="Integrated information (0-1)")
    entropy: float = Field(0.0, ge=0.0, le=1.0, description="System entropy / chaos level (0-1)")
    coherence: float = Field(0.0, ge=0.0, le=1.0, description="Coherence score (0-1)")
    trust: float | None = Field(None, ge=0.0, le=1.0, description="Trust score (0-1, optional)")
    w_final: float | None = Field(None, ge=0.0, le=1.0, description="Confidence fusion weight (0-1, optional)")


class AgentMessageEnvelope(BaseModel):
    """
    Message envelope for AI↔AI communication.

    Provides protocol-agnostic message structure for agent-to-agent interactions.

    Enhanced (Paket E) with:
    - message_id: UUID for deduplication
    - turn_id: Monotonic turn ID per session
    - timestamp_utc: ISO8601 timestamp
    - ttl_seconds: Time-to-live in seconds
    - nonce: Random nonce for replay protection
    - cognitive_metrics: Typed cognitive state at message creation (SF2-14)
    """
    protocol: str = Field(..., description="Protocol identifier (e.g., 'generic-json', 'openai-responses')")
    sender_participant_ref: ParticipantRef = Field(..., description="Sender participant reference")
    receiver_participant_ref: ParticipantRef = Field(..., description="Receiver participant reference")
    trace_id: str = Field(..., description="Trace ID for request tracking (MANDATORY for AI↔AI)")
    turn_id: int = Field(..., description="Turn ID (monotonic per session)", ge=1)

    # NEW (Paket E): Envelope hardening fields
    message_id: str = Field(..., description="Unique message ID (UUID) for deduplication")
    timestamp_utc: str = Field(..., description="ISO8601 UTC timestamp")
    ttl_seconds: int = Field(..., ge=0, description="Time-to-live in seconds (0 = no expiration)")
    nonce: str = Field(..., description="Random nonce for replay protection")

    intent: dict[str, Any] | None = Field(None, description="Intent metadata (optional)")
    payload: dict[str, Any] = Field(..., description="Message payload (protocol-specific)")
    capabilities: dict[str, Any] | None = Field(None, description="Sender capabilities (optional)")
    cognitive_metrics: CognitiveMetrics | None = Field(
        None, description="Cognitive state metrics at message creation time (SF2-14)"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator('message_id')
    @classmethod
    def validate_message_id(cls, v):
        """Validate message_id is a valid UUID."""
        try:
            uuid.UUID(v)
            return v
        except ValueError as err:
            raise ValueError(f"message_id must be a valid UUID, got: {v}") from err

    @field_validator('timestamp_utc')
    @classmethod
    def validate_timestamp(cls, v):
        """Validate timestamp is ISO8601 format."""
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except (ValueError, AttributeError) as err:
            raise ValueError(f"timestamp_utc must be ISO8601 format, got: {v}") from err

    @field_validator('nonce')
    @classmethod
    def validate_nonce(cls, v):
        """Validate nonce is non-empty."""
        if not v or not v.strip():
            raise ValueError("nonce must be non-empty")
        return v

    @classmethod
    def create(
        cls,
        protocol: str,
        sender_participant_ref: ParticipantRef,
        receiver_participant_ref: ParticipantRef,
        trace_id: str,
        turn_id: int,
        payload: dict[str, Any],
        ttl_seconds: int = 3600,  # Default 1 hour
        message_id: str | None = None,
        timestamp_utc: str | None = None,
        nonce: str | None = None,
        intent: dict[str, Any] | None = None,
        capabilities: dict[str, Any] | None = None,
        cognitive_metrics: CognitiveMetrics | None = None,
        metadata: dict[str, Any] | None = None
    ) -> 'AgentMessageEnvelope':
        """
        Create envelope with auto-generated fields.

        Args:
            protocol: Protocol identifier
            sender_participant_ref: Sender participant reference
            receiver_participant_ref: Receiver participant reference
            trace_id: Trace ID (mandatory)
            turn_id: Turn ID (monotonic)
            payload: Message payload
            ttl_seconds: Time-to-live in seconds (default: 3600)
            message_id: Optional message ID (auto-generated if not provided)
            timestamp_utc: Optional timestamp (auto-generated if not provided)
            nonce: Optional nonce (auto-generated if not provided)
            intent: Optional intent metadata
            capabilities: Optional capabilities
            metadata: Optional metadata

        Returns:
            AgentMessageEnvelope instance
        """
        # Auto-generate fields if not provided
        if message_id is None:
            message_id = str(uuid.uuid4())

        if timestamp_utc is None:
            timestamp_utc = datetime.now(timezone.utc).isoformat()

        if nonce is None:
            import secrets
            nonce = secrets.token_hex(16)

        return cls(
            protocol=protocol,
            sender_participant_ref=sender_participant_ref,
            receiver_participant_ref=receiver_participant_ref,
            trace_id=trace_id,
            turn_id=turn_id,
            message_id=message_id,
            timestamp_utc=timestamp_utc,
            ttl_seconds=ttl_seconds,
            nonce=nonce,
            intent=intent,
            payload=payload,
            capabilities=capabilities,
            cognitive_metrics=cognitive_metrics,
            metadata=metadata or {}
        )

    def validate_cognitive_integrity(
        self,
        min_phi: float = 0.0,
        max_entropy: float = 1.0,
        min_coherence: float = 0.0,
    ) -> bool:
        """
        Check cognitive integrity of envelope using embedded metrics.

        Patent SF2-14: Cognitive state metrics are used for integrity checking
        when present. Returns True if no metrics are attached (lenient).

        Args:
            min_phi: Minimum acceptable phi value
            max_entropy: Maximum acceptable entropy value
            min_coherence: Minimum acceptable coherence value

        Returns:
            True if metrics pass integrity check or are absent
        """
        if self.cognitive_metrics is None:
            return True  # No metrics → pass (backward compatible)
        m = self.cognitive_metrics
        if m.phi < min_phi:
            return False
        if m.entropy > max_entropy:
            return False
        if m.coherence < min_coherence:
            return False
        return True

    def is_expired(self) -> bool:
        """Check if envelope is expired based on TTL."""
        if self.ttl_seconds == 0:
            return False  # No expiration

        try:
            timestamp = datetime.fromisoformat(self.timestamp_utc.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            age_seconds = (now - timestamp).total_seconds()
            return age_seconds > self.ttl_seconds
        except Exception:
            return True  # If we can't parse, consider expired

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        # Handle ParticipantType: if it's already a string (use_enum_values=True), use directly
        # Otherwise, get .value if it's an enum
        sender_type = self.sender_participant_ref.type
        if isinstance(sender_type, str):
            sender_type_str = sender_type
        else:
            sender_type_str = sender_type.value if hasattr(sender_type, 'value') else str(sender_type)

        receiver_type = self.receiver_participant_ref.type
        if isinstance(receiver_type, str):
            receiver_type_str = receiver_type
        else:
            receiver_type_str = receiver_type.value if hasattr(receiver_type, 'value') else str(receiver_type)

        return {
            "protocol": self.protocol,
            "sender_participant_ref": {
                "id": self.sender_participant_ref.id,
                "type": sender_type_str
            },
            "receiver_participant_ref": {
                "id": self.receiver_participant_ref.id,
                "type": receiver_type_str
            },
            "trace_id": self.trace_id,
            "turn_id": self.turn_id,
            "message_id": self.message_id,
            "timestamp_utc": self.timestamp_utc,
            "ttl_seconds": self.ttl_seconds,
            "nonce": self.nonce,
            "intent": self.intent,
            "payload": self.payload,
            "capabilities": self.capabilities,
            "cognitive_metrics": self.cognitive_metrics.model_dump() if self.cognitive_metrics else None,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'AgentMessageEnvelope':
        """Deserialize from dictionary."""
        # Use core ParticipantRef (no bridge dependency)

        sender_ref = ParticipantRef(
            id=data["sender_participant_ref"]["id"],
            type=ParticipantType(data["sender_participant_ref"]["type"]),
            name=data["sender_participant_ref"].get("name"),
            metadata=data["sender_participant_ref"].get("metadata"),
        )
        receiver_ref = ParticipantRef(
            id=data["receiver_participant_ref"]["id"],
            type=ParticipantType(data["receiver_participant_ref"]["type"]),
            name=data["receiver_participant_ref"].get("name"),
            metadata=data["receiver_participant_ref"].get("metadata"),
        )

        return cls(
            protocol=data["protocol"],
            sender_participant_ref=sender_ref,
            receiver_participant_ref=receiver_ref,
            trace_id=data["trace_id"],
            turn_id=data["turn_id"],
            message_id=data.get("message_id", str(uuid.uuid4())),  # Backward compat: generate if missing
            timestamp_utc=data.get("timestamp_utc", datetime.now(timezone.utc).isoformat()),  # Backward compat
            ttl_seconds=data.get("ttl_seconds", 3600),  # Backward compat: default 1 hour
            nonce=data.get("nonce", ""),  # Backward compat: empty if missing
            intent=data.get("intent"),
            payload=data["payload"],
            capabilities=data.get("capabilities"),
            cognitive_metrics=CognitiveMetrics(**data["cognitive_metrics"]) if data.get("cognitive_metrics") else None,
            metadata=data.get("metadata", {})
        )


class HandshakeResponse(BaseModel):
    """
    Handshake response with capabilities and configuration.

    Returned by handshake() to exchange agent capabilities.
    """
    model_capabilities: dict[str, Any] = Field(..., description="Model capabilities (name, provider, context_window, etc.)")
    tool_capabilities: list[dict[str, Any]] | None = Field(None, description="Available tools")
    context_window_hints: dict[str, Any] = Field(default_factory=dict, description="Context window hints (max_tokens, etc.)")
    safety_level: str = Field(..., description="Safety level (e.g., 'strict', 'moderate', 'permissive')")
    protocol_version: str = Field(default="0.1", description="Protocol version")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


def detect_capabilities_from_participant(participant: ParticipantRef) -> dict[str, Any]:
    """
    Capability detection: extract model and tool capabilities from participant metadata.

    Reads participant.metadata for: provider, model_name, context_window, max_tokens,
    tool_capabilities, safety_level. Used by handshake() to build HandshakeResponse.
    """
    out: dict[str, Any] = {
        "provider": "unknown",
        "model_name": "default",
        "context_window": 4096,
        "max_tokens": 2048,
        "tool_capabilities": None,
        "safety_level": "moderate",
    }
    if not hasattr(participant, "metadata") or not participant.metadata:
        return out
    meta = participant.metadata if isinstance(participant.metadata, dict) else {}
    if meta.get("provider") is not None:
        out["provider"] = str(meta["provider"])
    if meta.get("model_name") is not None:
        out["model_name"] = str(meta["model_name"])
    if meta.get("context_window") is not None:
        try:
            out["context_window"] = int(meta["context_window"])
        except (TypeError, ValueError):
            pass
    if meta.get("max_tokens") is not None:
        try:
            out["max_tokens"] = int(meta["max_tokens"])
        except (TypeError, ValueError):
            pass
    if meta.get("tool_capabilities") is not None and isinstance(meta["tool_capabilities"], list):
        out["tool_capabilities"] = meta["tool_capabilities"]
    if meta.get("safety_level") is not None and isinstance(meta["safety_level"], str):
        out["safety_level"] = meta["safety_level"]
    return out


def handshake(
    participant: ParticipantRef,
    requested_capabilities: dict[str, Any] | None = None
) -> HandshakeResponse:
    """
    Perform handshake to exchange capabilities.

    Uses capability detection from participant.metadata (provider, model_name,
    context_window, max_tokens, tool_capabilities, safety_level). Falls back to
    defaults when metadata is missing or invalid.
    """
    cap = detect_capabilities_from_participant(participant)
    model_capabilities = {
        "name": cap["model_name"],
        "provider": cap["provider"],
        "context_window": cap["context_window"],
        "max_tokens": cap["max_tokens"],
    }
    return HandshakeResponse(
        model_capabilities=model_capabilities,
        tool_capabilities=cap["tool_capabilities"],
        context_window_hints={
            "max_tokens": cap["max_tokens"],
            "context_window": cap["context_window"],
        },
        safety_level=cap["safety_level"],
        protocol_version="0.1",
        metadata={
            "participant_id": participant.id,
            "participant_type": participant.type.value,
        },
    )
