"""
Learning Record Port — v4 (P1 / VLDR v1)
========================================

Port (AD-2 port-adapter) for emitting ``LearningDecisionRecord``s from the
Learning Gate. Core defines the interface plus a deterministic in-memory
hash-chained sink; the live RGE v0.2 signed-envelope adapter (Ed25519)
lives in the bridge/MCP companion because Core cannot import the envelope
store (see ``contracts/v4/decision_receipt.py``).

The in-core ``InMemoryLearningRecordPort`` is enough to make the gate's
audit trail (Contract v1.0 §7) and rollback record (§6) real and
*replay-testable* without any external dependency: records are linked by
``prev_record_hash`` and each carries a ``record_hash`` over its canonical
signing body, so tampering with any record breaks the chain.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from ..contracts.v4.learning_decision_record import LearningDecisionRecord


class LearningRecordPort(ABC):
    """Abstract sink for learning-gate decision records."""

    @abstractmethod
    def emit(self, record: LearningDecisionRecord) -> str:
        """Persist (and, in adapters, sign) one record. Returns the new chain head."""
        ...

    @abstractmethod
    def chain_head(self) -> Optional[str]:
        """Hash of the most recent record, or None if the chain is empty."""
        ...

    @abstractmethod
    def records(self) -> List[LearningDecisionRecord]:
        """Return all emitted records in order (for replay / inspection)."""
        ...

    @abstractmethod
    def verify_chain(self) -> bool:
        """Re-derive every hash + linkage. False if any record was tampered with."""
        ...


class InMemoryLearningRecordPort(LearningRecordPort):
    """Deterministic, tamper-evident in-memory hash chain (no external dependency).

    Bounded: keeps at most ``max_records`` (default 10_000) to avoid unbounded growth
    in a long-lived runtime. When the cap is hit the OLDEST record is evicted and
    ``evicted_count`` is incremented (eviction is observable, never silent). The chain
    head + linkage stay correct for the retained window; for durable, complete history
    inject the bridge envelope adapter instead.
    """

    def __init__(self, max_records: int = 10_000) -> None:
        if max_records < 1:
            raise ValueError("max_records must be >= 1")
        self.max_records = max_records
        self._records: List[LearningDecisionRecord] = []
        self._head: Optional[str] = None
        self.evicted_count: int = 0

    def emit(self, record: LearningDecisionRecord) -> str:
        record.prev_record_hash = self._head
        record.signature_alg = "sha256-chain"
        record.record_hash = record.compute_hash()
        self._head = record.record_hash
        self._records.append(record)
        if len(self._records) > self.max_records:
            self._records.pop(0)
            self.evicted_count += 1
        return record.record_hash

    def chain_head(self) -> Optional[str]:
        return self._head

    def records(self) -> List[LearningDecisionRecord]:
        return list(self._records)

    def verify_chain(self) -> bool:
        if not self._records:
            return True
        # Anchor on the first RETAINED record's prev (None for a full chain, or the
        # evicted predecessor's hash for a windowed chain); linkage + recomputation
        # must hold across the retained window.
        prev: Optional[str] = self._records[0].prev_record_hash
        for record in self._records:
            if record.prev_record_hash != prev:
                return False
            if record.record_hash != record.compute_hash():
                return False
            prev = record.record_hash
        return True


class NullLearningRecordPort(LearningRecordPort):
    """No-op sink for when record emission is not wired (records nothing)."""

    def emit(self, record: LearningDecisionRecord) -> str:
        return ""

    def chain_head(self) -> Optional[str]:
        return None

    def records(self) -> List[LearningDecisionRecord]:
        return []

    def verify_chain(self) -> bool:
        return True


__all__ = [
    "LearningRecordPort",
    "InMemoryLearningRecordPort",
    "NullLearningRecordPort",
]
