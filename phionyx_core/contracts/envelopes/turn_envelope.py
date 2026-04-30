"""
TurnEnvelope - End-to-End Delivery Guarantee Contract
======================================================

Provides delivery guarantee for messages from frontend -> API -> core -> response.

Critical invariants:
1. conversation_id is required (reject if missing)
2. turn_id must be monotonic per conversation (reject out-of-order)
3. message_id is idempotency key (same message_id -> same response)
4. user_text_sha256 guarantees message integrity
5. delivery_ack confirms message was received correctly

Schema version: 1.0
"""

import hashlib

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TurnEnvelope(BaseModel):
    """
    TurnEnvelope - Wraps user message with delivery metadata.

    Ensures message cannot be lost or modified in transit.
    """
    # Required fields
    conversation_id: str = Field(..., description="Conversation/session identifier (required)")
    turn_id: int = Field(..., description="Monotonic turn ID per conversation (starts at 1)")
    message_id: str = Field(..., description="UUID idempotency key for this message")
    user_text: str = Field(..., description="User input text (raw, unmodified)")
    user_text_sha256: str = Field(..., description="SHA256 hash of user_text for integrity check")
    client_timestamp_ms: int = Field(..., description="Client-side timestamp (milliseconds since epoch)")
    schema_version: str = Field(default="1.0", description="Schema version for contract evolution")

    # Optional fields
    parent_turn_id: int | None = Field(None, description="Parent turn ID (for conversation threading)")

    @field_validator('turn_id')
    @classmethod
    def validate_turn_id(cls, v):
        """Turn ID must be positive integer (starts at 1)."""
        if v < 1:
            raise ValueError(f"turn_id must be >= 1, got {v}")
        return v

    @field_validator('user_text_sha256')
    @classmethod
    def validate_sha256_format(cls, v):
        """SHA256 hash must be 64 hex characters."""
        if len(v) != 64:
            raise ValueError(f"user_text_sha256 must be 64 hex characters, got {len(v)}")
        try:
            int(v, 16)  # Validate hex
        except ValueError as err:
            raise ValueError(f"user_text_sha256 must be valid hex string, got {v}") from err
        return v.lower()  # Normalize to lowercase

    @classmethod
    def compute_sha256(cls, text: str) -> str:
        """Compute SHA256 hash of text."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def verify_hash(self) -> bool:
        """Verify that user_text_sha256 matches user_text."""
        computed_hash = self.compute_sha256(self.user_text)
        return computed_hash.lower() == self.user_text_sha256.lower()

    model_config = ConfigDict(json_schema_extra={'example': {'conversation_id': 'conv_abc123', 'turn_id': 1, 'message_id': '550e8400-e29b-41d4-a716-446655440000', 'user_text': 'Hello, how are you?', 'user_text_sha256': 'a1b2c3d4e5f6...', 'client_timestamp_ms': 1704067200000, 'schema_version': '1.0', 'parent_turn_id': None}})
class DeliveryAck(BaseModel):
    """
    Delivery acknowledgment - confirms message was received correctly.

    Returned in response to confirm:
    1. Message was received with matching hash
    2. Prompt context hash (for detecting context changes)
    """
    conversation_id: str = Field(..., description="Conversation ID from envelope")
    turn_id: int = Field(..., description="Turn ID from envelope")
    message_id: str = Field(..., description="Message ID from envelope")
    received_user_text_sha256: str = Field(..., description="SHA256 of user_text as received by core")
    prompt_context_sha256: str | None = Field(None, description="SHA256 of prompt context (if available)")
    delivery_status: str = Field(default="delivered", description="Delivery status: delivered, mismatch, rejected")
    delivery_error: str | None = Field(None, description="Error message if delivery failed")

    model_config = ConfigDict(json_schema_extra={'example': {'conversation_id': 'conv_abc123', 'turn_id': 1, 'message_id': '550e8400-e29b-41d4-a716-446655440000', 'received_user_text_sha256': 'a1b2c3d4e5f6...', 'prompt_context_sha256': 'b2c3d4e5f6a1...', 'delivery_status': 'delivered', 'delivery_error': None}})
