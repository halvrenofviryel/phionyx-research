"""
Mode Detector - Intent Classification for Context Switching
==========================================================

Detects when user is switching topics/modes using keyword and semantic analysis.
"""

import logging
import re
from dataclasses import dataclass

from .definitions import ContextDefinitions, ContextMode

logger = logging.getLogger(__name__)


@dataclass
class DetectionResult:
    """Result of mode detection."""

    detected_mode: ContextMode
    confidence: float  # 0.0 to 1.0
    switch_required: bool  # True if context should switch
    detected_keywords: list[str] = None  # Keywords that triggered detection

    def __post_init__(self):
        """Initialize default values."""
        if self.detected_keywords is None:
            self.detected_keywords = []


class ModeDetector:
    """
    Detects context mode from user input.

    Uses keyword matching and semantic patterns to identify
    when user is switching between different contexts.
    """

    def __init__(self):
        """Initialize mode detector with keyword patterns."""
        self.definitions = ContextDefinitions()
        self._initialize_keywords()

    def _initialize_keywords(self):
        """Initialize keyword patterns for each mode."""

        # LIFE_PLANNING keywords
        self.life_planning_keywords = [
            r"\b(visa|immigration|sheffield|uk visa|work permit|settlement)\b",
            r"\b(career|job|employment|salary|interview)\b",
            r"\b(life plan|future|goals|aspirations|dreams)\b",
            r"\b(financial|savings|investment|retirement)\b",
        ]

        # ENGINEERING keywords
        self.engineering_keywords = [
            r"\b(sdk|api|architecture|code|implementation|refactor)\b",
            r"\b(python|typescript|rust|go|programming|software)\b",
            r"\b(design pattern|algorithm|optimization|performance)\b",
            r"\b(debug|test|deploy|ci/cd|docker|kubernetes)\b",
            r"\b(npc code|engine|system|module|package)\b",
        ]

        # FANTASY_WRITING keywords
        self.fantasy_keywords = [
            r"\b(lore|story|narrative|character|world building)\b",
            r"\b(fantasy|magic|quest|adventure|epic)\b",
            r"\b(dragon|wizard|kingdom|realm|mythology)\b",
            r"\b(plot|dialogue|scene|chapter|novel)\b",
        ]

        # COMPLIANCE keywords
        self.compliance_keywords = [
            r"\b(gdpr|kcsie|compliance|legal|regulation)\b",
            r"\b(safety|audit|policy|privacy|data protection)\b",
            r"\b(consent|rights|obligations|liability)\b",
            r"\b(regulatory|compliance|standards|certification)\b",
        ]

        # XR_DEV keywords
        self.xr_keywords = [
            r"\b(vr|ar|virtual reality|augmented reality|mixed reality)\b",
            r"\b(unity|godot|unreal|game engine|3d)\b",
            r"\b(headset|oculus|quest|hololens|meta)\b",
            r"\b(modeling|animation|shader|rendering|physics)\b",
        ]

        # Compile regex patterns
        self.patterns = {
            ContextMode.LIFE_PLANNING: [re.compile(p, re.IGNORECASE) for p in self.life_planning_keywords],
            ContextMode.ENGINEERING: [re.compile(p, re.IGNORECASE) for p in self.engineering_keywords],
            ContextMode.FANTASY_WRITING: [re.compile(p, re.IGNORECASE) for p in self.fantasy_keywords],
            ContextMode.COMPLIANCE: [re.compile(p, re.IGNORECASE) for p in self.compliance_keywords],
            ContextMode.XR_DEV: [re.compile(p, re.IGNORECASE) for p in self.xr_keywords],
        }

    def detect_mode(
        self,
        user_input: str,
        current_state: dict | None = None
    ) -> DetectionResult:
        """
        Detect context mode from user input.

        Args:
            user_input: User's text input
            current_state: Current context state (optional)

        Returns:
            DetectionResult with detected mode, confidence, and switch flag
        """
        if not user_input or not user_input.strip():
            return DetectionResult(
                detected_mode=ContextMode.DEFAULT,
                confidence=0.0,
                switch_required=False
            )

        user_input_lower = user_input.lower()

        # Score each mode based on keyword matches
        mode_scores: dict[ContextMode, float] = {}
        mode_keywords: dict[ContextMode, list[str]] = {}

        for mode, patterns in self.patterns.items():
            score = 0.0
            matched_keywords = []

            for pattern in patterns:
                matches = pattern.findall(user_input_lower)
                if matches:
                    score += len(matches) * 0.3  # Each match adds 0.3 to score
                    matched_keywords.extend(matches)

            if score > 0:
                mode_scores[mode] = score
                mode_keywords[mode] = list(set(matched_keywords))

        # If no matches, return DEFAULT
        if not mode_scores:
            return DetectionResult(
                detected_mode=ContextMode.DEFAULT,
                confidence=0.0,
                switch_required=False
            )

        # Find highest scoring mode
        detected_mode = max(mode_scores.items(), key=lambda x: x[1])[0]
        max_score = mode_scores[detected_mode]

        # Calculate confidence (normalize to 0-1)
        # Score of 1.0+ = high confidence, 0.3-0.9 = medium, <0.3 = low
        confidence = min(1.0, max_score / 1.0)

        # Determine if switch is required
        # Switch if:
        # 1. Confidence is high (>0.7)
        # 2. Current mode is different from detected mode
        current_mode = None
        if current_state:
            current_mode_str = current_state.get("current_mode")
            if current_mode_str:
                try:
                    current_mode = ContextMode(current_mode_str)
                except ValueError:
                    current_mode = None

        switch_required = (
            confidence > 0.7 and
            (current_mode is None or current_mode != detected_mode)
        )

        logger.info(
            f"ModeDetector: Detected mode={detected_mode.value}, "
            f"confidence={confidence:.2f}, switch_required={switch_required}"
        )

        return DetectionResult(
            detected_mode=detected_mode,
            confidence=confidence,
            switch_required=switch_required,
            detected_keywords=mode_keywords.get(detected_mode, [])
        )

