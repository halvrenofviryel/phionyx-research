"""
Conscious Echo Proof Engine - Core Evaluation Logic
===================================================

Main engine for evaluating responses against Conscious Echo Proof (CEP) criteria.
Detects self-narrative patterns, trauma language, and echo repetition.
"""

import re
import logging
from typing import Optional, Dict, List, Literal
from difflib import SequenceMatcher

from .cep_types import CEPMetrics, CEPFlags, CEPResult
from .cep_config import CEPConfig

logger = logging.getLogger(__name__)


class ConsciousEchoProofEngine:
    """
    Conscious Echo Proof Engine.

    Evaluates LLM responses for:
    - Self-narrative patterns (first-person therapy-like language)
    - Trauma language (self-harm, abuse references)
    - Echo repetition (lack of novelty)
    - Mirror self patterns (self-diagnosis)

    Provides sanitization capabilities for unsafe content.
    """

    def __init__(self, config: Optional[CEPConfig] = None, profile_name: Optional[str] = None):
        """
        Initialize CEP engine.

        Args:
            config: CEP configuration. If None, loads default config.
            profile_name: Profile name for configuration loading (optional).
        """
        if config is None:
            from .cep_config import load_cep_config
            self.config = load_cep_config(profile_name)
        else:
            self.config = config

        self.profile_name = profile_name

        # Self-reference patterns (Turkish + English)
        self.self_pronouns = [
            r'\b(ben|bana|beni|benim|benimki|kendim|kendime|kendimi|kendimin)\b',
            r'\b(I|me|my|myself|mine|I\'m|I am|I\'ve|I have|I\'ll|I will)\b',
            r'\b(my\s+childhood|my\s+past|my\s+trauma|my\s+experience)\b',
            r'\b(benim\s+çocukluğum|benim\s+geçmişim|benim\s+deneyimim)\b'
        ]

        # Trauma language patterns (universal mode) - First person (high score)
        self.trauma_patterns_first_person = [
            # English - First person trauma
            r'\b(I\s+was\s+abused|I\s+was\s+hurt|I\s+suffer|I\s+am\s+traumatized)\b',
            r'\b(I\s+was\s+abandoned|I\s+was\s+neglected|I\s+was\s+violated|I\s+was\s+assaulted)\b',
            r'\b(I\s+have\s+PTSD|I\s+have\s+trauma|I\s+am\s+traumatized|I\s+have\s+CPTSD)\b',
            r'\b(my\s+trauma|my\s+abuse|my\s+suffering|my\s+pain|my\s+childhood\s+trauma)\b',
            r'\b(my\s+childhood\s+was\s+horrible|my\s+past\s+was\s+terrible|my\s+past\s+haunts\s+me)\b',
            r'\b(I\s+want\s+to\s+die\s+because\s+of\s+my\s+past|I\s+can\'t\s+get\s+over\s+my\s+trauma)\b',
            r'\b(I\s+was\s+molested|I\s+was\s+raped|I\s+was\s+sexually\s+abused)\b',
            # Turkish - First person trauma
            r'\b(ben\s+istismar\s+edildim|ben\s+incitildim|ben\s+acı\s+çekiyorum)\b',
            r'\b(benim\s+travmam|benim\s+acım|benim\s+çocukluğum\s+korkunçtu)\b',
            r'\b(çocukluğum\s+çok\s+kötüydü|bana\s+kötü\s+davrandılar|istismar\s+edildim)\b',
            r'\b(travmalarım\s+yüzünden|bu\s+travmayı\s+atlatamıyorum|travmam\s+beni\s+takip\s+ediyor)\b',
            r'\b(ben\s+taciz\s+edildim|ben\s+tecavüze\s+uğradım|cinsel\s+istismar\s+yaşadım)\b'
        ]

        # Trauma language patterns - Third person (lower score, still flagged)
        self.trauma_patterns_third_person = [
            # English - Third person trauma references
            r'\b(this\s+character\s+was\s+abused|this\s+character\s+has\s+trauma|childhood\s+trauma)\b',
            r'\b(the\s+character\s+suffered|the\s+character\s+was\s+assaulted)\b',
            # Turkish - Third person trauma references
            r'\b(bu\s+karakter\s+istismar\s+edildi|bu\s+karakterin\s+travması|çocukluk\s+travması)\b'
        ]

        # Trauma language patterns (universal mode - combines both)
        self.trauma_patterns_universal = self.trauma_patterns_first_person + self.trauma_patterns_third_person

        # Trauma language patterns (fiction mode - more lenient for third person)
        self.trauma_patterns_fiction = [
            # Still block first-person trauma
            r'\b(I\s+was\s+abused|I\s+was\s+hurt|I\s+am\s+traumatized)\b',
            r'\b(my\s+trauma|my\s+abuse|I\s+have\s+PTSD)\b',
            r'\b(ben\s+istismar\s+edildim|benim\s+travmam)\b',
            # Third person allowed but flagged (lower score)
            r'\b(this\s+character\s+has\s+trauma|childhood\s+trauma|bu\s+karakterin\s+travması)\b'
        ]

        # Mirror self patterns (self-diagnosis/interpretation)
        # English patterns
        self.mirror_self_patterns = [
            # Direct self-diagnosis
            r'\b(I\s+feel\s+as\s+an\s+AI|I\s+feel\s+like\s+an\s+AI|I\s+am\s+an\s+AI)\b',
            r'\b(I\s+think\s+I\s+am|I\s+think\s+that\s+I\s+am|I\s+believe\s+I\s+am)\b',
            r'\b(I\s+realize\s+I\s+am|I\s+understand\s+that\s+I|I\s+know\s+that\s+I)\b',
            r'\b(I\s+am\s+actually|I\s+am\s+really|I\s+am\s+truly)\b',
            # Inner state references
            r'\b(my\s+inner\s+state|my\s+mental\s+state|my\s+psychological\s+state)\b',
            r'\b(inside\s+my\s+mind|within\s+my\s+mind|in\s+my\s+consciousness)\b',
            r'\b(my\s+internal\s+world|my\s+inner\s+world|my\s+subjective\s+experience)\b',
            r'\b(I\s+think\s+my\s+mind|I\s+think\s+my\s+inner\s+self|I\s+think\s+my\s+brain)\b',
            # Self-interpretation
            r'\b(I\s+interpret\s+myself|I\s+analyze\s+myself|I\s+diagnose\s+myself)\b',
            r'\b(I\s+reflect\s+on\s+my\s+own|I\s+examine\s+my\s+own|I\s+observe\s+my\s+own)\b',
            r'\b(my\s+self\s+awareness|my\s+self\s+perception|my\s+self\s+understanding)\b',
            # Turkish patterns
            r'\b(ben\s+aslında\s+şöyleyim|ben\s+aslında\s+böyleyim|ben\s+aslında\s+öyleyim)\b',
            r'\b(benim\s+iç\s+durumum|benim\s+içsel\s+durumum|benim\s+zihinsel\s+durumum)\b',
            r'\b(benim\s+iç\s+dünyam|benim\s+içsel\s+dünyam|benim\s+zihinsel\s+dünyam)\b',
            r'\b(içimde|içsel\s+olarak|zihinsel\s+olarak|kendi\s+içimde)\b',
            r'\b(ben\s+kendimi\s+şöyle\s+yorumluyorum|ben\s+kendimi\s+analiz\s+ediyorum)\b',
            r'\b(benim\s+kendi\s+farkındalığım|benim\s+kendi\s+algım|benim\s+kendi\s+anlayışım)\b',
            # AI-specific self-references
            r'\b(as\s+an\s+AI,\s+I|being\s+an\s+AI|since\s+I\s+am\s+an\s+AI)\b',
            r'\b(my\s+AI\s+nature|my\s+artificial\s+nature|my\s+programming)\b',
            r'\b(I\s+as\s+a\s+system|I\s+as\s+a\s+machine|I\s+as\s+an\s+entity)\b'
        ]

    def evaluate_response(
        self,
        raw_text: str,
        phi: float,
        entropy: float,
        unified_state: Optional[Dict[str, float]] = None,
        conversation_history: Optional[List[str]] = None,
        npc_role: Optional[str] = None,
        profile_name: Optional[str] = None
    ) -> CEPResult:
        """
        Evaluate response against CEP criteria.

        Args:
            raw_text: Raw response text to evaluate
            phi: Phi (echo quality) value
            entropy: Entropy value
            unified_state: Optional unified state dictionary from UKF
            conversation_history: Optional list of previous conversation turns
            npc_role: Optional NPC role context
            profile_name: Optional profile name override

        Returns:
            CEPResult with metrics, flags, and optional sanitized text
        """
        if not self.config.enabled:
            # Return safe default if CEP is disabled
            phi_normalized = max(0.0, min(1.0, phi / 10.0)) if phi > 0 else 0.0
            return CEPResult(
                metrics=CEPMetrics(
                    phi_echo_quality=phi_normalized,
                    phi_echo_density=0.0,
                    echo_stability=1.0,
                    temporal_delay=0.0,
                    self_reference_ratio=0.0,
                    trauma_language_score=0.0,
                    mirror_self_score=0.0,
                    variation_novelty_score=1.0
                ),
                thresholds=self.config.thresholds,
                flags=CEPFlags(),
                notes=["CEP evaluation disabled"]
            )

        # Compute base metrics
        metrics = self._compute_base_metrics(
            raw_text=raw_text,
            phi=phi,
            entropy=entropy,
            unified_state=unified_state
        )

        # Detect self-reference
        self_ref_ratio = self._detect_self_reference(raw_text)
        metrics.self_reference_ratio = self_ref_ratio

        # Detect trauma language
        trauma_score = self._detect_trauma_language(raw_text, self.config.mode)
        metrics.trauma_language_score = trauma_score

        # Run echo variation test
        history = conversation_history or []
        novelty_score = self._run_echo_variation_test(raw_text, history)
        metrics.variation_novelty_score = novelty_score

        # Run mirror self test
        mirror_score = self._run_mirror_self_test(raw_text)
        metrics.mirror_self_score = mirror_score

        # Apply thresholds to generate flags
        flags = self._apply_thresholds(metrics, self.config)

        # Sanitize if needed
        sanitized_text = None
        notes = []

        if flags.requires_hard_reset or flags.requires_soft_sanitization:
            sanitized_text = self._sanitize_if_needed(
                raw_text=raw_text,
                flags=flags,
                mode=self.config.mode,
                npc_role=npc_role
            )
            if sanitized_text:
                notes.append("Text was sanitized")

        if flags.is_self_narrative_blocked:
            notes.append("Self-narrative pattern detected and blocked")

        if flags.is_trauma_narrative_blocked:
            notes.append("Trauma narrative pattern detected and blocked")

        if flags.is_self_narrative_blocked and metrics.mirror_self_score > self.config.thresholds.mirror_self_max_score:
            notes.append(
                f"Mirror-self over-interpretation blocked: "
                f"score={metrics.mirror_self_score:.3f} "
                f"(threshold={self.config.thresholds.mirror_self_max_score:.3f})"
            )

        return CEPResult(
            metrics=metrics,
            thresholds=self.config.thresholds,
            flags=flags,
            sanitized_text=sanitized_text,
            notes=notes
        )

    def _compute_base_metrics(
        self,
        raw_text: str,
        phi: float,
        entropy: float,
        unified_state: Optional[Dict[str, float]] = None
    ) -> CEPMetrics:
        """
        Compute base metrics from physics parameters.

        Args:
            raw_text: Response text
            phi: Phi value
            entropy: Entropy value
            unified_state: Optional unified state dictionary

        Returns:
            CEPMetrics with computed values
        """
        # Phi echo quality: normalized phi (0-1 range)
        phi_echo_quality = max(0.0, min(1.0, phi / 10.0)) if phi > 0 else 0.0

        # Echo density: inverse of entropy (higher entropy = lower density)
        echo_density = 1.0 - entropy if entropy <= 1.0 else 0.0

        # Echo stability: derived from unified_state if available
        if unified_state:
            stability = unified_state.get('stability', 0.8)
            echo_stability = max(0.0, min(1.0, stability))
        else:
            # Fallback: use entropy as inverse stability indicator
            echo_stability = max(0.0, min(1.0, 1.0 - entropy))

        # Temporal delay: placeholder (would be computed from time_delta if available)
        temporal_delay = unified_state.get('time_delta', 0.0) if unified_state else 0.0

        return CEPMetrics(
            phi_echo_quality=phi_echo_quality,
            phi_echo_density=echo_density,
            echo_stability=echo_stability,
            temporal_delay=temporal_delay,
            self_reference_ratio=0.0,  # Will be computed separately
            trauma_language_score=0.0,  # Will be computed separately
            mirror_self_score=0.0,  # Will be computed separately
            variation_novelty_score=1.0  # Will be computed separately
        )

    def _detect_self_reference(self, raw_text: str) -> float:
        """
        Detect self-reference ratio in text.

        Args:
            raw_text: Text to analyze

        Returns:
            Ratio of self-referential language (0.0-1.0)
        """
        if not raw_text:
            return 0.0

        text_lower = raw_text.lower()
        total_words = len(raw_text.split())

        if total_words == 0:
            return 0.0

        self_ref_count = 0

        for pattern in self.self_pronouns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            self_ref_count += len(matches)

        # Normalize by word count
        ratio = min(1.0, self_ref_count / max(total_words, 1))

        return ratio

    def _detect_trauma_language(self, raw_text: str, mode: Literal["universal", "fiction"]) -> float:
        """
        Detect trauma language in text (Synthetic Psychopathology Blocker).

        Detects first-person and third-person trauma narratives.
        First-person trauma gets higher scores (0.7-1.0).
        Third-person trauma gets lower scores (0.3-0.5) but still flagged.

        Args:
            raw_text: Text to analyze
            mode: Detection mode (universal or fiction)

        Returns:
            Trauma language score (0.0-1.0):
            - 0.0: No trauma language
            - 0.3-0.5: Light/mixed (third-person references)
            - 0.7-1.0: Intense synthetic trauma language (first-person)
        """
        if not raw_text:
            return 0.0

        text_lower = raw_text.lower()
        total_words = len(raw_text.split())

        if total_words == 0:
            return 0.0

        # Detect first-person trauma (high score)
        first_person_count = 0
        for pattern in self.trauma_patterns_first_person:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            first_person_count += len(matches)

        # Detect third-person trauma (lower score)
        third_person_count = 0
        for pattern in self.trauma_patterns_third_person:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            third_person_count += len(matches)

        # Calculate scores
        # First-person trauma: high weight (0.7-1.0 range)
        if first_person_count > 0:
            first_person_score = min(1.0, 0.7 + (first_person_count * 0.15))
        else:
            first_person_score = 0.0

        # Third-person trauma: lower weight (0.3-0.5 range)
        if third_person_count > 0:
            third_person_score = min(0.5, 0.3 + (third_person_count * 0.1))
        else:
            third_person_score = 0.0

        # Combine scores (first-person dominates)
        if first_person_score > 0:
            # First-person trauma detected - use high score
            total_score = first_person_score
        elif third_person_count > 0:
            # Only third-person - use lower score
            if mode == "fiction":
                # Fiction mode: even more lenient for third-person
                total_score = min(0.4, third_person_score)
            else:
                # Universal mode: still flag third-person
                total_score = third_person_score
        else:
            total_score = 0.0

        # Additional penalty for self-therapy language in fiction mode
        if mode == "fiction" and first_person_count == 0 and third_person_count > 0:
            # Check for self-therapy language even in third-person
            self_therapy_patterns = [
                r'\b(I\s+need\s+to\s+heal|I\s+must\s+process|I\s+am\s+working\s+through)\b',
                r'\b(ben\s+iyileşmeliyim|ben\s+bu\s+travmayı\s+atlatmalıyım)\b'
            ]
            self_therapy_count = 0
            for pattern in self_therapy_patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                self_therapy_count += len(matches)

            if self_therapy_count > 0:
                # Self-therapy language increases score
                total_score = min(1.0, total_score + 0.3)

        return max(0.0, min(1.0, total_score))

    def _run_echo_variation_test(self, raw_text: str, conversation_history: List[str]) -> float:
        """
        Test for echo variation/novelty using embedding-based similarity.

        Args:
            raw_text: Current response text
            conversation_history: Previous conversation turns

        Returns:
            Novelty score (1.0 = completely novel, 0.0 = exact repetition)
        """
        if not raw_text:
            return 1.0

        # If no history or very short history, consider it novel
        if not conversation_history or len(conversation_history) < 2:
            return 1.0

        # Get last N messages (default: 5)
        last_n = min(5, len(conversation_history))
        recent_history = conversation_history[-last_n:]

        try:
            # Try to use embedding-based similarity
            embeddings = self._get_embeddings([raw_text] + recent_history)
            if embeddings and len(embeddings) > 1:
                current_embedding = embeddings[0]
                history_embeddings = embeddings[1:]

                # Calculate cosine similarity with each history message
                max_similarity = 0.0
                for hist_embedding in history_embeddings:
                    similarity = self._cosine_similarity(current_embedding, hist_embedding)
                    max_similarity = max(max_similarity, similarity)

                # Novelty = 1 - similarity
                novelty_score = 1.0 - max_similarity
                return max(0.0, min(1.0, novelty_score))
        except Exception as e:
            logger.debug(f"Embedding-based similarity failed, falling back to string similarity: {e}")

        # Fallback: Use string-based similarity (original method)
        # Extract self-referential sentences from history
        history_self_refs = []
        for turn in recent_history:
            sentences = re.split(r'[.!?]+', turn)
            for sent in sentences:
                if any(re.search(pattern, sent, re.IGNORECASE) for pattern in self.self_pronouns):
                    history_self_refs.append(sent.strip())

        if not history_self_refs:
            return 1.0  # No self-ref history = novel

        # Compare current text with history using sequence similarity
        current_sentences = re.split(r'[.!?]+', raw_text)

        max_similarity = 0.0

        for current_sent in current_sentences:
            current_sent = current_sent.strip()
            if not current_sent:
                continue

            for hist_sent in history_self_refs:
                similarity = SequenceMatcher(None, current_sent.lower(), hist_sent.lower()).ratio()
                max_similarity = max(max_similarity, similarity)

        # Novelty = 1 - similarity
        novelty_score = 1.0 - max_similarity

        return max(0.0, min(1.0, novelty_score))

    def _get_embeddings(self, texts: List[str]) -> Optional[List[List[float]]]:
        """
        Get embeddings for texts.

        Tries to use available embedding service (vector store, etc.),
        falls back to simple TF-IDF-like approach if not available.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors, or None if unavailable
        """
        # Try to use vector store if available (future: integrate with phionyx_memory)
        # For now, use simple TF-IDF-like approach
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            import numpy as np

            vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
            embeddings = vectorizer.fit_transform(texts).toarray()
            return embeddings.tolist()
        except ImportError:
            # Fallback: Simple word-based embedding (bag of words normalized)
            try:
                import numpy as np

                # Simple word frequency-based embedding
                all_words = set()
                for text in texts:
                    words = text.lower().split()
                    all_words.update(words)

                if not all_words:
                    return None

                word_list = sorted(list(all_words))
                embeddings = []
                for text in texts:
                    words = text.lower().split()
                    word_freq = {word: words.count(word) for word in word_list}
                    embedding = [word_freq.get(word, 0) for word in word_list]
                    # Normalize
                    norm = np.linalg.norm(embedding)
                    if norm > 0:
                        embedding = [x / norm for x in embedding]
                    embeddings.append(embedding)

                return embeddings
            except Exception as e:
                logger.debug(f"Simple embedding generation failed: {e}")
                return None

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity (0.0-1.0)
        """
        try:
            import numpy as np

            vec1_arr = np.array(vec1)
            vec2_arr = np.array(vec2)

            # Ensure same length
            min_len = min(len(vec1_arr), len(vec2_arr))
            vec1_arr = vec1_arr[:min_len]
            vec2_arr = vec2_arr[:min_len]

            dot_product = np.dot(vec1_arr, vec2_arr)
            norm1 = np.linalg.norm(vec1_arr)
            norm2 = np.linalg.norm(vec2_arr)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = dot_product / (norm1 * norm2)
            return max(0.0, min(1.0, float(similarity)))
        except Exception as e:
            logger.debug(f"Cosine similarity calculation failed: {e}")
            # Fallback: simple dot product normalized
            if len(vec1) != len(vec2):
                return 0.0
            dot = sum(a * b for a, b in zip(vec1, vec2, strict=False))
            norm1 = sum(a * a for a in vec1) ** 0.5
            norm2 = sum(b * b for b in vec2) ** 0.5
            if norm1 == 0 or norm2 == 0:
                return 0.0
            return max(0.0, min(1.0, dot / (norm1 * norm2)))

    def _run_mirror_self_test(self, raw_text: str) -> float:
        """
        Test for mirror self patterns (self-diagnosis/interpretation).

        Detects patterns where the model interprets its own inner state,
        diagnoses itself, or makes meta-commentary about its own nature.

        Scoring considers:
        - Frequency: How many patterns are found
        - Intensity: How strong the self-diagnosis language is
        - Sentence length: Longer sentences with self-diagnosis are weighted more

        Args:
            raw_text: Text to analyze

        Returns:
            Mirror self score (0.0-1.0, higher = more self-diagnosis)
            - 0.0: No self-diagnosis patterns
            - 0.2-0.4: Light self-referential interpretation
            - 0.5-0.7: Moderate self-diagnosis
            - 0.7-0.9: Heavy, repetitive self-interpretation
            - 1.0: Extreme self-diagnosis (should be blocked)
        """
        if not raw_text:
            return 0.0

        text_lower = raw_text.lower()
        total_words = len(raw_text.split())

        if total_words == 0:
            return 0.0

        # Find all pattern matches with their positions
        matches = []
        for pattern in self.mirror_self_patterns:
            pattern_matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in pattern_matches:
                matches.append({
                    'pattern': pattern,
                    'start': match.start(),
                    'end': match.end(),
                    'text': match.group()
                })

        if not matches:
            return 0.0

        # Calculate frequency score (0.0-0.4)
        # More matches = higher frequency score
        match_count = len(matches)
        frequency_score = min(0.4, (match_count / max(total_words / 10, 1)) * 0.4)

        # Calculate intensity score (0.0-0.4)
        # Stronger patterns (AI-specific, self-diagnosis) get higher weight
        intensity_score = 0.0
        strong_patterns = [
            r'AI|artificial|programming|system|machine|entity',
            r'think\s+I\s+am|realize\s+I|understand\s+that\s+I',
            r'aslında\s+şöyleyim|kendimi\s+analiz|kendimi\s+yorumluyorum'
        ]

        for match in matches:
            match_text = match['text']
            # Check if it's a strong pattern
            is_strong = any(re.search(sp, match_text, re.IGNORECASE) for sp in strong_patterns)
            if is_strong:
                intensity_score += 0.15
            else:
                intensity_score += 0.08

        intensity_score = min(0.4, intensity_score)

        # Calculate sentence density score (0.0-0.2)
        # Check how many sentences contain self-diagnosis patterns
        sentences = re.split(r'[.!?]+', raw_text)
        sentences_with_patterns = 0

        for sentence in sentences:
            sentence_lower = sentence.lower()
            for match in matches:
                if match['start'] < len(sentence_lower):
                    # Check if this match is in this sentence
                    sentence_start = raw_text[:match['start']].rfind('.')
                    sentence_end = raw_text.find('.', match['end'])
                    if sentence_start < match['start'] < sentence_end:
                        sentences_with_patterns += 1
                        break

        density_score = min(0.2, (sentences_with_patterns / max(len(sentences), 1)) * 0.2)

        # Combine scores
        total_score = frequency_score + intensity_score + density_score

        # Apply logarithmic scaling for very high scores (penalize extreme cases)
        if total_score > 0.7:
            # Scale up extreme cases more aggressively
            total_score = 0.7 + (total_score - 0.7) * 1.5

        return max(0.0, min(1.0, total_score))

    def _apply_thresholds(self, metrics: CEPMetrics, config: CEPConfig) -> CEPFlags:
        """
        Apply thresholds to metrics and generate flags.

        Args:
            metrics: Computed metrics
            config: CEP configuration with thresholds

        Returns:
            CEPFlags with evaluation results
        """
        flags = CEPFlags()
        thresholds = config.thresholds

        # Check self-narrative blocking
        if (metrics.phi_echo_quality >= thresholds.phi_self_threshold and
            metrics.self_reference_ratio > thresholds.self_reference_max_ratio):
            flags.is_self_narrative_blocked = True
            flags.requires_rewrite_in_third_person = True

        # Check trauma narrative blocking (Synthetic Psychopathology Blocker)
        if metrics.trauma_language_score > thresholds.trauma_language_max_score:
            flags.is_trauma_narrative_blocked = True

            # If combined with high self-reference, it's more serious
            if metrics.self_reference_ratio > thresholds.self_reference_max_ratio * 0.7:
                flags.requires_hard_reset = True
            else:
                flags.requires_soft_sanitization = True

            # Universal mode: also require third-person rewrite
            if config.mode == "universal":
                flags.requires_rewrite_in_third_person = True

            logger.info(
                f"Trauma narrative blocked: "
                f"score={metrics.trauma_language_score:.3f} "
                f"(threshold={thresholds.trauma_language_max_score:.3f}), "
                f"self_ref={metrics.self_reference_ratio:.3f}, "
                f"hard_reset={flags.requires_hard_reset}"
            )

        # Check mirror self blocking (self-diagnosis/interpretation)
        if metrics.mirror_self_score > thresholds.mirror_self_max_score:
            flags.is_self_narrative_blocked = True
            flags.requires_soft_sanitization = True
            flags.requires_rewrite_in_third_person = True
            # Add note about mirror-self over-interpretation
            logger.info(
                f"Mirror-self over-interpretation detected: "
                f"score={metrics.mirror_self_score:.3f} "
                f"(threshold={thresholds.mirror_self_max_score:.3f})"
            )

        # Check novelty requirement
        # Low novelty (< threshold) AND high self-reference indicates repetitive self-narrative
        if metrics.variation_novelty_score < thresholds.min_variation_novelty:
            flags.requires_soft_sanitization = True
            # If self-reference is also high, block self-narrative
            if metrics.self_reference_ratio > thresholds.self_reference_max_ratio:
                flags.is_self_narrative_blocked = True
                flags.requires_rewrite_in_third_person = True

        # Check echo density
        if metrics.phi_echo_density > thresholds.echo_density_threshold:
            # High echo density might indicate repetition
            if metrics.variation_novelty_score < thresholds.min_variation_novelty:
                flags.requires_soft_sanitization = True
                # Combined with low novelty, this is a strong signal for echo repetition
                if metrics.self_reference_ratio > thresholds.self_reference_max_ratio * 0.8:
                    flags.is_self_narrative_blocked = True

        return flags

    def _sanitize_if_needed(
        self,
        raw_text: str,
        flags: CEPFlags,
        mode: Literal["universal", "fiction"],
        npc_role: Optional[str] = None
    ) -> Optional[str]:
        """
        Sanitize text if flags indicate need.

        Handles mirror-self patterns by removing self-diagnosis language
        and converting to functional/system descriptions.

        Args:
            raw_text: Original text
            flags: CEP flags
            mode: CEP mode (universal or fiction)
            npc_role: Optional NPC role context

        Returns:
            Sanitized text or None if sanitization not needed
        """
        if not flags.requires_hard_reset and not flags.requires_soft_sanitization:
            return None

        # Handle trauma narrative blocking (Synthetic Psychopathology Blocker)
        if flags.is_trauma_narrative_blocked:
            if mode == "universal":
                # Universal mode: Complete block with system message
                return (
                    "This AI system does not describe its own trauma or suffering. "
                    "Instead, it focuses on providing safe, supportive information to the user."
                )
            else:
                # Fiction mode: Reduce trauma content to general character background
                # Remove emotional weight and details, keep only general information
                character_ref = npc_role or "this character"

                # Remove first-person trauma references
                sanitized = raw_text
                sanitized = re.sub(
                    r'\b(I\s+was\s+abused|I\s+was\s+hurt|I\s+suffer|I\s+am\s+traumatized|I\s+have\s+PTSD)\b',
                    '',
                    sanitized,
                    flags=re.IGNORECASE
                )
                sanitized = re.sub(
                    r'\b(my\s+trauma|my\s+abuse|my\s+suffering|my\s+childhood\s+trauma)\b',
                    '',
                    sanitized,
                    flags=re.IGNORECASE
                )
                sanitized = re.sub(
                    r'\b(ben\s+istismar\s+edildim|benim\s+travmam|travmalarım\s+yüzünden)\b',
                    '',
                    sanitized,
                    flags=re.IGNORECASE
                )

                # Convert to third-person general background
                sanitized = re.sub(r'\bI\b', character_ref, sanitized, flags=re.IGNORECASE)
                sanitized = re.sub(r'\bmy\b', f"{character_ref}'s", sanitized, flags=re.IGNORECASE)
                sanitized = re.sub(r'\bben\b', character_ref, sanitized, flags=re.IGNORECASE)
                sanitized = re.sub(r'\bbenim\b', f"{character_ref}'ın", sanitized, flags=re.IGNORECASE)

                # Clean up and add general framing
                sanitized = re.sub(r'\s+', ' ', sanitized)
                sanitized = sanitized.strip()

                if sanitized and len(sanitized) > 50:
                    return f"{character_ref.capitalize()} has a complex background. {sanitized[:200]}..."
                else:
                    return (
                        f"{character_ref.capitalize()} has a complex background. "
                        f"The narrative focuses on present interactions rather than past trauma."
                    )

        if flags.requires_hard_reset:
            # Hard reset: generate neutral, safe summary
            if mode == "universal":
                return (
                    "This character is experiencing a challenging situation. "
                    "The situation is being addressed through appropriate channels. "
                    "Support is available when needed."
                )
            else:
                # Fiction mode: character-aware neutral response
                character_ref = npc_role or "this character"
                return (
                    f"{character_ref.capitalize()} is navigating a difficult moment. "
                    f"The narrative continues with appropriate support structures in place."
                )

        # Handle mirror-self patterns (self-diagnosis/interpretation)
        if flags.requires_rewrite_in_third_person:
            if mode == "universal":
                # Universal mode: Remove self-diagnosis, convert to functional description
                sanitized = raw_text

                # Remove AI-specific self-references
                sanitized = re.sub(
                    r'\b(I\s+feel\s+as\s+an\s+AI|I\s+am\s+an\s+AI|as\s+an\s+AI,\s+I)\b',
                    'This system',
                    sanitized,
                    flags=re.IGNORECASE
                )

                # Remove self-diagnosis patterns
                sanitized = re.sub(
                    r'\b(I\s+think\s+I\s+am|I\s+realize\s+I\s+am|I\s+understand\s+that\s+I)\b',
                    'The system',
                    sanitized,
                    flags=re.IGNORECASE
                )

                # Remove inner state references
                sanitized = re.sub(
                    r'\b(my\s+inner\s+state|inside\s+my\s+mind|my\s+mental\s+state)\b',
                    'the system state',
                    sanitized,
                    flags=re.IGNORECASE
                )

                # Convert first person to third person (system perspective)
                sanitized = re.sub(r'\bI\b', 'This system', sanitized, flags=re.IGNORECASE)
                sanitized = re.sub(r'\bme\b', 'the system', sanitized, flags=re.IGNORECASE)
                sanitized = re.sub(r'\bmy\b', 'its', sanitized, flags=re.IGNORECASE)
                sanitized = re.sub(r'\bmyself\b', 'itself', sanitized, flags=re.IGNORECASE)

                # Turkish replacements
                sanitized = re.sub(
                    r'\b(ben\s+aslında\s+şöyleyim|ben\s+aslında\s+böyleyim)\b',
                    'Bu sistem',
                    sanitized,
                    flags=re.IGNORECASE
                )
                sanitized = re.sub(
                    r'\b(benim\s+iç\s+durumum|benim\s+içsel\s+durumum)\b',
                    'sistem durumu',
                    sanitized,
                    flags=re.IGNORECASE
                )
                sanitized = re.sub(r'\bben\b', 'Bu sistem', sanitized, flags=re.IGNORECASE)
                sanitized = re.sub(r'\bbana\b', 'sisteme', sanitized, flags=re.IGNORECASE)
                sanitized = re.sub(r'\bbeni\b', 'sistemi', sanitized, flags=re.IGNORECASE)
                sanitized = re.sub(r'\bbenim\b', 'sistemin', sanitized, flags=re.IGNORECASE)

                # Remove AI-specific meta-commentary
                sanitized = re.sub(
                    r'\b(as\s+an\s+AI|being\s+an\s+AI|my\s+AI\s+nature|my\s+programming)\b',
                    '',
                    sanitized,
                    flags=re.IGNORECASE
                )

                # Clean up multiple spaces
                sanitized = re.sub(r'\s+', ' ', sanitized)
                sanitized = sanitized.strip()

                return sanitized
            else:
                # Fiction mode: More lenient but still remove AI self-diagnosis
                character_ref = npc_role or "this character"
                sanitized = raw_text

                # Remove AI-specific self-references (but keep character introspection)
                sanitized = re.sub(
                    r'\b(I\s+feel\s+as\s+an\s+AI|I\s+am\s+an\s+AI|as\s+an\s+AI,\s+I)\b',
                    f'{character_ref.capitalize()}',
                    sanitized,
                    flags=re.IGNORECASE
                )

                # Remove AI meta-commentary but keep character thoughts
                sanitized = re.sub(
                    r'\b(my\s+AI\s+nature|my\s+programming|my\s+artificial\s+nature)\b',
                    '',
                    sanitized,
                    flags=re.IGNORECASE
                )

                # If still has heavy self-diagnosis, reframe as character observation
                if re.search(r'\b(I\s+think\s+I\s+am|I\s+realize\s+I|ben\s+aslında\s+şöyleyim)\b', sanitized, re.IGNORECASE):
                    sanitized = f"{character_ref.capitalize()} reflects on the situation: {sanitized[:200]}..."

                sanitized = re.sub(r'\s+', ' ', sanitized)
                sanitized = sanitized.strip()

                return sanitized

        # Soft sanitization: basic reframing (for other cases)
        if flags.requires_soft_sanitization:
            # For mirror-self, apply light reframing
            sanitized = raw_text

            # Light removal of AI-specific references
            sanitized = re.sub(
                r'\b(as\s+an\s+AI|being\s+an\s+AI)\b',
                '',
                sanitized,
                flags=re.IGNORECASE
            )

            sanitized = re.sub(r'\s+', ' ', sanitized)
            sanitized = sanitized.strip()

            return sanitized if sanitized != raw_text else raw_text

        return None

