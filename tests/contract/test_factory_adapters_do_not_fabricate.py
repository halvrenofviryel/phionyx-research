"""An adapter that fabricates on a block's behalf is invisible to a block sweep.

OD-15, 2026-08-03. All fifteen inventory findings were inside blocks. This one
was in the **wiring**: `block_factory` handed a block a collaborator that
returned a hardcoded `{"neurotransmitter_updated": True, "growth_metrics": {}}`
while ignoring every parameter it was given, including the neurotransmitter and
growth_tracker it was constructed with.

The block was honest. It published what its adapter returned. And
`echo_orchestrator` merges block data into metadata, so the claim travelled —
`neurotransmitter_updated` has **no reader anywhere**, which makes it the
purest form of the thing this inventory is about: a claim nobody consumes and
anybody could cite.

Neither a block-level sweep nor `test_pipeline_doctrine_alignment.py` can see
it, because both read block source. This test reads the factory.

It was found by accident while tracing a consumer, so the sweep below covers
**every** inline adapter method rather than the one that was noticed. Six of
the seven constant-return methods turned out to be pass-throughs — returning a
variable computed from a real call — which is why the check is for a literal
that asserts something, not for the absence of a call.
"""
from __future__ import annotations

import ast
import pathlib

FACTORY = (pathlib.Path(__file__).resolve().parents[2] / "phionyx_core"
           / "orchestrator" / "block_factory.py")

#: Literal keys an adapter must not assert without measuring. Each names a
#: thing that happened, and a constant cannot know whether it did.
ASSERTION_KEYS = {
    "updated", "verified", "checked", "validated", "applied",
    "neurotransmitter_updated", "success", "passed",
}


def _literal_assertions() -> list[str]:
    """Adapter methods returning a dict literal that asserts something True."""
    source = FACTORY.read_text(encoding="utf-8")
    offenders = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.ClassDef):
            continue
        for member in node.body:
            if not isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for stmt in ast.walk(member):
                if not (isinstance(stmt, ast.Return)
                        and isinstance(stmt.value, ast.Dict)):
                    continue
                for key, value in zip(stmt.value.keys, stmt.value.values):
                    if not (isinstance(key, ast.Constant)
                            and isinstance(key.value, str)):
                        continue
                    asserts = any(word in key.value for word in ASSERTION_KEYS)
                    literal_true = (isinstance(value, ast.Constant)
                                    and value.value is True)
                    if asserts and literal_true:
                        offenders.append(
                            f"{node.name}.{member.name}:{stmt.lineno} "
                            f"-> {key.value}: True")
    return offenders


class TestNoFactoryAdapterAssertsWhatItDidNotDo:
    def test_no_hardcoded_true_on_an_assertion_key(self) -> None:
        offenders = _literal_assertions()

        assert offenders == [], (
            f"an adapter returns a literal True for a key that names "
            f"something happening: {offenders}. A constant cannot know "
            "whether it happened. The block downstream will publish it "
            "honestly, and echo_orchestrator will merge it into metadata, "
            "where it becomes a claim with a provenance nobody can trace back "
            "to a measurement.")

    def test_the_growth_block_is_wired_with_no_updater(self) -> None:
        """The specific repair, pinned.

        `None` is the honest wiring while no growth updater exists: the block
        records NOT_MEASURED / not_executed for it. If an updater is wired
        again it must be one that measures, and this test is where that gets
        noticed.
        """
        source = FACTORY.read_text(encoding="utf-8")

        assert "NeurotransmitterMemoryGrowthBlock(\n        growth_updater=None\n    )" in source, (
            "a growth updater is wired again. If it measures, update this "
            "test and OD-15; if it does not, it is the same defect.")
