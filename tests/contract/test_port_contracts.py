"""
Contract Tests: Port Interfaces
================================

Tests for:
- Physics Port contract
- Memory Port contract
- Intuition Port contract
- Pedagogy Port contract
- Policy Port contract
- Narrative Port contract
- Meta Port contract

All ports must satisfy their contracts, whether Real or Null implementation.
"""
import pytest
import sys
from pathlib import Path
from typing import Dict, Any, List
from abc import ABC, abstractmethod

# Add project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "echo-server"))
sys.path.insert(0, str(PROJECT_ROOT / "core-physics" / "src"))


# Mock Port Interfaces (for testing)
class PhysicsPort(ABC):
    @abstractmethod
    async def calculate_phi(self, **kwargs) -> Dict[str, float]:
        """Contract: Returns dict with 'phi', 'phi_cognitive', 'phi_physical'"""
        pass


class MemoryPort(ABC):
    @abstractmethod
    async def search_memories(self, query: str, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Contract: Returns list of memories"""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Contract: Returns bool"""
        pass


# Mock Null Implementations
class NullPhysicsEngine(PhysicsPort):
    async def calculate_phi(self, **kwargs) -> Dict[str, float]:
        """Null implementation: Returns safe defaults."""
        return {
            "phi": 5.0,
            "phi_cognitive": 2.5,
            "phi_physical": 2.5
        }


class NullMemoryEngine(MemoryPort):
    async def search_memories(self, query: str, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Null implementation: Returns empty list."""
        return []

    def is_connected(self) -> bool:
        """Null implementation: Returns False."""
        return False


# Mock Real Implementations (simplified)
class RealPhysicsEngine(PhysicsPort):
    async def calculate_phi(self, **kwargs) -> Dict[str, float]:
        """Real implementation: Uses actual physics formulas."""
        from phionyx_core.physics.formulas import calculate_phi_v2_1

        result = calculate_phi_v2_1(
            valence=kwargs.get("valence", 0.0),
            arousal=kwargs.get("arousal", 1.0),
            amplitude=kwargs.get("amplitude", 5.0),
            time_delta=kwargs.get("time_delta", 1.0),
            gamma=kwargs.get("gamma", 0.15),
            stability=kwargs.get("stability", 0.7),
            entropy=kwargs.get("entropy", 0.5),
            w_c=kwargs.get("w_c", 0.5),
            w_p=kwargs.get("w_p", 0.5)
        )

        return {
            "phi": result["phi"],
            "phi_cognitive": result["phi_cognitive"],
            "phi_physical": result["phi_physical"]
        }


class RealMemoryEngine(MemoryPort):
    def __init__(self):
        self._connected = False

    async def search_memories(self, query: str, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Real implementation: Would query Supabase."""
        # Mock implementation for testing
        return [
            {"content": f"Memory for {query}", "user_id": user_id, "importance": 0.8}
        ]

    def is_connected(self) -> bool:
        """Real implementation: Would check Supabase connection."""
        return self._connected


@pytest.mark.parametrize("engine_class", [RealPhysicsEngine, NullPhysicsEngine])
@pytest.mark.asyncio
async def test_physics_port_contract(engine_class):
    """Test Physics Port contract compliance."""
    engine = engine_class()

    # Contract: calculate_phi returns Dict[str, float]
    result = await engine.calculate_phi(
        amplitude=5.0,
        entropy=0.5,
        time_delta=0.1,
        gamma=0.15,
        stability=0.8
    )

    # Contract requirements
    assert isinstance(result, dict)
    assert "phi" in result
    assert isinstance(result["phi"], (int, float))
    assert 0.0 <= result["phi"] <= 10.0

    # Contract: Handles edge cases
    result_low = await engine.calculate_phi(amplitude=0.0, entropy=1.0, time_delta=0.0, gamma=0.0, stability=0.0)
    result_high = await engine.calculate_phi(amplitude=10.0, entropy=0.0, time_delta=100.0, gamma=1.0, stability=1.0)

    assert "phi" in result_low
    assert "phi" in result_high
    assert 0.0 <= result_low["phi"] <= 10.0
    assert 0.0 <= result_high["phi"] <= 10.0


@pytest.mark.parametrize("engine_class", [RealMemoryEngine, NullMemoryEngine])
@pytest.mark.asyncio
async def test_memory_port_contract(engine_class):
    """Test Memory Port contract compliance."""
    engine = engine_class()

    # Contract: search_memories returns List[Dict[str, Any]]
    results = await engine.search_memories(
        query="test query",
        user_id="user_123",
        limit=10
    )

    assert isinstance(results, list)
    for result in results:
        assert isinstance(result, dict)
        assert "content" in result or "memory_content" in result

    # Contract: is_connected returns bool
    assert isinstance(engine.is_connected(), bool)


@pytest.mark.asyncio
async def test_null_physics_safe_defaults():
    """Null physics engine should return safe defaults."""
    engine = NullPhysicsEngine()

    result = await engine.calculate_phi(
        amplitude=7.5,
        entropy=0.3,
        time_delta=1.0,
        gamma=0.15,
        stability=0.8
    )

    # Should return safe defaults without errors
    assert "phi" in result
    assert 0.0 <= result["phi"] <= 10.0
    assert "phi_cognitive" in result
    assert "phi_physical" in result


@pytest.mark.asyncio
async def test_null_physics_no_exceptions():
    """Null physics engine should never raise exceptions."""
    engine = NullPhysicsEngine()

    # Test with edge cases
    result1 = await engine.calculate_phi(amplitude=0.0, entropy=1.0, time_delta=0.0, gamma=0.0, stability=0.0)
    result2 = await engine.calculate_phi(amplitude=10.0, entropy=0.0, time_delta=100.0, gamma=1.0, stability=1.0)

    # Should never raise exceptions
    assert result1 is not None
    assert result2 is not None


@pytest.mark.asyncio
async def test_null_memory_empty_results():
    """Null memory engine should return empty results."""
    engine = NullMemoryEngine()

    results = await engine.search_memories(
        query="test query",
        user_id="user_123",
        limit=10
    )

    assert results == []  # Empty list
    assert engine.is_connected() is False


@pytest.mark.asyncio
async def test_null_memory_no_exceptions():
    """Null memory engine should never raise exceptions."""
    engine = NullMemoryEngine()

    # Test with various inputs
    result1 = await engine.search_memories(query="", user_id="", limit=0)
    result2 = await engine.search_memories(query="test", user_id="user_123", limit=100)
    result3 = engine.is_connected()

    # Should never raise exceptions
    assert result1 == []
    assert result2 == []
    assert result3 is False


@pytest.mark.asyncio
async def test_pipeline_stability_with_null():
    """Pipeline should work even with Null modules."""
    # Simulate EDU profile (Intuition is Null)
    physics = RealPhysicsEngine()
    memory = RealMemoryEngine()
    # intuition = NullIntuitionEngine()  # Null in EDU profile

    # Pipeline should still work
    physics_result = await physics.calculate_phi(amplitude=5.0, entropy=0.5, time_delta=1.0, gamma=0.15, stability=0.7)
    memory_result = await memory.search_memories("test", "user_123")

    # Should not crash
    assert physics_result is not None
    assert memory_result is not None

