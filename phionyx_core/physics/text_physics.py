"""
Text Physics - Deterministic Text Analysis Engine
==================================================
Sensor layer for extracting psycholinguistic signals from text.

Scientific Grounding:
- Psycholinguistic Lexicon: Dictionary-based valence/arousal extraction
- Kolmogorov Complexity: Information-theoretic entropy measure
- Determinstic Processing: No randomness, fully reproducible
"""

import re

from .core_math import calculate_kolmogorov_complexity

# Psycholinguistic Lexicon (Valence-Arousal-Dominance)
# Format: {term: (valence, arousal)}
# Valence: -1.0 (very negative) to +1.0 (very positive)
# Arousal: 0.0 (calm) to 1.0 (excited)
PSYCHOLINGUISTIC_LEXICON = {
    # Positive valence, high arousal
    "harika": (0.8, 0.7),
    "mükemmel": (0.9, 0.6),
    "muhteşem": (0.85, 0.75),
    "heyecanlı": (0.6, 0.9),
    "heyecanlıyım": (0.6, 0.9),
    "mutlu": (0.7, 0.6),
    "mutluyum": (0.7, 0.6),
    "sevinçli": (0.75, 0.7),
    "coşkulu": (0.7, 0.85),
    "neşeli": (0.7, 0.65),
    "happy": (0.7, 0.6),
    "excited": (0.6, 0.9),
    "great": (0.8, 0.7),
    "wonderful": (0.85, 0.65),
    "fantastic": (0.8, 0.75),
    "amazing": (0.75, 0.7),

    # Positive valence, low arousal
    "sakin": (0.5, 0.2),
    "sakinim": (0.5, 0.2),
    "rahat": (0.6, 0.3),
    "rahatım": (0.6, 0.3),
    "huzurlu": (0.7, 0.25),
    "huzurluyum": (0.7, 0.25),
    "dingin": (0.6, 0.2),
    "calm": (0.5, 0.2),
    "peaceful": (0.6, 0.25),
    "relaxed": (0.6, 0.3),
    "content": (0.65, 0.3),

    # Negative valence, high arousal
    "kötü": (-0.7, 0.6),
    "kötüyüm": (-0.7, 0.6),
    "berbat": (-0.8, 0.7),
    "korkunç": (-0.85, 0.8),
    "kızgın": (-0.6, 0.85),
    "kızgınım": (-0.6, 0.85),
    "sinirli": (-0.65, 0.8),
    "sinirliyim": (-0.65, 0.8),
    "öfkeliyim": (-0.7, 0.9),
    "üzgün": (-0.7, 0.5),
    "üzgünüm": (-0.7, 0.5),
    "kederli": (-0.75, 0.4),
    "mutsuz": (-0.7, 0.5),
    "mutsuzum": (-0.7, 0.5),
    "sad": (-0.7, 0.5),
    "angry": (-0.6, 0.85),
    "terrible": (-0.8, 0.7),
    "awful": (-0.75, 0.6),
    "furious": (-0.75, 0.9),
    "horrible": (-0.8, 0.7),

    # Negative valence, low arousal
    "yorgun": (-0.4, 0.2),
    "yorgunum": (-0.4, 0.2),
    "bitkin": (-0.5, 0.15),
    "tükenmiş": (-0.6, 0.2),
    "umutsuz": (-0.8, 0.3),
    "umutsuzum": (-0.8, 0.3),
    "tired": (-0.4, 0.2),
    "exhausted": (-0.5, 0.15),
    "hopeless": (-0.8, 0.3),
    "depressed": (-0.75, 0.25),
}

# Negation modifiers (reverse valence)
NEGATION_WORDS = {
    "değil", "değilim", "değiliz", "değilsin", "değilsiniz",
    "not", "no", "never", "nobody", "nothing", "nowhere", "neither", "nor"
}

# Intensifier modifiers (increase magnitude)
INTENSIFIERS = {
    "çok", "çokça", "fazla", "aşırı", "son derece", "oldukça", "gerçekten",
    "very", "extremely", "really", "quite", "so", "too", "incredibly", "absolutely"
}

# Diminisher modifiers (decrease magnitude)
DIMINISHERS = {
    "biraz", "birazcık", "az", "azıcık", "kısmen",
    "slightly", "somewhat", "a bit", "a little", "kinda", "sort of"
}


