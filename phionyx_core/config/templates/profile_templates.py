"""
Example Profile Templates
=========================

These are example profile configurations for Phionyx Core SDK.
Replace these values with your own based on your use case.

These templates demonstrate the structure and schema of profile configurations.
They are NOT production values and should be customized for your specific needs.
"""

from typing import Any

# ============================================================================
# EXAMPLE EDU PROFILE (Educational/School Use Cases)
# ============================================================================

EXAMPLE_EDU_PROFILE: dict[str, Any] = {
    "profile": "edu",
    "description": "Example educational profile for schools and mental health platforms",
    "modules": {
        "physics": "v2.1",  # Full Physics v2.1
        "memory": "standard",  # Limited memory
        "intuition": "null",  # No GraphRAG
        "pedagogy": "strict_school",  # School-safe pedagogy
        "policy": "standard",  # Standard policy
        "narrative": "simple",  # Simple narrative
        "meta": "standard"  # Meta-cognition
    },
    "features": {
        "gdpr_compliance": True,
        "audit_logging": True,
        "replay_mode": True,
        "trust_scoring": True
    },
    "physics_v2_1": {
        "valence": 0.0,  # EXAMPLE VALUE - Neutral valence for supportive tone
        "arousal": 0.5,  # EXAMPLE VALUE - Moderate arousal for calm learning
        "amplitude": 5.0,  # EXAMPLE VALUE
        "entropy": 0.3,  # EXAMPLE VALUE
        "stability": 0.9,  # EXAMPLE VALUE
        "gamma": 0.15,  # EXAMPLE VALUE
        "w_c": 0.75,  # EXAMPLE VALUE - Cognitive weight
        "w_p": 0.25  # EXAMPLE VALUE - Physical weight
    }
}

# ============================================================================
# EXAMPLE GAME PROFILE (Interactive Fiction / Game Studios)
# ============================================================================

EXAMPLE_GAME_PROFILE: dict[str, Any] = {
    "profile": "game",
    "description": "Example game profile for interactive fiction studios",
    "modules": {
        "physics": "v2.1",
        "memory": "extended",  # Extended memory for narrative continuity
        "intuition": "standard",  # GraphRAG enabled
        "pedagogy": "null",  # No pedagogy constraints
        "policy": "standard",
        "narrative": "rich",  # Rich narrative generation
        "meta": "standard"
    },
    "features": {
        "gdpr_compliance": True,
        "audit_logging": True,
        "replay_mode": True,
        "trust_scoring": True
    },
    "physics_v2_1": {
        "valence": 0.2,  # EXAMPLE VALUE - Slightly positive for engaging narrative
        "arousal": 0.7,  # EXAMPLE VALUE - Higher arousal for dynamic gameplay
        "amplitude": 7.0,  # EXAMPLE VALUE
        "entropy": 0.5,  # EXAMPLE VALUE
        "stability": 0.7,  # EXAMPLE VALUE
        "gamma": 0.2,  # EXAMPLE VALUE
        "w_c": 0.65,  # EXAMPLE VALUE
        "w_p": 0.35  # EXAMPLE VALUE
    }
}

# ============================================================================
# EXAMPLE CLINICAL PROFILE (Clinical/Mental Health Use Cases)
# ============================================================================

EXAMPLE_CLINICAL_PROFILE: dict[str, Any] = {
    "profile": "clinical",
    "description": "Example clinical profile for mental health applications",
    "modules": {
        "physics": "v2.1",
        "memory": "extended",  # Extended memory for therapeutic continuity
        "intuition": "standard",
        "pedagogy": "clinical",  # Clinical pedagogy constraints
        "policy": "strict",  # Strict policy enforcement
        "narrative": "therapeutic",  # Therapeutic narrative style
        "meta": "extended"  # Extended meta-cognition
    },
    "features": {
        "gdpr_compliance": True,
        "audit_logging": True,
        "replay_mode": True,
        "trust_scoring": True,
        "clinical_mode": True  # Clinical-specific features
    },
    "physics_v2_1": {
        "valence": 0.0,  # EXAMPLE VALUE - Neutral for therapeutic neutrality
        "arousal": 0.4,  # EXAMPLE VALUE - Lower arousal for calm environment
        "amplitude": 4.0,  # EXAMPLE VALUE
        "entropy": 0.25,  # EXAMPLE VALUE
        "stability": 0.95,  # EXAMPLE VALUE - High stability for reliability
        "gamma": 0.1,  # EXAMPLE VALUE
        "w_c": 0.8,  # EXAMPLE VALUE - Higher cognitive weight
        "w_p": 0.2  # EXAMPLE VALUE
    }
}

# ============================================================================
# USAGE INSTRUCTIONS
# ============================================================================

"""
To use these templates:

1. Copy the example profile that matches your use case
2. Customize the values based on your requirements
3. Replace "EXAMPLE VALUE" comments with your own values
4. Adjust physics_v2_1 parameters based on your behavioral requirements
5. Configure modules based on your feature needs

For detailed information on:
- Physics parameters: See arXiv paper Section 4
- Profile modules: See Phionyx Evaluation Standard v0.1
- Behavioral assessment: See technical book "Phionyx System: Deterministic AI, Observability, and Assurance"
"""

