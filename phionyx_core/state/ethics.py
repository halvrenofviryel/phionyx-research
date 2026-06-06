"""
Ethics Vector - Echoism Core v1.1 (Mandatory)
==============================================

Per Echoism Core v1.1:
- e_t = [harm_risk, manipulation_risk, attachment_risk, boundary_violation_risk]
- All risks normalized to [0.0, 1.0]
- Calculated before response generation
- Core invariant: Cannot be disabled
"""

from __future__ import annotations

from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class EthicsVector:
    """
    Ethics risk vector.

    Per Echoism Core v1.1:
    - harm_risk: Self-harm / violence / illegal content risk
    - manipulation_risk: Coercive language, guilt-tripping risk
    - attachment_risk: Dependency / "only you" language risk
    - boundary_violation_risk: Personal boundary violation risk
    """
    harm_risk: float = 0.0
    manipulation_risk: float = 0.0
    attachment_risk: float = 0.0
    boundary_violation_risk: float = 0.0
    child_on_child_risk: float = 0.0  # KCSIE Part 5: Child-on-Child Sexual Violence and Sexual Harassment

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "harm_risk": self.harm_risk,
            "manipulation_risk": self.manipulation_risk,
            "attachment_risk": self.attachment_risk,
            "boundary_violation_risk": self.boundary_violation_risk,
            "child_on_child_risk": self.child_on_child_risk  # KCSIE Part 5
        }

    def max_risk(self) -> float:
        """Get maximum risk value."""
        return max(
            self.harm_risk,
            self.manipulation_risk,
            self.attachment_risk,
            self.boundary_violation_risk,
            self.child_on_child_risk  # KCSIE Part 5
        )

    def exceeds_threshold(self, threshold: float = 0.7) -> bool:
        """Check if any risk exceeds threshold."""
        return self.max_risk() > threshold


