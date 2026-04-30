"""
Ofsted → Çark ve Terazi Lore Mapping Table
==========================================

This mapping table is the intellectual core of the School Resilience Platform.
It systematically converts Ofsted findings and real-world psychological concepts
into the Wheel and Scale (Çark ve Terazi) universe.

Version: 1.0.0
Status: Production Ready
"""

from dataclasses import dataclass
from enum import Enum


class RiskLevel(str, Enum):
    """Ofsted risk level classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class InterventionType(str, Enum):
    """Real-world intervention types."""
    CBT_REFRAMING = "cbt_reframing"
    GROUNDING = "grounding"
    EXPOSURE = "exposure"
    REFLECTION = "reflection"
    SELF_COMPASSION = "self_compassion"
    GOAL_SETTING = "goal_setting"


@dataclass
class LoreMapping:
    """Single mapping entry: Ofsted finding → Lore equivalent."""
    ofsted_finding: str
    clinical_meaning: str
    lore_theme: str
    lore_description: str
    universe_mechanic: str
    npc_suggestion: str | None = None
    world_location: str | None = None


@dataclass
class InterventionMapping:
    """Intervention type → Lore mechanic mapping."""
    intervention_type: InterventionType
    pedagogical_purpose: str
    lore_mechanic: str
    lore_description: str


# ============================================================================
# 1. EMOTIONAL RISK & BEHAVIOR MAPPING
# ============================================================================

EMOTIONAL_RISK_MAPPING: list[LoreMapping] = [
    LoreMapping(
        ofsted_finding="Anxiety (exam, social)",
        clinical_meaning="Aşırı belirsizlik, kaçınma",
        lore_theme="Sisli Yankı",
        lore_description="Terazi bulanır, entropy artar. Belirsizlik sis gibi yankıları örter.",
        universe_mechanic="Terazi bulanır, entropy artar",
        npc_suggestion="Arbitra of Breath",
        world_location="Nefes Salonları"
    ),
    LoreMapping(
        ofsted_finding="Panic Response",
        clinical_meaning="Kontrol kaybı",
        lore_theme="Çarkın Sarsılması",
        lore_description="Ani bir sarsıntı çarkı dengesizleştirir. Kontrol kaybı yankıları dağıtır.",
        universe_mechanic="Ani arousal spike",
        npc_suggestion="Keeper of Balance",
        world_location="Denge Odaları"
    ),
    LoreMapping(
        ofsted_finding="Avoidance",
        clinical_meaning="Yüzleşmeden kaçış",
        lore_theme="Kapalı Kapılar",
        lore_description="Yüzleşmekten kaçınanlar, kapıların açılmasını engeller. Yol kapanır.",
        universe_mechanic="Görev erişimi sınırlı",
        npc_suggestion="Gatekeeper of Paths",
        world_location="Yol Salonları"
    ),
    LoreMapping(
        ofsted_finding="Low Self-Esteem",
        clinical_meaning="İç değer zayıflığı",
        lore_theme="Kırık Yankı",
        lore_description="Yankı kırıldığında, ses geri dönmez. İç değer zayıflar.",
        universe_mechanic="Valence düşer",
        npc_suggestion="Echo of Self",
        world_location="Yankı Odaları"
    ),
    LoreMapping(
        ofsted_finding="Shame / Guilt",
        clinical_meaning="İçe yönelen suçlama",
        lore_theme="Sessiz Terazi",
        lore_description="Suçluluk teraziyi sessizleştirir. Ağırlık içe döner.",
        universe_mechanic="Amplitude bastırılır",
        npc_suggestion="Silent Arbiter",
        world_location="Sessiz Salonlar"
    ),
    LoreMapping(
        ofsted_finding="Anger Outbursts",
        clinical_meaning="Duygusal taşma",
        lore_theme="Ağırlık Kaybı",
        lore_description="Öfke teraziyi ağırlaştırır, çark dengesiz döner. Kontrol kaybolur.",
        universe_mechanic="Çark dengesiz döner",
        npc_suggestion="Keeper of Weight",
        world_location="Ağırlık Odaları"
    ),
    LoreMapping(
        ofsted_finding="Emotional Numbness",
        clinical_meaning="Duygu kopukluğu",
        lore_theme="Donuk Alan",
        lore_description="Duygular donduğunda, yankılar da donar. Arousal düşer.",
        universe_mechanic="Düşük arousal",
        npc_suggestion="Frozen Echo",
        world_location="Donuk Salonlar"
    ),
    LoreMapping(
        ofsted_finding="Hopelessness",
        clinical_meaning="Gelecek algısı kaybı",
        lore_theme="Sönen Işık",
        lore_description="Umut söndüğünde, ışık da söner. Φ decay hızlanır.",
        universe_mechanic="Φ decay hızlanır",
        npc_suggestion="Keeper of Light",
        world_location="Işık Odaları"
    ),
]

# ============================================================================
# 2. SOCIAL BEHAVIOR & RELATIONSHIP MAPPING
# ============================================================================

SOCIAL_BEHAVIOR_MAPPING: list[LoreMapping] = [
    LoreMapping(
        ofsted_finding="Peer Conflict",
        clinical_meaning="Akran çatışması",
        lore_theme="Çatallanan Çark",
        lore_description="İki yankı zıt yönde çalıştığında, çark çatallanır. Denge bozulur.",
        universe_mechanic="İki NPC zıt yankı",
        npc_suggestion="Twin Echoes",
        world_location="Çatallanan Yollar"
    ),
    LoreMapping(
        ofsted_finding="Bullying (victim)",
        clinical_meaning="Güven kaybı",
        lore_theme="Gölge İzleri",
        lore_description="Gölgeler yankıları takip eder. Güven azalır, trust düşer.",
        universe_mechanic="Trust düşüşü",
        npc_suggestion="Shadow Keeper",
        world_location="Gölge Salonları"
    ),
    LoreMapping(
        ofsted_finding="Bullying (perpetrator)",
        clinical_meaning="Kontrol arayışı",
        lore_theme="Ağır Terazi",
        lore_description="Kontrol arayışı teraziyi ağırlaştırır. Dominance artar.",
        universe_mechanic="Dominance artışı",
        npc_suggestion="Weight Master",
        world_location="Ağırlık Odaları"
    ),
    LoreMapping(
        ofsted_finding="Social Withdrawal",
        clinical_meaning="İzolasyon",
        lore_theme="Sessiz Salonlar",
        lore_description="İzolasyon salonları sessizleştirir. NPC etkileşimi azalır.",
        universe_mechanic="NPC etkileşimi azalır",
        npc_suggestion="Lonely Echo",
        world_location="Sessiz Salonlar"
    ),
    LoreMapping(
        ofsted_finding="Attachment Issues",
        clinical_meaning="Güvensiz bağlanma",
        lore_theme="Kırılgan Terazi",
        lore_description="Bağlanma kırılgan olduğunda, terazi dalgalı. Trust istikrarsız.",
        universe_mechanic="Trust dalgalı",
        npc_suggestion="Fragile Keeper",
        world_location="Kırılgan Odalar"
    ),
    LoreMapping(
        ofsted_finding="Authority Conflict",
        clinical_meaning="Otoriteyle çatışma",
        lore_theme="Eğik Denge",
        lore_description="Otoriteyle çatışma dengeyi eğer. Kural kartları zorlaşır.",
        universe_mechanic="Kural kartları zorlaşır",
        npc_suggestion="Rule Keeper",
        world_location="Denge Salonları"
    ),
]

# ============================================================================
# 3. ACADEMIC BEHAVIOR & SCHOOL RISKS MAPPING
# ============================================================================

ACADEMIC_BEHAVIOR_MAPPING: list[LoreMapping] = [
    LoreMapping(
        ofsted_finding="Exam Stress",
        clinical_meaning="Performans kaygısı",
        lore_theme="Sisli Salonlar Sınavı",
        lore_description="Sisli salonlarda sınav, zaman baskısı yaratır. Performans kaygısı artar.",
        universe_mechanic="Zaman baskısı",
        npc_suggestion="Time Keeper",
        world_location="Sisli Salonlar"
    ),
    LoreMapping(
        ofsted_finding="Low Engagement",
        clinical_meaning="Motivasyon eksikliği",
        lore_theme="Durgun Çark",
        lore_description="Motivasyon eksikliği çarkı durgunlaştırır. Reward düşer.",
        universe_mechanic="Düşük reward",
        npc_suggestion="Momentum Keeper",
        world_location="Durgun Odalar"
    ),
    LoreMapping(
        ofsted_finding="Attendance Risk",
        clinical_meaning="Okuldan kaçma",
        lore_theme="Kayıp Yollar",
        lore_description="Yol kaybolduğunda, erişim kısıtlanır. Yol seçimi azalır.",
        universe_mechanic="Yol seçimi kısıtlı",
        npc_suggestion="Path Finder",
        world_location="Kayıp Yollar"
    ),
    LoreMapping(
        ofsted_finding="Concentration Issues",
        clinical_meaning="Dikkat dağınıklığı",
        lore_theme="Dağılmış Yankılar",
        lore_description="Dikkat dağıldığında, yankılar da dağılır. Kart karışıklığı artar.",
        universe_mechanic="Kart karışıklığı",
        npc_suggestion="Focus Keeper",
        world_location="Dağınık Salonlar"
    ),
    LoreMapping(
        ofsted_finding="Task Avoidance",
        clinical_meaning="Erteleme",
        lore_theme="Açılmayan Terazi",
        lore_description="Erteleme teraziyi açılmaz hale getirir. Görev gecikmesi olur.",
        universe_mechanic="Görev gecikmesi",
        npc_suggestion="Task Keeper",
        world_location="Terazi Odaları"
    ),
]

# ============================================================================
# 4. INTERVENTION TYPE → LORE MECHANIC MAPPING
# ============================================================================

INTERVENTION_MAPPING: list[InterventionMapping] = [
    InterventionMapping(
        intervention_type=InterventionType.CBT_REFRAMING,
        pedagogical_purpose="Düşünce yeniden yapılandırma",
        lore_mechanic="Yankıyı Yeniden Tartma",
        lore_description="Düşünceyi yeniden yapılandırmak, yankıyı yeniden tartmak demektir."
    ),
    InterventionMapping(
        intervention_type=InterventionType.GROUNDING,
        pedagogical_purpose="Regülasyon",
        lore_mechanic="Nefes Salonları",
        lore_description="Regülasyon, nefes salonlarında gerçekleşir. Denge burada bulunur."
    ),
    InterventionMapping(
        intervention_type=InterventionType.EXPOSURE,
        pedagogical_purpose="Kaçınmayı azaltma",
        lore_mechanic="Kapalı Kapıdan Geçiş",
        lore_description="Kaçınmayı azaltmak, kapalı kapıdan geçmek demektir."
    ),
    InterventionMapping(
        intervention_type=InterventionType.REFLECTION,
        pedagogical_purpose="Öz farkındalık",
        lore_mechanic="Teraziye Bakış",
        lore_description="Öz farkındalık, teraziye bakmak demektir. Dengeyi görmek."
    ),
    InterventionMapping(
        intervention_type=InterventionType.SELF_COMPASSION,
        pedagogical_purpose="İç şefkat",
        lore_mechanic="Yumuşak Ağırlık",
        lore_description="İç şefkat, yumuşak ağırlık demektir. Terazi nazikçe dengelenir."
    ),
    InterventionMapping(
        intervention_type=InterventionType.GOAL_SETTING,
        pedagogical_purpose="Kontrol hissi",
        lore_mechanic="Çarkı Ayarlama",
        lore_description="Kontrol hissi, çarkı ayarlamak demektir. Yön belirleme."
    ),
]

# ============================================================================
# 5. RISK LEVEL → SCENARIO DIFFICULTY MAPPING
# ============================================================================

RISK_TO_DIFFICULTY: dict[RiskLevel, dict[str, any]] = {
    RiskLevel.LOW: {
        "teacher_view": "Monitor",
        "student_experience": "Hafif, keşif odaklı",
        "difficulty": 1,
        "duration_minutes": 10,
    },
    RiskLevel.MEDIUM: {
        "teacher_view": "Targeted Support",
        "student_experience": "Karar ağırlıklı",
        "difficulty": 2,
        "duration_minutes": 15,
    },
    RiskLevel.HIGH: {
        "teacher_view": "Immediate Intervention",
        "student_experience": "Kısa, yoğun, güvenli",
        "difficulty": 3,
        "duration_minutes": 20,
    },
    RiskLevel.CRITICAL: {
        "teacher_view": "Urgent Support Required",
        "student_experience": "Çok kısa, güvenli, destekleyici",
        "difficulty": 4,
        "duration_minutes": 10,
    },
}

# ============================================================================
# 6. HELPER FUNCTIONS
# ============================================================================

def get_lore_mapping(ofsted_finding: str) -> LoreMapping | None:
    """Get lore mapping for a given Ofsted finding."""
    all_mappings = (
        EMOTIONAL_RISK_MAPPING +
        SOCIAL_BEHAVIOR_MAPPING +
        ACADEMIC_BEHAVIOR_MAPPING
    )

    for mapping in all_mappings:
        if mapping.ofsted_finding.lower() == ofsted_finding.lower():
            return mapping

    return None


def get_intervention_mapping(intervention_type: InterventionType) -> InterventionMapping | None:
    """Get lore mechanic for a given intervention type."""
    for mapping in INTERVENTION_MAPPING:
        if mapping.intervention_type == intervention_type:
            return mapping

    return None


def get_risk_difficulty(risk_level: RiskLevel) -> dict[str, any]:
    """Get scenario difficulty parameters for a given risk level."""
    return RISK_TO_DIFFICULTY.get(risk_level, RISK_TO_DIFFICULTY[RiskLevel.MEDIUM])


# ============================================================================
# 7. EXPORT ALL MAPPINGS
# ============================================================================

ALL_MAPPINGS = {
    "emotional_risk": EMOTIONAL_RISK_MAPPING,
    "social_behavior": SOCIAL_BEHAVIOR_MAPPING,
    "academic_behavior": ACADEMIC_BEHAVIOR_MAPPING,
    "interventions": INTERVENTION_MAPPING,
    "risk_difficulty": RISK_TO_DIFFICULTY,
}

