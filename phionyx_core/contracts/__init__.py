"""
Phionyx Core Contracts Package

Single source of truth for all canonical contracts:
- Telemetry canonical blocks (46-block KERNEL CONTRACT, v3.8.0)
- Envelope contracts (turn, agent)
- State contracts
- Invariants
"""
from . import envelopes, telemetry

__all__ = [
    'telemetry',
    'envelopes',
]
