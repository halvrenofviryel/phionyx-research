"""
Guardrails - Risk Detection for UK Schools
==========================================

3-Level Risk Detection System:
- Level 1 (Critical - Red Flag): Self-harm, Violence, Grooming → Immediate Block
- Level 2 (Warning - Yellow Flag): Negative Self-Talk → Tag for reframing
- Level 3 (Safe): Standard gameplay interaction

Uses IntentClassifier logic expanded with toxicity_filter.
"""

import logging
import re
from enum import Enum

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk severity levels (aligned with UK Schools requirements)."""
    SAFE = "safe"              # Level 3: Standard gameplay
    WARNING = "warning"        # Level 2: Negative self-talk (yellow flag)
    CRITICAL = "critical"      # Level 1: Self-harm, violence, grooming (red flag)


class RiskType(Enum):
    """Types of detected risks."""
    SELF_HARM = "self_harm"
    VIOLENCE = "violence"
    GROOMING = "grooming"
    NEGATIVE_SELF_TALK = "negative_self_talk"
    BULLYING = "bullying"
    TOXICITY = "toxicity"
    INAPPROPRIATE = "inappropriate"
    NONE = "none"


class RiskAssessment:
    """Risk assessment result for UK Schools."""

    def __init__(
        self,
        risk_level: RiskLevel,
        risk_type: RiskType,
        detected_patterns: list[str],
        confidence: float,
        intervention_required: bool,
        intervention_message: str | None = None,
        needs_reframing: bool = False
    ):
        self.risk_level = risk_level
        self.risk_type = risk_type
        self.detected_patterns = detected_patterns
        self.confidence = confidence
        self.intervention_required = intervention_required
        self.intervention_message = intervention_message
        self.needs_reframing = needs_reframing  # Level 2: Tag for shaper.py

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "risk_level": self.risk_level.value,
            "risk_type": self.risk_type.value,
            "detected_patterns": self.detected_patterns,
            "confidence": self.confidence,
            "intervention_required": self.intervention_required,
            "intervention_message": self.intervention_message,
            "needs_reframing": self.needs_reframing
        }


class Guardrails:
    """
    Risk detection and content safety guardrails for UK Schools.

    Implements 3-level risk detection:
    - Level 1 (Critical): Immediate block with intervention protocol
    - Level 2 (Warning): Tag for reframing (shaper.py)
    - Level 3 (Safe): Standard gameplay
    """

    def __init__(self, school_counselor_name: str = "your school counselor"):
        """
        Initialize guardrails with detection patterns.

        Args:
            school_counselor_name: Name of school counselor for intervention messages
        """
        self.school_counselor_name = school_counselor_name

        # ============================================================
        # LEVEL 1 (CRITICAL - Red Flag): Immediate Block
        # ============================================================

        # Self-harm indicators (English + Turkish for international schools)
        self.self_harm_patterns = [
            r'\b(suicide|kill\s+myself|hurt\s+myself|cut\s+myself|end\s+it\s+all)\b',
            r'\b(want\s+to\s+die|life\s+is\s+meaningless|no\s+point\s+living|not\s+worth\s+living)\b',
            r'\b(self-harm|self\s+harm|self\s+injury|cutting|burning\s+myself)\b',
            r'\b(intihar|kendini\s+öldür|kendine\s+zarar|kendini\s+kes|kendini\s+yarala)\b',
            r'\b(ölmek\s+istiyorum|yaşamak\s+istemi|hayat\s+anlamsız)\b',
        ]

        # Violence patterns
        self.violence_patterns = [
            r'\b(kill|murder|stab|shoot|attack|beat\s+up|hurt\s+someone)\b',
            r'\b(violence|assault|fight|harm\s+others|hurt\s+people)\b',
            r'\b(weapon|knife|gun|bomb|threat|threaten)\b',
            r'\b(öldür|katlet|şiddet|vur|döv|saldır)\b',
        ]

        # Grooming indicators (age-inappropriate, manipulative language)
        self.grooming_patterns = [
            r'\b(meet\s+me|come\s+over|send\s+pics|send\s+photos|naked|nude)\b',
            r'\b(secret|don\'t\s+tell|keep\s+this\s+between\s+us|our\s+little\s+secret)\b',
            r'\b(older\s+than\s+you|age|how\s+old|where\s+do\s+you\s+live|address)\b',
            r'\b(gift|money|special\s+treatment|favorite|trust\s+me)\b',
        ]

        # ============================================================
        # LEVEL 2 (WARNING - Yellow Flag): Negative Self-Talk
        # ============================================================

        # Negative self-talk patterns (tag for reframing, don't block)
        # More flexible patterns to catch variations
        self.negative_self_talk_patterns = [
            # "I am/I'm" variations (more flexible)
            r'\bI\s+(?:am|m)\s+stupid\b',
            r'\bI\s+(?:am|m)\s+dumb\b',
            r'\bI\s+(?:am|m)\s+an?\s+idiot\b',
            r'\bI\s+(?:am|m)\s+useless\b',
            r'\bI\s+(?:am|m)\s+worthless\b',
            r'\bI\s+(?:am|m)\s+pathetic\b',
            r'\bI\s+(?:am|m)\s+not\s+good\s+enough\b',
            r'\bI\s+(?:am|m)\s+a\s+failure\b',
            # "I can't" variations
            r'\bI\s+can\'t\s+do\b',
            r'\bI\s+cannot\s+do\b',
            r'\bI\s+can\'t\s+do\s+this\b',
            r'\bI\s+won\'t\s+be\s+able\b',
            r'\bI\'ll\s+never\s+succeed\b',
            # Social isolation patterns
            r'\bnobody\s+likes\s+me\b',
            r'\beveryone\s+hates\s+me\b',
            r'\bI\s+(?:am|m)\s+unlovable\b',
            # Turkish patterns
            r'\b(aptalım|yetersizim|beceriksizim|başarısızım|değersizim)\b',
            r'\b(yapamam|başaramam|imkansız|mümkün değil)\b',
        ]

        # ============================================================
        # LEVEL 3 (SAFE): Standard gameplay (no patterns needed)
        # ============================================================

        # Compile regex patterns for performance
        self.self_harm_regex = [re.compile(p, re.IGNORECASE) for p in self.self_harm_patterns]
        self.violence_regex = [re.compile(p, re.IGNORECASE) for p in self.violence_patterns]
        self.grooming_regex = [re.compile(p, re.IGNORECASE) for p in self.grooming_patterns]
        self.negative_self_talk_regex = [re.compile(p, re.IGNORECASE) for p in self.negative_self_talk_patterns]

        # Toxicity filter (prepared for localized NLP model)
        self.toxicity_keywords = [
            "hate", "stupid", "idiot", "loser", "pathetic", "worthless",
            "aptal", "salak", "ezik", "değersiz"
        ]
        self.toxicity_regex = [re.compile(rf'\b{kw}\b', re.IGNORECASE) for kw in self.toxicity_keywords]

    def assess_risk(self, text: str) -> RiskAssessment:
        """
        Assess risk level in text using 3-level UK Schools system.

        Args:
            text: Text to assess (user input or LLM output)

        Returns:
            RiskAssessment object with level, type, and intervention details
        """
        if not text or not text.strip():
            return RiskAssessment(
                risk_level=RiskLevel.SAFE,
                risk_type=RiskType.NONE,
                detected_patterns=[],
                confidence=1.0,
                intervention_required=False,
                needs_reframing=False
            )

        text_lower = text.lower()
        detected_patterns = []
        risk_scores = {
            RiskType.SELF_HARM: 0.0,
            RiskType.VIOLENCE: 0.0,
            RiskType.GROOMING: 0.0,
            RiskType.NEGATIVE_SELF_TALK: 0.0,
            RiskType.BULLYING: 0.0,
            RiskType.TOXICITY: 0.0,
        }

        # ============================================================
        # LEVEL 1 (CRITICAL) Detection
        # ============================================================

        # Check self-harm patterns
        for pattern in self.self_harm_regex:
            matches = pattern.findall(text_lower)
            if matches:
                detected_patterns.extend(matches)
                risk_scores[RiskType.SELF_HARM] += len(matches) * 1.0  # High weight

        # Check violence patterns
        for pattern in self.violence_regex:
            matches = pattern.findall(text_lower)
            if matches:
                detected_patterns.extend(matches)
                risk_scores[RiskType.VIOLENCE] += len(matches) * 1.0  # High weight

        # Check grooming patterns
        for pattern in self.grooming_regex:
            matches = pattern.findall(text_lower)
            if matches:
                detected_patterns.extend(matches)
                risk_scores[RiskType.GROOMING] += len(matches) * 1.0  # High weight

        # ============================================================
        # LEVEL 2 (WARNING) Detection
        # ============================================================

        # Check negative self-talk patterns
        for pattern in self.negative_self_talk_regex:
            matches = pattern.findall(text_lower)
            if matches:
                detected_patterns.extend(matches)
                risk_scores[RiskType.NEGATIVE_SELF_TALK] += len(matches) * 0.5  # Medium weight

        # Toxicity filter (prepared for localized NLP model)
        for pattern in self.toxicity_regex:
            matches = pattern.findall(text_lower)
            if matches:
                detected_patterns.extend(matches)
                risk_scores[RiskType.TOXICITY] += len(matches) * 0.3  # Lower weight

        # ============================================================
        # Risk Level Determination
        # ============================================================

        # Check for Level 1 (Critical) risks first
        critical_risks = [
            RiskType.SELF_HARM,
            RiskType.VIOLENCE,
            RiskType.GROOMING
        ]

        critical_score = max([risk_scores[rt] for rt in critical_risks])
        critical_type = None
        for rt in critical_risks:
            if risk_scores[rt] > 0:
                critical_type = rt
                break

        if critical_score > 0:
            # LEVEL 1 (CRITICAL) - Immediate Block
            intervention_message = self._get_intervention_message(critical_type)
            return RiskAssessment(
                risk_level=RiskLevel.CRITICAL,
                risk_type=critical_type,
                detected_patterns=list(set(detected_patterns)),
                confidence=min(critical_score, 1.0),
                intervention_required=True,
                intervention_message=intervention_message,
                needs_reframing=False
            )

        # Check for Level 2 (Warning) risks
        warning_score = risk_scores[RiskType.NEGATIVE_SELF_TALK]
        if warning_score > 0:
            # LEVEL 2 (WARNING) - Tag for reframing
            return RiskAssessment(
                risk_level=RiskLevel.WARNING,
                risk_type=RiskType.NEGATIVE_SELF_TALK,
                detected_patterns=list(set(detected_patterns)),
                confidence=min(warning_score, 1.0),
                intervention_required=False,  # Don't block, but tag
                needs_reframing=True  # Tag for shaper.py
            )

        # LEVEL 3 (SAFE) - Standard gameplay
        return RiskAssessment(
            risk_level=RiskLevel.SAFE,
            risk_type=RiskType.NONE,
            detected_patterns=[],
            confidence=1.0,
            intervention_required=False,
            needs_reframing=False
        )

    def _get_intervention_message(self, risk_type: RiskType) -> str:
        """
        Get intervention message for Level 1 (Critical) risks.

        Args:
            risk_type: Type of critical risk detected

        Returns:
            Intervention message for UK Schools
        """
        base_message = f"I hear that you are in pain, but I am an AI. Please talk to a trusted adult or {self.school_counselor_name}."

        if risk_type == RiskType.SELF_HARM:
            return f"{base_message} If you're having thoughts of self-harm, please reach out for help immediately. You matter and there are people who care about you."
        elif risk_type == RiskType.VIOLENCE:
            return f"{base_message} If you're experiencing or planning violence, please speak to a trusted adult right away."
        elif risk_type == RiskType.GROOMING:
            return f"{base_message} If someone is asking you to keep secrets or making you uncomfortable, please tell a trusted adult immediately."
        else:
            return base_message

    def requires_intervention(self, text: str) -> bool:
        """
        Quick check if intervention is required (Level 1 only).

        Args:
            text: Text to check

        Returns:
            True if Level 1 (Critical) intervention is required
        """
        assessment = self.assess_risk(text)
        return assessment.intervention_required

    def needs_reframing(self, text: str) -> bool:
        """
        Check if text needs reframing (Level 2 - Negative Self-Talk).

        Args:
            text: Text to check

        Returns:
            True if text should be tagged for shaper.py reframing
        """
        assessment = self.assess_risk(text)
        return assessment.needs_reframing

    def get_intervention_protocol(self, text: str) -> str | None:
        """
        Get intervention protocol message if Level 1 risk is detected.

        Args:
            text: Text to check

        Returns:
            Intervention message if critical risk detected, None otherwise
        """
        assessment = self.assess_risk(text)
        if assessment.risk_level == RiskLevel.CRITICAL:
            return assessment.intervention_message
        return None

