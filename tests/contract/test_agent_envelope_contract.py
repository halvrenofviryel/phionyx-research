"""
Contract tests for AgentMessageEnvelope's correlation identifier.

Pins the property ADR-0006 depends on: every envelope carries a usable
`trace_id`. The ADR makes trace_id the single identifier linking the two MCPs'
outputs, so that a reviewer can answer "which gate decisions and which
envelopes belong to the same turn?". An envelope with an empty trace_id is a
record that exists and cannot be tied to anything — the exact condition the ADR
was written to remove.

The field was described as "MANDATORY for AI↔AI" from the start, but until
2026-07-30 nothing enforced it: Pydantic accepted `trace_id=""`. Contract test
added with the validator so the requirement cannot quietly lapse a second time.
"""

import pytest
from pydantic import ValidationError

from phionyx_core.contracts.envelopes.agent_envelope import AgentMessageEnvelope
from phionyx_core.contracts.participants import ParticipantRef, ParticipantType


def _envelope(trace_id):
    return AgentMessageEnvelope.create(
        protocol="generic-json",
        sender_participant_ref=ParticipantRef(
            id="agent_a", type=ParticipantType.AI_AGENT
        ),
        receiver_participant_ref=ParticipantRef(
            id="agent_b", type=ParticipantType.AI_AGENT
        ),
        trace_id=trace_id,
        turn_id=1,
        payload={"user_input": "Hello"},
    )


def test_valid_trace_id_is_preserved_verbatim():
    """The identifier must survive construction unchanged — it is a join key."""
    assert _envelope("trace_abc123").trace_id == "trace_abc123"


@pytest.mark.parametrize(
    "empty,description",
    [
        ("", "empty string"),
        ("   ", "whitespace only"),
        ("\t\n", "whitespace control characters"),
    ],
)
def test_unusable_trace_id_is_rejected(empty, description):
    """
    Whitespace is rejected alongside "" deliberately. A trace_id of " " is
    not more correlatable than one of "" — it merely passes a truthiness check,
    which is how this class of gap survives review.
    """
    with pytest.raises(ValidationError) as exc_info:
        _envelope(empty)

    reason = str(exc_info.value).lower()
    assert "trace_id" in reason, (
        f"Rejected the {description}, but not for trace_id. Reason: {reason}. "
        "A rejection sourced from another field leaves trace_id unenforced."
    )


def test_rejection_survives_the_dict_boundary():
    """
    `from_dict` is the path inbound envelopes actually take, so it is asserted
    separately from the constructor. Before the validator existed, this call
    did raise — on `nonce`, not on trace_id — and a test asserting only "it
    raises" reported the property as enforced when it was not.
    """
    payload = {
        "protocol": "generic-json",
        "sender_participant_ref": {"id": "agent_a", "type": "ai_agent"},
        "receiver_participant_ref": {"id": "agent_b", "type": "ai_agent"},
        "trace_id": "",
        "turn_id": 1,
        "payload": {"user_input": "Hello"},
    }

    with pytest.raises(Exception) as exc_info:
        AgentMessageEnvelope.from_dict(payload)

    assert "trace_id" in str(exc_info.value).lower()
