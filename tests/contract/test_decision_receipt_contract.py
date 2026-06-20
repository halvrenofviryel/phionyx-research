"""
Contract tests — DecisionReceipt (v4, F18)
==========================================

Pins the data-minimised "AI decision receipt" shape: governance facts only, NO raw user/output
text fields. F18 forensics-lite returns these when resolving evidence ids / filtering decisions.
"""

import json

import pytest
from pydantic import ValidationError

from phionyx_core.contracts.v4 import DecisionReceipt


class TestDecisionReceiptSchema:
    def test_defaults_are_safe(self):
        r = DecisionReceipt()
        assert r.evidence_id is None and r.directive is None
        assert r.policy_basis == [] and r.evidence_link_kinds == []
        assert r.redacted is False

    def test_data_minimisation_no_raw_text_fields(self):
        # The receipt must NOT carry raw user/output text — only governance facts.
        fields = set(DecisionReceipt.model_fields)
        for forbidden in ("user_text", "output_text", "text", "raw", "input", "output"):
            assert forbidden not in fields, f"DecisionReceipt must not expose {forbidden!r}"

    def test_turn_index_nonnegative(self):
        assert DecisionReceipt(turn_index=0).turn_index == 0
        with pytest.raises(ValidationError):
            DecisionReceipt(turn_index=-1)

    def test_roundtrip(self):
        r = DecisionReceipt(
            evidence_id="phionyx:trace:2026-06-10:sha256:" + "a" * 64,
            trace_id="trace-x", turn_index=7, timestamp_utc="2026-06-10T15:23:45Z",
            directive="block", decision_reason="blocked by ethics gate",
            policy_basis=["deliberative_ethics"], redacted=True,
            evidence_link_kinds=["policy"], anomaly=False, signature_alg="Ed25519",
            chain_verified=True,
        )
        again = DecisionReceipt(**json.loads(r.model_dump_json()))
        assert again.directive == "block"
        assert again.policy_basis == ["deliberative_ethics"]
        assert again.chain_verified is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
