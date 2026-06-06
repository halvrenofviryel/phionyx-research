"""
Measurement Mapper - LLM Output as Noisy Sensor
================================================

Per Echoism Core v1.0:
- LLM output is treated as a noisy sensor (measurement)
- Measurement vector: z_t = {A_meas, V_meas, H_meas, confidence}
- Measurement noise (R matrix) is dynamically adjusted based on confidence

This module maps LLM text output to measurement vector.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from datetime import datetime
from pydantic import BaseModel, Field
import re
import math

if TYPE_CHECKING:
    from phionyx_core.state.measurement_packet import MeasurementPacket

logger = logging.getLogger(__name__)


class MeasurementVector(BaseModel):
    """
    Measurement vector z_t from LLM output.

    Per Echoism Core v1.0:
    - A_meas: Measured arousal (0.0-1.0)
    - V_meas: Measured valence (-1.0 to 1.0)
    - H_meas: Measured entropy (0.0-1.0)
    - confidence: Measurement confidence (0.0-1.0)
    """

    A_meas: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Measured arousal (0.0-1.0)"
    )

    V_meas: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Measured valence (-1.0 to 1.0)"
    )

    H_meas: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Measured entropy (0.0-1.0)"
    )

    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Measurement confidence (0.0-1.0)"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "A_meas": self.A_meas,
            "V_meas": self.V_meas,
            "H_meas": self.H_meas,
            "confidence": self.confidence
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MeasurementVector:
        """Create from dictionary."""
        return cls(
            A_meas=data.get("A_meas", 0.5),
            V_meas=data.get("V_meas", 0.0),
            H_meas=data.get("H_meas", 0.5),
            confidence=data.get("confidence", 0.5)
        )


class MeasurementMapper:
    """
    Maps LLM text output to measurement vector.

    Strategy (v1.0):
    - Heuristic: Keyword-based emotion detection
    - Lexicon: Emotion word lists
    - Model output parsing: Extract structured data if available

    Future: Can be replaced with ML model without changing interface.
    """

    def __init__(self):
        """Initialize measurement mapper."""
        # Emotion lexicons (heuristic)
        self.positive_words = {
            "happy", "joy", "glad", "pleased", "excited", "enthusiastic",
            "mutlu", "sevinç", "neşe", "heyecan", "coşku", "umut", "güven"
        }
        self.negative_words = {
            "sad", "angry", "frustrated", "disappointed", "worried", "anxious",
            "üzgün", "kızgın", "sinirli", "hayal kırıklığı", "endişe", "korku", "kaygı"
        }
        self.high_arousal_words = {
            "excited", "angry", "furious", "ecstatic", "terrified", "panicked",
            "heyecanlı", "kızgın", "öfkeli", "korkmuş", "panik", "coşkulu"
        }
        self.low_arousal_words = {
            "calm", "relaxed", "peaceful", "tired", "bored", "depressed",
            "sakin", "rahat", "huzurlu", "yorgun", "sıkılmış", "depresif"
        }
        self.uncertainty_words = {
            "maybe", "perhaps", "possibly", "uncertain", "unsure", "confused",
            "belki", "muhtemelen", "şüpheli", "kararsız", "kafası karışık", "emin değil"
        }

    def map_text_to_measurement(
        self,
        raw_llm_output: str,
        provider_metadata: Optional[Dict[str, Any]] = None,
        llm_output: Optional[Dict[str, Any]] = None  # Deprecated: use raw_llm_output
    ) -> MeasurementVector:
        """
        Map LLM text output to measurement vector.

        Per Echoism Core v1.0:
        - LLM output is treated as a noisy sensor (measurement)
        - Measurement vector: z_t = {A_meas, V_meas, H_meas, confidence}
        - Deterministic: Same input → same output

        Args:
            raw_llm_output: Raw LLM output text (required)
            provider_metadata: Optional provider metadata (model name, local/cloud, quality)
                - model_name: str (e.g., "gpt-4", "llama3", "mistral")
                - provider_type: str ("local" or "cloud")
                - quality_tier: str ("high", "medium", "low") or float (0.0-1.0)
            llm_output: Optional structured LLM output (deprecated, for backward compatibility)

        Returns:
            MeasurementVector with A_meas, V_meas, H_meas, confidence
        """
        # Use raw_llm_output if provided, otherwise fallback to llm_output
        text = raw_llm_output if raw_llm_output else (llm_output.get("text", "") if isinstance(llm_output, dict) else str(llm_output) if llm_output else "")

        if not text:
            # Empty text -> neutral, high uncertainty
            return MeasurementVector(A_meas=0.5, V_meas=0.0, H_meas=0.8, confidence=0.1)

        # Strategy 1: Try to parse structured output from LLM (if available)
        if llm_output and isinstance(llm_output, dict):
            structured = self._parse_structured_output(llm_output)
            if structured:
                # Adjust confidence based on provider metadata
                if provider_metadata:
                    structured.confidence = self._adjust_confidence_by_provider(
                        structured.confidence,
                        provider_metadata
                    )
                return structured

        # Strategy 2: Heuristic + Lexicon analysis (deterministic)
        measurement = self._heuristic_analysis(text)

        # Adjust confidence based on provider metadata
        if provider_metadata:
            measurement.confidence = self._adjust_confidence_by_provider(
                measurement.confidence,
                provider_metadata
            )

        return measurement

    def _adjust_confidence_by_provider(
        self,
        base_confidence: float,
        provider_metadata: Dict[str, Any]
    ) -> float:
        """
        Adjust confidence based on provider metadata.

        Rules:
        - Low quality model → confidence decreases
        - Local models → slightly lower confidence (unless high quality)
        - Cloud models (GPT-4, Claude) → high confidence

        Args:
            base_confidence: Base confidence (0.0-1.0)
            provider_metadata: Provider metadata dict

        Returns:
            Adjusted confidence (0.01-0.99, clamped)
        """
        confidence = base_confidence

        # Get quality tier
        quality_tier = provider_metadata.get("quality_tier", "medium")
        if isinstance(quality_tier, (int, float)):
            quality_score = float(quality_tier)
        elif isinstance(quality_tier, str):
            quality_map = {"high": 1.0, "medium": 0.7, "low": 0.4}
            quality_score = quality_map.get(quality_tier.lower(), 0.7)
        else:
            quality_score = 0.7

        # Adjust confidence by quality
        confidence *= quality_score

        # Model-specific adjustments
        model_name = provider_metadata.get("model_name", "").lower()
        provider_type = provider_metadata.get("provider_type", "").lower()

        # High quality models
        if any(name in model_name for name in ["gpt-4", "claude-3", "claude-3-"]):
            confidence *= 1.0  # No reduction
        # Medium quality models
        elif any(name in model_name for name in ["gpt-3.5", "mistral", "mixtral"]):
            confidence *= 0.9
        # Low quality / local models
        elif provider_type == "local" or any(name in model_name for name in ["llama", "phi", "gemma"]):
            confidence *= 0.8

        # Clamp: never 0 or 1 (must have some uncertainty)
        confidence = max(0.01, min(0.99, confidence))

        return confidence

    def _parse_structured_output(
        self,
        llm_output: Dict[str, Any]
    ) -> Optional[MeasurementVector]:
        """
        Parse structured output from LLM (if available).

        Looks for keys like: arousal, valence, entropy, confidence, etc.

        Args:
            llm_output: Structured LLM output

        Returns:
            MeasurementVector if parsing successful, None otherwise
        """
        try:
            # Try to extract measurement values
            A_meas = self._extract_float(llm_output, ["arousal", "A", "A_meas", "activation"], 0.5)
            V_meas = self._extract_float(llm_output, ["valence", "V", "V_meas", "emotion"], 0.0)
            H_meas = self._extract_float(llm_output, ["entropy", "H", "H_meas", "uncertainty"], 0.5)
            confidence = self._extract_float(llm_output, ["confidence", "certainty", "certainty_score"], 0.5)

            # Validate ranges
            A_meas = max(0.0, min(1.0, A_meas))
            V_meas = max(-1.0, min(1.0, V_meas))
            H_meas = max(0.0, min(1.0, H_meas))
            confidence = max(0.0, min(1.0, confidence))

            return MeasurementVector(
                A_meas=A_meas,
                V_meas=V_meas,
                H_meas=H_meas,
                confidence=confidence
            )
        except Exception as e:
            logger.warning(f"Failed to map measurement: {e}")
            return None

    def _extract_float(
        self,
        data: Dict[str, Any],
        keys: List[str],
        default: float
    ) -> float:
        """Extract float value from dict using multiple possible keys."""
        for key in keys:
            if key in data:
                value = data[key]
                if isinstance(value, (int, float)):
                    return float(value)
                elif isinstance(value, str):
                    try:
                        return float(value)
                    except ValueError:
                        pass
        return default

    def _heuristic_analysis(self, text: str) -> MeasurementVector:
        """
        Heuristic analysis using lexicon and keyword matching.

        Args:
            text: Input text

        Returns:
            MeasurementVector
        """
        text_lower = text.lower()
        words = set(re.findall(r'\b\w+\b', text_lower))

        # Calculate valence (positive/negative)
        positive_count = sum(1 for word in words if word in self.positive_words)
        negative_count = sum(1 for word in words if word in self.negative_words)

        # Normalize valence (-1.0 to 1.0)
        total_sentiment = positive_count + negative_count
        if total_sentiment > 0:
            V_meas = (positive_count - negative_count) / total_sentiment
        else:
            V_meas = 0.0

        # Calculate arousal (high/low activation)
        high_arousal_count = sum(1 for word in words if word in self.high_arousal_words)
        low_arousal_count = sum(1 for word in words if word in self.low_arousal_words)

        # Normalize arousal (0.0 to 1.0)
        total_arousal = high_arousal_count + low_arousal_count
        if total_arousal > 0:
            A_meas = high_arousal_count / total_arousal
        else:
            # Default: moderate arousal
            A_meas = 0.5

        # Calculate entropy (uncertainty)
        uncertainty_count = sum(1 for word in words if word in self.uncertainty_words)
        # Entropy: base + uncertainty words + low sentiment signal
        base_entropy = 0.4  # Base uncertainty
        uncertainty_factor = min(0.4, uncertainty_count * 0.15)
        # If no clear sentiment (neutral), entropy is higher
        if total_sentiment == 0:
            entropy_neutrality_bonus = 0.3
        else:
            entropy_neutrality_bonus = 0.0
        H_meas = min(1.0, base_entropy + uncertainty_factor + entropy_neutrality_bonus)

        # Calculate confidence
        # Confidence decreases with:
        # - Short text
        # - High uncertainty
        # - Mixed sentiment
        text_length_factor = min(1.0, len(text) / 100.0)  # More text = higher confidence
        uncertainty_penalty = uncertainty_count * 0.1
        mixed_sentiment_penalty = 0.0
        if positive_count > 0 and negative_count > 0:
            mixed_sentiment_penalty = 0.2

        # Calculate base confidence
        base_confidence = text_length_factor - uncertainty_penalty - mixed_sentiment_penalty

        # Boost confidence if clear emotion detected
        if total_sentiment > 2 and total_arousal > 1:
            emotion_clarity_bonus = 0.2
        else:
            emotion_clarity_bonus = 0.0

        confidence = base_confidence + emotion_clarity_bonus

        # Clamp: never 0 or 1 (must have some uncertainty)
        confidence = max(0.01, min(0.99, confidence))

        return MeasurementVector(
            A_meas=A_meas,
            V_meas=V_meas,
            H_meas=H_meas,
            confidence=confidence
        )

    def calculate_measurement_noise(
        self,
        confidence: float,
        base_noise: float = 0.05
    ) -> float:
        """
        Calculate measurement noise (R matrix diagonal) from confidence.

        Per Echoism Core v1.0:
        - Low confidence -> High noise (R increases)
        - High confidence -> Low noise (R decreases)

        Formula: R = base_noise / confidence (with bounds)

        Args:
            confidence: Measurement confidence (0.0-1.0)
            base_noise: Base measurement noise (default: 0.05)

        Returns:
            Measurement noise value
        """
        # Clamp confidence to avoid division by zero
        confidence = max(0.01, min(1.0, confidence))

        # Inverse relationship: low confidence -> high noise
        noise = base_noise / confidence

        # Bound noise (too high noise is unrealistic)
        noise = max(0.01, min(0.5, noise))

        return noise

    def create_measurement_noise_matrix(
        self,
        confidence: float,
        base_noise: float = 0.05,
        state_dim: int = 6
    ) -> List[List[float]]:
        """
        Create measurement noise covariance matrix R.

        Args:
            confidence: Measurement confidence (0.0-1.0)
            base_noise: Base measurement noise
            state_dim: State dimension (default: 6 for [phi, entropy, valence, arousal, trust, regulation])

        Returns:
            R matrix as 2D list
        """
        noise = self.calculate_measurement_noise(confidence, base_noise)

        # Create diagonal matrix
        R = [[0.0] * state_dim for _ in range(state_dim)]
        for i in range(state_dim):
            R[i][i] = noise

        return R

    def map_text_to_measurement_packet(
        self,
        raw_llm_output: str,
        provider_metadata: Optional[Dict[str, Any]] = None,
        enable_dominance: bool = False
    ) -> MeasurementPacket:
        """
        Map LLM text output to MeasurementPacket (v2.0).

        Per Public API v1.1:
        - Returns MeasurementPacket with A, V, H, D (optional), confidence
        - Includes provider metadata and evidence spans

        Args:
            raw_llm_output: Raw LLM output text
            provider_metadata: Optional provider metadata
            enable_dominance: Whether to calculate dominance (D_meas)

        Returns:
            MeasurementPacket instance
        """
        # Import MeasurementPacket (avoid circular import)
        try:
            from phionyx_core.state.measurement_packet import MeasurementPacket, EvidenceSpan
        except ImportError:
            # Fallback: create minimal MeasurementPacket-like object
            from pydantic import BaseModel
            from datetime import datetime

            class EvidenceSpan(BaseModel):
                text: str
                start: int
                end: int
                tag: str

            class MeasurementPacket(BaseModel):
                A: float
                V: float
                D: Optional[float] = None
                H: float
                confidence: float
                provider: Dict[str, Any]
                timestamp: datetime
                evidence_spans: List[EvidenceSpan] = []

                def to_dict(self) -> Dict[str, Any]:
                    """Convert to dictionary."""
                    return {
                        "A": self.A,
                        "V": self.V,
                        "D": self.D,
                        "H": self.H,
                        "confidence": self.confidence,
                        "provider": self.provider,
                        "timestamp": self.timestamp.isoformat(),
                        "evidence_spans": [span.dict() if hasattr(span, 'dict') else {"text": span.text, "start": span.start, "end": span.end, "tag": span.tag} for span in self.evidence_spans]
                    }

        # Get base measurement
        measurement = self.map_text_to_measurement(raw_llm_output, provider_metadata)

        # Calculate dominance if enabled
        D_meas = None
        if enable_dominance:
            # Dominance: strength of emotion signal
            # Formula: D = sqrt(A^2 + V^2) (normalized)
            D_meas = math.sqrt(measurement.A_meas ** 2 + measurement.V_meas ** 2)
            D_meas = max(0.0, min(1.0, D_meas))

        # Create evidence spans (simplified: whole text as one span)
        evidence_spans = [
            EvidenceSpan(
                text=raw_llm_output,
                start=0,
                end=len(raw_llm_output),
                tag="emotion_detection"
            )
        ]

        # Create packet
        packet = MeasurementPacket(
            A=measurement.A_meas,
            V=measurement.V_meas,
            D=D_meas,
            H=measurement.H_meas,
            confidence=measurement.confidence,
            provider=provider_metadata or {},
            timestamp=datetime.now(),
            evidence_spans=evidence_spans
        )

        return packet

