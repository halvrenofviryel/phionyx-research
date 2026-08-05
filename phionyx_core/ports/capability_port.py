"""
Capability Port — v4
=======================

Port interface for capability derivation (AD-2: port-adapter pattern).

Core does not decide what a participant is allowed to do. It receives
capabilities and honours them; deriving them requires knowing about actor
profiles and product context, which are delivery-layer concerns. This port is
the seam: Core names the operation, the runtime supplies the answer.

A `CapabilityDeriverProtocol` served this role before `6aa41fff`
("Migration: reconcile core modules and finish consolidation", 2026-01-01),
which deleted it along with the rest of `echo-server/app/core/interfaces/`. It
was a `typing.Protocol` living in the delivery layer. Reinstated here as an
ABC in `phionyx_core/ports/`, because that is where ports belong under the
current architecture and ABC is the idiom the eleven existing ports use.

Types are `Any` for the same reason every other port uses them: the concrete
participant and capability models live in the bridge, and Core may not import
from it. Naming them here would invert the dependency this port exists to keep
pointing the right way.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class CapabilityPort(ABC):
    """Abstract port for deriving run capabilities."""

    @abstractmethod
    def derive(self, participant: Any, product_context: Optional[str] = None) -> Any:
        """
        Derive the capabilities a run may use, for this participant.

        Args:
            participant: The participant model (human, AI agent, system).
            product_context: Which product this run belongs to, when the answer
                depends on it.

        Returns:
            A capability set the pipeline can read, or None when nothing is
            derived — matching `BlockContext.capabilities`, which is Optional
            and defaults to None.
        """
        ...


class NullCapabilityPort(CapabilityPort):
    """
    Null implementation — derives nothing.

    Returns None rather than an all-permitted capability set. A port that
    silently granted everything when no deriver was wired would turn a missing
    adapter into an open gate, and the absence would look identical to a
    deliberate decision in the record.
    """

    def derive(self, participant: Any, product_context: Optional[str] = None) -> Any:
        return None
