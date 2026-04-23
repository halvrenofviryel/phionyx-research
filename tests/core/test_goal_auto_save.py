"""
Goal Persistence Auto-Save Tests — Sprint 3.4
================================================

Tests for auto_save, auto_load, and auto-save trigger functionality.
Total: 15 tests
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch

from phionyx_core.planning.goal_persistence import (
    GoalPersistence,
    GoalPriority,
    GoalStatus,
)


class TestGoalAutoSave:
    """Tests for goal persistence auto-save/load."""

    def test_save_load_roundtrip(self, tmp_path):
        """Save and load produce identical goals."""
        gp = GoalPersistence()
        gp.set_session("test-session-1")
        gp.add_goal("g1", "Test Goal", description="desc", priority=GoalPriority.HIGH)
        gp.auto_save(base_path=str(tmp_path))

        loaded = GoalPersistence.auto_load("test-session-1", base_path=str(tmp_path))
        assert loaded is not None
        assert len(loaded._goals) == 1
        assert loaded._goals["g1"].name == "Test Goal"

    def test_cross_session_persistence(self, tmp_path):
        """Goals survive session boundary via file persistence."""
        gp1 = GoalPersistence()
        gp1.set_session("session-A")
        gp1.add_goal("g1", "Persist Me")
        gp1.auto_save(base_path=str(tmp_path))

        gp2 = GoalPersistence.auto_load("session-A", base_path=str(tmp_path))
        assert gp2 is not None
        assert "g1" in gp2._goals

    def test_corrupt_file_returns_none(self, tmp_path):
        """Corrupt JSON file returns None gracefully."""
        file_path = tmp_path / "corrupt-session.json"
        file_path.write_text("not valid json{{{")

        result = GoalPersistence.auto_load("corrupt-session", base_path=str(tmp_path))
        assert result is None

    def test_missing_session_returns_none(self, tmp_path):
        """Non-existent session file returns None."""
        result = GoalPersistence.auto_load("nonexistent", base_path=str(tmp_path))
        assert result is None

    def test_auto_save_creates_directory(self, tmp_path):
        """auto_save creates the directory if it doesn't exist."""
        nested = tmp_path / "deep" / "nested"
        gp = GoalPersistence()
        gp.set_session("deep-test")
        gp.add_goal("g1", "Deep Goal")
        result = gp.auto_save(base_path=str(nested))
        assert result is not None
        assert Path(result).exists()


class TestGoalAutoSaveTrigger:
    """Tests for automatic save on mutation (enable_auto_save loop)."""

    @pytest.fixture
    def gp(self, tmp_path):
        """GoalPersistence with auto-save enabled."""
        gp = GoalPersistence()
        gp.set_session("trigger-test")
        gp.enable_auto_save(base_path=str(tmp_path))
        return gp

    def _saved_goals(self, tmp_path) -> dict:
        """Read saved goals from file."""
        fp = tmp_path / "trigger-test.json"
        if not fp.exists():
            return {}
        with open(fp) as f:
            return json.load(f).get("goals", {})

    def test_enable_disable_auto_save(self):
        """enable/disable toggles the flag."""
        gp = GoalPersistence()
        assert gp._auto_save_enabled is False
        gp.enable_auto_save()
        assert gp._auto_save_enabled is True
        gp.disable_auto_save()
        assert gp._auto_save_enabled is False

    def test_add_goal_triggers_save(self, gp, tmp_path):
        """add_goal persists immediately when auto-save enabled."""
        gp.add_goal("g1", "Auto Goal")
        saved = self._saved_goals(tmp_path)
        assert "g1" in saved
        assert saved["g1"]["name"] == "Auto Goal"

    def test_activate_triggers_save(self, gp, tmp_path):
        """activate persists new status."""
        gp.add_goal("g1", "Goal")
        gp.activate("g1")
        saved = self._saved_goals(tmp_path)
        assert saved["g1"]["status"] == "active"

    def test_complete_triggers_save(self, gp, tmp_path):
        """complete persists completed status and progress=1.0."""
        gp.add_goal("g1", "Goal")
        gp.activate("g1")
        gp.complete("g1")
        saved = self._saved_goals(tmp_path)
        assert saved["g1"]["status"] == "completed"
        assert saved["g1"]["progress"] == 1.0

    def test_abandon_triggers_save(self, gp, tmp_path):
        """abandon persists abandoned status with reason."""
        gp.add_goal("g1", "Goal")
        gp.abandon("g1", reason="no longer needed")
        saved = self._saved_goals(tmp_path)
        assert saved["g1"]["status"] == "abandoned"
        assert saved["g1"]["metadata"]["abandon_reason"] == "no longer needed"

    def test_block_triggers_save(self, gp, tmp_path):
        """block persists blocked status."""
        gp.add_goal("g1", "Goal")
        gp.block("g1", blocked_by="external dep")
        saved = self._saved_goals(tmp_path)
        assert saved["g1"]["status"] == "blocked"
        assert saved["g1"]["metadata"]["blocked_by"] == "external dep"

    def test_update_progress_triggers_save(self, gp, tmp_path):
        """update_progress persists new progress value."""
        gp.add_goal("g1", "Goal")
        gp.update_progress("g1", 0.75)
        saved = self._saved_goals(tmp_path)
        assert saved["g1"]["progress"] == 0.75

    def test_no_save_when_disabled(self, tmp_path):
        """Mutations do NOT save when auto-save is disabled."""
        gp = GoalPersistence()
        gp.set_session("no-save-test")
        gp.add_goal("g1", "Quiet Goal")
        fp = tmp_path / "no-save-test.json"
        assert not fp.exists()

    def test_auto_save_roundtrip_after_mutations(self, gp, tmp_path):
        """Full mutation sequence produces loadable state."""
        gp.add_goal("g1", "Goal A", priority=GoalPriority.HIGH)
        gp.add_goal("g2", "Goal B", priority=GoalPriority.LOW)
        gp.activate("g1")
        gp.update_progress("g1", 0.5)
        gp.abandon("g2", reason="deprioritized")

        loaded = GoalPersistence.auto_load("trigger-test", base_path=str(tmp_path))
        assert loaded is not None
        assert len(loaded._goals) == 2
        assert loaded._goals["g1"].status == GoalStatus.ACTIVE
        assert loaded._goals["g1"].progress == 0.5
        assert loaded._goals["g2"].status == GoalStatus.ABANDONED

    def test_auto_save_no_session_returns_none(self, tmp_path):
        """auto_save without session_id logs warning and returns None."""
        gp = GoalPersistence()
        gp.enable_auto_save(base_path=str(tmp_path))
        result = gp.auto_save(base_path=str(tmp_path))
        assert result is None
