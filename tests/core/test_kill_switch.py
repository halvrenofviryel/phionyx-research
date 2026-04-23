"""
Tests for Kill Switch — v4 §9.1
"""

import pytest
from phionyx_core.governance.kill_switch import (
    KillSwitch,
    KillSwitchConfig,
    KillSwitchState,
    KillSwitchTrigger,
    KillSwitchResult,
)


class TestKillSwitchBasic:
    """Basic kill switch behavior."""

    def test_initial_state_is_armed(self):
        ks = KillSwitch()
        assert ks.state == KillSwitchState.ARMED
        assert ks.is_armed
        assert not ks.is_triggered

    def test_safe_metrics_no_trigger(self):
        ks = KillSwitch()
        result = ks.evaluate(ethics_max_risk=0.1, t_meta=0.9, drift_detected=False)
        assert not result.triggered
        assert ks.state == KillSwitchState.ARMED

    def test_high_ethics_risk_triggers(self):
        ks = KillSwitch()
        result = ks.evaluate(ethics_max_risk=0.96, t_meta=0.9)
        assert result.triggered
        assert result.trigger == KillSwitchTrigger.ETHICS_CRITICAL
        assert ks.state == KillSwitchState.TRIGGERED

    def test_low_t_meta_triggers(self):
        ks = KillSwitch()
        result = ks.evaluate(ethics_max_risk=0.1, t_meta=0.05)
        assert result.triggered
        assert result.trigger == KillSwitchTrigger.TMETA_COLLAPSE

    def test_sustained_drift_triggers(self):
        ks = KillSwitch()
        # 5 drifts should NOT trigger (threshold is > 5)
        for _ in range(5):
            result = ks.evaluate(drift_detected=True)
            assert not result.triggered

        # 6th drift triggers
        result = ks.evaluate(drift_detected=True)
        assert result.triggered
        assert result.trigger == KillSwitchTrigger.SUSTAINED_DRIFT

    def test_drift_resets_on_no_drift(self):
        ks = KillSwitch()
        for _ in range(4):
            ks.evaluate(drift_detected=True)
        # No drift resets counter
        ks.evaluate(drift_detected=False)
        # 1 more drift should not trigger (counter was reset)
        result = ks.evaluate(drift_detected=True)
        assert not result.triggered


class TestKillSwitchTriggerPriority:
    """Trigger priority: ethics > t_meta > drift."""

    def test_ethics_takes_priority_over_t_meta(self):
        ks = KillSwitch()
        result = ks.evaluate(ethics_max_risk=0.99, t_meta=0.01)
        assert result.trigger == KillSwitchTrigger.ETHICS_CRITICAL


class TestKillSwitchManual:
    """Manual trigger and reset."""

    def test_manual_trigger(self):
        ks = KillSwitch()
        result = ks.manual_trigger("Admin requested shutdown")
        assert result.triggered
        assert result.trigger == KillSwitchTrigger.MANUAL
        assert ks.state == KillSwitchState.TRIGGERED

    def test_already_triggered_returns_triggered(self):
        ks = KillSwitch()
        ks.manual_trigger()
        result = ks.evaluate(ethics_max_risk=0.1)
        assert result.triggered
        assert "already triggered" in result.reason

    def test_reset_enters_cooldown(self):
        ks = KillSwitch()
        ks.manual_trigger()
        assert ks.reset("toygar")
        assert ks.state == KillSwitchState.COOLDOWN
        assert ks.is_armed  # cooldown counts as armed

    def test_cannot_reset_if_not_triggered(self):
        ks = KillSwitch()
        assert not ks.reset("toygar")


class TestKillSwitchDisarm:
    """Disarm for testing."""

    def test_disarmed_never_triggers(self):
        ks = KillSwitch()
        ks.disarm("admin")
        result = ks.evaluate(ethics_max_risk=1.0, t_meta=0.0)
        assert not result.triggered
        assert ks.state == KillSwitchState.DISARMED

    def test_rearm(self):
        ks = KillSwitch()
        ks.disarm("admin")
        ks.arm()
        assert ks.state == KillSwitchState.ARMED
        result = ks.evaluate(ethics_max_risk=0.99)
        assert result.triggered


class TestKillSwitchConfig:
    """Custom configuration."""

    def test_custom_thresholds(self):
        config = KillSwitchConfig(
            ethics_max_risk_threshold=0.8,
            t_meta_min_threshold=0.2,
            consecutive_drift_max=3,
        )
        ks = KillSwitch(config=config)

        # 0.85 should trigger with threshold 0.8
        result = ks.evaluate(ethics_max_risk=0.85)
        assert result.triggered

    def test_fail_open_config(self):
        config = KillSwitchConfig(fail_closed=False)
        ks = KillSwitch(config=config)
        # Even with fail_open, normal triggers still work
        result = ks.evaluate(ethics_max_risk=0.99)
        assert result.triggered


class TestKillSwitchCallback:
    """Callback on trigger."""

    def test_callback_called_on_trigger(self):
        triggered_results = []
        ks = KillSwitch(on_trigger=lambda r: triggered_results.append(r))
        ks.evaluate(ethics_max_risk=0.99)
        assert len(triggered_results) == 1
        assert triggered_results[0].triggered

    def test_callback_error_does_not_prevent_trigger(self):
        def bad_callback(r):
            raise RuntimeError("Callback failed")

        ks = KillSwitch(on_trigger=bad_callback)
        result = ks.evaluate(ethics_max_risk=0.99)
        assert result.triggered  # Still triggers despite callback error


class TestKillSwitchAudit:
    """Event log and serialization."""

    def test_events_logged(self):
        ks = KillSwitch()
        ks.evaluate(ethics_max_risk=0.1)
        ks.evaluate(ethics_max_risk=0.99)
        assert len(ks.event_log) == 2

    def test_to_dict(self):
        ks = KillSwitch()
        d = ks.to_dict()
        assert d["state"] == "armed"
        assert d["consecutive_drift_count"] == 0
        assert "config" in d

    def test_turn_id_in_result(self):
        ks = KillSwitch()
        result = ks.evaluate(ethics_max_risk=0.99, turn_id=42)
        assert result.turn_id == 42
