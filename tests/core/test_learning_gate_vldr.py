"""
VLDR v1 — Verified Learning Decision Record tests (P1)
======================================================

Covers Learning Gate Contract v1.0 §6/§7 compliance closure:
- every decision emits a signed, replayable record (§7)
- evidence-less self-modification is rejected AND recorded
- rollback restores the prior value AND writes an audit record (§6.5)
- the learning-gate block fails CLOSED (no "ok" on failure)
- the decision path is replayable from the record chain
- the record hash is decision-keyed (clock excluded) + tamper-evident
"""

import pytest

from phionyx_core.contracts.v4.learning_update import LearningUpdate, LearningGateDecision
from phionyx_core.contracts.v4.learning_decision_record import LearningDecisionRecord
from phionyx_core.ports.learning_record_port import (
    InMemoryLearningRecordPort,
    NullLearningRecordPort,
)
from phionyx_core.services.learning_gate_service import LearningGateService
from phionyx_core.pipeline.blocks.learning_gate import LearningGateBlock


def _update(param="DEFAULT_GAMMA", current=0.15, proposed=0.18, zone="adaptive", evidence=None):
    ev = (
        evidence
        if evidence is not None
        else [
            {"experiment_id": f"exp_{i}", "cqs_delta": 0.01, "guardrail_passed": True}
            for i in range(3)
        ]
    )
    return LearningUpdate(
        target_parameter=param,
        current_value=current,
        proposed_value=proposed,
        delta=proposed - current,
        boundary_zone=zone,
        evidence=ev,
    )


def _adaptive_service():
    """Service with a deterministic registry (DEFAULT_GAMMA -> adaptive)."""
    svc = LearningGateService()
    svc._zone_registry = {"DEFAULT_GAMMA": "adaptive", "ethics_pass_threshold": "gated"}
    return svc


# ── Record shape: decision-keyed hash + tamper evidence ──────────────────────

class TestLearningDecisionRecord:
    def test_hash_excludes_clock(self):
        """Same decision facts + same prev hash → identical hash regardless of timestamp."""
        a = LearningDecisionRecord(
            update_id="u1", target_parameter="x", boundary_zone="adaptive",
            gate_decision="approved", timestamp_utc="2026-06-13T00:00:00Z",
        )
        b = LearningDecisionRecord(
            update_id="u1", target_parameter="x", boundary_zone="adaptive",
            gate_decision="approved", timestamp_utc="2026-06-13T09:99:99Z",
        )
        assert a.compute_hash() == b.compute_hash()

    def test_hash_changes_with_decision(self):
        a = LearningDecisionRecord(
            update_id="u1", target_parameter="x", boundary_zone="adaptive",
            gate_decision="approved",
        )
        b = LearningDecisionRecord(
            update_id="u1", target_parameter="x", boundary_zone="adaptive",
            gate_decision="rejected",
        )
        assert a.compute_hash() != b.compute_hash()


class TestInMemoryPortChain:
    def test_chain_links_and_verifies(self):
        port = InMemoryLearningRecordPort()
        for i in range(3):
            port.emit(LearningDecisionRecord(
                update_id=f"u{i}", target_parameter="x",
                boundary_zone="adaptive", gate_decision="approved",
            ))
        recs = port.records()
        assert len(recs) == 3
        assert recs[0].prev_record_hash is None
        assert recs[1].prev_record_hash == recs[0].record_hash
        assert recs[2].prev_record_hash == recs[1].record_hash
        assert port.chain_head() == recs[2].record_hash
        assert port.verify_chain() is True

    def test_tamper_breaks_chain(self):
        port = InMemoryLearningRecordPort()
        for i in range(3):
            port.emit(LearningDecisionRecord(
                update_id=f"u{i}", target_parameter="x",
                boundary_zone="adaptive", gate_decision="approved",
            ))
        # Tamper: flip a recorded decision after the fact.
        port.records()[1].gate_decision = "rejected"
        assert port.verify_chain() is False


# ── Service emission: §7 every decision recorded ─────────────────────────────

class TestServiceEmitsRecords:
    @pytest.mark.asyncio
    async def test_evidence_less_rejected_and_recorded(self):
        """Adaptive update with no evidence → REJECTED, and the rejection is recorded."""
        svc = _adaptive_service()
        upd = _update(evidence=[])
        await svc.evaluate_updates([upd])
        assert upd.gate_decision == LearningGateDecision.REJECTED
        recs = svc.record_port.records()
        assert len(recs) == 1
        assert recs[0].gate_decision == "rejected"
        assert recs[0].update_id == upd.update_id

    @pytest.mark.asyncio
    async def test_approved_update_writes_signed_vldr(self):
        svc = _adaptive_service()
        upd = _update()
        await svc.evaluate_updates([upd])
        assert upd.gate_decision == LearningGateDecision.APPROVED
        rec = svc.record_port.records()[0]
        assert rec.gate_decision == "approved"
        assert rec.signature_alg == "sha256-chain"
        assert rec.record_hash is not None
        assert rec.evidence_count == 3
        assert rec.cqs_delta == pytest.approx(0.01)

    @pytest.mark.asyncio
    async def test_gated_update_pending_and_recorded(self):
        svc = _adaptive_service()
        upd = _update(param="ethics_pass_threshold")
        await svc.evaluate_updates([upd])
        assert upd.gate_decision == LearningGateDecision.PENDING
        assert svc.record_port.records()[0].gate_decision == "pending"

    @pytest.mark.asyncio
    async def test_replay_from_record_reconstructs_path(self):
        """The decision path is reconstructable from the record chain alone."""
        svc = _adaptive_service()
        batch = [
            _update(),                                  # approved
            _update(evidence=[]),                       # rejected (no evidence)
            _update(param="ethics_pass_threshold"),     # pending (gated)
        ]
        await svc.evaluate_updates(batch)
        replayed = [r.gate_decision for r in svc.record_port.records()]
        assert replayed == ["approved", "rejected", "pending"]
        assert svc.record_port.verify_chain() is True


