"""Ten blocks write a flat `reason` into shared metadata. Nothing reads it.

OD-17, corrected 2026-08-03. **The first version of this finding was wrong and
the correction is the point.**

It claimed three files read the merged `reason` and could not attribute it.
They do not. `engine_response_generator.py:83` *writes*
`response["safety"]["reason"]`; `ethics_pre_response.py:116` reads
`ethics_result.get("reason")` off the ethics result; `otel_export.py:255`
reads `step.get("reason")` off a step record. **Three unrelated `reason`s, one
word** — the same collision the finding was about, committed inside the
finding itself.

What is true, measured:

- **ten canonical blocks** publish a flat `reason` in their result data —
  causal_graph_update, causal_intervention, causal_simulation,
  counterfactual_analysis, goal_decomposition, **kill_switch_gate**,
  memory_consolidation, outcome_feedback, root_cause_analysis and
  self_model_assessment;
- `echo_orchestrator` merges block result data into `metadata`, so
  `metadata["reason"]` is last-writer-wins across a turn;
- **no code reads `metadata["reason"]`.** Zero.

So this is not a live provenance gap for any consumer. It is the shape OD-15
had: a value nobody consumes, sitting in the merged record where it can be
cited. With one edge that is worse than OD-15's — `kill_switch_gate` is
canonical block 1, so its reason, which carries text like "Kill switch
evaluation error (fail-closed)", is overwritten by **every** later block that
publishes one.

**The attributable channel already exists.** `block_outcome.to_record_fields()`
carries `reason` *and* `block_id`, per block, and every migrated block emits
it. Namespacing the flat key would be ten files of churn on something unread;
what matters is that the reason with a producer attached is already recorded.

This test pins the collision so it cannot grow silently, and fails if a reader
of the merged key appears — at which point the churn becomes worth it.
"""
from __future__ import annotations

import ast
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
BLOCKS = ROOT / "phionyx_core" / "pipeline" / "blocks"

#: Measured 2026-08-03. Raising this means another block joined the collision.
KNOWN_PRODUCERS = 10


def _reason_producers() -> list[str]:
    producers = []
    for path in sorted(BLOCKS.glob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:  # pragma: no cover
            continue
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call)
                    and getattr(node.func, "id", "") == "BlockResult"):
                continue
            for keyword in node.keywords:
                if keyword.arg == "data" and isinstance(keyword.value, ast.Dict):
                    for key in keyword.value.keys:
                        if (isinstance(key, ast.Constant)
                                and key.value == "reason"):
                            producers.append(path.stem)
    return sorted(set(producers))


class TestTheReasonKeyCollision:
    def test_the_producer_count_does_not_grow(self) -> None:
        producers = _reason_producers()

        assert len(producers) <= KNOWN_PRODUCERS, (
            f"{len(producers)} blocks now publish a flat `reason`: "
            f"{producers}. They overwrite each other in merged metadata. "
            "Emit it inside block_outcome, which already carries reason AND "
            "block_id per block, rather than adding to the collision.")

    def test_nothing_reads_the_merged_reason(self) -> None:
        """The assertion that keeps this finding proportionate.

        While nothing reads it, namespacing ten files is churn. The day
        something does, the collision becomes a live attribution failure and
        this test says so.
        """
        readers = []
        for root in (ROOT / "phionyx_core", ROOT / "phionyx_bridge"):
            for path in sorted(root.rglob("*.py")):
                if "__pycache__" in str(path):
                    continue
                for i, line in enumerate(
                        path.read_text(encoding="utf-8").splitlines(), 1):
                    if re.search(r'metadata\.get\(\s*["\']reason["\']|'
                                 r'metadata\[\s*["\']reason["\']\s*\]', line):
                        readers.append(f"{path.name}:{i}")

        assert readers == [], (
            f"the merged `reason` now has a reader: {readers}. It is "
            "last-writer-wins across ten producers, so that reader cannot "
            "know whose reason it received. Namespace the key or move the "
            "read to block_outcome.")

    def test_kill_switch_is_among_the_producers(self) -> None:
        """The edge that makes this worth pinning rather than shrugging at.

        kill_switch_gate is canonical block 1. Every later block that
        publishes a reason overwrites its one — and its text describes a
        safety trigger.
        """
        assert "kill_switch_gate" in _reason_producers()


class TestTheAttributableChannelExists:
    def test_block_outcome_carries_reason_and_block_id(self) -> None:
        """Why namespacing the flat key is not urgent: this already works."""
        from phionyx_core.pipeline.outcome import (
            BlockOutcome,
            BlockRunStatus,
            not_measured,
        )

        record = BlockOutcome(
            block_id="a_specific_block",
            legacy_control_status="ok",
            block_run_status=BlockRunStatus.COMPLETED,
            measurement=not_measured("a specific reason", cause="input_absent"),
        ).to_record_fields()

        assert record["reason"] == "a specific reason"
        assert "a_specific_block" in str(record), (
            "the outcome record no longer identifies its block, so the "
            "attributable reason channel is gone and the flat key becomes "
            "the only one — at which point OD-17 needs the namespacing fix")
