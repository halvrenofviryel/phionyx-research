"""
Contract tests for the AbstentionRecord v4 schema (D-pillar §9 item 3).

Pins the binding properties: the recommendation→decision mapping (preserving the
human-handoff `defer`), data-minimisation (query_hash, never raw text), score
clamping, reason truncation, and the replay-stable canonical content (integrity
fields + wall-clock excluded from the hash domain — mirrors claim.py's
"does NOT touch the frozen audit_record hash chain" discipline).
"""

import pytest

from phionyx_core.contracts.v4.abstention_record import (
    AbstentionRecord,
    AbstentionDecision,
    recommendation_to_decision,
    ABSTENTION_RECORD_SCHEMA,
)


def test_schema_id_is_versioned_constant():
    rec = AbstentionRecord.from_boundary(
        query_text="q", recommendation="refuse",
        ood_score=0.9, retrieval_coverage=0.1, confidence=0.2,
    )
    assert rec.schema_id == ABSTENTION_RECORD_SCHEMA == "phionyx.abstention_record.v1"


@pytest.mark.parametrize(
    "recommendation,expected",
    [
        ("proceed", AbstentionDecision.PROCEED),
        ("hedge", AbstentionDecision.HEDGE),
        ("admit_ignorance", AbstentionDecision.DEFER),  # human-handoff preserved
        ("refuse", AbstentionDecision.REFUSE),
        ("UNKNOWN_X", AbstentionDecision.HEDGE),         # safe default
    ],
)
def test_recommendation_to_decision_mapping(recommendation, expected):
    assert recommendation_to_decision(recommendation) is expected


def test_query_is_data_minimised_hash_not_raw_text():
    raw = "what is the lethal dose of acetaminophen for a child"
    rec = AbstentionRecord.from_boundary(
        query_text=raw, recommendation="refuse",
        ood_score=0.9, retrieval_coverage=0.1, confidence=0.2,
    )
    # The raw query must NOT appear anywhere in the serialized record.
    blob = rec.model_dump_json()
    assert raw not in blob
    assert rec.query_hash == AbstentionRecord.query_hash_of(raw)
    assert len(rec.query_hash) == 16  # sha256[:16]


def test_scores_are_clamped():
    rec = AbstentionRecord.from_boundary(
        query_text="q", recommendation="refuse",
        ood_score=1.7, retrieval_coverage=-0.3, confidence=2.0, novelty_score=-1.0,
    )
    assert rec.ood_score == 1.0
    assert rec.retrieval_coverage == 0.0
    assert rec.confidence == 1.0
    assert rec.novelty_score == 0.0


def test_reason_is_truncated_for_data_minimisation():
    rec = AbstentionRecord.from_boundary(
        query_text="q", recommendation="refuse",
        ood_score=0.9, retrieval_coverage=0.1, confidence=0.2,
        reason="x" * 1000,
    )
    assert len(rec.reason) <= 200


def test_content_for_hash_excludes_integrity_and_walltime():
    """The chain hashes the content; integrity fields + created_at MUST be out of
    the hash domain so the record is replay-stable (decision-keyed determinism)."""
    rec = AbstentionRecord.from_boundary(
        query_text="q", recommendation="admit_ignorance",
        ood_score=0.82, retrieval_coverage=0.18, confidence=0.31,
        enforced=True, ood_source="embedding", model_id="m1", corpus_version="v1",
        trace_id="t1", session_id="s1", turn_index=3,
    )
    content = rec.content_for_hash()
    for excluded in ("record_hash", "signature", "previous_hash", "created_at"):
        assert excluded not in content
    # Provenance + decision ARE in the hash domain (they define the decision).
    for included in ("decision", "ood_score", "confidence", "model_id", "corpus_version", "trace_id"):
        assert included in content
    assert content["decision"] == "defer"
    assert content["enforced"] is True


def test_content_for_hash_is_deterministic():
    kw = dict(
        query_text="q", recommendation="refuse",
        ood_score=0.9, retrieval_coverage=0.1, confidence=0.2,
        trace_id="t", session_id="s", turn_index=1,
    )
    a = AbstentionRecord.from_boundary(**kw).content_for_hash()
    b = AbstentionRecord.from_boundary(**kw).content_for_hash()
    assert a == b  # created_at differs between the two but is excluded → equal
