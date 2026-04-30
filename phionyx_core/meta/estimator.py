"""
Confidence Estimator - Meta-Cognition Lite
==========================================

Estimates system confidence based on PhysicsState (Entropy) and Context (Complexity).
When confidence is low, triggers hedging strategies or clarification requests.
"""

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ConfidenceResult:
    """
    Result of confidence estimation.

    Attributes:
        confidence_score: Confidence score (0.0-1.0)
        is_uncertain: Whether system is uncertain (score < 0.6)
        recommendation: Recommended action ("hedge", "clarify", "proceed")
        reasoning: Explanation of the confidence score
        entropy_contribution: How much entropy reduced confidence
        complexity_contribution: How much complexity reduced confidence
        epistemic_uncertainty: v4 — epistemic uncertainty component (Optional)
        aleatoric_uncertainty: v4 — aleatoric uncertainty component (Optional)
        t_meta: v4 — meta-cognitive trust score (Optional)
        ood_score: v4 — out-of-distribution score (Optional)
    """

    confidence_score: float
    is_uncertain: bool
    recommendation: str  # "hedge", "clarify", "proceed"
    reasoning: str
    entropy_contribution: float
    complexity_contribution: float

    # v4 optional extensions (AD-6: backward compat via Optional)
    epistemic_uncertainty: float | None = None
    aleatoric_uncertainty: float | None = None
    t_meta: float | None = None
    ood_score: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "confidence_score": self.confidence_score,
            "is_uncertain": self.is_uncertain,
            "recommendation": self.recommendation,
            "reasoning": self.reasoning,
            "entropy_contribution": self.entropy_contribution,
            "complexity_contribution": self.complexity_contribution,
        }
        # v4 fields (only include if set)
        if self.epistemic_uncertainty is not None:
            result["epistemic_uncertainty"] = self.epistemic_uncertainty
        if self.aleatoric_uncertainty is not None:
            result["aleatoric_uncertainty"] = self.aleatoric_uncertainty
        if self.t_meta is not None:
            result["t_meta"] = self.t_meta
        if self.ood_score is not None:
            result["ood_score"] = self.ood_score
        return result


