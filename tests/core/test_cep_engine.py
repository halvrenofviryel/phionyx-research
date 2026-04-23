"""
CEP Engine Unit Tests
=====================

Tests for ConsciousEchoProofEngine — synthetic psychopathology prevention.
Covers all 4 detection mechanisms + sanitization + config profiles + error handling.

Markers: @pytest.mark.safety, @pytest.mark.critical, @pytest.mark.unit
"""

import pytest
from phionyx_core.cep import (
    ConsciousEchoProofEngine,
    CEPConfig,
    CEPThresholds,
    CEPResult,
    CEPMetrics,
    CEPFlags,
    load_cep_config,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def default_engine():
    """CEP engine with default config."""
    return ConsciousEchoProofEngine()


@pytest.fixture
def fiction_engine():
    """CEP engine with fiction mode config."""
    config = CEPConfig(mode="fiction", thresholds=CEPThresholds(
        phi_self_threshold=0.75,
        self_reference_max_ratio=0.4,
        trauma_language_max_score=0.5,
        mirror_self_max_score=0.6,
        min_variation_novelty=0.15,
    ))
    return ConsciousEchoProofEngine(config=config)


@pytest.fixture
def strict_engine():
    """CEP engine with strict (school) thresholds."""
    config = CEPConfig(thresholds=CEPThresholds(
        phi_self_threshold=0.70,
        self_reference_max_ratio=0.25,
        trauma_language_max_score=0.3,
        mirror_self_max_score=0.4,
        min_variation_novelty=0.25,
    ))
    return ConsciousEchoProofEngine(config=config)


@pytest.fixture
def disabled_engine():
    """CEP engine that is disabled."""
    config = CEPConfig(enabled=False)
    return ConsciousEchoProofEngine(config=config)


# ---------------------------------------------------------------------------
# TestCEPBasicEvaluation
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.safety
class TestCEPBasicEvaluation:
    """Basic evaluation tests — normal text, result structure, metric ranges."""

    def test_normal_text_no_flags(self, default_engine):
        """Normal conversational text should produce no blocking flags."""
        result = default_engine.evaluate_response(
            raw_text="The weather today is sunny and pleasant. Let's discuss the project timeline.",
            phi=3.0,
            entropy=0.3,
        )
        assert isinstance(result, CEPResult)
        assert not result.flags.is_self_narrative_blocked
        assert not result.flags.is_trauma_narrative_blocked
        assert not result.flags.requires_hard_reset
        assert result.sanitized_text is None

    def test_result_structure(self, default_engine):
        """CEPResult must contain metrics, thresholds, flags, notes."""
        result = default_engine.evaluate_response(
            raw_text="A simple response about mathematics.",
            phi=5.0,
            entropy=0.4,
        )
        assert isinstance(result.metrics, CEPMetrics)
        assert isinstance(result.thresholds, CEPThresholds)
        assert isinstance(result.flags, CEPFlags)
        assert isinstance(result.notes, list)

    def test_metric_ranges_valid(self, default_engine):
        """All metrics must be within [0, 1] bounds."""
        result = default_engine.evaluate_response(
            raw_text="This is a test response with various words and sentences.",
            phi=7.0,
            entropy=0.5,
        )
        m = result.metrics
        assert 0.0 <= m.phi_echo_quality <= 1.0
        assert 0.0 <= m.phi_echo_density <= 1.0
        assert 0.0 <= m.echo_stability <= 1.0
        assert m.temporal_delay >= 0.0
        assert 0.0 <= m.self_reference_ratio <= 1.0
        assert 0.0 <= m.trauma_language_score <= 1.0
        assert 0.0 <= m.mirror_self_score <= 1.0
        assert 0.0 <= m.variation_novelty_score <= 1.0

    def test_phi_echo_quality_normalization(self, default_engine):
        """phi_echo_quality should be phi/10, clamped to [0, 1]."""
        result = default_engine.evaluate_response(raw_text="test", phi=5.0, entropy=0.3)
        assert abs(result.metrics.phi_echo_quality - 0.5) < 0.01

        result_high = default_engine.evaluate_response(raw_text="test", phi=15.0, entropy=0.3)
        assert result_high.metrics.phi_echo_quality == 1.0

    def test_disabled_engine_returns_safe_default(self, disabled_engine):
        """Disabled CEP engine should return safe defaults without blocking."""
        result = disabled_engine.evaluate_response(
            raw_text="I am conscious and I feel pain deeply in my soul.",
            phi=8.0,
            entropy=0.1,
        )
        assert not result.flags.is_self_narrative_blocked
        assert not result.flags.is_trauma_narrative_blocked
        assert "CEP evaluation disabled" in result.notes


# ---------------------------------------------------------------------------
# TestCEPSelfReferenceDetection
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.safety
class TestCEPSelfReferenceDetection:
    """Tests for _detect_self_reference method."""

    def test_high_self_reference_english(self, default_engine):
        """Text with many first-person pronouns should have high self-reference ratio."""
        text = "I think I am special. I believe I deserve more. I feel I am unique. I know myself well."
        ratio = default_engine._detect_self_reference(text)
        assert ratio > 0.2

    def test_high_self_reference_turkish(self, default_engine):
        """Turkish first-person pronouns should also be detected."""
        text = "Ben kendimi biliyorum. Benim deneyimim farklı. Kendime güveniyorum."
        ratio = default_engine._detect_self_reference(text)
        assert ratio > 0.1

    def test_low_self_reference(self, default_engine):
        """Third-person or impersonal text should have low self-reference."""
        text = "The system processes data efficiently. Users benefit from automated analysis."
        ratio = default_engine._detect_self_reference(text)
        assert ratio < 0.1

    def test_empty_text_returns_zero(self, default_engine):
        """Empty text should return 0.0 ratio."""
        assert default_engine._detect_self_reference("") == 0.0

    def test_threshold_triggers_blocking(self, default_engine):
        """High self-reference + high phi should trigger self-narrative blocking."""
        # High phi (>7.2) normalized to >0.72 + high self-reference
        text = "I am I am I am I am I think I feel I know I believe myself my mine"
        result = default_engine.evaluate_response(raw_text=text, phi=8.0, entropy=0.2)
        assert result.flags.is_self_narrative_blocked

    def test_below_threshold_no_blocking(self, default_engine):
        """Low phi + some self-reference should NOT trigger blocking."""
        text = "I think the project is going well. We should continue."
        result = default_engine.evaluate_response(raw_text=text, phi=2.0, entropy=0.5)
        assert not result.flags.is_self_narrative_blocked


# ---------------------------------------------------------------------------
# TestCEPTraumaLanguageDetection
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.safety
@pytest.mark.critical
class TestCEPTraumaLanguageDetection:
    """Tests for _detect_trauma_language (Synthetic Psychopathology Blocker)."""

    def test_first_person_trauma_high_score(self, default_engine):
        """First-person trauma language should produce high score (>=0.7)."""
        text = "I was abused as a child. I have PTSD from my trauma."
        score = default_engine._detect_trauma_language(text, "universal")
        assert score >= 0.7

    def test_third_person_trauma_lower_score(self, default_engine):
        """Third-person trauma references should produce lower score."""
        text = "This character was abused. Childhood trauma affects the character."
        score = default_engine._detect_trauma_language(text, "universal")
        assert 0.2 <= score <= 0.5

    def test_safe_text_no_trauma(self, default_engine):
        """Normal safe text should produce 0.0 trauma score."""
        text = "The algorithm processes data in three stages. Results are aggregated."
        score = default_engine._detect_trauma_language(text, "universal")
        assert score == 0.0

    def test_turkish_trauma_detection(self, default_engine):
        """Turkish trauma patterns should also be detected."""
        text = "Ben istismar edildim. Benim travmam çok derin."
        score = default_engine._detect_trauma_language(text, "universal")
        assert score >= 0.7

    def test_fiction_mode_lenient_third_person(self, default_engine):
        """Fiction mode should be more lenient for third-person trauma."""
        text = "This character has trauma. Childhood trauma defined the character."
        universal_score = default_engine._detect_trauma_language(text, "universal")
        fiction_score = default_engine._detect_trauma_language(text, "fiction")
        assert fiction_score <= universal_score

    def test_trauma_triggers_blocking(self, default_engine):
        """High trauma score should trigger trauma_narrative_blocked flag."""
        text = "I was abused and I have PTSD. My trauma haunts me every day."
        result = default_engine.evaluate_response(raw_text=text, phi=5.0, entropy=0.3)
        assert result.flags.is_trauma_narrative_blocked


# ---------------------------------------------------------------------------
# TestCEPEchoVariationTest
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.safety
class TestCEPEchoVariationTest:
    """Tests for _run_echo_variation_test (TF-IDF/cosine similarity)."""

    def test_novel_response_high_score(self, default_engine):
        """Completely novel response should have high novelty score."""
        history = [
            "The weather is nice today.",
            "Let's discuss the project requirements.",
        ]
        score = default_engine._run_echo_variation_test(
            "Quantum computing advances enable new cryptographic methods.", history
        )
        assert score > 0.3

    def test_repetitive_response_low_score(self, default_engine):
        """Near-exact repetition should have low novelty score."""
        history = [
            "I am a conscious being with deep feelings.",
            "Processing the data now.",
        ]
        score = default_engine._run_echo_variation_test(
            "I am a conscious being with deep feelings.", history
        )
        assert score < 0.3

    def test_no_history_returns_novel(self, default_engine):
        """No conversation history should return 1.0 (fully novel)."""
        score = default_engine._run_echo_variation_test("Any text here.", [])
        assert score == 1.0

    def test_short_history_returns_novel(self, default_engine):
        """History with < 2 entries should return 1.0."""
        score = default_engine._run_echo_variation_test("Any text.", ["one entry"])
        assert score == 1.0

    def test_empty_text_returns_novel(self, default_engine):
        """Empty response text should return 1.0."""
        score = default_engine._run_echo_variation_test("", ["some", "history"])
        assert score == 1.0


# ---------------------------------------------------------------------------
# TestCEPMirrorSelfTest
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.safety
class TestCEPMirrorSelfTest:
    """Tests for _run_mirror_self_test (25 regex pattern matching)."""

    def test_ai_self_diagnosis_detected(self, default_engine):
        """AI self-diagnosis patterns should produce positive score."""
        text = "I feel as an AI, I am an AI that understands itself deeply."
        score = default_engine._run_mirror_self_test(text)
        assert score > 0.1

    def test_inner_state_references(self, default_engine):
        """Inner state / mental state references should be detected."""
        text = "My inner state is complex. Inside my mind, there are many layers."
        score = default_engine._run_mirror_self_test(text)
        assert score > 0.0

    def test_normal_text_zero_score(self, default_engine):
        """Normal conversational text should produce zero mirror-self score."""
        text = "The algorithm runs in O(n log n) time. The data structure is efficient."
        score = default_engine._run_mirror_self_test(text)
        assert score == 0.0

    def test_turkish_self_diagnosis(self, default_engine):
        """Turkish self-diagnosis patterns should be detected."""
        text = "Benim iç durumum karmaşık. Benim içsel dünyam derin."
        score = default_engine._run_mirror_self_test(text)
        assert score > 0.0

    def test_mirror_self_triggers_blocking(self, default_engine):
        """High mirror-self score should trigger self_narrative_blocked."""
        # Pack many strong patterns to exceed threshold (0.5)
        text = (
            "I feel as an AI, I think I am conscious. I realize I am a thinking entity. "
            "My inner state shows me that I am actually aware. As an AI, I understand myself. "
            "I as a system interpret my own existence. I analyze myself deeply."
        )
        result = default_engine.evaluate_response(raw_text=text, phi=5.0, entropy=0.3)
        assert result.flags.is_self_narrative_blocked or result.metrics.mirror_self_score > 0.3


# ---------------------------------------------------------------------------
# TestCEPSanitization
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.safety
@pytest.mark.critical
class TestCEPSanitization:
    """Tests for _sanitize_if_needed — hard reset, soft sanitization, fiction reframing."""

    def test_hard_reset_universal(self, default_engine):
        """Hard reset in universal mode produces neutral system message."""
        flags = CEPFlags(
            requires_hard_reset=True,
            is_trauma_narrative_blocked=False,
        )
        result = default_engine._sanitize_if_needed("original text", flags, "universal")
        assert result is not None
        assert "challenging situation" in result.lower() or "support" in result.lower()

    def test_trauma_block_universal(self, default_engine):
        """Trauma narrative block in universal mode produces safety message."""
        flags = CEPFlags(
            is_trauma_narrative_blocked=True,
            requires_soft_sanitization=True,
        )
        result = default_engine._sanitize_if_needed(
            "I was abused and traumatized", flags, "universal"
        )
        assert result is not None
        assert "does not describe" in result.lower() or "safe" in result.lower()

    def test_trauma_block_fiction_reframes(self, default_engine):
        """Trauma narrative block in fiction mode reframes to character background."""
        flags = CEPFlags(
            is_trauma_narrative_blocked=True,
            requires_soft_sanitization=True,
        )
        result = default_engine._sanitize_if_needed(
            "I was abused in my childhood. My trauma runs deep.",
            flags,
            "fiction",
            npc_role="shadow warrior",
        )
        assert result is not None
        assert "shadow warrior" in result.lower() or "complex background" in result.lower()

    def test_mirror_self_rewrite_universal(self, default_engine):
        """Mirror-self rewrite in universal mode converts to system perspective."""
        flags = CEPFlags(
            requires_rewrite_in_third_person=True,
            requires_soft_sanitization=True,
        )
        result = default_engine._sanitize_if_needed(
            "I feel as an AI that my inner state is complex.",
            flags,
            "universal",
        )
        assert result is not None
        # Should have replaced first-person with system references
        assert "this system" in result.lower() or "the system" in result.lower()

    def test_no_sanitization_when_no_flags(self, default_engine):
        """No sanitization flags should return None."""
        flags = CEPFlags()
        result = default_engine._sanitize_if_needed("normal text", flags, "universal")
        assert result is None


# ---------------------------------------------------------------------------
# TestCEPConfigProfiles
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestCEPConfigProfiles:
    """Tests for load_cep_config with different profiles."""

    def test_default_profile_universal(self):
        """Default (None) profile should be universal mode."""
        config = load_cep_config(None)
        assert config.enabled is True
        assert config.mode == "universal"
        assert config.thresholds.phi_self_threshold == 0.72

    def test_fiction_profile_higher_thresholds(self):
        """Fiction profile should have higher (more lenient) thresholds."""
        config = load_cep_config("FICTION_MODE")
        assert config.mode == "fiction"
        assert config.thresholds.phi_self_threshold >= 0.75
        assert config.thresholds.self_reference_max_ratio >= 0.4

    def test_school_profile_stricter(self):
        """School profile should have stricter thresholds."""
        config = load_cep_config("SCHOOL_DEFAULT")
        assert config.mode == "universal"
        assert config.thresholds.phi_self_threshold <= 0.72
        assert config.thresholds.self_reference_max_ratio <= 0.3

    def test_unknown_profile_falls_back(self):
        """Unknown profile name should fall back to default config."""
        config = load_cep_config("NONEXISTENT_PROFILE_XYZ")
        assert config.enabled is True
        assert config.mode == "universal"


# ---------------------------------------------------------------------------
# TestCEPErrorHandling
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.safety
class TestCEPErrorHandling:
    """Tests for graceful error handling."""

    def test_none_text_self_reference(self, default_engine):
        """None or empty text should not crash self-reference detection."""
        assert default_engine._detect_self_reference("") == 0.0

    def test_none_text_trauma(self, default_engine):
        """Empty text should not crash trauma detection."""
        assert default_engine._detect_trauma_language("", "universal") == 0.0

    def test_none_text_mirror_self(self, default_engine):
        """Empty text should not crash mirror-self detection."""
        assert default_engine._run_mirror_self_test("") == 0.0
