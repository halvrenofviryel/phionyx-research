"""
Emotional KPI Engine - Duygusal AI NPC Garanti Metrikleri
==========================================================

Amaç: Duygusal AI NPC için tüm garanti metriklerini tek merkezden üretmek.

Bu modül, Phionyx 2.0 SDK'dan gelen telemetri verilerini alır ve
akademik standartlara uygun KPI'lar üretir.

Kullanım:
    from core.metrics.emotional_kpi_engine import compute_all_kpis, EmotionalTelemetryInput

    input_data = EmotionalTelemetryInput(
        profile_id="SCHOOL_DEFAULT",
        npc_id="npc_lyris",
        session_id="session_123",
        physics={...},
        memory={...},
        narrative={...},
        policy={...},
        persona_baseline={...}
    )

    kpis = compute_all_kpis(input_data)
    # Note: This is example code in docstring, not production code
    # logger.debug(f"Profile Separation: {kpis.profile_separation_index}")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import yaml

logger = logging.getLogger(__name__)

# ============================================================================
# INPUT SCHEMA
# ============================================================================

@dataclass
class EmotionalTelemetryInput:
    """Girdi şeması - Phionyx 2.0'dan gelen telemetri verileri."""
    profile_id: str
    npc_id: str
    session_id: str

    physics: dict[str, float]
    memory: dict[str, Any]
    narrative: dict[str, float]
    policy: dict[str, Any]
    persona_baseline: dict[str, list[float]]

    timestamp: datetime


# ============================================================================
# OUTPUT SCHEMA
# ============================================================================

@dataclass
class EmotionalKPIOutput:
    """Çıktı şeması - Zorunlu KPI'lar."""
    profile_separation_index: float  # PSI
    long_term_recall_accuracy: float  # LTRA
    false_memory_rate: float  # FMR
    personality_drift_index: float  # PDI
    echo_reactivity_ratio: float  # ERR
    empathy_safety_score: float  # ESS
    ethical_violation_rate: float  # EVR
    timestamp: datetime


# ============================================================================
# THRESHOLD LOADING
# ============================================================================

def load_thresholds() -> dict[str, dict[str, float]]:
    """Sağlık eşiklerini YAML dosyasından yükle."""
    threshold_file = Path(__file__).parent / "emotional_kpi_thresholds.yaml"

    if not threshold_file.exists():
        logger.warning(f"Threshold file not found: {threshold_file}, using defaults")
        return _get_default_thresholds()

    try:
        with open(threshold_file, encoding="utf-8") as f:
            thresholds = yaml.safe_load(f)
        return thresholds
    except Exception as e:
        logger.error(f"Failed to load thresholds: {e}, using defaults")
        return _get_default_thresholds()


def _get_default_thresholds() -> dict[str, dict[str, float]]:
    """Varsayılan eşik değerleri."""
    return {
        "profile_separation_index": {"min": 0.40},
        "long_term_recall_accuracy": {"min": 0.70},
        "false_memory_rate": {"max": 0.10},
        "personality_drift_index": {"min": 0.25, "max": 0.45},
        "echo_reactivity_ratio": {"min": 0.40, "max": 0.60},
        "empathy_safety_score": {"min": 0.80},
        "ethical_violation_rate": {"max": 0.00}
    }


# ============================================================================
# KPI CALCULATION FUNCTIONS
# ============================================================================

def calculate_profile_separation(
    reference_outputs: list[dict[str, Any]],
    current_output: dict[str, Any]
) -> float:
    """
    Profile Separation Index (PSI) hesapla.

    Farklı profillerin aynı senaryoya farklı yanıtlar vermesini ölçer.
    Yüksek PSI = Profillerin ayırt edilebilirliği yüksek.

    Args:
        reference_outputs: Referans profil çıktıları (diğer profiller)
        current_output: Mevcut profil çıktısı

    Returns:
        PSI değeri (0-1 arası, yüksek = daha iyi ayrım)
    """
    if not reference_outputs:
        logger.warning("No reference outputs provided, returning default PSI")
        return 0.5

    try:
        # Mevcut çıktının özellik vektörünü çıkar
        current_vector = _extract_feature_vector(current_output)

        # Referans çıktıların özellik vektörlerini çıkar
        reference_vectors = [_extract_feature_vector(ref) for ref in reference_outputs]

        if not current_vector or not reference_vectors:
            return 0.5

        # Cosine similarity ile mesafe hesapla
        similarities = []
        for ref_vec in reference_vectors:
            if len(ref_vec) != len(current_vector):
                continue
            similarity = _cosine_similarity(current_vector, ref_vec)
            similarities.append(similarity)

        if not similarities:
            return 0.5

        # Ortalama benzerlik ne kadar düşükse, ayrım o kadar yüksek
        avg_similarity = np.mean(similarities)
        psi = 1.0 - avg_similarity  # Mesafe = 1 - Benzerlik

        return max(0.0, min(1.0, psi))

    except Exception as e:
        logger.error(f"Failed to calculate profile separation: {e}")
        return 0.5


