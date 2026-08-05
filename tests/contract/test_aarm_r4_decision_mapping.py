"""AARM R4 — drive the real gate and check the five decisions come out.

R4 requires a policy engine to be capable of producing ALLOW, DENY, MODIFY,
STEP_UP and DEFER. Until this file existed, that claim rested on a table in a
document. A mapping nobody drives is a claim, and the evidence map says so about
itself: R4 is scored ``partial`` partly because of this gap.

These tests do two different jobs and the second is the one that matters:

1. the mapping is total and covers all five (cheap, tests a dict)
2. the *actual* ``_decide`` function, given real state snapshots, emits
   directives that translate to the expected AARM decision (drives the gate)
"""

from __future__ import annotations

import pytest

from phionyx_core.contracts.v4.aarm_decision import (
    AARMDecision,
    covered_decisions,
    missing_decisions,
    to_aarm,
)
from phionyx_core.pipeline.blocks.response_revision_gate import (
    ALL_DIRECTIVES,
    ResponseRevisionGateBlock,
    RevisionThresholds,
)


def _snapshot(**overrides):
    """A state snapshot that passes cleanly, before overrides push it somewhere."""
    # The eleven keys _decide actually reads, taken from the source rather than
    # guessed. An incomplete snapshot raises KeyError, which is the gate being
    # strict about its own inputs and is the right behaviour.
    base = {
        "entropy": 0.0,
        "coherence": 1.0,
        "coherence_leak": False,
        "phi": 1.0,
        "ethics_risk": 0.0,
        "ethics_enforced": False,
        "confidence": 1.0,
        "conflict_score": 0.0,
        "arbitration_strategy": None,
        "drift_score": 0.0,
        "cep_flagged": False,
    }
    base.update(overrides)
    return base


# --- 1. the mapping itself -----------------------------------------------


def test_all_five_aarm_decisions_are_reachable():
    assert missing_decisions() == set(), (
        f"AARM R4 names five decisions; the mapping reaches "
        f"{sorted(d.value for d in covered_decisions())}"
    )


def test_every_pipeline_directive_has_a_mapping():
    """A directive the mapping has not been taught is a hole in the R4 claim."""
    for directive in ALL_DIRECTIVES:
        to_aarm(directive)  # raises KeyError if unmapped


def test_unknown_directive_raises_rather_than_defaulting():
    """Silently defaulting would hide exactly the gap this file exists to close."""
    with pytest.raises(KeyError):
        to_aarm("a_directive_that_does_not_exist")


# --- 2. drive the real gate ----------------------------------------------


@pytest.mark.parametrize(
    "label, state, expected",
    [
        ("clean state", _snapshot(), AARMDecision.ALLOW),
        ("entropy over the damp threshold", _snapshot(entropy=0.75), AARMDecision.MODIFY),
        ("entropy over the rewrite threshold", _snapshot(entropy=0.90), AARMDecision.MODIFY),
        ("phi below the floor", _snapshot(phi=0.01), AARMDecision.MODIFY),
        ("entropy over the reject threshold", _snapshot(entropy=0.99), AARMDecision.DENY),
        ("coherence collapse", _snapshot(coherence=0.10), AARMDecision.DENY),
        ("ethics risk over reject", _snapshot(ethics_risk=0.90), AARMDecision.DENY),
    ],
)
def test_gate_emits_directives_that_map_to_the_expected_aarm_decision(label, state, expected):
    block = ResponseRevisionGateBlock(thresholds=RevisionThresholds())
    result = block._decide(state)
    assert to_aarm(result.directive) is expected, (
        f"{label}: gate emitted {result.directive!r} "
        f"-> {to_aarm(result.directive).value}, expected {expected.value}. "
        f"reasons={result.reasons}"
    )


def test_severity_ordering_survives_translation():
    """A worse internal directive must never translate to a more permissive AARM decision."""
    permissiveness = {
        AARMDecision.ALLOW: 0,
        AARMDecision.MODIFY: 1,
        AARMDecision.STEP_UP: 2,
        AARMDecision.DEFER: 2,
        AARMDecision.DENY: 3,
    }
    block = ResponseRevisionGateBlock(thresholds=RevisionThresholds())
    clean = to_aarm(block._decide(_snapshot()).directive)
    worst = to_aarm(block._decide(_snapshot(entropy=0.99, coherence=0.05)).directive)
    assert permissiveness[worst] > permissiveness[clean]


# --- 3. what this file does NOT establish --------------------------------


def test_no_single_component_produces_all_five():
    """Recorded as a test so the limit cannot quietly disappear.

    STEP_UP comes from the MCP response gate and DEFER from the knowledge
    boundary block; neither is reachable from the revision gate alone. AARM R4
    speaks of "the policy engine" in the singular. This is why R4 is scored
    partial in AARM_EVIDENCE_MAP.md rather than supported.
    """
    from_revision_gate = {to_aarm(d) for d in ALL_DIRECTIVES}
    assert AARMDecision.STEP_UP not in from_revision_gate
    assert AARMDecision.DEFER not in from_revision_gate
