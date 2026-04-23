"""
Memory Context Injection Tests
================================

Sprint 3: Proves that retrieved memories from RAG cache are injected
into the narrative layer's enhanced context string.

Evidence target:
- Memories present → "Relevant prior context" appears in LLM context
- Empty memories → no additional context
- Max 5 memories enforced
- Memory text truncated at 200 chars
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from phionyx_core.pipeline.blocks.narrative_layer import NarrativeLayerBlock
from phionyx_core.pipeline.base import BlockContext, BlockResult


class ContextCapturingProcessor:
    """Mock processor that captures the enhanced_context_string passed to it."""

    def __init__(self):
        self.captured_context = None
        self.captured_physics_state = None
        self.call_count = 0

    async def process_narrative_layer(
        self, frame=None, user_input="", enhanced_context_string="", **kwargs
    ):
        self.captured_context = enhanced_context_string
        self.captured_physics_state = kwargs.get("physics_state")
        self.call_count += 1
        frame = frame or {}
        if isinstance(frame, dict):
            frame["narrative_text"] = "Test response"
        result = MagicMock()
        result.status = "ok"
        result.text = "Test response"
        return (frame, "Test response", result)


def _make_ctx(memories=None, context_string="", **extra_metadata):
    """Helper to build BlockContext with common fields."""
    metadata = {
        "frame": {"user_input": "test"},
        "enhanced_context_string": context_string,
        **extra_metadata,
    }
    if memories is not None:
        metadata["retrieved_memories"] = memories
    return BlockContext(
        user_input="test input",
        card_type="shadow",
        card_title="test",
        card_result="",
        scene_context="",
        current_entropy=0.5,
        metadata=metadata,
    )


# --- Basic injection ---


@pytest.mark.asyncio
async def test_memories_injected_into_context():
    """Retrieved memories → 'Relevant prior context' section in enhanced context."""
    proc = ContextCapturingProcessor()
    block = NarrativeLayerBlock(processor=proc, enable_templates=False)
    ctx = _make_ctx(
        memories=[
            {"text": "User previously asked about Python decorators"},
            {"text": "User prefers Turkish language responses"},
        ]
    )
    await block.execute(ctx)
    assert proc.call_count == 1
    assert "Relevant prior context" in proc.captured_context
    assert "Python decorators" in proc.captured_context
    assert "Turkish language" in proc.captured_context


@pytest.mark.asyncio
async def test_empty_memories_no_injection():
    """Empty memories list → no additional context added."""
    proc = ContextCapturingProcessor()
    block = NarrativeLayerBlock(processor=proc, enable_templates=False)
    ctx = _make_ctx(memories=[])
    await block.execute(ctx)
    assert "Relevant prior context" not in proc.captured_context


@pytest.mark.asyncio
async def test_no_memories_key_no_injection():
    """No retrieved_memories in metadata → no additional context."""
    proc = ContextCapturingProcessor()
    block = NarrativeLayerBlock(processor=proc, enable_templates=False)
    ctx = _make_ctx(memories=None)
    await block.execute(ctx)
    assert "Relevant prior context" not in proc.captured_context


@pytest.mark.asyncio
async def test_none_memories_no_injection():
    """retrieved_memories = None → no additional context."""
    proc = ContextCapturingProcessor()
    block = NarrativeLayerBlock(processor=proc, enable_templates=False)
    ctx = _make_ctx()
    ctx.metadata["retrieved_memories"] = None
    await block.execute(ctx)
    assert "Relevant prior context" not in proc.captured_context


# --- Max 5 memories ---


@pytest.mark.asyncio
async def test_max_five_memories_enforced():
    """More than 5 memories → only first 5 included."""
    proc = ContextCapturingProcessor()
    block = NarrativeLayerBlock(processor=proc, enable_templates=False)
    memories = [{"text": f"Memory item {i}"} for i in range(10)]
    ctx = _make_ctx(memories=memories)
    await block.execute(ctx)
    assert "Memory item 0" in proc.captured_context
    assert "Memory item 4" in proc.captured_context
    assert "Memory item 5" not in proc.captured_context


# --- Truncation at 200 chars ---


@pytest.mark.asyncio
async def test_long_memory_truncated():
    """Memory text > 200 chars → truncated to 200."""
    proc = ContextCapturingProcessor()
    block = NarrativeLayerBlock(processor=proc, enable_templates=False)
    long_text = "A" * 300
    ctx = _make_ctx(memories=[{"text": long_text}])
    await block.execute(ctx)
    # The line should contain at most 200 A's (plus "- " prefix)
    lines = proc.captured_context.split("\n")
    memory_lines = [line for line in lines if line.startswith("- ")]
    assert len(memory_lines) == 1
    # Strip "- " prefix and check length
    content = memory_lines[0][2:]
    assert len(content) <= 200


# --- Different memory formats ---


@pytest.mark.asyncio
async def test_dict_memories_with_text_key():
    """Memories as dicts with 'text' key."""
    proc = ContextCapturingProcessor()
    block = NarrativeLayerBlock(processor=proc, enable_templates=False)
    ctx = _make_ctx(memories=[{"text": "First memory"}, {"text": "Second memory"}])
    await block.execute(ctx)
    assert "First memory" in proc.captured_context
    assert "Second memory" in proc.captured_context


@pytest.mark.asyncio
async def test_dict_memories_with_content_key():
    """Memories as dicts with 'content' key (alternative format)."""
    proc = ContextCapturingProcessor()
    block = NarrativeLayerBlock(processor=proc, enable_templates=False)
    ctx = _make_ctx(memories=[{"content": "Content-based memory"}])
    await block.execute(ctx)
    assert "Content-based memory" in proc.captured_context


@pytest.mark.asyncio
async def test_string_memories():
    """Memories as plain strings."""
    proc = ContextCapturingProcessor()
    block = NarrativeLayerBlock(processor=proc, enable_templates=False)
    ctx = _make_ctx(memories=["Plain string memory 1", "Plain string memory 2"])
    await block.execute(ctx)
    assert "Plain string memory 1" in proc.captured_context
    assert "Plain string memory 2" in proc.captured_context


# --- Preserves existing context ---


@pytest.mark.asyncio
async def test_memories_appended_to_existing_context():
    """Existing enhanced_context_string is preserved, memories appended."""
    proc = ContextCapturingProcessor()
    block = NarrativeLayerBlock(processor=proc, enable_templates=False)
    ctx = _make_ctx(
        memories=[{"text": "Prior knowledge about user"}],
        context_string="Existing project context here.",
    )
    await block.execute(ctx)
    assert proc.captured_context.startswith("Existing project context here.")
    assert "Relevant prior context" in proc.captured_context
    assert "Prior knowledge about user" in proc.captured_context


# --- Empty text memories filtered ---


@pytest.mark.asyncio
async def test_empty_text_memories_filtered():
    """Memories with empty text are not included."""
    proc = ContextCapturingProcessor()
    block = NarrativeLayerBlock(processor=proc, enable_templates=False)
    ctx = _make_ctx(
        memories=[
            {"text": ""},
            {"text": "Valid memory"},
            {"text": ""},
        ]
    )
    await block.execute(ctx)
    assert "Valid memory" in proc.captured_context
    # Only 1 memory line (the 2 empty ones are filtered)
    lines = [line for line in proc.captured_context.split("\n") if line.startswith("- ")]
    assert len(lines) == 1
