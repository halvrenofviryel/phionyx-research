"""Regression tests for the 0.8.0 type-check-flagged logic fixes (task #65).

Each of these would raise BEFORE the fix:
- EventReference was constructed with event_id/event_type/tags, but the dataclass
  fields are id/tag/intensity -> TypeError (state_migration + echo_state_2).
- VectorStore.store(metadata=None) called .get() on None -> AttributeError.
- VectorStore.search_similar in repository mode (client is None) called
  self.client.rpc(...) -> AttributeError.
"""
import pytest

from phionyx_core.state.echo_event import EventReference


def test_echo_state2_add_event_tag_builds_valid_eventref():
    from phionyx_core.state.echo_state_2 import EchoState2

    s = EchoState2(A=0.5, V=0.0, H=0.5)
    before = len(s.E_tags)
    s.add_event_tag(event_type="memory", intensity=0.7, semantic_context="topic_x")
    assert len(s.E_tags) == before + 1
    ref = s.E_tags[-1]
    assert isinstance(ref, EventReference)
    assert ref.tag == "topic_x"
    assert ref.intensity == pytest.approx(0.7)
    assert ref.id  # non-empty id assigned


def test_unified_to_echo_state2_migrates_memory_tags_to_eventrefs(monkeypatch):
    from phionyx_core.state import state_migration

    # The legacy migration path is gated behind OLD_STATE_AVAILABLE (an optional
    # import that is absent in CI — which is why this bug stayed cold). Open it.
    monkeypatch.setattr(state_migration, "OLD_STATE_AVAILABLE", True)

    class _OldState:
        # UnifiedEchoState (legacy) primary fields are arousal/valence/entropy.
        arousal = 0.4
        valence = 0.1
        entropy = 0.5
        memory_tags = ["alpha", "beta"]   # legacy path -> EventReference per tag

    es2, _aux = state_migration.unified_to_echo_state2(_OldState())
    # Two memory_tags -> two EventReference(id/tag/intensity); no TypeError
    assert len(es2.E_tags) == 2
    assert all(isinstance(r, EventReference) for r in es2.E_tags)
    assert {r.tag for r in es2.E_tags} == {"alpha", "beta"}
    assert all(r.intensity == pytest.approx(0.5) for r in es2.E_tags)


@pytest.mark.asyncio
async def test_vector_store_store_none_metadata_returns_none():
    from phionyx_core.memory.vector_store import VectorStore

    vs = VectorStore()  # no Supabase creds -> client is None
    result = await vs.store(content="hello", metadata=None)
    assert result is None  # graceful, no AttributeError


@pytest.mark.asyncio
async def test_vector_store_search_similar_repository_mode_returns_empty():
    from phionyx_core.memory.vector_store import VectorStore

    class _Repo:
        client = object()  # non-None -> is_connected() returns True

    vs = VectorStore(memory_repository=_Repo())
    assert vs.client is None
    assert vs.is_connected() is True
    # Before the fix this crashed on None.rpc(...); now it degrades to [].
    result = await vs.search_similar(query_embedding=[0.1, 0.2, 0.3], actor_ref="actor_1")
    assert result == []
