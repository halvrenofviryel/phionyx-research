"""
Envelope Contracts Package

Core message envelope contracts for turn and agent communication.
"""
from .agent_envelope import AgentMessageEnvelope, HandshakeResponse
from .causal_chain_tracker import CausalChainTracker, CausalConsistencyViolation
from .envelope_validator import EnvelopeValidationResult, EnvelopeValidator
from .subagent_chain import (
    SubagentChainProtocol,
    SubagentChainRole,
    SubagentChainV0,
    compute_handoff_signing_body,
)
from .turn_envelope import DeliveryAck, TurnEnvelope

__all__ = [
    'TurnEnvelope',
    'DeliveryAck',
    'AgentMessageEnvelope',
    'HandshakeResponse',
    'CausalChainTracker',
    'CausalConsistencyViolation',
    'EnvelopeValidator',
    'EnvelopeValidationResult',
    'SubagentChainV0',
    'SubagentChainProtocol',
    'SubagentChainRole',
    'compute_handoff_signing_body',
]