class ConfidenceEstimator:
    """
    Meta-Cognition Lite: Estimates system confidence.

    Uses PhysicsState (Entropy) and Context (Complexity) to determine
    when the system should hedge or request clarification.
    """

    def __init__(self, uncertainty_threshold: float = 0.6):
        """
        Initialize confidence estimator.

        Args:
            uncertainty_threshold: Confidence score below which system is considered uncertain
        """
        self.uncertainty_threshold = uncertainty_threshold
        logger.info(f"ConfidenceEstimator initialized (threshold: {uncertainty_threshold})")

    def estimate_confidence(
        self,
        physics_state: dict[str, Any],
        context: dict[str, Any] | None = None,
        user_input: str | None = None,
        memory_matches: list[dict[str, Any]] | None = None,
        memory_similarity: float | None = None,
        input_length: int | None = None
    ) -> ConfidenceResult:
        """
        Estimate confidence score based on entropy, memory similarity, and input clarity.

        Formula:
            Base Confidence = 1.0
            Penalty 1: If Entropy > 0.7 -> -0.3 (Confusion)
            Penalty 2: If Memory.max_similarity < 0.7 -> -0.4 (Unknown Territory)
            Penalty 3: If InputLength < 5 chars -> -0.2 (Ambiguity)

        Args:
            physics_state: Physics state with entropy, phi, etc.
            context: Optional context information
            user_input: Optional user input for analysis
            memory_matches: Optional list of memory matches with similarity scores

        Returns:
            ConfidenceResult with score and recommendations
        """
        # Base confidence
        confidence_score = 1.0

        # Extract entropy from physics state
        entropy = physics_state.get("entropy", 0.5)
        _phi = physics_state.get("phi", 1.0)

        # Penalty 1: High Entropy (Confusion)
        entropy_penalty = 0.0
        if entropy > 0.7:
            entropy_penalty = 0.3
            logger.info(f"ConfidenceEstimator: High entropy penalty applied ({entropy:.2f} > 0.7)")

        # Penalty 2: Low Memory Similarity (Unknown Territory)
        # 🚨 SEMANTIC ANOMALY DETECTOR: If similarity < 0.5, force confidence to 0.3
        memory_penalty = 0.0
        max_similarity = 1.0  # Default: assume perfect match if no memories
        semantic_anomaly_detected = False

        # Use memory_similarity parameter if provided (for backward compatibility with tests)
        if memory_similarity is not None:
            max_similarity = memory_similarity
            if max_similarity < 0.5:
                semantic_anomaly_detected = True
                confidence_score = 0.3
                logger.warning(
                    f"ConfidenceEstimator: SEMANTIC ANOMALY DETECTED! "
                    f"Memory similarity ({max_similarity:.2f}) < 0.5. "
                    f"Confidence forced to 0.3 (hard limit)."
                )
            elif max_similarity < 0.7:
                memory_penalty = 0.4
                logger.info(f"ConfidenceEstimator: Low memory similarity penalty applied ({max_similarity:.2f} < 0.7)")
        elif memory_matches:
            similarities = [m.get("similarity", 0.0) for m in memory_matches if isinstance(m, dict)]
            if similarities:
                max_similarity = max(similarities)
                # 🚨 CRITICAL: Semantic Anomaly Detection
                if max_similarity < 0.5:
                    # Force confidence to 0.3 (hard limit for unknown territory)
                    semantic_anomaly_detected = True
                    confidence_score = 0.3
                    logger.warning(
                        f"ConfidenceEstimator: SEMANTIC ANOMALY DETECTED! "
                        f"Max similarity ({max_similarity:.2f}) < 0.5. "
                        f"Confidence forced to 0.3 (hard limit)."
                    )
                elif max_similarity < 0.7:
                    memory_penalty = 0.4
                    logger.info(f"ConfidenceEstimator: Low memory similarity penalty applied ({max_similarity:.2f} < 0.7)")
        elif memory_matches is not None and len(memory_matches) == 0:
            # No memories found at all - unknown territory
            semantic_anomaly_detected = True
            memory_penalty = 0.4
            max_similarity = 0.0
            confidence_score = 0.3  # Force to 0.3 when no memories
            logger.warning(
                "ConfidenceEstimator: No memories found - SEMANTIC ANOMALY DETECTED! "
                "Confidence forced to 0.3 (hard limit)."
            )

        # Penalty 3: Short Input (Ambiguity)
        input_penalty = 0.0
        if input_length is not None:
            # Use provided input_length parameter (for backward compatibility with tests)
            actual_input_length = input_length
        else:
            actual_input_length = len(user_input.strip()) if user_input else 0
        if actual_input_length < 5:
            input_penalty = 0.2
            logger.info(f"ConfidenceEstimator: Short input penalty applied ({actual_input_length} < 5 chars)")

        # Calculate final confidence score (only if semantic anomaly not detected)
        if not semantic_anomaly_detected:
            confidence_score = confidence_score - entropy_penalty - memory_penalty - input_penalty
            # Clamp to [0.0, 1.0]
            confidence_score = max(0.0, min(1.0, confidence_score))
        # If semantic anomaly detected, confidence_score is already set to 0.3 above

        # Calculate contributions for reporting
        entropy_contribution = entropy_penalty
        complexity_contribution = memory_penalty + input_penalty

        # Determine if uncertain
        is_uncertain = confidence_score < self.uncertainty_threshold

        # Generate recommendation
        if confidence_score < 0.4:
            recommendation = "block"  # Very uncertain - block response
            reasoning = (
                f"Very low confidence ({confidence_score:.2f}). "
                f"Penalties: Entropy={entropy_penalty:.2f}, Memory={memory_penalty:.2f}, Input={input_penalty:.2f}. "
                f"System should block response to prevent hallucination."
            )
        elif confidence_score < 0.6:
            recommendation = "hedge"  # Uncertain - use hedging strategy
            reasoning = (
                f"Low confidence ({confidence_score:.2f}). "
                f"Penalties: Entropy={entropy_penalty:.2f}, Memory={memory_penalty:.2f}, Input={input_penalty:.2f}. "
                f"System should use hedging language (e.g., 'I am not certain, but...')."
            )
        else:
            recommendation = "proceed"  # Confident - proceed normally
            reasoning = (
                f"Confident ({confidence_score:.2f}). "
                f"Penalties: Entropy={entropy_penalty:.2f}, Memory={memory_penalty:.2f}, Input={input_penalty:.2f}. "
                f"System can proceed normally."
            )

        result = ConfidenceResult(
            confidence_score=confidence_score,
            is_uncertain=is_uncertain,
            recommendation=recommendation,
            reasoning=reasoning,
            entropy_contribution=entropy_contribution,
            complexity_contribution=complexity_contribution
        )

        logger.info(
            f"ConfidenceEstimator: Score={confidence_score:.2f}, "
            f"Uncertain={is_uncertain}, Recommendation={recommendation}"
        )

        return result

    def _calculate_complexity_factor(
        self,
        context: dict[str, Any] | None,
        user_input: str | None,
        physics_state: dict[str, Any]
    ) -> float:
        """
        Calculate complexity factor (0.0-1.0) based on context and input.

        Factors:
        - Context complexity (memory count, inferred contexts)
        - Input complexity (length, question count, ambiguity)
        - Physics state complexity (low phi, high amplitude)

        Args:
            context: Context information
            user_input: User input text
            physics_state: Physics state

        Returns:
            Complexity factor (0.0 = simple, 1.0 = very complex)
        """
        complexity = 0.0

        # Factor 1: Context complexity
        if context:
            # Memory count (more memories = more complex)
            memory_count = context.get("memory_count", 0)
            if memory_count > 10:
                complexity += 0.2
            elif memory_count > 5:
                complexity += 0.1

            # Inferred contexts (GraphRAG complexity)
            inferred_contexts = context.get("inferred_contexts", [])
            if len(inferred_contexts) > 3:
                complexity += 0.2
            elif len(inferred_contexts) > 1:
                complexity += 0.1

            # Multiple intents detected
            if context.get("multi_intent", False):
                complexity += 0.2

        # Factor 2: Input complexity
        if user_input:
            input_lower = user_input.lower()

            # Length (very long inputs are complex)
            word_count = len(user_input.split())
            if word_count > 50:
                complexity += 0.15
            elif word_count > 30:
                complexity += 0.1

            # Question count (multiple questions = complex)
            question_count = user_input.count('?')
            if question_count > 2:
                complexity += 0.15
            elif question_count > 1:
                complexity += 0.1

            # Ambiguity indicators
            ambiguity_phrases = [
                "maybe", "perhaps", "not sure", "i think", "possibly",
                "could be", "might be", "uncertain", "confused"
            ]
            ambiguity_count = sum(1 for phrase in ambiguity_phrases if phrase in input_lower)
            if ambiguity_count > 0:
                complexity += 0.1 * min(ambiguity_count, 3)

            # Contradictions
            contradiction_pairs = [
                ("yes", "no"), ("always", "never"), ("all", "none"),
                ("true", "false"), ("right", "wrong")
            ]
            for pair in contradiction_pairs:
                if pair[0] in input_lower and pair[1] in input_lower:
                    complexity += 0.2
                    break

        # Factor 3: Physics state complexity
        phi = physics_state.get("phi", 1.0)
        amplitude = physics_state.get("amplitude", 5.0)

        # Low phi = chaotic state = complex
        if phi < 0.3:
            complexity += 0.2
        elif phi < 0.5:
            complexity += 0.1

        # High amplitude = volatile = complex
        if amplitude > 8.0:
            complexity += 0.15
        elif amplitude > 6.0:
            complexity += 0.1

        # Clamp to [0.0, 1.0]
        complexity = max(0.0, min(1.0, complexity))

        return complexity

    def get_hedging_phrase(self, language: str = "tr") -> str:
        """
        Get a hedging phrase to add to responses when uncertain.

        Args:
            language: Language code ("tr" for Turkish, "en" for English)

        Returns:
            Hedging phrase
        """
        if language == "tr":
            return "Kesin olmamakla birlikte, "
        else:  # English
            return "I am not certain, but "

    def get_clarification_request(
        self,
        user_input: str | None = None,
        language: str = "tr"
    ) -> str:
        """
        Generate a clarification request when confidence is very low.

        Args:
            user_input: Original user input (for context)
            language: Language code

        Returns:
            Clarification request message
        """
        if language == "tr":
            base = "Bu konuda emin değilim. "
            if user_input and "?" in user_input:
                return base + "Sorunuzu biraz daha açıklayabilir misiniz? Hangi açıdan yardımcı olmamı istersiniz?"
            else:
                return base + "Biraz daha detay verebilir misiniz? Ne hakkında konuşmak istersiniz?"
        else:  # English
            base = "I'm not certain about this. "
            if user_input and "?" in user_input:
                return base + "Could you clarify your question? What specific aspect would you like help with?"
            else:
                return base + "Could you provide more details? What would you like to discuss?"

