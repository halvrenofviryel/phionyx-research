"""
Envelope Contracts Package

Core message envelope contracts for turn and agent communication.
"""
from .turn_envelope import TurnEnvelope, DeliveryAck
from .agent_envelope import AgentMessageEnvelope, HandshakeResponse
from .causal_chain_tracker import CausalChainTracker, CausalConsistencyViolation
from .envelope_validator import EnvelopeValidator, EnvelopeValidationResult

__all__ = [
    'TurnEnvelope',
    'DeliveryAck',
    'AgentMessageEnvelope',
    'HandshakeResponse',
    'CausalChainTracker',
    'CausalConsistencyViolation',
    'EnvelopeValidator',
    'EnvelopeValidationResult',
]
