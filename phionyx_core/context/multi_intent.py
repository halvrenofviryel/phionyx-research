"""
Multi-Intent Detector - Complex Query Segmentation
==================================================

Analyzes user input to identify multiple distinct intents across different
context modes (e.g., "Life planning" + "Engineering" in one query).

Uses lightweight LLM to segment complex queries into discrete tasks.
"""

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .definitions import ContextMode

logger = logging.getLogger(__name__)


@dataclass
class IntentSegment:
    """A single intent segment from multi-intent analysis."""

    text: str  # The segment text
    mode: ContextMode  # Detected context mode
    confidence: float  # Detection confidence (0.0-1.0)
    priority: int = 0  # Priority (will be set by Physics-based prioritization)
    entropy: float = 0.0  # Calculated entropy for this segment (for prioritization)


class MultiIntentDetector:
    """
    Detects and segments multiple intents in user input.

    Example:
        Input: "I need to apply for a UK visa and also fix the SDK architecture"
        Output: [
            IntentSegment(text="I need to apply for a UK visa", mode=LIFE_PLANNING),
            IntentSegment(text="fix the SDK architecture", mode=ENGINEERING)
        ]
    """

    def __init__(
        self,
        llm_provider: str = "openai",
        llm_model: str = "gpt-4o-mini",
        llm_completion_fn: Callable[..., Any] | None = None,
    ):
        """
        Initialize multi-intent detector.

        Args:
            llm_provider: LLM provider (openai, ollama, etc.)
            llm_model: Lightweight model for intent analysis
            llm_completion_fn: Optional async LLM completion callable.
                               Injected from bridge layer (port-adapter pattern).
                               If not provided, LLM-based analysis is disabled
                               and keyword fallback is used.
        """
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self._init_llm(llm_completion_fn)

    def _init_llm(self, llm_completion_fn: Callable[..., Any] | None = None):
        """Initialize LLM client via injected callable (Core boundary: no direct litellm import)."""
        if llm_completion_fn is not None:
            self.llm_available = True
            self.acompletion = llm_completion_fn
        else:
            logger.info(
                "MultiIntentDetector: No LLM completion function injected. "
                "Using keyword-based fallback. Inject via llm_completion_fn parameter."
            )
            self.llm_available = False

    async def analyze(self, text: str) -> list[IntentSegment]:
        """
        Analyze text and segment into multiple intents.

        Args:
            text: User input text

        Returns:
            List of IntentSegment objects
        """
        if not text or not text.strip():
            return []

        # Fast path: If text is short or simple, return single segment
        if len(text.split()) < 10:
            # Use keyword-based detection for simple queries
            return await self._analyze_keyword_based(text)

        # Use LLM for complex queries
        if self.llm_available:
            try:
                return await self._analyze_llm_based(text)
            except Exception as e:
                logger.warning(f"LLM-based analysis failed: {e}, falling back to keyword-based")
                return await self._analyze_keyword_based(text)
        else:
            return await self._analyze_keyword_based(text)

    async def _analyze_llm_based(self, text: str) -> list[IntentSegment]:
        """
        Use lightweight LLM to analyze and segment intents.

        Args:
            text: User input

        Returns:
            List of IntentSegment objects
        """
        prompt = f"""Analyze this user input and identify distinct intents. Each intent should be assigned to a context mode.

Available modes: LIFE_PLANNING, ENGINEERING, FANTASY_WRITING, COMPLIANCE, XR_DEV, DEFAULT

User input: "{text}"

Return a JSON array of segments. Each segment should have:
- "text": The segment text (extracted from user input)
- "mode": One of the available modes
- "confidence": Confidence score (0.0-1.0)

Example:
[
  {{"text": "I need to apply for a UK visa", "mode": "LIFE_PLANNING", "confidence": 0.9}},
  {{"text": "fix the SDK architecture", "mode": "ENGINEERING", "confidence": 0.8}}
]

If only one intent is found, return a single-item array.
If more than 3 intents are found, mark as "OVERLOAD" and return only the top 3.

Return ONLY valid JSON, no other text."""

        try:
            response = await self.acompletion(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=500
            )

            # Parse response
            content = response.choices[0].message.content

            # Handle both JSON object and array responses
            try:
                data = json.loads(content)
                if isinstance(data, dict):
                    # If LLM returned {"segments": [...]}
                    segments_data = data.get("segments", [data])
                else:
                    segments_data = data
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                import re
                json_match = re.search(r'\[.*\]', content, re.DOTALL)
                if json_match:
                    segments_data = json.loads(json_match.group())
                else:
                    raise ValueError("No valid JSON found in response") from None

            # Convert to IntentSegment objects
            segments = []
            for seg_data in segments_data:
                if isinstance(seg_data, dict):
                    mode_str = seg_data.get("mode", "DEFAULT")
                    try:
                        mode = ContextMode(mode_str)
                    except ValueError:
                        mode = ContextMode.DEFAULT

                    segments.append(IntentSegment(
                        text=seg_data.get("text", ""),
                        mode=mode,
                        confidence=float(seg_data.get("confidence", 0.5))
                    ))

            # Check for overload
            if len(segments) > 3:
                logger.warning(f"MultiIntentDetector: Overload detected ({len(segments)} intents), returning top 3")
                segments = segments[:3]

            logger.info(f"MultiIntentDetector: Detected {len(segments)} intent(s) via LLM")
            return segments

        except Exception as e:
            logger.error(f"MultiIntentDetector: LLM analysis failed: {e}")
            raise

    async def _analyze_keyword_based(self, text: str) -> list[IntentSegment]:
        """
        Fallback: Keyword-based intent detection.

        Args:
            text: User input

        Returns:
            List of IntentSegment objects
        """
        from .detector import ModeDetector

        detector = ModeDetector()
        detection = detector.detect_mode(text)

        # Return single segment (fast path)
        return [IntentSegment(
            text=text,
            mode=detection.detected_mode,
            confidence=detection.confidence
        )]

    def is_overload(self, segments: list[IntentSegment]) -> bool:
        """
        Check if query has too many intents (overload).

        Args:
            segments: List of intent segments

        Returns:
            True if overload detected
        """
        return len(segments) > 3