# ── Rollback: §6.5 restore value + write audit record ────────────────────────

class TestRollbackRecord:
    @pytest.mark.asyncio
    async def test_rollback_restores_and_records(self):
        svc = _adaptive_service()
        upd = _update()
        await svc.evaluate_updates([upd])          # approved + 1 record
        await svc.apply_approved([upd])
        n_before = len(svc.record_port.records())

        ok = svc.rollback_update(upd.update_id)
        assert ok is True
        # value restored (gate authority): restored_value == original current_value
        assert upd.metadata.get("restored_value") == upd.current_value
        # a rollback audit record was written
        recs = svc.record_port.records()
        assert len(recs) == n_before + 1
        last = recs[-1]
        assert last.rollback is True
        assert last.restored is True
        assert last.restored_value_repr == repr(upd.current_value)[:128]
        assert svc.record_port.verify_chain() is True

    @pytest.mark.asyncio
    async def test_null_port_is_noop(self):
        svc = LearningGateService(record_port=NullLearningRecordPort())
        svc._zone_registry = {"DEFAULT_GAMMA": "adaptive"}
        await svc.evaluate_updates([_update()])
        assert svc.record_port.records() == []
        assert svc.record_port.chain_head() is None


# ── Block: fail-CLOSED on failure ────────────────────────────────────────────

class _RaisingService:
    async def evaluate_updates(self, updates):
        raise RuntimeError("boom")

    async def apply_approved(self, updates):
        return 0


class _Ctx:
    """Minimal duck-typed BlockContext for the failure path."""
    def __init__(self):
        self.metadata = {"learning_updates": [_update()]}
        self.pipeline_version = "3.8.0"


class TestBlockFailsClosed:
    @pytest.mark.asyncio
    async def test_block_fails_closed_on_service_error(self):
        block = LearningGateBlock(gate_service=_RaisingService())
        result = await block.execute(_Ctx())
        assert result.status == "error"          # NOT "ok"
        assert result.error is not None          # exception surfaced for telemetry (①)
        assert result.data.get("fail_closed") is True
        assert result.data.get("updates_approved") == 0


# ── ③ no silent fallback: block with NO service still records every decision ──

class TestBlockNoSilentFallback:
    @pytest.mark.asyncio
    async def test_block_defaults_to_recording_service(self):
        block = LearningGateBlock()  # no gate_service injected
        # the default service must be a real one with a record sink (no ad-hoc fallback)
        assert block.gate_service is not None
        block.gate_service._zone_registry = {"DEFAULT_GAMMA": "adaptive"}
        ctx = _Ctx()
        await block.execute(ctx)
        # §7: the decision was recorded, not silently made
        assert len(block.gate_service.record_port.records()) == 1


# ── ④ bounded in-memory port: oldest evicted, eviction observable, chain still verifies ──

class TestBoundedPort:
    def test_eviction_is_bounded_and_observable(self):
        port = InMemoryLearningRecordPort(max_records=3)
        for i in range(5):
            port.emit(LearningDecisionRecord(
                update_id=f"u{i}", target_parameter="x",
                boundary_zone="adaptive", gate_decision="approved",
            ))
        assert len(port.records()) == 3
        assert port.evicted_count == 2
        assert port.verify_chain() is True   # windowed chain still verifies


# ── ⑦ full-value hash: same truncated repr, different value → different record hash ──

class TestValueHashCollisionSafety:
    def test_truncated_repr_collision_does_not_collide_hash(self):
        prefix = "x" * 128
        a = LearningDecisionRecord(
            update_id="u", target_parameter="p", boundary_zone="adaptive",
            gate_decision="approved", original_value_repr=prefix,
            original_value_hash="sha256:" + "a" * 64,
        )
        b = LearningDecisionRecord(
            update_id="u", target_parameter="p", boundary_zone="adaptive",
            gate_decision="approved", original_value_repr=prefix,   # SAME truncated repr
            original_value_hash="sha256:" + "b" * 64,               # DIFFERENT full value
        )
        assert a.compute_hash() != b.compute_hash()
