"""Reading an ethics processor's return value as a measurement.

Shared by ``ethics_pre_response`` (canonical 17) and ``ethics_post_response``
(canonical 21), which take the same shape of result from the same processor
family. One reader rather than two so the two blocks cannot drift into
disagreeing about what an ethics result means.

The processors are injected and their payloads vary — a mapping with a
``status``, a mapping carrying only risk scores, an object with attributes.
This reads what is there and says ``NOT_MEASURED`` when what is there does not
settle the question, rather than defaulting to the clear side. The previous
code defaulted a missing ``status`` to ``"ok"``.
"""
from __future__ import annotations

from typing import Any, Optional

from .outcome import Measurement, measured_fail, measured_pass, not_measured

#: Values of an ethics result's ``status`` that mean the check was satisfied.
CLEAR_STATUSES = frozenset({"ok", "pass", "passed", "clear", "cleared", "allowed"})


def _field(result: Any, name: str) -> Any:
    """Read ``name`` from a mapping or an object, without inventing a default."""
    if isinstance(result, dict):
        return result.get(name)
    return getattr(result, name, None)


def _risk(result: Any) -> Optional[float]:
    for name in ("max_risk_score", "risk_level", "harm_risk", "risk_score"):
        value = _field(result, name)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
    return None


def measure_ethics(result: Any, *, evaluator: str) -> Measurement:
    """What the ethics result establishes, and nothing more.

    Args:
        result: whatever the injected processor returned, or ``None``.
        evaluator: the block id, for the recorded reason.
    """
    if result is None:
        return not_measured(
            f"{evaluator}: no ethics evaluator produced a result",
            cause="not_executed")

    detail: dict[str, Any] = {"evaluator": evaluator}
    risk = _risk(result)
    if risk is not None:
        detail["risk"] = risk

    if _field(result, "enforced") is True:
        return measured_fail("ethics enforcement was triggered",
                             items_checked=1, **detail)

    status = _field(result, "status")
    if status is None:
        # A risk score on its own does not carry the evaluator's verdict, and
        # there is no threshold here to apply to it — that belongs to the
        # evaluator. Reading "no status" as "clear" is what this removes.
        return not_measured(
            f"{evaluator}: the ethics result carries no status",
            cause="unknown", **detail)

    if str(status).strip().lower() in CLEAR_STATUSES:
        return measured_pass(1, status=str(status), **detail)

    return measured_fail(f"ethics status {str(status)!r} is not a clear result",
                         items_checked=1, status=str(status), **detail)
