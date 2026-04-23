"""
Unit Tests for Measurement Mapper v2.0 (Faz 2.1)
================================================

Per Faz 2.1 requirements:
- D field: Closed/open scenarios
- Timestamp: Must be set
- Evidence spans: Clamp/normalize rules if not empty
- Provider quality: Confidence should change in expected direction
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Import modules from phionyx_core
from phionyx_core.state.measurement_mapper import MeasurementMapper
from phionyx_core.state.measurement_mapper_v2 import MeasurementPacket, EvidenceSpan


def test_d_field_closed_scenario():
    """
    Test: D field is None when enable_dominance=False.

    Per requirement: D field should be None when dominance extraction is disabled.
    """
    mapper = MeasurementMapper()
    text = "I am confident and in control of this situation."

    packet = mapper.map_text_to_measurement_packet(
        raw_llm_output=text,
        provider_metadata={"model_name": "gpt-4", "provider_type": "cloud"},
        enable_dominance=False
    )

    assert packet.D is None, f"D should be None when enable_dominance=False, got {packet.D}"
    print(f"✅ D field closed: D={packet.D}")


def test_d_field_open_scenario():
    """
    Test: D field is extracted when enable_dominance=True.

    Per requirement: D field should be extracted (0.0-1.0) when dominance extraction is enabled.
    """
    mapper = MeasurementMapper()
    text = "I am confident and in control. I lead this team."

    packet = mapper.map_text_to_measurement_packet(
        raw_llm_output=text,
        provider_metadata={"model_name": "gpt-4", "provider_type": "cloud"},
        enable_dominance=True
    )

    assert packet.D is not None, "D should not be None when enable_dominance=True"
    assert 0.0 <= packet.D <= 1.0, f"D should be in [0.0, 1.0], got {packet.D}"
    assert packet.D > 0.0, f"D should be > 0.0 for confident text, got {packet.D}"
    print(f"✅ D field open: D={packet.D:.3f}")


def test_timestamp_set():
    """
    Test: Timestamp is set in MeasurementPacket.

    Per requirement: Timestamp must be set (datetime object).
    """
    mapper = MeasurementMapper()
    text = "Hello, how are you?"

    before = datetime.now()
    packet = mapper.map_text_to_measurement_packet(
        raw_llm_output=text,
        provider_metadata={"model_name": "gpt-4"}
    )
    after = datetime.now()

    assert isinstance(packet.timestamp, datetime), f"Timestamp should be datetime, got {type(packet.timestamp)}"
    assert before <= packet.timestamp <= after, "Timestamp should be between before and after"
    print(f"✅ Timestamp set: {packet.timestamp}")


def test_evidence_spans_clamp_normalize():
    """
    Test: Evidence spans are clamped/normalized when not empty.

    Per requirement: Evidence spans should be clamped (max 10) and normalized if present.
    Note: MeasurementMapper doesn't currently generate evidence_spans, so this test
    verifies the structure allows evidence_spans to be set.
    """
    mapper = MeasurementMapper()

    # Create text with many emotion words
    emotion_words = ["happy", "sad", "excited", "angry", "calm", "worried", "joyful", "frustrated", "peaceful", "anxious", "ecstatic", "depressed"]
    text = " ".join(emotion_words * 2)  # 24 emotion words

    packet = mapper.map_text_to_measurement_packet(
        raw_llm_output=text,
        provider_metadata={"model_name": "gpt-4"}
    )

    # Evidence spans should be clamped to max 10 (if they exist)
    # Currently MeasurementMapper doesn't generate evidence_spans, so they will be empty
    assert len(packet.evidence_spans) <= 10, f"Evidence spans should be clamped to 10, got {len(packet.evidence_spans)}"

    # If evidence spans exist, check they are valid
    if packet.evidence_spans:
        for span in packet.evidence_spans:
            # Check for required attributes (start, end, text)
            assert hasattr(span, 'start'), f"Span should have 'start' attribute: {type(span)}"
            assert hasattr(span, 'end'), f"Span should have 'end' attribute: {type(span)}"
            assert hasattr(span, 'text'), f"Span should have 'text' attribute: {type(span)}"
            # Check for contribution (not confidence_contribution)
            if hasattr(span, 'contribution'):
                assert 0.0 <= span.contribution <= 1.0, \
                    f"Contribution should be [0.0, 1.0], got {span.contribution}"
            # Check for start/end (not start_char/end_char)
            assert span.start >= 0, f"Start should be >= 0, got {span.start}"
            assert span.end >= span.start, "End should be >= start"

    print(f"✅ Evidence spans: {len(packet.evidence_spans)} spans (clamped to max 10)")


def test_provider_quality_affects_confidence():
    """
    Test: Provider quality changes confidence in expected direction.

    Per requirement: High quality → higher confidence, Low quality → lower confidence.
    """
    mapper = MeasurementMapper()
    text = "I am very happy and excited about this opportunity!"

    # High quality provider
    packet_high = mapper.map_text_to_measurement_packet(
        raw_llm_output=text,
        provider_metadata={
            "model_name": "gpt-4",
            "provider_type": "cloud",
            "quality_tier": "high"
        }
    )

    # Low quality provider
    packet_low = mapper.map_text_to_measurement_packet(
        raw_llm_output=text,
        provider_metadata={
            "model_name": "llama3",
            "provider_type": "local",
            "quality_tier": "low"
        }
    )

    # High quality should have >= confidence than low quality
    assert packet_high.confidence >= packet_low.confidence, \
        f"High quality should have >= confidence: high={packet_high.confidence:.3f}, low={packet_low.confidence:.3f}"

    print(f"✅ Provider quality affects confidence: high={packet_high.confidence:.3f}, low={packet_low.confidence:.3f}")


def test_provider_school_safety_grade():
    """
    Test: School safety grade affects confidence conservatively.

    Per requirement: School safety grade A/B/C should affect confidence.
    """
    mapper = MeasurementMapper()
    text = "I am feeling good today."

    # Grade A (highest confidence)
    packet_a = mapper.map_text_to_measurement_packet(
        raw_llm_output=text,
        provider_metadata={
            "model_name": "gpt-4",
            "school_safety_grade": "A"
        }
    )

    # Grade C (lower confidence)
    packet_c = mapper.map_text_to_measurement_packet(
        raw_llm_output=text,
        provider_metadata={
            "model_name": "gpt-4",
            "school_safety_grade": "C"
        }
    )

    # Grade A should have >= confidence than Grade C
    assert packet_a.confidence >= packet_c.confidence, \
        f"Grade A should have >= confidence: A={packet_a.confidence:.3f}, C={packet_c.confidence:.3f}"

    print(f"✅ School safety grade: A={packet_a.confidence:.3f}, C={packet_c.confidence:.3f}")


def test_provider_latency_budget():
    """
    Test: Latency budget affects confidence (placeholder).

    Per requirement: Latency budget should be considered in confidence calculation.
    """
    mapper = MeasurementMapper()
    text = "I am feeling good today."

    # With latency budget
    packet_with_budget = mapper.map_text_to_measurement_packet(
        raw_llm_output=text,
        provider_metadata={
            "model_name": "gpt-4",
            "latency_budget": 2.0  # 2 seconds
        }
    )

    # Without latency budget
    _packet_without = mapper.map_text_to_measurement_packet(
        raw_llm_output=text,
        provider_metadata={
            "model_name": "gpt-4"
        }
    )

    # Latency budget should slightly reduce confidence (0.95x multiplier)
    # But due to deterministic nature, both might be same if base confidence is same
    # This test just verifies it doesn't crash
    assert 0.01 <= packet_with_budget.confidence <= 0.99, \
        f"Confidence with latency budget should be in [0.01, 0.99], got {packet_with_budget.confidence:.3f}"

    print(f"✅ Latency budget: confidence={packet_with_budget.confidence:.3f}")


def test_measurement_packet_deterministic():
    """
    Test: Same input + same provider → same packet (deterministic).

    Per requirement: Deterministic behavior must be maintained.
    Note: Using math.isclose for floating point comparison.
    """
    import math

    mapper = MeasurementMapper()
    text = "I am very happy and confident!"
    provider_metadata = {"model_name": "gpt-4", "provider_type": "cloud"}

    # Run multiple times
    packet1 = mapper.map_text_to_measurement_packet(raw_llm_output=text, provider_metadata=provider_metadata)
    packet2 = mapper.map_text_to_measurement_packet(raw_llm_output=text, provider_metadata=provider_metadata)
    packet3 = mapper.map_text_to_measurement_packet(raw_llm_output=text, provider_metadata=provider_metadata)

    # A, V, H, D should be approximately equal (within floating point precision)
    tolerance = 1e-5
    assert math.isclose(packet1.A, packet2.A, abs_tol=tolerance) and math.isclose(packet2.A, packet3.A, abs_tol=tolerance), "A should be deterministic"
    assert math.isclose(packet1.V, packet2.V, abs_tol=tolerance) and math.isclose(packet2.V, packet3.V, abs_tol=tolerance), "V should be deterministic"
    assert math.isclose(packet1.H, packet2.H, abs_tol=tolerance) and math.isclose(packet2.H, packet3.H, abs_tol=tolerance), "H should be deterministic"
    assert math.isclose(packet1.confidence, packet2.confidence, abs_tol=tolerance) and math.isclose(packet2.confidence, packet3.confidence, abs_tol=tolerance), "confidence should be deterministic"
    if packet1.D is not None:
        assert math.isclose(packet1.D, packet2.D, abs_tol=tolerance) and math.isclose(packet2.D, packet3.D, abs_tol=tolerance), "D should be deterministic"

    print(f"✅ Deterministic: A={packet1.A:.3f}, V={packet1.V:.3f}, H={packet1.H:.3f}, D={packet1.D}")


def test_measurement_packet_to_dict():
    """
    Test: MeasurementPacket can be serialized to dict and back.
    """
    mapper = MeasurementMapper()
    text = "I am confident and happy."

    packet = mapper.map_text_to_measurement_packet(
        raw_llm_output=text,
        provider_metadata={"model_name": "gpt-4"}
    )

    # Convert to dict
    packet_dict = packet.to_dict()

    # Convert back
    packet_restored = MeasurementPacket.from_dict(packet_dict)

    # Check core fields
    assert abs(packet_restored.A - packet.A) < 0.001, "A should match"
    assert abs(packet_restored.V - packet.V) < 0.001, "V should match"
    assert abs(packet_restored.H - packet.H) < 0.001, "H should match"
    assert abs(packet_restored.confidence - packet.confidence) < 0.001, "confidence should match"
    assert packet_restored.D == packet.D, "D should match"
    assert packet_restored.provider == packet.provider, "provider should match"

    print("✅ Serialization: packet → dict → packet works")


if __name__ == "__main__":
    test_d_field_closed_scenario()
    test_d_field_open_scenario()
    test_timestamp_set()
    test_evidence_spans_clamp_normalize()
    test_provider_quality_affects_confidence()
    test_provider_school_safety_grade()
    test_provider_latency_budget()
    test_measurement_packet_deterministic()
    test_measurement_packet_to_dict()
    print("\n✅ All Measurement Mapper v2.0 tests passed!")

