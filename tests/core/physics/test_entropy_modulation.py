"""
Integration Tests for Entropy Modulation
========================================

Tests:
1. H yükselince daha temkinli/refusal/ask-clarify eğilimi artmalı
2. Response amplitude entropy ile modüle edilmeli
3. Behavior parameters (empathic strength, directiveness, sentence length) modüle edilmeli
"""

import sys
from pathlib import Path

# Import modules from phionyx_core
from phionyx_core.physics.entropy_modulation import (
    calculate_entropy_modulated_amplitude,
    calculate_behavior_modulation,
    EntropyModulationConfig
)


def test_high_entropy_increases_caution():
    """
    Test: H yükselince daha temkinli/refusal/ask-clarify eğilimi artmalı.

    Given: High entropy (H = 0.9)
    Expected:
    - Lower response amplitude
    - Lower empathic intervention strength
    - Lower directiveness (more questions, less commands)
    - Shorter sentences
    - Higher caution factor
    """
    base_amplitude = 5.0
    high_entropy = 0.9
    low_entropy = 0.1

    config = EntropyModulationConfig(kH=1.0)

    # High entropy behavior
    high_entropy_behavior = calculate_behavior_modulation(
        base_amplitude=base_amplitude,
        entropy=high_entropy,
        config=config
    )

    # Low entropy behavior
    low_entropy_behavior = calculate_behavior_modulation(
        base_amplitude=base_amplitude,
        entropy=low_entropy,
        config=config
    )

    # High entropy should produce:
    # 1. Lower response amplitude
    assert high_entropy_behavior["response_amplitude"] < low_entropy_behavior["response_amplitude"], \
        "High entropy should reduce response amplitude"

    # 2. Lower empathic intervention strength
    assert high_entropy_behavior["empathic_intervention_strength"] < low_entropy_behavior["empathic_intervention_strength"], \
        "High entropy should reduce empathic intervention strength"

    # 3. Lower directiveness (more questions, less commands)
    assert high_entropy_behavior["directiveness_level"] < low_entropy_behavior["directiveness_level"], \
        "High entropy should reduce directiveness (more questions, less commands)"

    # 4. Shorter sentences
    assert high_entropy_behavior["sentence_length_intensity"] < low_entropy_behavior["sentence_length_intensity"], \
        "High entropy should reduce sentence length"

    # 5. Higher caution factor
    assert high_entropy_behavior["caution_factor"] > low_entropy_behavior["caution_factor"], \
        "High entropy should increase caution factor"

    print("✅ Test passed: High entropy increases caution (temkinli/refusal/ask-clarify)")


def test_amplitude_modulation_formula():
    """
    Test: response_amplitude = base_amplitude / (1 + kH * H) formülü doğru çalışmalı.
    """
    base_amplitude = 10.0
    config = EntropyModulationConfig(kH=1.0)

    # Test cases
    test_cases = [
        (0.0, 10.0),   # H=0: amplitude = 10.0 / (1 + 0) = 10.0
        (0.5, 6.67),  # H=0.5: amplitude = 10.0 / (1 + 0.5) ≈ 6.67
        (1.0, 5.0),   # H=1.0: amplitude = 10.0 / (1 + 1.0) = 5.0
    ]

    for entropy, expected_amplitude in test_cases:
        amplitude = calculate_entropy_modulated_amplitude(
            base_amplitude=base_amplitude,
            entropy=entropy,
            config=config
        )

        # Allow small tolerance for floating point
        assert abs(amplitude - expected_amplitude) < 0.1, \
            f"Amplitude mismatch: H={entropy}, expected≈{expected_amplitude}, got={amplitude}"

    print("✅ Test passed: Amplitude modulation formula works correctly")


def test_behavior_parameters_modulation():
    """
    Test: Behavior parameters (empathic strength, directiveness, sentence length) modüle edilmeli.
    """
    base_amplitude = 5.0
    entropy = 0.7

    behavior = calculate_behavior_modulation(
        base_amplitude=base_amplitude,
        entropy=entropy,
        config=EntropyModulationConfig(kH=1.0)
    )

    # All parameters should be modulated
    assert "response_amplitude" in behavior
    assert "empathic_intervention_strength" in behavior
    assert "directiveness_level" in behavior
    assert "sentence_length_intensity" in behavior
    assert "caution_factor" in behavior

    # All should be in valid ranges
    assert 0.0 < behavior["response_amplitude"] <= 10.0
    assert 0.0 <= behavior["empathic_intervention_strength"] <= 1.0
    assert 0.0 <= behavior["directiveness_level"] <= 1.0
    assert behavior["sentence_length_intensity"] > 0
    assert behavior["caution_factor"] > 0

    print("✅ Test passed: Behavior parameters are modulated correctly")


def test_kH_configuration():
    """
    Test: kH konfigürasyonu amplitude modülasyonunu etkilemeli.
    """
    base_amplitude = 10.0
    entropy = 0.5

    # Low kH (weak modulation)
    config_low = EntropyModulationConfig(kH=0.5)
    amplitude_low = calculate_entropy_modulated_amplitude(
        base_amplitude=base_amplitude,
        entropy=entropy,
        config=config_low
    )

    # High kH (strong modulation)
    config_high = EntropyModulationConfig(kH=2.0)
    amplitude_high = calculate_entropy_modulated_amplitude(
        base_amplitude=base_amplitude,
        entropy=entropy,
        config=config_high
    )

    # Higher kH should produce lower amplitude
    assert amplitude_high < amplitude_low, \
        "Higher kH should produce stronger modulation (lower amplitude)"

    print("✅ Test passed: kH configuration affects modulation strength")


def test_caution_tendency_increase():
    """
    Test: H yükselince refusal/ask-clarify eğilimi artmalı.

    This is tested through:
    - Lower directiveness (more questions)
    - Higher caution factor
    - Lower empathic intervention (less direct intervention)
    """
    base_amplitude = 5.0

    # Low entropy: confident, direct
    low_entropy_behavior = calculate_behavior_modulation(
        base_amplitude=base_amplitude,
        entropy=0.1,
        config=EntropyModulationConfig(kH=1.0)
    )

    # High entropy: cautious, questioning
    high_entropy_behavior = calculate_behavior_modulation(
        base_amplitude=base_amplitude,
        entropy=0.9,
        config=EntropyModulationConfig(kH=1.0)
    )

    # High entropy should show:
    # 1. Lower directiveness (more questions, less commands)
    directiveness_ratio = high_entropy_behavior["directiveness_level"] / low_entropy_behavior["directiveness_level"]
    assert directiveness_ratio < 0.7, \
        f"High entropy should significantly reduce directiveness (ratio={directiveness_ratio:.2f})"

    # 2. Higher caution factor
    caution_ratio = high_entropy_behavior["caution_factor"] / low_entropy_behavior["caution_factor"]
    assert caution_ratio > 1.5, \
        f"High entropy should significantly increase caution (ratio={caution_ratio:.2f})"

    # 3. Lower empathic intervention (less direct intervention)
    intervention_ratio = high_entropy_behavior["empathic_intervention_strength"] / low_entropy_behavior["empathic_intervention_strength"]
    assert intervention_ratio < 0.7, \
        f"High entropy should reduce empathic intervention (ratio={intervention_ratio:.2f})"

    print("✅ Test passed: High entropy increases refusal/ask-clarify tendency")


if __name__ == "__main__":
    test_high_entropy_increases_caution()
    test_amplitude_modulation_formula()
    test_behavior_parameters_modulation()
    test_kH_configuration()
    test_caution_tendency_increase()
    print("\n✅ All integration tests passed!")

