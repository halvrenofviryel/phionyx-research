"""
Tests for SelfModel — v4 §7 (AGI Layer 7)
==========================================
"""

import pytest
from phionyx_core.meta.self_model import (
    SelfModel,
    CapabilityStatus,
    CapabilityAssessment,
    SelfAwarenessReport,
)


# ── Basic Capability Registration ──


def test_register_available_capability():
    model = SelfModel()
    model.register_capability("respond", available=True)
    assert "respond" in model.get_available_capabilities()


def test_register_unavailable_capability():
    model = SelfModel()
    model.register_capability("external_api", available=False, reason="No API key")
    assert "external_api" not in model.get_available_capabilities()


def test_register_degraded_capability():
    model = SelfModel()
    model.register_capability("llm", available=True, degraded=True, reason="Slow")
    caps = model.get_available_capabilities()
    assert "llm" in caps  # degraded is still available


def test_override_capability():
    model = SelfModel()
    model.register_capability("x", available=True)
    model.register_capability("x", available=False, reason="Disabled")
    assert "x" not in model.get_available_capabilities()


# ── can_i_do() ──


def test_can_do_available_high_confidence():
    model = SelfModel()
    model.register_capability("respond", available=True)
    result = model.can_i_do("respond", context_confidence=0.9, knowledge_score=0.9)
    assert result.can_do is True
    assert result.confidence == pytest.approx(0.81)
    assert result.status == CapabilityStatus.AVAILABLE


def test_cannot_do_unavailable():
    model = SelfModel()
    model.register_capability("external_api", available=False, reason="No key")
    result = model.can_i_do("external_api", context_confidence=1.0)
    assert result.can_do is False
    assert result.confidence == 0.0
    assert result.status == CapabilityStatus.UNAVAILABLE
    assert "No key" in result.limitations[0]


def test_cannot_do_low_confidence():
    model = SelfModel()
    model.register_capability("respond", available=True)
    result = model.can_i_do("respond", context_confidence=0.1, knowledge_score=1.0)
    assert result.can_do is False
    assert "Low confidence" in str(result.limitations)


def test_cannot_do_outside_boundary():
    model = SelfModel()
    model.register_capability("respond", available=True)
    result = model.can_i_do("respond", context_confidence=1.0, knowledge_score=0.1)
    assert result.can_do is False
    assert "knowledge boundary" in str(result.limitations).lower()


def test_degraded_adds_limitation():
    model = SelfModel()
    model.register_capability("llm", available=True, degraded=True, reason="Slow")
    result = model.can_i_do("llm", context_confidence=0.9, knowledge_score=0.9)
    assert result.can_do is True
    assert any("Degraded" in lim for lim in result.limitations)


def test_unknown_capability():
    model = SelfModel()
    result = model.can_i_do("unknown_action", context_confidence=0.8, knowledge_score=0.8)
    assert result.can_do is True  # combined 0.64 >= 0.3
    assert result.status in (CapabilityStatus.AVAILABLE, CapabilityStatus.DEGRADED)


def test_combined_score_threshold():
    model = SelfModel()
    model.register_capability("x", available=True)
    # 0.5 * 0.5 = 0.25 < 0.3 → cannot do
    result = model.can_i_do("x", context_confidence=0.5, knowledge_score=0.5)
    assert result.can_do is False


# ── Limitations ──


def test_add_and_get_limitations():
    model = SelfModel()
    model.add_limitation("No GPU available")
    model.add_limitation("Limited context window")
    lims = model.get_limitations()
    assert "No GPU available" in lims
    assert "Limited context window" in lims


def test_remove_limitation():
    model = SelfModel()
    model.add_limitation("No GPU available")
    model.remove_limitation("No GPU available")
    assert "No GPU available" not in model.get_limitations()


def test_duplicate_limitation_ignored():
    model = SelfModel()
    model.add_limitation("A")
    model.add_limitation("A")
    assert model.get_limitations().count("A") == 1


def test_limitations_include_unavailable_capabilities():
    model = SelfModel()
    model.register_capability("api", available=False, reason="No key")
    lims = model.get_limitations()
    assert any("api" in entry and "unavailable" in entry for entry in lims)


# ── SelfAwarenessReport ──


def test_report_counts():
    model = SelfModel()
    model.register_capability("a", available=True)
    model.register_capability("b", available=True, degraded=True)
    model.register_capability("c", available=False)
    report = model.get_report(knowledge_coverage=0.7)
    assert report.capabilities_available == 1
    assert report.capabilities_degraded == 1
    assert report.capabilities_unavailable == 1
    assert report.knowledge_coverage == 0.7


def test_report_confidence_mean():
    model = SelfModel()
    model.can_i_do("x", context_confidence=0.8)
    model.can_i_do("y", context_confidence=0.6)
    report = model.get_report()
    assert report.confidence_mean == pytest.approx(0.7)


def test_report_empty():
    model = SelfModel()
    report = model.get_report()
    assert report.capabilities_available == 0
    assert report.confidence_mean == 0.5  # default


# ── Serialization ──


