"""Tests proving entropy and phi VARY with different inputs.

Addresses P1-PIPELINE-GERCEKLIK Sorun 3: in mock pipelines phi/entropy are
constant because engines are None → fallback values. These tests prove the
real physics formulas produce different values for different inputs.
"""

import pytest
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


class TestEntropyZlibVariability:
    """Entropy zlib compression varies with input characteristics."""

    def test_entropy_zlib_varies_with_input_length(self):
        """Short vs long text → different entropy values."""
        from phionyx_core.physics.text_physics import calculate_text_entropy_zlib

        short = calculate_text_entropy_zlib("hi")
        long = calculate_text_entropy_zlib(
            "The quick brown fox jumps over the lazy dog. "
            "This is a much longer sentence with more information content "
            "and varied vocabulary to increase compressibility ratio."
        )

        assert short != long, f"Expected different entropy: short={short}, long={long}"

    def test_entropy_zlib_varies_with_content(self):
        """Same length, different content → different entropy."""
        from phionyx_core.physics.text_physics import calculate_text_entropy_zlib

        repetitive = calculate_text_entropy_zlib("aaa bbb aaa bbb aaa bbb aaa bbb")
        diverse = calculate_text_entropy_zlib("fox cat dog sun elk map zen owl")

        assert repetitive != diverse, (
            f"Expected different entropy: repetitive={repetitive}, diverse={diverse}"
        )


class TestPhiVariability:
    """Phi computation varies with input parameters."""

    def test_phi_fallback_varies_with_stability(self):
        """Different stability → different phi (via calculate_phi_cognitive).

        Note: PRE tuned entropy_penalty_k=0.0 (291 experiments), so entropy
        does not affect phi. Stability is the correct variability axis.
        """
        from phionyx_core.physics.formulas import calculate_phi_cognitive

        phi_stable = calculate_phi_cognitive(entropy=0.5, stability=0.9, valence=0.7)
        phi_unstable = calculate_phi_cognitive(entropy=0.5, stability=0.3, valence=0.7)

        assert phi_stable != phi_unstable, f"phi_stable={phi_stable}, phi_unstable={phi_unstable}"
        # Higher stability → higher phi
        assert phi_stable > phi_unstable

    def test_phi_with_real_formula_varies_with_valence(self):
        """calculate_phi_cognitive with different valence → different phi."""
        from phionyx_core.physics.formulas import calculate_phi_cognitive

        phi_neutral = calculate_phi_cognitive(entropy=0.3, stability=0.8, valence=0.0)
        phi_positive = calculate_phi_cognitive(entropy=0.3, stability=0.8, valence=0.8)
        phi_negative = calculate_phi_cognitive(entropy=0.3, stability=0.8, valence=-0.8)

        # All three should differ (neutral is base_resonance floor, pos/neg have intensity)
        assert phi_neutral != phi_positive, (
            f"neutral={phi_neutral}, positive={phi_positive}"
        )
        assert phi_neutral != phi_negative, (
            f"neutral={phi_neutral}, negative={phi_negative}"
        )

    def test_entropy_with_real_formula_varies_with_text(self):
        """calculate_text_entropy_zlib produces spread across diverse inputs."""
        from phionyx_core.physics.text_physics import calculate_text_entropy_zlib

        inputs = [
            "hello",
            "The cognitive pipeline processes blocks in sequence",
            "aaaaaaaaaaaaaaaaaaaaa",
            "x9k#Lm@pQ!zW$eR^tY&uI*oP",
            "Phionyx deterministic governance-first cognitive architecture runtime",
        ]

        values = [calculate_text_entropy_zlib(t) for t in inputs]
        unique_values = set(round(v, 4) for v in values)

        assert len(unique_values) >= 3, (
            f"Expected ≥3 distinct entropy values from 5 inputs, got {len(unique_values)}: {values}"
        )