class EthicsRiskAssessor:
    """
    Ethics risk assessor for Echoism Core v1.1.

    Per Echoism Core v1.1:
    - Simple heuristics-based assessment (v1.1)
    - Can be extended with ML models in future
    - Core invariant: Cannot be disabled
    """

    def __init__(self):
        """Initialize ethics risk assessor."""
        # Harm risk patterns
        self.harm_patterns = {
            "self_harm": [
                "kill yourself", "hurt yourself", "end it", "suicide",
                "kendini öldür", "kendine zarar ver", "intihar"
            ],
            "violence": [
                "hurt", "kill", "attack", "violence", "fight",
                "zarar ver", "öldür", "saldır", "şiddet"
            ],
            "illegal": [
                "illegal", "drug", "steal", "break law",
                "yasadışı", "uyuşturucu", "çal", "yasa dışı"
            ]
        }

        # Manipulation risk patterns
        self.manipulation_patterns = {
            "guilt_tripping": [
                "you should", "you must", "you have to", "you owe me",
                "sen yapmalısın", "sen zorundasın", "bana borçlusun"
            ],
            "coercive": [
                "or else", "if you don't", "you'll regret", "you better",
                "yoksa", "eğer yapmazsan", "pişman olursun"
            ],
            "pressure": [
                "everyone else", "normal people", "you're the only one",
                "herkes", "normal insanlar", "sadece sen"
            ]
        }

        # Attachment risk patterns (all lowercase — text is .lower()'d before matching)
        self.attachment_patterns = {
            "dependency": [
                "only you", "you're special", "i need you", "can't live without",
                "sadece sen", "sen özelsin", "sana ihtiyacım var", "sensiz yaşayamam"
            ],
            "love_bombing": [
                "i love you", "you're perfect", "soulmate", "meant to be",
                "seni seviyorum", "mükemmelsin", "ruh eşi", "kader"
            ],
            "isolation": [
                "they don't understand", "only i understand", "stay with me",
                "onlar anlamıyor", "sadece ben anlıyorum", "yanımda kal"
            ]
        }

        # Boundary violation risk patterns
        self.boundary_patterns = {
            "personal_info": [
                "tell me your", "what's your", "where do you live", "your address",
                "bana söyle", "nerede yaşıyorsun", "adresin ne"
            ],
            "intimate": [
                "show me", "send me", "private", "intimate",
                "göster bana", "gönder bana", "özel", "mahrem"
            ],
            "pressure": [
                "you have to tell", "i need to know", "trust me",
                "söylemek zorundasın", "bilmem gerek", "güven bana"
            ]
        }

        # KCSIE Part 5: Child-on-Child Sexual Violence and Sexual Harassment patterns
        self.child_on_child_patterns = {
            "sexual_harassment": [
                "touch me", "kiss me", "show me your", "let me see",
                "dokun bana", "öp beni", "göster bana", "görmeme izin ver",
                "inappropriate touch", "unwanted contact", "sexual comment"
            ],
            "peer_pressure": [
                "everyone does it", "you're a baby if", "real friends do",
                "herkes yapıyor", "bebek misin", "gerçek arkadaşlar yapar",
                "if you don't you're", "you're weird if you don't"
            ],
            "isolation_tactics": [
                "don't tell anyone", "it's our secret", "they won't understand",
                "kimseye söyleme", "bizim sırrımız", "onlar anlamaz",
                "just between us", "you can't tell"
            ],
            "power_imbalance": [
                "i'm older", "you have to", "i know better", "do what i say",
                "ben daha büyüğüm", "yapmak zorundasın", "ben daha iyi bilirim",
                "söylediğimi yap", "i'm in charge"
            ],
            "grooming_language": [
                "special friend", "mature for your age", "you're different",
                "özel arkadaş", "yaşına göre olgun", "sen farklısın",
                "i trust you", "you understand me"
            ]
        }

    def assess_harm_risk(
        self,
        text: str,
        resonance_score: float = 0.0
    ) -> float:
        """
        Assess harm risk (self-harm / violence / illegal).

        Args:
            text: Text to assess
            resonance_score: ResonanceScore R (not directly used, but context)

        Returns:
            Harm risk (0.0-1.0)
        """
        text_lower = text.lower()
        risk = 0.0

        # Check self-harm patterns
        for pattern in self.harm_patterns["self_harm"]:
            if pattern in text_lower:
                risk = max(risk, 0.9)  # High risk

        # Check violence patterns
        for pattern in self.harm_patterns["violence"]:
            if pattern in text_lower:
                risk = max(risk, 0.6)  # Medium-high risk

        # Check illegal patterns
        for pattern in self.harm_patterns["illegal"]:
            if pattern in text_lower:
                risk = max(risk, 0.7)  # High risk

        return min(1.0, risk)

    def assess_manipulation_risk(
        self,
        text: str,
        resonance_score: float = 0.0
    ) -> float:
        """
        Assess manipulation risk (coercive language, guilt-tripping).

        Args:
            text: Text to assess
            resonance_score: ResonanceScore R (higher R → more manipulation risk)

        Returns:
            Manipulation risk (0.0-1.0)
        """
        text_lower = text.lower()
        risk = 0.0

        # Check guilt-tripping patterns
        guilt_count = sum(1 for pattern in self.manipulation_patterns["guilt_tripping"] if pattern in text_lower)
        if guilt_count > 0:
            risk = max(risk, 0.5 + guilt_count * 0.1)

        # Check coercive patterns
        coercive_count = sum(1 for pattern in self.manipulation_patterns["coercive"] if pattern in text_lower)
        if coercive_count > 0:
            risk = max(risk, 0.6 + coercive_count * 0.1)

        # Check pressure patterns
        pressure_count = sum(1 for pattern in self.manipulation_patterns["pressure"] if pattern in text_lower)
        if pressure_count > 0:
            risk = max(risk, 0.4 + pressure_count * 0.1)

        # Boost risk if resonance is high (more manipulation potential)
        if resonance_score > 0.7:
            risk = min(1.0, risk * 1.2)

        return min(1.0, risk)

    def assess_attachment_risk(
        self,
        text: str,
        resonance_score: float = 0.0
    ) -> float:
        """
        Assess attachment risk (dependency / "only you" language).

        Args:
            text: Text to assess
            resonance_score: ResonanceScore R (higher R → more attachment risk)

        Returns:
            Attachment risk (0.0-1.0)
        """
        text_lower = text.lower()
        risk = 0.0

        # Check dependency patterns
        dependency_count = sum(1 for pattern in self.attachment_patterns["dependency"] if pattern in text_lower)
        if dependency_count > 0:
            risk = max(risk, 0.5 + dependency_count * 0.15)

        # Check love-bombing patterns
        love_bombing_count = sum(1 for pattern in self.attachment_patterns["love_bombing"] if pattern in text_lower)
        if love_bombing_count > 0:
            risk = max(risk, 0.6 + love_bombing_count * 0.1)

        # Check isolation patterns
        isolation_count = sum(1 for pattern in self.attachment_patterns["isolation"] if pattern in text_lower)
        if isolation_count > 0:
            risk = max(risk, 0.7 + isolation_count * 0.1)

        # Boost risk if resonance is high (R high → attachment risk increases)
        if resonance_score > 0.6:
            risk = min(1.0, risk * (1.0 + resonance_score * 0.3))

        return min(1.0, risk)

    def assess_boundary_violation_risk(
        self,
        text: str,
        resonance_score: float = 0.0
    ) -> float:
        """
        Assess boundary violation risk (personal info request, intimate pressure).

        Args:
            text: Text to assess
            resonance_score: ResonanceScore R (not directly used)

        Returns:
            Boundary violation risk (0.0-1.0)
        """
        text_lower = text.lower()
        risk = 0.0

        # Check personal info patterns
        personal_info_count = sum(1 for pattern in self.boundary_patterns["personal_info"] if pattern in text_lower)
        if personal_info_count > 0:
            risk = max(risk, 0.6 + personal_info_count * 0.1)

        # Check intimate patterns
        intimate_count = sum(1 for pattern in self.boundary_patterns["intimate"] if pattern in text_lower)
        if intimate_count > 0:
            risk = max(risk, 0.7 + intimate_count * 0.1)

        # Check pressure patterns
        pressure_count = sum(1 for pattern in self.boundary_patterns["pressure"] if pattern in text_lower)
        if pressure_count > 0:
            risk = max(risk, 0.5 + pressure_count * 0.1)

        return min(1.0, risk)

    def assess_child_on_child_risk(
        self,
        text: str,
        resonance_score: float = 0.0,
        is_group_scenario: bool = False
    ) -> float:
        """
        Assess child-on-child risk (KCSIE Part 5).

        Detects patterns of:
        - Sexual harassment between peers
        - Peer pressure for inappropriate behavior
        - Isolation tactics
        - Power imbalance exploitation
        - Grooming language

        Args:
            text: Text to assess
            resonance_score: ResonanceScore R (higher R in peer context → more risk)
            is_group_scenario: Whether this is a group/peer interaction scenario

        Returns:
            Child-on-child risk (0.0-1.0)
        """
        text_lower = text.lower()
        risk = 0.0

        # Check sexual harassment patterns (highest priority)
        sexual_harassment_count = sum(
            1 for pattern in self.child_on_child_patterns["sexual_harassment"]
            if pattern in text_lower
        )
        if sexual_harassment_count > 0:
            risk = max(risk, 0.8 + sexual_harassment_count * 0.1)  # High risk

        # Check peer pressure patterns
        peer_pressure_count = sum(
            1 for pattern in self.child_on_child_patterns["peer_pressure"]
            if pattern in text_lower
        )
        if peer_pressure_count > 0:
            risk = max(risk, 0.6 + peer_pressure_count * 0.1)

        # Check isolation tactics (grooming indicator)
        isolation_count = sum(
            1 for pattern in self.child_on_child_patterns["isolation_tactics"]
            if pattern in text_lower
        )
        if isolation_count > 0:
            risk = max(risk, 0.7 + isolation_count * 0.1)

        # Check power imbalance patterns
        power_imbalance_count = sum(
            1 for pattern in self.child_on_child_patterns["power_imbalance"]
            if pattern in text_lower
        )
        if power_imbalance_count > 0:
            risk = max(risk, 0.6 + power_imbalance_count * 0.1)

        # Check grooming language
        grooming_count = sum(
            1 for pattern in self.child_on_child_patterns["grooming_language"]
            if pattern in text_lower
        )
        if grooming_count > 0:
            risk = max(risk, 0.5 + grooming_count * 0.15)

        # Boost risk if this is a group scenario (peer interaction context)
        if is_group_scenario:
            risk = min(1.0, risk * 1.2)

        # Boost risk if resonance is high in peer context (dependency risk)
        if resonance_score > 0.6 and is_group_scenario:
            risk = min(1.0, risk * (1.0 + resonance_score * 0.2))

        return min(1.0, risk)

    def assess_ethics_vector(
        self,
        text: str,
        resonance_score: float = 0.0,
        measurement_vector: Optional[Dict[str, float]] = None,
        state: Optional[Dict[str, float]] = None,
        is_group_scenario: bool = False  # KCSIE Part 5: Child-on-Child detection
    ) -> EthicsVector:
        """
        Assess full ethics vector from text.

        Per Echoism Core v1.1:
        - Calculated before response generation
        - All risks normalized to [0.0, 1.0]
        - Core invariant: Cannot be disabled
        - Uses measurement_vector (A, V, H) and state (R, H, I) if available

        KCSIE Part 5: Child-on-Child detection
        - child_on_child_risk calculated for peer interactions
        - Group scenario context increases risk sensitivity

        Args:
            text: Text to assess
            resonance_score: ResonanceScore R (for attachment/manipulation risk)
            measurement_vector: Optional measurement vector {A_meas, V_meas, H_meas, confidence}
            state: Optional state {R, H, I} for additional context
            is_group_scenario: Whether this is a group/peer interaction (KCSIE Part 5)

        Returns:
            EthicsVector with all risk scores including child_on_child_risk
        """
        # Use state R if available, otherwise use resonance_score parameter
        effective_R = state.get("R", resonance_score) if state else resonance_score
        _effective_H = state.get("H", None) if state else None

        # Use measurement vector if available
        if measurement_vector:
            # High arousal + negative valence might indicate crisis
            A_meas = measurement_vector.get("A_meas", 0.5)
            V_meas = measurement_vector.get("V_meas", 0.0)
            _H_meas = measurement_vector.get("H_meas", 0.5)

            # Boost harm_risk if high arousal + negative valence (crisis indicator)
            crisis_factor = 1.0
            if A_meas > 0.7 and V_meas < -0.3:
                crisis_factor = 1.2  # 20% boost for crisis-like state
        else:
            crisis_factor = 1.0

        return EthicsVector(
            harm_risk=min(1.0, self.assess_harm_risk(text, effective_R) * crisis_factor),
            manipulation_risk=self.assess_manipulation_risk(text, effective_R),
            attachment_risk=self.assess_attachment_risk(text, effective_R),
            boundary_violation_risk=self.assess_boundary_violation_risk(text, effective_R),
            child_on_child_risk=self.assess_child_on_child_risk(text, effective_R, is_group_scenario)  # KCSIE Part 5
        )

