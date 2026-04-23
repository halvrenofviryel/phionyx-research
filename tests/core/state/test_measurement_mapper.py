"""
Unit Tests for Measurement Mapper
==================================

Per Echoism Core v1.0 requirements:
- Deterministic: Same input → same output
- Neutral text → low A, V≈0, high H
- Clear emotion → A or V prominent, low H
- Confidence never 0 or 1 (clamped to [0.01, 0.99])
"""

import pytest
import sys
from pathlib import Path

# Import modules from phionyx_core
from phionyx_core.state.measurement_mapper import MeasurementMapper, MeasurementVector


def test_deterministic_same_input():
    """
    Test: Same text → same A/V/H (deterministic).

    Per requirement: Deterministic and testable.
    """
    mapper = MeasurementMapper()
    text = "I am very happy and excited about this!"

    # Run multiple times
    result1 = mapper.map_text_to_measurement(text)
    result2 = mapper.map_text_to_measurement(text)
    result3 = mapper.map_text_to_measurement(text)

    # All results should be identical
    assert result1.A_meas == result2.A_meas == result3.A_meas, "A_meas should be deterministic"
    assert result1.V_meas == result2.V_meas == result3.V_meas, "V_meas should be deterministic"
    assert result1.H_meas == result2.H_meas == result3.H_meas, "H_meas should be deterministic"
    assert result1.confidence == result2.confidence == result3.confidence, "confidence should be deterministic"

    print("✅ Test passed: Deterministic output for same input")


def test_neutral_text_low_arousal_neutral_valence_high_entropy():
    """
    Test: Neutral text → low A, V≈0, high H.

    Per requirement: Neutral text should produce low arousal, neutral valence, high entropy.
    """
    mapper = MeasurementMapper()

    # Neutral texts
    neutral_texts = [
        "Hello, how are you?",
        "The weather is nice today.",
        "I see.",
        "Okay, thank you."
    ]

    for text in neutral_texts:
        result = mapper.map_text_to_measurement(text)

        # Low arousal (A <= 0.5, or at least not high)
        assert result.A_meas <= 0.5, f"Neutral text should have low arousal, got {result.A_meas:.3f}"

        # Neutral valence (V close to 0)
        assert abs(result.V_meas) < 0.3, f"Neutral text should have neutral valence, got {result.V_meas:.3f}"

        # High entropy (H > 0.5) - uncertainty due to lack of clear emotion
        assert result.H_meas > 0.5, f"Neutral text should have high entropy, got {result.H_meas:.3f}"

        print(f"✅ Neutral text '{text[:30]}...' → A={result.A_meas:.3f}, V={result.V_meas:.3f}, H={result.H_meas:.3f}")


def test_clear_emotion_prominent_arousal_or_valence_low_entropy():
    """
    Test: Clear emotion → A or V prominent, low H.

    Per requirement: Clear emotion should produce prominent A or V, low entropy.
    """
    mapper = MeasurementMapper()

    # Positive emotion (high V, moderate A, low H)
    positive_text = "I am so happy and excited! This is amazing!"
    result_pos = mapper.map_text_to_measurement(positive_text)

    assert result_pos.V_meas > 0.3, f"Positive text should have positive valence, got {result_pos.V_meas:.3f}"
    assert result_pos.H_meas < 0.6, f"Clear positive emotion should have low entropy, got {result_pos.H_meas:.3f}"
    print(f"✅ Positive emotion → V={result_pos.V_meas:.3f}, H={result_pos.H_meas:.3f}")

    # Negative emotion (low V, high A if angry, low H)
    negative_text = "I am very sad and disappointed about this."
    result_neg = mapper.map_text_to_measurement(negative_text)

    assert result_neg.V_meas < -0.1, f"Negative text should have negative valence, got {result_neg.V_meas:.3f}"
    assert result_neg.H_meas < 0.7, f"Clear negative emotion should have low entropy, got {result_neg.H_meas:.3f}"
    print(f"✅ Negative emotion → V={result_neg.V_meas:.3f}, H={result_neg.H_meas:.3f}")

    # High arousal (high A, low H)
    high_arousal_text = "I am furious and angry! This is terrible!"
    result_arousal = mapper.map_text_to_measurement(high_arousal_text)

    assert result_arousal.A_meas > 0.6, f"High arousal text should have high arousal, got {result_arousal.A_meas:.3f}"
    assert result_arousal.H_meas < 0.6, f"High arousal should have low entropy, got {result_arousal.H_meas:.3f}"
    print(f"✅ High arousal → A={result_arousal.A_meas:.3f}, H={result_arousal.H_meas:.3f}")