def analyze_text_psycholinguistics(text: str) -> dict[str, float]:
    """
    Analyze text using psycholinguistic lexicon to extract Valence and Arousal.

    Scientific Approach:
    - Dictionary-based extraction (reproducible, deterministic)
    - Negation handling (semantic inversion)
    - Modifier handling (intensifiers, diminishers)
    - Weighted averaging of matched terms

    Args:
        text: Input text string

    Returns:
        Dictionary with:
        - "valence": float in [-1.0, +1.0] (negative to positive)
        - "arousal": float in [0.0, 1.0] (calm to excited)
        - "confidence": float in [0.0, 1.0] (how many terms matched)

    Example:
        >>> result = analyze_text_psycholinguistics("I am very happy and excited!")
        >>> result["valence"] > 0.5
        True
        >>> result["arousal"] > 0.7
        True
    """
    if not text or not text.strip():
        return {
            "valence": 0.0,
            "arousal": 0.5,
            "confidence": 0.0
        }

    # Normalize text (lowercase, remove extra spaces)
    normalized_text = text.lower().strip()
    words = re.findall(r'\b\w+\b', normalized_text)

    # Track matched terms
    matched_terms = []
    valence_scores = []
    arousal_scores = []

    # Check for negation (presence in sentence)
    has_negation = any(word in NEGATION_WORDS for word in words)

    # Check for intensifiers/diminishers
    intensifier_count = sum(1 for word in words if word in INTENSIFIERS)
    diminisher_count = sum(1 for word in words if word in DIMINISHERS)

    # Match lexicon terms
    for term, (term_valence, term_arousal) in PSYCHOLINGUISTIC_LEXICON.items():
        if term in normalized_text:
            matched_terms.append(term)
            valence_scores.append(term_valence)
            arousal_scores.append(term_arousal)

    # Calculate base valence and arousal (weighted average)
    if valence_scores:
        base_valence = sum(valence_scores) / len(valence_scores)
        base_arousal = sum(arousal_scores) / len(arousal_scores)
        confidence = min(1.0, len(matched_terms) / 5.0)  # Normalize to 5 terms = 1.0
    else:
        # No matches - return neutral with low confidence
        base_valence = 0.0
        base_arousal = 0.5
        confidence = 0.0

    # Apply negation (reverse valence sign)
    if has_negation and matched_terms:
        base_valence = -base_valence * 0.7  # Reduce magnitude when negated
        base_arousal = base_arousal * 0.8   # Slightly reduce arousal

    # Apply intensifiers (increase magnitude)
    if intensifier_count > 0:
        multiplier = 1.0 + (intensifier_count * 0.15)  # Each intensifier adds 15%
        if base_valence > 0:
            base_valence = min(1.0, base_valence * multiplier)
        else:
            base_valence = max(-1.0, base_valence * multiplier)
        base_arousal = min(1.0, base_arousal * multiplier)

    # Apply diminishers (decrease magnitude)
    if diminisher_count > 0:
        multiplier = 1.0 - (diminisher_count * 0.2)  # Each diminisher reduces 20%
        base_valence = base_valence * multiplier
        base_arousal = max(0.0, base_arousal * multiplier)

    # Clamp to valid ranges
    final_valence = max(-1.0, min(1.0, base_valence))
    final_arousal = max(0.0, min(1.0, base_arousal))

    return {
        "valence": final_valence,
        "arousal": final_arousal,
        "confidence": confidence
    }


def calculate_text_entropy_zlib(text: str) -> float:
    """
    Calculate text entropy using Kolmogorov Complexity (Zlib compression ratio).

    Scientific Approach:
    - Uses Information Theory (Kolmogorov Complexity approximation)
    - Replaces naive "length/500" or "word_count/100" heuristics
    - Measures actual information density (compressibility)

    Args:
        text: Input text string

    Returns:
        Entropy value in [0.0, 1.0] where:
        - 0.0 = highly compressible (low entropy, predictable)
        - 1.0 = incompressible (high entropy, random/unpredictable)

    Example:
        >>> calculate_text_entropy_zlib("AAAAA")  # Repetitive, low entropy
        0.1
        >>> calculate_text_entropy_zlib("random unpredictable text with high complexity")  # High entropy
        0.8
    """
    if not text:
        return 0.0

    # Use Kolmogorov Complexity as entropy measure
    return calculate_kolmogorov_complexity(text)

