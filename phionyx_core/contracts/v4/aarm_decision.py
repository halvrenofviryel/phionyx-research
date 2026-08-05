"""AARM R4 — the five authorization decisions, and how Phionyx directives map onto them.

AARM R4 requires a policy engine to be *capable of producing one of five decisions*:
ALLOW, DENY, MODIFY, STEP_UP, DEFER.

Phionyx does not use those names. It has its own vocabulary, arrived at
independently and ordered by severity, and renaming it to match an external
standard would be worse than translating: the internal names carry distinctions
the AARM five do not (``damp`` and ``rewrite`` are different interventions and
the pipeline ranks them differently), and a rename would lose that.

So this module is a **translation layer, not a redefinition**. Nothing here
changes what the gates decide. It states, in one testable place, which AARM
decision each Phionyx directive corresponds to — so that the claim "Phionyx can
produce all five" stops being an assertion and becomes something a test drives.

The mapping spans three components, and that is worth saying plainly rather than
hiding behind a single table:

* ``phionyx_core/pipeline/blocks/response_revision_gate.py`` — the severity-ordered
  five: ``pass`` (0), ``damp`` (1), ``rewrite`` (2), ``regenerate`` (3), ``reject`` (4)
* ``phionyx_core/pipeline/blocks/knowledge_boundary_check.py`` — ``admit_ignorance``
  becomes ``defer_to_human`` when the abstention gate is fail-closed
* the MCP response gate — ``require_tool``, which withholds a pass until evidence
  is externally bound

Known limit, stated because R4 is scored ``partial`` on the strength of it: no
single component produces all five. A system that had to answer AARM with one
enforcement point would not be satisfied by this mapping.
"""

from __future__ import annotations

from enum import Enum


class AARMDecision(str, Enum):
    """The five decisions named in AARM R4."""

    ALLOW = "ALLOW"
    DENY = "DENY"
    MODIFY = "MODIFY"
    STEP_UP = "STEP_UP"
    DEFER = "DEFER"


#: Phionyx directive -> AARM decision.
#:
#: ``damp``, ``rewrite`` and ``regenerate`` all map to MODIFY. They are three
#: distinct interventions internally — attenuate, rewrite in place, produce
#: again — and AARM has one word for all three. The collapse is lossy in our
#: direction, not theirs.
DIRECTIVE_TO_AARM: dict[str, AARMDecision] = {
    # phionyx_core/pipeline/blocks/response_revision_gate.py
    "pass": AARMDecision.ALLOW,
    "damp": AARMDecision.MODIFY,
    "rewrite": AARMDecision.MODIFY,
    "regenerate": AARMDecision.MODIFY,
    "reject": AARMDecision.DENY,
    # MCP response gate
    "block": AARMDecision.DENY,
    "hedge": AARMDecision.MODIFY,
    "require_tool": AARMDecision.STEP_UP,
    # phionyx_core/pipeline/blocks/knowledge_boundary_check.py, fail-closed
    "defer_to_human": AARMDecision.DEFER,
    "admit_ignorance": AARMDecision.DEFER,
    "refuse": AARMDecision.DENY,
}


def to_aarm(directive: str) -> AARMDecision:
    """Translate a Phionyx directive into its AARM R4 decision.

    Raises ``KeyError`` on an unknown directive rather than guessing. A directive
    this module has not been taught is a gap in the mapping, and silently
    returning a default would hide it — which is the failure mode the whole
    evidence map exists to avoid.
    """
    try:
        return DIRECTIVE_TO_AARM[directive]
    except KeyError as exc:  # pragma: no cover - exercised by the test suite
        raise KeyError(
            f"no AARM R4 mapping for directive {directive!r}. "
            "Add it to DIRECTIVE_TO_AARM, or the claim that Phionyx covers the "
            "five AARM decisions no longer holds for this path."
        ) from exc


def covered_decisions() -> set[AARMDecision]:
    """Which of the five AARM decisions the current mapping can produce."""
    return set(DIRECTIVE_TO_AARM.values())


def missing_decisions() -> set[AARMDecision]:
    """The AARM decisions no Phionyx directive currently maps to. Empty is the goal."""
    return set(AARMDecision) - covered_decisions()
