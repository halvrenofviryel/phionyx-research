"""
Interlink Envelope Model
========================

Represents a secure agent-to-agent communication envelope.

Migrated from `phionyx_interlink.envelope.envelope` on 2026-05-28 (see
`phionyx_core/contracts/interlink/__init__.py` for the migration note).
Schema preserved as dataclass form (not Pydantic) to keep the migration
behaviour-identical for `phionyx_agents/interlink/`. A future v5 schema
pass may align this with the Pydantic v4 contracts.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib
import json


@dataclass
class EnvelopeHeader:
    """Envelope header containing metadata"""
    turn_id: str  # Monotonic counter for message ordering
    parent_trace: Optional[str] = None  # Cryptographic reference to parent message
    decision_signature: Optional[str] = None  # Hash of kernel output
    ttl: int = 3600  # Semantic time delta (seconds)
    sender_id: str = ""
    receiver_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert header to dictionary"""
        return {
            "turn_id": self.turn_id,
            "parent_trace": self.parent_trace,
            "decision_signature": self.decision_signature,
            "ttl": self.ttl,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EnvelopeHeader":
        """Create header from dictionary"""
        return cls(
            turn_id=data.get("turn_id", ""),
            parent_trace=data.get("parent_trace"),
            decision_signature=data.get("decision_signature"),
            ttl=data.get("ttl", 3600),
            sender_id=data.get("sender_id", ""),
            receiver_id=data.get("receiver_id", ""),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
        )


@dataclass
class StateMetrics:
    """Cognitive state metrics"""
    phi: float = 0.0  # Integrated information
    entropy: float = 0.0  # System entropy
    coherence: float = 0.0  # Coherence score

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            "phi": self.phi,
            "entropy": self.entropy,
            "coherence": self.coherence,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StateMetrics":
        """Create metrics from dictionary"""
        return cls(
            phi=data.get("phi", 0.0),
            entropy=data.get("entropy", 0.0),
            coherence=data.get("coherence", 0.0),
        )


@dataclass
class EnvelopePayload:
    """Envelope payload containing message and state"""
    message: str
    state_metrics: Optional[StateMetrics] = None
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert payload to dictionary"""
        return {
            "message": self.message,
            "state_metrics": self.state_metrics.to_dict() if self.state_metrics else None,
            "context": self.context,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EnvelopePayload":
        """Create payload from dictionary"""
        state_metrics = None
        if data.get("state_metrics"):
            state_metrics = StateMetrics.from_dict(data["state_metrics"])

        return cls(
            message=data.get("message", ""),
            state_metrics=state_metrics,
            context=data.get("context", {}),
        )


@dataclass
class ValidationResult:
    """Envelope validation result"""
    causal_integrity: bool = False
    cognitive_health: bool = False
    semantic_freshness: bool = False
    signature_valid: bool = False

    def is_valid(self) -> bool:
        """Check if all validations passed"""
        return all([
            self.causal_integrity,
            self.cognitive_health,
            self.semantic_freshness,
            self.signature_valid,
        ])

    def to_dict(self) -> Dict[str, Any]:
        """Convert validation result to dictionary"""
        return {
            "causal_integrity": self.causal_integrity,
            "cognitive_health": self.cognitive_health,
            "semantic_freshness": self.semantic_freshness,
            "signature_valid": self.signature_valid,
        }


@dataclass
class InterlinkEnvelope:
    """
    Interlink Protocol Envelope

    Represents a secure, cognitively-validated agent communication message.
    """
    header: EnvelopeHeader
    payload: EnvelopePayload
    validation: Optional[ValidationResult] = None
    signature: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert envelope to dictionary"""
        result = {
            "header": self.header.to_dict(),
            "payload": self.payload.to_dict(),
        }

        if self.validation:
            result["validation"] = self.validation.to_dict()

        if self.signature:
            result["signature"] = self.signature

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InterlinkEnvelope":
        """Create envelope from dictionary"""
        header = EnvelopeHeader.from_dict(data.get("header", {}))
        payload = EnvelopePayload.from_dict(data.get("payload", {}))

        validation = None
        if data.get("validation"):
            validation = ValidationResult(**data["validation"])

        return cls(
            header=header,
            payload=payload,
            validation=validation,
            signature=data.get("signature"),
        )

    def to_json(self) -> str:
        """Serialize envelope to JSON"""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "InterlinkEnvelope":
        """Deserialize envelope from JSON"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def compute_signature(self, secret_key: Optional[str] = None) -> str:
        """
        Compute cryptographic signature for envelope

        Args:
            secret_key: Optional secret key for signing

        Returns:
            Cryptographic signature
        """
        # Create signature payload
        signature_data = {
            "header": self.header.to_dict(),
            "payload": self.payload.to_dict(),
        }

        if secret_key:
            signature_data["secret"] = secret_key

        # Compute hash
        signature_str = json.dumps(signature_data, sort_keys=True)
        signature = hashlib.sha256(signature_str.encode()).hexdigest()

        return signature

    def is_expired(self) -> bool:
        """Check if envelope has expired based on TTL"""
        try:
            timestamp = datetime.fromisoformat(self.header.timestamp.replace('Z', '+00:00'))
            expiry = timestamp + timedelta(seconds=self.header.ttl)
            return datetime.utcnow() > expiry
        except Exception:
            return True

    def get_age_seconds(self) -> float:
        """Get age of envelope in seconds"""
        try:
            timestamp = datetime.fromisoformat(self.header.timestamp.replace('Z', '+00:00'))
            age = datetime.utcnow() - timestamp
            return age.total_seconds()
        except Exception:
            return float('inf')

