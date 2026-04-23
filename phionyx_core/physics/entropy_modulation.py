"""
Entropy Modulation - Response Amplitude Regulation
===================================================

Per Echoism Core v1.0:
- Entropy modulates response amplitude
- Formula: response_amplitude = base_amplitude / (1 + kH * H)
- High entropy -> Lower amplitude -> More cautious behavior

This module provides core functions (independent of HarmonicComposer).
"""

from __future__ import annotations

from typing import Dict, Optional
from dataclasses import dataclass


# Module-level tunable defaults (Tier A — PRE surfaces)
ENTROPY_MOD_KH = 1.0
MIN_AMPLITUDE = 0.1
MAX_AMPLITUDE = 10.0


@dataclass
class EntropyModulationConfig:
    """
    Configuration for entropy modulation.

    Attributes:
        kH: Entropy modulation coefficient (default: 1.0)
            Higher kH -> stronger entropy damping
        min_amplitude: Minimum amplitude (default: 0.1)
        max_amplitude: Maximum amplitude (default: 10.0)
    """
    kH: float = ENTROPY_MOD_KH
    min_amplitude: float = MIN_AMPLITUDE
    max_amplitude: float = MAX_AMPLITUDE


def calculate_entropy_modulated_amplitude(
    base_amplitude: float,
    entropy: float,
    config: Optional[EntropyModulationConfig] = None
) -> float:
    """
    Calculate entropy-modulated response amplitude.

    Per Echoism Core v1.0:
    - High entropy -> Lower amplitude (more cautious)
    - Low entropy -> Higher amplitude (more confident)

    Formula: response_amplitude = base_amplitude / (1 + kH * H)

    Args:
        base_amplitude: Base amplitude (before modulation)
        entropy: Current entropy H (0.0-1.0)
        config: Entropy modulation configuration

    Returns:
        Modulated amplitude (clamped to config range)
    """
    if config is None:
        config = EntropyModulationConfig()

    # Clamp entropy to valid range
    entropy = max(0.0, min(1.0, entropy))

    # Apply entropy modulation
    # response_amplitude = base_amplitude / (1 + kH * H)
    denominator = 1.0 + config.kH * entropy
    modulated_amplitude = base_amplitude / denominator

    # Clamp to valid range
    modulated_amplitude = max(config.min_amplitude, min(config.max_amplitude, modulated_amplitude))

    return modulated_amplitude


def modulate_empathic_intervention_strength(
    base_strength: float,
    entropy: float,
    config: Optional[EntropyModulationConfig] = None
) -> float:
    """
    Modulate empathic intervention strength based on entropy.

    High entropy -> Lower intervention strength (more cautious)
    Low entropy -> Higher intervention strength (more direct)

    Args:
        base_strength: Base intervention strength (0.0-1.0)
        entropy: Current entropy H (0.0-1.0)
        config: Entropy modulation configuration

    Returns:
        Modulated intervention strength (0.0-1.0)
    """
    # Use entropy-modulated amplitude as factor
    amplitude_factor = calculate_entropy_modulated_amplitude(
        base_amplitude=1.0,  # Normalized
        entropy=entropy,
        config=config
    )

    # Scale intervention strength
    modulated_strength = base_strength * amplitude_factor

    # Clamp to valid range
    return max(0.0, min(1.0, modulated_strength))


def modulate_directiveness_level(
    base_directiveness: float,
    entropy: float,
    config: Optional[EntropyModulationConfig] = None
) -> float:
    """
    Modulate directiveness level based on entropy.

    High entropy -> Lower directiveness (more questions, less commands)
    Low entropy -> Higher directiveness (more commands, less questions)

    Args:
        base_directiveness: Base directiveness level (0.0-1.0)
        entropy: Current entropy H (0.0-1.0)
        config: Entropy modulation configuration

    Returns:
        Modulated directiveness level (0.0-1.0)
    """
    # High entropy reduces directiveness
    amplitude_factor = calculate_entropy_modulated_amplitude(
        base_amplitude=1.0,  # Normalized
        entropy=entropy,
        config=config
    )

    # Scale directiveness
    modulated_directiveness = base_directiveness * amplitude_factor

    # Clamp to valid range
    return max(0.0, min(1.0, modulated_directiveness))


def modulate_sentence_length_intensity(
    base_length: float,
    entropy: float,
    config: Optional[EntropyModulationConfig] = None
) -> float:
    """
    Modulate sentence length/intensity based on entropy.

    High entropy -> Shorter sentences, less intensity (more cautious)
    Low entropy -> Longer sentences, more intensity (more confident)

    Args:
        base_length: Base sentence length/intensity
        entropy: Current entropy H (0.0-1.0)
        config: Entropy modulation configuration

    Returns:
        Modulated sentence length/intensity
    """
    # Use entropy-modulated amplitude as factor
    amplitude_factor = calculate_entropy_modulated_amplitude(
        base_amplitude=1.0,  # Normalized
        entropy=entropy,
        config=config
    )

    # Scale sentence length
    modulated_length = base_length * amplitude_factor

    # Ensure minimum length
    return max(1.0, modulated_length)


def calculate_behavior_modulation(
    base_amplitude: float,
    entropy: float,
    config: Optional[EntropyModulationConfig] = None
) -> Dict[str, float]:
    """
    Calculate all behavior parameters modulated by entropy.

    Returns:
        Dictionary with:
        - response_amplitude: Modulated amplitude
        - empathic_intervention_strength: Modulated intervention strength
        - directiveness_level: Modulated directiveness
        - sentence_length_intensity: Modulated sentence length
        - caution_factor: Caution factor (inverse of amplitude)
    """
    if config is None:
        config = EntropyModulationConfig()

    # Calculate modulated amplitude
    response_amplitude = calculate_entropy_modulated_amplitude(
        base_amplitude=base_amplitude,
        entropy=entropy,
        config=config
    )

    # Calculate behavior parameters
    empathic_strength = modulate_empathic_intervention_strength(
        base_strength=1.0,  # Normalized
        entropy=entropy,
        config=config
    )

    directiveness = modulate_directiveness_level(
        base_directiveness=1.0,  # Normalized
        entropy=entropy,
        config=config
    )

    sentence_length = modulate_sentence_length_intensity(
        base_length=10.0,  # Default sentence length
        entropy=entropy,
        config=config
    )

    # Caution factor: inverse of amplitude (high entropy -> high caution)
    caution_factor = 1.0 / response_amplitude if response_amplitude > 0 else 1.0
    caution_factor = max(0.1, min(10.0, caution_factor))

    return {
        "response_amplitude": response_amplitude,
        "empathic_intervention_strength": empathic_strength,
        "directiveness_level": directiveness,
        "sentence_length_intensity": sentence_length,
        "caution_factor": caution_factor,
        "entropy": entropy,
        "base_amplitude": base_amplitude
    }

