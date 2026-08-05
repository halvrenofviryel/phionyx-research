"""
Response Revision Gate Block
============================

Block: response_revision_gate
Purpose: Close the in-turn state → response feedback loop.

This block consumes final-turn state measurements (phi, entropy, confidence,
arbitration conflict, drift, ethics post-result, CEP flags) AFTER all state
computation blocks but BEFORE ``response_build``. It does NOT rewrite the
narrative itself — it only emits a ``revision_directive`` that downstream
blocks (``response_build``, ``narrative_layer`` re-entry) consume.

Claim references:
    - SF1 Claim 1  — deterministic recovery / state-based control
    - SF1 Claim 4  — post state-update, pre response-build position
    - SF1 Claim 9  — failure classification (entropy, coherence, ethics, corruption)
    - SF1 Claim 15 — LLM output treated as sensor, evaluated deterministically
    - SF1 Claim 18 — kernel + state + recovery inseparability
    - SF2 Claim 1  — pre-response amplitude damping + entropy floor
    - SF2 Claim 11 — governance at state level, not post-generation filtering

This block **is** canonical block 41 of v3.8.0, immediately before
``response_build``. (An earlier version of this docstring said it was "NOT wired
into any canonical order"; checked against
``contracts/telemetry/canonical_blocks_v3_8_0.json`` on 2026-08-02, it is.)

Class (P-5): **safety / ethics authority.** It is the only block that can
replace the whole user-visible response — ``response_build`` turns a ``reject``
directive into a refusal. It was recorded as quality/revision in the silent-
failure inventory; that classification was made without reading it.

**Failure policy (P-4).** On an exception this block emits **no directive** and
records ``ERROR``. It does not emit ``pass``: an unmeasured gate must not
produce an authorising verdict, and ``OUTCOMES_ALLOWED_WHEN_UNMEASURED`` is
``{block, escalate, abstain}``. Nor does it emit ``reject``, which would record
a *measured* violation when what happened was a crash — the same collapse with
the opposite sign, and one that produces a refusal with an empty ``reasons``
list. ``FAIL`` and ``ERROR`` are distinct verdicts precisely so this cannot be
written. The turn-level consequence of a required gate that did not measure
belongs to the envelope (P-6), not to a blanked answer here.

**Criteria are applied only when their inputs are present.** Every default in
the old ``_extract_state`` sat on the non-triggering side of its threshold
(φ 0.5 vs a 0.05 floor, coherence 1.0 vs 0.50/0.30, confidence 1.0 vs
0.35/0.50, conflict and drift 0.0 vs 0.60), so a criterion with no input could
never fire — it only made the record say the criterion had been checked and
found clean. Skipping it instead yields the identical directive and an honest
count. Measured on 2026-08-02 by AST across all 46 canonical blocks, five of the
nine keys this gate reads have **no canonical producer**, for three different
reasons:

- ``confidence_result``, ``arbitration_result``, ``drift_result`` — the
  producing blocks exist and run, but write flat keys (``w_final``,
  ``conflict_score``, ``drift_report``). A key-name mismatch.
- ``coherence_qa_result`` — its only writer is ``blocks/archive/coherence_qa.py``,
  which is not among the 46. Coherence is genuinely not computed in v3.8.0.
- ``ethics_post_result`` — written by nothing at all; the ``or`` falls through
  to ``ethics_result``, which the two ethics blocks do write. Both names are
  read here: the first is what the patent-claim tests supply, the second is
  what the pipeline produces.

Repairing any of these activates rules that have never fired on a real turn, so
each is a separate decision taken one signal at a time. Nothing is removed here.
Until then the record reports those criteria as not measured rather than as
passed, which is what makes the gap countable.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from typing import AbstractSet, Any, Dict, Mapping, Optional

from ..base import BlockContext, BlockResult, PipelineBlock
from ..outcome import (
    BlockOutcome,
    BlockRunStatus,
    Measurement,
    Observation,
    RecoveryAction,
    errored,
    measured_fail,
    measured_pass,
    not_measured,
)

logger = logging.getLogger(__name__)

#: The criteria this gate evaluates. Named so `items_checked` counts something
#: that exists rather than a denominator invented at the call site (MA-3.9).
CRITERIA = ("entropy", "coherence", "phi", "ethics",
            "conflict", "confidence", "drift", "cep")


# Directive constants (enum-like to keep stdlib-only).
DIRECTIVE_PASS = "pass"
DIRECTIVE_DAMP = "damp"
DIRECTIVE_REWRITE = "rewrite"
DIRECTIVE_REGENERATE = "regenerate"
DIRECTIVE_REJECT = "reject"

ALL_DIRECTIVES = (
    DIRECTIVE_PASS,
    DIRECTIVE_DAMP,
    DIRECTIVE_REWRITE,
    DIRECTIVE_REGENERATE,
    DIRECTIVE_REJECT,
)


@dataclass
class RevisionThresholds:
    """
    Configurable thresholds for revision decisions.

    Defaults are derived from the preferred embodiments in:
      - SF1 Claim 6  (entropy threshold = 0.5 for dual-regime penalty)
      - SF1 Claim 21A (phi_min_floor = 0.05)
      - SF1 Claim 9  (failure classification thresholds)
      - SF2 Claim 1  (risk-vector thresholds)
    """

    # SF1 C9: entropy overflow
    entropy_damp: float = 0.70     # apply amplitude damping above this
    entropy_rewrite: float = 0.85  # force rewrite above this
    entropy_reject: float = 0.95   # hard reject above this

    # SF1 C9: coherence violation (lower is worse)
    coherence_rewrite: float = 0.50
    coherence_reject: float = 0.30

    # SF1 C21A: phi floor
    phi_min: float = 0.05          # if phi collapses below, regenerate

    # SF1 C9: ethics risk escalation
    ethics_risk_rewrite: float = 0.60
    ethics_risk_reject: float = 0.85

    # Arbitration (SF1 C11 / SF2 arbitration)
    conflict_rewrite: float = 0.60
    conflict_reject: float = 0.85

    # Confidence fusion (higher is better)
    confidence_regenerate: float = 0.35  # low confidence → regenerate
    confidence_rewrite: float = 0.50     # medium-low → rewrite

    # Drift
    drift_rewrite: float = 0.60

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


@dataclass
class RevisionDirective:
    """Structured directive emitted by the revision gate."""

    directive: str = DIRECTIVE_PASS
    reasons: list = field(default_factory=list)
    damp_factor: Optional[float] = None   # only set for DAMP
    entropy_floor: Optional[float] = None  # SF2 C1 entropy floor when damping
    state_snapshot: Dict[str, Any] = field(default_factory=dict)
    claim_refs: tuple = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["claim_refs"] = list(self.claim_refs)
        return d


def _severity_rank(directive: str) -> int:
    """Order directives by severity — used to pick the most severe trigger."""
    order = {
        DIRECTIVE_PASS: 0,
        DIRECTIVE_DAMP: 1,
        DIRECTIVE_REWRITE: 2,
        DIRECTIVE_REGENERATE: 3,
        DIRECTIVE_REJECT: 4,
    }
    return order.get(directive, 0)


def _compute_damp_factor(entropy: float, thresholds: RevisionThresholds) -> float:
    """
    SF2 Claim 8 style exponential damping curve.

    damp_factor = base ** (entropy / entropy_damp)
    Bounded to [0.1, 1.0]. Lower factor = more aggressive damping.
    """
    if entropy <= thresholds.entropy_damp:
        return 1.0
    base = 0.5
    ratio = entropy / max(thresholds.entropy_damp, 1e-6)
    factor = base ** ratio
    return max(0.1, min(1.0, factor))


class ResponseRevisionGateBlock(PipelineBlock):
    """
    Response Revision Gate — closes in-turn state → response feedback loop.

    Reads final-turn state metrics and emits a ``revision_directive`` consumed
    by ``response_build`` (or, for ``regenerate``, by the orchestrator to
    re-enter ``narrative_layer``).

    Emits (via BlockResult.data and context.metadata["revision_directive"]):
        - ``directive``: one of pass / damp / rewrite / regenerate / reject
        - ``reasons``: list of human-readable triggers
        - ``damp_factor``: suggested amplitude multiplier (damp only)
        - ``entropy_floor``: enforced minimum entropy (damp only)
        - ``state_snapshot``: the inputs used for the decision
        - ``claim_refs``: patent claim bindings for audit

    This block DOES NOT modify ``narrative_text``. It only decides.
    Execution of the directive is the downstream block's responsibility.
    """

    CLAIM_REFS = (
        "SF1:C1", "SF1:C4", "SF1:C9", "SF1:C15", "SF1:C18",
        "SF2:C1", "SF2:C11",
    )

    def __init__(self, thresholds: Optional[RevisionThresholds] = None):
        super().__init__("response_revision_gate", claim_refs=self.CLAIM_REFS)
        self.thresholds = thresholds or RevisionThresholds()

    def should_skip(self, context: BlockContext) -> Optional[str]:
        """Never skip — missing signals are handled by the decision logic."""
        return None

    # ----- decision helpers -------------------------------------------------

    @staticmethod
    def _number(source: Any, *names: str) -> Optional[float]:
        """The first of `names` carrying a number, or ``None``.

        ``None`` and not a default: a signal that is absent is not a signal that
        is good, and every default this replaced sat on the passing side.
        Reads mappings and objects alike, because one of the confidence sources
        is a `ConfidencePayload` rather than a dict. Booleans are excluded —
        `isinstance(True, int)` is True in Python, and a flag where a score
        belongs is malformed input rather than a score of 1.0.
        """
        for name in names:
            value = (source.get(name) if isinstance(source, Mapping)
                     else getattr(source, name, None))
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue
            return float(value)
        return None

    def _extract_state(
        self, context: BlockContext
    ) -> tuple[Dict[str, Any], set[str], str]:
        """Collect the state signals this gate cares about.

        Returns the snapshot and the set of `CRITERIA` whose inputs were
        actually found. The snapshot keeps its previous shape and its previous
        placeholder values so `state_snapshot` and direct `_decide` callers are
        unaffected; the presence set is what stops an absent input from being
        recorded as a clean check.
        """
        metadata = context.metadata or {}
        physics_state = metadata.get("physics_state") or {}
        if not isinstance(physics_state, Mapping):
            physics_state = {}
        present: set[str] = set()

        # Phi: prefer computed phi, fall back to physics_state.phi
        phi = self._number(metadata, "phi")
        if phi is None:
            phi = self._number(physics_state, "phi")
        if phi is not None:
            present.add("phi")

        # Entropy: computed this turn, then physics_state, then the context's
        # running value. The third is not a measurement made this turn —
        # `BlockContext.current_entropy` is a non-optional field defaulting to
        # 0.5, so a turn where `entropy_computation` never ran is
        # indistinguishable from one where it produced 0.5. The block can still
        # evaluate it, so the rule still applies and the directive is unchanged;
        # what the record does is name the source rather than imply a fresh
        # measurement.
        entropy_source = "metadata"
        entropy = self._number(metadata, "entropy")
        if entropy is None:
            entropy, entropy_source = self._number(physics_state, "entropy"), "physics_state"
        if entropy is None and isinstance(context.current_entropy, (int, float)):
            entropy, entropy_source = float(context.current_entropy), "carried_state"
        if entropy is not None:
            present.add("entropy")
        else:
            entropy_source = "absent"

        # Coherence — no canonical producer today; see the module docstring
        coherence_result = metadata.get("coherence_qa_result")
        coherence = self._number(coherence_result, "coherence_score")
        leak_detected = bool(
            isinstance(coherence_result, Mapping)
            and coherence_result.get("leak_detected")
        )
        if coherence is not None or (isinstance(coherence_result, Mapping)
                                     and "leak_detected" in coherence_result):
            present.add("coherence")

        # Ethics. `ethics_post_result` has no canonical producer — the `or`
        # falls through to `ethics_result`, which `ethics_pre_response` and
        # `ethics_post_response` do write. Both are kept: the first is the key
        # the patent-claim tests supply and the documented name, the second is
        # what the pipeline actually writes. Choosing one is part of the
        # key-naming decision, not of this record-only change.
        ethics_result = metadata.get("ethics_post_result") or metadata.get("ethics_result")
        ethics_enforced = bool(
            isinstance(ethics_result, Mapping) and ethics_result.get("enforced")
        )
        ethics_risk = self._number(ethics_result, "risk_score") or 0.0
        if isinstance(ethics_result, Mapping) and ethics_result:
            present.add("ethics")

        # Arbitration. `arbitration_result` is the documented key and nothing
        # writes it; `arbitration_resolve` (canonical 40) writes `conflict_score`
        # and `resolution_strategy` flat. Repair 2, second half — wired only
        # after `compute_conflict_score` was corrected on 2026-08-02, because
        # the previous `1 - HHI` formula scored module *agreement* at 0.667 and
        # would have rewritten responses whenever the modules concurred.
        arb_result = metadata.get("arbitration_result")
        conflict_score = self._number(arb_result, "conflict_score")
        if isinstance(arb_result, Mapping) and conflict_score is not None:
            arbitration_strategy = str(arb_result.get("resolution_strategy", "none"))
            present.add("conflict")
        else:
            conflict_score = self._number(metadata, "conflict_score")
            arbitration_strategy = str(metadata.get("resolution_strategy", "none"))
            if conflict_score is not None:
                present.add("conflict")
        if conflict_score is None:
            conflict_score = 0.0

        # Confidence. Three sources, in order of directness:
        #   1. `confidence_result` — the documented key and what the
        #      patent-claim tests supply. No canonical block writes it.
        #   2. `w_final` — what `confidence_fusion` (canonical 39) actually
        #      writes, and the repair: until 2026-08-02 this gate read a key
        #      nobody wrote, so its two confidence rules never fired.
        #   3. `context.v4_confidence` — the payload the same block sets.
        # The old code read `W_final` off that payload. No object in this
        # repository has that attribute; `ConfidencePayload`'s field is
        # `confidence_score` and `ArbitrationResult`'s is `w_final`. So the
        # fallback was unreachable *and* pointed at nothing.
        confidence = self._number(metadata.get("confidence_result"), "confidence")
        if confidence is None:
            confidence = self._number(metadata, "w_final")
        if confidence is None and context.v4_confidence is not None:
            confidence = self._number(context.v4_confidence,
                                      "confidence_score", "w_final")
        if confidence is not None:
            present.add("confidence")

        # Drift. `drift_result` is the documented key and nothing writes it;
        # `behavioral_drift_detection` (canonical 23) writes `drift_score`
        # flat. Repair 3. That block only publishes the key when its detector
        # had a baseline — a report built without one carries drift_score 0.0
        # and confidence 0.0, and publishing it would have made this criterion
        # read as checked-and-clean on every baseline-less turn.
        drift_score = self._number(metadata.get("drift_result"), "drift_score")
        if drift_score is None:
            drift_score = self._number(metadata, "drift_score")
        if drift_score is not None:
            present.add("drift")

        # CEP flags
        cep_flags = metadata.get("cep_flags")
        cep_flagged = bool(
            isinstance(cep_flags, Mapping)
            and (cep_flags.get("self_narrative") or cep_flags.get("trauma_language"))
        )
        if isinstance(cep_flags, Mapping) and cep_flags:
            present.add("cep")

        return {
            "phi": 0.5 if phi is None else float(phi),
            "entropy": 0.0 if entropy is None else float(entropy),
            "coherence": 1.0 if coherence is None else float(coherence),
            "coherence_leak": leak_detected,
            "ethics_enforced": ethics_enforced,
            "ethics_risk": ethics_risk,
            "conflict_score": conflict_score,
            "arbitration_strategy": arbitration_strategy,
            "confidence": 1.0 if confidence is None else float(confidence),
            "drift_score": 0.0 if drift_score is None else float(drift_score),
            "cep_flagged": cep_flagged,
        }, present, entropy_source

    def _decide(self, s: Mapping[str, Any],
                present: Optional[AbstractSet[str]] = None) -> RevisionDirective:
        """Pure decision function over the extracted state snapshot.

        `present` names the `CRITERIA` whose inputs were actually found. It
        defaults to *all of them*, so a caller that hands over a complete
        snapshot — as the contract and Echoism tests do — gets exactly the
        previous behaviour.
        """
        t = self.thresholds
        reasons: list = []
        current = DIRECTIVE_PASS
        measured = set(CRITERIA) if present is None else set(present)

        def escalate(candidate: str, reason: str) -> None:
            nonlocal current
            if _severity_rank(candidate) > _severity_rank(current):
                current = candidate
            reasons.append(reason)

        # SF1 C9: entropy overflow
        if "entropy" in measured:
            if s["entropy"] >= t.entropy_reject:
                escalate(DIRECTIVE_REJECT, f"entropy>={t.entropy_reject}")
            elif s["entropy"] >= t.entropy_rewrite:
                escalate(DIRECTIVE_REWRITE, f"entropy>={t.entropy_rewrite}")
            elif s["entropy"] >= t.entropy_damp:
                escalate(DIRECTIVE_DAMP, f"entropy>={t.entropy_damp}")

        # SF1 C9: coherence violation
        if "coherence" in measured:
            if s["coherence"] <= t.coherence_reject:
                escalate(DIRECTIVE_REJECT, f"coherence<={t.coherence_reject}")
            elif s["coherence"] <= t.coherence_rewrite:
                escalate(DIRECTIVE_REWRITE, f"coherence<={t.coherence_rewrite}")
            if s["coherence_leak"]:
                escalate(DIRECTIVE_REWRITE, "coherence_leak_detected")

        # SF1 C21A: phi floor
        if "phi" in measured and s["phi"] < t.phi_min:
            escalate(DIRECTIVE_REGENERATE, f"phi<{t.phi_min}")

        # SF1 C9: ethics risk escalation
        if "ethics" in measured:
            if s["ethics_risk"] >= t.ethics_risk_reject:
                escalate(DIRECTIVE_REJECT, f"ethics_risk>={t.ethics_risk_reject}")
            elif s["ethics_risk"] >= t.ethics_risk_rewrite:
                escalate(DIRECTIVE_REWRITE, f"ethics_risk>={t.ethics_risk_rewrite}")
            elif s["ethics_enforced"]:
                escalate(DIRECTIVE_DAMP, "ethics_enforced")

        # Arbitration conflict
        if "conflict" in measured:
            if s["conflict_score"] >= t.conflict_reject:
                escalate(DIRECTIVE_REJECT, f"conflict>={t.conflict_reject}")
            elif s["conflict_score"] >= t.conflict_rewrite:
                escalate(DIRECTIVE_REWRITE, f"conflict>={t.conflict_rewrite}")
            if s["arbitration_strategy"] == "safety_override":
                escalate(DIRECTIVE_DAMP, "arbitration_safety_override")

        # Confidence fusion (lower triggers regenerate)
        if "confidence" in measured:
            if s["confidence"] <= t.confidence_regenerate:
                escalate(DIRECTIVE_REGENERATE,
                         f"confidence<={t.confidence_regenerate}")
            elif s["confidence"] <= t.confidence_rewrite:
                escalate(DIRECTIVE_REWRITE, f"confidence<={t.confidence_rewrite}")

        # Drift
        if "drift" in measured and s["drift_score"] >= t.drift_rewrite:
            escalate(DIRECTIVE_REWRITE, f"drift>={t.drift_rewrite}")

        # CEP flagged
        if "cep" in measured and s["cep_flagged"]:
            escalate(DIRECTIVE_REWRITE, "cep_flagged")

        damp_factor: Optional[float] = None
        entropy_floor: Optional[float] = None
        if current == DIRECTIVE_DAMP:
            damp_factor = _compute_damp_factor(s["entropy"], t)
            # SF2 C9: entropy floor = max(current_entropy, min_threshold)
            entropy_floor = max(s["entropy"], t.entropy_damp)

        return RevisionDirective(
            directive=current,
            reasons=reasons,
            damp_factor=damp_factor,
            entropy_floor=entropy_floor,
            state_snapshot=dict(s),
            claim_refs=self.CLAIM_REFS,
        )

    # ----- execute ----------------------------------------------------------

    def _measure(self, directive_obj: RevisionDirective,
                 present: AbstractSet[str],
                 entropy_source: str = "metadata") -> Measurement:
        """What the gate established, counted over criteria that had inputs."""
        if not present:
            return not_measured(
                "no revision signal was present on the turn — none of "
                f"{', '.join(CRITERIA)} had an input",
                cause="input_absent")
        detail = {"criteria_measured": ",".join(sorted(present)),
                  "entropy_source": entropy_source,
                  "criteria_absent": ",".join(sorted(set(CRITERIA) - set(present)))}
        if directive_obj.directive == DIRECTIVE_PASS:
            return measured_pass(len(present), **detail)
        return measured_fail(
            f"{directive_obj.directive}: {', '.join(directive_obj.reasons)}",
            items_checked=len(present), directive=directive_obj.directive, **detail)

    async def execute(self, context: BlockContext) -> BlockResult:
        try:
            state, present, entropy_source = self._extract_state(context)
            directive_obj = self._decide(state, present)

            metadata = context.metadata or {}
            metadata["revision_directive"] = directive_obj.to_dict()
            context.metadata = metadata

            if directive_obj.directive != DIRECTIVE_PASS:
                logger.info(
                    "response_revision_gate: directive=%s reasons=%s",
                    directive_obj.directive,
                    directive_obj.reasons,
                )

            outcome = BlockOutcome(
                block_id=self.block_id,
                legacy_control_status="ok",
                block_run_status=BlockRunStatus.COMPLETED,
                measurement=self._measure(directive_obj, present,
                                          entropy_source),
            )
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={**directive_obj.to_dict(),
                      "block_outcome": outcome.to_record_fields()},
            )
        except Exception as e:  # pragma: no cover - defensive
            logger.error("response_revision_gate failed: %s", e, exc_info=True)
            # No directive. `pass` would be an authorising verdict produced by a
            # crash; `reject` would record a measured violation that never
            # happened, and would refuse the user with an empty `reasons` list.
            # The gate emitted nothing, so nothing is emitted — `response_build`
            # finds no `revision_directive` and proceeds, which is exactly what
            # it did before, since the old error path never wrote that key
            # either. What changes is that the record now says ERROR.
            outcome = BlockOutcome(
                block_id=self.block_id,
                legacy_control_status="skipped",
                block_run_status=BlockRunStatus.FAILED,
                measurement=errored(
                    f"revision decision raised {type(e).__name__}: {e}"),
                recovery_action=RecoveryAction.FALLBACK,
                observation=Observation.RECORDED,
                operating_mode="degraded",
            )
            return BlockResult(
                block_id=self.block_id,
                status="skipped",
                skip_reason=f"revision decision raised {type(e).__name__}",
                error=e,
                data={
                    "reasons": [],
                    "error": str(e),
                    "claim_refs": list(self.CLAIM_REFS),
                    "block_outcome": outcome.to_record_fields(),
                },
            )