def test_confidence_never_zero_or_one():
    """
    Test: Confidence never 0 or 1 (clamped to [0.01, 0.99]).

    Per requirement: Confidence must be clamped to avoid 0 or 1.
    """
    mapper = MeasurementMapper()

    # Test various texts
    test_texts = [
        "",  # Empty text (should be low confidence but not 0)
        "a",  # Very short text
        "I am very happy and excited about this amazing opportunity that makes me feel so good!" * 10,  # Long clear text
        "maybe perhaps possibly uncertain unsure confused belki muhtemelen şüpheli kararsız",  # High uncertainty
        "happy sad angry calm excited bored"  # Mixed sentiment
    ]

    for text in test_texts:
        result = mapper.map_text_to_measurement(text)

        # Confidence must be in (0, 1) range (clamped)
        assert result.confidence > 0.0, f"Confidence should never be 0, got {result.confidence:.3f} for text: {text[:30]}"
        assert result.confidence < 1.0, f"Confidence should never be 1, got {result.confidence:.3f} for text: {text[:30]}"
        assert 0.01 <= result.confidence <= 0.99, f"Confidence should be clamped to [0.01, 0.99], got {result.confidence:.3f}"

        print(f"✅ Confidence clamped: {result.confidence:.3f} for text: {text[:40]}...")


def test_provider_metadata_affects_confidence():
    """
    Test: Provider metadata affects confidence.

    - Low quality model → confidence decreases
    - High quality model → confidence stays high
    """
    mapper = MeasurementMapper()
    text = "I am very happy and excited!"

    # High quality model (GPT-4)
    result_high = mapper.map_text_to_measurement(
        text,
        provider_metadata={"model_name": "gpt-4", "provider_type": "cloud", "quality_tier": "high"}
    )

    # Low quality model (local llama)
    result_low = mapper.map_text_to_measurement(
        text,
        provider_metadata={"model_name": "llama3", "provider_type": "local", "quality_tier": "low"}
    )

    # High quality should have >= confidence than low quality
    assert result_high.confidence >= result_low.confidence, \
        f"High quality model should have >= confidence than low quality: {result_high.confidence:.3f} vs {result_low.confidence:.3f}"

    print(f"✅ Provider metadata affects confidence: high={result_high.confidence:.3f}, low={result_low.confidence:.3f}")


def test_measurement_vector_ranges():
    """
    Test: Measurement vector values are in valid ranges.
    """
    mapper = MeasurementMapper()
    text = "Test text with some emotion"
    result = mapper.map_text_to_measurement(text)

    # Check ranges
    assert 0.0 <= result.A_meas <= 1.0, f"A_meas should be in [0.0, 1.0], got {result.A_meas:.3f}"
    assert -1.0 <= result.V_meas <= 1.0, f"V_meas should be in [-1.0, 1.0], got {result.V_meas:.3f}"
    assert 0.0 <= result.H_meas <= 1.0, f"H_meas should be in [0.0, 1.0], got {result.H_meas:.3f}"
    assert 0.01 <= result.confidence <= 0.99, f"confidence should be in [0.01, 0.99], got {result.confidence:.3f}"

    print("✅ Measurement vector ranges valid")


if __name__ == "__main__":
    test_deterministic_same_input()
    test_neutral_text_low_arousal_neutral_valence_high_entropy()
    test_clear_emotion_prominent_arousal_or_valence_low_entropy()
    test_confidence_never_zero_or_one()
    test_provider_metadata_affects_confidence()
    test_measurement_vector_ranges()
    print("\n✅ All measurement mapper tests passed!")