def test_to_dict():
    model = SelfModel()
    model.register_capability("respond", available=True)
    model.register_capability("api", available=False, reason="Down")
    model.add_limitation("No GPU")
    model.can_i_do("respond", context_confidence=0.9)
    d = model.to_dict()
    assert d["capabilities"]["respond"] == "available"
    assert d["capabilities"]["api"] == "unavailable"
    assert "No GPU" in d["known_limitations"]
    assert len(d["confidence_history"]) == 1
    assert d["capability_reasons"]["api"] == "Down"


def test_to_dict_empty():
    model = SelfModel()
    d = model.to_dict()
    assert d["capabilities"] == {}
    assert d["known_limitations"] == []
    assert d["confidence_history"] == []


# ── Confidence History Limit ──


def test_confidence_history_capped():
    model = SelfModel()
    for i in range(150):
        model.can_i_do("x", context_confidence=0.5)
    d = model.to_dict()
    assert len(d["confidence_history"]) == 100  # max_history


# ── Reasoning Messages ──


def test_reasoning_can_do():
    model = SelfModel()
    model.register_capability("x", available=True)
    result = model.can_i_do("x", context_confidence=0.9, knowledge_score=0.9)
    assert "Can perform" in result.reasoning


def test_reasoning_cannot_do():
    model = SelfModel()
    model.register_capability("x", available=False, reason="Broken")
    result = model.can_i_do("x")
    assert "Cannot perform" in result.reasoning or "unavailable" in result.reasoning


# ── Auto-Save Trigger Tests ──

import json  # noqa: E402


class TestSelfModelAutoSave:
    """Tests for SelfModel auto-save/load and trigger mechanism."""

    @pytest.fixture
    def sm(self, tmp_path):
        """SelfModel with auto-save enabled."""
        sm = SelfModel()
        sm.set_session("sm-test")
        sm.enable_auto_save(base_path=str(tmp_path))
        return sm

    def _saved_data(self, tmp_path) -> dict:
        fp = tmp_path / "sm-test.json"
        if not fp.exists():
            return {}
        with open(fp) as f:
            return json.load(f)

    def test_save_load_roundtrip(self, tmp_path):
        """Save and load produce identical self-model."""
        sm = SelfModel()
        sm.set_session("roundtrip")
        sm.register_capability("respond", available=True)
        sm.register_capability("api", available=False, reason="Down")
        sm.add_limitation("No GPU")
        sm.can_i_do("respond", context_confidence=0.85)
        sm.auto_save(base_path=str(tmp_path))

        loaded = SelfModel.auto_load("roundtrip", base_path=str(tmp_path))
        assert loaded is not None
        assert loaded._capabilities["respond"].value == "available"
        assert loaded._capabilities["api"].value == "unavailable"
        assert loaded._capability_reasons["api"] == "Down"
        assert "No GPU" in loaded._known_limitations
        assert len(loaded._confidence_history) == 1
        assert loaded._confidence_history[0] == pytest.approx(0.85)

    def test_from_dict_reconstructs_state(self):
        """from_dict correctly restores all fields."""
        data = {
            "session_id": "s1",
            "capabilities": {"a": "available", "b": "degraded"},
            "capability_reasons": {"b": "Slow"},
            "known_limitations": ["limit1"],
            "confidence_history": [0.5, 0.7, 0.9],
        }
        sm = SelfModel.from_dict(data)
        assert sm._session_id == "s1"
        assert sm._capabilities["a"].value == "available"
        assert sm._capabilities["b"].value == "degraded"
        assert sm._capability_reasons["b"] == "Slow"
        assert sm._known_limitations == ["limit1"]
        assert sm._confidence_history == [0.5, 0.7, 0.9]

    def test_register_capability_triggers_save(self, sm, tmp_path):
        """register_capability persists immediately."""
        sm.register_capability("respond", available=True)
        data = self._saved_data(tmp_path)
        assert data["capabilities"]["respond"] == "available"

    def test_add_limitation_triggers_save(self, sm, tmp_path):
        """add_limitation persists immediately."""
        sm.add_limitation("No GPU")
        data = self._saved_data(tmp_path)
        assert "No GPU" in data["known_limitations"]

    def test_remove_limitation_triggers_save(self, sm, tmp_path):
        """remove_limitation persists the removal."""
        sm.add_limitation("No GPU")
        sm.remove_limitation("No GPU")
        data = self._saved_data(tmp_path)
        assert "No GPU" not in data["known_limitations"]

    def test_no_save_when_disabled(self, tmp_path):
        """Mutations do NOT save when auto-save is disabled."""
        sm = SelfModel()
        sm.set_session("quiet")
        sm.register_capability("x", available=True)
        fp = tmp_path / "quiet.json"
        assert not fp.exists()

    def test_corrupt_file_returns_none(self, tmp_path):
        """Corrupt JSON returns None."""
        fp = tmp_path / "bad.json"
        fp.write_text("{{{not json")
        result = SelfModel.auto_load("bad", base_path=str(tmp_path))
        assert result is None

    def test_missing_session_returns_none(self, tmp_path):
        """Missing file returns None."""
        result = SelfModel.auto_load("nonexistent", base_path=str(tmp_path))
        assert result is None

    def test_auto_save_no_session_returns_none(self, tmp_path):
        """auto_save without session_id returns None."""
        sm = SelfModel()
        result = sm.auto_save(base_path=str(tmp_path))
        assert result is None
