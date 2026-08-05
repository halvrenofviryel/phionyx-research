"""Every canonical block's failure path records what happened.

2026-08-02. The Measurement Axioms separate two things a block reports:

- the **control channel** — did the pipeline continue? `status="ok"` means the
  block ran to completion, and it is what the orchestrator reads;
- the **measurement** — what did the block actually establish? PASS, FAIL,
  NOT_MEASURED, INCONCLUSIVE, ERROR or NOT_APPLICABLE.

Collapsing them is the defect this whole inventory is about. A block that
raised an exception and returned `status="ok"` reported a pass nobody made,
because telemetry reads `is_success()`. Twenty-five blocks did that.

The fix is *not* to make every block fail the pipeline. Most of these are
deliberately fail-open — a crash in phi publishing should not lose the user's
turn — and changing that is a behaviour decision, not a reporting fix. What
changed is that the record now says `block_run_status: FAILED`,
`measurement.verdict: ERROR` and `operating_mode: degraded`, so the two
channels can disagree out loud instead of one silently speaking for the other.

This test asserts that alignment holds for every canonical block that has an
exception path, by importing the module and reading its source — so a new
block, or a regression in an existing one, fails here rather than being found
by the next audit.
"""
from __future__ import annotations

import ast
import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
BLOCKS_DIR = ROOT / "phionyx_core" / "pipeline" / "blocks"
CONTRACT = (ROOT / "phionyx_core" / "contracts" / "telemetry"
            / "canonical_blocks_v3_8_0.json")


def _canonical_names() -> list[str]:
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    return [b if isinstance(b, str) else b["name"]
            for b in data["canonical_block_order"]]


def _module_for(block_name: str) -> pathlib.Path | None:
    path = BLOCKS_DIR / f"{block_name}.py"
    return path if path.exists() else None


def _handlers_returning_ok(path):
    """Exception handlers whose fail-open return is a BlockResult(status ok).

    Widened 2026-08-04. The first version matched only a DIRECT
    `return BlockResult(status="ok")` statement inside the handler. Blocks
    written as

        _result = BlockResult(block_id=..., status="ok", data={...})
        return _result

    were invisible to it, and that shape is not hypothetical — it was written
    during this very migration and made a fix invisible to its own guard. The
    gate skipped 54 of its cases saying "no fail-open exception path" while an
    independent AST scan found an except handler in all 46 blocks, so the gate
    was under-reporting the work it existed to measure.

    `status="skipped"` counts too: context_retrieval_rag and cep_evaluation
    were deliberately moved from "ok" to "skipped" so a crash stops reading as
    a clean pass. That is still a fail-open return and still needs a record.
    """
    import ast

    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = []
    for handler in [n for n in ast.walk(tree)
                    if isinstance(n, ast.ExceptHandler)]:
        assigned = {}
        for node in ast.walk(handler):
            if (isinstance(node, ast.Assign)
                    and isinstance(node.value, ast.Call)
                    and getattr(node.value.func, "id", "") == "BlockResult"):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        assigned[target.id] = node.value
        for node in ast.walk(handler):
            if not isinstance(node, ast.Return) or node.value is None:
                continue
            call = None
            if (isinstance(node.value, ast.Call)
                    and getattr(node.value.func, "id", "") == "BlockResult"):
                call = node.value
            elif (isinstance(node.value, ast.Name)
                  and node.value.id in assigned):
                call = assigned[node.value.id]
            if call is None:
                continue
            for kw in call.keywords:
                if (kw.arg == "status"
                        and getattr(kw.value, "value", None) in ("ok", "skipped")):
                    found.append(call)
    return found


CANONICAL = _canonical_names()
WITH_MODULES = [n for n in CANONICAL if _module_for(n) is not None]


class TestTheContractIsWhatWeThinkItIs:
    def test_the_canonical_order_is_46_blocks(self) -> None:
        assert len(CANONICAL) == 46
        assert len(set(CANONICAL)) == 46, "a name appears twice"

    def test_most_canonical_blocks_have_a_module_of_their_own(self) -> None:
        """Named so the next assertion's denominator is not a guess."""
        missing = [n for n in CANONICAL if _module_for(n) is None]

        assert len(WITH_MODULES) >= 40, (
            f"only {len(WITH_MODULES)} of 46 canonical blocks resolve to a "
            f"module in blocks/; missing: {missing}")


