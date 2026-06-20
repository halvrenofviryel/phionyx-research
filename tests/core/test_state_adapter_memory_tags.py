"""Regression — StateAdapter.to_unified_echo_state_dict() memory_tags (RC0.9 stabilization).

Was ``[tag.semantic_context for tag in E_tags]`` — a non-existent attribute on EventReference
(id/tag/intensity), a latent AttributeError that only fired on a NON-empty E_tags (so it slipped
past tests until now). Now ``[tag.tag ...]`` (the primary semantic tag). This pins it.
"""

from phionyx_core.state.echo_event import EventReference
from phionyx_core.state.echo_state_2 import EchoState2
from phionyx_core.state.state_adapter import EchoState2Adapter


def test_memory_tags_uses_event_reference_tag_and_does_not_crash():
    state = EchoState2()
    state.E_tags.append(EventReference(id="e0", tag="ethics_trigger", intensity=0.7))
    state.E_tags.append(EventReference(id="e1", tag="user_correction", intensity=0.4))
    out = EchoState2Adapter(state).to_unified_echo_state_dict()
    assert out["memory_tags"] == ["ethics_trigger", "user_correction"]


def test_memory_tags_empty_when_no_events():
    out = EchoState2Adapter(EchoState2()).to_unified_echo_state_dict()
    assert out["memory_tags"] == []
