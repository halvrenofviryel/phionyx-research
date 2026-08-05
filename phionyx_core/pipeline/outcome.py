"""Block outcome recording — the four axes a pipeline block reports on.

`BlockResult.status` answers two questions with one word. ``ok`` covers both
*"ran and found nothing wrong"* and *"did not run, and we continued"*; ``skipped``
covers both a policy bypass under §6 of the kernel execution contract and a
block falling over. MA-4.1 of the Measurement Axioms forbids that conflation.

Four axes, and only one of them is new here:

===================  ============================  ==============================
Axis                 Field                         Answers
===================  ============================  ==============================
Block runtime        :class:`BlockRunStatus`       did the block/evaluator run?
Measurement          ``Measurement.verdict``       what did it establish?
Decision             ``decision_outcome``          what was decided?
Enforcement          ``execution_status``          was the decision carried out?
===================  ============================  ==============================

The last two are the doctrine's own core fields and are not modelled here: they
belong to the turn, not the block. The doctrine's ``execution_status`` describes
the *decision's* enforcement — *"what happened when the decision was carried
out"* — which is why block runtime needed its own axis rather than borrowing it.

**Nothing in this module defaults to a passing value.** An earlier draft
proposed ``measurement_status: str = "PASS"`` on the grounds that it preserved
the meaning of the existing constructions. It does not: the finding that
produced this work is that some existing ``status="ok"`` values never meant
success, so a permissive default copies a false claim into a new field where it
looks authoritative.

Provenance
----------
:class:`Measurement`, :class:`Verdict` and their constructors are vendored from
the frozen Measurement Axioms v1.0 reference implementation at
``docs/publications/spec/measurement-axioms/v1.0/conformance/verdict.py``.
``phionyx_core`` may depend only on the standard library, pydantic and its own
modules, and the specification directory is not packaged into the wheel, so the
reference cannot be imported — it is copied. A differential test drives both
implementations through the same inputs and fails if their behaviour parts. The
frozen copy remains the normative one.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


class CollapseError(TypeError):
    """A measurement was about to be read as something it is not."""


class Verdict(str, Enum):
    """The six-value algebra. Section 3 of the specification."""

    PASS = "PASS"
    FAIL = "FAIL"
    NOT_MEASURED = "NOT_MEASURED"
    INCONCLUSIVE = "INCONCLUSIVE"
    ERROR = "ERROR"
    NOT_APPLICABLE = "NOT_APPLICABLE"

    @property
    def is_passing(self) -> bool:
        return self is Verdict.PASS


class BlockRunStatus(str, Enum):
    """Did the block run? A pipeline fact, not a doctrine dimension.

    Reported under ``profiles.phionyx_pipeline`` rather than in the record's
    core, because it describes one implementation's runtime and the doctrine
    reserves ``profiles`` for exactly that.
    """

    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    NOT_STARTED = "not_started"


class RecoveryAction(str, Enum):
    """What the pipeline did after a block failed to complete.

    Mirrors ``contracts/v4/error_payload.RecoveryAction``. Fail-open is
    legitimate — §7 of the kernel execution contract accepts degrading to safe
    mode — and this is where it is recorded rather than left implicit in a
    passing status.
    """

    RETRY = "retry"
    FALLBACK = "fallback"
    SKIP = "skip"
    ESCALATE = "escalate"
    SHUTDOWN = "shutdown"
    NONE = "none"


class Observation(str, Enum):
    """When the event became observable. MA-4.5."""

    RECORDED = "recorded"
    DETECTED_AFTER_EXECUTION = "detected_after_execution"
    PREVIOUSLY_SILENT_FAILURE = "previously_silent_failure"


NON_MEASUREMENT_CAUSES = frozenset({
    "not_executed", "suppressed_by_tier", "input_absent",
    "input_unreadable", "object_unreachable", "unknown",
})

#: Which outcomes an unmeasured decision may take. MA-4.3 enumerates these
#: three; `attenuate` is absent because attenuating by a stated amount
#: presupposes a measurement.
OUTCOMES_ALLOWED_WHEN_UNMEASURED = frozenset({"block", "escalate", "abstain"})

_DIGEST_LENGTHS = {"sha256": 64, "sha384": 96, "sha512": 128,
                   "blake2b": 128, "blake3": 64}
_DIGEST = re.compile(
    "|".join(f"{alg}:[0-9a-f]{{{n}}}" for alg, n in sorted(_DIGEST_LENGTHS.items())))


def _require_json(value: Any, path: str = "detail",
                  active: set[int] | None = None) -> Any:
    """Return a canonical JSON tree, or raise.

    Validation and conversion in one pass: checking a tree and keeping a
    different one is how a ``UserDict`` that ``isinstance(x, Mapping)`` accepts
    reaches a record the JSON encoder cannot write.
    """
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if math.isfinite(value):
            return value
        raise CollapseError(
            f"{path} is {value!r}: JSON has no literal for it, so a reader "
            "outside this process cannot receive the value you recorded.")
    if isinstance(value, (Mapping, list)):
        if active is None:
            active = set()
        marker = id(value)
        if marker in active:
            raise CollapseError(
                f"{path} refers back to a container that already encloses it. "
                "A cycle has no JSON form, so there is no record to write.")
        active.add(marker)
        try:
            if isinstance(value, Mapping):
                out: dict[str, Any] = {}
                for key, item in value.items():
                    if not isinstance(key, str):
                        raise CollapseError(
                            f"{path} has a non-string key {key!r}. "
                            "Serialisation would convert it, so the record "
                            "would carry a key the caller never wrote.")
                    out[key] = _require_json(item, f"{path}.{key}", active)
                return out
            return [_require_json(x, f"{path}[{i}]", active)
                    for i, x in enumerate(value)]
        finally:
            active.discard(marker)
    if isinstance(value, tuple):
        raise CollapseError(
            f"{path} is a tuple. JSON has one sequence type, so this would be "
            "recorded as a list — a different value from the one passed.")
    raise CollapseError(
        f"{path} is {type(value).__name__}, which has no JSON representation.")


def _freeze(value: Any) -> Any:
    """Make a canonical JSON tree unwritable, all the way down."""
    if isinstance(value, Mapping):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    return value


def _thaw(value: Any) -> Any:
    """Rebuild plain JSON containers for emission, fresh each call."""
    if isinstance(value, Mapping):
        return {k: _thaw(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_thaw(v) for v in value]
    return value


@dataclass(frozen=True)
class ScopeDecision:
    """MA-3.3 — why an object lies outside the assessed scope.

    A free string is not a scope decision: a reader cannot resolve it, so it
    does not distinguish a genuine exclusion from a check that never ran.
    ``resolvable: False`` is honest and it is not NOT_APPLICABLE — an
    unresolvable pointer leaves the exclusion unestablished, which is
    NOT_MEASURED.
    """

    ref: str
    resolvable: bool
    evaluated_version: str | None = None
    content_hash: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.ref, str) or not self.ref.strip():
            raise CollapseError("MA-3.3: a scope decision requires a reference.")
        if not isinstance(self.resolvable, bool):
            raise CollapseError(
                f"resolvable={self.resolvable!r}: this field decides whether "
                "the exclusion is established, so a truthy string is not an "
                "answer.")
        if self.evaluated_version is not None and (
                not isinstance(self.evaluated_version, str)
                or not self.evaluated_version.strip()):
            raise CollapseError("evaluated_version, where given, names a version.")
        if self.content_hash is not None and (
                not isinstance(self.content_hash, str)
                or not _DIGEST.fullmatch(self.content_hash)):
            raise CollapseError(
                f"content_hash={self.content_hash!r}: expected an "
                "algorithm-prefixed lowercase hex digest.")

    def to_record_fields(self) -> dict[str, Any]:
        out: dict[str, Any] = {"ref": self.ref, "resolvable": self.resolvable}
        if self.evaluated_version is not None:
            out["evaluated_version"] = self.evaluated_version
        if self.content_hash is not None:
            out["content_hash"] = self.content_hash
        return out


@dataclass(frozen=True)
class Measurement:
    """One measurement result, in a container that resists collapse.

    No ``__bool__``: truthiness is the commonest route by which NOT_MEASURED
    becomes a pass, because the value is non-null and ``if result:`` succeeds.
    MA-3.5 names it. Asking for the boolean raises rather than guessing.
    """

    verdict: Verdict
    reason: str | None = None
    scope_decision: ScopeDecision | None = None
    items_checked: int | None = None
    #: None means nobody established either way. Recording an unknown as a known
    #: negative is itself a claim that was not measured.
    inputs_present: bool | None = None
    cause: str | None = None
    detail: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.verdict, Verdict):
            raise CollapseError(
                f"verdict={self.verdict!r} is not a Verdict. A string survives "
                "construction and fails at serialisation, which puts the error "
                "in the wrong place: the record is already believed by then.")
        if self.items_checked is not None and (
                isinstance(self.items_checked, bool)
                or not isinstance(self.items_checked, int)):
            raise CollapseError(
                f"items_checked={self.items_checked!r}: a count of examined "
                "objects is an integer. True reads as 1 and 1.5 counts nothing.")
        if self.reason is not None and (
                not isinstance(self.reason, str) or not self.reason.strip()):
            raise CollapseError(
                f"reason={self.reason!r}: an empty one occupies the field "
                "without answering it.")
        if self.scope_decision is not None and not isinstance(
                self.scope_decision, ScopeDecision):
            raise CollapseError(
                f"scope_decision={self.scope_decision!r} is not a ScopeDecision.")
        if self.inputs_present is not None and not isinstance(
                self.inputs_present, bool):
            raise CollapseError(
                f"inputs_present={self.inputs_present!r}: this field carries "
                "present, absent or unknown.")
        if not isinstance(self.detail, Mapping):
            raise CollapseError(
                f"detail={self.detail!r}: detail is a mapping of string keys to "
                "JSON values.")
        object.__setattr__(self, "detail", _freeze(_require_json(self.detail)))

        if self.verdict is Verdict.NOT_APPLICABLE and self.scope_decision is None:
            raise CollapseError(
                "MA-3.3: NOT_APPLICABLE requires a ScopeDecision. Without one "
                "it is NOT_MEASURED wearing a better name.")
        if self.verdict is Verdict.NOT_MEASURED and self.cause is None:
            raise CollapseError(
                "MA-3.11: NOT_MEASURED requires a non_measurement_cause.")
        if self.cause is not None:
            if self.verdict is not Verdict.NOT_MEASURED:
                raise CollapseError(
                    f"a non_measurement_cause is meaningful only with "
                    f"NOT_MEASURED; this record is {self.verdict.value}.")
            if self.cause not in NON_MEASUREMENT_CAUSES:
                raise CollapseError(
                    f"non_measurement_cause={self.cause!r} is not one of "
                    f"{sorted(NON_MEASUREMENT_CAUSES)}.")
            if self.cause in ("input_absent", "input_unreadable"):
                if self.inputs_present is True:
                    raise CollapseError(
                        f"cause={self.cause!r} says the required input could "
                        "not be obtained, and inputs_present=True says it "
                        "could. One of the two was not established.")
                if self.inputs_present is None:
                    object.__setattr__(self, "inputs_present", False)
        if (self.scope_decision is not None
                and self.verdict is not Verdict.NOT_APPLICABLE):
            raise CollapseError(
                "a scope_decision says why an object was not assessed, so it "
                f"belongs only to NOT_APPLICABLE; this is {self.verdict.value}.")
        if self.verdict is Verdict.NOT_APPLICABLE:
            if self.scope_decision is not None and not self.scope_decision.resolvable:
                raise CollapseError(
                    "MA-3.3: the scope decision did not resolve, so the "
                    "exclusion is unestablished.")
            if self.inputs_present is not None:
                raise CollapseError(
                    "MA-3.3: an out-of-scope object was not examined, so the "
                    "record establishes nothing about its input.")
            if self.items_checked is not None:
                raise CollapseError(
                    "MA-3.3: an out-of-scope object was not examined, so there "
                    "is no count to record.")
        if self.inputs_present is False and self.verdict is not Verdict.NOT_MEASURED:
            raise CollapseError(
                f"MA-3.8: inputs_present=False says the required input could "
                f"not be obtained or read, so the status is NOT_MEASURED — not "
                f"{self.verdict.value}.")
        if self.items_checked is not None and self.items_checked < 0:
            raise CollapseError(
                f"items_checked={self.items_checked}: cannot be negative.")
        if self.verdict is Verdict.PASS and self.items_checked == 0:
            raise CollapseError(
                "MA-3.9/MA-6.1: PASS over zero items is a vacuous pass.")

    def __bool__(self) -> bool:  # noqa: D105 - the docstring is the error message
        raise CollapseError(
            f"MA-3.5: a Measurement is not a boolean. This one is "
            f"{self.verdict.value}; truthiness would have made it pass. Test "
            "`m.verdict.is_passing`, and handle NOT_MEASURED, INCONCLUSIVE and "
            "ERROR separately (MA-3.4).")

    def __or__(self, other: Any) -> Any:
        raise CollapseError(
            "MA-3.5: `measurement or default` substitutes a passing value for a "
            "verdict that is not passing. Branch on m.verdict instead.")

    def to_record_fields(self) -> dict[str, Any]:
        """The subset of a decision record this measurement determines."""
        out: dict[str, Any] = {"measurement_status": self.verdict.value}
        if self.reason is not None:
            out["reason"] = self.reason
        if self.scope_decision is not None:
            out["scope_decision"] = self.scope_decision.to_record_fields()
        measured: dict[str, Any] = {}
        if self.inputs_present is not None:
            measured["inputs_present"] = self.inputs_present
        if self.items_checked is not None:
            measured["items_checked"] = self.items_checked
        if measured:
            out["measured"] = measured
        if self.cause is not None:
            out["non_measurement_cause"] = self.cause
        if self.detail:
            out["profiles"] = {"reference_detail": _thaw(self.detail)}
        return out


def measured_pass(items_checked: int, **detail: Any) -> Measurement:
    """The check ran over ``items_checked`` objects and its criterion was met."""
    return Measurement(Verdict.PASS, items_checked=items_checked,
                       inputs_present=True, detail=detail)


def measured_fail(reason: str, items_checked: int | None = None,
                  **detail: Any) -> Measurement:
    """The check ran and its criterion was not met. A measured negative."""
    return Measurement(Verdict.FAIL, reason=reason, inputs_present=True,
                       items_checked=items_checked, detail=detail)


def not_measured(reason: str, *, cause: str = "unknown",
                 inputs_present: bool | None = None, **detail: Any) -> Measurement:
    """No measurement was taken. ``cause`` says why, from a closed vocabulary."""
    return Measurement(Verdict.NOT_MEASURED, reason=reason,
                       inputs_present=inputs_present, cause=cause, detail=detail)


def inconclusive(reason: str, items_checked: int, **detail: Any) -> Measurement:
    """The check ran; the evidence obtained did not decide."""
    return Measurement(Verdict.INCONCLUSIVE, reason=reason, inputs_present=True,
                       items_checked=items_checked, detail=detail)


def errored(reason: str, *, inputs_present: bool | None = None,
            items_checked: int | None = None, **detail: Any) -> Measurement:
    """The check could not complete for a technical reason.

    ``inputs_present`` defaults to None: a crash may occur before the input was
    read, after it was read, or somewhere the caller cannot determine.
    """
    return Measurement(Verdict.ERROR, reason=reason, inputs_present=inputs_present,
                       items_checked=items_checked, detail=detail)


def not_applicable(scope_decision: ScopeDecision, **detail: Any) -> Measurement:
    """Out of scope by a documented, resolvable decision."""
    if not isinstance(scope_decision, ScopeDecision):
        raise CollapseError(
            "MA-3.3: not_applicable() takes a ScopeDecision, not a string.")
    if not scope_decision.resolvable:
        raise CollapseError(
            "MA-3.3: the scope decision did not resolve, so the exclusion is "
            "unestablished. Use not_measured(cause='object_unreachable').")
    return Measurement(Verdict.NOT_APPLICABLE, scope_decision=scope_decision,
                       detail=detail)


# ── The block outcome ───────────────────────────────────────────────────────

#: The versioned adapter named in MA-3.7. A legacy status carries no evidence of
#: what it meant, so every one of the three maps to NOT_MEASURED / unknown. A
#: sharper reading is permitted only where recorded metadata proves it — a
#: `skipped` with policy-tier evidence is `suppressed_by_tier`, an `error` with
#: evaluator-started evidence is ERROR — and is never inferred from the bare
#: string in either direction.
COMPATIBILITY_ADAPTER = "block-result-v1-to-v2/1.0"

_LEGACY_STATUSES = frozenset({"ok", "error", "skipped"})


@dataclass(frozen=True)
class BlockOutcome:
    """What a pipeline block reports, with runtime and measurement separated.

    ``legacy_control_status`` stays as the orchestrator's control channel — it
    decides rollback and always-on handling — and stops being the evidence
    channel.
    """

    block_id: str
    legacy_control_status: str
    block_run_status: BlockRunStatus
    measurement: Measurement
    recovery_action: RecoveryAction = RecoveryAction.NONE
    observation: Observation = Observation.RECORDED
    operating_mode: str = "normal"
    #: Set by :func:`from_legacy`; ``None`` for an outcome a block built itself.
    compatibility_adapter: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.block_id, str) or not self.block_id.strip():
            raise CollapseError("block_id names the block; it must have text.")
        if self.legacy_control_status not in _LEGACY_STATUSES:
            raise CollapseError(
                f"legacy_control_status={self.legacy_control_status!r} is not "
                f"one of {sorted(_LEGACY_STATUSES)}.")
        for name, enum_cls in (("block_run_status", BlockRunStatus),
                               ("recovery_action", RecoveryAction),
                               ("observation", Observation)):
            if not isinstance(getattr(self, name), enum_cls):
                raise CollapseError(f"{name} must be a {enum_cls.__name__}.")
        if not isinstance(self.measurement, Measurement):
            raise CollapseError(
                f"measurement={self.measurement!r} is not a Measurement. The "
                "point of this type is that the status is not a string.")
        if self.operating_mode not in ("normal", "degraded"):
            raise CollapseError(
                f"operating_mode={self.operating_mode!r} is normal or degraded.")
        if (self.operating_mode == "degraded"
                and self.measurement.verdict is Verdict.PASS):
            raise CollapseError(
                "MA-4.4: a bounded degradation is recorded with the honest "
                "measurement status, never as passing.")
        if (self.block_run_status is BlockRunStatus.NOT_STARTED
                and self.measurement.verdict is not Verdict.NOT_MEASURED):
            raise CollapseError(
                "a block that never started measured nothing, so its status is "
                f"NOT_MEASURED — not {self.measurement.verdict.value}.")

    @property
    def mapping_status(self) -> str:
        """Migration state — pipeline metadata, never a measurement value."""
        return "legacy_unmapped" if self.compatibility_adapter else "migrated"

    def to_profile_fields(self) -> dict[str, Any]:
        """The ``profiles.phionyx_pipeline`` block for this outcome."""
        out: dict[str, Any] = {
            "block_id": self.block_id,
            "block_run_status": self.block_run_status.value,
            "recovery_action": self.recovery_action.value,
            "observation": self.observation.value,
            "mapping_status": self.mapping_status,
        }
        if self.compatibility_adapter:
            out["compatibility_adapter"] = self.compatibility_adapter
        return out

    def to_record_fields(self) -> dict[str, Any]:
        """The measurement's core fields, plus the pipeline profile."""
        out = dict(self.measurement.to_record_fields())
        if self.operating_mode != "normal":
            out["operating_mode"] = self.operating_mode
        profiles = dict(out.get("profiles", {}))
        profiles["phionyx_pipeline"] = self.to_profile_fields()
        out["profiles"] = profiles
        return out


