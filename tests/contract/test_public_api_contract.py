"""
Contract Tests for Echoism Core v1.1 Public API
===============================================

Per Faz 3.1: Contract tests are mandatory for RC-1.

These tests verify that the public API surface remains stable
and that internal changes don't break external contracts.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add parent directories to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "core-state" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "core-memory" / "src"))

from phionyx_core.state import (  # noqa: E402
    EchoState2,
    EchoState2Plus,
    AuxState,
    TimeManager,
    MeasurementMapper,
    MeasurementPacket,
    echoism_process_model,
    EchoEvent,
)

# Optional imports (may not be in __init__.py)
try:
    from phionyx_core.state import (
        EthicsRiskAssessor,
        EthicsVector,
        EthicsPolicyConfig,
        apply_forced_damping,
    )
except ImportError:
    from phionyx_core.state.ethics import EthicsVector, EthicsRiskAssessor
    from phionyx_core.state.ethics_enforcement import (
        EthicsPolicyConfig,
        apply_forced_damping,
    )

try:
    from phionyx_core.memory import TraceStore, trace_weight, aggregate_trace
except ImportError:
    from phionyx_core.memory.trace_store import TraceStore
    from phionyx_core.memory.trace import trace_weight, aggregate_trace


class TestPublicAPIContract:
    """
    Contract tests for public API surface.

    These tests verify that:
    1. Public classes/functions exist and are importable
    2. Required methods/properties are present
    3. Type signatures match expectations
    4. Default behaviors are consistent
    """

    def test_echo_state2_contract(self):
        """Test: EchoState2 public API contract."""
        # Verify class exists
        assert EchoState2 is not None

        # Verify required fields
        state = EchoState2()
        assert hasattr(state, 'A')
        assert hasattr(state, 'V')
        assert hasattr(state, 'H')
        assert hasattr(state, 'dA')
        assert hasattr(state, 'dV')
        assert hasattr(state, 't_local')
        assert hasattr(state, 't_global')
        assert hasattr(state, 'E_tags')

        # Verify derived properties
        assert hasattr(state, 'phi')
        assert hasattr(state, 'stability')

        # Verify required methods
        assert hasattr(state, 'update_time')
        assert hasattr(state, 'add_event_tag')

        print("✅ EchoState2 contract verified")

    def test_echo_state2plus_contract(self):
        """Test: EchoState2Plus public API contract (v1.1)."""
        # Verify class exists and extends EchoState2
        assert EchoState2Plus is not None
        assert issubclass(EchoState2Plus, EchoState2)

        # Verify v1.1 fields
        state = EchoState2Plus()
        assert hasattr(state, 'I')
        assert hasattr(state, 'R')
        assert hasattr(state, 'C')
        assert hasattr(state, 'D')

        # Verify v1.1 methods
        assert hasattr(state, 'update_resonance')
        assert hasattr(state, 'update_coherence')
        assert hasattr(state, 'apply_inertia_to_decay_rate')

        print("✅ EchoState2Plus contract verified")

    def test_measurement_mapper_contract(self):
        """Test: MeasurementMapper public API contract."""
        mapper = MeasurementMapper()

        # Verify methods exist
        assert hasattr(mapper, 'map_text_to_measurement')
        assert hasattr(mapper, 'map_text_to_measurement_packet')

        # Test basic functionality (contract: should not crash)
        result = mapper.map_text_to_measurement("I am happy", {})
        assert result is not None
        assert hasattr(result, 'A_meas')
        assert hasattr(result, 'V_meas')
        assert hasattr(result, 'H_meas')
        assert hasattr(result, 'confidence')

        print("✅ MeasurementMapper contract verified")

    def test_measurement_packet_contract(self):
        """Test: MeasurementPacket public API contract (v2.0)."""
        mapper = MeasurementMapper()
        # map_text_to_measurement_packet method exists
        assert hasattr(mapper, 'map_text_to_measurement_packet')

        # Test without dominance (default)
        packet = mapper.map_text_to_measurement_packet("I am confident", {})

        # Verify v2.0 fields (MeasurementPacket uses A, V, H, not A_meas, V_meas, H_meas)
        assert hasattr(packet, 'A')
        assert hasattr(packet, 'V')
        assert hasattr(packet, 'D')  # Optional in v2.0 (may be None)
        assert hasattr(packet, 'H')
        assert hasattr(packet, 'confidence')
        assert hasattr(packet, 'provider')
        assert hasattr(packet, 'timestamp')  # Note: field is 'timestamp', not 't_now'
        assert hasattr(packet, 'evidence_spans')

        # Verify D is None when dominance is disabled (default)
        assert packet.D is None  # D should be None when enable_dominance=False

        # Verify serialization
        assert hasattr(packet, 'to_dict')

        # Verify values are valid
        assert 0.0 <= packet.A <= 1.0
        assert -1.0 <= packet.V <= 1.0
        assert 0.0 <= packet.H <= 1.0
        assert 0.0 <= packet.confidence <= 1.0

        print("✅ MeasurementPacket contract verified")

    def test_ethics_policy_config_contract(self):
        """Test: EthicsPolicyConfig public API contract (v1.1)."""
        policy = EthicsPolicyConfig()

        # Verify required fields
        assert hasattr(policy, 'risk_threshold')
        assert hasattr(policy, 'damping_factor')
        assert hasattr(policy, 'entropy_boost')
        assert hasattr(policy, 'message_style')
        assert hasattr(policy, 'damping_curve')

        # Verify optional per-risk thresholds
        assert hasattr(policy, 'attachment_risk_threshold')
        assert hasattr(policy, 'harm_risk_threshold')

        print("✅ EthicsPolicyConfig contract verified")

    def test_apply_forced_damping_contract(self):
        """Test: apply_forced_damping public API contract."""
        from phionyx_core.state.ethics import EthicsVector

        ethics = EthicsVector(
            harm_risk=0.8,
            manipulation_risk=0.2,
            attachment_risk=0.3,
            boundary_violation_risk=0.1
        )

        state = {"entropy": 0.3, "amplitude": 5.0}
        policy = EthicsPolicyConfig(risk_threshold=0.7)

        # Contract: should return dict with expected keys
        result = apply_forced_damping(state, ethics, policy)

        assert isinstance(result, dict)
        assert "enforced" in result
        assert "entropy" in result
        assert "amplitude" in result
        assert "safety_message" in result
        assert "triggered_risks" in result
        assert "max_risk" in result

        print("✅ apply_forced_damping contract verified")

    def test_echoism_process_model_contract(self):
        """Test: echoism_process_model public API contract."""
        import numpy as np

        # Contract: f(x, dt, u) signature
        x = np.array([0.5, 0.5, 0.0, 0.5, 0.5, 0.5])  # [phi, H, V, A, trust, regulation]
        dt = 1.0
        u = {
            "event_features": {"dA": 0.1, "dV": 0.1, "uncertainty": 0.0},
            "trace_strength": 0.5,
            "confidence": 0.8
        }

        result = echoism_process_model(x, dt, u)

        # Contract: should return numpy array of same shape
        assert isinstance(result, np.ndarray)
        assert result.shape == x.shape
        assert len(result) == 6  # [phi, H, V, A, trust, regulation]

        # Contract: should preserve valid ranges
        assert 0.0 <= result[0] <= 1.0  # phi
        assert 0.01 <= result[1] <= 1.0  # H (entropy minimum)
        assert -1.0 <= result[2] <= 1.0  # V
        assert 0.0 <= result[3] <= 1.0  # A

        print("✅ echoism_process_model contract verified")

    def test_trace_store_contract(self):
        """Test: TraceStore public API contract."""
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            store = TraceStore(db_path=db_path)

            # Verify required methods
            assert hasattr(store, 'store_event')
            assert hasattr(store, 'get_event')
            assert hasattr(store, 'get_events_by_tags')
            assert hasattr(store, 'mark_suppressed')
            assert hasattr(store, 'erase_event')
            assert hasattr(store, 'close')

            # Test basic contract (should not crash)
            event = EchoEvent(
                type="test",
                timestamp=datetime.now(),
                intensity=0.5,
                tags=["test"]
            )

            success = store.store_event(event)
            assert success is True

            retrieved = store.get_event(event.id)
            assert retrieved is not None
            assert retrieved.id == event.id

            store.close()
            print("✅ TraceStore contract verified")
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_trace_weight_contract(self):
        """Test: trace_weight function contract."""
        from datetime import timedelta

        try:
            from phionyx_core.state import EchoEvent
            from phionyx_core.memory import trace_weight
        except ImportError:
            pytest.skip("trace_weight or EchoEvent not available")

        event = EchoEvent(
            type="test",
            timestamp=datetime.now() - timedelta(seconds=100),
            intensity=1.0,
            tags=["test"]
        )

        # Contract: should return float in [0.0, 1.0]
        weight = trace_weight(event, datetime.now(), half_life_seconds=300.0)

        assert isinstance(weight, float)
        assert 0.0 <= weight <= 1.0

        # Contract: suppressed parameter should reduce weight
        weight_normal = trace_weight(event, datetime.now(), suppressed=False)
        weight_suppressed = trace_weight(event, datetime.now(), suppressed=True, suppression_factor=0.1)

        assert weight_suppressed < weight_normal

        print("✅ trace_weight contract verified")

    def test_time_manager_contract(self):
        """Test: TimeManager public API contract."""
        state = EchoState2()
        manager = TimeManager(state)

        # Verify required methods
        assert hasattr(manager, 'advance_turn')
        assert hasattr(manager, 'get_dt')
        assert hasattr(manager, 'get_turn_index')
        assert hasattr(manager, 'get_t_now')
        assert hasattr(manager, 'get_t_local')
        assert hasattr(manager, 'get_t_global')

        # Contract: advance_turn should return dt
        dt = manager.advance_turn()
        assert isinstance(dt, float)
        assert dt >= 0.0

        # Contract: get_dt should return state.dt
        assert manager.get_dt() == state.dt

        print("✅ TimeManager contract verified")


@pytest.mark.contract
class TestAPIBackwardCompatibility:
    """
    Backward compatibility tests for API changes.

    These tests verify that v1.0 APIs still work in v1.1.
    """

    def test_echo_state2_backward_compat(self):
        """Test: EchoState2 v1.0 API still works."""
        state = EchoState2(
            A=0.5,
            V=0.0,
            H=0.5,
            dA=0.0,
            dV=0.0
        )

        # v1.0 properties should still work
        phi = state.phi
        stability = state.stability

        assert isinstance(phi, float)
        assert isinstance(stability, float)

        print("✅ EchoState2 backward compatibility verified")

    def test_measurement_mapper_backward_compat(self):
        """Test: MeasurementMapper v1.0 API still works."""
        mapper = MeasurementMapper()

        # v1.0 method should still work
        result = mapper.map_text_to_measurement("test", {})

        assert result is not None
        assert hasattr(result, 'A_meas')

        print("✅ MeasurementMapper backward compatibility verified")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

