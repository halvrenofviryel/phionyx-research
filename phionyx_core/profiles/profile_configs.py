"""
Product Profile Configurations
==============================

Predefined product profiles for different use cases.
"""

from typing import Dict, Any

# ============================================================================
# EDU PROFILE (Kooth / Smoothwall)
# ============================================================================

EDU_PROFILE: Dict[str, Any] = {
    "profile": "edu",
    "description": "Educational profile for schools and mental health platforms",
    "modules": {
        "physics": "v2.1",  # ON - Full Physics v2.1
        "memory": "standard",  # ON - Limited memory
        "intuition": "null",  # OFF - No GraphRAG
        "pedagogy": "strict_school",  # STRICT - School-safe pedagogy
        "policy": "standard",  # ON - Standard policy
        "narrative": "simple",  # SIMPLE - Simple narrative
        "meta": "standard"  # ON - Meta-cognition
    },
    "features": {
        "gdpr_compliance": True,
        "audit_logging": True,
        "replay_mode": True,
        "trust_scoring": True
    },
    "physics_v2_1": {
        "valence": 0.0,  # Neutral valence for supportive tone
        "arousal": 0.5,  # Moderate arousal for calm learning
        "amplitude": 5.0,
        "entropy": 0.3,
        "stability": 0.9,
        "gamma": 0.15,
        "w_c": 0.75,
        "w_p": 0.25
    }
}

# ============================================================================
# GAME PROFILE (Inkle / Failbetter)
# ============================================================================

GAME_PROFILE: Dict[str, Any] = {
    "profile": "game",
    "description": "Game profile for interactive fiction studios",
    "modules": {
        "physics": "v2.1",  # ON - Full Physics v2.1
        "memory": "full",  # ON - Full memory
        "intuition": "graphrag",  # ON - GraphRAG enabled
        "pedagogy": "light",  # LIGHT - Minimal pedagogy
        "policy": "standard",  # ON - Standard policy
        "narrative": "rich",  # RICH - Rich narrative
        "meta": "standard"  # ON - Meta-cognition
    },
    "features": {
        "gdpr_compliance": False,
        "audit_logging": False,
        "replay_mode": True,
        "trust_scoring": False
    },
    "physics_v2_1": {
        "valence": 0.3,  # Slightly positive for engaging narrative
        "arousal": 0.8,  # High arousal for exciting gameplay
        "amplitude": 7.0,
        "entropy": 0.4,
        "stability": 0.7,
        "gamma": 0.2,
        "w_c": 0.65,
        "w_p": 0.35
    }
}

# ============================================================================
# CLINICAL PROFILE (Kooth clinical triage)
# ============================================================================

CLINICAL_PROFILE: Dict[str, Any] = {
    "profile": "clinical",
    "description": "Clinical profile for mental health triage",
    "modules": {
        "physics": "v2.1_ptg",  # ON - PTG-weighted Physics
        "memory": "controlled",  # ON - Very controlled memory
        "intuition": "limited",  # ON - Limited GraphRAG
        "pedagogy": "max_strict",  # MAX STRICT - Maximum pedagogy
        "policy": "clinical",  # ON - Clinical policy
        "narrative": "therapeutic",  # THERAPEUTIC - Therapeutic narrative
        "meta": "enhanced"  # ON - Enhanced meta-cognition + logging
    },
    "features": {
        "gdpr_compliance": True,
        "audit_logging": True,
        "replay_mode": True,
        "trust_scoring": True,
        "extra_logging": True
    },
    "physics_v2_1": {
        "valence": 0.0,  # Neutral valence for therapeutic neutrality
        "arousal": 0.3,  # Low arousal for calm, supportive environment
        "amplitude": 4.0,
        "entropy": 0.2,
        "stability": 0.95,
        "gamma": 0.1,
        "w_c": 0.8,
        "w_p": 0.2
    }
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_profile_config(profile_name: str) -> Dict[str, Any]:
    """
    Get profile configuration by name.

    Args:
        profile_name: Profile name ('edu', 'game', 'clinical')

    Returns:
        Profile configuration dictionary
    """
    profiles = {
        "edu": EDU_PROFILE,
        "game": GAME_PROFILE,
        "clinical": CLINICAL_PROFILE
    }

    return profiles.get(profile_name.lower(), EDU_PROFILE)  # Default to EDU