class TestEveryFailOpenHandlerRecordsTheFailure:
    """The alignment itself, one canonical block at a time."""

    @pytest.mark.parametrize("block_name", WITH_MODULES)
    def test_a_fail_open_handler_carries_a_block_outcome(
        self, block_name: str
    ) -> None:
        path = _module_for(block_name)
        assert path is not None
        handlers = _handlers_returning_ok(path)
        if not handlers:
            pytest.skip(f"{block_name} has no fail-open exception path")

        source = path.read_text(encoding="utf-8")

        assert "BlockOutcome(" in source, (
            f"{block_name} returns status='ok' from an exception handler and "
            "builds no BlockOutcome. The pipeline continuing is fine; the "
            "record claiming a measurement that never happened is not. See "
            "phionyx_core/pipeline/outcome.py and the migrated blocks for the "
            "shape.")
        assert "BlockRunStatus.FAILED" in source, (
            f"{block_name} records a BlockOutcome but never marks the run "
            "FAILED, so the control channel still speaks for the measurement")
        assert "errored(" in source, (
            f"{block_name} does not report an ERROR verdict on its exception "
            "path. NOT_MEASURED is for an input that was absent; a raised "
            "exception is ERROR.")
        assert 'operating_mode="degraded"' in source, (
            f"{block_name} does not mark the turn degraded, so a consumer "
            "cannot tell this turn apart from one where everything worked")

    @pytest.mark.parametrize("block_name", WITH_MODULES)
    def test_the_outcome_reaches_the_result_data(self, block_name: str) -> None:
        """A record nothing carries is a comment.

        `block_outcome` has to be in the returned data, or the honest verdict
        never leaves the block and telemetry reads `is_success()` as before.
        """
        path = _module_for(block_name)
        assert path is not None
        if not _handlers_returning_ok(path):
            pytest.skip(f"{block_name} has no fail-open exception path")

        source = path.read_text(encoding="utf-8")

        assert "block_outcome" in source, (
            f"{block_name} builds an outcome and does not put it in the "
            "result data")
        assert "to_record_fields()" in source, (
            f"{block_name} does not serialise its outcome into the record")


class TestTheTwoChannelsStayDistinct:
    """The property the whole exercise protects.

    It would be easy to 'fix' these by making every handler return
    `status="error"`. That is a different system: a crash in phi publishing
    would lose the user's turn. The point is that a block may continue AND
    report that it measured nothing.
    """

    def test_at_least_one_block_keeps_ok_while_recording_a_failure(self) -> None:
        both = []
        for name in WITH_MODULES:
            path = _module_for(name)
            assert path is not None
            source = path.read_text(encoding="utf-8")
            if (_handlers_returning_ok(path)
                    and 'legacy_control_status="ok"' in source
                    and "BlockRunStatus.FAILED" in source):
                both.append(name)

        assert len(both) >= 15, (
            f"only {len(both)} blocks hold both channels at once. If this "
            "dropped, someone collapsed them again — either by failing the "
            "pipeline everywhere or by dropping the record.")

    def test_no_block_claims_a_passing_verdict_from_an_exception(self) -> None:
        """`measured_pass` inside an exception handler is the original defect."""
        offenders = []
        for path in sorted(BLOCKS_DIR.glob("*.py")):
            src = path.read_text(encoding="utf-8")
            for node in ast.walk(ast.parse(src)):
                if not isinstance(node, ast.ExceptHandler):
                    continue
                for stmt in ast.walk(node):
                    if (isinstance(stmt, ast.Call)
                            and getattr(stmt.func, "id", "") == "measured_pass"):
                        offenders.append(f"{path.name}:{stmt.lineno}")

        assert offenders == [], (
            f"measured_pass called from an exception handler: {offenders}. "
            "Nothing was measured — the block raised.")