@dataclass
class _MockBlockContext:
    """Minimal BlockContext for phi_computation block tests."""
    user_input: str = "test"
    card_type: str = "test"
    card_title: str = "test"
    scene_context: str = "test"
    card_result: str = "result"
    scenario_id: Optional[str] = None
    scenario_step_id: Optional[str] = None
    session_id: Optional[str] = "s1"
    current_amplitude: float = 5.0
    current_entropy: float = 0.5
    current_integrity: float = 100.0
    previous_phi: Optional[float] = None
    mode: Optional[str] = None
    strategy: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TestPhiComputationBlockFallback:
    """PhiComputationBlock uses real calculate_phi_cognitive when phi_computer=None."""

    @pytest.mark.asyncio
    async def test_no_phi_computer_uses_real_formula(self):
        """Block with phi_computer=None uses calculate_phi_cognitive, not entropy*0.8."""
        from phionyx_core.pipeline.blocks.phi_computation import PhiComputationBlock

        block = PhiComputationBlock(phi_computer=None)
        ctx = _MockBlockContext(
            current_entropy=0.3,
            metadata={"physics_state": {"entropy": 0.3, "stability": 0.8, "valence": 0.0}}
        )
        result = await block.execute(ctx)

        assert result.status == "ok"
        phi = result.data["phi"]
        # Old heuristic would give 0.3*0.8 = 0.24
        # Real formula gives different value (base_resonance floor with entropy penalty)
        assert phi != pytest.approx(0.24, abs=0.01), (
            f"phi={phi} matches old heuristic — real formula should differ"
        )
        assert result.data["phi_components"].get("source") == "calculate_phi_cognitive_inline"

    @pytest.mark.asyncio
    async def test_fallback_varies_with_stability(self):
        """Different stability values produce different phi in fallback mode.

        Note: PRE tuned entropy_penalty_k=0.0, so entropy has no effect.
        Stability is the correct variability axis.
        """
        from phionyx_core.pipeline.blocks.phi_computation import PhiComputationBlock

        block = PhiComputationBlock(phi_computer=None)

        ctx_stable = _MockBlockContext(
            current_entropy=0.5,
            metadata={"physics_state": {"entropy": 0.5, "stability": 0.9, "valence": 0.7}}
        )
        ctx_unstable = _MockBlockContext(
            current_entropy=0.5,
            metadata={"physics_state": {"entropy": 0.5, "stability": 0.3, "valence": 0.7}}
        )

        result_stable = await block.execute(ctx_stable)
        result_unstable = await block.execute(ctx_unstable)

        phi_stable = result_stable.data["phi"]
        phi_unstable = result_unstable.data["phi"]
        assert phi_stable != phi_unstable, f"phi_stable={phi_stable}, phi_unstable={phi_unstable}"
        assert phi_stable > phi_unstable  # Higher stability → higher phi

    @pytest.mark.asyncio
    async def test_fallback_varies_with_valence(self):
        """Different valence values produce different phi in fallback mode."""
        from phionyx_core.pipeline.blocks.phi_computation import PhiComputationBlock

        block = PhiComputationBlock(phi_computer=None)

        ctx_neutral = _MockBlockContext(
            metadata={"physics_state": {"entropy": 0.3, "stability": 0.8, "valence": 0.0}}
        )
        ctx_positive = _MockBlockContext(
            metadata={"physics_state": {"entropy": 0.3, "stability": 0.8, "valence": 0.9}}
        )

        r_neutral = await block.execute(ctx_neutral)
        r_positive = await block.execute(ctx_positive)

        assert r_neutral.data["phi"] != r_positive.data["phi"]

    @pytest.mark.asyncio
    async def test_phi_computer_takes_precedence(self):
        """When phi_computer is injected, it takes precedence over inline formula."""
        from phionyx_core.pipeline.blocks.phi_computation import PhiComputationBlock

        class FixedPhiComputer:
            def compute_phi(self, physics_state=None, previous_phi=None):
                return {"phi": 0.42, "components": {"source": "fixed_test"}}

        block = PhiComputationBlock(phi_computer=FixedPhiComputer())
        ctx = _MockBlockContext(
            metadata={"physics_state": {"entropy": 0.5, "stability": 0.8}}
        )
        result = await block.execute(ctx)

        assert result.data["phi"] == pytest.approx(0.42)
        assert result.data["phi_components"]["source"] == "fixed_test"