def from_legacy(block_id: str, status: str, *,
                skip_reason: str | None = None,
                error: BaseException | None = None) -> BlockOutcome:
    """Read a pre-migration ``BlockResult`` status honestly.

    MA-3.7 asks for a versioned adapter that handles every status explicitly.
    Defaults are not one, and neither is a guess: ``ok`` did not reliably mean
    success — that finding is what produced this module — ``error`` does not
    establish that the evaluator *started*, which is what ERROR asserts, and
    ``skipped`` was written both by a policy bypass and by a block falling over.

    So all three read NOT_MEASURED with cause ``unknown``. An unmigrated block
    says *"nobody has established what this meant"*, which is true, rather than
    PASS, which is a guess in the permissive direction.
    """
    if status not in _LEGACY_STATUSES:
        raise CollapseError(
            f"status={status!r} is not one of {sorted(_LEGACY_STATUSES)}; the "
            "adapter handles every legacy value explicitly and this is not one.")
    reason = (f"legacy status {status!r} carried no evidence of what it "
              f"established (adapter {COMPATIBILITY_ADAPTER})")
    if skip_reason:
        reason = f"{reason}; skip_reason: {skip_reason}"
    elif error is not None:
        reason = f"{reason}; error: {type(error).__name__}"
    run_status = (BlockRunStatus.FAILED if status == "error"
                  else BlockRunStatus.COMPLETED)
    return BlockOutcome(
        block_id=block_id,
        legacy_control_status=status,
        block_run_status=run_status,
        measurement=not_measured(reason, cause="unknown"),
        recovery_action=(RecoveryAction.SKIP if status == "skipped"
                         else RecoveryAction.NONE),
        compatibility_adapter=COMPATIBILITY_ADAPTER,
    )


__all__ = [
    "BlockOutcome", "BlockRunStatus", "COMPATIBILITY_ADAPTER", "CollapseError",
    "Measurement", "NON_MEASUREMENT_CAUSES", "Observation",
    "OUTCOMES_ALLOWED_WHEN_UNMEASURED", "RecoveryAction", "ScopeDecision",
    "Verdict", "errored", "from_legacy", "inconclusive", "measured_fail",
    "measured_pass", "not_applicable", "not_measured",
]
