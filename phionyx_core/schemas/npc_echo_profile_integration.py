"""
NPC Echo Profile Integration Helpers
====================================

Helper functions to integrate NPC echo profile criteria into various systems:
- Memory Engine (trace_half_life)
- Reaction Queue (delay_tendency)
- Social System (propagation_radius)
- Event Filtering (selectivity_threshold)
- Policy Engine (feedback_sensitivity)
"""


from .npc_echo_profile import NPCEchoProfile


def apply_trace_half_life(
    npc_profile: NPCEchoProfile,
    memory_decay_rate: float
) -> float:
    """
    Apply trace_half_life to memory decay rate.

    Higher trace_half_life → memories fade faster (lower decay rate needed).
    Lower trace_half_life → memories persist longer (higher decay rate needed).

    Formula: adjusted_decay = memory_decay_rate * (1.0 - trace_half_life)

    Args:
        npc_profile: NPC echo profile
        memory_decay_rate: Base memory decay rate (0-1)

    Returns:
        Adjusted memory decay rate
    """
    # trace_half_life: 0.0 = memories persist forever, 1.0 = memories fade instantly
    # We invert it: higher trace_half_life → faster decay
    adjusted = memory_decay_rate * (1.0 + npc_profile.trace_half_life)
    return min(1.0, adjusted)


def apply_delay_tendency(
    npc_profile: NPCEchoProfile,
    base_reaction_delay: float
) -> float:
    """
    Apply delay_tendency to reaction delay (pending_reactions queue).

    Higher delay_tendency → NPC reacts slower (longer delay).
    Lower delay_tendency → NPC reacts faster (shorter delay).

    Formula: adjusted_delay = base_reaction_delay * (1.0 + delay_tendency)

    Args:
        npc_profile: NPC echo profile
        base_reaction_delay: Base reaction delay in seconds

    Returns:
        Adjusted reaction delay
    """
    # delay_tendency: 0.0 = instant reaction, 1.0 = very slow reaction
    adjusted = base_reaction_delay * (1.0 + npc_profile.delay_tendency)
    return adjusted


def apply_propagation_radius(
    npc_profile: NPCEchoProfile,
    base_social_influence: float
) -> float:
    """
    Apply propagation_radius to social influence.

    Higher propagation_radius → NPC affects more NPCs.
    Lower propagation_radius → NPC affects fewer NPCs.

    Formula: adjusted_influence = base_social_influence * propagation_radius

    Args:
        npc_profile: NPC echo profile
        base_social_influence: Base social influence value (0-1)

    Returns:
        Adjusted social influence
    """
    # propagation_radius: 0.0 = no social influence, 1.0 = maximum social influence
    return base_social_influence * npc_profile.propagation_radius


def apply_selectivity_threshold(
    npc_profile: NPCEchoProfile,
    event_importance: float
) -> bool:
    """
    Apply selectivity_threshold to event filtering.

    Higher selectivity_threshold → NPC ignores more events (only reacts to important ones).
    Lower selectivity_threshold → NPC reacts to more events.

    Formula: event_importance >= selectivity_threshold → process event

    Args:
        npc_profile: NPC echo profile
        event_importance: Event importance score (0-1)

    Returns:
        True if event should be processed, False if filtered out
    """
    # selectivity_threshold: 0.0 = process all events, 1.0 = process only critical events
    return event_importance >= npc_profile.selectivity_threshold


def apply_feedback_sensitivity(
    npc_profile: NPCEchoProfile,
    base_learning_rate: float
) -> float:
    """
    Apply feedback_sensitivity to policy learning rate.

    Higher feedback_sensitivity → NPC adapts faster to feedback.
    Lower feedback_sensitivity → NPC adapts slower to feedback.

    Formula: adjusted_learning_rate = base_learning_rate * feedback_sensitivity

    Args:
        npc_profile: NPC echo profile
        base_learning_rate: Base policy learning rate (0-1)

    Returns:
        Adjusted learning rate
    """
    # feedback_sensitivity: 0.0 = no adaptation, 1.0 = maximum adaptation
    return base_learning_rate * npc_profile.feedback_sensitivity


def get_npc_physics_params(
    npc_profile: NPCEchoProfile,
    time_delta: float = 0.0
) -> dict[str, float]:
    """
    Get physics parameters for NPC from echo profile.

    This extracts base_valence and base_arousal from the NPC echo profile
    and prepares them for use with compute_phi_components().

    Args:
        npc_profile: NPC echo profile
        time_delta: Time elapsed (t) for physics calculation

    Returns:
        Dictionary with physics parameters compatible with NPCPhysicsParams
    """
    return {
        "valence": npc_profile.base_valence,
        "arousal": npc_profile.base_arousal,
        "amplitude": 5.0,  # Default, can be overridden by emotion mapping preset
        "gamma": 0.25,  # Default, can be overridden
        "stability": 0.7,  # Default, can be overridden
        "entropy": 0.3,  # Default, can be overridden
        "w_cognitive": 0.5,  # Default, can be overridden
        "w_physical": 0.5,  # Default, can be overridden
        "t": time_delta
    }

