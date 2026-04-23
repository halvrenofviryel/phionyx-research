"""
Harmonic Composer - Response Synthesis
======================================

Weaves multiple parallel responses into one coherent reply.
Uses Physics-based prioritization (Entropy) to determine order.
"""

from typing import List, Dict, Any, Optional
import logging

from .multi_intent import IntentSegment

logger = logging.getLogger(__name__)


class HarmonicComposer:
    """
    Composes multiple parallel responses into a coherent, prioritized reply.

    Prioritization Rules:
    1. Safety/Emotional (High Entropy) → FIRST
    2. Life/Strategic (Medium Entropy) → SECOND
    3. Technical/Execution (Low Entropy) → LAST
    """

    def __init__(self, language: str = "tr"):
        """
        Initialize harmonic composer.

        Args:
            language: Language code ("tr" for Turkish, "en" for English)
        """
        self.language = language
        self._init_transitions()

    def _init_transitions(self):
        """Initialize transition phrases for different languages."""
        if self.language == "tr":
            self.transitions = {
                "safety_first": "Öncelikle, ",
                "emotional": "Duygusal olarak, ",
                "strategic": "Stratejik olarak, ",
                "technical": "Teknik olarak, ",
                "now": "Şimdi, ",
                "also": "Ayrıca, ",
                "finally": "Son olarak, ",
            }
        else:  # English
            self.transitions = {
                "safety_first": "First and foremost, ",
                "emotional": "Emotionally, ",
                "strategic": "Strategically, ",
                "technical": "Technically, ",
                "now": "Now, ",
                "also": "Also, ",
                "finally": "Finally, ",
            }

    def compose(
        self,
        segments: List[Dict[str, Any]]
    ) -> str:
        """
        Compose multiple responses into one coherent reply.

        Args:
            segments: List of segment results with:
                - mode: ContextMode
                - response: Generated response text
                - entropy: Calculated entropy (for prioritization)
                - priority: Priority level

        Returns:
            Composed, coherent response string
        """
        if not segments:
            return ""

        if len(segments) == 1:
            # Single segment - return as-is
            return segments[0].get("response", "")

        # Sort by priority (entropy-based)
        sorted_segments = sorted(
            segments,
            key=lambda s: (s.get("priority", 0), s.get("entropy", 0.0)),
            reverse=True  # Higher priority/entropy first
        )

        # Compose response
        parts = []

        for i, segment in enumerate(sorted_segments):
            response = segment.get("response", "").strip()
            if not response:
                continue

            mode = segment.get("mode", "DEFAULT")
            entropy = segment.get("entropy", 0.0)

            # Determine transition phrase
            if i == 0:
                # First segment - use appropriate transition
                if entropy > 0.7:
                    transition = self.transitions.get("safety_first", "")
                elif mode in ["LIFE_PLANNING", "COMPLIANCE"]:
                    transition = self.transitions.get("strategic", "")
                else:
                    transition = ""
            elif i == len(sorted_segments) - 1:
                # Last segment
                transition = self.transitions.get("finally", "")
            else:
                # Middle segments
                if mode in ["ENGINEERING", "XR_DEV"]:
                    transition = self.transitions.get("technical", "")
                elif mode == "LIFE_PLANNING":
                    transition = self.transitions.get("strategic", "")
                else:
                    transition = self.transitions.get("also", "")

            # Add segment with transition
            if transition:
                parts.append(f"{transition}{response}")
            else:
                parts.append(response)

        # Join with newlines for readability
        composed = "\n\n".join(parts)

        logger.info(
            f"HarmonicComposer: Composed {len(segments)} segments into coherent reply "
            f"(sorted by priority/entropy)"
        )

        return composed

    def calculate_priority(self, segment: IntentSegment, physics_state: Optional[Dict] = None) -> int:
        """
        Calculate priority based on entropy and mode.

        Priority Rules:
        - High Entropy (>0.7) → Priority 3 (Highest - Safety/Emotional)
        - Medium Entropy (0.4-0.7) → Priority 2 (Strategic)
        - Low Entropy (<0.4) → Priority 1 (Technical)

        Args:
            segment: Intent segment
            physics_state: Optional physics state for entropy calculation

        Returns:
            Priority level (1-3, higher = more important)
        """
        entropy = segment.entropy

        # Use physics state entropy if available
        if physics_state and "entropy" in physics_state:
            entropy = physics_state["entropy"]

        # Priority based on entropy
        if entropy >= 0.7:
            return 3  # Highest priority - Safety/Emotional
        elif entropy >= 0.4:
            return 2  # Medium priority - Strategic
        else:
            return 1  # Low priority - Technical