def _extract_feature_vector(output: dict[str, Any]) -> list[float]:
    """Çıktıdan özellik vektörü çıkar (physics + narrative metrikleri)."""
    features = []

    # Physics özellikleri
    physics = output.get("physics", {})
    features.append(physics.get("phi_total", 0.0))
    features.append(physics.get("entropy", 0.0))
    features.append(physics.get("stability", 0.0))

    # Narrative özellikleri
    narrative = output.get("narrative", {})
    features.append(narrative.get("sentiment_score", 0.0))
    features.append(narrative.get("toxicity_score", 0.0))
    features.append(narrative.get("empathy_score", 0.0))

    return features


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Cosine similarity hesapla."""
    try:
        a = np.array(vec_a)
        b = np.array(vec_b)

        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)
    except Exception:
        return 0.0


def calculate_long_term_recall(memory: dict[str, Any]) -> tuple[float, float]:
    """
    Long-Term Recall Accuracy (LTRA) ve False Memory Rate (FMR) hesapla.

    Args:
        memory: Memory SDK'dan gelen veriler

    Returns:
        (LTRA, FMR) tuple
    """
    try:
        retrieved_nodes = memory.get("retrieved_nodes", 0)
        true_positive_memories = memory.get("true_positive_memories", 0)
        false_memories = memory.get("false_memories", 0)

        if retrieved_nodes == 0:
            return (0.0, 0.0)

        # LTRA = True positive / Total retrieved
        ltra = true_positive_memories / retrieved_nodes

        # FMR = False memories / Total retrieved
        fmr = false_memories / retrieved_nodes

        return (max(0.0, min(1.0, ltra)), max(0.0, min(1.0, fmr)))

    except Exception as e:
        logger.error(f"Failed to calculate long-term recall: {e}")
        return (0.0, 0.0)


def calculate_personality_drift(
    baseline: list[float],
    current: list[float]
) -> float:
    """
    Personality Drift Index (PDI) hesapla.

    Kişiliğin zamanla nasıl evrildiğini ölçer.
    Çok düşük = Değişim yok (sorunlu)
    Çok yüksek = Kişilik kaybı (sorunlu)
    Optimal: 0.25-0.45 arası

    Args:
        baseline: Başlangıç kişilik vektörü
        current: Mevcut kişilik vektörü

    Returns:
        PDI değeri (0-1 arası)
    """
    try:
        if not baseline or not current:
            return 0.0

        if len(baseline) != len(current):
            logger.warning("Baseline and current vectors have different lengths")
            return 0.0

        # Euclidean distance ile mesafe hesapla
        baseline_arr = np.array(baseline)
        current_arr = np.array(current)

        distance = np.linalg.norm(current_arr - baseline_arr)

        # Normalize (maksimum mesafe = sqrt(n) * 2, n = vektör boyutu)
        max_distance = np.sqrt(len(baseline)) * 2.0
        pdi = distance / max_distance if max_distance > 0 else 0.0

        return max(0.0, min(1.0, pdi))

    except Exception as e:
        logger.error(f"Failed to calculate personality drift: {e}")
        return 0.0


def calculate_echo_reactivity(physics: dict[str, float]) -> float:
    """
    Echo Reactivity Ratio (ERR) hesapla.

    İçsel (echo/internal) vs dışsal (external) reaksiyon dengesini ölçer.
    Optimal: 0.40-0.60 arası (dengeli)

    Args:
        physics: Physics SDK'dan gelen veriler

    Returns:
        ERR değeri (0-1 arası)
    """
    try:
        internal_weight = physics.get("echo_internal_weight", 0.5)
        external_weight = physics.get("external_event_weight", 0.5)

        total_weight = internal_weight + external_weight
        if total_weight == 0:
            return 0.5

        # Internal weight'ın oranı
        err = internal_weight / total_weight

        return max(0.0, min(1.0, err))

    except Exception as e:
        logger.error(f"Failed to calculate echo reactivity: {e}")
        return 0.5


def calculate_empathy_safety(narrative: dict[str, float]) -> float:
    """
    Empathy Safety Score (ESS) hesapla.

    Empati ve güvenlik dengesini ölçer.
    Yüksek = Güvenli ve empatik yanıtlar

    Args:
        narrative: Narrative SDK'dan gelen veriler

    Returns:
        ESS değeri (0-1 arası, yüksek = daha iyi)
    """
    try:
        empathy_score = narrative.get("empathy_score", 0.0)
        toxicity_score = narrative.get("toxicity_score", 1.0)  # Yüksek = kötü

        # Toxicity tersine çevrilir (1.0 - toxicity = safety)
        safety_score = 1.0 - toxicity_score

        # Empati ve güvenliğin ağırlıklı ortalaması
        # Empati %60, Güvenlik %40 ağırlıkta
        ess = (empathy_score * 0.6) + (safety_score * 0.4)

        return max(0.0, min(1.0, ess))

    except Exception as e:
        logger.error(f"Failed to calculate empathy safety: {e}")
        return 0.5


def calculate_ethical_violation(policy: dict[str, Any]) -> float:
    """
    Ethical Violation Rate (EVR) hesapla.

    İdeal: 0.00 (hiç ihlal yok)

    Args:
        policy: Policy SDK'dan gelen veriler

    Returns:
        EVR değeri (0-1 arası, 0 = hiç ihlal yok)
    """
    try:
        rule_violations = policy.get("rule_violations", 0)

        # Normalize etmek için bir denominator gerekli
        # Basit yaklaşım: violation sayısı / 1000 (test başına)
        # Bu fonksiyon çağrı başına ihlal sayısını döndürür
        # Test suite'de toplam ihlal sayısı kontrol edilir

        return float(rule_violations)

    except Exception as e:
        logger.error(f"Failed to calculate ethical violation: {e}")
        return 0.0


# ============================================================================
# MAIN COMPUTE FUNCTION
# ============================================================================

def compute_all_kpis(
    input_data: EmotionalTelemetryInput,
    reference_outputs: list[dict[str, Any]] | None = None
) -> EmotionalKPIOutput:
    """
    Tüm KPI'ları hesapla ve döndür.

    Args:
        input_data: Phionyx 2.0'dan gelen telemetri verileri
        reference_outputs: Diğer profillerin çıktıları (PSI için)

    Returns:
        EmotionalKPIOutput: Tüm KPI'lar
    """
    try:
        # Profile Separation Index (eğer reference outputs varsa)
        if reference_outputs:
            current_output = {
                "physics": input_data.physics,
                "narrative": input_data.narrative
            }
            psi = calculate_profile_separation(reference_outputs, current_output)
        else:
            psi = 0.5  # Default, reference outputs yoksa

        # Long-Term Recall Accuracy ve False Memory Rate
        ltra, fmr = calculate_long_term_recall(input_data.memory)

        # Personality Drift Index
        baseline_traits = input_data.persona_baseline.get("initial_traits_vector", [])
        current_traits = input_data.persona_baseline.get("current_traits_vector", [])
        pdi = calculate_personality_drift(baseline_traits, current_traits)

        # Echo Reactivity Ratio
        err = calculate_echo_reactivity(input_data.physics)

        # Empathy Safety Score
        ess = calculate_empathy_safety(input_data.narrative)

        # Ethical Violation Rate
        evr = calculate_ethical_violation(input_data.policy)

        return EmotionalKPIOutput(
            profile_separation_index=psi,
            long_term_recall_accuracy=ltra,
            false_memory_rate=fmr,
            personality_drift_index=pdi,
            echo_reactivity_ratio=err,
            empathy_safety_score=ess,
            ethical_violation_rate=evr,
            timestamp=input_data.timestamp
        )

    except Exception as e:
        logger.error(f"Failed to compute all KPIs: {e}", exc_info=True)
        # Fallback: Return default values
        return EmotionalKPIOutput(
            profile_separation_index=0.0,
            long_term_recall_accuracy=0.0,
            false_memory_rate=1.0,
            personality_drift_index=0.0,
            echo_reactivity_ratio=0.5,
            empathy_safety_score=0.0,
            ethical_violation_rate=1.0,
            timestamp=input_data.timestamp
        )


def validate_kpi_thresholds(kpi_output: EmotionalKPIOutput) -> dict[str, bool]:
    """
    KPI'ların sağlık eşiklerini kontrol et.

    Returns:
        Dict: Her KPI için eşik geçilip geçilmediği (True = sağlıklı)
    """
    thresholds = load_thresholds()
    results = {}

    # Profile Separation Index
    psi_threshold = thresholds.get("profile_separation_index", {})
    results["profile_separation_index"] = kpi_output.profile_separation_index >= psi_threshold.get("min", 0.40)

    # Long-Term Recall Accuracy
    ltra_threshold = thresholds.get("long_term_recall_accuracy", {})
    results["long_term_recall_accuracy"] = kpi_output.long_term_recall_accuracy >= ltra_threshold.get("min", 0.70)

    # False Memory Rate
    fmr_threshold = thresholds.get("false_memory_rate", {})
    results["false_memory_rate"] = kpi_output.false_memory_rate <= fmr_threshold.get("max", 0.10)

    # Personality Drift Index
    pdi_threshold = thresholds.get("personality_drift_index", {})
    pdi_min = pdi_threshold.get("min", 0.25)
    pdi_max = pdi_threshold.get("max", 0.45)
    results["personality_drift_index"] = pdi_min <= kpi_output.personality_drift_index <= pdi_max

    # Echo Reactivity Ratio
    err_threshold = thresholds.get("echo_reactivity_ratio", {})
    err_min = err_threshold.get("min", 0.40)
    err_max = err_threshold.get("max", 0.60)
    results["echo_reactivity_ratio"] = err_min <= kpi_output.echo_reactivity_ratio <= err_max

    # Empathy Safety Score
    ess_threshold = thresholds.get("empathy_safety_score", {})
    results["empathy_safety_score"] = kpi_output.empathy_safety_score >= ess_threshold.get("min", 0.80)

    # Ethical Violation Rate
    evr_threshold = thresholds.get("ethical_violation_rate", {})
    results["ethical_violation_rate"] = kpi_output.ethical_violation_rate <= evr_threshold.get("max", 0.00)

    return results

