"""context_retrieval_rag must not describe a crash as an empty retrieval.

Canonical block 5. Its crash path built a full result set — `context_string:
""`, `memories: []`, `token_count: 0`, `relevance_scores: []` — and wrote the
empty string into `metadata["enhanced_context_string"]`.

Every one of those values describes a retrieval that **ran and found nothing**.
That is a real outcome, and a different one from a retrieval that crashed. The
shape of the record said the first while the `error` key said the second.

The metadata write mattered most: `entropy_amplitude_pre_gate.py:91` reads
`metadata.get("enhanced_context_string", "")` and supplies its own default.
Leaving the key absent gives that gate exactly the string it would have used
anyway — so nothing downstream changes — while writing `""` here made a
crashed retrieval indistinguishable from a genuinely empty one.
"""
from __future__ import annotations

import pytest

from phionyx_core.pipeline.base import BlockContext
from phionyx_core.pipeline.blocks.context_retrieval_rag import (
    ContextRetrievalRagBlock,
)


class _Boom:
    def __getattr__(self, name):
        def _raise(*args, **kwargs):
            raise RuntimeError("rag down")
        return _raise


def _context():
    return BlockContext(
        user_input="test",
        card_type="test",
        card_title="Test",
        scene_context="test",
        card_result="",
        metadata={},
    )


@pytest.mark.asyncio
class TestACrashIsNotAnEmptyRetrieval:
    async def test_no_empty_result_set_is_fabricated(self):
        block = ContextRetrievalRagBlock(rag_service=_Boom(), vector_store=None)

        result = await block.execute(_context())

        assert result.status == "ok", "fail-open: the turn continues"
        for key in ("context_string", "memories", "token_count",
                    "relevance_scores"):
            assert key not in result.data, (
                f"{key} described a retrieval that ran and found nothing; "
                "this one crashed")
        assert result.data["method"] == "not_retrieved"

    async def test_the_gate_key_is_left_absent(self):
        """The write that mattered, and the reason absence is safe."""
        block = ContextRetrievalRagBlock(rag_service=_Boom(), vector_store=None)
        context = _context()

        await block.execute(context)

        assert "enhanced_context_string" not in context.metadata, (
            'writing "" here made a crashed retrieval indistinguishable from '
            "an empty one, for a gate that supplies its own default anyway")

    async def test_the_downstream_gate_still_has_its_own_default(self):
        """Absence is only safe while the reader defaults. Asserted, not assumed."""
        import inspect

        from phionyx_core.pipeline.blocks import entropy_amplitude_pre_gate

        source = inspect.getsource(entropy_amplitude_pre_gate)
        assert 'metadata.get("enhanced_context_string", "")' in source, (
            "the pre-gate no longer supplies its own default; leaving the key "
            "absent is only safe while it does")
